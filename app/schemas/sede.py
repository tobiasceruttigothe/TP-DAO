from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SedeBase(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    direccion: str = Field(min_length=3, max_length=200)
    telefono: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    horario: str | None = Field(default=None, max_length=200, examples=["Lun a Vie 8 a 20"])


class SedeCrear(SedeBase):
    pass


class SedeActualizar(SedeBase):
    pass


class SedeRespuesta(SedeBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    activa: bool
