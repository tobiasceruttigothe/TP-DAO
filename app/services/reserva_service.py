from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.config import settings
from app.domain.enums import EstadoEjemplar, EstadoReserva
from app.exceptions import NoEncontradoError, ReglaNegocioError
from app.models import Ejemplar, Reserva
from app.repositories import EjemplarRepository, LibroRepository, ReservaRepository
from app.repositories.base import Paginacion, ResultadoPaginado
from app.schemas.reserva import ReservaCrear
from app.services.sede_service import SedeService
from app.services.socio_service import SocioService


class ReservaService:
    """Un socio reserva un libro en una sede. Si hay un ejemplar libre se le aparta
    en el momento; si no, queda en espera y se le asigna el primero que se libere."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = ReservaRepository(db)
        self.ejemplares = EjemplarRepository(db)
        self.libros = LibroRepository(db)

    def listar(
        self, paginacion: Paginacion, socio_id: int | None = None, estado: EstadoReserva | None = None
    ) -> ResultadoPaginado[Reserva]:
        return self.repo.listar_filtrado(paginacion, socio_id, estado)

    def obtener(self, reserva_id: int) -> Reserva:
        reserva = self.repo.obtener(reserva_id)
        if reserva is None:
            raise NoEncontradoError(f"No existe la reserva {reserva_id}")
        return reserva

    def crear(self, datos: ReservaCrear, hoy: date | None = None) -> Reserva:
        hoy = hoy or date.today()
        socio = SocioService(self.db).obtener_habilitado(datos.socio_id)
        sede = SedeService(self.db).obtener_activa(datos.sede_id)
        libro = self.libros.obtener(datos.libro_id)
        if libro is None:
            raise NoEncontradoError(f"No existe el libro {datos.libro_id}")

        if self.repo.activa_de_socio(socio.id, libro.id) is not None:
            raise ReglaNegocioError("El socio ya tiene una reserva activa para ese libro")

        en_sede = [
            e for e in self.ejemplares.de_libro_en_sede(libro.id, sede.id)
            if e.estado not in (EstadoEjemplar.BAJA, EstadoEjemplar.EXTRAVIADO)
        ]
        if not en_sede:
            raise ReglaNegocioError(f"La sede '{sede.nombre}' no tiene ejemplares de ese libro")

        reserva = Reserva(
            socio_id=socio.id,
            libro_id=libro.id,
            sede_id=sede.id,
            estado=EstadoReserva.PENDIENTE,
            fecha_reserva=hoy,
        )
        self.repo.agregar(reserva)

        disponible = self.ejemplares.primero_disponible(libro.id, sede.id)
        if disponible is not None:
            self._apartar(reserva, disponible, hoy)

        self.db.commit()
        return reserva

    def cancelar(self, reserva_id: int) -> Reserva:
        reserva = self.obtener(reserva_id)
        if not reserva.esta_activa:
            raise ReglaNegocioError(f"La reserva ya esta {reserva.estado.value}")
        reserva.estado = EstadoReserva.CANCELADA
        self._liberar_ejemplar_de(reserva)
        self.db.commit()
        return reserva

    def procesar_vencidas(self, hoy: date | None = None) -> int:
        """Vence las reservas cuyo ejemplar apartado no se retiro a tiempo."""
        hoy = hoy or date.today()
        vencidas = self.repo.disponibles_vencidas(hoy)
        for reserva in vencidas:
            reserva.estado = EstadoReserva.VENCIDA
            self._liberar_ejemplar_de(reserva, hoy)
        self.db.commit()
        return len(vencidas)

    def asignar_ejemplar_liberado(self, ejemplar: Ejemplar, hoy: date | None = None):
        """Si alguien espera este libro en la sede del ejemplar, se lo aparta.
        No hace commit; lo llama otro servicio dentro de su propia operacion."""
        if not ejemplar.esta_disponible or not ejemplar.sede.activa:
            return
        reserva = self.repo.primera_pendiente(ejemplar.libro_id, ejemplar.sede_id)
        if reserva is not None:
            self._apartar(reserva, ejemplar, hoy or date.today())

    def _apartar(self, reserva: Reserva, ejemplar: Ejemplar, hoy: date):
        ejemplar.cambiar_estado(EstadoEjemplar.RESERVADO)
        reserva.ejemplar_id = ejemplar.id
        reserva.estado = EstadoReserva.DISPONIBLE
        reserva.fecha_expiracion = hoy + timedelta(days=settings.dias_validez_reserva)
        self.db.flush()

    def _liberar_ejemplar_de(self, reserva: Reserva, hoy: date | None = None):
        if reserva.ejemplar is None or reserva.ejemplar.estado != EstadoEjemplar.RESERVADO:
            return
        ejemplar = reserva.ejemplar
        ejemplar.cambiar_estado(EstadoEjemplar.DISPONIBLE)
        self.db.flush()
        self.asignar_ejemplar_liberado(ejemplar, hoy)
