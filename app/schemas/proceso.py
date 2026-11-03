from pydantic import BaseModel

from app.schemas.socio import SocioRespuesta


class ResultadoProcesoRespuesta(BaseModel):
    model_config = {"from_attributes": True}

    reservas_vencidas: int
    socios_inhabilitados: list[SocioRespuesta]
