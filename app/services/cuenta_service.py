from sqlalchemy.orm import Session

from app.config import settings
from app.domain.enums import EstadoUsuario, Rol
from app.exceptions import DuplicadoError, NoAutorizadoError, NoEncontradoError, ReglaNegocioError, SinPermisoError
from app.models import Socio, Usuario
from app.repositories import SocioRepository, UsuarioRepository
from app.repositories.base import Paginacion, ResultadoPaginado
from app.schemas.usuario import AdminCrear, RegistroCrear
from app.seguridad import contrasenas, tokens
from app.services.correo import armar_correo
from app.services.eventos import CuentaAprobada, CuentaRechazada, RegistroPendiente, publicador
from app.services.notificaciones import encolar_correo

# Motivo con el que queda inhabilitado el socio que se registro solo, hasta que lo aprueban
MOTIVO_PENDIENTE = "Registro pendiente de aprobación"

MENSAJES_SIN_ACCESO = {
    EstadoUsuario.PENDIENTE_CONFIRMACION: "Todavía no confirmaste tu email. Revisá tu correo (y la carpeta de spam).",
    EstadoUsuario.PENDIENTE_APROBACION: "Tu cuenta está esperando la aprobación de la biblioteca. Te avisamos por correo.",
    EstadoUsuario.RECHAZADO: "Tu solicitud de registro fue rechazada.",
}


