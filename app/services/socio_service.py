from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.config import settings

from app.exceptions import DuplicadoError, NoEncontradoError, ReglaNegocioError
from app.models import Socio
from app.repositories import PrestamoRepository, SocioRepository
from app.repositories.base import Paginacion, ResultadoPaginado
from app.schemas.socio import SocioActualizar, SocioCrear
from app.services.eventos import SocioInhabilitado, publicador


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
        publicador(self.db).publicar(SocioInhabilitado(socio))
        self.db.commit()
        return socio

    def habilitar(self, socio_id: int) -> Socio:
        socio = self.obtener(socio_id)
        socio.habilitar()
        self.db.commit()
        return socio

    def inhabilitar_por_atraso(self, hoy: date | None = None) -> list[Socio]:
        """Inhabilita a los socios con algun prestamo vencido hace mas de
        `dias_atraso_inhabilitacion` dias. Devuelve los que inhabilito en esta pasada.
        No hace commit; lo hace el proceso que lo llama."""
        hoy = hoy or date.today()
        limite = hoy - timedelta(days=settings.dias_atraso_inhabilitacion)
        inhabilitados = []
        for prestamo in PrestamoRepository(self.db).vencidos_antes_de(limite):
            socio = prestamo.socio
            if not socio.habilitado:
                continue
            titulo = prestamo.ejemplar.libro.titulo
            socio.inhabilitar(
                f"Préstamo N° {prestamo.id} ({titulo}) vencido hace {prestamo.dias_atraso(hoy)} días sin devolver"
            )
            publicador(self.db).publicar(SocioInhabilitado(socio))
            inhabilitados.append(socio)
        self.db.flush()
        return inhabilitados

    def _validar_unicos(self, dni: str, email: str, excluir_id: int | None = None):
        por_dni = self.repo.buscar_por_dni(dni)
        if por_dni is not None and por_dni.id != excluir_id:
            raise DuplicadoError(f"Ya existe un socio con DNI {dni}")
        por_email = self.repo.buscar_por_email(email)
        if por_email is not None and por_email.id != excluir_id:
            raise DuplicadoError(f"Ya existe un socio con email {email}")
