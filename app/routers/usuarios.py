from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.enums import EstadoUsuario, Rol
from app.repositories.base import Paginacion
from app.routers.dependencias import SOLO_ADMIN, paginacion
from app.schemas.paginacion import Pagina
from app.schemas.usuario import AdminCrear, Rechazo, UsuarioRespuesta
from app.services.cuenta_service import CuentaService

router = APIRouter(prefix="/usuarios", tags=["Usuarios"], dependencies=SOLO_ADMIN)


def get_service(db: Session = Depends(get_db)) -> CuentaService:
    return CuentaService(db)


@router.get("", response_model=Pagina[UsuarioRespuesta])
def listar_usuarios(
    estado: EstadoUsuario | None = None,
    rol: Rol | None = None,
    q: str | None = None,
    pag: Paginacion = Depends(paginacion),
    service: CuentaService = Depends(get_service),
):
    """Cuentas del sistema. Con `estado=PENDIENTE_APROBACION`, los registros a aprobar."""
    return Pagina[UsuarioRespuesta].desde(service.listar(pag, estado, rol, q))


@router.post("/{usuario_id}/aprobar", response_model=UsuarioRespuesta)
def aprobar(usuario_id: int, service: CuentaService = Depends(get_service)):
    """Aprueba el registro: el socio queda habilitado y le llega un aviso."""
    return service.aprobar(usuario_id)


@router.post("/{usuario_id}/rechazar", response_model=UsuarioRespuesta)
def rechazar(usuario_id: int, datos: Rechazo, service: CuentaService = Depends(get_service)):
    return service.rechazar(usuario_id, datos.motivo)


@router.post("/administradores", response_model=UsuarioRespuesta, status_code=status.HTTP_201_CREATED)
def crear_administrador(datos: AdminCrear, service: CuentaService = Depends(get_service)):
    return service.crear_admin(datos)
