from sqlalchemy.orm import Session

from app.exceptions import DuplicadoError, NoEncontradoError, ReglaNegocioError
from app.models import Socio
from app.repositories import SocioRepository
from app.repositories.base import Paginacion, ResultadoPaginado
from app.schemas.socio import SocioActualizar, SocioCrear


class SocioService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SocioRepository(db)

    def listar(
        self, paginacion: Paginacion, texto: str | None = None, habilitado: bool | None = None
    ) -> ResultadoPaginado[Socio]:
        return self.repo.listar_filtrado(paginacion, texto, habilitado)

    def obtener(self, socio_id: int) -> Socio:
        socio = self.repo.obtener(socio_id)
        if socio is None:
            raise NoEncontradoError(f"No existe el socio {socio_id}")
        return socio

    def obtener_habilitado(self, socio_id: int) -> Socio:
        socio = self.obtener(socio_id)
        if not socio.habilitado:
            raise ReglaNegocioError(f"El socio {socio.nombre_completo} esta inhabilitado")
        return socio

    def crear(self, datos: SocioCrear) -> Socio:
        self._validar_unicos(datos.dni, datos.email)
        socio = self.repo.agregar(Socio(**datos.model_dump(), habilitado=True))
        self.db.commit()
        return socio

    def actualizar(self, socio_id: int, datos: SocioActualizar) -> Socio:
        socio = self.obtener(socio_id)
        self._validar_unicos(datos.dni, datos.email, excluir_id=socio.id)
        for campo, valor in datos.model_dump().items():
            setattr(socio, campo, valor)
        self.db.commit()
        return socio

    def inhabilitar(self, socio_id: int, motivo: str) -> Socio:
        socio = self.obtener(socio_id)
        socio.inhabilitar(motivo)
        self.db.commit()
        return socio

    def habilitar(self, socio_id: int) -> Socio:
        socio = self.obtener(socio_id)
        socio.habilitar()
        self.db.commit()
        return socio

    def _validar_unicos(self, dni: str, email: str, excluir_id: int | None = None):
        por_dni = self.repo.buscar_por_dni(dni)
        if por_dni is not None and por_dni.id != excluir_id:
            raise DuplicadoError(f"Ya existe un socio con DNI {dni}")
        por_email = self.repo.buscar_por_email(email)
        if por_email is not None and por_email.id != excluir_id:
            raise DuplicadoError(f"Ya existe un socio con email {email}")
