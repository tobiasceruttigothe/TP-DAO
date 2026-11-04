"""Carga datos de ejemplo para probar la API: python -m app.seed

Arma un escenario con historia: prestamos devueltos (con y sin multa), activos, vencidos,
envios en cada estado, incidencias y reservas. Todo pasa por los servicios, asi que respeta
las mismas reglas que la API. Las fechas se calculan hacia atras desde hoy.
"""
from datetime import date, datetime, time, timedelta

from app.config import settings
from app.database import SessionLocal
from app.domain.enums import EstadoFisico
from app.models import Remito
from app.repositories import EjemplarRepository, SedeRepository
from app.schemas.libro import EjemplarCrear, LibroCrear
from app.schemas.prestamo import DevolucionCrear, PrestamoCrear
from app.schemas.reserva import ReservaCrear
from app.schemas.sede import SedeCrear
from app.schemas.socio import SocioCrear
from app.domain.enums import EstadoUsuario, Rol
from app.models import Usuario
from app.repositories import InventarioRepository
from app.schemas.pedido import PedidoCrear
from app.schemas.usuario import RegistroCrear
from app.seguridad import contrasenas
from app.services.catalogo_service import CatalogoService
from app.services.cuenta_service import CuentaService
from app.services.inventario_service import InventarioService
from app.services.pedido_service import PedidoService
from app.services.prestamo_service import PrestamoService
from app.services.proceso_service import ProcesoVencimientos
from app.services.remito_service import RemitoService
from app.services.reserva_service import ReservaService
from app.services.sede_service import SedeService
from app.services.socio_service import SocioService

SEDES = [
    ("CEN", SedeCrear(nombre="Biblioteca Central", direccion="Av. Colón 1200", telefono="3514000001",
                      email="central@bibliotecas.gob.ar", horario="Lun a Vie 8 a 20, Sab 9 a 13")),
    ("NOR", SedeCrear(nombre="Sede Norte", direccion="Av. Monseñor Pablo Cabrera 3500", telefono="3514000002",
                      email="norte@bibliotecas.gob.ar", horario="Lun a Vie 9 a 18")),
    ("SUR", SedeCrear(nombre="Sede Sur", direccion="Av. Vélez Sarsfield 4100", telefono="3514000003",
                      email="sur@bibliotecas.gob.ar", horario="Lun a Sab 9 a 14")),
    ("OES", SedeCrear(nombre="Sede Oeste", direccion="Av. Fuerza Aérea 2800", telefono="3514000004",
                      horario="Lun a Vie 14 a 20")),
]

SOCIOS = [
    SocioCrear(dni="38111222", nombre="Lucía", apellido="Fernández", email="lucia.fernandez@example.com", telefono="3515550001"),
    SocioCrear(dni="40222333", nombre="Martín", apellido="Gómez", email="martin.gomez@example.com", telefono="3515550002"),
    SocioCrear(dni="35333444", nombre="Sofia", apellido="Ramírez", email="sofia.ramirez@example.com"),
    SocioCrear(dni="42444555", nombre="Joaquín", apellido="Díaz", email="joaquin.diaz@example.com"),
    SocioCrear(dni="33555666", nombre="Valentina", apellido="López", email="valentina.lopez@example.com", telefono="3515550005"),
    SocioCrear(dni="39666777", nombre="Tomás", apellido="Martínez", email="tomas.martinez@example.com"),
    SocioCrear(dni="41777888", nombre="Camila", apellido="Sosa", email="camila.sosa@example.com"),
    SocioCrear(dni="36888999", nombre="Nicolás", apellido="Romero", email="nicolas.romero@example.com"),
    SocioCrear(dni="37999000", nombre="Diego", apellido="Acosta", email="diego.acosta@example.com"),
]

LIBROS = [
    LibroCrear(isbn="9789875666474", titulo="Ficciones", autor="Jorge Luis Borges", editorial="Debolsillo", anio_publicacion=1944, genero="Cuentos"),
    LibroCrear(isbn="9789500728997", titulo="Rayuela", autor="Julio Cortázar", editorial="Alfaguara", anio_publicacion=1963, genero="Novela"),
    LibroCrear(isbn="9789500739559", titulo="El túnel", autor="Ernesto Sábato", editorial="Seix Barral", anio_publicacion=1948, genero="Novela"),
    LibroCrear(isbn="9788437604947", titulo="Cien años de soledad", autor="Gabriel García Márquez", editorial="Catedra", anio_publicacion=1967, genero="Novela"),
    LibroCrear(isbn="9789500747127", titulo="El Aleph", autor="Jorge Luis Borges", editorial="Debolsillo", anio_publicacion=1949, genero="Cuentos"),
    LibroCrear(isbn="9789871138548", titulo="Martín Fierro", autor="José Hernández", editorial="Colihue", anio_publicacion=1872, genero="Poesía"),
    LibroCrear(isbn="9789504918974", titulo="Sobre héroes y tumbas", autor="Ernesto Sábato", editorial="Seix Barral", anio_publicacion=1961, genero="Novela"),
    LibroCrear(isbn="9789875809901", titulo="Bestiario", autor="Julio Cortázar", editorial="Alfaguara", anio_publicacion=1951, genero="Cuentos"),
    LibroCrear(isbn="9789500433860", titulo="Facundo", autor="Domingo F. Sarmiento", editorial="Emece", anio_publicacion=1845, genero="Ensayo"),
    LibroCrear(isbn="9789871136650", titulo="Don Segundo Sombra", autor="Ricardo Güiraldes", editorial="Losada", anio_publicacion=1926, genero="Novela"),
]

