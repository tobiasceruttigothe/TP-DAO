from datetime import date, timedelta

import pytest

from app.config import settings
from app.domain.enums import EstadoEjemplar, EstadoFisico, EstadoReserva
from app.exceptions import ReglaNegocioError
from app.schemas.prestamo import DevolucionCrear, PrestamoCrear
from app.schemas.reserva import ReservaCrear
from app.services.prestamo_service import PrestamoService
from app.services.reserva_service import ReservaService
from app.services.sede_service import SedeService

HOY = date(2026, 10, 1)


@pytest.fixture
def escenario(datos):
    sede = datos.sede()
    libro = datos.libro()
    ejemplar = datos.ejemplar(libro, sede)
    return sede, libro, ejemplar


def reservar(db, socio, libro, sede):
    return ReservaService(db).crear(ReservaCrear(socio_id=socio.id, libro_id=libro.id, sede_id=sede.id), hoy=HOY)


def prestar(db, socio, ejemplar, sede):
    return PrestamoService(db).solicitar(
        PrestamoCrear(socio_id=socio.id, ejemplar_id=ejemplar.id, sede_origen_id=sede.id, sede_destino_id=sede.id),
        hoy=HOY,
    )


def test_reserva_con_ejemplar_libre_lo_aparta(db, datos, escenario):
    sede, libro, ejemplar = escenario
    reserva = reservar(db, datos.socio(), libro, sede)

    assert reserva.estado == EstadoReserva.DISPONIBLE
    assert reserva.ejemplar_id == ejemplar.id
    assert reserva.fecha_expiracion == HOY + timedelta(days=settings.dias_validez_reserva)
    assert ejemplar.estado == EstadoEjemplar.RESERVADO


def test_ejemplar_reservado_solo_lo_retira_quien_reservo(db, datos, escenario):
    sede, libro, ejemplar = escenario
    titular = datos.socio()
    reserva = reservar(db, titular, libro, sede)

    with pytest.raises(ReglaNegocioError, match="otro socio"):
        prestar(db, datos.socio(), ejemplar, sede)

    prestar(db, titular, ejemplar, sede)
    assert reserva.estado == EstadoReserva.CUMPLIDA


def test_reserva_pendiente_se_asigna_al_devolver(db, datos, escenario):
    sede, libro, ejemplar = escenario
    prestamo = prestar(db, datos.socio(), ejemplar, sede)
    reserva = reservar(db, datos.socio(), libro, sede)
    assert reserva.estado == EstadoReserva.PENDIENTE

    PrestamoService(db).devolver(prestamo.id, DevolucionCrear(estado_fisico=EstadoFisico.BUENO, fecha_devolucion=HOY))
    assert reserva.estado == EstadoReserva.DISPONIBLE
    assert ejemplar.estado == EstadoEjemplar.RESERVADO


def test_reservas_se_atienden_por_orden_de_llegada(db, datos, escenario):
    sede, libro, ejemplar = escenario
    prestamo = prestar(db, datos.socio(), ejemplar, sede)
    primera = reservar(db, datos.socio(), libro, sede)
    segunda = reservar(db, datos.socio(), libro, sede)

    PrestamoService(db).devolver(prestamo.id, DevolucionCrear(estado_fisico=EstadoFisico.BUENO, fecha_devolucion=HOY))
    assert primera.estado == EstadoReserva.DISPONIBLE
    assert segunda.estado == EstadoReserva.PENDIENTE

    ReservaService(db).cancelar(primera.id)
    assert segunda.estado == EstadoReserva.DISPONIBLE
    assert segunda.ejemplar_id == ejemplar.id


def test_no_duplica_reserva_activa(db, datos, escenario):
    sede, libro, _ = escenario
    socio = datos.socio()
    reservar(db, socio, libro, sede)
    with pytest.raises(ReglaNegocioError, match="ya tiene"):
        reservar(db, socio, libro, sede)


def test_no_reserva_en_sede_dada_de_baja(db, datos, escenario):
    sede, libro, _ = escenario
    SedeService(db).dar_de_baja(sede.id)
    with pytest.raises(ReglaNegocioError, match="dada de baja"):
        reservar(db, datos.socio(), libro, sede)


def test_no_reserva_libro_sin_ejemplares_en_la_sede(db, datos, escenario):
    _, libro, _ = escenario
    with pytest.raises(ReglaNegocioError, match="no tiene ejemplares"):
        reservar(db, datos.socio(), libro, datos.sede())


def test_reservas_vencidas_liberan_el_ejemplar(db, datos, escenario):
    sede, libro, ejemplar = escenario
    reserva = reservar(db, datos.socio(), libro, sede)

    vencidas = ReservaService(db).procesar_vencidas(hoy=reserva.fecha_expiracion + timedelta(days=1))
    assert vencidas == 1
    assert reserva.estado == EstadoReserva.VENCIDA
    assert ejemplar.estado == EstadoEjemplar.DISPONIBLE
