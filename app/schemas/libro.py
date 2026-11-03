from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EstadoEjemplar, EstadoFisico
from app.schemas.resumen import LibroResumen, SedeResumen
from app.schemas.validaciones import AnioPublicacion, Isbn, texto, texto_opcional


class LibroBase(BaseModel):
    isbn: Isbn = Field(description="ISBN-10 o ISBN-13; se aceptan guiones, que se quitan")
    titulo: texto(1, 200)
    autor: texto(2, 150)
    editorial: texto_opcional(100) = None
    anio_publicacion: AnioPublicacion = None
    genero: texto_opcional(60) = None


class LibroCrear(LibroBase):
    pass


class LibroActualizar(LibroBase):
    pass


class LibroRespuesta(BaseModel):
    """Lo que devuelve la API. No valida formato: muestra lo que hay en la base."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn: str
    titulo: str
    autor: str
    editorial: str | None
    anio_publicacion: int | None
    genero: str | None


class EjemplarCrear(BaseModel):
    codigo_inventario: texto(1, 30)
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
