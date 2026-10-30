# Arquitectura

El sistema tiene dos partes: una API REST en Python (backend) y una aplicación web en React
(frontend) que la consume por HTTP. La documentación interactiva de los endpoints está en `/docs`
(Swagger) al levantar la API.

## Vista general

```mermaid
flowchart LR
    NAV[Navegador] -- descarga la app --> WEB[web: Nginx + React]
    NAV -- HTTP/JSON --> API
    subgraph Contenedor api
        API[FastAPI] --> SRV[Servicios]
        SRV --> REPO[Repositorios]
        REPO --> ORM[SQLAlchemy]
    end
    ORM -- psycopg2 --> DB[(PostgreSQL)]
    MIG[Alembic] -. crea/actualiza tablas .-> DB
```

## Capas

```
app/
  routers/       HTTP: recibe la petición, valida la entrada, devuelve la respuesta
  schemas/       Contratos de entrada y salida (Pydantic)
  services/      Reglas de negocio, validaciones y control de la transacción
  domain/        Lógica pura sin base de datos: estados del remito, multas, enums
  repositories/  Consultas a la base
  models/        Entidades mapeadas a tablas (SQLAlchemy)
```

Cada capa solo conoce a la de abajo:

| Capa | Responsabilidad | No hace |
|---|---|---|
| Router | Traducir HTTP a llamadas al servicio | Lógica de negocio |
| Schema | Validar formato (tipos, largos, email, DNI numérico) | Validar reglas de negocio |
| Servicio | Aplicar las reglas de la consigna, coordinar entidades, hacer commit | Armar SQL |
| Dominio | Transiciones del remito, cálculo de multas | Acceder a la base |
| Repositorio | Consultar y agregar entidades | Commit, reglas de negocio |
| Modelo | Representar la entidad y su comportamiento propio | Conocer HTTP o servicios |

`domain/` está separado para que los patrones se puedan probar sin base de datos
(`tests/test_estados_remito.py`, `tests/test_multas.py`).

## Flujo de una petición

Ejemplo: `POST /prestamos` para un préstamo interbibliotecario.

```mermaid
sequenceDiagram
    participant C as Cliente
    participant R as Router (prestamos.py)
    participant S as PrestamoService
    participant RS as RemitoService
    participant Rep as Repositorios
    participant DB as PostgreSQL

    C->>R: POST /prestamos {socio, ejemplar, origen, destino}
    R->>R: Pydantic valida el JSON (si falla: 422)
    R->>S: solicitar(datos)
    S->>Rep: socio, sedes, ejemplar, préstamos del socio
    Rep->>DB: SELECT
    S->>S: valida reglas (si falla: ReglaNegocioError)
    S->>Rep: agregar(prestamo)
    S->>RS: generar(prestamo, IDA)
    RS->>Rep: agregar(remito) con movimiento PENDIENTE
    S->>DB: COMMIT
    S-->>R: Prestamo
    R-->>C: 201 + PrestamoRespuesta
```

Si cualquier validación falla, no se llega al commit. La sesión se cierra al terminar la petición
y lo que se haya hecho se descarta.

## Manejo de errores

Los servicios lanzan excepciones propias (`app/exceptions.py`), sin depender de HTTP. Un único
manejador en `app/main.py` las traduce a códigos HTTP:

```mermaid
classDiagram
    class BibliotecaError {
        +mensaje: str
    }
    BibliotecaError <|-- NoEncontradoError
    BibliotecaError <|-- DuplicadoError
    BibliotecaError <|-- ReglaNegocioError
    ReglaNegocioError <|-- TransicionInvalidaError
```

| Excepción | HTTP | Ejemplo |
|---|---|---|
| `NoEncontradoError` | 404 | El socio 99 no existe |
| `DuplicadoError` | 409 | Ya existe un socio con ese DNI |
| `ReglaNegocioError` | 400 | El socio está inhabilitado |
| `TransicionInvalidaError` | 400 | No se puede despachar un remito PENDIENTE |
| Error de validación de Pydantic | 422 | Email con formato inválido |

La respuesta siempre tiene la forma `{"detail": "mensaje"}`.

## Paginación

Todos los listados están paginados, salvo `GET /sedes` (son pocas y se usan para completar
listas desplegables). Se piden con `?pagina=1&tamanio=20` (tamaño máximo 100) y responden:

