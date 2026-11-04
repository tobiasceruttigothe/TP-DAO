from datetime import date, timedelta

from app.config import settings
from app.domain.enums import EstadoFisico, TipoNotificacion
from app.models import Notificacion
from app.schemas.prestamo import PrestamoCrear
from app.services.eventos import Contenido, ObservadorEventos, PedidoNuevo, PublicadorEventos
from app.services.proceso_service import ProcesoVencimientos
from app.services.prestamo_service import PrestamoService
from app.services.remito_service import RemitoService
from app.services.socio_service import SocioService


def prestar(db, socio, ejemplar, origen, destino, hoy=None):
    return PrestamoService(db).solicitar(
        PrestamoCrear(socio_id=socio.id, ejemplar_id=ejemplar.id, sede_origen_id=origen.id, sede_destino_id=destino.id),
        hoy=hoy,
    )


def tipos(db, usuario):
    return [n.tipo for n in db.query(Notificacion).filter_by(usuario_id=usuario.id).order_by(Notificacion.id)]


class ObservadorDePrueba(ObservadorEventos):
    def __init__(self):
        self.recibidos = []

    def notificar(self, destinatarios, contenido: Contenido):
        self.recibidos.append((destinatarios, contenido))


def test_el_publicador_avisa_a_todos_los_observadores(db, datos):
    admin = datos.admin()
    uno, dos = ObservadorDePrueba(), ObservadorDePrueba()
    publicador = PublicadorEventos(db, [uno])
    publicador.suscribir(dos)

    sede, libro, socio = datos.sede(), datos.libro(), datos.socio()

    class PedidoFalso:
        pass

    pedido = PedidoFalso()
    pedido.socio, pedido.libro, pedido.sede = socio, libro, sede
    publicador.publicar(PedidoNuevo(pedido))

    for observador in (uno, dos):
        destinatarios, contenido = observador.recibidos[0]
        assert destinatarios == [admin]
        assert contenido.tipo == TipoNotificacion.PEDIDO_NUEVO


def test_llegada_a_la_sede_avisa_al_socio(db, datos):
    centro, norte = datos.sede(), datos.sede()
    socio = datos.socio()
    usuario = datos.usuario_de(socio)
    prestamo = prestar(db, socio, datos.ejemplar(datos.libro(), centro), centro, norte)
    remito = prestamo.remitos[0]
    servicio = RemitoService(db)
    servicio.empaquetar(remito.id)
    servicio.despachar(remito.id)
    servicio.recibir(remito.id, EstadoFisico.BUENO)
    assert TipoNotificacion.LISTO_PARA_RETIRAR in tipos(db, usuario)


def test_socio_sin_cuenta_no_genera_notificaciones(db, datos):
    socio = datos.socio()
    SocioService(db).inhabilitar(socio.id, "deuda")
    assert db.query(Notificacion).count() == 0


def test_inhabilitacion_avisa_al_socio(db, datos):
    socio = datos.socio()
    usuario = datos.usuario_de(socio)
    SocioService(db).inhabilitar(socio.id, "deuda")
    assert tipos(db, usuario) == [TipoNotificacion.SOCIO_INHABILITADO]


def test_socios_de_ejemplo_no_reciben_correos(db, datos, correos):
    socio = datos.socio()
    usuario = datos.usuario_de(socio)
    usuario.recibe_correos = False
    SocioService(db).inhabilitar(socio.id, "deuda")
    assert tipos(db, usuario) == [TipoNotificacion.SOCIO_INHABILITADO]
    assert correos == []


def test_avisos_por_vencer_y_vencido_una_sola_vez(db, datos, correos):
    sede = datos.sede()
    socio = datos.socio()
    usuario = datos.usuario_de(socio)
    hoy = date(2026, 10, 1)
    prestamo = prestar(db, socio, datos.ejemplar(datos.libro(), sede), sede, sede, hoy=hoy)
    proceso = ProcesoVencimientos(db)

    lejos = prestamo.fecha_vencimiento - timedelta(days=settings.dias_aviso_vencimiento + 1)
    assert proceso.ejecutar(lejos).avisos_enviados == 0

    cerca = prestamo.fecha_vencimiento - timedelta(days=settings.dias_aviso_vencimiento)
    assert proceso.ejecutar(cerca).avisos_enviados == 1
    assert proceso.ejecutar(cerca).avisos_enviados == 0

    vencido = prestamo.fecha_vencimiento + timedelta(days=1)
    assert proceso.ejecutar(vencido).avisos_enviados == 1
    assert proceso.ejecutar(vencido + timedelta(days=1)).avisos_enviados == 0

    assert tipos(db, usuario) == [TipoNotificacion.PRESTAMO_POR_VENCER, TipoNotificacion.PRESTAMO_VENCIDO]
    assert len(correos) == 2


def test_notificaciones_por_api(socio_conectado, db):
    cliente, socio = socio_conectado
    SocioService(db).inhabilitar(socio.id, "deuda")

    lista = cliente.get("/notificaciones").json()
    assert lista["total"] == 1
    assert cliente.get("/notificaciones/no-leidas").json() == {"no_leidas": 1}

    notificacion = lista["items"][0]
    assert cliente.post(f"/notificaciones/{notificacion['id']}/leida").json()["leida"] is True
    assert cliente.get("/notificaciones/no-leidas").json() == {"no_leidas": 0}
    assert cliente.post("/notificaciones/leer-todas").json() == {"no_leidas": 0}
