from fastapi import Depends, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.exceptions import NoAutorizadoError, SinPermisoError
from app.models import Socio, Usuario
from app.repositories.base import Paginacion
from app.services.cuenta_service import CuentaService

# El frontend manda el token en el encabezado "Authorization: Bearer <token>"
esquema_bearer = HTTPBearer(auto_error=False, description="Token que devuelve POST /auth/ingresar")


def paginacion(
    pagina: int = Query(default=1, ge=1, description="Numero de pagina, desde 1"),
    tamanio: int = Query(default=20, ge=1, le=100, description="Elementos por pagina (maximo 100)"),
) -> Paginacion:
    return Paginacion(pagina=pagina, tamanio=tamanio)


def usuario_actual(
    credenciales: HTTPAuthorizationCredentials | None = Depends(esquema_bearer), db: Session = Depends(get_db)
) -> Usuario:
    if credenciales is None:
        raise NoAutorizadoError("Tenés que iniciar sesión")
    return CuentaService(db).usuario_de_token(credenciales.credentials)


def requiere_admin(usuario: Usuario = Depends(usuario_actual)) -> Usuario:
    if not usuario.es_admin:
        raise SinPermisoError("Solo el personal de la biblioteca puede hacer esto")
    return usuario


def socio_actual(usuario: Usuario = Depends(usuario_actual)) -> Socio:
    if usuario.socio is None:
        raise SinPermisoError("Esta sección es para socios")
    return usuario.socio


# Para proteger un router o un endpoint completo: dependencies=SOLO_ADMIN
SOLO_ADMIN = [Depends(requiere_admin)]