```json
{
  "items": [ ... ],
  "total": 57,
  "pagina": 2,
  "tamanio": 20,
  "paginas": 3
}
```

`BaseRepository.paginar` resuelve el conteo y el corte para cualquier consulta, así cada
repositorio solo arma su consulta con filtros. Los listados tienen un orden estable (desempatan
por id) para que un elemento no aparezca en dos páginas.

## CORS

El navegador bloquea las llamadas de una página a un servidor de otro origen (otro dominio o
puerto) salvo que el servidor las autorice. Como el frontend corre en su propio servidor, la API
habilita los orígenes listados en `CORS_ORIGENES`. Por defecto son los puertos habituales de
desarrollo: 3000 (React), 5173 (Vite) y 4200 (Angular).

## Respuestas con datos relacionados

Las respuestas de préstamos, remitos, reservas, ejemplares e incidencias incluyen, además de los
ids, un resumen de las entidades relacionadas (`app/schemas/resumen.py`). Por ejemplo, un préstamo
trae `socio: {id, dni, nombre, apellido}`, `ejemplar: {codigo_inventario, libro: {titulo, autor}}`
y las dos sedes. Así una tabla del frontend se arma con una sola llamada en lugar de una por fila.

## Búsquedas

Las búsquedas por texto (socios por nombre, apellido o DNI; libros por título o autor) son
parciales e ignoran mayúsculas y tildes: "cortazar" encuentra "Cortázar". Usan la extensión
`unaccent` de Postgres, que se habilita en la migración `0003`. Los caracteres `%` y `_` que
escriba el usuario se buscan como texto, no como comodines (`contiene()` en
`app/repositories/base.py`).

## Sesión y transacciones

- `app/database.py` crea el `engine` una sola vez y define `get_db()`, que abre una sesión por
  petición y la cierra al terminar.
- Los routers reciben el servicio por inyección de dependencias (`Depends`). El servicio recibe
  la sesión en el constructor y la comparte con los repositorios que usa.
