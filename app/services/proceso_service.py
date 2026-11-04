from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.config import settings
from app.models import Socio
from app.repositories import PrestamoRepository
from app.services.eventos import PrestamoPorVencer, PrestamoVencido, publicador
from app.services.reserva_service import ReservaService
from app.services.socio_service import SocioService


@dataclass
class ResultadoProceso:
    reservas_vencidas: int
    socios_inhabilitados: list[Socio]
    avisos_enviados: int = 0


class ProcesoVencimientos:
    """Tareas que dependen del paso del tiempo: vencer las reservas no retiradas, avisar a
    los socios de los prestamos por vencer o vencidos e inhabilitar a los que tienen
    atrasos largos. La API lo corre sola cada cierto tiempo (ver app/tareas.py) y tambien
    se puede disparar a mano."""

    def __init__(self, db: Session):
        self.db = db

    def ejecutar(self, hoy: date | None = None) -> ResultadoProceso:
        hoy = hoy or date.today()
        reservas = ReservaService(self.db).procesar_vencidas(hoy)
        avisos = self.avisar_vencimientos(hoy)
        socios = SocioService(self.db).inhabilitar_por_atraso(hoy)
        self.db.commit()
        return ResultadoProceso(reservas_vencidas=reservas, socios_inhabilitados=socios, avisos_enviados=avisos)

    def avisar_vencimientos(self, hoy: date) -> int:
        """Un aviso cuando faltan pocos dias y otro cuando ya vencio; cada uno, una sola vez."""
        eventos = publicador(self.db)
        enviados = 0
        for prestamo in PrestamoRepository(self.db).activos():
            dias_restantes = (prestamo.fecha_vencimiento - hoy).days
            if dias_restantes < 0 and not prestamo.aviso_vencido:
                eventos.publicar(PrestamoVencido(prestamo))
                prestamo.aviso_vencido = True
                prestamo.aviso_por_vencer = True
                enviados += 1
            elif 0 <= dias_restantes <= settings.dias_aviso_vencimiento and not prestamo.aviso_por_vencer:
                eventos.publicar(PrestamoPorVencer(prestamo))
                prestamo.aviso_por_vencer = True
                enviados += 1
        self.db.flush()
        return enviados
