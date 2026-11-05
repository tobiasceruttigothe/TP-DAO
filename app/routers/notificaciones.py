from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.repositories.base import Paginacion
from app.routers.dependencias import paginacion, usuario_actual
from app.schemas.notificacion import CantidadNoLeidas, NotificacionRespuesta
from app.schemas.paginacion import Pagina
from app.services.notificacion_service import NotificacionService

router = APIRouter(prefix="/notificaciones", tags=["Notificaciones"])


def get_service(db: Session = Depends(get_db)) -> NotificacionService:
    return NotificacionService(db)


@router.get("", response_model=Pagina[NotificacionRespuesta])
def mis_notificaciones(
    solo_no_leidas: bool = False,
    pag: Paginacion = Depends(paginacion),
    usuario: Usuario = Depends(usuario_actual),
    service: NotificacionService = Depends(get_service),
):
    """Notificaciones del usuario conectado (socio o administrador), de la mas nueva a la mas vieja."""
    return Pagina[NotificacionRespuesta].desde(service.listar(usuario, pag, solo_no_leidas))


@router.get("/no-leidas", response_model=CantidadNoLeidas)
def cantidad_no_leidas(usuario: Usuario = Depends(usuario_actual), service: NotificacionService = Depends(get_service)):
    return {"no_leidas": service.contar_no_leidas(usuario)}


@router.post("/{notificacion_id}/leida", response_model=NotificacionRespuesta)
def marcar_leida(
    notificacion_id: int, usuario: Usuario = Depends(usuario_actual), service: NotificacionService = Depends(get_service)
):
    return service.marcar_leida(usuario, notificacion_id)


@router.post("/leer-todas", response_model=CantidadNoLeidas)
def marcar_todas_leidas(usuario: Usuario = Depends(usuario_actual), service: NotificacionService = Depends(get_service)):
    service.marcar_todas_leidas(usuario)
    return {"no_leidas": 0}
