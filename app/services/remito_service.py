from datetime import date

from sqlalchemy.orm import Session

from app.config import settings
from app.domain.enums import EstadoEjemplar, EstadoFisico, EstadoPrestamo, TipoIncidencia, TipoRemito
from app.exceptions import NoEncontradoError, ReglaNegocioError
from app.models import Incidencia, Prestamo, Remito
from app.repositories import IncidenciaRepository, RemitoRepository
from app.repositories.base import Paginacion, ResultadoPaginado
from app.services.reserva_service import ReservaService

_INCIDENCIA_POR_ESTADO_FISICO = {
    EstadoFisico.DANADO: TipoIncidencia.DANIO,
    EstadoFisico.DESTRUIDO: TipoIncidencia.DESTRUCCION,
}


class RemitoService:
    """Coordina las transiciones del remito (patron State, ver domain/estados_remito.py)
    con sus efectos sobre el ejemplar y el prestamo."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = RemitoRepository(db)
        self.incidencias = IncidenciaRepository(db)

    def listar(
        self, paginacion: Paginacion, estado: str | None = None, sede_id: int | None = None
    ) -> ResultadoPaginado[Remito]:
        return self.repo.listar_filtrado(paginacion, estado, sede_id)

    def obtener(self, remito_id: int) -> Remito:
        remito = self.repo.obtener(remito_id)
        if remito is None:
            raise NoEncontradoError(f"No existe el remito {remito_id}")
        return remito

    def obtener_por_numero(self, numero: str) -> Remito:
        remito = self.repo.buscar_por_numero(numero)
        if remito is None:
            raise NoEncontradoError(f"No existe el remito {numero}")
        return remito

    def listar_incidencias(
        self,
        paginacion: Paginacion,
        tipo: TipoIncidencia | None = None,
        sede_id: int | None = None,
        desde: date | None = None,
        hasta: date | None = None,
    ) -> ResultadoPaginado[Incidencia]:
        return self.incidencias.listar_filtrado(paginacion, tipo, sede_id, desde, hasta)

    def generar(self, prestamo: Prestamo, tipo: TipoRemito) -> Remito:
        """Crea el remito en estado PENDIENTE. No hace commit."""
        if tipo == TipoRemito.IDA:
            origen, destino = prestamo.sede_origen_id, prestamo.sede_destino_id
        else:
            origen, destino = prestamo.sede_destino_id, prestamo.sede_origen_id
        remito = Remito(
            numero=self.repo.siguiente_numero(),
            tipo=tipo,
            prestamo=prestamo,
            ejemplar_id=prestamo.ejemplar_id,
            sede_origen_id=origen,
            sede_destino_id=destino,
        )
        remito.registrar_creacion()
        return self.repo.agregar(remito)

    def empaquetar(self, remito_id: int, observacion: str | None = None) -> Remito:
        remito = self.obtener(remito_id)
        remito.empaquetar(observacion)
        self.db.commit()
        return remito

    def despachar(self, remito_id: int, observacion: str | None = None) -> Remito:
        remito = self.obtener(remito_id)
        if remito.tipo == TipoRemito.IDA:
            # El retorno no se bloquea: el ejemplar tiene que volver a su sede igual.
            for sede in (remito.sede_origen, remito.sede_destino):
                if not sede.activa:
                    raise ReglaNegocioError(f"No se pueden iniciar envios desde/hacia '{sede.nombre}' (dada de baja)")
        remito.despachar(observacion)
        remito.ejemplar.cambiar_estado(EstadoEjemplar.EN_TRANSITO)
        if remito.tipo == TipoRemito.IDA:
            remito.prestamo.estado = EstadoPrestamo.EN_TRANSITO
        self.db.commit()
        return remito

    def recibir(
        self,
        remito_id: int,
        estado_fisico: EstadoFisico = EstadoFisico.BUENO,
        observacion: str | None = None,
        hoy: date | None = None,
    ) -> Remito:
        """Registra la llegada y la revision del ejemplar. Si llega danado o destruido
        queda registrada la incidencia."""
        remito = self.obtener(remito_id)
        remito.recibir(observacion)
        remito.estado_fisico_recepcion = estado_fisico
        ejemplar = remito.ejemplar
        ejemplar.estado_fisico = estado_fisico

        if estado_fisico in _INCIDENCIA_POR_ESTADO_FISICO:
            remito.registrar_incidencia(_INCIDENCIA_POR_ESTADO_FISICO[estado_fisico], observacion)

        if estado_fisico == EstadoFisico.DESTRUIDO:
            ejemplar.cambiar_estado(EstadoEjemplar.BAJA)
            if remito.tipo == TipoRemito.IDA:
                remito.prestamo.estado = EstadoPrestamo.CANCELADO
                remito.prestamo.observaciones = f"Cancelado: ejemplar destruido en el remito {remito.numero}"
        elif remito.tipo == TipoRemito.IDA:
            # Llego a la sede destino: el socio ya puede retirarlo y empieza a correr el plazo.
            remito.prestamo.activar(hoy or date.today(), settings.dias_prestamo)
            ejemplar.cambiar_estado(EstadoEjemplar.PRESTADO)
        else:
            ejemplar.liberar()
            self.db.flush()
            ReservaService(self.db).asignar_ejemplar_liberado(ejemplar, hoy)
        self.db.commit()
        return remito

    def marcar_extraviado(self, remito_id: int, observacion: str | None = None) -> Remito:
        remito = self.obtener(remito_id)
        remito.marcar_extraviado(observacion)
        remito.registrar_incidencia(TipoIncidencia.EXTRAVIO, observacion)
        remito.ejemplar.cambiar_estado(EstadoEjemplar.EXTRAVIADO)
        if remito.tipo == TipoRemito.IDA:
            remito.prestamo.estado = EstadoPrestamo.CANCELADO
            remito.prestamo.observaciones = f"Cancelado por extravio del remito {remito.numero}"
        self.db.commit()
        return remito

    def cancelar(self, remito_id: int, observacion: str | None = None) -> Remito:
        remito = self.obtener(remito_id)
        if remito.tipo == TipoRemito.RETORNO:
            raise ReglaNegocioError("Un remito de retorno no se puede cancelar: el ejemplar debe volver a su sede")
        remito.cancelar(observacion)
        remito.prestamo.estado = EstadoPrestamo.CANCELADO
        ejemplar = remito.ejemplar
        ejemplar.liberar()
        self.db.flush()
        ReservaService(self.db).asignar_ejemplar_liberado(ejemplar)
        self.db.commit()
        return remito
