from fastapi import Query

from app.repositories.base import Paginacion


def paginacion(
    pagina: int = Query(default=1, ge=1, description="Numero de pagina, desde 1"),
    tamanio: int = Query(default=20, ge=1, le=100, description="Elementos por pagina (maximo 100)"),
) -> Paginacion:
    return Paginacion(pagina=pagina, tamanio=tamanio)
