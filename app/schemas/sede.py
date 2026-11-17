from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.schemas.validaciones import PrefijoSede, Telefono, texto, texto_opcional


class SedeBase(BaseModel):
    nombre: texto(2, 100)
    direccion: texto(3, 200)
    telefono: Telefono = Field(default=None, description="Solo números, entre 6 y 15 dígitos")
    email: EmailStr | None = None
    horario: texto_opcional(200) = Field(default=None, examples=["Lun a Vie 8 a 20"])


class SedeCrear(SedeBase):
    prefijo: PrefijoSede = Field(
        description="De 2 a 5 letras. Encabeza los códigos de sus ejemplares y no se puede cambiar",
        examples=["CEN"],
    )


class SedeActualizar(SedeBase):
    """Sin prefijo: los codigos ya impresos en las etiquetas dependen de el."""


class SedeRespuesta(BaseModel):
    """Lo que devuelve la API. No valida formato: muestra lo que hay en la base."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nombre: str
    prefijo: str
    direccion: str
    telefono: str | None
    email: str | None
    horario: str | None
    activa: bool
