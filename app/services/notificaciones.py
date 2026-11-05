"""Observadores de eventos: guardan la notificacion en el sistema y la mandan por correo."""
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.models import Notificacion
from app.services.correo import armar_correo, correo_configurado
from app.services.eventos import Contenido, ObservadorEventos


class NotificacionesEnSistema(ObservadorEventos):
    """La notificacion que aparece en la campanita. Se guarda en la misma transaccion que la
    operacion que la genero: si la operacion falla, tampoco queda la notificacion."""

    def __init__(self, db: Session):
        self.db = db

    def notificar(self, destinatarios, contenido: Contenido):
        for usuario in destinatarios:
            self.db.add(
                Notificacion(
                    usuario_id=usuario.id,
                    tipo=contenido.tipo,
                    titulo=contenido.titulo,
                    mensaje=contenido.mensaje,
                    enlace=contenido.enlace,
                )
            )


class NotificacionesPorCorreo(ObservadorEventos):
    """Los correos quedan en espera y salen recien cuando la base confirma la transaccion
    (commit). Si la operacion se deshace, no se envia nada."""

    def __init__(self, db: Session):
        self.db = db

    def notificar(self, destinatarios, contenido: Contenido):
        if self.db.info.get("sin_correo"):
            return
        pendientes = self.db.info.setdefault("correos_pendientes", [])
        for usuario in destinatarios:
            if usuario.recibe_correos:
                pendientes.append(armar_correo(usuario.email, contenido.titulo, contenido.mensaje, contenido.enlace))
        escuchar_transaccion(self.db)


def escuchar_transaccion(db: Session):
    if db.info.get("escucha_correos"):
        return
    db.info["escucha_correos"] = True
    event.listen(db, "after_commit", _enviar_pendientes)
    event.listen(db, "after_soft_rollback", _descartar_pendientes)


def encolar_correo(db: Session, correo):
    """Para correos que no salen de un evento (por ejemplo, el de confirmar el email)."""
    if db.info.get("sin_correo"):
        return
    db.info.setdefault("correos_pendientes", []).append(correo)
    escuchar_transaccion(db)


def _enviar_pendientes(db: Session):
    pendientes = db.info.pop("correos_pendientes", [])
    servicio = correo_configurado()
    for correo in pendientes:
        servicio.enviar(correo)


def _descartar_pendientes(db: Session, transaccion_anterior=None):
    db.info.pop("correos_pendientes", None)