# Contrasena de todos los socios de ejemplo
CONTRASENA_SOCIOS = "socio123"

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
        self._enviar(p.remitos[0], momento(16, 10), momento(15, 11), EstadoFisico.DESTRUIDO, "Llegó mojado e ilegible")

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

    def cuentas(self):
        """Cada socio de ejemplo tiene su cuenta ya confirmada y aprobada. Sus emails son
        inventados (example.com), asi que no se les manda ningun correo."""
        hash_comun = contrasenas.generar_hash(CONTRASENA_SOCIOS)
        for socio in self.socios:
            self.db.add(
                Usuario(
                    email=socio.email,
                    nombre=f"{socio.nombre} {socio.apellido}",
                    hash_contrasena=hash_comun,
                    rol=Rol.SOCIO,
                    estado=EstadoUsuario.ACTIVO,
                    socio=socio,
                    recibe_correos=False,
                )
            )
        self.db.commit()

        # Una persona que se registro sola, confirmo su email y espera que la aprueben
        cuentas = CuentaService(self.db)
        pendiente = cuentas.registrar(
            RegistroCrear(
                dni="43111222",
                nombre="Florencia",
                apellido="Ruiz",
                email="florencia.ruiz@example.com",
                contrasena=CONTRASENA_SOCIOS,
            )
        )
        pendiente.recibe_correos = False
        cuentas.confirmar_email(pendiente.token_confirmacion)

    def pedidos(self):
        lucia, martin, sofia, camila = self.socios[0], self.socios[1], self.socios[2], self.socios[6]
        libros = self.libros
        servicio = PedidoService(self.db)

        def pedir(socio, libro, sede, comentario=None):
            return servicio.crear(socio, PedidoCrear(libro_id=libro.id, sede_id=self.sedes[sede].id, comentario=comentario))

        # Pendientes, para que el administrador los resuelva
        pedir(sofia, libros[8], "SUR", "Lo necesito para un trabajo de la facultad")
        pedir(martin, libros[9], "NOR")
        # Ya resueltos
        servicio.reservar(pedir(lucia, libros[7], "SUR").id)
        servicio.rechazar(
            pedir(camila, libros[4], "CEN").id,
            "El ejemplar está en restauración; volvé a pedirlo la semana próxima",
        )

    def inventario(self):
        """Un recuento ya cerrado en Sede Sur, con un faltante, un ejemplar de otra sede y un
        codigo desconocido, para que el informe tenga de todo."""
        sur = self.sedes["SUR"]
        servicio = InventarioService(self.db)
        inventario = servicio.iniciar(sur.id, "Recuento mensual")
        en_estante = InventarioRepository(self.db).esperados_en_sede(sur.id)
        for ejemplar in en_estante[1:]:  # el primero "no aparece"
            servicio.registrar_codigo(inventario.id, ejemplar.codigo_inventario)
        servicio.registrar_codigo(inventario.id, "NOR-0003")
        servicio.registrar_codigo(inventario.id, "SUR-9999")
        servicio.cerrar(inventario.id)

    def reservas(self):
        servicio = ReservaService(self.db)
        joaquin, nicolas = self.socios[3], self.socios[7]
        martin_fierro = self.libros[5]
        central = self.sedes["CEN"]
        # La primera aparta la copia libre; la segunda queda en espera
        servicio.crear(ReservaCrear(socio_id=nicolas.id, libro_id=martin_fierro.id, sede_id=central.id))
        servicio.crear(ReservaCrear(socio_id=joaquin.id, libro_id=martin_fierro.id, sede_id=central.id))

    def estados_finales(self):
        # Diego se llevo un libro hace casi dos meses y no lo devolvio: al correr el proceso
        # de vencimientos queda inhabilitado por atraso, con el motivo cargado.
        self._pedir(self.socios[8], self.libros[3], "CEN", "CEN", 50)
        ProcesoVencimientos(self.db).ejecutar()
        SedeService(self.db).dar_de_baja(self.sedes["OES"].id)


def cargar():
    db = SessionLocal()
    # Mientras se cargan los datos de ejemplo no se manda ningun correo
    db.info["sin_correo"] = True
    try:
        CuentaService(db).asegurar_admin()
        if SedeRepository(db).listar():
            print("La base ya tiene datos, no se carga nada.")
            return
        carga = CargaDeEjemplo(db)
        carga.maestros()
        carga.cuentas()
        carga.historial()
        carga.en_curso()
        carga.reservas()
        carga.estados_finales()
        carga.pedidos()
        carga.inventario()
        print(
            f"Cargados {len(SEDES)} sedes, {len(SOCIOS)} socios, {len(LIBROS)} libros, "
            f"prestamos, envios, incidencias, reservas, pedidos e inventario de ejemplo.\n"
            f"Administrador: {settings.admin_email} / {settings.admin_contrasena}\n"
            f"Socios: su email (por ejemplo {SOCIOS[0].email}) / {CONTRASENA_SOCIOS}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    cargar()
