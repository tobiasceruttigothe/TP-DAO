from typing import Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import Base

T = TypeVar("T", bound=Base)


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
