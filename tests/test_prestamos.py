from datetime import date, timedelta

import pytest

from app.config import settings
from app.domain.enums import EstadoEjemplar, EstadoFisico, EstadoPrestamo, TipoPrestamo, TipoRemito
from app.exceptions import NoEncontradoError, ReglaNegocioError, TransicionInvalidaError
from app.schemas.prestamo import DevolucionCrear, PrestamoCrear
from app.services.prestamo_service import PrestamoService
from app.services.remito_service import RemitoService
from app.services.sede_service import SedeService
from app.services.socio_service import SocioService

HOY = date(2026, 10, 1)


@pytest.fixture
def escenario(datos):
    centro = datos.sede("Centro")
    norte = datos.sede("Norte")
    libro = datos.libro(titulo="Ficciones")
    ejemplar = datos.ejemplar(libro, centro)
    socio = datos.socio()
    return centro, norte, libro, ejemplar, socio


def pedir(db, socio, ejemplar, origen, destino, hoy=HOY):
    return PrestamoService(db).solicitar(
        PrestamoCrear(socio_id=socio.id, ejemplar_id=ejemplar.id, sede_origen_id=origen.id, sede_destino_id=destino.id),
        hoy=hoy,
    )


def devolver(db, prestamo, fecha, estado_fisico=EstadoFisico.BUENO):
    return PrestamoService(db).devolver(
        prestamo.id, DevolucionCrear(estado_fisico=estado_fisico, fecha_devolucion=fecha)
    )


def test_prestamo_local_queda_activo(db, escenario):
    centro, _, _, ejemplar, socio = escenario
    prestamo = pedir(db, socio, ejemplar, centro, centro)

    assert prestamo.tipo == TipoPrestamo.LOCAL
    assert prestamo.estado == EstadoPrestamo.ACTIVO
    assert prestamo.fecha_vencimiento == HOY + timedelta(days=settings.dias_prestamo)
    assert ejemplar.estado == EstadoEjemplar.PRESTADO
    assert prestamo.remitos == []


def test_no_presta_ejemplar_no_disponible(db, datos, escenario):
    centro, _, _, ejemplar, socio = escenario
    pedir(db, socio, ejemplar, centro, centro)
    with pytest.raises(ReglaNegocioError, match="no esta disponible"):
        pedir(db, datos.socio(), ejemplar, centro, centro)


def test_no_presta_a_socio_inhabilitado(db, escenario):
    centro, _, _, ejemplar, socio = escenario
    SocioService(db).inhabilitar(socio.id, "deuda")
    with pytest.raises(ReglaNegocioError, match="inhabilitado"):
        pedir(db, socio, ejemplar, centro, centro)


def test_ejemplar_debe_ser_de_la_sede_origen(db, escenario):
    _, norte, _, ejemplar, socio = escenario
    with pytest.raises(ReglaNegocioError, match="no pertenece"):
        pedir(db, socio, ejemplar, norte, norte)


@pytest.mark.parametrize("cual", ["origen", "destino"])
def test_no_presta_con_sede_dada_de_baja(db, escenario, cual):
    centro, norte, _, ejemplar, socio = escenario
    SedeService(db).dar_de_baja(centro.id if cual == "origen" else norte.id)
    with pytest.raises(ReglaNegocioError, match="dada de baja"):
        pedir(db, socio, ejemplar, centro, norte)


def test_maximo_de_prestamos(db, datos, escenario):
    centro, _, libro, _, socio = escenario
    for _ in range(settings.max_prestamos_activos):
        pedir(db, socio, datos.ejemplar(libro, centro), centro, centro)
    with pytest.raises(ReglaNegocioError, match="maximo"):
        pedir(db, socio, datos.ejemplar(libro, centro), centro, centro)


def test_socio_con_prestamo_vencido_no_puede_pedir_otro(db, datos, escenario):
    centro, _, libro, ejemplar, socio = escenario
    pedir(db, socio, ejemplar, centro, centro)
    despues_del_vencimiento = HOY + timedelta(days=settings.dias_prestamo + 1)
    with pytest.raises(ReglaNegocioError, match="vencidos"):
        pedir(db, socio, datos.ejemplar(libro, centro), centro, centro, hoy=despues_del_vencimiento)


def test_prestamo_inexistente(db):
    with pytest.raises(NoEncontradoError):
        PrestamoService(db).obtener(9999)


def test_devolucion_en_termino_sin_multa(db, escenario):
    centro, _, _, ejemplar, socio = escenario
    prestamo = pedir(db, socio, ejemplar, centro, centro)
    devolver(db, prestamo, HOY + timedelta(days=5))

    assert prestamo.estado == EstadoPrestamo.DEVUELTO
    assert prestamo.multa == 0
    assert ejemplar.estado == EstadoEjemplar.DISPONIBLE


