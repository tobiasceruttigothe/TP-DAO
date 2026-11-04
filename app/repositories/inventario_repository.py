from sqlalchemy import func, select

from app.domain.enums import EstadoEjemplar, EstadoInventario
from app.models import Ejemplar, Inventario, ItemInventario
from app.repositories.base import BaseRepository, Paginacion, ResultadoPaginado

# Estados en los que el ejemplar deberia estar fisicamente en el estante de su sede
ESTADOS_EN_ESTANTE = (EstadoEjemplar.DISPONIBLE, EstadoEjemplar.RESERVADO, EstadoEjemplar.EN_REPARACION)


class InventarioRepository(BaseRepository[Inventario]):
    modelo = Inventario

    def listar_filtrado(self, paginacion: Paginacion, sede_id: int | None = None) -> ResultadoPaginado[Inventario]:
        consulta = select(Inventario).order_by(Inventario.fecha_inicio.desc(), Inventario.id.desc())
        if sede_id is not None:
            consulta = consulta.where(Inventario.sede_id == sede_id)
        return self.paginar(consulta, paginacion)

    def en_curso_de_sede(self, sede_id: int) -> Inventario | None:
        return self.db.scalar(
            select(Inventario).where(Inventario.sede_id == sede_id, Inventario.estado == EstadoInventario.EN_CURSO)
        )

    def esperados_en_sede(self, sede_id: int) -> list[Ejemplar]:
        consulta = (
            select(Ejemplar)
            .where(Ejemplar.sede_id == sede_id, Ejemplar.estado.in_(ESTADOS_EN_ESTANTE))
            .order_by(Ejemplar.codigo_inventario)
        )
        return list(self.db.scalars(consulta))

    def item_por_codigo(self, inventario_id: int, codigo: str) -> ItemInventario | None:
        return self.db.scalar(
            select(ItemInventario).where(ItemInventario.inventario_id == inventario_id, ItemInventario.codigo == codigo)
        )

    def ejemplar_por_codigo(self, codigo: str) -> Ejemplar | None:
        return self.db.scalar(select(Ejemplar).where(func.upper(Ejemplar.codigo_inventario) == codigo.upper()))
