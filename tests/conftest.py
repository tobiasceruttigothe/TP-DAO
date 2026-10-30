import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.database import Base, get_db
from app.main import app
from app.schemas.libro import EjemplarCrear, LibroCrear
from app.schemas.sede import SedeCrear
from app.schemas.socio import SocioCrear
from app.services.catalogo_service import CatalogoService
from app.services.sede_service import SedeService
from app.services.socio_service import SocioService

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+psycopg2://biblioteca:biblioteca@localhost:5432/biblioteca_test"
)


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    Base.metadata.drop_all(engine)
    with engine.begin() as conexion:
        conexion.execute(text("CREATE EXTENSION IF NOT EXISTS unaccent"))
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def db(engine):
    """Cada test corre dentro de una transaccion que se descarta al final.
    Los commit() de los servicios quedan como savepoints."""
    conexion = engine.connect()
    transaccion = conexion.begin()
    sesion = Session(bind=conexion, join_transaction_mode="create_savepoint", expire_on_commit=False)
    yield sesion
    sesion.close()
    transaccion.rollback()
    conexion.close()


@pytest.fixture
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# --- Datos de prueba ---

class Datos:
    """Atajos para armar escenarios sin repetir codigo en cada test."""

    def __init__(self, db: Session):
        self.db = db
        self._contador = 0

    def _n(self) -> int:
        self._contador += 1
        return self._contador

    def sede(self, nombre: str | None = None):
        n = self._n()
        return SedeService(self.db).crear(
            SedeCrear(nombre=nombre or f"Sede {n}", direccion=f"Calle {n} 123", horario="8 a 20")
        )

    def socio(self, **kwargs):
        n = self._n()
        datos = {"dni": f"3000000{n}", "nombre": "Ana", "apellido": f"Perez{n}", "email": f"socio{n}@mail.com"}
        datos.update(kwargs)
        return SocioService(self.db).crear(SocioCrear(**datos))

    def libro(self, **kwargs):
        n = self._n()
        datos = {"isbn": f"978000000{n:04d}", "titulo": f"Libro {n}", "autor": "Borges"}
        datos.update(kwargs)
        return CatalogoService(self.db).crear_libro(LibroCrear(**datos))

    def ejemplar(self, libro, sede):
        n = self._n()
        return CatalogoService(self.db).crear_ejemplar(
            EjemplarCrear(codigo_inventario=f"INV-{n:05d}", libro_id=libro.id, sede_id=sede.id)
        )


@pytest.fixture
def datos(db):
    return Datos(db)
