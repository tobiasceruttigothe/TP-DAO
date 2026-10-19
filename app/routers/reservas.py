from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.enums import EstadoReserva
from app.schemas.reserva import ReservaCrear, ReservaRespuesta
from app.services.reserva_service import ReservaService

router = APIRouter(prefix="/reservas", tags=["Reservas"])


def get_service(db: Session = Depends(get_db)) -> ReservaService:
    return ReservaService(db)


@router.get("", response_model=list[ReservaRespuesta])
def listar_reservas(
    socio_id: int | None = None, estado: EstadoReserva | None = None, service: ReservaService = Depends(get_service)
):
    return service.listar(socio_id, estado)


@router.get("/{reserva_id}", response_model=ReservaRespuesta)
def obtener_reserva(reserva_id: int, service: ReservaService = Depends(get_service)):
    return service.obtener(reserva_id)


@router.post("", response_model=ReservaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_reserva(datos: ReservaCrear, service: ReservaService = Depends(get_service)):
    """Si hay un ejemplar libre en la sede se aparta en el momento (DISPONIBLE).
    Si no, queda PENDIENTE hasta que se libere uno."""
    return service.crear(datos)


@router.post("/{reserva_id}/cancelar", response_model=ReservaRespuesta)
def cancelar_reserva(reserva_id: int, service: ReservaService = Depends(get_service)):
    return service.cancelar(reserva_id)


@router.post("/procesar-vencidas")
def procesar_vencidas(service: ReservaService = Depends(get_service)) -> dict:
    """Vence las reservas no retiradas a tiempo y libera sus ejemplares."""
    return {"reservas_vencidas": service.procesar_vencidas()}
