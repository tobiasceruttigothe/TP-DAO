from enum import Enum


class EstadoEjemplar(str, Enum):
    DISPONIBLE = "DISPONIBLE"
    RESERVADO = "RESERVADO"
    PRESTADO = "PRESTADO"
    EN_TRANSITO = "EN_TRANSITO"
    EN_REPARACION = "EN_REPARACION"
    EXTRAVIADO = "EXTRAVIADO"
    BAJA = "BAJA"


class EstadoFisico(str, Enum):
    BUENO = "BUENO"
    REGULAR = "REGULAR"
    DANADO = "DANADO"
    DESTRUIDO = "DESTRUIDO"


class TipoIncidencia(str, Enum):
    DANIO = "DANIO"
    DESTRUCCION = "DESTRUCCION"
    EXTRAVIO = "EXTRAVIO"


class TipoPrestamo(str, Enum):
    LOCAL = "LOCAL"
    INTERBIBLIOTECARIO = "INTERBIBLIOTECARIO"


class EstadoPrestamo(str, Enum):
    SOLICITADO = "SOLICITADO"  # interbibliotecario esperando envio
    EN_TRANSITO = "EN_TRANSITO"
    ACTIVO = "ACTIVO"
    DEVUELTO = "DEVUELTO"
    CANCELADO = "CANCELADO"


class TipoRemito(str, Enum):
    IDA = "IDA"  # sede origen -> sede destino del prestamo
    RETORNO = "RETORNO"  # vuelta del ejemplar a su sede


class EstadoReserva(str, Enum):
    PENDIENTE = "PENDIENTE"  # sin ejemplar asignado todavia
    DISPONIBLE = "DISPONIBLE"  # ejemplar apartado, esperando retiro
    CUMPLIDA = "CUMPLIDA"
    CANCELADA = "CANCELADA"
    VENCIDA = "VENCIDA"


class Rol(str, Enum):
    ADMIN = "ADMIN"
    SOCIO = "SOCIO"


class EstadoUsuario(str, Enum):
    PENDIENTE_CONFIRMACION = "PENDIENTE_CONFIRMACION"  # todavia no confirmo el email
    PENDIENTE_APROBACION = "PENDIENTE_APROBACION"  # confirmo el email, espera al admin
    ACTIVO = "ACTIVO"
    RECHAZADO = "RECHAZADO"


class EstadoPedido(str, Enum):
    PENDIENTE = "PENDIENTE"
    APROBADO = "APROBADO"
    RECHAZADO = "RECHAZADO"
    CANCELADO = "CANCELADO"  # lo cancelo el socio antes de que se resolviera


class TipoNotificacion(str, Enum):
    REGISTRO_PENDIENTE = "REGISTRO_PENDIENTE"
    CUENTA_APROBADA = "CUENTA_APROBADA"
    CUENTA_RECHAZADA = "CUENTA_RECHAZADA"
    PEDIDO_NUEVO = "PEDIDO_NUEVO"
    PEDIDO_APROBADO = "PEDIDO_APROBADO"
    PEDIDO_RECHAZADO = "PEDIDO_RECHAZADO"
    RESERVA_DISPONIBLE = "RESERVA_DISPONIBLE"
    LISTO_PARA_RETIRAR = "LISTO_PARA_RETIRAR"
    PRESTAMO_POR_VENCER = "PRESTAMO_POR_VENCER"
    PRESTAMO_VENCIDO = "PRESTAMO_VENCIDO"
    SOCIO_INHABILITADO = "SOCIO_INHABILITADO"


class EstadoInventario(str, Enum):
    EN_CURSO = "EN_CURSO"
    CERRADO = "CERRADO"
