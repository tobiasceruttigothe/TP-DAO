"""Patron Strategy para el calculo de multas por atraso."""
from abc import ABC, abstractmethod


class EstrategiaMulta(ABC):
    @abstractmethod
    def calcular(self, dias_atraso: int) -> float:
        pass


class MultaFija(EstrategiaMulta):
    """Monto fijo por cada dia de atraso."""

    def __init__(self, monto_diario: float):
        self.monto_diario = monto_diario

    def calcular(self, dias_atraso: int) -> float:
        if dias_atraso <= 0:
            return 0.0
        return round(dias_atraso * self.monto_diario, 2)


class MultaEscalonada(EstrategiaMulta):
    """La primera semana se cobra el monto base; desde el dia 8 se duplica."""

    def __init__(self, monto_diario: float, dias_tramo: int = 7, factor: float = 2.0):
        self.monto_diario = monto_diario
        self.dias_tramo = dias_tramo
        self.factor = factor

    def calcular(self, dias_atraso: int) -> float:
        if dias_atraso <= 0:
            return 0.0
        primer_tramo = min(dias_atraso, self.dias_tramo)
        excedente = max(dias_atraso - self.dias_tramo, 0)
        total = primer_tramo * self.monto_diario + excedente * self.monto_diario * self.factor
        return round(total, 2)


class CalculadorMulta:
    def __init__(self, estrategia: EstrategiaMulta):
        self._estrategia = estrategia

    def set_estrategia(self, estrategia: EstrategiaMulta):
        self._estrategia = estrategia

    def calcular(self, dias_atraso: int) -> float:
        return self._estrategia.calcular(dias_atraso)


def crear_estrategia(nombre: str, monto_diario: float) -> EstrategiaMulta:
    estrategias = {
        "fija": MultaFija,
        "escalonada": MultaEscalonada,
    }
    if nombre not in estrategias:
        raise ValueError(f"Estrategia de multa desconocida: {nombre}")
    return estrategias[nombre](monto_diario)
