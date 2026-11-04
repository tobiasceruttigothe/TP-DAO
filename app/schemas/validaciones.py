"""Tipos con validacion de formato reutilizables en los DTO.

Se aplican antes de llegar al servicio: si un dato no cumple, la API responde 422 con el
motivo y no se ejecuta nada. Las reglas de negocio (duplicados, estados, etc.) siguen en los
servicios.
"""
import re
from datetime import date
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator

# Palabras de letras (con tildes y ñ) separadas por un espacio, apostrofe o guion:
# "María de los Ángeles", "O'Brien", "Pérez-Gil"
_PALABRAS = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$")


def _limpiar_espacios(valor):
    """Quita espacios al principio y al final, y deja uno solo entre palabras."""
    if isinstance(valor, str):
        return " ".join(valor.split())
    return valor


def _vacio_a_nulo(valor):
    valor = _limpiar_espacios(valor)
    return valor or None


def _largo(minimo: int, maximo: int):
    """Controla el largo con un mensaje claro (el de Pydantic dice "items")."""

    def validar(valor):
        if valor is None:
            return valor
        if len(valor) < minimo:
            raise ValueError(f"debe tener al menos {minimo} caracteres")
        if len(valor) > maximo:
            raise ValueError(f"no puede tener más de {maximo} caracteres")
        return valor

    return AfterValidator(validar)


def _validar_nombre(valor: str) -> str:
    if not _PALABRAS.match(valor):
        raise ValueError("solo puede tener letras, espacios, apóstrofes o guiones")
    return valor


def _quitar_separadores(valor):
    """Para DNI e ISBN: acepta que se escriban con puntos, guiones o espacios."""
    if isinstance(valor, str):
        return re.sub(r"[.\-\s]", "", valor)
    return valor


def _validar_dni(valor: str) -> str:
    if not re.fullmatch(r"\d{7,8}", valor):
        raise ValueError("debe tener 7 u 8 dígitos, sin letras")
    return valor


def _validar_telefono(valor: str | None) -> str | None:
    if valor is not None and not re.fullmatch(r"\d{6,15}", valor):
        raise ValueError("debe tener solo números, entre 6 y 15 dígitos")
    return valor


def isbn_es_valido(isbn: str) -> bool:
    """ISBN-10 o ISBN-13 con el digito verificador correcto."""
    if re.fullmatch(r"\d{13}", isbn):
        suma = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(isbn[:12]))
        return (10 - suma % 10) % 10 == int(isbn[12])
    if re.fullmatch(r"\d{9}[\dX]", isbn):
        digitos = [10 if d == "X" else int(d) for d in isbn]
        return sum(d * (10 - i) for i, d in enumerate(digitos)) % 11 == 0
    return False


def _validar_isbn(valor: str) -> str:
    valor = valor.upper()
    if not isbn_es_valido(valor):
        raise ValueError("no es un ISBN-10 o ISBN-13 válido (revisar los dígitos)")
    return valor


def _validar_anio(valor: int | None) -> int | None:
    if valor is None:
        return valor
    if valor < 1400:
        raise ValueError("debe ser 1400 o posterior")
    if valor > date.today().year:
        raise ValueError("no puede ser posterior al año actual")
    return valor


NombrePersona = Annotated[str, BeforeValidator(_limpiar_espacios), _largo(2, 50), AfterValidator(_validar_nombre)]

Dni = Annotated[str, BeforeValidator(_quitar_separadores), AfterValidator(_validar_dni)]

Telefono = Annotated[str | None, BeforeValidator(_vacio_a_nulo), AfterValidator(_validar_telefono)]

Isbn = Annotated[str, BeforeValidator(_quitar_separadores), AfterValidator(_validar_isbn)]

AnioPublicacion = Annotated[int | None, AfterValidator(_validar_anio)]


def texto(minimo: int, maximo: int):
    """Texto obligatorio, sin espacios de mas."""
    return Annotated[str, BeforeValidator(_limpiar_espacios), _largo(minimo, maximo)]


def texto_opcional(maximo: int):
    """Texto opcional: si viene vacio se guarda como nulo."""
    return Annotated[str | None, BeforeValidator(_vacio_a_nulo), _largo(1, maximo)]


def _validar_contrasena(valor: str) -> str:
    if len(valor) < 8:
        raise ValueError("debe tener al menos 8 caracteres")
    if len(valor.encode("utf-8")) > 72:
        raise ValueError("no puede tener más de 72 caracteres")
    if not re.search(r"[A-Za-z]", valor) or not re.search(r"\d", valor):
        raise ValueError("debe tener letras y números")
    return valor


Contrasena = Annotated[str, AfterValidator(_validar_contrasena)]

