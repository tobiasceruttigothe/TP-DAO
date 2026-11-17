import pytest
from pydantic import ValidationError

from app.domain.enums import EstadoEjemplar, EstadoFisico
from app.exceptions import DuplicadoError, ReglaNegocioError
from app.models import Ejemplar
from app.repositories import EjemplarRepository
from app.schemas.libro import EjemplarCrear
from app.schemas.sede import SedeActualizar, SedeCrear
from app.services.catalogo_service import CatalogoService
from app.services.sede_service import SedeService


def nueva_sede(db, nombre, prefijo):
    return SedeService(db).crear(SedeCrear(nombre=nombre, prefijo=prefijo, direccion="Colón 100"))


def cargar(db, libro, sede, cantidad=1, estado_fisico=EstadoFisico.BUENO):
    datos = EjemplarCrear(libro_id=libro.id, sede_id=sede.id, cantidad=cantidad, estado_fisico=estado_fisico)
    return CatalogoService(db).crear_ejemplares(datos)


def codigos(ejemplares):
    return [e.codigo_inventario for e in ejemplares]


# --- Codigos asignados por el sistema ---

def test_codigos_correlativos_con_el_prefijo_de_cada_sede(db, datos):
    libro = datos.libro()
    centro, norte = nueva_sede(db, "Centro", "CEN"), nueva_sede(db, "Norte", "NOR")

    assert codigos(cargar(db, libro, centro)) == ["CEN-0001"]
    assert codigos(cargar(db, libro, norte)) == ["NOR-0001"]
    assert codigos(cargar(db, datos.libro(), centro)) == ["CEN-0002"]


def test_carga_varios_iguales_de_una_vez(db, datos):
    libro, sede = datos.libro(), nueva_sede(db, "Centro", "CEN")

    nuevos = cargar(db, libro, sede, cantidad=5, estado_fisico=EstadoFisico.REGULAR)

    assert codigos(nuevos) == ["CEN-0001", "CEN-0002", "CEN-0003", "CEN-0004", "CEN-0005"]
    assert all(e.sede_id == sede.id and e.libro_id == libro.id for e in nuevos)
    assert all(e.estado == EstadoEjemplar.DISPONIBLE for e in nuevos)
    assert all(e.estado_fisico == EstadoFisico.REGULAR for e in nuevos)


def test_sigue_desde_el_numero_mas_alto_aunque_haya_huecos(db, datos):
    sede = nueva_sede(db, "Centro", "CEN")
    # Un codigo cargado antes de que el sistema los asignara, con un numero salteado
    EjemplarRepository(db).agregar(
        Ejemplar(codigo_inventario="CEN-0040", libro_id=datos.libro().id, sede_id=sede.id, estado=EstadoEjemplar.DISPONIBLE)
    )

    assert codigos(cargar(db, datos.libro(), sede, cantidad=2)) == ["CEN-0041", "CEN-0042"]
    assert CatalogoService(db).proximo_codigo(sede.id) == "CEN-0043"


def test_un_ejemplar_dado_de_baja_no_libera_su_numero(db, datos):
    sede = nueva_sede(db, "Centro", "CEN")
    [ejemplar] = cargar(db, datos.libro(), sede)
    CatalogoService(db).dar_de_baja_ejemplar(ejemplar.id)

    assert codigos(cargar(db, datos.libro(), sede)) == ["CEN-0002"]


def test_se_guardan_todos_o_ninguno(db, datos, monkeypatch):
    libro, sede = datos.libro(), nueva_sede(db, "Centro", "CEN")
    cargar(db, libro, sede, cantidad=3)
    # Como si otra carga simultanea hubiera tomado los mismos numeros
    monkeypatch.setattr(EjemplarRepository, "ultimo_numero", lambda self, prefijo: 1)

    with pytest.raises(DuplicadoError):
        cargar(db, libro, sede, cantidad=4)

    monkeypatch.undo()
    assert CatalogoService(db).proximo_codigo(sede.id) == "CEN-0004"


def test_no_carga_en_una_sede_dada_de_baja(db, datos):
    sede = nueva_sede(db, "Centro", "CEN")
    SedeService(db).dar_de_baja(sede.id)

    with pytest.raises(ReglaNegocioError):
        cargar(db, datos.libro(), sede)


@pytest.mark.parametrize("cantidad", [0, -1, 51])
def test_cantidad_entre_1_y_50(cantidad):
    with pytest.raises(ValidationError):
        EjemplarCrear(libro_id=1, sede_id=1, cantidad=cantidad)


def test_por_defecto_carga_uno():
    assert EjemplarCrear(libro_id=1, sede_id=1).cantidad == 1


# --- Prefijo de la sede ---

def test_prefijo_se_guarda_en_mayusculas(db):
    assert nueva_sede(db, "Centro", " cen ").prefijo == "CEN"


@pytest.mark.parametrize("prefijo", ["C", "CENTRO", "CE1", "CÉN", "C-N", ""])
def test_prefijo_de_2_a_5_letras(prefijo):
    with pytest.raises(ValidationError):
        SedeCrear(nombre="Centro", prefijo=prefijo, direccion="Colón 100")


def test_prefijo_repetido(db):
    nueva_sede(db, "Centro", "CEN")
    with pytest.raises(DuplicadoError):
        nueva_sede(db, "Centenario", "cen")


def test_el_prefijo_no_se_cambia_al_editar(db):
    sede = nueva_sede(db, "Centro", "CEN")
    datos = {"nombre": "Centro renovado", "direccion": "Colón 200", "prefijo": "OTR"}

    actualizada = SedeService(db).actualizar(sede.id, SedeActualizar(**datos))

    assert actualizada.nombre == "Centro renovado"
    assert actualizada.prefijo == "CEN"


# --- Por API ---

def test_carga_multiple_por_api(client, datos):
    libro = datos.libro()
    r = client.post("/sedes", json={"nombre": "Centro", "prefijo": "cen", "direccion": "Colón 100"})
    sede = r.json()
    assert sede["prefijo"] == "CEN"

    assert client.get("/ejemplares/proximo-codigo", params={"sede_id": sede["id"]}).json() == {"codigo": "CEN-0001"}
    r = client.post("/ejemplares", json={"libro_id": libro.id, "sede_id": sede["id"], "cantidad": 3})
    assert r.status_code == 201, r.text
    assert [e["codigo_inventario"] for e in r.json()] == ["CEN-0001", "CEN-0002", "CEN-0003"]

    r = client.put(f"/sedes/{sede['id']}", json={"nombre": "Centro", "prefijo": "OTR", "direccion": "Colón 100"})
    assert r.json()["prefijo"] == "CEN"
