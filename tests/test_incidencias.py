from datetime import date

import pytest

from app.domain.enums import EstadoEjemplar, EstadoFisico, EstadoPrestamo, TipoIncidencia
from app.repositories.base import Paginacion
from app.schemas.prestamo import DevolucionCrear, PrestamoCrear
from app.services.prestamo_service import PrestamoService
from app.services.remito_service import RemitoService
from app.services.reporte_service import ReporteService

HOY = date(2026, 10, 1)


@pytest.fixture
def interbibliotecario(db, datos):
    centro, norte = datos.sede("Centro"), datos.sede("Norte")
    ejemplar = datos.ejemplar(datos.libro(), centro)
    prestamo = PrestamoService(db).solicitar(
        PrestamoCrear(
            socio_id=datos.socio().id, ejemplar_id=ejemplar.id, sede_origen_id=centro.id, sede_destino_id=norte.id
        ),
        hoy=HOY,
    )
    remito = prestamo.remitos[0]
    RemitoService(db).empaquetar(remito.id)
    RemitoService(db).despachar(remito.id)
    return prestamo, remito, ejemplar


def test_recepcion_sin_problemas_no_genera_incidencia(db, interbibliotecario):
    prestamo, remito, _ = interbibliotecario
    RemitoService(db).recibir(remito.id, EstadoFisico.BUENO, hoy=HOY)
    assert remito.incidencias == []
    assert not remito.tuvo_incidencia


def test_recepcion_con_danio_registra_incidencia(db, interbibliotecario):
    prestamo, remito, ejemplar = interbibliotecario
    RemitoService(db).recibir(remito.id, EstadoFisico.DANADO, "tapa rota", hoy=HOY)

    assert [(i.tipo, i.descripcion) for i in remito.incidencias] == [(TipoIncidencia.DANIO, "tapa rota")]
    assert prestamo.estado == EstadoPrestamo.ACTIVO
    assert ejemplar.estado_fisico == EstadoFisico.DANADO


def test_recepcion_destruido_cancela_prestamo_y_da_de_baja(db, interbibliotecario):
    prestamo, remito, ejemplar = interbibliotecario
    RemitoService(db).recibir(remito.id, EstadoFisico.DESTRUIDO, "mojado", hoy=HOY)

    assert remito.incidencias[0].tipo == TipoIncidencia.DESTRUCCION
    assert prestamo.estado == EstadoPrestamo.CANCELADO
    assert ejemplar.estado == EstadoEjemplar.BAJA


def test_extravio_registra_incidencia(db, interbibliotecario):
    _, remito, _ = interbibliotecario
    RemitoService(db).marcar_extraviado(remito.id, "no llego")
    assert remito.incidencias[0].tipo == TipoIncidencia.EXTRAVIO


def test_retorno_destruido_da_de_baja(db, interbibliotecario):
    prestamo, remito, ejemplar = interbibliotecario
    servicio = RemitoService(db)
    servicio.recibir(remito.id, hoy=HOY)
    PrestamoService(db).devolver(prestamo.id, DevolucionCrear(estado_fisico=EstadoFisico.BUENO, fecha_devolucion=HOY))
    retorno = prestamo.remitos[1]
    servicio.empaquetar(retorno.id)
    servicio.despachar(retorno.id)
    servicio.recibir(retorno.id, EstadoFisico.DESTRUIDO)
    assert ejemplar.estado == EstadoEjemplar.BAJA


def test_devolucion_destruido_no_genera_retorno(db, interbibliotecario):
    prestamo, remito, ejemplar = interbibliotecario
    RemitoService(db).recibir(remito.id, hoy=HOY)
    PrestamoService(db).devolver(
        prestamo.id, DevolucionCrear(estado_fisico=EstadoFisico.DESTRUIDO, fecha_devolucion=HOY)
    )
    assert len(prestamo.remitos) == 1
    assert ejemplar.estado == EstadoEjemplar.BAJA


def test_listado_de_incidencias_filtra_por_tipo_y_sede(db, datos, interbibliotecario):
    prestamo, remito, _ = interbibliotecario
    RemitoService(db).recibir(remito.id, EstadoFisico.DANADO, hoy=HOY)
    servicio = RemitoService(db)

    todas = servicio.listar_incidencias(Paginacion())
    assert todas.total == 1
    assert servicio.listar_incidencias(Paginacion(), tipo=TipoIncidencia.EXTRAVIO).total == 0
    assert servicio.listar_incidencias(Paginacion(), sede_id=prestamo.sede_destino_id).total == 1
    assert servicio.listar_incidencias(Paginacion(), sede_id=datos.sede().id).total == 0


def test_reporte_de_envios_cuenta_destruidos(db, interbibliotecario):
    _, remito, _ = interbibliotecario
    RemitoService(db).recibir(remito.id, EstadoFisico.DESTRUIDO, hoy=HOY)
    envios = ReporteService(db).tasa_envios()
    assert envios.recibidos_destruidos == 1
    assert envios.recibidos_ok == 0
    assert envios.tasa_incidencias == 100.0
