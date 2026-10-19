from datetime import date

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SocioBase(BaseModel):
    dni: str = Field(min_length=6, max_length=20, pattern=r"^\d+$")
    nombre: str = Field(min_length=1, max_length=100)
    apellido: str = Field(min_length=1, max_length=100)
    email: EmailStr
    telefono: str | None = Field(default=None, max_length=30)


class SocioCrear(SocioBase):
    pass


class SocioActualizar(SocioBase):
    pass


class SocioInhabilitar(BaseModel):
    motivo: str = Field(min_length=3, max_length=200)


class SocioRespuesta(SocioBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    fecha_alta: date
    habilitado: bool
    motivo_inhabilitacion: str | None
