from datetime import date

from sqlalchemy import select

from app.domain.enums import EstadoReserva
from app.models import Reserva
from app.repositories.base import BaseRepository, Paginacion, ResultadoPaginado

ESTADOS_ACTIVOS = (EstadoReserva.PENDIENTE, EstadoReserva.DISPONIBLE)


class ReservaRepository(BaseRepository[Reserva]):
    modelo = Reserva

    def listar_filtrado(
        self, paginacion: Paginacion, socio_id: int | None = None, estado: EstadoReserva | None = None
    ) -> ResultadoPaginado[Reserva]:
        consulta = select(Reserva).order_by(Reserva.id.desc())
        if socio_id is not None:
            consulta = consulta.where(Reserva.socio_id == socio_id)
        if estado is not None:
            consulta = consulta.where(Reserva.estado == estado)
        return self.paginar(consulta, paginacion)

    def activa_de_socio(self, socio_id: int, libro_id: int) -> Reserva | None:
        consulta = select(Reserva).where(
            Reserva.socio_id == socio_id,
            Reserva.libro_id == libro_id,
            Reserva.estado.in_(ESTADOS_ACTIVOS),
        )
        return self.db.scalar(consulta)

    def por_ejemplar_apartado(self, ejemplar_id: int) -> Reserva | None:
        consulta = select(Reserva).where(
            Reserva.ejemplar_id == ejemplar_id, Reserva.estado == EstadoReserva.DISPONIBLE
        )
        return self.db.scalar(consulta)

    def primera_pendiente(self, libro_id: int, sede_id: int) -> Reserva | None:
        """La reserva mas antigua que espera ese libro en esa sede (orden de llegada)."""
        consulta = (
            select(Reserva)
            .where(
                Reserva.libro_id == libro_id,
                Reserva.sede_id == sede_id,
                Reserva.estado == EstadoReserva.PENDIENTE,
            )
            .order_by(Reserva.fecha_reserva, Reserva.id)
            .limit(1)
        )
        return self.db.scalar(consulta)

    def disponibles_vencidas(self, fecha: date) -> list[Reserva]:
        consulta = select(Reserva).where(
            Reserva.estado == EstadoReserva.DISPONIBLE, Reserva.fecha_expiracion < fecha
        )
        return list(self.db.scalars(consulta))
