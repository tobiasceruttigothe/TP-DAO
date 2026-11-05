# Biblioteca - Sistema de Préstamos Interbibliotecarios

TP Integrador 2026 - Desarrollo de Aplicaciones con Objetos (Tema 1).

Backend en Python con FastAPI, SQLAlchemy y PostgreSQL. La documentación interactiva de
cada endpoint queda disponible en `/docs` (Swagger) y `/redoc` al levantar la API.

## Documentación

| Documento | Contenido |
|---|---|
| [Instalar Docker en Windows](docs/instalar-docker-windows.md) | Paso a paso para instalar WSL 2 y Docker Desktop |
| [Despliegue local](docs/despliegue-local.md) | Levantar el sistema, cargar datos, comandos diarios y problemas frecuentes |
| [Modelo de datos](docs/modelo-de-datos.md) | Diagrama entidad-relación, decisiones de modelado, restricciones y estados de cada entidad |
| [Patrones de diseño](docs/patrones-de-diseno.md) | State, Strategy, Repository y Observer con diagramas de clases; por qué se descartaron Singleton y Keycloak |
| [Arquitectura](docs/arquitectura.md) | Capas, flujo de una petición, seguridad y roles, correo, manejo de errores, decisiones técnicas y despliegue |
| [Procesos y reglas de negocio](docs/procesos-y-reglas.md) | Cada proceso y validación de la consigna, dónde se implementa y qué test lo cubre |

## Stack

| Componente      | Elección                         |
|-----------------|----------------------------------|
| API             | FastAPI                          |
| Frontend        | React 18 + Vite, Ant Design      |
| ORM             | SQLAlchemy 2.0                   |
| Base de datos   | PostgreSQL 16                    |
| Migraciones     | Alembic                          |
| Validación      | Pydantic                         |
| Seguridad       | JWT (PyJWT) + bcrypt             |
| Correo          | SMTP: Mailpit (desarrollo), Gmail |
| Tests           | pytest                           |
| Despliegue      | Docker + docker compose          |
| CI              | GitHub Actions                   |

## Cómo levantarlo

### Con Docker (recomendado)

Guía detallada para Windows, incluida la instalación de Docker: [docs/despliegue-local.md](docs/despliegue-local.md).

```bash
docker compose up --build
```

Levanta Postgres, la API en `http://localhost:8000`, el frontend en `http://localhost:3000` y
Mailpit (los correos que manda el sistema) en `http://localhost:8025`. Al iniciar, la API aplica
las migraciones pendientes y crea el administrador (`admin@example.com` / `admin123`). Para
cargar datos de ejemplo (sedes, socios con su cuenta, catálogo y un escenario con préstamos
devueltos, activos y vencidos, multas, envíos en distintos estados, incidencias, reservas,
pedidos y un inventario, para que todas las pantallas muestren información):

```bash
docker compose exec api python -m app.seed
```

