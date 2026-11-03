from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.validaciones import Dni, NombrePersona, Telefono, texto


class SocioBase(BaseModel):
    dni: Dni = Field(description="7 u 8 dígitos; se aceptan puntos, que se quitan")
    nombre: NombrePersona
    apellido: NombrePersona
    email: EmailStr = Field(max_length=120)
    telefono: Telefono = Field(default=None, description="Solo números, entre 6 y 15 dígitos")


class SocioCrear(SocioBase):
    pass


class SocioActualizar(SocioBase):
    pass


class SocioInhabilitar(BaseModel):
    motivo: texto(3, 200)


class SocioRespuesta(BaseModel):
    """Lo que devuelve la API. No valida formato: muestra lo que hay en la base."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    dni: str
    nombre: str
    apellido: str
    email: str
    telefono: str | None
    fecha_alta: date
    habilitado: bool
    motivo_inhabilitacion: str | None
    tiene_vencidos: bool = Field(description="Tiene prestamos vencidos sin devolver (no puede pedir otro)")
