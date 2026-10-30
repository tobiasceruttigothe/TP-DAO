# Despliegue local

Paso a paso para levantar el backend (API + base de datos) en una PC con Docker. Si Docker
todavía no está instalado, seguir antes [instalar-docker-windows.md](instalar-docker-windows.md).

Los comandos son para **PowerShell** en Windows; en Linux o Mac son los mismos.

## Resumen rápido

Para quien ya lo hizo alguna vez:

```powershell
git clone https://github.com/tobiasceruttigothe/TP-DAO.git
cd TP-DAO
docker compose up --build -d
docker compose exec api python -m app.seed
# abrir http://localhost:8000/docs
```

## 1. Descargar el repositorio

Si el repositorio es privado, el dueño tiene que agregar a cada integrante como colaborador en
GitHub (*Settings* → *Collaborators*) y cada uno aceptar la invitación que le llega por mail.

```powershell
cd $HOME\Documents
git clone https://github.com/tobiasceruttigothe/TP-DAO.git
cd TP-DAO
```

La primera vez, Git puede abrir una ventana del navegador para iniciar sesión en GitHub.

## 2. Levantar el sistema

Con **Docker Desktop abierto** y dentro de la carpeta `TP-DAO`:

```powershell
docker compose up --build -d
```

Qué hace:

- `--build` construye la imagen de la API (la primera vez tarda unos minutos porque descarga
  Python y las librerías; las siguientes es casi inmediato).
- `-d` lo deja corriendo en segundo plano y devuelve la consola.
- Levanta dos contenedores: `db` (PostgreSQL) y `api` (la aplicación). La API espera a que la base
  esté lista y, al arrancar, crea o actualiza las tablas solas (migraciones).

Verificar que estén corriendo:

```powershell
docker compose ps
```

Los dos servicios tienen que figurar como `running` (la base, además, `healthy`).

## 3. Cargar datos de ejemplo

```powershell
docker compose exec api python -m app.seed
```

Carga sedes, socios, libros, ejemplares y un escenario con préstamos, envíos, incidencias y
reservas, para que todas las pantallas y reportes tengan algo que mostrar. Si la base ya tiene
datos, no hace nada.

## 4. Probar que funciona

| Qué | Dónde |
|---|---|
| Documentación interactiva (Swagger) | http://localhost:8000/docs |
| Documentación alternativa (ReDoc) | http://localhost:8000/redoc |
| Chequeo rápido | http://localhost:8000/health → `{"status":"ok"}` |

En Swagger se puede probar cada endpoint: abrir uno, **Try it out**, completar los datos y
**Execute**. Por ejemplo, `GET /reportes/prestamos-activos`.

Para el frontend, la URL base de la API es `http://localhost:8000`.

## 5. Correr los tests

```powershell
docker compose exec api pytest
```

Usan una base separada (`biblioteca_test`), así que no tocan los datos cargados.

## Comandos del día a día

| Para | Comando |
|---|---|
| Levantar (sin reconstruir) | `docker compose up -d` |
| Detener (los datos se conservan) | `docker compose down` |
| Ver qué está corriendo | `docker compose ps` |
| Ver los logs de la API en vivo (`Ctrl + C` para salir) | `docker compose logs -f api` |
| Actualizar después de un `git pull` | `docker compose up --build -d` |
| Borrar la base y empezar de cero | `docker compose down -v` y después levantar y cargar el seed de nuevo |
| Abrir una consola de la base | `docker compose exec db psql -U biblioteca` (salir con `\q`) |

Después de un `git pull` siempre conviene usar `--build`: si cambió el código o las librerías, la
imagen se reconstruye, y si hay migraciones nuevas se aplican solas al arrancar.

## Conectarse a la base con un cliente gráfico (opcional)

Con DBeaver, pgAdmin o la extensión de VS Code:

| Campo | Valor |
|---|---|
| Host | `localhost` |
| Puerto | `5432` (o el configurado en `DB_PORT`) |
| Base | `biblioteca` |
| Usuario | `biblioteca` |
| Contraseña | `biblioteca` |

## Cambiar puertos

Si el puerto 8000 o el 5432 ya está en uso en la PC (por ejemplo, porque hay un PostgreSQL
instalado), crear un archivo `.env` en la carpeta del proyecto copiando el ejemplo:

```powershell
Copy-Item .env.example .env
```

Y cambiar los valores que hagan falta:

```
API_PORT=8001
DB_PORT=5433
```

Después, `docker compose up -d`. La API queda en `http://localhost:8001`.

En ese mismo archivo se puede ajustar `CORS_ORIGENES` si el frontend corre en un puerto que no
está en la lista por defecto (3000, 5173 y 4200).

## Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| `error during connect` / `cannot find the file specified ... dockerDesktopLinuxEngine` | Docker Desktop no está abierto o todavía está arrancando. Abrirlo y esperar a que diga *Engine running*. |
| `Bind for 0.0.0.0:5432 failed: port is already allocated` (o 8000) | Otro programa usa ese puerto. Ver [Cambiar puertos](#cambiar-puertos). |
| La API se reinicia o no arranca y el log dice `exec docker/entrypoint.sh: no such file or directory` o `\r: not found` | El script quedó con finales de línea de Windows. El repo ya lo evita con `.gitattributes`; si se clonó antes de ese cambio, ejecutar `git rm --cached -r .`, `git reset --hard` y volver a levantar con `--build`. |
| `GET` a la API desde el frontend falla con un error de CORS en la consola del navegador | El puerto del frontend no está habilitado. Agregarlo en `CORS_ORIGENES` (ver [Cambiar puertos](#cambiar-puertos)) y reiniciar con `docker compose up -d`. |
| El seed dice "La base ya tiene datos" | Es normal si ya se cargó. Para empezar de cero: `docker compose down -v`, `docker compose up -d` y el seed de nuevo. |
| Cambié código y no se ve el cambio | La API corre desde la imagen construida. Volver a levantar con `docker compose up --build -d`. |

Para ver el detalle de cualquier error: `docker compose logs api` o `docker compose logs db`.

## Sin Docker

También se puede correr con Python y un PostgreSQL instalados en la PC. Los pasos están en el
[README](../README.md#sin-docker).
