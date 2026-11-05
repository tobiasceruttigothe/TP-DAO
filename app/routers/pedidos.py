from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.enums import EstadoPedido
from app.repositories.base import Paginacion
from app.routers.dependencias import SOLO_ADMIN, paginacion
from app.schemas.paginacion import Pagina
from app.schemas.pedido import EnvioPedido, PedidoRespuesta, RechazoPedido
from app.services.pedido_service import PedidoService

router = APIRouter(prefix="/pedidos", tags=["Pedidos"], dependencies=SOLO_ADMIN)


def get_service(db: Session = Depends(get_db)) -> PedidoService:
    return PedidoService(db)


@router.get("", response_model=Pagina[PedidoRespuesta])
def listar_pedidos(
    estado: EstadoPedido | None = None,
    socio_id: int | None = None,
    pag: Paginacion = Depends(paginacion),
    service: PedidoService = Depends(get_service),
):
    return Pagina[PedidoRespuesta].desde(service.listar(pag, socio_id, estado))


@router.get("/{pedido_id}", response_model=PedidoRespuesta)
def obtener_pedido(pedido_id: int, service: PedidoService = Depends(get_service)):
    return service.obtener(pedido_id)


@router.post("/{pedido_id}/reservar", response_model=PedidoRespuesta)
def aprobar_con_reserva(pedido_id: int, service: PedidoService = Depends(get_service)):
    """Lo reserva en la sede pedida (listo para retirar si hay un ejemplar libre, o en espera)."""
    return service.reservar(pedido_id)


@router.post("/{pedido_id}/enviar", response_model=PedidoRespuesta)
def aprobar_con_envio(pedido_id: int, datos: EnvioPedido, service: PedidoService = Depends(get_service)):
    """Lo trae desde otra sede: crea el préstamo entre sedes y su remito."""
    return service.enviar_desde(pedido_id, datos.sede_origen_id)


@router.post("/{pedido_id}/rechazar", response_model=PedidoRespuesta)
def rechazar_pedido(pedido_id: int, datos: RechazoPedido, service: PedidoService = Depends(get_service)):
    return service.rechazar(pedido_id, datos.motivo)
