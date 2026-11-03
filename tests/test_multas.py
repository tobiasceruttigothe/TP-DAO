import pytest

from app.domain.enums import EstadoFisico
from app.domain.multas import (
    CalculadorMulta,
    DatosMulta,
    MultaAtrasoGrave,
    MultaAtrasoLeve,
    MultaPorDanio,
)


@pytest.fixture
def calculador():
    return CalculadorMulta(
        atraso_leve=MultaAtrasoLeve(500),
        atraso_grave=MultaAtrasoGrave(500, 1000, dias_leves=7),
        por_danio=MultaPorDanio({EstadoFisico.DANADO: 5000, EstadoFisico.DESTRUIDO: 20000}),
    )


# --- Cada estrategia por separado ---

def test_atraso_leve():
    assert MultaAtrasoLeve(500).calcular(DatosMulta(3)).monto == 1500


def test_atraso_grave_cobra_los_primeros_dias_al_monto_leve():
    # 7 x 500 + 3 x 1000
    assert MultaAtrasoGrave(500, 1000, dias_leves=7).calcular(DatosMulta(10)).monto == 6500


def test_cargo_por_danio():
    estrategia = MultaPorDanio({EstadoFisico.DANADO: 5000})
    assert estrategia.calcular(DatosMulta(0, EstadoFisico.DANADO)).monto == 5000
    assert not estrategia.cobra(EstadoFisico.BUENO)
    assert not estrategia.cobra(None)


# --- El calculador elige las estrategias segun el caso ---

def tipos(calculador, datos):
    return [type(e) for e in calculador.estrategias_para(datos)]


@pytest.mark.parametrize(
    "dias, estado, esperadas, total",
    [
        (0, EstadoFisico.BUENO, [], 0),
        (0, None, [], 0),
        (1, EstadoFisico.BUENO, [MultaAtrasoLeve], 500),
        (7, EstadoFisico.BUENO, [MultaAtrasoLeve], 3500),
        (8, EstadoFisico.BUENO, [MultaAtrasoGrave], 4500),
        (36, None, [MultaAtrasoGrave], 32500),
        (3, EstadoFisico.REGULAR, [MultaAtrasoLeve], 1500),
        (3, EstadoFisico.DANADO, [MultaAtrasoLeve, MultaPorDanio], 6500),
        (10, EstadoFisico.DANADO, [MultaAtrasoGrave, MultaPorDanio], 11500),
        (0, EstadoFisico.DESTRUIDO, [MultaPorDanio], 20000),
    ],
)
def test_eleccion_de_estrategias(calculador, dias, estado, esperadas, total):
    datos = DatosMulta(dias, estado)
    assert tipos(calculador, datos) == esperadas
    assert calculador.calcular(datos).total == total


def test_detalle_de_la_multa(calculador):
    resultado = calculador.calcular(DatosMulta(10, EstadoFisico.DANADO))
    assert [(c.concepto, c.monto) for c in resultado.conceptos] == [
        ("Atraso grave: 7 días × $500 + 3 días × $1.000", 6500),
        ("Devuelto dañado", 5000),
    ]
