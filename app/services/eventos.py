"""Patron Observer: los servicios publican eventos y los observadores reaccionan.

Cada evento sabe a quien le interesa (destinatarios) y que decir (contenido). Los servicios
solo publican: no saben si el aviso termina en la campanita del sistema, en un correo o en
ambos. Para sumar otro canal se agrega un observador, sin tocar los servicios.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.enums import EstadoUsuario, Rol, TipoNotificacion
from app.utiles_texto import pesos


@dataclass
class Contenido:
    tipo: TipoNotificacion
    titulo: str
    mensaje: str
    enlace: str | None = None


def administradores(db: Session):
    from app.models import Usuario

    return list(db.scalars(select(Usuario).where(Usuario.rol == Rol.ADMIN, Usuario.estado == EstadoUsuario.ACTIVO)))


def usuario_del_socio(socio):
    usuario = socio.usuario
    return [usuario] if usuario is not None and usuario.puede_ingresar else []


class Evento(ABC):
    @abstractmethod
    def destinatarios(self, db: Session) -> list:
        pass

    @abstractmethod
    def contenido(self) -> Contenido:
        pass


# --- Cuentas ---

@dataclass
class RegistroPendiente(Evento):
    usuario: object

    def destinatarios(self, db):
        return administradores(db)

    def contenido(self):
        socio = self.usuario.socio
        return Contenido(
            TipoNotificacion.REGISTRO_PENDIENTE,
            "Nuevo socio para aprobar",
            f"{socio.nombre} {socio.apellido} (DNI {socio.dni}) confirmó su email y espera la aprobación de su cuenta.",
            "/panel/usuarios",
        )


@dataclass
class CuentaAprobada(Evento):
    usuario: object

    def destinatarios(self, db):
        return [self.usuario]

    def contenido(self):
        return Contenido(
            TipoNotificacion.CUENTA_APROBADA,
            "Tu cuenta fue aprobada",
            "Ya podés ingresar con tu email y contraseña, hacer pedidos y consultar tus préstamos.",
            "/ingresar",
        )


@dataclass
class CuentaRechazada(Evento):
    usuario: object

    def destinatarios(self, db):
        return [self.usuario]

    def contenido(self):
        return Contenido(
            TipoNotificacion.CUENTA_RECHAZADA,
            "Tu solicitud de registro fue rechazada",
            f"Motivo: {self.usuario.motivo_rechazo}. Acercate a cualquier sede si querés más información.",
        )


# --- Pedidos ---

@dataclass
class PedidoNuevo(Evento):
    pedido: object

    def destinatarios(self, db):
        return administradores(db)

    def contenido(self):
        p = self.pedido
        return Contenido(
            TipoNotificacion.PEDIDO_NUEVO,
            "Nuevo pedido de un socio",
            f"{p.socio.nombre} {p.socio.apellido} pidió «{p.libro.titulo}» para retirar en {p.sede.nombre}.",
            "/panel/pedidos",
        )


@dataclass
class PedidoAprobado(Evento):
    pedido: object

    def destinatarios(self, db):
        return usuario_del_socio(self.pedido.socio)

    def contenido(self):
        p = self.pedido
        return Contenido(
            TipoNotificacion.PEDIDO_APROBADO,
            f"Tu pedido de «{p.libro.titulo}» fue aprobado",
            p.resolucion,
            "/socio/pedidos",
        )


@dataclass
class PedidoRechazado(Evento):
    pedido: object

    def destinatarios(self, db):
        return usuario_del_socio(self.pedido.socio)

    def contenido(self):
        p = self.pedido
        return Contenido(
            TipoNotificacion.PEDIDO_RECHAZADO,
            f"Tu pedido de «{p.libro.titulo}» fue rechazado",
            f"Motivo: {p.resolucion}",
            "/socio/pedidos",
        )


# --- Prestamos y reservas ---

@dataclass
class ReservaDisponible(Evento):
    reserva: object

    def destinatarios(self, db):
        return usuario_del_socio(self.reserva.socio)

    def contenido(self):
        r = self.reserva
        return Contenido(
            TipoNotificacion.RESERVA_DISPONIBLE,
            f"«{r.libro.titulo}» está listo para retirar",
            f"Te apartamos un ejemplar en {r.sede.nombre}. Podés retirarlo hasta el {r.fecha_expiracion:%d/%m/%Y}.",
            "/socio",
        )


@dataclass
class ListoParaRetirar(Evento):
    """El ejemplar de un prestamo entre sedes llego a la sede donde lo retira el socio."""

    prestamo: object

    def destinatarios(self, db):
        return usuario_del_socio(self.prestamo.socio)

    def contenido(self):
        p = self.prestamo
        return Contenido(
            TipoNotificacion.LISTO_PARA_RETIRAR,
            f"«{p.ejemplar.libro.titulo}» llegó a {p.sede_destino.nombre}",
            f"Ya podés retirarlo. Tenés que devolverlo antes del {p.fecha_vencimiento:%d/%m/%Y}.",
            "/socio",
        )


@dataclass
class PrestamoPorVencer(Evento):
    prestamo: object

    def destinatarios(self, db):
        return usuario_del_socio(self.prestamo.socio)

    def contenido(self):
        p = self.prestamo
        return Contenido(
            TipoNotificacion.PRESTAMO_POR_VENCER,
            f"«{p.ejemplar.libro.titulo}» vence pronto",
            f"Tenés que devolverlo antes del {p.fecha_vencimiento:%d/%m/%Y} en {p.sede_destino.nombre} para evitar multas.",
            "/socio",
        )


@dataclass
class PrestamoVencido(Evento):
    prestamo: object

    def destinatarios(self, db):
        return usuario_del_socio(self.prestamo.socio)

    def contenido(self):
        p = self.prestamo
        return Contenido(
            TipoNotificacion.PRESTAMO_VENCIDO,
            f"«{p.ejemplar.libro.titulo}» está vencido",
            f"Venció el {p.fecha_vencimiento:%d/%m/%Y}. La multa crece cada día de atraso "
            f"(hoy: {pesos(p.multa_actual)}). Devolvelo en {p.sede_destino.nombre} lo antes posible.",
            "/socio",
        )


@dataclass
class SocioInhabilitado(Evento):
    socio: object

    def destinatarios(self, db):
        usuario = self.socio.usuario
        return [usuario] if usuario is not None and usuario.puede_ingresar else []

    def contenido(self):
        return Contenido(
            TipoNotificacion.SOCIO_INHABILITADO,
            "Tu cuenta fue inhabilitada para nuevos préstamos",
            f"Motivo: {self.socio.motivo_inhabilitacion}. Acercate a cualquier sede para regularizar tu situación.",
            "/socio",
        )


# --- Sujeto del patron ---

class ObservadorEventos(ABC):
    @abstractmethod
    def notificar(self, destinatarios: list, contenido: Contenido):
        pass


class PublicadorEventos:
    def __init__(self, db: Session, observadores: list[ObservadorEventos] | None = None):
        self.db = db
        self.observadores = list(observadores or [])

    def suscribir(self, observador: ObservadorEventos):
        self.observadores.append(observador)

    def publicar(self, evento: Evento):
        destinatarios = evento.destinatarios(self.db)
        if not destinatarios:
            return
        contenido = evento.contenido()
        for observador in self.observadores:
            observador.notificar(destinatarios, contenido)


def publicador(db: Session) -> PublicadorEventos:
    """Publicador con los dos canales: la campanita del sistema y el correo."""
    from app.services.notificaciones import NotificacionesEnSistema, NotificacionesPorCorreo

    return PublicadorEventos(db, [NotificacionesEnSistema(db), NotificacionesPorCorreo(db)])
