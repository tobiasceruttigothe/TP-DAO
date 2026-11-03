from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.validaciones import Telefono, texto, texto_opcional


class SedeBase(BaseModel):
    nombre: texto(2, 100)
    direccion: texto(3, 200)
    telefono: Telefono = Field(default=None, description="Solo números, entre 6 y 15 dígitos")
    email: EmailStr | None = None
    horario: texto_opcional(200) = Field(default=None, examples=["Lun a Vie 8 a 20"])


class SedeCrear(SedeBase):
    pass


class SedeActualizar(SedeBase):
    pass


class SedeRespuesta(BaseModel):
    """Lo que devuelve la API. No valida formato: muestra lo que hay en la base."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    direccion: str
    telefono: str | None
    email: str | None
    horario: str | None
    activa: bool
