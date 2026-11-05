# Despliegue local

Paso a paso para levantar el sistema completo (base de datos, API y frontend) en una PC con Docker. Si Docker
todavía no está instalado, seguir antes [instalar-docker-windows.md](instalar-docker-windows.md).

Los comandos son para **PowerShell** en Windows; en Linux o Mac son los mismos.

## Resumen rápido

Para quien ya lo hizo alguna vez:

```powershell
git clone https://github.com/tobiasceruttigothe/TP-DAO.git
cd TP-DAO
docker compose up --build -d
docker compose exec api python -m app.seed
# abrir http://localhost:3000 (admin@example.com / admin123)
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

- `--build` construye las imágenes de la API y del frontend (la primera vez tarda unos minutos
  porque descarga Python, Node y las librerías; las siguientes es mucho más rápido).
- `-d` lo deja corriendo en segundo plano y devuelve la consola.
- Levanta cinco contenedores: `db` (PostgreSQL), `api` (el backend), `web` (el frontend),
  `mailpit` (buzón de prueba para los correos) y `pgadmin` (para ver la base). La API espera a que la base esté lista y, al arrancar, crea o
  actualiza las tablas solas (migraciones).

Verificar que estén corriendo:

```powershell
docker compose ps
```

Los cinco servicios tienen que figurar como `running` (la base, además, `healthy`).

## 3. Cargar datos de ejemplo

```powershell
docker compose exec api python -m app.seed
```

Carga sedes, socios, libros, ejemplares y un escenario con préstamos, envíos, incidencias,
reservas, pedidos y un inventario cerrado, para que todas las pantallas y reportes tengan algo
que mostrar. Si la base ya tiene datos, no hace nada.

Cada socio de ejemplo tiene su cuenta lista para usar, como si ya hubiera confirmado el email y
lo hubieran aprobado. Sus emails son inventados (`@example.com`) y no se les manda ningún correo.
Hay además una cuenta (Florencia Ruiz) esperando aprobación, para probar esa pantalla.

## 4. Probar que funciona

| Qué | Dónde |
|---|---|
| **Catálogo público** (sin login) | http://localhost:3000 |
| Ingresar (administrador o socio) | http://localhost:3000/ingresar |
| Panel del administrador | http://localhost:3000/panel |
| **Mailpit** (los correos que manda el sistema) | http://localhost:8025 |
| pgAdmin (ver la base de datos) | http://localhost:5050 |
| Documentación interactiva de la API (Swagger) | http://localhost:8000/docs |
| Documentación alternativa (ReDoc) | http://localhost:8000/redoc |
| Chequeo rápido | http://localhost:8000/health → `{"status":"ok"}` |

En Swagger se puede probar cada endpoint: abrir uno, **Try it out**, completar los datos y
**Execute**. Por ejemplo, `GET /reportes/prestamos-activos`.

### Usuarios para probar

| Quién | Email | Contraseña |
|---|---|---|
| Administrador | `admin@example.com` | `admin123` |
| Socia con historial y pedidos | `lucia.fernandez@example.com` | `socio123` |
| Socio con un préstamo vencido | `tomas.martinez@example.com` | `socio123` |
| Socio inhabilitado por atraso | `diego.acosta@example.com` | `socio123` |
| Socio con una reserva lista para retirar | `nicolas.romero@example.com` | `socio123` |

Todos los socios de ejemplo usan `socio123`; el email de cada uno se ve en el panel, en
**Socios**. El administrador se puede cambiar con `ADMIN_EMAIL` y `ADMIN_CONTRASENA` en `.env`
antes de levantar por primera vez (si ya existe un administrador, no se crea otro).

### Probar el registro de un socio

1. En http://localhost:3000, **Hacerme socio** y completar los datos con cualquier email.
2. Abrir http://localhost:8025: llegó el correo **Confirmá tu email**. Abrirlo y tocar el botón.
3. Ingresar como administrador: la campana muestra **Nuevo socio para aprobar**. En
   **Usuarios** → **Por aprobar**, aprobarlo.
4. En Mailpit llega **Tu cuenta fue aprobada**. Ya se puede ingresar con esa cuenta.

Mailpit no reenvía nada: todo queda en esa bandeja, sea cual sea el email. Para que los correos
lleguen de verdad, ver [Mandar correos reales con Gmail](#mandar-correos-reales-con-gmail).

Para trabajar en el código del frontend con recarga automática, ver
[frontend/README.md](../frontend/README.md).

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
| Reconstruir solo el frontend | `docker compose up --build -d web` |
| Actualizar después de un `git pull` | ver [Actualizar a una versión nueva](#actualizar-a-una-versión-nueva) |
| Borrar la base y empezar de cero | `docker compose down -v` y después levantar y cargar el seed de nuevo |
| Vaciar la bandeja de Mailpit | Botón **Delete all** en http://localhost:8025 |
| Abrir una consola de la base | `docker compose exec db psql -U biblioteca` (salir con `\q`) |

## Actualizar a una versión nueva

Cada vez que se baja código nuevo con `git pull`, los contenedores siguen corriendo la versión
vieja hasta que se reconstruyen. Desde la carpeta del proyecto:

```powershell
git pull
docker compose down
docker compose up --build -d
```

- `down` detiene y borra los contenedores viejos. **Los datos de la base se conservan**, porque
  viven en un volumen aparte.
- `up --build` reconstruye las imágenes con el código nuevo. Si hay migraciones nuevas, la API
  las aplica sola al arrancar.

Si además se quiere **empezar con la base limpia** (por ejemplo, porque cambiaron los datos de
ejemplo o la base quedó con datos de prueba rotos), agregar `-v`, que también borra el volumen de
la base, y volver a cargar el seed:

```powershell
docker compose down -v
docker compose up --build -d
docker compose exec api python -m app.seed
```

> `-v` borra **todos** los datos cargados. Usarlo solo si no hay nada que conservar.

> **Al pasar a la versión con usuarios** conviene empezar con la base limpia. Si se conserva
> una base cargada antes, las tablas nuevas se crean igual y se crea el administrador, pero los
> socios de ejemplo no tienen cuenta (el seed no vuelve a correr sobre una base con datos).

Si después de actualizar algo se ve raro (por ejemplo, una pantalla vieja), forzar una
reconstrucción completa con `docker compose build --no-cache` y luego `docker compose up -d`. En el
navegador, `Ctrl + F5` recarga la página sin la caché.

## Ver y editar la base de datos

### Con pgAdmin (incluido)

El `docker compose` levanta también **pgAdmin**, un administrador de PostgreSQL que se usa desde
el navegador:

1. Abrir http://localhost:5050 (la primera vez tarda unos segundos en cargar).
2. En el panel izquierdo, desplegar **Servers → Biblioteca**. La conexión ya viene configurada.
3. Cuando pida la contraseña, poner `biblioteca` (se puede tildar *Save password*).
4. Las tablas están en **Databases → biblioteca → Schemas → public → Tables**. Clic derecho
   sobre una tabla → **View/Edit Data** para ver o editar filas, o **Tools → Query Tool** para
   escribir SQL.

> **Cuidado al editar datos a mano.** Lo que se cambia directo en la base se saltea todas las
> validaciones del sistema: se puede prestar un ejemplar ya prestado, cambiar el estado de un
> remito sin dejar trazabilidad o dejar datos inconsistentes que rompen los reportes. Para cargar
> datos conviene usar el sistema o Swagger (http://localhost:8000/docs); la base directa sirve
> para consultar o corregir algo puntual.

### Por consola

```powershell
docker compose exec db psql -U biblioteca
```

Por ejemplo `SELECT * FROM socios;`. Se sale con `\q`.

### Con otro programa

Con DBeaver o la extensión de PostgreSQL de VS Code:

| Campo | Valor |
|---|---|
| Host | `localhost` |
| Puerto | `5432` (o el configurado en `DB_PORT`) |
| Base | `biblioteca` |
| Usuario | `biblioteca` |
| Contraseña | `biblioteca` |

Dentro de pgAdmin el host es `db` (el nombre del contenedor), no `localhost`.

## Cambiar puertos

Si el puerto 3000, 8000 o 5432 ya está en uso en la PC (por ejemplo, porque hay un PostgreSQL
instalado), crear un archivo `.env` en la carpeta del proyecto copiando el ejemplo:

```powershell
Copy-Item .env.example .env
```

Y cambiar los valores que hagan falta:

```
API_PORT=8001
DB_PORT=5433
WEB_PORT=3001
CORS_ORIGENES=http://localhost:3001,http://localhost:5173
```

Después, `docker compose up --build -d` (con `--build`, porque el frontend guarda la dirección de
la API al compilarse). El sistema queda en `http://localhost:3001` y la API en
`http://localhost:8001`.

