from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.domain.enums import EstadoFisico, TipoIncidencia, TipoRemito
from app.domain.estados_remito import EstadoRemito, Extraviado, Pendiente, estado_desde_nombre


class Remito(Base):
    __tablename__ = "remitos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    numero = Column(String(20), nullable=False, unique=True)
    tipo = Column(Enum(TipoRemito, native_enum=False, length=10), nullable=False)
    prestamo_id = Column(Integer, ForeignKey("prestamos.id"), nullable=False)
    ejemplar_id = Column(Integer, ForeignKey("ejemplares.id"), nullable=False)
    sede_origen_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    sede_destino_id = Column(Integer, ForeignKey("sedes.id"), nullable=False)
    estado = Column(String(20), nullable=False, default=Pendiente.nombre)
    fecha_creacion = Column(DateTime, nullable=False, default=datetime.now)
    fecha_despacho = Column(DateTime)
    fecha_recepcion = Column(DateTime)
    estado_fisico_recepcion = Column(Enum(EstadoFisico, native_enum=False, length=20))

    prestamo = relationship("Prestamo", back_populates="remitos")
    ejemplar = relationship("Ejemplar")
    sede_origen = relationship("Sede", foreign_keys=[sede_origen_id])
    sede_destino = relationship("Sede", foreign_keys=[sede_destino_id])
    movimientos = relationship(
        "MovimientoRemito",
        back_populates="remito",
        order_by="MovimientoRemito.id",
        cascade="all, delete-orphan",
    )
    incidencias = relationship(
        "Incidencia",
        back_populates="remito",
        order_by="Incidencia.id",
        cascade="all, delete-orphan",
    )

    # --- Contexto del patron State ---

    @property
    def estado_actual(self) -> EstadoRemito:
        return estado_desde_nombre(self.estado or Pendiente.nombre)

    def cambiar_estado(self, nuevo: EstadoRemito, observacion: str | None = None):
        anterior = self.estado
        self.estado = nuevo.nombre
        nuevo.entrar(self)
        self.movimientos.append(
            MovimientoRemito(estado_anterior=anterior, estado_nuevo=nuevo.nombre, observacion=observacion)
        )

    def registrar_creacion(self):
        self.estado = Pendiente.nombre
        self.movimientos.append(MovimientoRemito(estado_anterior=None, estado_nuevo=Pendiente.nombre))

    def empaquetar(self, observacion=None):
        self.estado_actual.empaquetar(self, observacion)

    def despachar(self, observacion=None):
        self.estado_actual.despachar(self, observacion)

    def recibir(self, observacion=None):
        self.estado_actual.recibir(self, observacion)

    def marcar_extraviado(self, observacion=None):
        self.estado_actual.marcar_extraviado(self, observacion)

    def cancelar(self, observacion=None):
        self.estado_actual.cancelar(self, observacion)

    def registrar_incidencia(self, tipo: TipoIncidencia, descripcion: str | None = None):
        self.incidencias.append(Incidencia(tipo=tipo, descripcion=descripcion))

    @property
    def tuvo_incidencia(self) -> bool:
        return self.estado == Extraviado.nombre or self.estado_fisico_recepcion in (
            EstadoFisico.DANADO,
            EstadoFisico.DESTRUIDO,
        )

    @property
    def horas_en_transito(self) -> float | None:
        if self.fecha_despacho is None or self.fecha_recepcion is None:
            return None
        return (self.fecha_recepcion - self.fecha_despacho).total_seconds() / 3600


class MovimientoRemito(Base):
    """Historial de cambios de estado: da la trazabilidad del remito."""

    __tablename__ = "movimientos_remito"

    id = Column(Integer, primary_key=True, autoincrement=True)
    remito_id = Column(Integer, ForeignKey("remitos.id"), nullable=False)
    estado_anterior = Column(String(20))
    estado_nuevo = Column(String(20), nullable=False)
    fecha = Column(DateTime, nullable=False, default=datetime.now)
    observacion = Column(String(300))

    remito = relationship("Remito", back_populates="movimientos")


class Incidencia(Base):
    """Problema detectado en un envio: dano o destruccion al recibir, o extravio."""

    __tablename__ = "incidencias"

    id = Column(Integer, primary_key=True, autoincrement=True)
    remito_id = Column(Integer, ForeignKey("remitos.id"), nullable=False)
    tipo = Column(Enum(TipoIncidencia, native_enum=False, length=20), nullable=False)
    descripcion = Column(String(300))
    fecha = Column(DateTime, nullable=False, default=datetime.now)

    remito = relationship("Remito", back_populates="incidencias")
