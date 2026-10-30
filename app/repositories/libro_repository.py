from sqlalchemy import or_, select

from app.models import Libro
from app.repositories.base import BaseRepository, Paginacion, ResultadoPaginado


class LibroRepository(BaseRepository[Libro]):
    modelo = Libro

    def buscar_por_isbn(self, isbn: str) -> Libro | None:
        return self.db.scalar(select(Libro).where(Libro.isbn == isbn))

    def buscar(self, paginacion: Paginacion, texto: str | None = None) -> ResultadoPaginado[Libro]:
        consulta = select(Libro).order_by(Libro.titulo, Libro.id)
        if texto:
            patron = f"%{texto}%"
            consulta = consulta.where(or_(Libro.titulo.ilike(patron), Libro.autor.ilike(patron)))
        return self.paginar(consulta, paginacion)
