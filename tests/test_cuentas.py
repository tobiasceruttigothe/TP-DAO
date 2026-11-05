import pytest
from sqlalchemy import text

from app.domain.enums import EstadoUsuario, TipoNotificacion
from app.exceptions import DuplicadoError, NoAutorizadoError, NoEncontradoError, ReglaNegocioError, SinPermisoError
from app.models import Notificacion
from app.repositories.base import Paginacion
from app.schemas.usuario import RegistroCrear
from app.services.cuenta_service import MOTIVO_PENDIENTE, CuentaService

DATOS = {
    "dni": "41222333",
    "nombre": "Paula",
    "apellido": "Quiroga",
    "email": "paula@example.com",
    "contrasena": "clave1234",
}


def registrar(db, **cambios):
    return CuentaService(db).registrar(RegistroCrear(**{**DATOS, **cambios}))


def token_del_correo(correo):
    return correo.texto.split("token=")[1].strip()


def test_registro_crea_socio_pendiente_y_manda_confirmacion(db, correos):
    usuario = registrar(db)

    assert usuario.estado == EstadoUsuario.PENDIENTE_CONFIRMACION
    assert not usuario.socio.habilitado
    assert usuario.socio.motivo_inhabilitacion == MOTIVO_PENDIENTE
    assert usuario.hash_contrasena != DATOS["contrasena"]
    assert [c.destinatario for c in correos] == ["paula@example.com"]
    assert "/confirmar?token=" in correos[0].texto


def test_circuito_completo_registro_confirmacion_aprobacion_ingreso(db, datos, correos):
    admin = datos.admin("jefa@example.com")
    servicio = CuentaService(db)
    usuario = registrar(db)

    with pytest.raises(SinPermisoError, match="confirmaste"):
        servicio.ingresar(DATOS["email"], DATOS["contrasena"])

    servicio.confirmar_email(token_del_correo(correos[0]))
    assert usuario.estado == EstadoUsuario.PENDIENTE_APROBACION
    aviso_admin = db.query(Notificacion).filter_by(usuario_id=admin.id).one()
    assert aviso_admin.tipo == TipoNotificacion.REGISTRO_PENDIENTE
    assert "jefa@example.com" in [c.destinatario for c in correos]

    with pytest.raises(SinPermisoError, match="aprobación"):
        servicio.ingresar(DATOS["email"], DATOS["contrasena"])

    servicio.aprobar(usuario.id)
    assert usuario.socio.habilitado
    assert correos[-1].destinatario == DATOS["email"]
    assert "aprobada" in correos[-1].asunto

    token, conectado = servicio.ingresar("PAULA@example.com", DATOS["contrasena"])
    assert conectado.id == usuario.id
    assert servicio.usuario_de_token(token).id == usuario.id


def test_rechazo_inhabilita_al_socio_y_avisa(db, correos):
    servicio = CuentaService(db)
    usuario = registrar(db)
    servicio.confirmar_email(token_del_correo(correos[0]))
    servicio.rechazar(usuario.id, "Datos incompletos")

    assert usuario.estado == EstadoUsuario.RECHAZADO
    assert "Registro rechazado" in usuario.socio.motivo_inhabilitacion
    assert "rechazada" in correos[-1].asunto
    with pytest.raises(SinPermisoError, match="rechazada"):
        servicio.ingresar(DATOS["email"], DATOS["contrasena"])


def test_socio_ya_cargado_activa_su_cuenta_sin_aprobacion(db, datos, correos):
    socio = datos.socio(dni="41222333", email="paula@example.com")
    usuario = registrar(db)
    assert usuario.socio_id == socio.id

    CuentaService(db).confirmar_email(token_del_correo(correos[0]))
    assert usuario.estado == EstadoUsuario.ACTIVO


def test_socio_ya_cargado_con_otro_email_no_puede_registrarse(db, datos):
    datos.socio(dni="41222333", email="otro@example.com")
    with pytest.raises(ReglaNegocioError, match="otro email"):
        registrar(db)


def test_no_se_duplican_cuentas(db):
    registrar(db)
    with pytest.raises(DuplicadoError):
        registrar(db, dni="41222334")
    with pytest.raises(DuplicadoError):
        registrar(db, email="otra@example.com")


def test_token_de_confirmacion_se_usa_una_vez(db, correos):
    registrar(db)
    token = token_del_correo(correos[0])
    CuentaService(db).confirmar_email(token)
    with pytest.raises(NoEncontradoError):
        CuentaService(db).confirmar_email(token)


def test_credenciales_invalidas(db, datos):
    datos.admin("jefa@example.com")
    servicio = CuentaService(db)
    with pytest.raises(NoAutorizadoError):
        servicio.ingresar("jefa@example.com", "incorrecta")
    with pytest.raises(NoAutorizadoError):
        servicio.ingresar("nadie@example.com", "admin1234")
    with pytest.raises(NoAutorizadoError):
        servicio.usuario_de_token("no-es-un-token")


def test_asegurar_admin_crea_uno_solo(db):
    servicio = CuentaService(db)
    servicio.asegurar_admin()
    servicio.asegurar_admin()
    assert servicio.repo.hay_administrador()
    assert servicio.listar(Paginacion()).total == 1


def test_correo_no_sale_si_la_operacion_se_deshace(db, correos):
    from app.services.correo import armar_correo
    from app.services.notificaciones import encolar_correo

    # Como en una operacion real: algo se consulto o modifico antes de encolar el correo
    registrar(db)
    correos.clear()
    db.execute(text("SELECT 1"))
    encolar_correo(db, armar_correo("x@example.com", "Prueba", "Mensaje"))
    db.rollback()
    db.commit()
    assert correos == []
