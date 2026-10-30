# Instalar Docker en Windows

Guía para instalar **Docker Desktop** en Windows 10 u 11. Se hace una sola vez por PC y lleva
entre 15 y 30 minutos, contando los reinicios. Después de esto, seguir con
[despliegue-local.md](despliegue-local.md).

> Los requisitos exactos (versión mínima de Windows, etc.) cambian con cada versión de Docker
> Desktop. Ante cualquier duda, la referencia es la página oficial:
> https://docs.docker.com/desktop/setup/install/windows-install/

## Qué se va a instalar

- **WSL 2** (Subsistema de Windows para Linux): permite correr Linux dentro de Windows. Docker lo
  usa para ejecutar los contenedores.
- **Docker Desktop**: el programa que administra los contenedores. Trae los comandos `docker` y
  `docker compose`.
- **Git**, si no está instalado, para descargar el repositorio.

## Requisitos

- Windows 10 u 11 de 64 bits, **actualizado** (Windows Update al día). Sirve la edición Home.
- Al menos 8 GB de RAM recomendados (con 4 GB funciona, pero lento).
- Unos 10 GB libres en disco.
- La **virtualización habilitada** en la PC. Se verifica en el paso 1.
- Usuario con permisos de administrador.

## Paso 1: verificar que la virtualización esté habilitada

1. Abrir el **Administrador de tareas** (`Ctrl + Shift + Esc`).
2. Ir a la pestaña **Rendimiento** → **CPU**.
3. Abajo a la derecha tiene que decir **Virtualización: Habilitado**.

Si dice **Deshabilitado**, hay que activarla en la BIOS/UEFI de la PC:

1. Reiniciar y entrar a la BIOS. Según la marca, se entra apretando `F2`, `F10`, `Supr` o `Esc`
   al encender.
2. Buscar la opción **Intel Virtualization Technology (VT-x)**, **Intel VT** o, en procesadores
   AMD, **SVM Mode** / **AMD-V**. Suele estar en *Advanced*, *CPU Configuration* o *Security*.
3. Pasarla a **Enabled**, guardar y salir (generalmente `F10`).

Si no se encuentra, buscar en internet "habilitar virtualización" más el modelo exacto de la PC
o del motherboard.

## Paso 2: instalar WSL 2

1. Abrir **PowerShell como administrador**: menú Inicio → escribir `PowerShell` → clic derecho →
   **Ejecutar como administrador**.
2. Ejecutar:

   ```powershell
   wsl --install
   ```

3. **Reiniciar la PC** cuando termine.
4. Al volver, puede abrirse sola una ventana que pide crear un usuario y contraseña de Linux
   (Ubuntu). Se puede completar con cualquier dato o cerrarla: Docker no lo necesita.
5. Verificar en PowerShell (no hace falta que sea como administrador):

   ```powershell
   wsl --status
   ```

   Tiene que indicar que la versión predeterminada es la **2**.

Si WSL ya estaba instalado de antes, actualizarlo con:

```powershell
wsl --update
```

## Paso 3: instalar Docker Desktop

1. Descargar el instalador desde https://www.docker.com/products/docker-desktop/ → **Download for
   Windows**. El archivo se llama `Docker Desktop Installer.exe`.
2. Ejecutarlo. En la pantalla de configuración, dejar marcada la opción **Use WSL 2 instead of
   Hyper-V** (puede no aparecer si la PC no soporta Hyper-V; en ese caso usa WSL 2 directamente).
3. Esperar a que termine. Si pide **cerrar sesión o reiniciar**, hacerlo.
4. Abrir **Docker Desktop** desde el menú Inicio.
5. Aceptar el acuerdo de licencia. Docker Desktop es gratuito para uso personal y educativo.
6. Si pide iniciar sesión o crear una cuenta, se puede **omitir** (*Skip* / *Continue without
   signing in*). Lo mismo con las encuestas.
7. Esperar a que el ícono de la ballena en la barra de tareas deje de moverse y Docker Desktop
   muestre **Engine running** abajo a la izquierda.

## Paso 4: verificar la instalación

En PowerShell (uno normal):

```powershell
docker --version
docker compose version
docker run hello-world
```

Los dos primeros muestran las versiones instaladas. El último descarga una imagen de prueba y
tiene que imprimir un mensaje que empieza con **Hello from Docker!**. Si eso aparece, Docker
funciona.

## Paso 5: instalar Git (si no lo tienen)

```powershell
git --version
```

Si da error, descargarlo de https://git-scm.com/download/win e instalarlo con las opciones por
defecto. Cerrar y volver a abrir PowerShell después de instalarlo.

## Uso diario

- **Docker Desktop tiene que estar abierto** para usar los comandos `docker`. Si un comando falla
  con un error que menciona `pipe/dockerDesktopLinuxEngine` o "cannot connect to the Docker
  daemon", es porque Docker Desktop está cerrado o todavía está arrancando.
- Para que arranque solo: Docker Desktop → **Settings** → **General** → *Start Docker Desktop when
  you sign in to your computer*.
- Docker consume bastante memoria. Cuando no se usa, se puede cerrar desde el ícono de la
  ballena → **Quit Docker Desktop**.

## Problemas frecuentes

| Problema | Solución |
|---|---|
| "Virtualization support not detected" o "WSL 2 installation is incomplete" | Revisar el paso 1 (virtualización en la BIOS) y ejecutar `wsl --update` en PowerShell como administrador. Reiniciar. |
| Docker Desktop queda en *Starting...* para siempre | Cerrarlo, ejecutar `wsl --shutdown` en PowerShell y volver a abrirlo. Si sigue, reiniciar la PC. |
| `wsl --install` muestra la ayuda en lugar de instalar | WSL ya está instalado. Ejecutar `wsl --update` y `wsl --set-default-version 2`. |
| La PC queda muy lenta con Docker abierto | Cerrar Docker Desktop cuando no se use. También se puede limitar la memoria de WSL creando el archivo `C:\Users\<usuario>\.wslconfig` con las líneas `[wsl2]` y `memory=3GB`, y después ejecutar `wsl --shutdown`. |
| Error de permisos al ejecutar `docker` | Cerrar sesión de Windows y volver a entrar (el instalador agrega el usuario al grupo `docker-users`). |