- Solo los servicios hacen `commit`, una vez por operación de negocio. Los repositorios hacen
  `flush`. La justificación está en [patrones-de-diseno.md](patrones-de-diseno.md#repository-acceso-a-datos).

## Decisiones técnicas

| Decisión | Alternativa | Por qué |
|---|---|---|
| **FastAPI** | Flask | Valida la entrada con Pydantic y genera la documentación de cada endpoint (Swagger) automáticamente, que es lo que usa el equipo de frontend. |
| **PostgreSQL** | SQLite (visto en clase) | Base cliente-servidor real: soporta concurrencia, corre en su propio contenedor y es lo que se usaría en un despliegue. SQLite guarda todo en un archivo local y bloquea la base entera en cada escritura. |
| **SQLAlchemy (ORM)** | SQL con `cursor` (visto en clase) | Visto en la semana 8. Mapea las clases a tablas, maneja relaciones y transacciones, y evita escribir SQL a mano. Es el equivalente en Python a JPA / Spring Data. |
| **Alembic** | `Base.metadata.create_all()` | `create_all` solo crea tablas que no existen: no aplica cambios a tablas existentes. Alembic versiona cada cambio del esquema como una migración que se puede aplicar y revertir. |
| **Pydantic** | Validar a mano | Valida tipos y formatos antes de llegar al servicio y documenta los contratos en Swagger. |
| **Docker Compose** | Instalar todo localmente | Cualquier integrante levanta el sistema completo (base + API) con un comando y la misma versión de todo. |
| **pytest contra Postgres** | Tests con SQLite en memoria | Se prueba contra el mismo motor que en producción; algunas consultas (`ilike`, agregaciones) se comportan distinto según el motor. |
| **Sin autenticación** | Login con roles | La consigna no lo pide. Se puede agregar sin cambiar los servicios. |
| **React + Vite** | Angular, Vue | La opción más difundida y la que el grupo conoce. Vite compila rápido y recarga al guardar. |
| **JavaScript** | TypeScript | Menos configuración y curva de aprendizaje para un grupo con poco tiempo. |
| **Ant Design** | Material UI, Bootstrap | Pensada para paneles de gestión: tablas paginadas, formularios con validación, línea de tiempo y pasos ya resueltos, y traducida al español. |
| **Recharts** | Chart.js | Gráficos declarados como componentes de React. |

## Configuración

Todo se configura por variables de entorno (`app/config.py`, ejemplo en `.env.example`):

| Variable | Por defecto | Uso |
|---|---|---|
| `DATABASE_URL` | Postgres local | Conexión de la API |
| `CORS_ORIGENES` | `localhost` en 3000, 5173 y 4200 | Orígenes del frontend habilitados, separados por coma |
| `TEST_DATABASE_URL` | `biblioteca_test` local | Conexión de los tests |
| `DIAS_PRESTAMO` | 14 | Plazo del préstamo |
| `MAX_PRESTAMOS_ACTIVOS` | 3 | Préstamos en curso por socio |
| `DIAS_VALIDEZ_RESERVA` | 3 | Días para retirar una reserva disponible |
| `MULTA_ESTRATEGIA` | `fija` | `fija` o `escalonada` |
| `MULTA_MONTO_DIARIO` | 500 | Monto base de la multa |

## Despliegue

```mermaid
flowchart LR
    subgraph docker compose
        WEB[web<br/>nginx:1.27-alpine<br/>puerto 3000] --> API
        API[api<br/>python:3.12-slim<br/>puerto 8000] -- espera healthcheck --> DB[(db<br/>postgres:16-alpine<br/>puerto 5432)]
        DB --- VOL[(volumen pgdata)]
    end
```

- `db`: Postgres con un volumen para que los datos sobrevivan a reinicios. Un script de inicio
  (`docker/init-db.sql`) crea además la base `biblioteca_test`.
- `api`: la imagen se construye con el `Dockerfile`. Al arrancar, `docker/entrypoint.sh` aplica
  las migraciones pendientes (`alembic upgrade head`) y después levanta uvicorn. Arranca recién
  cuando la base responde (`depends_on` con `service_healthy`).
- `web`: el `frontend/Dockerfile` compila la aplicación con Node y la sirve con Nginx
  (`frontend/nginx.conf`). La URL de la API se fija al compilar (`VITE_API_URL`). Nginx devuelve
  `index.html` para cualquier ruta, así funcionan las direcciones del panel (`/remitos/3`) al
  recargar la página.

## Tests

| Archivo | Qué prueba | Base de datos |
|---|---|---|
| `test_estados_remito.py` | Patrón State: transiciones válidas, inválidas e historial | No |
| `test_multas.py` | Patrón Strategy: cada estrategia y el cambio entre ellas | No |
| `test_prestamos.py` | Préstamos locales e inter-sede, remitos, devoluciones y validaciones | Sí |
| `test_reservas.py` | Reservas, orden de llegada, vencimientos | Sí |
| `test_reportes.py` | Los seis reportes con datos armados | Sí |
| `test_incidencias.py` | Revisión de recepción: daño, destrucción, extravío y listado de incidencias | Sí |
| `test_historial.py` | Historial de lecturas del socio | Sí |
| `test_api.py` | Endpoints, códigos HTTP, paginación y CORS | Sí |

Cada test corre dentro de una transacción que se revierte al terminar (`tests/conftest.py`), así
los tests no dependen entre sí ni del orden en que se ejecutan. GitHub Actions corre la suite y
prueba las migraciones (ida y vuelta) en cada push; también revisa (ESLint) y compila el frontend.

## Frontend

```
frontend/src/
  api/          una función por endpoint, agrupadas por recurso
  componentes/  etiquetas de estado, selectores con búsqueda, encabezados
  hooks/        useListado, useCarga, useAccion
  layouts/      panel del personal y consulta pública
  paginas/      una pantalla por sección
  utiles/       textos y colores de los estados, formatos
```

- **Dos áreas**: el panel del personal (`/`) y la consulta para socios (`/consulta`), sin login.
  La consulta busca al socio por DNI exacto y muestra solo sus préstamos en curso y reservas
  activas.
- **Llamadas a la API**: centralizadas en `src/api/`. Un interceptor de axios convierte los
  errores en un `Error` con el mensaje del backend, que las pantallas muestran tal cual. Las
  reglas de negocio no se duplican en el front.
- **Listados**: el hook `useListado` maneja la paginación del backend, los filtros y la recarga.
- **Carga por pantalla**: cada página se descarga recién cuando se visita (`React.lazy`), así la
  primera carga no incluye, por ejemplo, la librería de gráficos de Reportes.
- **Gráficos**: barras horizontales con una paleta validada para daltonismo, y siempre una tabla
  con los mismos datos al lado.
