from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain.enums import EstadoEjemplar, EstadoFisico


class Ejemplar(Base):
    __tablename__ = "ejemplares"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_inventario = Column(String(30), nullable=False, unique=True)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    estado = Column(
        Enum(EstadoEjemplar, native_enum=False, length=20),
        nullable=False,
        default=EstadoEjemplar.DISPONIBLE,
    )
    estado_fisico = Column(
        Enum(EstadoFisico, native_enum=False, length=20),
        nullable=False,
        default=EstadoFisico.BUENO,
    )

    libro = relationship("Libro", back_populates="ejemplares")
    sede = relationship("Sede", back_populates="ejemplares")

    @property
    def esta_disponible(self) -> bool:
        return self.estado == EstadoEjemplar.DISPONIBLE

    def cambiar_estado(self, estado: EstadoEjemplar):
        self.estado = estado

    def liberar(self):
        """Vuelve a quedar disponible, salvo que haya llegado danado."""
        if self.estado_fisico == EstadoFisico.DANADO:
            self.estado = EstadoEjemplar.EN_REPARACION
        else:
            self.estado = EstadoEjemplar.DISPONIBLE

    def __str__(self):
        return f"{self.codigo_inventario} ({self.estado.value})"
