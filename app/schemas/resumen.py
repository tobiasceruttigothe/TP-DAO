"""Versiones cortas de las entidades para incluir dentro de otras respuestas,
asi el frontend no necesita una consulta extra por cada fila."""
from pydantic import BaseModel, ConfigDict


class Resumen(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class SedeResumen(Resumen):
    id: int
    nombre: str


class SocioResumen(Resumen):
    id: int
    dni: str
    nombre: str
    apellido: str


class LibroResumen(Resumen):
    id: int
    titulo: str
    autor: str


class EjemplarResumen(Resumen):
    id: int
    codigo_inventario: str
    libro: LibroResumen


class RemitoResumen(Resumen):
    id: int
    numero: str
    sede_origen: SedeResumen
    sede_destino: SedeResumen
