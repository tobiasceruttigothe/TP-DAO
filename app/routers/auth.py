from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Usuario
from app.routers.dependencias import usuario_actual
from app.schemas.usuario import (
    ConfirmacionEmail,
    Credenciales,
    Mensaje,
    ReenvioConfirmacion,
    RegistroCrear,
    Sesion,
    UsuarioRespuesta,
)
from app.services.cuenta_service import CuentaService

router = APIRouter(prefix="/auth", tags=["Cuenta"])


def get_service(db: Session = Depends(get_db)) -> CuentaService:
    return CuentaService(db)


@router.post("/registro", response_model=Mensaje, status_code=status.HTTP_201_CREATED)
def registrarse(datos: RegistroCrear, service: CuentaService = Depends(get_service)):
    """Alta de un socio. Le llega un correo para confirmar el email; despues la biblioteca
    aprueba la cuenta. Si el socio ya estaba cargado (mismo DNI y email), no hace falta aprobacion."""
    service.registrar(datos)
    return {"mensaje": "Te enviamos un correo para confirmar tu email."}


@router.post("/confirmar", response_model=UsuarioRespuesta)
def confirmar_email(datos: ConfirmacionEmail, service: CuentaService = Depends(get_service)):
    """Confirma el email con el token del link que llego por correo."""
    return service.confirmar_email(datos.token)


@router.post("/reenviar-confirmacion", response_model=Mensaje)
def reenviar_confirmacion(datos: ReenvioConfirmacion, service: CuentaService = Depends(get_service)):
    service.reenviar_confirmacion(datos.email)
    return {"mensaje": "Si el email tiene una cuenta sin confirmar, te reenviamos el correo."}


@router.post("/ingresar", response_model=Sesion)
def ingresar(datos: Credenciales, service: CuentaService = Depends(get_service)):
    """Devuelve el token de sesion. Se manda en las siguientes llamadas como
    `Authorization: Bearer <token>`."""
    token, usuario = service.ingresar(datos.email, datos.contrasena)
    return {"token": token, "usuario": usuario}


@router.get("/yo", response_model=UsuarioRespuesta)
def usuario_conectado(usuario: Usuario = Depends(usuario_actual)):
    return usuario
