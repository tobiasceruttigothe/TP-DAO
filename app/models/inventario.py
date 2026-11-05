from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain.enums import EstadoInventario


class Inventario(Base):
    """Recuento fisico de los ejemplares de una sede: se registran los codigos que se
    encuentran en los estantes y se comparan con lo que el sistema dice que deberia haber."""

    __tablename__ = "inventarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    sede_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    estado = Column(Enum(EstadoInventario, native_enum=False, length=20), nullable=False, default=EstadoInventario.EN_CURSO)
    fecha_inicio = Column(DateTime, nullable=False, default=datetime.now)
    fecha_cierre = Column(DateTime)
    observacion = Column(String(300))
    # Totales del informe al cerrar, para que no cambien si despues se mueven ejemplares
    resumen = Column(JSON)

    sede = relationship("Sede")
    items = relationship("ItemInventario", back_populates="inventario", order_by="ItemInventario.id.desc()", cascade="all, delete-orphan")

    @property
    def en_curso(self) -> bool:
        return self.estado == EstadoInventario.EN_CURSO

    @property
    def cantidad_registrados(self) -> int:
        return len(self.items)


class ItemInventario(Base):
    """Un codigo registrado durante el recuento."""

    __tablename__ = "items_inventario"
    __table_args__ = (UniqueConstraint("inventario_id", "codigo", name="uq_item_inventario_codigo"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    inventario_id = Column(Integer, ForeignKey("inventarios.id"), nullable=False)
    codigo = Column(String(30), nullable=False)
    ejemplar_id = Column(Integer, ForeignKey("ejemplares.id"))
    fecha = Column(DateTime, nullable=False, default=datetime.now)

    inventario = relationship("Inventario", back_populates="items")
    ejemplar = relationship("Ejemplar")
