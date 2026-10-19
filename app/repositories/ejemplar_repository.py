from sqlalchemy import select

from app.domain.enums import EstadoEjemplar
from app.models import Ejemplar
from app.repositories.base import BaseRepository


class EjemplarRepository(BaseRepository[Ejemplar]):
    modelo = Ejemplar

    def buscar_por_codigo(self, codigo: str) -> Ejemplar | None:
        return self.db.scalar(select(Ejemplar).where(Ejemplar.codigo_inventario == codigo))

    def listar_filtrado(
        self,
        libro_id: int | None = None,
        sede_id: int | None = None,
        estado: EstadoEjemplar | None = None,
    ) -> list[Ejemplar]:
        consulta = select(Ejemplar).order_by(Ejemplar.id)
        if libro_id is not None:
            consulta = consulta.where(Ejemplar.libro_id == libro_id)
        if sede_id is not None:
            consulta = consulta.where(Ejemplar.sede_id == sede_id)
        if estado is not None:
            consulta = consulta.where(Ejemplar.estado == estado)
        return list(self.db.scalars(consulta))

    def primero_disponible(self, libro_id: int, sede_id: int) -> Ejemplar | None:
        consulta = (
            select(Ejemplar)
            .where(
                Ejemplar.libro_id == libro_id,
                Ejemplar.sede_id == sede_id,
                Ejemplar.estado == EstadoEjemplar.DISPONIBLE,
            )
            .order_by(Ejemplar.id)
            .limit(1)
        )
        return self.db.scalar(consulta)
