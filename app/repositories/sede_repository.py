from sqlalchemy import select

from app.models import Sede
from app.repositories.base import BaseRepository


class SedeRepository(BaseRepository[Sede]):
    modelo = Sede

    def buscar_por_nombre(self, nombre: str) -> Sede | None:
        return self.db.scalar(select(Sede).where(Sede.nombre.ilike(nombre)))

    def listar_filtrado(self, activa: bool | None = None) -> list[Sede]:
        consulta = select(Sede).order_by(Sede.nombre)
        if activa is not None:
            consulta = consulta.where(Sede.activa == activa)
        return list(self.db.scalars(consulta))