def test_devolucion_con_atraso_genera_multa(db, escenario):
    centro, _, _, ejemplar, socio = escenario
    prestamo = pedir(db, socio, ejemplar, centro, centro)
    devolver(db, prestamo, prestamo.fecha_vencimiento + timedelta(days=4))
    assert prestamo.multa == 4 * settings.multa_monto_diario


def test_devolucion_danado_pasa_a_reparacion(db, escenario):
    centro, _, _, ejemplar, socio = escenario
    prestamo = pedir(db, socio, ejemplar, centro, centro)
    devolver(db, prestamo, HOY, EstadoFisico.DANADO)
    assert ejemplar.estado == EstadoEjemplar.EN_REPARACION
    assert ejemplar.estado_fisico == EstadoFisico.DANADO


def test_no_se_devuelve_dos_veces(db, escenario):
    centro, _, _, ejemplar, socio = escenario
    prestamo = pedir(db, socio, ejemplar, centro, centro)
    devolver(db, prestamo, HOY)
    with pytest.raises(ReglaNegocioError):
        devolver(db, prestamo, HOY)


def test_circuito_interbibliotecario_completo(db, escenario):
    centro, norte, _, ejemplar, socio = escenario
    remitos = RemitoService(db)

    prestamo = pedir(db, socio, ejemplar, centro, norte)
    assert prestamo.tipo == TipoPrestamo.INTERBIBLIOTECARIO
    assert prestamo.estado == EstadoPrestamo.SOLICITADO
    ida = prestamo.remitos[0]
    assert ida.tipo == TipoRemito.IDA
    assert (ida.sede_origen_id, ida.sede_destino_id) == (centro.id, norte.id)

    remitos.empaquetar(ida.id)
    remitos.despachar(ida.id)
    assert prestamo.estado == EstadoPrestamo.EN_TRANSITO
    assert ejemplar.estado == EstadoEjemplar.EN_TRANSITO

    remitos.recibir(ida.id, hoy=HOY)
    assert prestamo.estado == EstadoPrestamo.ACTIVO
    assert prestamo.fecha_vencimiento == HOY + timedelta(days=settings.dias_prestamo)

    devolver(db, prestamo, HOY + timedelta(days=3))
    retorno = prestamo.remitos[1]
    assert retorno.tipo == TipoRemito.RETORNO
    assert (retorno.sede_origen_id, retorno.sede_destino_id) == (norte.id, centro.id)

    remitos.empaquetar(retorno.id)
    remitos.despachar(retorno.id)
    remitos.recibir(retorno.id)
    assert ejemplar.estado == EstadoEjemplar.DISPONIBLE
    assert [m.estado_nuevo for m in retorno.movimientos] == ["PENDIENTE", "EMPAQUETADO", "DESPACHADO", "RECIBIDO"]


def test_no_se_despacha_si_la_sede_se_dio_de_baja(db, escenario):
    centro, norte, _, ejemplar, socio = escenario
    prestamo = pedir(db, socio, ejemplar, centro, norte)
    ida = prestamo.remitos[0]
    RemitoService(db).empaquetar(ida.id)
    SedeService(db).dar_de_baja(norte.id)
    with pytest.raises(ReglaNegocioError, match="dada de baja"):
        RemitoService(db).despachar(ida.id)


def test_cancelar_remito_libera_ejemplar(db, escenario):
    centro, norte, _, ejemplar, socio = escenario
    prestamo = pedir(db, socio, ejemplar, centro, norte)
    RemitoService(db).cancelar(prestamo.remitos[0].id)
    assert prestamo.estado == EstadoPrestamo.CANCELADO
    assert ejemplar.estado == EstadoEjemplar.DISPONIBLE


def test_extravio_cancela_prestamo(db, escenario):
    centro, norte, _, ejemplar, socio = escenario
    prestamo = pedir(db, socio, ejemplar, centro, norte)
    ida = prestamo.remitos[0]
    RemitoService(db).empaquetar(ida.id)
    RemitoService(db).despachar(ida.id)
    RemitoService(db).marcar_extraviado(ida.id, "no llego")
    assert prestamo.estado == EstadoPrestamo.CANCELADO
    assert ejemplar.estado == EstadoEjemplar.EXTRAVIADO


def test_remito_de_retorno_no_se_cancela(db, escenario):
    centro, norte, _, ejemplar, socio = escenario
    prestamo = pedir(db, socio, ejemplar, centro, norte)
    ida = prestamo.remitos[0]
    for paso in (RemitoService(db).empaquetar, RemitoService(db).despachar):
        paso(ida.id)
    RemitoService(db).recibir(ida.id, hoy=HOY)
    devolver(db, prestamo, HOY)
    with pytest.raises(ReglaNegocioError):
        RemitoService(db).cancelar(prestamo.remitos[1].id)


def test_transicion_invalida_desde_el_servicio(db, escenario):
    centro, norte, _, ejemplar, socio = escenario
    prestamo = pedir(db, socio, ejemplar, centro, norte)
    with pytest.raises(TransicionInvalidaError):
        RemitoService(db).recibir(prestamo.remitos[0].id)
