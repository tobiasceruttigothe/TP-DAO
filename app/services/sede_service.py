from sqlalchemy.orm import Session

from app.exceptions import DuplicadoError, NoEncontradoError, ReglaNegocioError
from app.models import Sede
from app.repositories import SedeRepository
from app.schemas.sede import SedeActualizar, SedeCrear


class SedeService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = SedeRepository(db)

    def listar(self, activa: bool | None = None) -> list[Sede]:
        return self.repo.listar_filtrado(activa)

    def obtener(self, sede_id: int) -> Sede:
        sede = self.repo.obtener(sede_id)
        if sede is None:
            raise NoEncontradoError(f"No existe la sede {sede_id}")
        return sede

    def obtener_activa(self, sede_id: int) -> Sede:
        sede = self.obtener(sede_id)
        if not sede.activa:
            raise ReglaNegocioError(f"La sede '{sede.nombre}' esta dada de baja")
        return sede

    def crear(self, datos: SedeCrear) -> Sede:
        self._validar_nombre_unico(datos.nombre)
        sede = self.repo.agregar(Sede(**datos.model_dump(), activa=True))
        self.db.commit()
        return sede

    def actualizar(self, sede_id: int, datos: SedeActualizar) -> Sede:
        sede = self.obtener(sede_id)
        self._validar_nombre_unico(datos.nombre, excluir_id=sede.id)
        for campo, valor in datos.model_dump().items():
            setattr(sede, campo, valor)
        self.db.commit()
        return sede

    def dar_de_baja(self, sede_id: int) -> Sede:
        sede = self.obtener(sede_id)
        sede.dar_de_baja()
        self.db.commit()
        return sede

    def dar_de_alta(self, sede_id: int) -> Sede:
        sede = self.obtener(sede_id)
        sede.dar_de_alta()
        self.db.commit()
        return sede

    def _validar_nombre_unico(self, nombre: str, excluir_id: int | None = None):
        existente = self.repo.buscar_por_nombre(nombre)
        if existente is not None and existente.id != excluir_id:
            raise DuplicadoError(f"Ya existe una sede llamada '{nombre}'")
