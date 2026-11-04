# Frontend

Interfaz web del sistema, hecha con **React 18 + Vite** y **Ant Design 5**. Consume la API del
backend (ver el [README principal](../README.md)).

Tiene tres partes:

- **Sitio público** (`/`): sin login. Catálogo con disponibilidad por sede, ingreso
  (`/ingresar`), registro de socios (`/registro`) y confirmación del email (`/confirmar`).
- **Área del socio** (`/socio`): sus préstamos y reservas, pedidos, historial de lectura y
  notificaciones. Pide libros desde el catálogo.
- **Panel del administrador** (`/panel`): pedidos, préstamos, remitos, reservas, catálogo,
  inventario, etiquetas con código de barras, socios, usuarios, sedes, incidencias y reportes.

Credenciales de prueba en [docs/despliegue-local.md](../docs/despliegue-local.md#usuarios-para-probar).

## Levantarlo

**Con Docker** (junto con la API y la base): desde la raíz del repo, `docker compose up --build -d`.
Queda en http://localhost:3000.

**Para desarrollar** (recarga automática al guardar): necesita Node 20 o superior y la API
corriendo en http://localhost:8000.

```bash
cd frontend
npm install
npm run dev
```

Queda en http://localhost:5173. Si la API está en otra URL, crear `frontend/.env` a partir de
`.env.example` y cambiar `VITE_API_URL`.

| Comando | Para qué |
|---|---|
| `npm run dev` | Servidor de desarrollo |
| `npm run lint` | Revisar el código con ESLint |
| `npm run build` | Compilar para producción (carpeta `dist/`) |

## Estructura

```
src/
  api/          llamadas a la API (cliente.js configura axios; index.js agrupa por recurso)
  componentes/  piezas reutilizables: etiquetas de estado, buscador, selectores, encabezado
  hooks/        useListado (tablas paginadas), useCarga (cargar datos), useAccion (operaciones)
  layouts/      marco del panel (menú lateral) y del sitio público / área del socio
  paginas/
    panel/      una pantalla por sección del menú del administrador
    publico/    catálogo, ingreso, registro, confirmación del email
    socio/      préstamos, pedidos e historial del socio
    compartido/ pantallas de los dos roles (notificaciones)
  sesion/       usuario conectado (ProveedorSesion, useSesion) y RutaProtegida por rol
  utiles/       textos y colores de cada estado, formatos, reglas de validación
```

## Convenciones

- Nombres en español, igual que el backend. Componentes en PascalCase, un archivo por pantalla.
- La sesión vive en `src/sesion/`. El token se guarda en `localStorage` y el cliente de axios lo
  agrega en cada llamada; si la API responde 401, la sesión se cierra. Las rutas de cada rol se
  envuelven con `<RutaProtegida rol="...">`, que es solo para la navegación: los permisos los
  controla la API.
- Toda llamada a la API pasa por `src/api/`. Los errores llegan como `Error` con el mensaje que
  devuelve el backend, y se muestran con `useAccion` o `useListado`.
- Los estados (`ACTIVO`, `DESPACHADO`, ...) se muestran siempre con `<EstadoTag>`, que toma el
  texto y el color de `utiles/estados.js`. Si el backend agrega un estado, se agrega ahí.
- Las funciones que se pasan a `useListado` o `useCarga` tienen que ser estables (definidas
  fuera del componente o con `useCallback`); si no, la tabla se recarga en cada render.
- Los formularios dentro de un modal usan `forceRender` y se reinician con `form.resetFields()`
  al abrirse, para que no queden datos de la vez anterior.
- Las reglas de los campos (DNI, nombre, teléfono, ISBN...) están en `utiles/reglas.js` y son las
  mismas que valida la API. Para validar un formulario usar `validar(form)`, que devuelve `null`
  si hay errores en lugar de lanzar una excepción.
- Las búsquedas por texto usan `<Buscador>`, que busca mientras se escribe.
- Las reglas de negocio las valida el backend. El front solo valida formato (campos
  obligatorios, email, DNI numérico) y muestra el mensaje de error que devuelve la API.
