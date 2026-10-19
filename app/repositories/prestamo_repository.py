from datetime import date

from sqlalchemy import func, select

from app.domain.enums import EstadoPrestamo
from app.models import Prestamo
from app.repositories.base import BaseRepository

ESTADOS_EN_CURSO = (EstadoPrestamo.SOLICITADO, EstadoPrestamo.EN_TRANSITO, EstadoPrestamo.ACTIVO)


class PrestamoRepository(BaseRepository[Prestamo]):
    modelo = Prestamo

    def listar_filtrado(
        self, socio_id: int | None = None, estado: EstadoPrestamo | None = None
    ) -> list[Prestamo]:
        consulta = select(Prestamo).order_by(Prestamo.id.desc())
        if socio_id is not None:
            consulta = consulta.where(Prestamo.socio_id == socio_id)
        if estado is not None:
            consulta = consulta.where(Prestamo.estado == estado)
        return list(self.db.scalars(consulta))

    def contar_en_curso(self, socio_id: int) -> int:
        consulta = select(func.count(Prestamo.id)).where(
            Prestamo.socio_id == socio_id, Prestamo.estado.in_(ESTADOS_EN_CURSO)
        )
        return self.db.scalar(consulta)

    def tiene_vencidos(self, socio_id: int, fecha: date) -> bool:
        consulta = select(func.count(Prestamo.id)).where(
            Prestamo.socio_id == socio_id,
            Prestamo.estado == EstadoPrestamo.ACTIVO,
            Prestamo.fecha_vencimiento < fecha,
        )
        return self.db.scalar(consulta) > 0
