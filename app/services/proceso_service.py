from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.models import Socio
from app.services.reserva_service import ReservaService
from app.services.socio_service import SocioService


@dataclass
class ResultadoProceso:
    reservas_vencidas: int
    socios_inhabilitados: list[Socio]


class ProcesoVencimientos:
    """Tareas que dependen del paso del tiempo: vencer las reservas no retiradas e
    inhabilitar a los socios con atrasos largos. La API lo corre sola cada cierto
    tiempo (ver app/main.py) y tambien se puede disparar a mano."""

    def __init__(self, db: Session):
        self.db = db

    def ejecutar(self, hoy: date | None = None) -> ResultadoProceso:
        hoy = hoy or date.today()
        reservas = ReservaService(self.db).procesar_vencidas(hoy)
        socios = SocioService(self.db).inhabilitar_por_atraso(hoy)
        self.db.commit()
        return ResultadoProceso(reservas_vencidas=reservas, socios_inhabilitados=socios)
