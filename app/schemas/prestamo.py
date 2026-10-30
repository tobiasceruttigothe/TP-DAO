from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain.enums import EstadoFisico, EstadoPrestamo, TipoIncidencia, TipoPrestamo, TipoRemito


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


class IncidenciaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    remito_id: int
    tipo: TipoIncidencia
    descripcion: str | None
    fecha: datetime


class RemitoDetalle(RemitoRespuesta):
    movimientos: list[MovimientoRespuesta]
    incidencias: list[IncidenciaRespuesta]


class TransicionRemito(BaseModel):
    observacion: str | None = Field(default=None, max_length=300)


class RecepcionRemito(TransicionRemito):
    estado_fisico: EstadoFisico = Field(
        default=EstadoFisico.BUENO,
        description="Resultado de la revision al recibir. DANADO y DESTRUIDO registran una incidencia",
    )


class LecturaRespuesta(BaseModel):
    """Un prestamo ya devuelto, visto como parte del historial del socio."""

    prestamo_id: int
    libro_id: int
    titulo: str
    autor: str
    tipo: TipoPrestamo
    sede_retiro: str
    fecha_inicio: date
    fecha_devolucion: date
    dias_atraso: int
    multa: float

    @classmethod
    def desde_prestamo(cls, prestamo) -> "LecturaRespuesta":
        libro = prestamo.ejemplar.libro
        return cls(
            prestamo_id=prestamo.id,
            libro_id=libro.id,
            titulo=libro.titulo,
            autor=libro.autor,
            tipo=prestamo.tipo,
            sede_retiro=prestamo.sede_destino.nombre,
            fecha_inicio=prestamo.fecha_inicio,
            fecha_devolucion=prestamo.fecha_devolucion,
            dias_atraso=prestamo.dias_atraso(prestamo.fecha_devolucion),
            multa=prestamo.multa,
        )
