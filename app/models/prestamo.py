from datetime import date, timedelta

from sqlalchemy import Column, Date, Enum, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain.enums import EstadoFisico, EstadoPrestamo, TipoPrestamo


class Prestamo(Base):
    __tablename__ = "prestamos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    socio_id = Column(Integer, ForeignKey("socios.id"), nullable=False)
    ejemplar_id = Column(Integer, ForeignKey("ejemplares.id"), nullable=False)
    sede_origen_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    sede_destino_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    tipo = Column(Enum(TipoPrestamo, native_enum=False, length=20), nullable=False)
    estado = Column(Enum(EstadoPrestamo, native_enum=False, length=20), nullable=False)
    fecha_solicitud = Column(Date, nullable=False, default=date.today)
    fecha_inicio = Column(Date)
    fecha_vencimiento = Column(Date)
    fecha_devolucion = Column(Date)
    estado_fisico_devolucion = Column(Enum(EstadoFisico, native_enum=False, length=20))
    multa = Column(Float, nullable=False, default=0.0)
    observaciones = Column(String(300))

    socio = relationship("Socio", back_populates="prestamos")
    ejemplar = relationship("Ejemplar")
    sede_origen = relationship("Sede", foreign_keys=[sede_origen_id])
    sede_destino = relationship("Sede", foreign_keys=[sede_destino_id])
    remitos = relationship("Remito", back_populates="prestamo", order_by="Remito.id")

    def activar(self, fecha: date, dias_prestamo: int):
        self.estado = EstadoPrestamo.ACTIVO
        self.fecha_inicio = fecha
        self.fecha_vencimiento = fecha + timedelta(days=dias_prestamo)

    def dias_atraso(self, fecha: date) -> int:
        if self.fecha_vencimiento is None:
            return 0
        return max((fecha - self.fecha_vencimiento).days, 0)

    def esta_vencido(self, fecha: date) -> bool:
        return self.estado == EstadoPrestamo.ACTIVO and self.dias_atraso(fecha) > 0

    @property
    def es_interbibliotecario(self) -> bool:
        return self.tipo == TipoPrestamo.INTERBIBLIOTECARIO
