from sqlalchemy import or_, select

from app.models import Socio
from app.repositories.base import BaseRepository


class SocioRepository(BaseRepository[Socio]):
    modelo = Socio

    def buscar_por_dni(self, dni: str) -> Socio | None:
        return self.db.scalar(select(Socio).where(Socio.dni == dni))

    def buscar_por_email(self, email: str) -> Socio | None:
        return self.db.scalar(select(Socio).where(Socio.email.ilike(email)))

    def listar_filtrado(self, texto: str | None = None, habilitado: bool | None = None) -> list[Socio]:
        consulta = select(Socio).order_by(Socio.apellido, Socio.nombre)
        if texto:
            patron = f"%{texto}%"
            consulta = consulta.where(
                or_(Socio.nombre.ilike(patron), Socio.apellido.ilike(patron), Socio.dni.ilike(patron))
            )
        if habilitado is not None:
            consulta = consulta.where(Socio.habilitado == habilitado)
        return list(self.db.scalars(consulta))
