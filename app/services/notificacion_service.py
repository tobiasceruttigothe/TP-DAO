from sqlalchemy.orm import Session

from app.exceptions import NoEncontradoError
from app.models import Notificacion, Usuario
from app.repositories import NotificacionRepository
from app.repositories.base import Paginacion, ResultadoPaginado


class NotificacionService:
    """Lectura de las notificaciones de un usuario (las crea el observador de eventos)."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = NotificacionRepository(db)

    def listar(self, usuario: Usuario, paginacion: Paginacion, solo_no_leidas: bool = False) -> ResultadoPaginado[Notificacion]:
        return self.repo.de_usuario(usuario.id, paginacion, solo_no_leidas)

    def contar_no_leidas(self, usuario: Usuario) -> int:
        return self.repo.contar_no_leidas(usuario.id)

    def marcar_leida(self, usuario: Usuario, notificacion_id: int) -> Notificacion:
        notificacion = self.repo.obtener(notificacion_id)
        if notificacion is None or notificacion.usuario_id != usuario.id:
            raise NoEncontradoError("No existe la notificación")
        notificacion.leida = True
        self.db.commit()
        return notificacion

    def marcar_todas_leidas(self, usuario: Usuario):
        self.repo.marcar_todas_leidas(usuario.id)
        self.db.commit()
