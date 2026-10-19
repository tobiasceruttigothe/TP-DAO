"""Carga datos de ejemplo para probar la API: python -m app.seed"""
from app.database import SessionLocal
from app.exceptions import DuplicadoError
from app.schemas.libro import EjemplarCrear, LibroCrear
from app.schemas.sede import SedeCrear
from app.schemas.socio import SocioCrear
from app.services.catalogo_service import CatalogoService
from app.services.sede_service import SedeService
from app.services.socio_service import SocioService

SEDES = [
    SedeCrear(nombre="Biblioteca Central", direccion="Av. Colon 1200", telefono="351-4000001", horario="Lun a Vie 8 a 20"),
    SedeCrear(nombre="Sede Norte", direccion="Av. Monsenor Pablo Cabrera 3500", telefono="351-4000002", horario="Lun a Vie 9 a 18"),
    SedeCrear(nombre="Sede Sur", direccion="Av. Velez Sarsfield 4100", telefono="351-4000003", horario="Lun a Sab 9 a 14"),
]

SOCIOS = [
    SocioCrear(dni="38111222", nombre="Lucia", apellido="Fernandez", email="lucia.fernandez@mail.com"),
    SocioCrear(dni="40222333", nombre="Martin", apellido="Gomez", email="martin.gomez@mail.com"),
    SocioCrear(dni="35333444", nombre="Sofia", apellido="Ramirez", email="sofia.ramirez@mail.com"),
]

LIBROS = [
    LibroCrear(isbn="9789875666474", titulo="Ficciones", autor="Jorge Luis Borges", editorial="Debolsillo", anio_publicacion=1944),
    LibroCrear(isbn="9789500728997", titulo="Rayuela", autor="Julio Cortazar", editorial="Alfaguara", anio_publicacion=1963),
    LibroCrear(isbn="9789500739559", titulo="El tunel", autor="Ernesto Sabato", editorial="Seix Barral", anio_publicacion=1948),
    LibroCrear(isbn="9788437604947", titulo="Cien anios de soledad", autor="Gabriel Garcia Marquez", editorial="Catedra", anio_publicacion=1967),
]


def cargar():
    db = SessionLocal()
    try:
        sedes = SedeService(db)
        socios = SocioService(db)
        catalogo = CatalogoService(db)
        try:
            creadas = [sedes.crear(s) for s in SEDES]
        except DuplicadoError:
            print("La base ya tiene datos de ejemplo, no se carga nada.")
            return
        for socio in SOCIOS:
            socios.crear(socio)
        n = 1
        for libro_datos in LIBROS:
            libro = catalogo.crear_libro(libro_datos)
            for sede in creadas[:2]:
                catalogo.crear_ejemplar(
                    EjemplarCrear(codigo_inventario=f"INV-{n:05d}", libro_id=libro.id, sede_id=sede.id)
                )
                n += 1
        print(f"Cargados {len(SEDES)} sedes, {len(SOCIOS)} socios, {len(LIBROS)} libros y {n - 1} ejemplares.")
    finally:
        db.close()


if __name__ == "__main__":
    cargar()
