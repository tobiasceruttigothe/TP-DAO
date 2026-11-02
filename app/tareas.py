"""Ejecucion periodica del proceso de vencimientos mientras la API esta levantada."""
import asyncio
import logging

from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.database import SessionLocal
from app.services.proceso_service import ProcesoVencimientos

log = logging.getLogger("uvicorn.error")


def correr_proceso():
    db = SessionLocal()
    try:
        resultado = ProcesoVencimientos(db).ejecutar()
        log.info(
            "Proceso de vencimientos: %s reservas vencidas, %s socios inhabilitados",
            resultado.reservas_vencidas,
            len(resultado.socios_inhabilitados),
        )
    finally:
        db.close()


async def proceso_periodico():
    while True:
        try:
            await run_in_threadpool(correr_proceso)
        except Exception:
            # Un fallo puntual (por ejemplo, la base todavia no responde) no debe frenar los siguientes
            log.exception("Fallo el proceso de vencimientos")
        await asyncio.sleep(settings.intervalo_proceso_minutos * 60)
