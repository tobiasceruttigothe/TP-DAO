from datetime import datetime

from sqlalchemy.orm import Session

from app.domain.enums import EstadoEjemplar, EstadoInventario
from app.exceptions import NoEncontradoError, ReglaNegocioError
from app.models import Inventario, ItemInventario
from app.repositories import InventarioRepository
from app.repositories.inventario_repository import ESTADOS_EN_ESTANTE
from app.repositories.base import Paginacion, ResultadoPaginado
from app.schemas.inventario import FilaInforme, Informe, InventarioDetalle, ResultadoCodigo
from app.services.sede_service import SedeService

MOTIVO_FUERA_DE_LUGAR = {
    EstadoEjemplar.PRESTADO: "Figura prestado",
    EstadoEjemplar.EN_TRANSITO: "Figura en tránsito",
    EstadoEjemplar.EXTRAVIADO: "Figura extraviado",
    EstadoEjemplar.BAJA: "Figura dado de baja",
}


class InventarioService:
    """Recuento fisico de una sede: se registran los codigos encontrados en los estantes y
    el informe los compara con los ejemplares que deberian estar ahi."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = InventarioRepository(db)

    def listar(self, paginacion: Paginacion, sede_id: int | None = None) -> ResultadoPaginado[Inventario]:
        return self.repo.listar_filtrado(paginacion, sede_id)

    def obtener(self, inventario_id: int) -> Inventario:
        inventario = self.repo.obtener(inventario_id)
        if inventario is None:
            raise NoEncontradoError(f"No existe el inventario {inventario_id}")
        return inventario

    def iniciar(self, sede_id: int, observacion: str | None = None) -> Inventario:
        sede = SedeService(self.db).obtener_activa(sede_id)
        if self.repo.en_curso_de_sede(sede.id) is not None:
            raise ReglaNegocioError(f"Ya hay un inventario en curso en {sede.nombre}")
        inventario = self.repo.agregar(Inventario(sede_id=sede.id, observacion=observacion))
        self.db.commit()
        return inventario

    def registrar_codigo(self, inventario_id: int, codigo: str) -> ResultadoCodigo:
        inventario = self._en_curso(inventario_id)
        codigo = codigo.strip().upper()
        if self.repo.item_por_codigo(inventario.id, codigo) is not None:
            raise ReglaNegocioError(f"El código {codigo} ya se registró en este inventario")
        ejemplar = self.repo.ejemplar_por_codigo(codigo)
        item = ItemInventario(inventario_id=inventario.id, codigo=codigo, ejemplar_id=ejemplar.id if ejemplar else None)
        self.db.add(item)
        self.db.commit()

        if ejemplar is None:
            resultado, detalle = "DESCONOCIDO", "El código no corresponde a ningún ejemplar"
        elif self._esperado_en(ejemplar, inventario.sede_id):
            resultado, detalle = "ENCONTRADO", ejemplar.libro.titulo
        else:
            resultado, detalle = "FUERA_DE_LUGAR", f"{ejemplar.libro.titulo}: {self._motivo(ejemplar, inventario.sede_id)}"
        return ResultadoCodigo(item_id=item.id, codigo=codigo, resultado=resultado, detalle=detalle)

    def quitar_codigo(self, inventario_id: int, item_id: int):
        inventario = self._en_curso(inventario_id)
        item = next((i for i in inventario.items if i.id == item_id), None)
        if item is None:
            raise NoEncontradoError("Ese código no está registrado en el inventario")
        inventario.items.remove(item)  # se borra de la base por el cascade delete-orphan
        self.db.commit()

    def cerrar(self, inventario_id: int) -> Inventario:
        inventario = self._en_curso(inventario_id)
        informe = self._calcular_informe(inventario)
        inventario.estado = EstadoInventario.CERRADO
        inventario.fecha_cierre = datetime.now()
        # Se guarda la foto del informe: despues los ejemplares pueden cambiar de estado
        inventario.resumen = {
            "esperados": len(informe.encontrados) + len(informe.faltantes),
            "informe": informe.model_dump(),
        }
        self.db.commit()
        return inventario

    def detalle(self, inventario_id: int) -> InventarioDetalle:
        inventario = self.obtener(inventario_id)
        if inventario.en_curso:
            informe = self._calcular_informe(inventario)
            esperados = len(informe.encontrados) + len(informe.faltantes)
        else:
            informe = Informe(**inventario.resumen["informe"])
            esperados = inventario.resumen["esperados"]
        return InventarioDetalle(
            id=inventario.id,
            sede=inventario.sede,
            estado=inventario.estado,
            fecha_inicio=inventario.fecha_inicio,
            fecha_cierre=inventario.fecha_cierre,
            observacion=inventario.observacion,
            cantidad_registrados=inventario.cantidad_registrados,
            esperados=esperados,
            informe=informe,
        )

    # --- Calculo del informe ---

    def _calcular_informe(self, inventario: Inventario) -> Informe:
        esperados = {e.id: e for e in self.repo.esperados_en_sede(inventario.sede_id)}
        registrados = {i.ejemplar_id for i in inventario.items if i.ejemplar_id is not None}

        encontrados, fuera_de_lugar, desconocidos = [], [], []
        for item in sorted(inventario.items, key=lambda i: i.codigo):
            ejemplar = item.ejemplar
            if ejemplar is None:
                desconocidos.append(FilaInforme(codigo=item.codigo, detalle="No existe en el sistema"))
            elif ejemplar.id in esperados:
                encontrados.append(self._fila(ejemplar))
            else:
                fuera_de_lugar.append(self._fila(ejemplar, self._motivo(ejemplar, inventario.sede_id)))
        faltantes = [
            self._fila(e, "No se encontró en el estante") for e in esperados.values() if e.id not in registrados
        ]
        return Informe(
            encontrados=encontrados, faltantes=faltantes, fuera_de_lugar=fuera_de_lugar, desconocidos=desconocidos
        )

    @staticmethod
    def _fila(ejemplar, detalle: str | None = None) -> FilaInforme:
        return FilaInforme(
            codigo=ejemplar.codigo_inventario,
            ejemplar_id=ejemplar.id,
            titulo=ejemplar.libro.titulo,
            estado=ejemplar.estado.value,
            detalle=detalle,
        )

    @staticmethod
    def _esperado_en(ejemplar, sede_id: int) -> bool:
        return ejemplar.sede_id == sede_id and ejemplar.estado in ESTADOS_EN_ESTANTE

    @staticmethod
    def _motivo(ejemplar, sede_id: int) -> str:
        if ejemplar.sede_id != sede_id:
            return f"Pertenece a {ejemplar.sede.nombre}"
        return MOTIVO_FUERA_DE_LUGAR.get(ejemplar.estado, "No debería estar en el estante")

    def _en_curso(self, inventario_id: int) -> Inventario:
        inventario = self.obtener(inventario_id)
        if not inventario.en_curso:
            raise ReglaNegocioError("El inventario ya está cerrado")
        return inventario
