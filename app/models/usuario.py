from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain.enums import EstadoUsuario, Rol


class Usuario(Base):
    """Cuenta para ingresar al sistema. Un administrador no tiene socio; un socio, si."""

    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(120), nullable=False, unique=True)
    nombre = Column(String(100), nullable=False)
    hash_contrasena = Column(String(100), nullable=False)
    rol = Column(Enum(Rol, native_enum=False, length=10), nullable=False)
    estado = Column(Enum(EstadoUsuario, native_enum=False, length=30), nullable=False)
    socio_id = Column(Integer, ForeignKey("socios.id"), unique=True)
    # Los datos de ejemplo tienen emails inventados: no se les manda ningun correo
    recibe_correos = Column(Boolean, nullable=False, default=True)
    token_confirmacion = Column(String(64), unique=True)
    fecha_alta = Column(DateTime, nullable=False, default=datetime.now)
    motivo_rechazo = Column(String(200))

    socio = relationship("Socio", back_populates="usuario")
    notificaciones = relationship("Notificacion", back_populates="usuario", order_by="Notificacion.id.desc()")

    @property
    def es_admin(self) -> bool:
        return self.rol == Rol.ADMIN

    @property
    def puede_ingresar(self) -> bool:
        return self.estado == EstadoUsuario.ACTIVO

    def confirmar_email(self, requiere_aprobacion: bool):
        self.token_confirmacion = None
        self.estado = EstadoUsuario.PENDIENTE_APROBACION if requiere_aprobacion else EstadoUsuario.ACTIVO

    def aprobar(self):
        self.estado = EstadoUsuario.ACTIVO
        self.motivo_rechazo = None

    def rechazar(self, motivo: str):
        self.estado = EstadoUsuario.RECHAZADO
        self.motivo_rechazo = motivo
