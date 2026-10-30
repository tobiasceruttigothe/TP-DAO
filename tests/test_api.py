def crear_sede(client, nombre):
    r = client.post("/sedes", json={"nombre": nombre, "direccion": "San Martin 100"})
    assert r.status_code == 201, r.text
    return r.json()


def crear_socio(client, dni="30111222", email="ana@mail.com"):
    r = client.post("/socios", json={"dni": dni, "nombre": "Ana", "apellido": "Lopez", "email": email})
    assert r.status_code == 201, r.text
    return r.json()


def crear_libro(client, isbn="9789500000001"):
    r = client.post("/libros", json={"isbn": isbn, "titulo": "Rayuela", "autor": "Cortazar"})
    assert r.status_code == 201, r.text
    return r.json()


def crear_ejemplar(client, libro_id, sede_id, codigo="INV-1"):
    r = client.post("/ejemplares", json={"codigo_inventario": codigo, "libro_id": libro_id, "sede_id": sede_id})
    assert r.status_code == 201, r.text
    return r.json()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_duplicados_devuelven_409(client):
    crear_sede(client, "Centro")
    assert client.post("/sedes", json={"nombre": "centro", "direccion": "Otra 1"}).status_code == 409

    crear_socio(client)
    assert client.post(
        "/socios", json={"dni": "30111222", "nombre": "X", "apellido": "Y", "email": "otro@mail.com"}
    ).status_code == 409

    libro = crear_libro(client)
    assert client.post("/libros", json={"isbn": "9789500000001", "titulo": "T", "autor": "A"}).status_code == 409

    sede = client.get("/sedes").json()[0]
    crear_ejemplar(client, libro["id"], sede["id"], codigo="INV-1")
    r = client.post("/ejemplares", json={"codigo_inventario": "INV-1", "libro_id": libro["id"], "sede_id": sede["id"]})
    assert r.status_code == 409


def test_inexistente_devuelve_404(client):
    assert client.get("/socios/999").status_code == 404
    assert client.get("/remitos/numero/R-999999").status_code == 404


def test_validacion_de_entrada_devuelve_422(client):
    r = client.post("/socios", json={"dni": "abc", "nombre": "A", "apellido": "B", "email": "no-es-mail"})
    assert r.status_code == 422


def test_flujo_interbibliotecario_por_api(client):
    centro = crear_sede(client, "Centro")
    norte = crear_sede(client, "Norte")
    socio = crear_socio(client)
    libro = crear_libro(client)
    ejemplar = crear_ejemplar(client, libro["id"], centro["id"])

    disp = client.get(f"/libros/{libro['id']}/disponibilidad").json()
    assert disp["total_disponibles"] == 1

    r = client.post(
        "/prestamos",
        json={
            "socio_id": socio["id"],
            "ejemplar_id": ejemplar["id"],
            "sede_origen_id": centro["id"],
            "sede_destino_id": norte["id"],
        },
    )
    assert r.status_code == 201, r.text
    prestamo = r.json()
    assert prestamo["tipo"] == "INTERBIBLIOTECARIO"

    remito = client.get(f"/prestamos/{prestamo['id']}/remitos").json()[0]
    assert client.post(f"/remitos/{remito['id']}/despachar").status_code == 400  # sin empaquetar

    for accion in ("empaquetar", "despachar"):
        assert client.post(f"/remitos/{remito['id']}/{accion}").status_code == 200
    r = client.post(f"/remitos/{remito['id']}/recibir", json={"estado_fisico": "BUENO"})
    assert r.status_code == 200
    detalle = client.get(f"/remitos/numero/{remito['numero']}").json()
    assert [m["estado_nuevo"] for m in detalle["movimientos"]] == ["PENDIENTE", "EMPAQUETADO", "DESPACHADO", "RECIBIDO"]

    assert client.get(f"/prestamos/{prestamo['id']}").json()["estado"] == "ACTIVO"
    r = client.post(f"/prestamos/{prestamo['id']}/devolucion", json={"estado_fisico": "BUENO"})
    assert r.status_code == 200
    assert r.json()["estado"] == "DEVUELTO"


def test_regla_de_negocio_devuelve_400(client):
    centro = crear_sede(client, "Centro")
    socio = crear_socio(client)
    libro = crear_libro(client)
    ejemplar = crear_ejemplar(client, libro["id"], centro["id"])
    client.patch(f"/socios/{socio['id']}/inhabilitar", json={"motivo": "deuda"})

    r = client.post(
        "/prestamos",
        json={
            "socio_id": socio["id"],
            "ejemplar_id": ejemplar["id"],
            "sede_origen_id": centro["id"],
            "sede_destino_id": centro["id"],
        },
    )
    assert r.status_code == 400
    assert "inhabilitado" in r.json()["detail"]


def test_reportes_responden(client):
    for ruta in (
        "/reportes/prestamos-activos",
        "/reportes/vencidos-multas",
        "/reportes/libros-mas-solicitados",
        "/reportes/disponibilidad-sedes",
        "/reportes/envios",
        "/reportes/movimientos-sedes",
    ):
        assert client.get(ruta).status_code == 200, ruta
