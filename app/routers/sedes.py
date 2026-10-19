from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.sede import SedeActualizar, SedeCrear, SedeRespuesta
from app.services.sede_service import SedeService

router = APIRouter(prefix="/sedes", tags=["Sedes"])


def get_service(db: Session = Depends(get_db)) -> SedeService:
    return SedeService(db)


@router.get("", response_model=list[SedeRespuesta])
def listar_sedes(activa: bool | None = None, service: SedeService = Depends(get_service)):
    """Lista las sedes. Con `activa` se filtra por estado."""
    return service.listar(activa)


@router.get("/{sede_id}", response_model=SedeRespuesta)
def obtener_sede(sede_id: int, service: SedeService = Depends(get_service)):
    return service.obtener(sede_id)


@router.post("", response_model=SedeRespuesta, status_code=status.HTTP_201_CREATED)
def crear_sede(datos: SedeCrear, service: SedeService = Depends(get_service)):
    """Alta de sede. El nombre no puede repetirse."""
    return service.crear(datos)


@router.put("/{sede_id}", response_model=SedeRespuesta)
def actualizar_sede(sede_id: int, datos: SedeActualizar, service: SedeService = Depends(get_service)):
    return service.actualizar(sede_id, datos)


@router.patch("/{sede_id}/baja", response_model=SedeRespuesta)
def dar_de_baja_sede(sede_id: int, service: SedeService = Depends(get_service)):
    """Una sede dada de baja no puede iniciar prestamos, reservas ni envios."""
    return service.dar_de_baja(sede_id)


@router.patch("/{sede_id}/alta", response_model=SedeRespuesta)
def dar_de_alta_sede(sede_id: int, service: SedeService = Depends(get_service)):
    return service.dar_de_alta(sede_id)
