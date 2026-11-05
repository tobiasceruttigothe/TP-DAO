from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.routers.dependencias import SOLO_ADMIN
from app.schemas.proceso import ResultadoProcesoRespuesta
from app.services.proceso_service import ProcesoVencimientos

router = APIRouter(prefix="/procesos", tags=["Procesos"], dependencies=SOLO_ADMIN)


@router.post("/vencimientos", response_model=ResultadoProcesoRespuesta)
def procesar_vencimientos(db: Session = Depends(get_db)):
    """Vence las reservas no retiradas e inhabilita a los socios con atrasos largos.
    La API lo ejecuta sola periodicamente; este endpoint permite correrlo en el momento."""
    return ProcesoVencimientos(db).ejecutar()
