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
