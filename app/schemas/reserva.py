from datetime import date

from pydantic import BaseModel, ConfigDict

from app.domain.enums import EstadoReserva


class ReservaCrear(BaseModel):
    socio_id: int
    libro_id: int
    sede_id: int


class ReservaRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    socio_id: int
    libro_id: int
    sede_id: int
    ejemplar_id: int | None
    estado: EstadoReserva
    fecha_reserva: date
    fecha_expiracion: date | None
