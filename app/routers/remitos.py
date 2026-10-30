from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.enums import TipoIncidencia
from app.repositories.base import Paginacion
from app.routers.dependencias import paginacion
from app.schemas.paginacion import Pagina
from app.schemas.prestamo import (
    IncidenciaRespuesta,
    RecepcionRemito,
    RemitoDetalle,
    RemitoRespuesta,
    TransicionRemito,
)
from app.services.remito_service import RemitoService

router = APIRouter(prefix="/remitos", tags=["Remitos"])
incidencias_router = APIRouter(prefix="/incidencias", tags=["Remitos"])


def get_service(db: Session = Depends(get_db)) -> RemitoService:
    return RemitoService(db)


@router.get("", response_model=Pagina[RemitoRespuesta])
def listar_remitos(
    estado: str | None = None,
    sede_id: int | None = None,
    pag: Paginacion = Depends(paginacion),
    service: RemitoService = Depends(get_service),
):
    """Filtra por estado (PENDIENTE, EMPAQUETADO, DESPACHADO, RECIBIDO, EXTRAVIADO, CANCELADO) o por sede. Paginado."""
    return Pagina[RemitoRespuesta].desde(service.listar(pag, estado, sede_id))


@router.get("/numero/{numero}", response_model=RemitoDetalle)
def buscar_por_numero(numero: str, service: RemitoService = Depends(get_service)):
    return service.obtener_por_numero(numero)


@router.get("/{remito_id}", response_model=RemitoDetalle)
def obtener_remito(remito_id: int, service: RemitoService = Depends(get_service)):
    """Incluye el historial de estados (trazabilidad)."""
    return service.obtener(remito_id)


@router.post("/{remito_id}/empaquetar", response_model=RemitoDetalle)
def empaquetar(remito_id: int, datos: TransicionRemito | None = None, service: RemitoService = Depends(get_service)):
    return service.empaquetar(remito_id, datos.observacion if datos else None)


@router.post("/{remito_id}/despachar", response_model=RemitoDetalle)
def despachar(remito_id: int, datos: TransicionRemito | None = None, service: RemitoService = Depends(get_service)):
    return service.despachar(remito_id, datos.observacion if datos else None)


@router.post("/{remito_id}/recibir", response_model=RemitoDetalle)
def recibir(remito_id: int, datos: RecepcionRemito | None = None, service: RemitoService = Depends(get_service)):
    """Registra la llegada y la revision del ejemplar. DANADO o DESTRUIDO generan una
    incidencia; DESTRUIDO ademas da de baja el ejemplar y, si es de ida, cancela el prestamo."""
    datos = datos or RecepcionRemito()
    return service.recibir(remito_id, datos.estado_fisico, datos.observacion)


@router.post("/{remito_id}/extraviar", response_model=RemitoDetalle)
def marcar_extraviado(remito_id: int, datos: TransicionRemito | None = None, service: RemitoService = Depends(get_service)):
    return service.marcar_extraviado(remito_id, datos.observacion if datos else None)


@router.post("/{remito_id}/cancelar", response_model=RemitoDetalle)
def cancelar(remito_id: int, datos: TransicionRemito | None = None, service: RemitoService = Depends(get_service)):
    """Solo antes de despachar. Cancela tambien el prestamo y libera el ejemplar."""
    return service.cancelar(remito_id, datos.observacion if datos else None)


@incidencias_router.get("", response_model=Pagina[IncidenciaRespuesta])
def listar_incidencias(
    tipo: TipoIncidencia | None = None,
    sede_id: int | None = None,
    desde: date | None = None,
    hasta: date | None = None,
    pag: Paginacion = Depends(paginacion),
    service: RemitoService = Depends(get_service),
):
    """Danos, destrucciones y extravios registrados en los envios. Paginado."""
    return Pagina[IncidenciaRespuesta].desde(service.listar_incidencias(pag, tipo, sede_id, desde, hasta))
