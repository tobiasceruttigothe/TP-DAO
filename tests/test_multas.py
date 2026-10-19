import pytest

from app.domain.multas import CalculadorMulta, MultaEscalonada, MultaFija, crear_estrategia


def test_multa_fija():
    assert MultaFija(500).calcular(3) == 1500
    assert MultaFija(500).calcular(0) == 0
    assert MultaFija(500).calcular(-2) == 0


def test_multa_escalonada():
    estrategia = MultaEscalonada(100)
    assert estrategia.calcular(5) == 500
    assert estrategia.calcular(7) == 700
    # 7 dias a 100 + 3 dias a 200
    assert estrategia.calcular(10) == 1300


def test_cambiar_estrategia_en_tiempo_de_ejecucion():
    calculador = CalculadorMulta(MultaFija(100))
    assert calculador.calcular(10) == 1000
    calculador.set_estrategia(MultaEscalonada(100))
    assert calculador.calcular(10) == 1300


def test_crear_estrategia_por_nombre():
    assert isinstance(crear_estrategia("fija", 10), MultaFija)
    assert isinstance(crear_estrategia("escalonada", 10), MultaEscalonada)
    with pytest.raises(ValueError):
        crear_estrategia("otra", 10)
