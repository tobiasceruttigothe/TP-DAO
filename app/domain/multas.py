"""Patron Strategy para el calculo de multas.

Hay varias formas de multar que conviven. En cada devolucion el contexto (CalculadorMulta)
mira la situacion y elige que estrategias aplican:

    atraso de 1 a 7 dias      -> MultaAtrasoLeve
    atraso de 8 dias o mas    -> MultaAtrasoGrave
    devuelto danado/destruido -> MultaPorDanio (se suma a la de atraso)

Las estrategias no saben cuando se aplican: solo saben calcular su parte. La decision
queda en un unico lugar, el calculador.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from app.domain.enums import EstadoFisico
from app.utiles_texto import pesos as _pesos


@dataclass
class DatosMulta:
    """Lo que hace falta saber para multar. El estado fisico se conoce recien al devolver."""

    dias_atraso: int
    estado_fisico: EstadoFisico | None = None


@dataclass
class ConceptoMulta:
    """Un renglon del detalle de la multa."""

    concepto: str
    monto: float


@dataclass
class ResultadoMulta:
    conceptos: list[ConceptoMulta] = field(default_factory=list)

    @property
    def total(self) -> float:
        return round(sum(c.monto for c in self.conceptos), 2)


class EstrategiaMulta(ABC):
    @abstractmethod
    def calcular(self, datos: DatosMulta) -> ConceptoMulta:
        pass


class MultaAtrasoLeve(EstrategiaMulta):
    """Atraso corto: un monto por cada dia."""

    def __init__(self, monto_diario: float):
        self.monto_diario = monto_diario

    def calcular(self, datos: DatosMulta) -> ConceptoMulta:
        dias = datos.dias_atraso
        return ConceptoMulta(
            f"Atraso leve: {dias} días × {_pesos(self.monto_diario)}",
            round(dias * self.monto_diario, 2),
        )


class MultaAtrasoGrave(EstrategiaMulta):
    """Atraso largo: los primeros dias al monto leve y, desde el siguiente, al monto grave."""

    def __init__(self, monto_diario: float, monto_diario_grave: float, dias_leves: int):
        self.monto_diario = monto_diario
        self.monto_diario_grave = monto_diario_grave
        self.dias_leves = dias_leves

    def calcular(self, datos: DatosMulta) -> ConceptoMulta:
        excedente = datos.dias_atraso - self.dias_leves
        monto = self.dias_leves * self.monto_diario + excedente * self.monto_diario_grave
        return ConceptoMulta(
            f"Atraso grave: {self.dias_leves} días × {_pesos(self.monto_diario)}"
            f" + {excedente} días × {_pesos(self.monto_diario_grave)}",
            round(monto, 2),
        )


class MultaPorDanio(EstrategiaMulta):
    """Cargo fijo segun el estado en que se devolvio el ejemplar."""

    def __init__(self, cargos: dict[EstadoFisico, float]):
        self.cargos = cargos

    def cobra(self, estado: EstadoFisico | None) -> bool:
        return self.cargos.get(estado, 0) > 0

    def calcular(self, datos: DatosMulta) -> ConceptoMulta:
        texto = {EstadoFisico.DANADO: "dañado", EstadoFisico.DESTRUIDO: "destruido"}.get(
            datos.estado_fisico, datos.estado_fisico.value.lower()
        )
        return ConceptoMulta(f"Devuelto {texto}", self.cargos[datos.estado_fisico])


class CalculadorMulta:
    """Contexto del patron: elige las estrategias que corresponden a cada caso y suma."""

    def __init__(
        self,
        atraso_leve: MultaAtrasoLeve,
        atraso_grave: MultaAtrasoGrave,
        por_danio: MultaPorDanio,
    ):
        self.atraso_leve = atraso_leve
        self.atraso_grave = atraso_grave
        self.por_danio = por_danio

    def estrategias_para(self, datos: DatosMulta) -> list[EstrategiaMulta]:
        elegidas: list[EstrategiaMulta] = []
        if datos.dias_atraso > self.atraso_grave.dias_leves:
            elegidas.append(self.atraso_grave)
        elif datos.dias_atraso > 0:
            elegidas.append(self.atraso_leve)
        if self.por_danio.cobra(datos.estado_fisico):
            elegidas.append(self.por_danio)
        return elegidas

    def calcular(self, datos: DatosMulta) -> ResultadoMulta:
        return ResultadoMulta([estrategia.calcular(datos) for estrategia in self.estrategias_para(datos)])


def calculador_configurado() -> CalculadorMulta:
    """Calculador con los montos definidos en la configuracion."""
    from app.config import settings

    return CalculadorMulta(
        atraso_leve=MultaAtrasoLeve(settings.multa_monto_diario),
        atraso_grave=MultaAtrasoGrave(
            settings.multa_monto_diario, settings.multa_monto_diario_grave, settings.multa_dias_leves
        ),
        por_danio=MultaPorDanio(
            {
                EstadoFisico.DANADO: settings.multa_cargo_danado,
                EstadoFisico.DESTRUIDO: settings.multa_cargo_destruido,
            }
        ),
    )