Los socios de ejemplo ingresan con su email (por ejemplo `lucia.fernandez@example.com`) y la
contraseña `socio123`. Más usuarios y cómo mandar correos reales con Gmail en
[docs/despliegue-local.md](docs/despliegue-local.md#usuarios-para-probar).

Tests dentro del contenedor (usan la base `biblioteca_test`):

```bash
docker compose exec api pytest
```

### Sin Docker

Requiere Python 3.12+ y un Postgres corriendo (con las extensiones estándar, que incluyen
`unaccent`). El frontend se levanta aparte: ver [frontend/README.md](frontend/README.md).

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # ajustar DATABASE_URL; SMTP_HOST=localhost (o CORREO_MODO=desactivado)
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
pytest
```

## Estructura

```
app/
  domain/        enums, estados del remito (State) y cálculo de multas (Strategy)
  models/        entidades mapeadas con SQLAlchemy
  repositories/  acceso a datos, una clase por entidad
  seguridad/     contraseñas (bcrypt) y tokens de sesión (JWT)
  services/      reglas de negocio y validaciones; eventos y notificaciones (Observer), correo
  schemas/       DTOs de entrada/salida (Pydantic)
  routers/       endpoints HTTP
alembic/         migraciones
tests/
frontend/        aplicación web (ver frontend/README.md)
```

El flujo de una petición es siempre `router -> service -> repository -> modelo`. Los routers
no tienen lógica, los repositorios no hacen commit y las reglas de negocio están en los servicios.

## Modelo

- **Sede**: datos de contacto, horario y estado activa/baja.
- **Socio**: DNI y email únicos; puede estar habilitado o inhabilitado (con motivo).
- **Libro**: la obra del catálogo (ISBN único).
- **Ejemplar**: copia física de un libro; pertenece a una sede y tiene código de inventario único,
  estado de circulación y estado físico.
- **Préstamo**: local (origen = destino) o interbibliotecario (origen ≠ destino).
- **Remito**: envío de un ejemplar entre sedes. Cada cambio de estado queda registrado en
  **MovimientoRemito**, que da la trazabilidad completa.
- **Reserva**: un socio reserva un libro en una sede.
- **Usuario**: cuenta para ingresar (administrador o socio). La del socio está vinculada a su
  ficha de Socio.
- **Pedido**: lo que pide un socio desde el catálogo; el administrador lo resuelve con una
  reserva o un préstamo inter-sede, o lo rechaza.
- **Notificación**: aviso para un usuario, que además puede llegar por correo.
- **Inventario**: recuento físico de una sede, con los códigos leídos (**ItemInventario**).

### Ciclo de vida del remito

```
PENDIENTE ──empaquetar──> EMPAQUETADO ──despachar──> DESPACHADO ──recibir──> RECIBIDO
    │                          │                          │
    └────────cancelar──────────┴──> CANCELADO             └──extraviar──> EXTRAVIADO
```

Un préstamo interbibliotecario genera dos remitos:

1. **IDA** (sede origen → sede destino) al solicitarse. Al recibirse, el préstamo pasa a ACTIVO
   y empieza a correr el plazo.
2. **RETORNO** (sede destino → sede origen) al registrarse la devolución. Al recibirse, el
   ejemplar vuelve a estar disponible en su sede.

Efectos sobre el resto del sistema:

| Transición               | Préstamo                 | Ejemplar                         |
|--------------------------|--------------------------|----------------------------------|
| despachar (IDA)          | EN_TRANSITO              | EN_TRANSITO                      |
| recibir (IDA)            | ACTIVO                   | PRESTADO                         |
| recibir (RETORNO)        | -                        | DISPONIBLE (o EN_REPARACION)     |
| extraviar                | CANCELADO (si es IDA)    | EXTRAVIADO                       |
| cancelar (solo IDA)      | CANCELADO                | DISPONIBLE                       |

## Patrones de diseño

### State - ciclo de vida del remito (`app/domain/estados_remito.py`)

El remito es el contexto y cada estado es una clase que decide qué operaciones admite.
`EstadoRemito` define todas las operaciones rechazando la transición por defecto; cada estado
concreto sobrescribe solo las que son válidas para él.

Por qué: el enunciado evalúa especialmente el ciclo de vida del remito. Sin el patrón, cada
operación tendría un `if estado == ... elif ...` repetido, y agregar un estado obligaría a
tocar todos esos condicionales. Con State, las reglas de cada estado están en un solo lugar,
agregar uno nuevo es agregar una clase, y una transición inválida es imposible por diseño.

En la base se guarda el nombre del estado (columna `estado`) y se reconstruye el objeto al
operar (`Remito.estado_actual`).

### Strategy - cálculo de multas (`app/domain/multas.py`)

`EstrategiaMulta` define `calcular(datos)`. Hay tres estrategias que conviven: `MultaAtrasoLeve`
(hasta 7 días, $500 por día), `MultaAtrasoGrave` (desde el día 8: los primeros 7 a $500 y el resto
a $1.000) y `MultaPorDanio` (cargo fijo si se devuelve dañado o destruido). En cada devolución,
`CalculadorMulta` (el contexto) elige cuáles aplicar según los días de atraso y el estado físico,
y suma. La multa se guarda con su detalle.

Por qué: hay varias formas de multar según la situación, y la política es lo que más
probablemente cambie. Con Strategy cada regla está en su clase, se agrega una nueva sin tocar el
préstamo ni la devolución, y cada una se testea aislada.

### Repository / DAO (`app/repositories/`)

`BaseRepository` resuelve las operaciones comunes (obtener, listar, agregar, eliminar) y cada
repositorio concreto agrega sus consultas. Los servicios no escriben SQL ni conocen la sesión
más allá de hacer commit, lo que separa la lógica de negocio de la persistencia.

### Observer - notificaciones (`app/services/eventos.py`)

Los servicios publican un evento (`PedidoNuevo`, `CuentaAprobada`, `ReservaDisponible`, ...) en
un `PublicadorEventos`. Los observadores suscritos reaccionan: `NotificacionesEnSistema` guarda
la notificación de la campana y `NotificacionesPorCorreo` manda el mail, recién cuando la
operación se confirma en la base.

Por qué: muchos procesos tienen que avisar a alguien y por dos canales. Sin el patrón, cada
servicio conocería la tabla de notificaciones y el servidor de correo. Con Observer, los
servicios solo publican y sumar un canal es agregar un observador.

### Por qué no Singleton

Se evaluó usar Singleton para la conexión, pero no se aplicó:

- El `engine` de SQLAlchemy ya es único por proceso: se crea una sola vez al importar
  `app/database.py` (los módulos de Python se cargan una sola vez) y maneja internamente el
  pool de conexiones.
- Lo que no puede ser único es la **sesión**: no es thread-safe y FastAPI atiende requests en
  paralelo. Compartir una sesión entre requests mezclaría transacciones. Por eso se abre una
  sesión por request con `get_db()` y se inyecta con `Depends`.
- Un Singleton dificulta los tests: con inyección de dependencias los tests reemplazan
  `get_db` por una sesión de prueba sin tocar el código.

## Reglas de negocio

- Validación de formato en cada alta y modificación: DNI de 7 u 8 dígitos, nombre y apellido de
  2 a 50 letras, teléfono solo con dígitos, ISBN con dígito verificador, entre otros. El detalle
  está en [docs/procesos-y-reglas.md](docs/procesos-y-reglas.md#validaciones-de-formato).
- No se prestan ejemplares no disponibles. Un ejemplar reservado solo lo puede retirar el socio
  que lo reservó.
- No se presta ni se reserva a socios inhabilitados.
- Un socio con préstamos vencidos sin devolver no puede pedir otro.
- Si un préstamo pasa más de 30 días vencido, el socio queda inhabilitado automáticamente con el
  motivo cargado. Se rehabilita a mano. Lo hace el proceso de vencimientos, que la API corre sola
  cada hora (también vence las reservas no retiradas).
- Máximo de préstamos en curso por socio (por defecto 3).
- El ejemplar debe pertenecer a la sede de origen del préstamo.
- No se inician préstamos, reservas ni envíos hacia o desde una sede dada de baja. El remito de
  retorno sí se permite: el ejemplar tiene que volver a su sede igual.
- Sin duplicados: nombre de sede, DNI y email de socio, ISBN y código de inventario.
- El vencimiento se calcula al activarse el préstamo (por defecto 14 días). La multa se guarda
  al devolver, según la estrategia configurada; mientras tanto cada préstamo informa el atraso y
  la multa acumulada a la fecha.
- Las reservas se atienden por orden de llegada. Cuando se libera un ejemplar se aparta para la
  primera reserva pendiente, que tiene 3 días para retirarlo.
- Un ejemplar devuelto o recibido dañado pasa a EN_REPARACION y no circula hasta marcarlo reparado.
  Si llega o se devuelve destruido se da de baja.
- Los extravíos, daños y destrucciones en envíos quedan registrados como incidencias.
- El catálogo es público. Para pedir un libro, ver préstamos, reservas o historial hay que ser
  socio con cuenta activa: registrarse, confirmar el email y ser aprobado por un administrador.
- El socio hace un **pedido**; el administrador lo aprueba reservando en la sede pedida o
  trayéndolo de otra sede, o lo rechaza con un motivo. Un pedido pendiente por libro y socio.
- Cada aviso (cuenta aprobada, pedido resuelto, reserva lista, libro que llegó, préstamo por
  vencer o vencido, inhabilitación) aparece en el sistema y llega por correo.
- **Inventario**: recuento físico por sede leyendo los códigos de barras. Informa encontrados,
  faltantes, fuera de lugar y desconocidos; al cerrar, el informe queda guardado.

Los valores numéricos se configuran por variables de entorno (ver `.env.example`).

## Endpoints

En Swagger, los endpoints que piden sesión muestran un candado: para probarlos, ingresar con
`POST /auth/ingresar`, copiar el `token` y pegarlo en **Authorize**. Sin sesión solo se accede al catálogo
(`GET /libros`, `/libros/{id}`, `/libros/{id}/disponibilidad`, `GET /sedes`) y a `/auth`.
`/mi/...` es del socio conectado; `/notificaciones`, de cualquier usuario conectado; el resto,
del administrador.

| Método | Ruta | Descripción |
|---|---|---|
| POST | `/auth/registro`, `/auth/confirmar`, `/auth/reenviar-confirmacion` | Alta de socio y confirmación del email |
| POST | `/auth/ingresar` | Iniciar sesión: devuelve el token |
| GET | `/auth/yo` | Usuario conectado |
| GET | `/mi/socio`, `/mi/prestamos`, `/mi/reservas`, `/mi/historial` | Datos del socio conectado |
| POST | `/mi/reservas/{id}/cancelar` | Cancelar una reserva propia |
| GET/POST | `/mi/pedidos` | Mis pedidos / pedir un libro |
| POST | `/mi/pedidos/{id}/cancelar` | Cancelar un pedido pendiente |
| GET | `/notificaciones`, `/notificaciones/no-leidas` | Notificaciones del usuario conectado |
| POST | `/notificaciones/{id}/leida`, `/notificaciones/leer-todas` | Marcar como leídas |
| GET | `/pedidos`, `/pedidos/{id}` | Pedidos de los socios |
| POST | `/pedidos/{id}/reservar`, `/pedidos/{id}/enviar`, `/pedidos/{id}/rechazar` | Resolver un pedido |
| GET | `/usuarios` | Cuentas (filtro por estado, rol y texto) |
| POST | `/usuarios/{id}/aprobar`, `/usuarios/{id}/rechazar` | Aprobar o rechazar un registro |
| POST | `/usuarios/administradores` | Crear un administrador |
| GET/POST | `/inventarios` | Listar / iniciar un inventario |
| GET | `/inventarios/{id}` | Detalle con el informe |
| POST/DELETE | `/inventarios/{id}/codigos`, `/inventarios/{id}/codigos/{item}` | Registrar / quitar un código leído |
| POST | `/inventarios/{id}/cerrar` | Cerrar y guardar el informe |
| GET/POST | `/sedes` | Listar / crear sedes |
| GET/PUT | `/sedes/{id}` | Ver / modificar sede |
| PATCH | `/sedes/{id}/baja`, `/sedes/{id}/alta` | Dar de baja / reactivar |
| GET/POST | `/socios` | Listar (búsqueda con `q`) / crear socios |
| GET | `/socios/{id}/historial` | Historial de lecturas del socio |
| GET/PUT | `/socios/{id}` | Ver / modificar socio |
| PATCH | `/socios/{id}/inhabilitar`, `/socios/{id}/habilitar` | Cambiar habilitación |
| GET/POST | `/libros` | Buscar / crear libros |
| GET/PUT | `/libros/{id}` | Ver / modificar libro |
| GET | `/libros/{id}/disponibilidad` | Disponibilidad por sede |
| GET/POST | `/ejemplares` | Listar (filtros) / crear ejemplares |
| GET | `/ejemplares/{id}` | Ver ejemplar |
| PATCH | `/ejemplares/{id}/baja`, `/ejemplares/{id}/reparado` | Baja / fin de reparación |
| PATCH | `/ejemplares/{id}/extraviado`, `/ejemplares/{id}/recuperado` | Marcar extraviado / apareció |
| GET/POST | `/prestamos` | Listar / solicitar préstamo |
| GET | `/prestamos/{id}`, `/prestamos/{id}/remitos` | Ver préstamo y sus remitos |
| POST | `/prestamos/{id}/devolucion` | Registrar devolución |
| GET | `/remitos`, `/remitos/{id}`, `/remitos/numero/{numero}` | Consultar remitos con su historial |
| POST | `/remitos/{id}/empaquetar` `/despachar` `/recibir` `/extraviar` `/cancelar` | Transiciones |
| GET | `/incidencias` | Daños, destrucciones y extravíos de envíos |
| GET/POST | `/reservas` | Listar / crear reservas |
| GET | `/reservas/{id}` | Ver reserva |
| POST | `/reservas/{id}/cancelar` | Cancelar reserva |
| POST | `/reservas/procesar-vencidas` | Vencer reservas no retiradas |
| POST | `/procesos/vencimientos` | Proceso completo: vence reservas, avisa vencimientos e inhabilita por atraso |

### Reportes

| Ruta | Contenido |
|---|---|
| `/reportes/prestamos-activos` | Préstamos activos y material en tránsito |
| `/reportes/vencidos-multas` | Préstamos vencidos y multas acumuladas por socio |
| `/reportes/libros-mas-solicitados` | Ranking de libros en préstamos inter-sedes (filtro por fechas) |
| `/reportes/disponibilidad-sedes` | Ejemplares por sede y estado, % disponible |
| `/reportes/envios` | Tasa de envíos exitosos e incidencias |
| `/reportes/movimientos-sedes` | Envíos por origen/destino y tiempo promedio de tránsito |

Códigos de error: `400` regla de negocio, `401` sin sesión o sesión vencida, `403` sin permiso
para esa operación, `404` no encontrado, `409` duplicado, `422` datos de entrada inválidos.

Los listados (salvo `/sedes`) están paginados con `?pagina=&tamanio=` y devuelven
`{items, total, pagina, tamanio, paginas}`. La API acepta llamadas del frontend desde los orígenes
configurados en `CORS_ORIGENES` (ver `.env.example`).

## Tests

Los tests corren contra Postgres (base `biblioteca_test`, configurable con `TEST_DATABASE_URL`).
Cada test se ejecuta dentro de una transacción que se descarta al terminar, así no dependen
entre sí. Hay tests unitarios de los patrones (sin base de datos), de servicios y de la API.
