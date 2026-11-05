from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.domain.enums import TipoNotificacion


class NotificacionRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tipo: TipoNotificacion
    titulo: str
    mensaje: str
    enlace: str | None
    leida: bool
    fecha: datetime


class CantidadNoLeidas(BaseModel):
    no_leidas: int
