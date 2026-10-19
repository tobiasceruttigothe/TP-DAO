"""Patron State para el ciclo de vida del remito.

    PENDIENTE -> EMPAQUETADO -> DESPACHADO -> RECIBIDO
        |             |              |
        +-> CANCELADO <+              +-> EXTRAVIADO

Cada estado sabe que operaciones admite. Las que no admite heredan el
comportamiento por defecto de EstadoRemito, que rechaza la transicion.
"""
from abc import ABC
from datetime import datetime

from app.exceptions import TransicionInvalidaError


class EstadoRemito(ABC):
    nombre: str = ""
    es_final: bool = False

    def entrar(self, remito):
        pass

    def empaquetar(self, remito, observacion=None):
        self._rechazar("empaquetar")

    def despachar(self, remito, observacion=None):
        self._rechazar("despachar")

    def recibir(self, remito, observacion=None):
        self._rechazar("recibir")

    def marcar_extraviado(self, remito, observacion=None):
        self._rechazar("marcar como extraviado")

    def cancelar(self, remito, observacion=None):
        self._rechazar("cancelar")

    def _rechazar(self, accion: str):
        raise TransicionInvalidaError(f"No se puede {accion} un remito en estado {self.nombre}")

    def __str__(self):
        return self.nombre


class Pendiente(EstadoRemito):
    nombre = "PENDIENTE"

    def empaquetar(self, remito, observacion=None):
        remito.cambiar_estado(Empaquetado(), observacion)

    def cancelar(self, remito, observacion=None):
        remito.cambiar_estado(Cancelado(), observacion)


class Empaquetado(EstadoRemito):
    nombre = "EMPAQUETADO"

    def despachar(self, remito, observacion=None):
        remito.cambiar_estado(Despachado(), observacion)

    def cancelar(self, remito, observacion=None):
        remito.cambiar_estado(Cancelado(), observacion)


class Despachado(EstadoRemito):
    nombre = "DESPACHADO"

    def entrar(self, remito):
        remito.fecha_despacho = datetime.now()

    def recibir(self, remito, observacion=None):
        remito.cambiar_estado(Recibido(), observacion)

    def marcar_extraviado(self, remito, observacion=None):
        remito.cambiar_estado(Extraviado(), observacion)


class Recibido(EstadoRemito):
    nombre = "RECIBIDO"
    es_final = True

    def entrar(self, remito):
        remito.fecha_recepcion = datetime.now()


class Extraviado(EstadoRemito):
    nombre = "EXTRAVIADO"
    es_final = True


class Cancelado(EstadoRemito):
    nombre = "CANCELADO"
    es_final = True


_ESTADOS = {cls.nombre: cls for cls in (Pendiente, Empaquetado, Despachado, Recibido, Extraviado, Cancelado)}


def estado_desde_nombre(nombre: str) -> EstadoRemito:
    try:
        return _ESTADOS[nombre]()
    except KeyError:
        raise ValueError(f"Estado de remito desconocido: {nombre}")


def nombres_estados() -> list[str]:
    return list(_ESTADOS.keys())
