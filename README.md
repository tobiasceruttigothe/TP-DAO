# Biblioteca - Sistema de Préstamos Interbibliotecarios

TP Integrador 2026 - Desarrollo de Aplicaciones con Objetos (Tema 1).

Backend en Python con FastAPI, SQLAlchemy y PostgreSQL. La documentación interactiva de
cada endpoint queda disponible en `/docs` (Swagger) y `/redoc` al levantar la API.

## Documentación

| Documento | Contenido |
|---|---|
| [Modelo de datos](docs/modelo-de-datos.md) | Diagrama entidad-relación, decisiones de modelado, restricciones y estados de cada entidad |
| [Patrones de diseño](docs/patrones-de-diseno.md) | State, Strategy y Repository con diagramas de clases; por qué se descartó Singleton |
| [Arquitectura](docs/arquitectura.md) | Capas, flujo de una petición, manejo de errores, decisiones técnicas y despliegue |
| [Procesos y reglas de negocio](docs/procesos-y-reglas.md) | Cada proceso y validación de la consigna, dónde se implementa y qué test lo cubre |

## Stack

| Componente      | Elección                         |
|-----------------|----------------------------------|
| API             | FastAPI                          |
| ORM             | SQLAlchemy 2.0                   |
| Base de datos   | PostgreSQL 16                    |
| Migraciones     | Alembic                          |
| Validación      | Pydantic                         |
| Tests           | pytest                           |
| Despliegue      | Docker + docker compose          |
| CI              | GitHub Actions                   |

## Cómo levantarlo

### Con Docker (recomendado)

```bash
docker compose up --build
```

Levanta Postgres y la API en `http://localhost:8000`. Al iniciar, el contenedor aplica las
migraciones pendientes. Para cargar datos de ejemplo (sedes, socios, catálogo y un escenario con
préstamos devueltos, activos y vencidos, multas, envíos en distintos estados, incidencias y
reservas, para que los reportes muestren información):

```bash
docker compose exec api python -m app.seed
```

Tests dentro del contenedor (usan la base `biblioteca_test`):

```bash
docker compose exec api pytest
```

### Sin Docker

Requiere Python 3.12+ y un Postgres corriendo.

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp .env.example .env             # ajustar DATABASE_URL si hace falta
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
  services/      reglas de negocio y validaciones
  schemas/       DTOs de entrada/salida (Pydantic)
  routers/       endpoints HTTP
alembic/         migraciones
tests/
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

`EstrategiaMulta` define `calcular(dias_atraso)`. Hay dos implementaciones: `MultaFija`
(monto por día) y `MultaEscalonada` (monto base la primera semana, doble desde el día 8).
`CalculadorMulta` es el contexto y la estrategia se elige por configuración
(`MULTA_ESTRATEGIA`).

Por qué: la política de multas es lo que más probablemente cambie (cada biblioteca o cada año
puede tener otra). Con Strategy se cambia o agrega una política sin tocar el préstamo ni la
devolución, y cada política se testea aislada.

### Repository / DAO (`app/repositories/`)

`BaseRepository` resuelve las operaciones comunes (obtener, listar, agregar, eliminar) y cada
repositorio concreto agrega sus consultas. Los servicios no escriben SQL ni conocen la sesión
más allá de hacer commit, lo que separa la lógica de negocio de la persistencia.

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

- No se prestan ejemplares no disponibles. Un ejemplar reservado solo lo puede retirar el socio
  que lo reservó.
- No se presta ni se reserva a socios inhabilitados.
- Un socio con préstamos vencidos sin devolver no puede pedir otro.
- Máximo de préstamos en curso por socio (por defecto 3).
- El ejemplar debe pertenecer a la sede de origen del préstamo.
- No se inician préstamos, reservas ni envíos hacia o desde una sede dada de baja. El remito de
  retorno sí se permite: el ejemplar tiene que volver a su sede igual.
- Sin duplicados: nombre de sede, DNI y email de socio, ISBN y código de inventario.
- El vencimiento se calcula al activarse el préstamo (por defecto 14 días). La multa se calcula
  al devolver, según la estrategia configurada.
- Las reservas se atienden por orden de llegada. Cuando se libera un ejemplar se aparta para la
  primera reserva pendiente, que tiene 3 días para retirarlo.
- Un ejemplar devuelto o recibido dañado pasa a EN_REPARACION y no circula hasta marcarlo reparado.
  Si llega o se devuelve destruido se da de baja.
- Los extravíos, daños y destrucciones en envíos quedan registrados como incidencias.

Los valores numéricos se configuran por variables de entorno (ver `.env.example`).

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
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

### Reportes

| Ruta | Contenido |
|---|---|
| `/reportes/prestamos-activos` | Préstamos activos y material en tránsito |
| `/reportes/vencidos-multas` | Préstamos vencidos y multas acumuladas por socio |
| `/reportes/libros-mas-solicitados` | Ranking de libros en préstamos inter-sedes (filtro por fechas) |
| `/reportes/disponibilidad-sedes` | Ejemplares por sede y estado, % disponible |
| `/reportes/envios` | Tasa de envíos exitosos e incidencias |
| `/reportes/movimientos-sedes` | Envíos por origen/destino y tiempo promedio de tránsito |

Códigos de error: `400` regla de negocio, `404` no encontrado, `409` duplicado,
`422` datos de entrada inválidos.

Los listados (salvo `/sedes`) están paginados con `?pagina=&tamanio=` y devuelven
`{items, total, pagina, tamanio, paginas}`. La API acepta llamadas del frontend desde los orígenes
configurados en `CORS_ORIGENES` (ver `.env.example`).

## Tests

Los tests corren contra Postgres (base `biblioteca_test`, configurable con `TEST_DATABASE_URL`).
Cada test se ejecuta dentro de una transacción que se descarta al terminar, así no dependen
entre sí. Hay tests unitarios de los patrones (sin base de datos), de servicios y de la API.
