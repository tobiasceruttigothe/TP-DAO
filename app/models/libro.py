from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Libro(Base):
    __tablename__ = "libros"

    id = Column(Integer, primary_key=True, autoincrement=True)
    isbn = Column(String(20), nullable=False, unique=True)
    titulo = Column(String(200), nullable=False)
    autor = Column(String(150), nullable=False)
    editorial = Column(String(100))
    anio_publicacion = Column(Integer)
    genero = Column(String(60))

    ejemplares = relationship("Ejemplar", back_populates="libro")

    def __str__(self):
        return f"{self.titulo} - {self.autor}"
