import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.exceptions import (
    BibliotecaError,
    DuplicadoError,
    NoAutorizadoError,
    NoEncontradoError,
    ReglaNegocioError,
    SinPermisoError,
)
from app.database import SessionLocal
from app.routers import (
    auth,
    catalogo,
    inventarios,
    mi,
    notificaciones,
    pedidos,
    prestamos,
    procesos,
    remitos,
    reportes,
    reservas,
    sedes,
    socios,
    usuarios,
)
from app.services.cuenta_service import CuentaService
from app.tareas import proceso_periodico

def crear_admin_inicial():
    db = SessionLocal()
    try:
        CuentaService(db).asegurar_admin()
    finally:
        db.close()


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    if settings.crear_admin_al_iniciar:
        crear_admin_inicial()
    tarea = asyncio.create_task(proceso_periodico()) if settings.proceso_automatico else None
    yield
    if tarea:
        tarea.cancel()


app = FastAPI(
    title="Biblioteca - Prestamos Interbibliotecarios",
    description="API del TP integrador de DAO.",
    version="1.0.0",
    lifespan=ciclo_de_vida,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.lista_cors_origenes,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(mi.router)
app.include_router(notificaciones.router)
app.include_router(sedes.router)
app.include_router(socios.router)
app.include_router(catalogo.libros_router)
app.include_router(catalogo.ejemplares_router)
app.include_router(prestamos.router)
app.include_router(remitos.router)
app.include_router(remitos.incidencias_router)
app.include_router(reservas.router)
app.include_router(reportes.router)
app.include_router(procesos.router)
app.include_router(pedidos.router)
app.include_router(usuarios.router)
app.include_router(inventarios.router)

_CODIGOS = {
    NoAutorizadoError: 401,
    SinPermisoError: 403,
    NoEncontradoError: 404,
    DuplicadoError: 409,
    ReglaNegocioError: 400,
}


@app.exception_handler(BibliotecaError)
def manejar_error(request: Request, exc: BibliotecaError):
    codigo = next((c for tipo, c in _CODIGOS.items() if isinstance(exc, tipo)), 400)
    return JSONResponse(status_code=codigo, content={"detail": exc.mensaje})


@app.get("/health", tags=["Sistema"])
def health():
    return {"status": "ok"}
