from datetime import date

from sqlalchemy import Boolean, Column, Date, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Socio(Base):
    __tablename__ = "socios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    dni = Column(String(20), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    email = Column(String(120), nullable=False, unique=True)
    telefono = Column(String(30))
    fecha_alta = Column(Date, nullable=False, default=date.today)
    habilitado = Column(Boolean, nullable=False, default=True)
    motivo_inhabilitacion = Column(String(200))

    prestamos = relationship("Prestamo", back_populates="socio")
    reservas = relationship("Reserva", back_populates="socio")

    def inhabilitar(self, motivo: str):
        self.habilitado = False
        self.motivo_inhabilitacion = motivo

    def habilitar(self):
        self.habilitado = True
        self.motivo_inhabilitacion = None

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    def __str__(self):
        return f"{self.nombre_completo} (DNI: {self.dni})"
