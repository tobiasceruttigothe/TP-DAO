from datetime import date

import pytest

from app.domain.enums import EstadoPedido, EstadoPrestamo, EstadoReserva, TipoNotificacion, TipoPrestamo
from app.exceptions import ReglaNegocioError, SinPermisoError
from app.models import Notificacion
from app.schemas.pedido import PedidoCrear
from app.services.pedido_service import PedidoService
from app.services.socio_service import SocioService


@pytest.fixture
def red(db, datos):
    centro, norte = datos.sede("Centro"), datos.sede("Norte")
    libro = datos.libro(titulo="Rayuela")
    admin = datos.admin()
    socio = datos.socio()
    usuario = datos.usuario_de(socio)
    return centro, norte, libro, admin, socio, usuario


def pedir(db, socio, libro, sede):
    return PedidoService(db).crear(socio, PedidoCrear(libro_id=libro.id, sede_id=sede.id))


def notificaciones_de(db, usuario):
    return db.query(Notificacion).filter_by(usuario_id=usuario.id).order_by(Notificacion.id).all()


def test_crear_pedido_avisa_a_los_administradores(db, datos, red):
    centro, _, libro, admin, socio, _ = red
    datos.ejemplar(libro, centro)
    pedido = pedir(db, socio, libro, centro)

    assert pedido.estado == EstadoPedido.PENDIENTE
    assert [n.tipo for n in notificaciones_de(db, admin)] == [TipoNotificacion.PEDIDO_NUEVO]


def test_aprobar_con_reserva_si_hay_ejemplar(db, datos, red, correos):
    centro, _, libro, _, socio, usuario = red
    datos.ejemplar(libro, centro)
    pedido = PedidoService(db).reservar(pedir(db, socio, libro, centro).id)

    assert pedido.estado == EstadoPedido.APROBADO
    assert pedido.reserva.estado == EstadoReserva.DISPONIBLE
    tipos = [n.tipo for n in notificaciones_de(db, usuario)]
    assert TipoNotificacion.PEDIDO_APROBADO in tipos
    assert TipoNotificacion.RESERVA_DISPONIBLE in tipos
    assert usuario.email in [c.destinatario for c in correos]


def test_aprobar_con_reserva_en_espera(db, datos, red):
    centro, _, libro, _, socio, _ = red
    otro = datos.socio()
    ejemplar = datos.ejemplar(libro, centro)
    from app.schemas.prestamo import PrestamoCrear
    from app.services.prestamo_service import PrestamoService

    PrestamoService(db).solicitar(
        PrestamoCrear(socio_id=otro.id, ejemplar_id=ejemplar.id, sede_origen_id=centro.id, sede_destino_id=centro.id)
    )
    pedido = PedidoService(db).reservar(pedir(db, socio, libro, centro).id)
    assert pedido.reserva.estado == EstadoReserva.PENDIENTE
    assert "espera" in pedido.resolucion


def test_aprobar_enviando_desde_otra_sede(db, datos, red):
    centro, norte, libro, _, socio, _ = red
    datos.ejemplar(libro, centro)
    pedido = PedidoService(db).enviar_desde(pedir(db, socio, libro, norte).id, centro.id)

    assert pedido.estado == EstadoPedido.APROBADO
    assert pedido.prestamo.tipo == TipoPrestamo.INTERBIBLIOTECARIO
    assert pedido.prestamo.estado == EstadoPrestamo.SOLICITADO
    assert (pedido.prestamo.sede_origen_id, pedido.prestamo.sede_destino_id) == (centro.id, norte.id)
    assert pedido.prestamo.remitos


def test_enviar_valida_la_sede_de_origen(db, datos, red):
    centro, norte, libro, _, socio, _ = red
    datos.ejemplar(libro, centro)
    pedido = pedir(db, socio, libro, norte)
    with pytest.raises(ReglaNegocioError, match="misma sede"):
        PedidoService(db).enviar_desde(pedido.id, norte.id)
    with pytest.raises(ReglaNegocioError, match="no tiene ejemplares"):
        PedidoService(db).enviar_desde(pedido.id, datos.sede().id)


def test_rechazar_avisa_con_el_motivo(db, datos, red):
    centro, _, libro, _, socio, usuario = red
    datos.ejemplar(libro, centro)
    pedido = PedidoService(db).rechazar(pedir(db, socio, libro, centro).id, "Ejemplar en restauración")

    assert pedido.estado == EstadoPedido.RECHAZADO
    aviso = notificaciones_de(db, usuario)[-1]
    assert aviso.tipo == TipoNotificacion.PEDIDO_RECHAZADO
    assert "restauración" in aviso.mensaje


def test_un_pedido_resuelto_no_se_vuelve_a_resolver(db, datos, red):
    centro, _, libro, _, socio, _ = red
    datos.ejemplar(libro, centro)
    pedido = PedidoService(db).rechazar(pedir(db, socio, libro, centro).id, "No")
    with pytest.raises(ReglaNegocioError, match="ya está"):
        PedidoService(db).reservar(pedido.id)


def test_validaciones_al_pedir(db, datos, red):
    centro, _, libro, _, socio, _ = red
    with pytest.raises(ReglaNegocioError, match="no tiene ejemplares"):
        pedir(db, socio, libro, centro)
    datos.ejemplar(libro, centro)
    pedir(db, socio, libro, centro)
    with pytest.raises(ReglaNegocioError, match="pendiente"):
        pedir(db, socio, libro, centro)
    SocioService(db).inhabilitar(socio.id, "deuda")
    with pytest.raises(ReglaNegocioError, match="inhabilitado"):
        pedir(db, socio, datos.libro(), centro)


def test_el_socio_cancela_solo_sus_pedidos(db, datos, red):
    centro, _, libro, _, socio, _ = red
    datos.ejemplar(libro, centro)
    pedido = pedir(db, socio, libro, centro)
    with pytest.raises(SinPermisoError):
        PedidoService(db).cancelar(datos.socio(), pedido.id)
    assert PedidoService(db).cancelar(socio, pedido.id).estado == EstadoPedido.CANCELADO


def test_circuito_por_api(client, socio_conectado, datos, db):
    cliente_socio, socio = socio_conectado
    centro = datos.sede("Centro")
    libro = datos.libro()
    datos.ejemplar(libro, centro)

    r = cliente_socio.post("/mi/pedidos", json={"libro_id": libro.id, "sede_id": centro.id, "comentario": "Para el finde"})
    assert r.status_code == 201, r.text
    pedido = r.json()
    assert client.get("/pedidos", params={"estado": "PENDIENTE"}).json()["total"] == 1

    r = client.post(f"/pedidos/{pedido['id']}/reservar")
    assert r.json()["estado"] == "APROBADO"
    assert cliente_socio.get("/mi/reservas").json()["items"][0]["estado"] == "DISPONIBLE"
    assert cliente_socio.get("/notificaciones/no-leidas").json()["no_leidas"] == 2

    assert cliente_socio.get(f"/pedidos/{pedido['id']}").status_code == 403
    assert date.today().isoformat() in cliente_socio.get("/mi/pedidos").json()["items"][0]["fecha"]
