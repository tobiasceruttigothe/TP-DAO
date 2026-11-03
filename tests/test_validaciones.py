import pytest
from pydantic import ValidationError

from app.schemas.libro import LibroCrear
from app.schemas.sede import SedeCrear
from app.schemas.socio import SocioCrear
from app.schemas.validaciones import isbn_es_valido

SOCIO = {"dni": "30111222", "nombre": "Ana", "apellido": "Paz", "email": "ana@mail.com"}
LIBRO = {"isbn": "9789500728997", "titulo": "Rayuela", "autor": "Julio Cortázar"}


def error_de(modelo, datos) -> str:
    with pytest.raises(ValidationError) as error:
        modelo(**datos)
    return error.value.errors()[0]["msg"]


# --- Socio ---

@pytest.mark.parametrize("dni", ["1234567", "12345678", "30.111.222", " 30111222 "])
def test_dni_valido(dni):
    assert SocioCrear(**{**SOCIO, "dni": dni}).dni.isdigit()


@pytest.mark.parametrize("dni", ["123456", "123456789", "3011122a", "", "abcdefgh"])
def test_dni_invalido(dni):
    assert "7 u 8 dígitos" in error_de(SocioCrear, {**SOCIO, "dni": dni})


@pytest.mark.parametrize("nombre", ["Li", "María de los Ángeles", "O'Brien", "Pérez-Gil", "Ñandú"])
def test_nombre_valido(nombre):
    assert SocioCrear(**{**SOCIO, "nombre": nombre}).nombre == nombre


def test_nombre_se_limpia_de_espacios():
    assert SocioCrear(**{**SOCIO, "nombre": "  Juan   Pablo "}).nombre == "Juan Pablo"


@pytest.mark.parametrize(
    "nombre, mensaje",
    [
        ("J", "al menos 2"),
        ("   ", "al menos 2"),
        ("x" * 51, "más de 50"),
        ("Juan2", "solo puede tener letras"),
        ("Juan!", "solo puede tener letras"),
        ("Juan  -", "solo puede tener letras"),
    ],
)
def test_nombre_invalido(nombre, mensaje):
    assert mensaje in error_de(SocioCrear, {**SOCIO, "apellido": nombre})


def test_telefono_opcional_y_solo_digitos():
    assert SocioCrear(**SOCIO).telefono is None
    assert SocioCrear(**{**SOCIO, "telefono": ""}).telefono is None
    assert SocioCrear(**{**SOCIO, "telefono": "3514000001"}).telefono == "3514000001"
    for telefono in ["351-4000001", "12345", "351400000a", "1" * 16]:
        assert "solo números" in error_de(SocioCrear, {**SOCIO, "telefono": telefono})


def test_sede_usa_el_mismo_formato_de_telefono():
    with pytest.raises(ValidationError):
        SedeCrear(nombre="Centro", direccion="Colón 100", telefono="351-400")


# --- Libro ---

@pytest.mark.parametrize("isbn", ["9789500728997", "978-950-07-2899-7", "0306406152", "080442957X", "080442957x"])
def test_isbn_valido(isbn):
    assert isbn_es_valido(LibroCrear(**{**LIBRO, "isbn": isbn}).isbn)


@pytest.mark.parametrize("isbn", ["9789500728990", "0306406153", "123", "97895007289971", "abcdefghij"])
def test_isbn_invalido(isbn):
    assert "ISBN" in error_de(LibroCrear, {**LIBRO, "isbn": isbn})


def test_isbn_se_guarda_sin_guiones():
    assert LibroCrear(**{**LIBRO, "isbn": "978-950-07-2899-7"}).isbn == "9789500728997"


@pytest.mark.parametrize("anio, mensaje", [(1399, "1400"), (3000, "posterior al año actual")])
def test_anio_invalido(anio, mensaje):
    assert mensaje in error_de(LibroCrear, {**LIBRO, "anio_publicacion": anio})
