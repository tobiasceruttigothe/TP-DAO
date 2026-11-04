from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EstadoInventario
from app.schemas.resumen import SedeResumen
from app.schemas.validaciones import texto, texto_opcional


class InventarioCrear(BaseModel):
    sede_id: int
    observacion: texto_opcional(300) = None


class CodigoRegistrar(BaseModel):
    codigo: texto(1, 30) = Field(description="Código de inventario del ejemplar (se puede escanear)")


class FilaInforme(BaseModel):
    codigo: str
    ejemplar_id: int | None = None
    titulo: str | None = None
    estado: str | None = None
    detalle: str | None = None


class Informe(BaseModel):
    encontrados: list[FilaInforme]
    faltantes: list[FilaInforme]
    fuera_de_lugar: list[FilaInforme]
    desconocidos: list[FilaInforme]


class ResultadoCodigo(BaseModel):
    """Respuesta inmediata al registrar un codigo, para avisar mientras se escanea."""

    item_id: int
    codigo: str
    resultado: str = Field(description="ENCONTRADO | FUERA_DE_LUGAR | DESCONOCIDO")
    detalle: str


class InventarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sede: SedeResumen
    estado: EstadoInventario
    fecha_inicio: datetime
    fecha_cierre: datetime | None
    observacion: str | None
    cantidad_registrados: int


class InventarioDetalle(InventarioRespuesta):
    esperados: int
    informe: Informe