Si se cambia `WEB_PORT`, hay que agregar ese puerto a `CORS_ORIGENES`: si no, el navegador bloquea
las llamadas del frontend a la API. También cambiar `URL_FRONTEND` (por ejemplo,
`http://localhost:3001`), que es la dirección de los enlaces de los correos.

## Mandar correos reales con Gmail

Por defecto los correos van a Mailpit. Para la demostración se pueden mandar desde una cuenta de
Gmail. Gmail no acepta la contraseña normal de la cuenta: hay que crear una **contraseña de
aplicación**.

1. En la cuenta de Google, activar la **verificación en dos pasos** (es requisito).
2. Entrar a https://myaccount.google.com/apppasswords, escribir un nombre (por ejemplo,
   "Biblioteca") y **Crear**. Google muestra una contraseña de 16 letras: copiarla (no se vuelve
   a mostrar).
3. Crear el `.env` (`Copy-Item .env.example .env`) y completar, sin espacios en la contraseña:

   ```
   SMTP_HOST=smtp.gmail.com
   SMTP_PUERTO=587
   SMTP_TLS=true
   SMTP_USUARIO=tu.cuenta@gmail.com
   SMTP_CONTRASENA=abcdefghijklmnop
   CORREO_REMITENTE=Red de Bibliotecas <tu.cuenta@gmail.com>
   ```

