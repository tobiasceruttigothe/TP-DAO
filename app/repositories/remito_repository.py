from sqlalchemy import func, select

from app.models import Remito
from app.repositories.base import BaseRepository


class RemitoRepository(BaseRepository[Remito]):
    modelo = Remito

    def buscar_por_numero(self, numero: str) -> Remito | None:
        return self.db.scalar(select(Remito).where(Remito.numero == numero))

    def listar_filtrado(self, estado: str | None = None, sede_id: int | None = None) -> list[Remito]:
        consulta = select(Remito).order_by(Remito.id.desc())
        if estado:
            consulta = consulta.where(Remito.estado == estado)
        if sede_id is not None:
            consulta = consulta.where((Remito.sede_origen_id == sede_id) | (Remito.sede_destino_id == sede_id))
        return list(self.db.scalars(consulta))

    def siguiente_numero(self) -> str:
        ultimo = self.db.scalar(select(func.max(Remito.id))) or 0
        return f"R-{ultimo + 1:06d}"
