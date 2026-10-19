from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import BibliotecaError, DuplicadoError, NoEncontradoError, ReglaNegocioError
from app.routers import catalogo, prestamos, remitos, reportes, reservas, sedes, socios

app = FastAPI(
    title="Biblioteca - Prestamos Interbibliotecarios",
    description="API del TP integrador de DAO.",
    version="1.0.0",
)

app.include_router(sedes.router)
app.include_router(socios.router)
app.include_router(catalogo.libros_router)
app.include_router(catalogo.ejemplares_router)
app.include_router(prestamos.router)
app.include_router(remitos.router)
app.include_router(reservas.router)
app.include_router(reportes.router)

_CODIGOS = {
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
