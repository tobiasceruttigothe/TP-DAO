from sqlalchemy import func, select, update

from app.models import Notificacion
from app.repositories.base import BaseRepository, Paginacion, ResultadoPaginado


class NotificacionRepository(BaseRepository[Notificacion]):
    modelo = Notificacion

    def de_usuario(self, usuario_id: int, paginacion: Paginacion, solo_no_leidas: bool = False) -> ResultadoPaginado[Notificacion]:
        consulta = select(Notificacion).where(Notificacion.usuario_id == usuario_id)
        if solo_no_leidas:
            consulta = consulta.where(Notificacion.leida.is_(False))
        return self.paginar(consulta.order_by(Notificacion.fecha.desc(), Notificacion.id.desc()), paginacion)

    def contar_no_leidas(self, usuario_id: int) -> int:
        consulta = select(func.count(Notificacion.id)).where(
            Notificacion.usuario_id == usuario_id, Notificacion.leida.is_(False)
        )
        return self.db.scalar(consulta)

    def marcar_todas_leidas(self, usuario_id: int):
        self.db.execute(
            update(Notificacion)
            .where(Notificacion.usuario_id == usuario_id, Notificacion.leida.is_(False))
            .values(leida=True)
        )
