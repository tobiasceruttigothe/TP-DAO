from datetime import date

from sqlalchemy.orm import Session

from app.config import settings
from app.domain.enums import EstadoEjemplar, EstadoPrestamo, EstadoReserva, TipoPrestamo, TipoRemito
from app.domain.multas import CalculadorMulta, crear_estrategia
from app.exceptions import NoEncontradoError, ReglaNegocioError
from app.models import Prestamo
from app.repositories import EjemplarRepository, PrestamoRepository, ReservaRepository
from app.schemas.prestamo import DevolucionCrear, PrestamoCrear
from app.services.remito_service import RemitoService
from app.services.reserva_service import ReservaService
from app.services.sede_service import SedeService
from app.services.socio_service import SocioService


class PrestamoService:
    def __init__(self, db: Session, calculador: CalculadorMulta | None = None):
        self.db = db
        self.repo = PrestamoRepository(db)
        self.ejemplares = EjemplarRepository(db)
        self.reservas = ReservaRepository(db)
        self.calculador = calculador or CalculadorMulta(
            crear_estrategia(settings.multa_estrategia, settings.multa_monto_diario)
        )

    def listar(self, socio_id: int | None = None, estado: EstadoPrestamo | None = None) -> list[Prestamo]:
        return self.repo.listar_filtrado(socio_id, estado)

    def obtener(self, prestamo_id: int) -> Prestamo:
        prestamo = self.repo.obtener(prestamo_id)
        if prestamo is None:
            raise NoEncontradoError(f"No existe el prestamo {prestamo_id}")
        return prestamo

    def solicitar(self, datos: PrestamoCrear, hoy: date | None = None) -> Prestamo:
        hoy = hoy or date.today()
        socio = SocioService(self.db).obtener_habilitado(datos.socio_id)
        if self.repo.tiene_vencidos(socio.id, hoy):
            raise ReglaNegocioError("El socio tiene prestamos vencidos sin devolver")
        if self.repo.contar_en_curso(socio.id) >= settings.max_prestamos_activos:
            raise ReglaNegocioError(f"El socio alcanzo el maximo de {settings.max_prestamos_activos} prestamos")

        sedes = SedeService(self.db)
        origen = sedes.obtener_activa(datos.sede_origen_id)
        destino = sedes.obtener_activa(datos.sede_destino_id)

        ejemplar = self.ejemplares.obtener(datos.ejemplar_id)
        if ejemplar is None:
            raise NoEncontradoError(f"No existe el ejemplar {datos.ejemplar_id}")
        if ejemplar.sede_id != origen.id:
            raise ReglaNegocioError("El ejemplar no pertenece a la sede de origen del prestamo")

        reserva = None
        if ejemplar.estado == EstadoEjemplar.RESERVADO:
            reserva = self.reservas.por_ejemplar_apartado(ejemplar.id)
            if reserva is None or reserva.socio_id != socio.id:
                raise ReglaNegocioError("El ejemplar esta reservado para otro socio")
        elif not ejemplar.esta_disponible:
            raise ReglaNegocioError(f"El ejemplar no esta disponible (estado {ejemplar.estado.value})")

        tipo = TipoPrestamo.LOCAL if origen.id == destino.id else TipoPrestamo.INTERBIBLIOTECARIO
        prestamo = Prestamo(
            socio_id=socio.id,
            ejemplar_id=ejemplar.id,
            sede_origen_id=origen.id,
            sede_destino_id=destino.id,
            tipo=tipo,
            estado=EstadoPrestamo.SOLICITADO,
            fecha_solicitud=hoy,
        )
        self.repo.agregar(prestamo)
        ejemplar.cambiar_estado(EstadoEjemplar.PRESTADO)

        if tipo == TipoPrestamo.LOCAL:
            prestamo.activar(hoy, settings.dias_prestamo)
        else:
            RemitoService(self.db).generar(prestamo, TipoRemito.IDA)

        if reserva is not None:
            reserva.estado = EstadoReserva.CUMPLIDA

        self.db.commit()
        return prestamo

    def devolver(self, prestamo_id: int, datos: DevolucionCrear) -> Prestamo:
        prestamo = self.obtener(prestamo_id)
        if prestamo.estado != EstadoPrestamo.ACTIVO:
            raise ReglaNegocioError(f"Solo se pueden devolver prestamos activos (estado {prestamo.estado.value})")
        fecha = datos.fecha_devolucion or date.today()
        if fecha < prestamo.fecha_inicio:
            raise ReglaNegocioError("La fecha de devolucion es anterior al inicio del prestamo")

        prestamo.estado = EstadoPrestamo.DEVUELTO
        prestamo.fecha_devolucion = fecha
        prestamo.estado_fisico_devolucion = datos.estado_fisico
        prestamo.observaciones = datos.observaciones
        prestamo.multa = self.calculador.calcular(prestamo.dias_atraso(fecha))

        ejemplar = prestamo.ejemplar
        ejemplar.estado_fisico = datos.estado_fisico
        if prestamo.es_interbibliotecario:
            # Se devuelve en la sede destino y tiene que volver a su sede de origen.
            ejemplar.cambiar_estado(EstadoEjemplar.EN_TRANSITO)
            RemitoService(self.db).generar(prestamo, TipoRemito.RETORNO)
        else:
            ejemplar.liberar()
            self.db.flush()
            ReservaService(self.db).asignar_ejemplar_liberado(ejemplar, fecha)

        self.db.commit()
        return prestamo

    def multa_estimada(self, prestamo: Prestamo, hoy: date) -> float:
        """Multa que se cobraria si se devolviera hoy (para prestamos todavia activos)."""
        return self.calculador.calcular(prestamo.dias_atraso(hoy))
