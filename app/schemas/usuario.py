from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.enums import EstadoUsuario, Rol
from app.schemas.resumen import SocioResumen
from app.schemas.validaciones import Contrasena, Dni, NombrePersona, Telefono, texto


class RegistroCrear(BaseModel):
    dni: Dni
    nombre: NombrePersona
    apellido: NombrePersona
    email: EmailStr = Field(max_length=120)
    telefono: Telefono = None
    contrasena: Contrasena = Field(description="Al menos 8 caracteres, con letras y números")


class ConfirmacionEmail(BaseModel):
    token: str


class ReenvioConfirmacion(BaseModel):
    email: EmailStr


class Credenciales(BaseModel):
    email: EmailStr
    contrasena: str


class AdminCrear(BaseModel):
    email: EmailStr = Field(max_length=120)
    nombre: NombrePersona
    contrasena: Contrasena


class Rechazo(BaseModel):
    motivo: texto(3, 200)


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    nombre: str
    rol: Rol
    estado: EstadoUsuario
    fecha_alta: datetime
    motivo_rechazo: str | None
    socio: SocioResumen | None


class Sesion(BaseModel):
    token: str
    usuario: UsuarioRespuesta


class Mensaje(BaseModel):
    mensaje: str
