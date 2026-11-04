from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain.enums import TipoNotificacion


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    tipo = Column(Enum(TipoNotificacion, native_enum=False, length=30), nullable=False)
    titulo = Column(String(150), nullable=False)
    mensaje = Column(String(500), nullable=False)
    # Pantalla del frontend a la que lleva la notificacion (por ejemplo /panel/pedidos)
    enlace = Column(String(200))
    leida = Column(Boolean, nullable=False, default=False)
    fecha = Column(DateTime, nullable=False, default=datetime.now)

    usuario = relationship("Usuario", back_populates="notificaciones")
