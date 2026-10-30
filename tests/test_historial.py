from datetime import date, timedelta

import pytest

from app.config import settings
from app.domain.enums import EstadoFisico
from app.exceptions import NoEncontradoError
from app.repositories.base import Paginacion
from app.schemas.prestamo import DevolucionCrear, LecturaRespuesta, PrestamoCrear
from app.services.prestamo_service import PrestamoService

HOY = date(2026, 10, 1)


def prestar_y_devolver(db, socio, ejemplar, sede, inicio, dias):
    servicio = PrestamoService(db)
    prestamo = servicio.solicitar(
        PrestamoCrear(socio_id=socio.id, ejemplar_id=ejemplar.id, sede_origen_id=sede.id, sede_destino_id=sede.id),
        hoy=inicio,
    )
    servicio.devolver(
        prestamo.id,
        DevolucionCrear(estado_fisico=EstadoFisico.BUENO, fecha_devolucion=inicio + timedelta(days=dias)),
    )
    return prestamo


def test_historial_solo_incluye_devueltos_del_socio_en_orden(db, datos):
    sede = datos.sede()
    socio, otro = datos.socio(), datos.socio()
    primero = prestar_y_devolver(db, socio, datos.ejemplar(datos.libro(titulo="Primero"), sede), sede, HOY, 3)
    segundo = prestar_y_devolver(db, socio, datos.ejemplar(datos.libro(titulo="Segundo"), sede), sede, HOY, 20)
    prestar_y_devolver(db, otro, datos.ejemplar(datos.libro(), sede), sede, HOY, 3)
    # un prestamo activo no es parte del historial
    PrestamoService(db).solicitar(
        PrestamoCrear(
            socio_id=socio.id,
            ejemplar_id=datos.ejemplar(datos.libro(), sede).id,
            sede_origen_id=sede.id,
            sede_destino_id=sede.id,
        ),
        hoy=HOY,
    )

    historial = PrestamoService(db).historial_de_socio(socio.id, Paginacion())
    assert historial.total == 2
    assert [p.id for p in historial.items] == [segundo.id, primero.id]
    lectura = LecturaRespuesta.desde_prestamo(historial.items[0])
    assert lectura.titulo == "Segundo"
    assert lectura.dias_atraso == 20 - settings.dias_prestamo
    assert lectura.multa > 0


def test_historial_de_socio_inexistente(db):
    with pytest.raises(NoEncontradoError):
        PrestamoService(db).historial_de_socio(9999, Paginacion())
