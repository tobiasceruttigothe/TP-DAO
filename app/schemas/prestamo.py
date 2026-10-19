from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EstadoFisico, EstadoPrestamo, TipoPrestamo, TipoRemito


class PrestamoCrear(BaseModel):
    socio_id: int
    ejemplar_id: int
    sede_origen_id: int = Field(description="Sede duena del ejemplar")
    sede_destino_id: int = Field(description="Sede donde retira el socio; igual a origen si es local")


class DevolucionCrear(BaseModel):
    estado_fisico: EstadoFisico
    observaciones: str | None = Field(default=None, max_length=300)
    fecha_devolucion: date | None = Field(default=None, description="Por defecto, la fecha actual")


class PrestamoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    socio_id: int
    ejemplar_id: int
    sede_origen_id: int
    sede_destino_id: int
    tipo: TipoPrestamo
    estado: EstadoPrestamo
    fecha_solicitud: date
    fecha_inicio: date | None
    fecha_vencimiento: date | None
    fecha_devolucion: date | None
    estado_fisico_devolucion: EstadoFisico | None
    multa: float
    observaciones: str | None


class MovimientoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    estado_anterior: str | None
    estado_nuevo: str
    fecha: datetime
    observacion: str | None


class RemitoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    numero: str
    tipo: TipoRemito
    prestamo_id: int
    ejemplar_id: int
    sede_origen_id: int
    sede_destino_id: int
    estado: str
    fecha_creacion: datetime
    fecha_despacho: datetime | None
    fecha_recepcion: datetime | None
    estado_fisico_recepcion: EstadoFisico | None


class RemitoDetalle(RemitoRespuesta):
    movimientos: list[MovimientoRespuesta]


class TransicionRemito(BaseModel):
    observacion: str | None = Field(default=None, max_length=300)


class RecepcionRemito(TransicionRemito):
    estado_fisico: EstadoFisico = EstadoFisico.BUENO
