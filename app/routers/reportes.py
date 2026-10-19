from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.reporte import (
    DisponibilidadSedeItem,
    LibroSolicitadoItem,
    MovimientoSedesItem,
    ReporteActivosYTransito,
    ReporteEnvios,
    ReporteVencidosYMultas,
)
from app.services.reporte_service import ReporteService

router = APIRouter(prefix="/reportes", tags=["Reportes"])


def get_service(db: Session = Depends(get_db)) -> ReporteService:
    return ReporteService(db)


@router.get("/prestamos-activos", response_model=ReporteActivosYTransito)
def prestamos_activos_y_transito(service: ReporteService = Depends(get_service)):
    """Prestamos activos y ejemplares que estan viajando entre sedes."""
    return service.activos_y_en_transito()


@router.get("/vencidos-multas", response_model=ReporteVencidosYMultas)
def vencidos_y_multas(fecha: date | None = None, service: ReporteService = Depends(get_service)):
    """Prestamos vencidos y multas acumuladas por socio (cobradas + pendientes a la fecha)."""
    return service.vencidos_y_multas(fecha)


@router.get("/libros-mas-solicitados", response_model=list[LibroSolicitadoItem])
def libros_mas_solicitados(
    desde: date | None = None,
    hasta: date | None = None,
    limite: int = Query(default=10, ge=1, le=100),
    service: ReporteService = Depends(get_service),
):
    """Ranking de libros pedidos en prestamos inter-sedes."""
    return service.libros_mas_solicitados_intersede(desde, hasta, limite)


@router.get("/disponibilidad-sedes", response_model=list[DisponibilidadSedeItem])
def disponibilidad_por_sede(service: ReporteService = Depends(get_service)):
    """Ejemplares por sede agrupados por estado y porcentaje disponible."""
    return service.disponibilidad_por_sede()


@router.get("/envios", response_model=ReporteEnvios)
def tasa_envios(desde: date | None = None, hasta: date | None = None, service: ReporteService = Depends(get_service)):
    """Tasa de envios exitosos e incidencias (extravios y recepciones con danio)."""
    return service.tasa_envios(desde, hasta)


@router.get("/movimientos-sedes", response_model=list[MovimientoSedesItem])
def movimiento_entre_sedes(
    desde: date | None = None, hasta: date | None = None, service: ReporteService = Depends(get_service)
):
    """Envios por par origen/destino y tiempo promedio de transito en horas."""
    return service.movimiento_entre_sedes(desde, hasta)
