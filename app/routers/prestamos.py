from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.base import Paginacion
from app.routers.dependencias import paginacion
from app.domain.enums import EstadoPrestamo
from app.schemas.paginacion import Pagina
from app.schemas.prestamo import DevolucionCrear, PrestamoCrear, PrestamoRespuesta, RemitoRespuesta
from app.services.prestamo_service import PrestamoService

router = APIRouter(prefix="/prestamos", tags=["Prestamos"])


def get_service(db: Session = Depends(get_db)) -> PrestamoService:
    return PrestamoService(db)


@router.get("", response_model=Pagina[PrestamoRespuesta])
def listar_prestamos(
    socio_id: int | None = None,
    estado: EstadoPrestamo | None = None,
    pag: Paginacion = Depends(paginacion),
    service: PrestamoService = Depends(get_service),
):
    """Del mas reciente al mas antiguo. Paginado."""
    return Pagina[PrestamoRespuesta].desde(service.listar(pag, socio_id, estado))


@router.get("/{prestamo_id}", response_model=PrestamoRespuesta)
def obtener_prestamo(prestamo_id: int, service: PrestamoService = Depends(get_service)):
    return service.obtener(prestamo_id)


@router.get("/{prestamo_id}/remitos", response_model=list[RemitoRespuesta])
def remitos_del_prestamo(prestamo_id: int, service: PrestamoService = Depends(get_service)):
    return service.obtener(prestamo_id).remitos


@router.post("", response_model=PrestamoRespuesta, status_code=status.HTTP_201_CREATED)
def solicitar_prestamo(datos: PrestamoCrear, service: PrestamoService = Depends(get_service)):
    """Si origen y destino son la misma sede el prestamo es local y queda activo.
    Si no, es interbibliotecario: queda SOLICITADO y se genera el remito de ida."""
    return service.solicitar(datos)


@router.post("/{prestamo_id}/devolucion", response_model=PrestamoRespuesta)
def registrar_devolucion(prestamo_id: int, datos: DevolucionCrear, service: PrestamoService = Depends(get_service)):
    """Registra la devolucion, el estado fisico y la multa si hubo atraso.
    En los interbibliotecarios genera el remito de retorno a la sede de origen."""
    return service.devolver(prestamo_id, datos)
