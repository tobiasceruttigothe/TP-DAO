from datetime import date, datetime, timedelta

import pytest

from app.config import settings
from app.domain.enums import EstadoFisico
from app.schemas.prestamo import DevolucionCrear, PrestamoCrear
from app.services.prestamo_service import PrestamoService
from app.services.remito_service import RemitoService
from app.services.reporte_service import ReporteService

HOY = date(2026, 10, 1)


def pedir(db, socio, ejemplar, origen, destino):
    return PrestamoService(db).solicitar(
        PrestamoCrear(socio_id=socio.id, ejemplar_id=ejemplar.id, sede_origen_id=origen.id, sede_destino_id=destino.id),
        hoy=HOY,
    )


def enviar(db, remito, estado_fisico=EstadoFisico.BUENO, horas=None):
    servicio = RemitoService(db)
    servicio.empaquetar(remito.id)
    servicio.despachar(remito.id)
    if horas is not None:
        remito.fecha_despacho = datetime.now() - timedelta(hours=horas)
    servicio.recibir(remito.id, estado_fisico, hoy=HOY)


@pytest.fixture
def red(datos):
    centro, norte, sur = datos.sede("Centro"), datos.sede("Norte"), datos.sede("Sur")
    return centro, norte, sur


def test_activos_y_en_transito(db, datos, red):
    centro, norte, _ = red
    libro = datos.libro()
    pedir(db, datos.socio(), datos.ejemplar(libro, centro), centro, centro)
    viajando = pedir(db, datos.socio(), datos.ejemplar(libro, centro), centro, norte)
    RemitoService(db).empaquetar(viajando.remitos[0].id)
    RemitoService(db).despachar(viajando.remitos[0].id)

    reporte = ReporteService(db).activos_y_en_transito(HOY)
    assert reporte.total_prestamos_activos == 1
    assert reporte.total_en_transito == 1
    assert reporte.en_transito[0].sede_destino == "Norte"


def test_vencidos_y_multas(db, datos, red):
    centro, _, _ = red
    libro = datos.libro()
    socio = datos.socio()
    devuelto = pedir(db, socio, datos.ejemplar(libro, centro), centro, centro)
    PrestamoService(db).devolver(
        devuelto.id,
        DevolucionCrear(estado_fisico=EstadoFisico.BUENO, fecha_devolucion=devuelto.fecha_vencimiento + timedelta(days=2)),
    )
    pendiente = pedir(db, socio, datos.ejemplar(libro, centro), centro, centro)

    fecha = pendiente.fecha_vencimiento + timedelta(days=3)
    reporte = ReporteService(db).vencidos_y_multas(fecha)

    monto = settings.multa_monto_diario
    assert reporte.total_prestamos_vencidos == 1
    item = reporte.socios[0]
    assert item.multas_cobradas == 2 * monto
    assert item.multas_pendientes == 3 * monto
    assert item.total_acumulado == 5 * monto


def test_libros_mas_solicitados_solo_cuenta_intersede(db, datos, red):
    centro, norte, _ = red
    popular, otro = datos.libro(titulo="Popular"), datos.libro(titulo="Otro")
    for _ in range(2):
        pedir(db, datos.socio(), datos.ejemplar(popular, centro), centro, norte)
    pedir(db, datos.socio(), datos.ejemplar(otro, centro), centro, norte)
    pedir(db, datos.socio(), datos.ejemplar(otro, centro), centro, centro)  # local, no cuenta

    ranking = ReporteService(db).libros_mas_solicitados_intersede()
    assert [(r.titulo, r.cantidad_prestamos) for r in ranking] == [("Popular", 2), ("Otro", 1)]


def test_disponibilidad_por_sede(db, datos, red):
    centro, norte, _ = red
    libro = datos.libro()
    datos.ejemplar(libro, centro)
    prestado = datos.ejemplar(libro, centro)
    datos.ejemplar(datos.libro(), norte)
    pedir(db, datos.socio(), prestado, centro, centro)

    por_sede = {s.sede: s for s in ReporteService(db).disponibilidad_por_sede()}
    assert por_sede["Centro"].total_ejemplares == 2
    assert por_sede["Centro"].disponibles == 1
    assert por_sede["Centro"].porcentaje_disponible == 50.0
    assert por_sede["Centro"].por_estado == {"DISPONIBLE": 1, "PRESTADO": 1}
    assert por_sede["Norte"].titulos_distintos == 1
    assert por_sede["Sur"].total_ejemplares == 0


def test_tasa_envios_y_movimientos(db, datos, red):
    centro, norte, sur = red
    libro = datos.libro()

    ok = pedir(db, datos.socio(), datos.ejemplar(libro, centro), centro, norte)
    enviar(db, ok.remitos[0], horas=10)
    danado = pedir(db, datos.socio(), datos.ejemplar(libro, centro), centro, norte)
    enviar(db, danado.remitos[0], EstadoFisico.DANADO, horas=20)
    perdido = pedir(db, datos.socio(), datos.ejemplar(libro, centro), centro, sur)
    RemitoService(db).empaquetar(perdido.remitos[0].id)
    RemitoService(db).despachar(perdido.remitos[0].id)
    RemitoService(db).marcar_extraviado(perdido.remitos[0].id)
    cancelado = pedir(db, datos.socio(), datos.ejemplar(libro, centro), centro, sur)
    RemitoService(db).cancelar(cancelado.remitos[0].id)

    envios = ReporteService(db).tasa_envios()
    assert (envios.recibidos_ok, envios.recibidos_con_danio, envios.extraviados, envios.cancelados) == (1, 1, 1, 1)
    assert envios.tasa_exito == pytest.approx(33.3, abs=0.1)
    assert envios.tasa_incidencias == pytest.approx(66.7, abs=0.1)

    movimientos = {(m.sede_origen, m.sede_destino): m for m in ReporteService(db).movimiento_entre_sedes()}
    centro_norte = movimientos[("Centro", "Norte")]
    assert centro_norte.envios == 2
    assert centro_norte.incidencias == 1
    assert centro_norte.promedio_horas_transito == pytest.approx(15, abs=0.1)
    assert movimientos[("Centro", "Sur")].envios == 1  # el cancelado no cuenta