class CuentaService:
    """Alta de cuentas, confirmacion de email, aprobacion e ingreso."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = UsuarioRepository(db)
        self.socios = SocioRepository(db)
        self.eventos = publicador(db)

    # --- Registro de socios ---

    def registrar(self, datos: RegistroCrear) -> Usuario:
        """El socio completa sus datos. Si ya estaba cargado por la biblioteca (mismo DNI y
        email), la cuenta se vincula a ese socio y no necesita aprobacion; si no, se crea un
        socio nuevo que queda pendiente hasta que un administrador lo apruebe."""
        if self.repo.buscar_por_email(datos.email) is not None:
            raise DuplicadoError("Ya hay una cuenta con ese email")

        socio = self.socios.buscar_por_dni(datos.dni)
        if socio is not None:
            if socio.usuario is not None:
                raise DuplicadoError("Ese DNI ya tiene una cuenta. Si no recordás la contraseña, acercate a una sede.")
            if socio.email.lower() != datos.email.lower():
                raise ReglaNegocioError(
                    "Ese DNI ya está registrado con otro email. Acercate a una sede para actualizar tus datos."
                )
        else:
            if self.socios.buscar_por_email(datos.email) is not None:
                raise DuplicadoError("Ya hay un socio con ese email")
            socio = Socio(
                dni=datos.dni,
                nombre=datos.nombre,
                apellido=datos.apellido,
                email=datos.email,
                telefono=datos.telefono,
                habilitado=False,
                motivo_inhabilitacion=MOTIVO_PENDIENTE,
            )
            self.socios.agregar(socio)

        usuario = Usuario(
            email=datos.email,
            nombre=f"{datos.nombre} {datos.apellido}",
            hash_contrasena=contrasenas.generar_hash(datos.contrasena),
            rol=Rol.SOCIO,
            estado=EstadoUsuario.PENDIENTE_CONFIRMACION,
            socio=socio,
            token_confirmacion=tokens.crear_token_confirmacion(),
        )
        self.repo.agregar(usuario)
        self._enviar_confirmacion(usuario)
        self.db.commit()
        return usuario

    def reenviar_confirmacion(self, email: str):
        usuario = self.repo.buscar_por_email(email)
        # No se informa si el email existe o no, para no revelar quien tiene cuenta
        if usuario is not None and usuario.estado == EstadoUsuario.PENDIENTE_CONFIRMACION:
            usuario.token_confirmacion = tokens.crear_token_confirmacion()
            self._enviar_confirmacion(usuario)
            self.db.commit()

    def confirmar_email(self, token: str) -> Usuario:
        usuario = self.repo.buscar_por_token(token)
        if usuario is None:
            raise NoEncontradoError("El link de confirmación no es válido o ya se usó")
        socio = usuario.socio
        requiere_aprobacion = not socio.habilitado and socio.motivo_inhabilitacion == MOTIVO_PENDIENTE
        usuario.confirmar_email(requiere_aprobacion)
        self.db.flush()
        if requiere_aprobacion:
            self.eventos.publicar(RegistroPendiente(usuario))
        self.db.commit()
        return usuario

    def _enviar_confirmacion(self, usuario: Usuario):
        encolar_correo(
            self.db,
            armar_correo(
                usuario.email,
                "Confirmá tu email",
                f"Hola {usuario.nombre}, gracias por registrarte en la Red de Bibliotecas. "
                "Confirmá tu email para continuar:",
                f"/confirmar?token={usuario.token_confirmacion}",
            ),
        )

    # --- Administracion ---

    def listar(self, paginacion: Paginacion, estado=None, rol=None, texto=None) -> ResultadoPaginado[Usuario]:
        return self.repo.listar_filtrado(paginacion, estado, rol, texto)

    def obtener(self, usuario_id: int) -> Usuario:
        usuario = self.repo.obtener(usuario_id)
        if usuario is None:
            raise NoEncontradoError(f"No existe el usuario {usuario_id}")
        return usuario

    def aprobar(self, usuario_id: int) -> Usuario:
        usuario = self._pendiente_de_aprobacion(usuario_id)
        usuario.aprobar()
        usuario.socio.habilitar()
        self.eventos.publicar(CuentaAprobada(usuario))
        self.db.commit()
        return usuario

    def rechazar(self, usuario_id: int, motivo: str) -> Usuario:
        usuario = self._pendiente_de_aprobacion(usuario_id)
        usuario.rechazar(motivo)
        usuario.socio.inhabilitar(f"Registro rechazado: {motivo}")
        self.eventos.publicar(CuentaRechazada(usuario))
        self.db.commit()
        return usuario

    def _pendiente_de_aprobacion(self, usuario_id: int) -> Usuario:
        usuario = self.obtener(usuario_id)
        if usuario.estado != EstadoUsuario.PENDIENTE_APROBACION:
            raise ReglaNegocioError("La cuenta no está esperando aprobación")
        return usuario

    def crear_admin(self, datos: AdminCrear) -> Usuario:
        if self.repo.buscar_por_email(datos.email) is not None:
            raise DuplicadoError("Ya hay una cuenta con ese email")
        usuario = self._nuevo_admin(datos.email, datos.nombre, datos.contrasena)
        self.db.commit()
        return usuario

    def asegurar_admin(self):
        """Si no hay ningun administrador, crea el de la configuracion (ADMIN_EMAIL)."""
        if not self.repo.hay_administrador():
            self._nuevo_admin(settings.admin_email, settings.admin_nombre, settings.admin_contrasena)
            self.db.commit()

    def _nuevo_admin(self, email: str, nombre: str, contrasena: str) -> Usuario:
        return self.repo.agregar(
            Usuario(
                email=email,
                nombre=nombre,
                hash_contrasena=contrasenas.generar_hash(contrasena),
                rol=Rol.ADMIN,
                estado=EstadoUsuario.ACTIVO,
            )
        )

    # --- Ingreso ---

    def ingresar(self, email: str, contrasena: str) -> tuple[str, Usuario]:
        usuario = self.repo.buscar_por_email(email)
        if usuario is None or not contrasenas.verificar(contrasena, usuario.hash_contrasena):
            raise NoAutorizadoError("Email o contraseña incorrectos")
        if not usuario.puede_ingresar:
            raise SinPermisoError(MENSAJES_SIN_ACCESO[usuario.estado])
        return tokens.crear_token_sesion(usuario.id, usuario.rol.value), usuario

    def usuario_de_token(self, token: str) -> Usuario:
        datos = tokens.leer_token_sesion(token)
        if datos is None:
            raise NoAutorizadoError("La sesión venció o no es válida. Volvé a ingresar.")
        usuario = self.repo.obtener(int(datos["sub"]))
        if usuario is None or not usuario.puede_ingresar:
            raise NoAutorizadoError("La sesión ya no es válida. Volvé a ingresar.")
        return usuario
