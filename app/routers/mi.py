from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.enums import EstadoPedido
from app.exceptions import SinPermisoError
from app.models import Socio
from app.repositories.base import Paginacion
from app.routers.dependencias import paginacion, socio_actual
from app.schemas.paginacion import Pagina
from app.schemas.pedido import PedidoCrear, PedidoRespuesta
from app.schemas.prestamo import LecturaRespuesta, PrestamoRespuesta
from app.schemas.reserva import ReservaRespuesta
from app.schemas.socio import SocioRespuesta
from app.services.pedido_service import PedidoService
from app.services.prestamo_service import PrestamoService
from app.services.reserva_service import ReservaService

router = APIRouter(prefix="/mi", tags=["Área del socio"])


@router.get("/socio", response_model=SocioRespuesta)
def mis_datos(socio: Socio = Depends(socio_actual)):
    return socio


@router.get("/prestamos", response_model=Pagina[PrestamoRespuesta])
def mis_prestamos(pag: Paginacion = Depends(paginacion), socio: Socio = Depends(socio_actual), db: Session = Depends(get_db)):
    return Pagina[PrestamoRespuesta].desde(PrestamoService(db).listar(pag, socio.id))


@router.get("/reservas", response_model=Pagina[ReservaRespuesta])
def mis_reservas(pag: Paginacion = Depends(paginacion), socio: Socio = Depends(socio_actual), db: Session = Depends(get_db)):
    return Pagina[ReservaRespuesta].desde(ReservaService(db).listar(pag, socio.id))


@router.post("/reservas/{reserva_id}/cancelar", response_model=ReservaRespuesta)
def cancelar_mi_reserva(reserva_id: int, socio: Socio = Depends(socio_actual), db: Session = Depends(get_db)):
    servicio = ReservaService(db)
    if servicio.obtener(reserva_id).socio_id != socio.id:
        raise SinPermisoError("La reserva no es tuya")
    return servicio.cancelar(reserva_id)


@router.get("/historial", response_model=Pagina[LecturaRespuesta])
def mi_historial(pag: Paginacion = Depends(paginacion), socio: Socio = Depends(socio_actual), db: Session = Depends(get_db)):
    """Libros que ya leiste (prestamos devueltos)."""
    resultado = PrestamoService(db).historial_de_socio(socio.id, pag)
    return Pagina[LecturaRespuesta].desde(resultado, [LecturaRespuesta.desde_prestamo(p) for p in resultado.items])


@router.get("/pedidos", response_model=Pagina[PedidoRespuesta])
def mis_pedidos(
    estado: EstadoPedido | None = None,
    pag: Paginacion = Depends(paginacion),
    socio: Socio = Depends(socio_actual),
    db: Session = Depends(get_db),
):
    return Pagina[PedidoRespuesta].desde(PedidoService(db).listar(pag, socio.id, estado))


@router.post("/pedidos", response_model=PedidoRespuesta, status_code=status.HTTP_201_CREATED)
def hacer_pedido(datos: PedidoCrear, socio: Socio = Depends(socio_actual), db: Session = Depends(get_db)):
    """Pedir un libro para retirar en una sede. La biblioteca lo revisa y avisa por notificación."""
    return PedidoService(db).crear(socio, datos)


@router.post("/pedidos/{pedido_id}/cancelar", response_model=PedidoRespuesta)
def cancelar_mi_pedido(pedido_id: int, socio: Socio = Depends(socio_actual), db: Session = Depends(get_db)):
    return PedidoService(db).cancelar(socio, pedido_id)
