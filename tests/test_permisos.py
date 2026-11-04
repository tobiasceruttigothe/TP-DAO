import pytest

ENDPOINTS_DEL_PANEL = [
    ("get", "/socios"),
    ("get", "/prestamos"),
    ("get", "/remitos"),
    ("get", "/reservas"),
    ("get", "/incidencias"),
    ("get", "/reportes/envios"),
    ("get", "/pedidos"),
    ("get", "/usuarios"),
    ("get", "/inventarios"),
    ("get", "/ejemplares"),
    ("post", "/procesos/vencimientos"),
    ("post", "/sedes"),
    ("post", "/libros"),
]

PUBLICOS = ["/health", "/libros", "/sedes"]


def llamar(cliente, metodo, ruta):
    return cliente.post(ruta, json={}) if metodo == "post" else cliente.get(ruta)


@pytest.mark.parametrize("metodo, ruta", ENDPOINTS_DEL_PANEL)
def test_sin_sesion_pide_ingresar(anonimo, metodo, ruta):
    r = llamar(anonimo, metodo, ruta)
    assert r.status_code == 401
    assert "iniciar sesión" in r.json()["detail"]


@pytest.mark.parametrize("metodo, ruta", ENDPOINTS_DEL_PANEL)
def test_socio_no_entra_al_panel(socio_conectado, metodo, ruta):
    cliente, _ = socio_conectado
    assert llamar(cliente, metodo, ruta).status_code == 403


@pytest.mark.parametrize("ruta", PUBLICOS)
def test_consulta_publica_sin_sesion(anonimo, ruta):
    assert anonimo.get(ruta).status_code == 200


def test_disponibilidad_es_publica(anonimo, client):
    libro = client.post("/libros", json={"isbn": "9789500728997", "titulo": "Rayuela", "autor": "Julio Cortázar"}).json()
    assert anonimo.get(f"/libros/{libro['id']}/disponibilidad").status_code == 200


def test_area_del_socio_requiere_ser_socio(client, anonimo):
    assert anonimo.get("/mi/prestamos").status_code == 401
    # El administrador no tiene socio asociado
    assert client.get("/mi/prestamos").status_code == 403


def test_token_invalido(anonimo):
    anonimo.headers["Authorization"] = "Bearer cualquier-cosa"
    r = anonimo.get("/auth/yo")
    assert r.status_code == 401


def test_ingreso_por_api(anonimo, datos):
    datos.admin("jefa@example.com")
    r = anonimo.post("/auth/ingresar", json={"email": "jefa@example.com", "contrasena": "admin1234"})
    assert r.status_code == 200
    sesion = r.json()
    assert sesion["usuario"]["rol"] == "ADMIN"
    anonimo.headers["Authorization"] = f"Bearer {sesion['token']}"
    assert anonimo.get("/auth/yo").json()["email"] == "jefa@example.com"
    assert anonimo.get("/socios").status_code == 200

    r = anonimo.post("/auth/ingresar", json={"email": "jefa@example.com", "contrasena": "mal"})
    assert r.status_code == 401


def test_registro_por_api_valida_la_contrasena(anonimo):
    datos = {"dni": "41222333", "nombre": "Paula", "apellido": "Quiroga", "email": "p@example.com", "contrasena": "corta"}
    r = anonimo.post("/auth/registro", json=datos)
    assert r.status_code == 422
    r = anonimo.post("/auth/registro", json={**datos, "contrasena": "clave1234"})
    assert r.status_code == 201
