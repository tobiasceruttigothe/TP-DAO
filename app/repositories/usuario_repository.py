from sqlalchemy import func, or_, select

from app.domain.enums import EstadoUsuario, Rol
from app.models import Socio, Usuario
from app.repositories.base import BaseRepository, Paginacion, ResultadoPaginado, contiene


class UsuarioRepository(BaseRepository[Usuario]):
    modelo = Usuario

    def buscar_por_email(self, email: str) -> Usuario | None:
        return self.db.scalar(select(Usuario).where(func.lower(Usuario.email) == email.lower()))

    def buscar_por_token(self, token: str) -> Usuario | None:
        return self.db.scalar(select(Usuario).where(Usuario.token_confirmacion == token))

    def hay_administrador(self) -> bool:
        return self.db.scalar(select(func.count(Usuario.id)).where(Usuario.rol == Rol.ADMIN)) > 0

    def listar_filtrado(
        self,
        paginacion: Paginacion,
        estado: EstadoUsuario | None = None,
        rol: Rol | None = None,
        texto: str | None = None,
    ) -> ResultadoPaginado[Usuario]:
        consulta = select(Usuario).outerjoin(Socio).order_by(Usuario.fecha_alta.desc(), Usuario.id.desc())
        if estado is not None:
            consulta = consulta.where(Usuario.estado == estado)
        if rol is not None:
            consulta = consulta.where(Usuario.rol == rol)
        if texto:
            consulta = consulta.where(
                or_(contiene(Usuario.email, texto), contiene(Usuario.nombre, texto), contiene(Socio.dni, texto))
            )
        return self.paginar(consulta, paginacion)
