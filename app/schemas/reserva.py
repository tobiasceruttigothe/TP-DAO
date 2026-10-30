from datetime import date

from pydantic import BaseModel, ConfigDict

from app.domain.enums import EstadoReserva
from app.schemas.resumen import EjemplarResumen, LibroResumen, SedeResumen, SocioResumen


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
    socio: SocioResumen
    libro: LibroResumen
    sede: SedeResumen
    ejemplar: EjemplarResumen | None
