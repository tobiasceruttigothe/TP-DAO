from datetime import date, timedelta

import pytest

from app.config import settings
from app.domain.enums import EstadoFisico, EstadoReserva
from app.exceptions import ReglaNegocioError
from app.schemas.prestamo import DevolucionCrear, PrestamoCrear
from app.schemas.reserva import ReservaCrear
from app.services.prestamo_service import PrestamoService
from app.services.proceso_service import ProcesoVencimientos
from app.services.reserva_service import ReservaService
from app.services.socio_service import SocioService

HOY = date(2026, 10, 1)


@pytest.fixture
def prestamo_local(db, datos):
    sede = datos.sede()
    socio = datos.socio()
    prestamo = PrestamoService(db).solicitar(
        PrestamoCrear(
            socio_id=socio.id,
            ejemplar_id=datos.ejemplar(datos.libro(titulo="Ficciones"), sede).id,
            sede_origen_id=sede.id,
            sede_destino_id=sede.id,
        ),
        hoy=HOY,
    )
    return prestamo, socio


def dia_con_atraso(prestamo, dias):
    return prestamo.fecha_vencimiento + timedelta(days=dias)


def test_no_inhabilita_antes_del_limite(db, prestamo_local):
    prestamo, socio = prestamo_local
    inhabilitados = SocioService(db).inhabilitar_por_atraso(dia_con_atraso(prestamo, settings.dias_atraso_inhabilitacion))
    assert inhabilitados == []
    assert socio.habilitado


def test_inhabilita_pasado_el_limite_con_motivo(db, prestamo_local):
    prestamo, socio = prestamo_local
    dias = settings.dias_atraso_inhabilitacion + 1
    inhabilitados = SocioService(db).inhabilitar_por_atraso(dia_con_atraso(prestamo, dias))

    assert inhabilitados == [socio]
    assert not socio.habilitado
    assert f"N° {prestamo.id}" in socio.motivo_inhabilitacion
    assert "Ficciones" in socio.motivo_inhabilitacion
    assert f"{dias} días" in socio.motivo_inhabilitacion


def test_no_vuelve_a_procesar_a_un_inhabilitado(db, prestamo_local):
    prestamo, socio = prestamo_local
    servicio = SocioService(db)
    dia = dia_con_atraso(prestamo, settings.dias_atraso_inhabilitacion + 1)
    servicio.inhabilitar_por_atraso(dia)
    assert servicio.inhabilitar_por_atraso(dia) == []


def test_devuelto_a_tiempo_no_cuenta(db, prestamo_local):
    prestamo, socio = prestamo_local
    PrestamoService(db).devolver(prestamo.id, DevolucionCrear(estado_fisico=EstadoFisico.BUENO, fecha_devolucion=HOY))
    assert SocioService(db).inhabilitar_por_atraso(dia_con_atraso(prestamo, 100)) == []


def test_inhabilitado_por_atraso_no_puede_pedir_ni_reservar(db, datos, prestamo_local):
    prestamo, socio = prestamo_local
    SocioService(db).inhabilitar_por_atraso(dia_con_atraso(prestamo, settings.dias_atraso_inhabilitacion + 1))
    sede = datos.sede()
    with pytest.raises(ReglaNegocioError, match="inhabilitado"):
        ReservaService(db).crear(ReservaCrear(socio_id=socio.id, libro_id=datos.ejemplar(datos.libro(), sede).libro_id, sede_id=sede.id))


def test_proceso_vence_reservas_e_inhabilita(db, datos, prestamo_local):
    prestamo, socio = prestamo_local
    sede = datos.sede()
    libro = datos.libro()
    datos.ejemplar(libro, sede)
    reserva = ReservaService(db).crear(ReservaCrear(socio_id=datos.socio().id, libro_id=libro.id, sede_id=sede.id), hoy=HOY)

    resultado = ProcesoVencimientos(db).ejecutar(dia_con_atraso(prestamo, settings.dias_atraso_inhabilitacion + 1))
    assert resultado.reservas_vencidas == 1
    assert reserva.estado == EstadoReserva.VENCIDA
    assert resultado.socios_inhabilitados == [socio]


def test_atraso_y_multa_a_la_fecha(db, prestamo_local):
    prestamo, _ = prestamo_local
    # El prestamo del fixture empezo el 01/10/2026; a hoy (fecha real del sistema) puede estar vencido o no
    esperado = max((date.today() - prestamo.fecha_vencimiento).days, 0)
    assert prestamo.dias_atraso_actual == esperado
    assert prestamo.multa_actual == esperado * settings.multa_monto_diario

    PrestamoService(db).devolver(
        prestamo.id, DevolucionCrear(estado_fisico=EstadoFisico.BUENO, fecha_devolucion=dia_con_atraso(prestamo, 3))
    )
    assert prestamo.dias_atraso_actual == 3
    assert prestamo.multa_actual == prestamo.multa == 3 * settings.multa_monto_diario


def test_socio_con_vencidos(db, datos):
    sede = datos.sede()
    socio = datos.socio()
    hace_mucho = date.today() - timedelta(days=settings.dias_prestamo + 2)
    PrestamoService(db).solicitar(
        PrestamoCrear(
            socio_id=socio.id,
            ejemplar_id=datos.ejemplar(datos.libro(), sede).id,
            sede_origen_id=sede.id,
            sede_destino_id=sede.id,
        ),
        hoy=hace_mucho,
    )
    db.refresh(socio)
    assert socio.tiene_vencidos
    assert not datos.socio().tiene_vencidos
