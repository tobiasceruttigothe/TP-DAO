from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums import EstadoPedido
from app.schemas.resumen import LibroResumen, SedeResumen, SocioResumen
from app.schemas.validaciones import texto, texto_opcional


class PedidoCrear(BaseModel):
    libro_id: int
    sede_id: int
    comentario: texto_opcional(300) = None


class EnvioPedido(BaseModel):
    sede_origen_id: int


class RechazoPedido(BaseModel):
    motivo: texto(3, 300)


class PedidoRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    estado: EstadoPedido
    fecha: datetime
    comentario: str | None
    resolucion: str | None
    fecha_resolucion: datetime | None
    reserva_id: int | None
    prestamo_id: int | None
    socio: SocioResumen
    libro: LibroResumen
    sede: SedeResumen
