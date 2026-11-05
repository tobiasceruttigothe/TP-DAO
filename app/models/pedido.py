from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain.enums import EstadoPedido


class Pedido(Base):
    """Solicitud de un socio para retirar un libro en una sede. La resuelve un administrador:
    la convierte en una reserva, en un prestamo entre sedes o la rechaza."""

    __tablename__ = "pedidos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    socio_id = Column(Integer, ForeignKey("socios.id"), nullable=False)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    estado = Column(Enum(EstadoPedido, native_enum=False, length=20), nullable=False, default=EstadoPedido.PENDIENTE)
    comentario = Column(String(300))
    fecha = Column(DateTime, nullable=False, default=datetime.now)
    fecha_resolucion = Column(DateTime)
    resolucion = Column(String(300))
    reserva_id = Column(Integer, ForeignKey("reservas.id"))
    prestamo_id = Column(Integer, ForeignKey("prestamos.id"))

    socio = relationship("Socio")
    libro = relationship("Libro")
    sede = relationship("Sede")
    reserva = relationship("Reserva")
    prestamo = relationship("Prestamo")

    @property
    def esta_pendiente(self) -> bool:
        return self.estado == EstadoPedido.PENDIENTE

    def resolver(self, estado: EstadoPedido, resolucion: str):
        self.estado = estado
        self.resolucion = resolucion
        self.fecha_resolucion = datetime.now()
