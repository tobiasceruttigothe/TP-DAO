from sqlalchemy import select

from app.domain.enums import EstadoPedido
from app.models import Pedido
from app.repositories.base import BaseRepository, Paginacion, ResultadoPaginado


class PedidoRepository(BaseRepository[Pedido]):
    modelo = Pedido

    def listar_filtrado(
        self, paginacion: Paginacion, socio_id: int | None = None, estado: EstadoPedido | None = None
    ) -> ResultadoPaginado[Pedido]:
        consulta = select(Pedido).order_by(Pedido.fecha.desc(), Pedido.id.desc())
        if socio_id is not None:
            consulta = consulta.where(Pedido.socio_id == socio_id)
        if estado is not None:
            consulta = consulta.where(Pedido.estado == estado)
        return self.paginar(consulta, paginacion)

    def pendiente_de_socio(self, socio_id: int, libro_id: int) -> Pedido | None:
        consulta = select(Pedido).where(
            Pedido.socio_id == socio_id, Pedido.libro_id == libro_id, Pedido.estado == EstadoPedido.PENDIENTE
        )
        return self.db.scalar(consulta)
