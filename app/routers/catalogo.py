from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.domain.enums import EstadoEjemplar
from app.schemas.libro import (
    DisponibilidadLibro,
    EjemplarCrear,
    EjemplarRespuesta,
    LibroActualizar,
    LibroCrear,
    LibroRespuesta,
)
from app.services.catalogo_service import CatalogoService

libros_router = APIRouter(prefix="/libros", tags=["Catalogo"])
ejemplares_router = APIRouter(prefix="/ejemplares", tags=["Catalogo"])


def get_service(db: Session = Depends(get_db)) -> CatalogoService:
    return CatalogoService(db)


@libros_router.get("", response_model=list[LibroRespuesta])
def buscar_libros(q: str | None = None, service: CatalogoService = Depends(get_service)):
    """Busca libros por titulo o autor."""
    return service.buscar_libros(q)


@libros_router.get("/{libro_id}", response_model=LibroRespuesta)
def obtener_libro(libro_id: int, service: CatalogoService = Depends(get_service)):
    return service.obtener_libro(libro_id)


@libros_router.post("", response_model=LibroRespuesta, status_code=status.HTTP_201_CREATED)
def crear_libro(datos: LibroCrear, service: CatalogoService = Depends(get_service)):
    """Alta de libro en el catalogo. El ISBN es unico."""
    return service.crear_libro(datos)


@libros_router.put("/{libro_id}", response_model=LibroRespuesta)
def actualizar_libro(libro_id: int, datos: LibroActualizar, service: CatalogoService = Depends(get_service)):
    return service.actualizar_libro(libro_id, datos)


@libros_router.get("/{libro_id}/disponibilidad", response_model=DisponibilidadLibro)
def consultar_disponibilidad(libro_id: int, service: CatalogoService = Depends(get_service)):
    """Cuantos ejemplares hay y cuantos estan disponibles en cada sede activa."""
    return service.disponibilidad(libro_id)


@ejemplares_router.get("", response_model=list[EjemplarRespuesta])
def listar_ejemplares(
    libro_id: int | None = None,
    sede_id: int | None = None,
    estado: EstadoEjemplar | None = None,
    service: CatalogoService = Depends(get_service),
):
    return service.listar_ejemplares(libro_id, sede_id, estado)


@ejemplares_router.get("/{ejemplar_id}", response_model=EjemplarRespuesta)
def obtener_ejemplar(ejemplar_id: int, service: CatalogoService = Depends(get_service)):
    return service.obtener_ejemplar(ejemplar_id)


@ejemplares_router.post("", response_model=EjemplarRespuesta, status_code=status.HTTP_201_CREATED)
def crear_ejemplar(datos: EjemplarCrear, service: CatalogoService = Depends(get_service)):
    """Alta de un ejemplar fisico en una sede. El codigo de inventario es unico."""
    return service.crear_ejemplar(datos)


@ejemplares_router.patch("/{ejemplar_id}/baja", response_model=EjemplarRespuesta)
def dar_de_baja_ejemplar(ejemplar_id: int, service: CatalogoService = Depends(get_service)):
    """Solo se pueden dar de baja ejemplares disponibles o en reparacion."""
    return service.dar_de_baja_ejemplar(ejemplar_id)


@ejemplares_router.patch("/{ejemplar_id}/reparado", response_model=EjemplarRespuesta)
def marcar_reparado(ejemplar_id: int, service: CatalogoService = Depends(get_service)):
    """Vuelve a poner en circulacion un ejemplar que estaba en reparacion."""
    return service.reparar_ejemplar(ejemplar_id)
