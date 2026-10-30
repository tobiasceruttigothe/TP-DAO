"""Carga datos de ejemplo para probar la API: python -m app.seed

Arma un escenario con historia: prestamos devueltos (con y sin multa), activos, vencidos,
envios en cada estado, incidencias y reservas. Todo pasa por los servicios, asi que respeta
las mismas reglas que la API. Las fechas se calculan hacia atras desde hoy.
"""
from datetime import date, datetime, time, timedelta

from app.database import SessionLocal
from app.domain.enums import EstadoFisico
from app.models import Remito
from app.repositories import EjemplarRepository, SedeRepository
from app.schemas.libro import EjemplarCrear, LibroCrear
from app.schemas.prestamo import DevolucionCrear, PrestamoCrear
from app.schemas.reserva import ReservaCrear
from app.schemas.sede import SedeCrear
from app.schemas.socio import SocioCrear
from app.services.catalogo_service import CatalogoService
from app.services.prestamo_service import PrestamoService
from app.services.remito_service import RemitoService
from app.services.reserva_service import ReservaService
from app.services.sede_service import SedeService
from app.services.socio_service import SocioService

SEDES = [
    ("CEN", SedeCrear(nombre="Biblioteca Central", direccion="Av. Colon 1200", telefono="351-4000001",
                      email="central@bibliotecas.gob.ar", horario="Lun a Vie 8 a 20, Sab 9 a 13")),
    ("NOR", SedeCrear(nombre="Sede Norte", direccion="Av. Monsenor Pablo Cabrera 3500", telefono="351-4000002",
                      email="norte@bibliotecas.gob.ar", horario="Lun a Vie 9 a 18")),
    ("SUR", SedeCrear(nombre="Sede Sur", direccion="Av. Velez Sarsfield 4100", telefono="351-4000003",
                      email="sur@bibliotecas.gob.ar", horario="Lun a Sab 9 a 14")),
    ("OES", SedeCrear(nombre="Sede Oeste", direccion="Av. Fuerza Aerea 2800", telefono="351-4000004",
                      horario="Lun a Vie 14 a 20")),
]

SOCIOS = [
    SocioCrear(dni="38111222", nombre="Lucia", apellido="Fernandez", email="lucia.fernandez@mail.com", telefono="351-5550001"),
    SocioCrear(dni="40222333", nombre="Martin", apellido="Gomez", email="martin.gomez@mail.com", telefono="351-5550002"),
    SocioCrear(dni="35333444", nombre="Sofia", apellido="Ramirez", email="sofia.ramirez@mail.com"),
    SocioCrear(dni="42444555", nombre="Joaquin", apellido="Diaz", email="joaquin.diaz@mail.com"),
    SocioCrear(dni="33555666", nombre="Valentina", apellido="Lopez", email="valentina.lopez@mail.com", telefono="351-5550005"),
    SocioCrear(dni="39666777", nombre="Tomas", apellido="Martinez", email="tomas.martinez@mail.com"),
    SocioCrear(dni="41777888", nombre="Camila", apellido="Sosa", email="camila.sosa@mail.com"),
    SocioCrear(dni="36888999", nombre="Nicolas", apellido="Romero", email="nicolas.romero@mail.com"),
    SocioCrear(dni="37999000", nombre="Diego", apellido="Acosta", email="diego.acosta@mail.com"),
]

LIBROS = [
    LibroCrear(isbn="9789875666474", titulo="Ficciones", autor="Jorge Luis Borges", editorial="Debolsillo", anio_publicacion=1944, genero="Cuentos"),
    LibroCrear(isbn="9789500728997", titulo="Rayuela", autor="Julio Cortazar", editorial="Alfaguara", anio_publicacion=1963, genero="Novela"),
    LibroCrear(isbn="9789500739559", titulo="El tunel", autor="Ernesto Sabato", editorial="Seix Barral", anio_publicacion=1948, genero="Novela"),
    LibroCrear(isbn="9788437604947", titulo="Cien anios de soledad", autor="Gabriel Garcia Marquez", editorial="Catedra", anio_publicacion=1967, genero="Novela"),
    LibroCrear(isbn="9789500747127", titulo="El Aleph", autor="Jorge Luis Borges", editorial="Debolsillo", anio_publicacion=1949, genero="Cuentos"),
    LibroCrear(isbn="9789871138548", titulo="Martin Fierro", autor="Jose Hernandez", editorial="Colihue", anio_publicacion=1872, genero="Poesia"),
    LibroCrear(isbn="9789504918974", titulo="Sobre heroes y tumbas", autor="Ernesto Sabato", editorial="Seix Barral", anio_publicacion=1961, genero="Novela"),
    LibroCrear(isbn="9789875809901", titulo="Bestiario", autor="Julio Cortazar", editorial="Alfaguara", anio_publicacion=1951, genero="Cuentos"),
    LibroCrear(isbn="9789500433860", titulo="Facundo", autor="Domingo F. Sarmiento", editorial="Emece", anio_publicacion=1845, genero="Ensayo"),
    LibroCrear(isbn="9789871136650", titulo="Don Segundo Sombra", autor="Ricardo Guiraldes", editorial="Losada", anio_publicacion=1926, genero="Novela"),
]

