from datetime import date

from sqlalchemy import Column, Date, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain.enums import EstadoReserva


class Reserva(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, autoincrement=True)
    socio_id = Column(Integer, ForeignKey("socios.id"), nullable=False)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    ejemplar_id = Column(Integer, ForeignKey("ejemplares.id"))
    estado = Column(Enum(EstadoReserva, native_enum=False, length=20), nullable=False)
    fecha_reserva = Column(Date, nullable=False, default=date.today)
    fecha_expiracion = Column(Date)

    socio = relationship("Socio", back_populates="reservas")
    libro = relationship("Libro")
    sede = relationship("Sede")
    ejemplar = relationship("Ejemplar")

    @property
    def esta_activa(self) -> bool:
        return self.estado in (EstadoReserva.PENDIENTE, EstadoReserva.DISPONIBLE)
