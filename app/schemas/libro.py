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


MAXIMO_EJEMPLARES_POR_CARGA = 50


class EjemplarCrear(BaseModel):
    """El codigo de inventario no se pide: lo asigna el sistema con el prefijo de la sede."""

    libro_id: int
    sede_id: int
    estado_fisico: EstadoFisico = EstadoFisico.BUENO
    cantidad: int = Field(
        default=1, ge=1, le=MAXIMO_EJEMPLARES_POR_CARGA,
        description="Cuántos ejemplares iguales se cargan (misma sede y estado físico)",
    )


class ProximoCodigo(BaseModel):
    codigo: str


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
