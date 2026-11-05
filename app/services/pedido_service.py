from sqlalchemy.orm import Session

from app.domain.enums import EstadoPedido, EstadoReserva
from app.exceptions import NoEncontradoError, ReglaNegocioError, SinPermisoError
from app.models import Pedido, Socio
from app.repositories import EjemplarRepository, LibroRepository, PedidoRepository, ReservaRepository
from app.repositories.base import Paginacion, ResultadoPaginado
from app.schemas.pedido import PedidoCrear
from app.schemas.prestamo import PrestamoCrear
from app.schemas.reserva import ReservaCrear
from app.services.eventos import PedidoAprobado, PedidoNuevo, PedidoRechazado, publicador
from app.services.prestamo_service import PrestamoService
from app.services.reserva_service import ReservaService
from app.services.sede_service import SedeService
from app.services.socio_service import SocioService


class PedidoService:
    """Un socio pide un libro para retirar en una sede, y un administrador lo resuelve:
    lo reserva en esa sede, lo trae desde otra con un prestamo entre sedes, o lo rechaza."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = PedidoRepository(db)
        self.ejemplares = EjemplarRepository(db)
        self.eventos = publicador(db)

    def listar(self, paginacion: Paginacion, socio_id=None, estado=None) -> ResultadoPaginado[Pedido]:
        return self.repo.listar_filtrado(paginacion, socio_id, estado)

    def obtener(self, pedido_id: int) -> Pedido:
        pedido = self.repo.obtener(pedido_id)
        if pedido is None:
            raise NoEncontradoError(f"No existe el pedido {pedido_id}")
        return pedido

    # --- Socio ---

    def crear(self, socio: Socio, datos: PedidoCrear) -> Pedido:
        SocioService(self.db).obtener_habilitado(socio.id)
        SedeService(self.db).obtener_activa(datos.sede_id)
        libro = LibroRepository(self.db).obtener(datos.libro_id)
        if libro is None:
            raise NoEncontradoError(f"No existe el libro {datos.libro_id}")
        if not self.ejemplares.hay_en_circulacion(libro.id):
            raise ReglaNegocioError("Ese libro no tiene ejemplares en la red")
        if self.repo.pendiente_de_socio(socio.id, libro.id) is not None:
            raise ReglaNegocioError("Ya tenés un pedido pendiente de ese libro")
        if ReservaRepository(self.db).activa_de_socio(socio.id, libro.id) is not None:
            raise ReglaNegocioError("Ya tenés una reserva activa de ese libro")

        pedido = self.repo.agregar(
            Pedido(socio_id=socio.id, libro_id=libro.id, sede_id=datos.sede_id, comentario=datos.comentario)
        )
        self.eventos.publicar(PedidoNuevo(pedido))
        self.db.commit()
        return pedido

    def cancelar(self, socio: Socio, pedido_id: int) -> Pedido:
        pedido = self.obtener(pedido_id)
        if pedido.socio_id != socio.id:
            raise SinPermisoError("El pedido no es tuyo")
        self._validar_pendiente(pedido)
        pedido.resolver(EstadoPedido.CANCELADO, "Cancelado por el socio")
        self.db.commit()
        return pedido

    # --- Administrador ---

    def reservar(self, pedido_id: int) -> Pedido:
        """Lo reserva en la sede pedida: si hay un ejemplar libre queda listo para retirar;
        si no, en espera del primero que se libere."""
        pedido = self.obtener(pedido_id)
        self._validar_pendiente(pedido)
        reserva = ReservaService(self.db).crear(
            ReservaCrear(socio_id=pedido.socio_id, libro_id=pedido.libro_id, sede_id=pedido.sede_id)
        )
        if reserva.estado == EstadoReserva.DISPONIBLE:
            texto = (
                f"Te reservamos un ejemplar en {pedido.sede.nombre}. "
                f"Podés retirarlo hasta el {reserva.fecha_expiracion:%d/%m/%Y}."
            )
        else:
            texto = (
                f"Quedaste en espera en {pedido.sede.nombre}: te avisamos apenas se libere un ejemplar."
            )
        pedido.reserva_id = reserva.id
        pedido.resolver(EstadoPedido.APROBADO, texto)
        self.eventos.publicar(PedidoAprobado(pedido))
        self.db.commit()
        return pedido

    def enviar_desde(self, pedido_id: int, sede_origen_id: int) -> Pedido:
        """Lo trae desde otra sede: genera el prestamo entre sedes y su remito."""
        pedido = self.obtener(pedido_id)
        self._validar_pendiente(pedido)
        if sede_origen_id == pedido.sede_id:
            raise ReglaNegocioError("Es la misma sede del pedido: en ese caso, reservalo")
        origen = SedeService(self.db).obtener_activa(sede_origen_id)
        ejemplar = self.ejemplares.primero_disponible(pedido.libro_id, origen.id)
        if ejemplar is None:
            raise ReglaNegocioError(f"{origen.nombre} no tiene ejemplares disponibles de ese libro")
        prestamo = PrestamoService(self.db).solicitar(
            PrestamoCrear(
                socio_id=pedido.socio_id,
                ejemplar_id=ejemplar.id,
                sede_origen_id=origen.id,
                sede_destino_id=pedido.sede_id,
            )
        )
        pedido.prestamo_id = prestamo.id
        pedido.resolver(
            EstadoPedido.APROBADO,
            f"Lo enviamos desde {origen.nombre} a {pedido.sede.nombre}. Te avisamos cuando llegue para que lo retires.",
        )
        self.eventos.publicar(PedidoAprobado(pedido))
        self.db.commit()
        return pedido

    def rechazar(self, pedido_id: int, motivo: str) -> Pedido:
        pedido = self.obtener(pedido_id)
        self._validar_pendiente(pedido)
        pedido.resolver(EstadoPedido.RECHAZADO, motivo)
        self.eventos.publicar(PedidoRechazado(pedido))
        self.db.commit()
        return pedido

    def _validar_pendiente(self, pedido: Pedido):
        if not pedido.esta_pendiente:
            raise ReglaNegocioError(f"El pedido ya está {pedido.estado.value.lower()}")
