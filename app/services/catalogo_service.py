from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.domain.enums import EstadoEjemplar, EstadoFisico
from app.exceptions import DuplicadoError, NoEncontradoError, ReglaNegocioError
from app.models import Ejemplar, Libro
from app.repositories import EjemplarRepository, LibroRepository, SedeRepository
from app.repositories.base import Paginacion, ResultadoPaginado
from app.schemas.libro import (
    DisponibilidadLibro,
    DisponibilidadSede,
    EjemplarCrear,
    LibroActualizar,
    LibroCrear,
)
from app.services.reserva_service import ReservaService
from app.services.sede_service import SedeService


def codigo_de_inventario(prefijo: str, numero: int) -> str:
    return f"{prefijo}-{numero:04d}"


class CatalogoService:
    """Libros (la obra) y ejemplares (las copias fisicas de cada sede)."""

    def __init__(self, db: Session):
        self.db = db
        self.libros = LibroRepository(db)
        self.ejemplares = EjemplarRepository(db)
        self.sedes = SedeRepository(db)

    # --- Libros ---

    def buscar_libros(self, paginacion: Paginacion, texto: str | None = None) -> ResultadoPaginado[Libro]:
        return self.libros.buscar(paginacion, texto)

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
        self,
        paginacion: Paginacion,
        libro_id: int | None = None,
        sede_id: int | None = None,
        estado: EstadoEjemplar | None = None,
    ) -> ResultadoPaginado[Ejemplar]:
        return self.ejemplares.listar_filtrado(paginacion, libro_id, sede_id, estado)

    def obtener_ejemplar(self, ejemplar_id: int) -> Ejemplar:
        ejemplar = self.ejemplares.obtener(ejemplar_id)
        if ejemplar is None:
            raise NoEncontradoError(f"No existe el ejemplar {ejemplar_id}")
        return ejemplar

    def crear_ejemplares(self, datos: EjemplarCrear) -> list[Ejemplar]:
        """Da de alta una o varias copias iguales. Los codigos los asigna el sistema, correlativos
        al ultimo de la sede (CEN-0021, CEN-0022...), y se guardan todas juntas o ninguna."""
        self.obtener_libro(datos.libro_id)
        sede = SedeService(self.db).obtener_activa(datos.sede_id)
        primero = self.ejemplares.ultimo_numero(sede.prefijo) + 1
        nuevos = [
            Ejemplar(
                codigo_inventario=codigo_de_inventario(sede.prefijo, numero),
                libro_id=datos.libro_id,
                sede_id=sede.id,
                estado_fisico=datos.estado_fisico,
                estado=EstadoEjemplar.DISPONIBLE,
            )
            for numero in range(primero, primero + datos.cantidad)
        ]
        try:
            for ejemplar in nuevos:
                self.ejemplares.agregar(ejemplar)
            self.db.commit()
        except IntegrityError:
            # Otra carga en la misma sede tomo esos numeros al mismo tiempo
            self.db.rollback()
            raise DuplicadoError("Se cargaron otros ejemplares en esa sede al mismo tiempo. Volvé a intentar")
        return nuevos

    def proximo_codigo(self, sede_id: int) -> str:
        sede = SedeService(self.db).obtener(sede_id)
        return codigo_de_inventario(sede.prefijo, self.ejemplares.ultimo_numero(sede.prefijo) + 1)

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

    def marcar_extraviado(self, ejemplar_id: int) -> Ejemplar:
        """Para un ejemplar que deberia estar en el estante y no aparece (por ejemplo, un
        faltante del inventario)."""
        ejemplar = self.obtener_ejemplar(ejemplar_id)
        if ejemplar.estado not in (EstadoEjemplar.DISPONIBLE, EstadoEjemplar.EN_REPARACION):
            raise ReglaNegocioError(
                f"Solo se marca extraviado un ejemplar disponible o en reparación (estado {ejemplar.estado.value})"
            )
        ejemplar.cambiar_estado(EstadoEjemplar.EXTRAVIADO)
        self.db.commit()
        return ejemplar

    def recuperar(self, ejemplar_id: int) -> Ejemplar:
        """Un ejemplar que figuraba extraviado aparecio: vuelve a circular."""
        ejemplar = self.obtener_ejemplar(ejemplar_id)
        if ejemplar.estado != EstadoEjemplar.EXTRAVIADO:
            raise ReglaNegocioError("El ejemplar no figura extraviado")
        ejemplar.liberar()
        self.db.flush()
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
