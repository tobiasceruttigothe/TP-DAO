from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Sede(Base):
    __tablename__ = "sedes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    nombre = Column(String(100), nullable=False, unique=True)
    direccion = Column(String(200), nullable=False)
    telefono = Column(String(30))
    email = Column(String(120))
    horario = Column(String(200))
    activa = Column(Boolean, nullable=False, default=True)

    ejemplares = relationship("Ejemplar", back_populates="sede")

    def dar_de_baja(self):
        self.activa = False

    def dar_de_alta(self):
        self.activa = True

    def __str__(self):
        return self.nombre
