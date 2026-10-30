from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EstadoEjemplar, EstadoFisico
from app.schemas.resumen import LibroResumen, SedeResumen


class LibroBase(BaseModel):
    isbn: str = Field(min_length=10, max_length=20)
    titulo: str = Field(min_length=1, max_length=200)
    autor: str = Field(min_length=1, max_length=150)
    editorial: str | None = Field(default=None, max_length=100)
    anio_publicacion: int | None = Field(default=None, ge=1400, le=2100)
    genero: str | None = Field(default=None, max_length=60)


class LibroCrear(LibroBase):
    pass


class LibroActualizar(LibroBase):
    pass


class LibroRespuesta(LibroBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class EjemplarCrear(BaseModel):
    codigo_inventario: str = Field(min_length=1, max_length=30)
    libro_id: int
    sede_id: int
    estado_fisico: EstadoFisico = EstadoFisico.BUENO


class EjemplarRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    codigo_inventario: str
    libro_id: int
    sede_id: int
    estado: EstadoEjemplar
    estado_fisico: EstadoFisico
    libro: LibroResumen
    sede: SedeResumen


class DisponibilidadSede(BaseModel):
    sede_id: int
    sede: str
    total: int
    disponibles: int
    ejemplares_disponibles: list[str]


class DisponibilidadLibro(BaseModel):
    libro_id: int
    titulo: str
    total_disponibles: int
    sedes: list[DisponibilidadSede]