4. `docker compose up -d` (no hace falta `--build`: son variables de la API).
5. Registrar un socio con un email real y seguir los pasos de
   [Probar el registro de un socio](#probar-el-registro-de-un-socio): el correo llega a esa
   casilla (revisar también *Spam* la primera vez).

Los avisos para el administrador van al email del administrador. El de ejemplo
(`admin@example.com`) no existe, así que esos correos rebotan y Gmail avisa del rebote en la
cuenta que envía. Para recibirlos, crear en **Usuarios** → **Nuevo administrador** uno con un
email real (o poner `ADMIN_EMAIL` real antes de levantar la base por primera vez).

> El `.env` tiene la contraseña de aplicación: **no subirlo a GitHub** (ya está en
> `.gitignore`). Si se filtra, borrarla desde la misma página de Google.

Para volver a Mailpit, borrar esas líneas del `.env` y `docker compose up -d`.

## Problemas frecuentes

| Síntoma | Causa y solución |
|---|---|
| `error during connect` / `cannot find the file specified ... dockerDesktopLinuxEngine` | Docker Desktop no está abierto o todavía está arrancando. Abrirlo y esperar a que diga *Engine running*. |
| `Bind for 0.0.0.0:5432 failed: port is already allocated` (o 8000) | Otro programa usa ese puerto. Ver [Cambiar puertos](#cambiar-puertos). |
| La API se reinicia o no arranca y el log dice `exec docker/entrypoint.sh: no such file or directory` o `\r: not found` | El script quedó con finales de línea de Windows. El repo ya lo evita con `.gitattributes`; si se clonó antes de ese cambio, ejecutar `git rm --cached -r .`, `git reset --hard` y volver a levantar con `--build`. |
| El frontend carga pero todas las pantallas dicen "No se pudo conectar con el servidor" | La API no está corriendo (`docker compose ps`), o el puerto del frontend no está en `CORS_ORIGENES` (en la consola del navegador, `F12`, aparece un error de CORS). Ver [Cambiar puertos](#cambiar-puertos). |
| No llegan los correos a Gmail | `docker compose logs api` muestra el error. `Username and Password not accepted`: la contraseña no es la de aplicación o tiene espacios. Si no hay error, revisar *Spam*. |
| El enlace del correo abre una página que no carga | `URL_FRONTEND` no coincide con la dirección del frontend (por ejemplo, se cambió `WEB_PORT`). |
| "Tu cuenta está esperando la aprobación" | Un administrador tiene que aprobarla en **Usuarios** → **Por aprobar**. |
| El seed dice "La base ya tiene datos" | Es normal si ya se cargó. Para empezar de cero: `docker compose down -v`, `docker compose up -d` y el seed de nuevo. |
| Cambié código y no se ve el cambio | La API corre desde la imagen construida. Volver a levantar con `docker compose up --build -d`. |

Para ver el detalle de cualquier error: `docker compose logs api` o `docker compose logs db`.

## Sin Docker

También se puede correr con Python y un PostgreSQL instalados en la PC. Los pasos están en el
[README](../README.md#sin-docker).
