import os

# Los tests no deben disparar el proceso periodico contra la base real
os.environ["PROCESO_AUTOMATICO"] = "false"
os.environ["CREAR_ADMIN_AL_INICIAR"] = "false"
os.environ["CORREO_MODO"] = "memoria"
os.environ["BCRYPT_RONDAS"] = "4"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.database import Base, get_db
from app.domain.enums import EstadoUsuario, Rol
from app.models import Usuario
from app.main import app
from app.schemas.libro import EjemplarCrear, LibroCrear
from app.schemas.sede import SedeCrear
from app.schemas.socio import SocioCrear
from app.seguridad import contrasenas, tokens
from app.services.catalogo_service import CatalogoService
from app.services.correo import CorreoEnMemoria
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


@pytest.fixture(autouse=True)
def correos():
    """Correos 'enviados' durante el test (CORREO_MODO=memoria)."""
    CorreoEnMemoria.enviados.clear()
    yield CorreoEnMemoria.enviados
    CorreoEnMemoria.enviados.clear()


def cliente_con_token(db, usuario=None):
    app.dependency_overrides[get_db] = lambda: db
    cliente = TestClient(app)
    if usuario is not None:
        cliente.headers["Authorization"] = f"Bearer {tokens.crear_token_sesion(usuario.id, usuario.rol.value)}"
    return cliente


@pytest.fixture
def client(db, datos):
    """Cliente con sesion de administrador (la mayoria de los endpoints son del panel)."""
    with cliente_con_token(db, datos.admin()) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def anonimo(db):
    with cliente_con_token(db) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def socio_conectado(db, datos):
    """(cliente, socio): cliente con la sesion de un socio activo."""
    socio = datos.socio()
    usuario = datos.usuario_de(socio)
    with cliente_con_token(db, usuario) as c:
        yield c, socio
    app.dependency_overrides.clear()


# --- Datos de prueba ---

def isbn_valido(n: int) -> str:
    """ISBN-13 distinto para cada n, con su digito verificador correcto."""
    base = f"978000{n:06d}"
    suma = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(base))
    return base + str((10 - suma % 10) % 10)


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
        datos = {"dni": str(30_000_000 + n), "nombre": "Ana", "apellido": "Perez", "email": f"socio{n}@mail.com"}
        datos.update(kwargs)
        return SocioService(self.db).crear(SocioCrear(**datos))

    def libro(self, **kwargs):
        n = self._n()
        datos = {"isbn": isbn_valido(n), "titulo": f"Libro {n}", "autor": "Borges"}
        datos.update(kwargs)
        return CatalogoService(self.db).crear_libro(LibroCrear(**datos))

    def admin(self, email: str | None = None):
        n = self._n()
        usuario = Usuario(
            email=email or f"admin{n}@example.com",
            nombre="Admin Prueba",
            hash_contrasena=contrasenas.generar_hash("admin1234"),
            rol=Rol.ADMIN,
            estado=EstadoUsuario.ACTIVO,
        )
        self.db.add(usuario)
        self.db.flush()
        return usuario

    def usuario_de(self, socio, contrasena: str = "socio1234", estado=EstadoUsuario.ACTIVO):
        usuario = Usuario(
            email=socio.email,
            nombre=f"{socio.nombre} {socio.apellido}",
            hash_contrasena=contrasenas.generar_hash(contrasena),
            rol=Rol.SOCIO,
            estado=estado,
            socio=socio,
        )
        self.db.add(usuario)
        self.db.flush()
        return usuario

    def ejemplar(self, libro, sede):
        n = self._n()
        return CatalogoService(self.db).crear_ejemplar(
            EjemplarCrear(codigo_inventario=f"INV-{n:05d}", libro_id=libro.id, sede_id=sede.id)
        )


@pytest.fixture
def datos(db):
    return Datos(db)
