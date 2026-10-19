import pytest

from app.domain.enums import TipoRemito
from app.domain.estados_remito import estado_desde_nombre
from app.exceptions import TransicionInvalidaError
from app.models import Remito


@pytest.fixture
def remito():
    r = Remito(numero="R-000001", tipo=TipoRemito.IDA)
    r.registrar_creacion()
    return r


def test_recorrido_completo(remito):
    remito.empaquetar()
    remito.despachar("sale en camioneta")
    remito.recibir()

    assert remito.estado == "RECIBIDO"
    assert remito.estado_actual.es_final
    assert [m.estado_nuevo for m in remito.movimientos] == ["PENDIENTE", "EMPAQUETADO", "DESPACHADO", "RECIBIDO"]
    assert remito.movimientos[2].observacion == "sale en camioneta"
    assert remito.fecha_despacho is not None
    assert remito.fecha_recepcion >= remito.fecha_despacho
    assert remito.horas_en_transito >= 0


def test_no_se_puede_despachar_sin_empaquetar(remito):
    with pytest.raises(TransicionInvalidaError):
        remito.despachar()
    assert remito.estado == "PENDIENTE"
    assert len(remito.movimientos) == 1


def test_no_se_puede_recibir_dos_veces(remito):
    remito.empaquetar()
    remito.despachar()
    remito.recibir()
    with pytest.raises(TransicionInvalidaError):
        remito.recibir()


def test_cancelar_solo_antes_de_despachar(remito):
    remito.empaquetar()
    remito.despachar()
    with pytest.raises(TransicionInvalidaError):
        remito.cancelar()


def test_extravio_solo_en_viaje(remito):
    with pytest.raises(TransicionInvalidaError):
        remito.marcar_extraviado()
    remito.empaquetar()
    remito.despachar()
    remito.marcar_extraviado("no llego")
    assert remito.estado == "EXTRAVIADO"
    with pytest.raises(TransicionInvalidaError):
        remito.recibir()


@pytest.mark.parametrize("estado", ["RECIBIDO", "EXTRAVIADO", "CANCELADO"])
def test_estados_finales_no_admiten_cambios(estado):
    r = Remito(numero="R-1", tipo=TipoRemito.IDA, estado=estado)
    for accion in (r.empaquetar, r.despachar, r.recibir, r.marcar_extraviado, r.cancelar):
        with pytest.raises(TransicionInvalidaError):
            accion()


def test_estado_desconocido():
    with pytest.raises(ValueError):
        estado_desde_nombre("VOLANDO")
