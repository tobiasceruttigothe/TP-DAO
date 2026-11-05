import pytest

from app.domain.enums import EstadoEjemplar, EstadoInventario
from app.exceptions import ReglaNegocioError
from app.schemas.prestamo import PrestamoCrear
from app.services.catalogo_service import CatalogoService
from app.services.inventario_service import InventarioService
from app.services.prestamo_service import PrestamoService


@pytest.fixture
def sedes(datos):
    return datos.sede("Centro"), datos.sede("Norte")


def codigos(filas):
    return sorted(f.codigo for f in filas)


def test_informe_clasifica_cada_codigo(db, datos, sedes):
    centro, norte = sedes
    libro = datos.libro()
    en_estante = datos.ejemplar(libro, centro)
    faltante = datos.ejemplar(libro, centro)
    prestado = datos.ejemplar(libro, centro)
    de_otra_sede = datos.ejemplar(libro, norte)
    PrestamoService(db).solicitar(
        PrestamoCrear(socio_id=datos.socio().id, ejemplar_id=prestado.id, sede_origen_id=centro.id, sede_destino_id=centro.id)
    )

    servicio = InventarioService(db)
    inventario = servicio.iniciar(centro.id)
    assert servicio.registrar_codigo(inventario.id, en_estante.codigo_inventario.lower()).resultado == "ENCONTRADO"
    assert servicio.registrar_codigo(inventario.id, prestado.codigo_inventario).resultado == "FUERA_DE_LUGAR"
    resultado = servicio.registrar_codigo(inventario.id, de_otra_sede.codigo_inventario)
    assert resultado.resultado == "FUERA_DE_LUGAR" and "Norte" in resultado.detalle
    assert servicio.registrar_codigo(inventario.id, "XYZ-999").resultado == "DESCONOCIDO"

    detalle = servicio.detalle(inventario.id)
    assert detalle.esperados == 2
    assert codigos(detalle.informe.encontrados) == [en_estante.codigo_inventario]
    assert codigos(detalle.informe.faltantes) == [faltante.codigo_inventario]
    assert codigos(detalle.informe.fuera_de_lugar) == sorted([prestado.codigo_inventario, de_otra_sede.codigo_inventario])
    assert codigos(detalle.informe.desconocidos) == ["XYZ-999"]


def test_no_se_registra_dos_veces_el_mismo_codigo(db, datos, sedes):
    centro, _ = sedes
    ejemplar = datos.ejemplar(datos.libro(), centro)
    servicio = InventarioService(db)
    inventario = servicio.iniciar(centro.id)
    servicio.registrar_codigo(inventario.id, ejemplar.codigo_inventario)
    with pytest.raises(ReglaNegocioError, match="ya se registró"):
        servicio.registrar_codigo(inventario.id, ejemplar.codigo_inventario)


def test_un_solo_inventario_en_curso_por_sede(db, sedes):
    centro, norte = sedes
    servicio = InventarioService(db)
    servicio.iniciar(centro.id)
    with pytest.raises(ReglaNegocioError, match="en curso"):
        servicio.iniciar(centro.id)
    servicio.iniciar(norte.id)


def test_cerrar_guarda_el_informe(db, datos, sedes):
    centro, _ = sedes
    ejemplar = datos.ejemplar(datos.libro(), centro)
    servicio = InventarioService(db)
    inventario = servicio.iniciar(centro.id)
    servicio.cerrar(inventario.id)

    assert inventario.estado == EstadoInventario.CERRADO
    assert codigos(servicio.detalle(inventario.id).informe.faltantes) == [ejemplar.codigo_inventario]
    # Un cambio posterior del ejemplar no altera el informe ya cerrado
    CatalogoService(db).marcar_extraviado(ejemplar.id)
    assert codigos(servicio.detalle(inventario.id).informe.faltantes) == [ejemplar.codigo_inventario]
    with pytest.raises(ReglaNegocioError, match="cerrado"):
        servicio.registrar_codigo(inventario.id, ejemplar.codigo_inventario)


def test_marcar_extraviado_y_recuperar(db, datos, sedes):
    centro, _ = sedes
    ejemplar = datos.ejemplar(datos.libro(), centro)
    catalogo = CatalogoService(db)
    catalogo.marcar_extraviado(ejemplar.id)
    assert ejemplar.estado == EstadoEjemplar.EXTRAVIADO
    with pytest.raises(ReglaNegocioError):
        catalogo.marcar_extraviado(ejemplar.id)
    catalogo.recuperar(ejemplar.id)
    assert ejemplar.estado == EstadoEjemplar.DISPONIBLE


def test_inventario_por_api(client, datos):
    centro = datos.sede("Centro")
    ejemplar = datos.ejemplar(datos.libro(), centro)
    inventario = client.post("/inventarios", json={"sede_id": centro.id}).json()
    r = client.post(f"/inventarios/{inventario['id']}/codigos", json={"codigo": ejemplar.codigo_inventario})
    assert r.status_code == 201 and r.json()["resultado"] == "ENCONTRADO"
    item_id = r.json()["item_id"]
    assert client.delete(f"/inventarios/{inventario['id']}/codigos/{item_id}").status_code == 204
    cerrado = client.post(f"/inventarios/{inventario['id']}/cerrar").json()
    assert cerrado["estado"] == "CERRADO"
    assert len(cerrado["informe"]["faltantes"]) == 1
