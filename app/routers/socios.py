from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.base import Paginacion
from app.routers.dependencias import paginacion
from app.schemas.paginacion import Pagina
from app.schemas.prestamo import LecturaRespuesta
from app.schemas.socio import SocioActualizar, SocioCrear, SocioInhabilitar, SocioRespuesta
from app.services.prestamo_service import PrestamoService
from app.services.socio_service import SocioService

router = APIRouter(prefix="/socios", tags=["Socios"])


def get_service(db: Session = Depends(get_db)) -> SocioService:
    return SocioService(db)


@router.get("", response_model=Pagina[SocioRespuesta])
def listar_socios(
    q: str | None = None,
    habilitado: bool | None = None,
    pag: Paginacion = Depends(paginacion),
    service: SocioService = Depends(get_service),
):
    """Busca por nombre, apellido o DNI (`q`) y/o por estado. Paginado."""
    return Pagina[SocioRespuesta].desde(service.listar(pag, q, habilitado))


@router.get("/{socio_id}", response_model=SocioRespuesta)
def obtener_socio(socio_id: int, service: SocioService = Depends(get_service)):
    return service.obtener(socio_id)


@router.get("/{socio_id}/historial", response_model=Pagina[LecturaRespuesta])
def historial_de_lecturas(socio_id: int, pag: Paginacion = Depends(paginacion), db: Session = Depends(get_db)):
    """Libros que el socio ya leyo (prestamos devueltos), del mas reciente al mas antiguo. Paginado."""
    resultado = PrestamoService(db).historial_de_socio(socio_id, pag)
    lecturas = [LecturaRespuesta.desde_prestamo(p) for p in resultado.items]
    return Pagina[LecturaRespuesta].desde(resultado, lecturas)


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