# Copias por sede de cada libro
COPIAS = {"CEN": 2, "NOR": 1, "SUR": 1}


def hace(dias: int) -> date:
    return date.today() - timedelta(days=dias)


def momento(dias: int, hora: int) -> datetime:
    return datetime.combine(hace(dias), time(hora))


class CargaDeEjemplo:
    def __init__(self, db):
        self.db = db
        self.prestamos = PrestamoService(db)
        self.remitos = RemitoService(db)
        self.ejemplares = EjemplarRepository(db)

    # --- Datos maestros ---

    def maestros(self):
        sedes = SedeService(self.db)
        self.sedes = {codigo: sedes.crear(datos) for codigo, datos in SEDES}
        self.socios = [SocioService(self.db).crear(datos) for datos in SOCIOS]
        catalogo = CatalogoService(self.db)
        self.libros = [catalogo.crear_libro(datos) for datos in LIBROS]
        numero = {codigo: 0 for codigo in COPIAS}
        for libro in self.libros:
            for codigo, cantidad in COPIAS.items():
                for _ in range(cantidad):
                    numero[codigo] += 1
                    catalogo.crear_ejemplar(
                        EjemplarCrear(
                            codigo_inventario=f"{codigo}-{numero[codigo]:04d}",
                            libro_id=libro.id,
                            sede_id=self.sedes[codigo].id,
                        )
                    )

    # --- Ayudas ---

    def _pedir(self, socio, libro, origen, destino, dias):
        ejemplar = self.ejemplares.primero_disponible(libro.id, self.sedes[origen].id)
        return self.prestamos.solicitar(
            PrestamoCrear(
                socio_id=socio.id,
                ejemplar_id=ejemplar.id,
                sede_origen_id=self.sedes[origen].id,
                sede_destino_id=self.sedes[destino].id,
            ),
            hoy=hace(dias),
        )

    def _devolver(self, prestamo, dias, estado_fisico=EstadoFisico.BUENO, observaciones=None):
        self.prestamos.devolver(
            prestamo.id,
            DevolucionCrear(estado_fisico=estado_fisico, fecha_devolucion=hace(dias), observaciones=observaciones),
        )

    def _enviar(self, remito: Remito, despacho: datetime, recepcion: datetime | None = None,
                estado_fisico=EstadoFisico.BUENO, observacion=None):
        """Lleva el remito hasta despachado (y recibido si hay fecha) y ajusta las fechas
        para que el historial y los tiempos de transito sean realistas."""
        self.remitos.empaquetar(remito.id)
        self.remitos.despachar(remito.id)
        if recepcion is not None:
            self.remitos.recibir(remito.id, estado_fisico, observacion, hoy=recepcion.date())
        self._fechar(remito, despacho - timedelta(hours=20), despacho, recepcion)

    def _fechar(self, remito: Remito, creacion: datetime, despacho=None, final=None):
        remito.fecha_creacion = creacion
        remito.fecha_despacho = despacho
        if remito.fecha_recepcion is not None:
            remito.fecha_recepcion = final
        fechas = {
            "PENDIENTE": creacion,
            "EMPAQUETADO": creacion + timedelta(hours=3),
            "DESPACHADO": despacho,
            "RECIBIDO": final,
            "EXTRAVIADO": final,
            "CANCELADO": creacion + timedelta(hours=1),
        }
        for movimiento in remito.movimientos:
            movimiento.fecha = fechas[movimiento.estado_nuevo] or creacion
        for incidencia in remito.incidencias:
            incidencia.fecha = final or creacion
        self.db.commit()

    # --- Escenario ---

    def historial(self):
        """Prestamos ya terminados, de los mas viejos a los mas nuevos."""
        lucia, martin, sofia, joaquin = self.socios[:4]
        libros = self.libros

        p = self._pedir(lucia, libros[0], "CEN", "CEN", 60)
        self._devolver(p, 50)
        p = self._pedir(lucia, libros[1], "CEN", "CEN", 45)
        self._devolver(p, 25, EstadoFisico.REGULAR, "Hojas subrayadas")  # 6 dias de atraso

        p = self._pedir(martin, libros[2], "CEN", "NOR", 40)
        self._enviar(p.remitos[0], momento(39, 10), momento(38, 12))
        self._devolver(p, 30)
        self._enviar(p.remitos[1], momento(29, 9), momento(28, 15))

        p = self._pedir(sofia, libros[3], "NOR", "SUR", 35)
        self._enviar(p.remitos[0], momento(34, 11), momento(32, 10))
        self._devolver(p, 20)
        self._enviar(p.remitos[1], momento(19, 10), momento(18, 9))

        p = self._pedir(joaquin, libros[4], "SUR", "SUR", 30)
        self._devolver(p, 12)  # 4 dias de atraso

    def en_curso(self):
        lucia, martin, sofia, joaquin, valentina, tomas, camila, nicolas = self.socios[:8]
        libros = self.libros

        # Ejemplar destruido en el viaje: el prestamo se cancela
        p = self._pedir(lucia, libros[0], "CEN", "SUR", 17)
        self._enviar(p.remitos[0], momento(16, 10), momento(15, 11), EstadoFisico.DESTRUIDO, "Llego mojado e ilegible")

        # Extraviado en el viaje
        p = self._pedir(valentina, libros[9], "CEN", "SUR", 13)
        self._enviar(p.remitos[0], momento(12, 9))
        self.remitos.marcar_extraviado(p.remitos[0].id, "La empresa de transporte no lo encuentra")
        self._fechar(p.remitos[0], momento(13, 14), momento(12, 9), momento(10, 16))

        # Llego danado pero se presta igual
        p = self._pedir(joaquin, libros[8], "CEN", "NOR", 10)
        self._enviar(p.remitos[0], momento(9, 10), momento(8, 13), EstadoFisico.DANADO, "Tapa despegada")

        # Interbibliotecario activo
        p = self._pedir(martin, libros[6], "CEN", "SUR", 6)
        self._enviar(p.remitos[0], momento(5, 10), momento(4, 12))

        # Prestamo local activo y otro vencido
        self._pedir(valentina, libros[5], "CEN", "CEN", 5)
        self._pedir(tomas, libros[0], "NOR", "NOR", 20)

        # En viaje ahora
        p = self._pedir(sofia, libros[2], "SUR", "CEN", 2)
        self._enviar(p.remitos[0], momento(1, 9))

        # Recien pedido y empaquetado
        p = self._pedir(camila, libros[7], "CEN", "NOR", 0)
        self._fechar(p.remitos[0], datetime.now() - timedelta(hours=2))
        p = self._pedir(camila, libros[1], "NOR", "CEN", 1)
        self.remitos.empaquetar(p.remitos[0].id)
        self._fechar(p.remitos[0], momento(1, 11))

        # Cancelado antes de salir
        p = self._pedir(nicolas, libros[4], "NOR", "SUR", 3)
        self.remitos.cancelar(p.remitos[0].id, "El socio ya no lo necesita")
        self._fechar(p.remitos[0], momento(3, 10))

    def reservas(self):
        servicio = ReservaService(self.db)
        joaquin, nicolas = self.socios[3], self.socios[7]
        martin_fierro = self.libros[5]
        central = self.sedes["CEN"]
        # La primera aparta la copia libre; la segunda queda en espera
        servicio.crear(ReservaCrear(socio_id=nicolas.id, libro_id=martin_fierro.id, sede_id=central.id))
        servicio.crear(ReservaCrear(socio_id=joaquin.id, libro_id=martin_fierro.id, sede_id=central.id))

    def estados_finales(self):
        SocioService(self.db).inhabilitar(self.socios[8].id, "Extravio un libro y no lo repuso")
        SedeService(self.db).dar_de_baja(self.sedes["OES"].id)


def cargar():
    db = SessionLocal()
    try:
        if SedeRepository(db).listar():
            print("La base ya tiene datos, no se carga nada.")
            return
        carga = CargaDeEjemplo(db)
        carga.maestros()
        carga.historial()
        carga.en_curso()
        carga.reservas()
        carga.estados_finales()
        print(
            f"Cargados {len(SEDES)} sedes, {len(SOCIOS)} socios, {len(LIBROS)} libros, "
            f"prestamos, envios, incidencias y reservas de ejemplo."
        )
    finally:
        db.close()


if __name__ == "__main__":
    cargar()
