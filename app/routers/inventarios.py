from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.base import Paginacion
from app.routers.dependencias import SOLO_ADMIN, paginacion
from app.schemas.inventario import CodigoRegistrar, InventarioCrear, InventarioDetalle, InventarioRespuesta, ResultadoCodigo
from app.schemas.paginacion import Pagina
from app.services.inventario_service import InventarioService

router = APIRouter(prefix="/inventarios", tags=["Inventario"], dependencies=SOLO_ADMIN)


def get_service(db: Session = Depends(get_db)) -> InventarioService:
    return InventarioService(db)


@router.get("", response_model=Pagina[InventarioRespuesta])
def listar_inventarios(
    sede_id: int | None = None, pag: Paginacion = Depends(paginacion), service: InventarioService = Depends(get_service)
):
    return Pagina[InventarioRespuesta].desde(service.listar(pag, sede_id))


@router.post("", response_model=InventarioRespuesta, status_code=status.HTTP_201_CREATED)
def iniciar_inventario(datos: InventarioCrear, service: InventarioService = Depends(get_service)):
    """Empieza un recuento en una sede. Solo puede haber uno en curso por sede."""
    return service.iniciar(datos.sede_id, datos.observacion)


@router.get("/{inventario_id}", response_model=InventarioDetalle)
def detalle_inventario(inventario_id: int, service: InventarioService = Depends(get_service)):
    """Incluye el informe: encontrados, faltantes, fuera de lugar y desconocidos."""
    return service.detalle(inventario_id)


@router.post("/{inventario_id}/codigos", response_model=ResultadoCodigo, status_code=status.HTTP_201_CREATED)
def registrar_codigo(inventario_id: int, datos: CodigoRegistrar, service: InventarioService = Depends(get_service)):
    """Registra un código encontrado en el estante (se puede escanear con un lector de código de barras)."""
    return service.registrar_codigo(inventario_id, datos.codigo)


@router.delete("/{inventario_id}/codigos/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_codigo(inventario_id: int, item_id: int, service: InventarioService = Depends(get_service)):
    service.quitar_codigo(inventario_id, item_id)


@router.post("/{inventario_id}/cerrar", response_model=InventarioDetalle)
def cerrar_inventario(inventario_id: int, service: InventarioService = Depends(get_service)):
    """Cierra el recuento y guarda el informe final."""
    service.cerrar(inventario_id)
    return service.detalle(inventario_id)
