import math
from dataclasses import dataclass
from typing import Generic, TypeVar

from sqlalchemy import ColumnElement, Select, func, select
from sqlalchemy.orm import Session

from app.database import Base

T = TypeVar("T", bound=Base)


def contiene(columna, texto: str) -> ColumnElement[bool]:
    """Busqueda parcial que ignora mayusculas y tildes ("cortazar" encuentra "Cortázar").
    Los comodines de LIKE que escriba el usuario se toman como texto literal."""
    literal = texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    return func.unaccent(columna).ilike(func.unaccent(f"%{literal}%"), escape="\\")


@dataclass
class Paginacion:
    pagina: int = 1
    tamanio: int = 20

    @property
    def desplazamiento(self) -> int:
        return (self.pagina - 1) * self.tamanio


@dataclass
class ResultadoPaginado(Generic[T]):
    items: list[T]
    total: int
    pagina: int
    tamanio: int

    @property
    def paginas(self) -> int:
        return math.ceil(self.total / self.tamanio) if self.total else 0


class BaseRepository(Generic[T]):
    """Operaciones comunes de acceso a datos. Las subclases solo indican el modelo
    y agregan sus consultas propias. No hace commit: eso lo decide el servicio."""

    modelo: type[T]

    def __init__(self, db: Session):
        self.db = db

    def obtener(self, id: int) -> T | None:
        return self.db.get(self.modelo, id)

    def listar(self) -> list[T]:
        return list(self.db.scalars(select(self.modelo).order_by(self.modelo.id)))

    def agregar(self, entidad: T) -> T:
        self.db.add(entidad)
        self.db.flush()
        return entidad

    def eliminar(self, entidad: T):
        self.db.delete(entidad)
        self.db.flush()

    def paginar(self, consulta: Select, paginacion: Paginacion) -> ResultadoPaginado[T]:
        total = self.db.scalar(select(func.count()).select_from(consulta.order_by(None).subquery()))
        items = self.db.scalars(consulta.offset(paginacion.desplazamiento).limit(paginacion.tamanio))
        return ResultadoPaginado(
            items=list(items), total=total, pagina=paginacion.pagina, tamanio=paginacion.tamanio
        )
