from sqlalchemy.orm import Session

from app.domain.enums import EstadoEjemplar, EstadoFisico
from app.exceptions import DuplicadoError, NoEncontradoError, ReglaNegocioError
from app.models import Ejemplar, Libro
from app.repositories import EjemplarRepository, LibroRepository, SedeRepository
from app.schemas.libro import (
    DisponibilidadLibro,
    DisponibilidadSede,
    EjemplarCrear,
    LibroActualizar,
    LibroCrear,
)
from app.services.reserva_service import ReservaService
from app.services.sede_service import SedeService


class CatalogoService:
    """Libros (la obra) y ejemplares (las copias fisicas de cada sede)."""

    def __init__(self, db: Session):
        self.db = db
        self.libros = LibroRepository(db)
        self.ejemplares = EjemplarRepository(db)
        self.sedes = SedeRepository(db)

    # --- Libros ---

    def buscar_libros(self, texto: str | None = None) -> list[Libro]:
        return self.libros.buscar(texto)

    def obtener_libro(self, libro_id: int) -> Libro:
        libro = self.libros.obtener(libro_id)
        if libro is None:
            raise NoEncontradoError(f"No existe el libro {libro_id}")
        return libro

    def crear_libro(self, datos: LibroCrear) -> Libro:
        self._validar_isbn_unico(datos.isbn)
        libro = self.libros.agregar(Libro(**datos.model_dump()))
        self.db.commit()
        return libro

    def actualizar_libro(self, libro_id: int, datos: LibroActualizar) -> Libro:
        libro = self.obtener_libro(libro_id)
        self._validar_isbn_unico(datos.isbn, excluir_id=libro.id)
        for campo, valor in datos.model_dump().items():
            setattr(libro, campo, valor)
        self.db.commit()
        return libro

    def _validar_isbn_unico(self, isbn: str, excluir_id: int | None = None):
        existente = self.libros.buscar_por_isbn(isbn)
        if existente is not None and existente.id != excluir_id:
            raise DuplicadoError(f"Ya existe un libro con ISBN {isbn}")

    # --- Ejemplares ---

    def listar_ejemplares(
        self, libro_id: int | None = None, sede_id: int | None = None, estado: EstadoEjemplar | None = None
    ) -> list[Ejemplar]:
        return self.ejemplares.listar_filtrado(libro_id, sede_id, estado)

    def obtener_ejemplar(self, ejemplar_id: int) -> Ejemplar:
        ejemplar = self.ejemplares.obtener(ejemplar_id)
        if ejemplar is None:
            raise NoEncontradoError(f"No existe el ejemplar {ejemplar_id}")
        return ejemplar

    def crear_ejemplar(self, datos: EjemplarCrear) -> Ejemplar:
        self.obtener_libro(datos.libro_id)
        SedeService(self.db).obtener_activa(datos.sede_id)
        if self.ejemplares.buscar_por_codigo(datos.codigo_inventario) is not None:
            raise DuplicadoError(f"Ya existe un ejemplar con codigo {datos.codigo_inventario}")
        ejemplar = Ejemplar(**datos.model_dump(), estado=EstadoEjemplar.DISPONIBLE)
        self.ejemplares.agregar(ejemplar)
        self.db.commit()
        return ejemplar

    def dar_de_baja_ejemplar(self, ejemplar_id: int) -> Ejemplar:
        ejemplar = self.obtener_ejemplar(ejemplar_id)
        if ejemplar.estado not in (EstadoEjemplar.DISPONIBLE, EstadoEjemplar.EN_REPARACION):
            raise ReglaNegocioError(
                f"No se puede dar de baja un ejemplar en estado {ejemplar.estado.value}"
            )
        ejemplar.cambiar_estado(EstadoEjemplar.BAJA)
        self.db.commit()
        return ejemplar

    def reparar_ejemplar(self, ejemplar_id: int) -> Ejemplar:
        """Marca como reparado un ejemplar danado y lo vuelve a poner en circulacion."""
        ejemplar = self.obtener_ejemplar(ejemplar_id)
        if ejemplar.estado != EstadoEjemplar.EN_REPARACION:
            raise ReglaNegocioError("El ejemplar no esta en reparacion")
        ejemplar.estado_fisico = EstadoFisico.REGULAR
        ejemplar.liberar()
        ReservaService(self.db).asignar_ejemplar_liberado(ejemplar)
        self.db.commit()
        return ejemplar

    # --- Disponibilidad ---

    def disponibilidad(self, libro_id: int) -> DisponibilidadLibro:
        libro = self.obtener_libro(libro_id)
        por_sede: dict[int, DisponibilidadSede] = {}
        for ejemplar in libro.ejemplares:
            if ejemplar.estado == EstadoEjemplar.BAJA or not ejemplar.sede.activa:
                continue
            item = por_sede.setdefault(
                ejemplar.sede_id,
                DisponibilidadSede(
                    sede_id=ejemplar.sede_id,
                    sede=ejemplar.sede.nombre,
                    total=0,
                    disponibles=0,
                    ejemplares_disponibles=[],
                ),
            )
            item.total += 1
            if ejemplar.esta_disponible:
                item.disponibles += 1
                item.ejemplares_disponibles.append(ejemplar.codigo_inventario)
        sedes = sorted(por_sede.values(), key=lambda s: s.sede)
        return DisponibilidadLibro(
            libro_id=libro.id,
            titulo=libro.titulo,
            total_disponibles=sum(s.disponibles for s in sedes),
            sedes=sedes,
        )
