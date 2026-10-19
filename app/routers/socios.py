from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.socio import SocioActualizar, SocioCrear, SocioInhabilitar, SocioRespuesta
from app.services.socio_service import SocioService

router = APIRouter(prefix="/socios", tags=["Socios"])


def get_service(db: Session = Depends(get_db)) -> SocioService:
    return SocioService(db)


@router.get("", response_model=list[SocioRespuesta])
def listar_socios(
    q: str | None = None, habilitado: bool | None = None, service: SocioService = Depends(get_service)
):
    """Busca por nombre, apellido o DNI (`q`) y/o por estado."""
    return service.listar(q, habilitado)


@router.get("/{socio_id}", response_model=SocioRespuesta)
def obtener_socio(socio_id: int, service: SocioService = Depends(get_service)):
    return service.obtener(socio_id)


@router.post("", response_model=SocioRespuesta, status_code=status.HTTP_201_CREATED)
def crear_socio(datos: SocioCrear, service: SocioService = Depends(get_service)):
    """Alta de socio. DNI y email son unicos."""
    return service.crear(datos)


@router.put("/{socio_id}", response_model=SocioRespuesta)
def actualizar_socio(socio_id: int, datos: SocioActualizar, service: SocioService = Depends(get_service)):
    return service.actualizar(socio_id, datos)


@router.patch("/{socio_id}/inhabilitar", response_model=SocioRespuesta)
def inhabilitar_socio(socio_id: int, datos: SocioInhabilitar, service: SocioService = Depends(get_service)):
    """Un socio inhabilitado no puede pedir prestamos ni hacer reservas."""
    return service.inhabilitar(socio_id, datos.motivo)


@router.patch("/{socio_id}/habilitar", response_model=SocioRespuesta)
def habilitar_socio(socio_id: int, service: SocioService = Depends(get_service)):
    return service.habilitar(socio_id)
