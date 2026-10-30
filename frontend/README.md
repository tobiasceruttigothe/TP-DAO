# Frontend

Interfaz web del sistema, hecha con **React 18 + Vite** y **Ant Design 5**. Consume la API del
backend (ver el [README principal](../README.md)).

Tiene dos partes:

- **Panel del personal** (`/`): préstamos, remitos, reservas, catálogo, socios, sedes,
  incidencias y reportes.
- **Consulta para socios** (`/consulta`): sin login. Buscar libros y ver en qué sedes hay
  ejemplares libres, y consultar préstamos, vencimientos y reservas ingresando el DNI.

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
  componentes/  piezas reutilizables: etiquetas de estado, selectores con búsqueda, encabezado
  hooks/        useListado (tablas paginadas), useCarga (cargar datos), useAccion (operaciones)
  layouts/      marco del panel (menú lateral) y de la consulta pública
  paginas/
    panel/      una pantalla por sección del menú
    consulta/   consulta para socios
  utiles/       textos y colores de cada estado, formato de fechas y moneda
```

## Convenciones

- Nombres en español, igual que el backend. Componentes en PascalCase, un archivo por pantalla.
- Toda llamada a la API pasa por `src/api/`. Los errores llegan como `Error` con el mensaje que
  devuelve el backend, y se muestran con `useAccion` o `useListado`.
- Los estados (`ACTIVO`, `DESPACHADO`, ...) se muestran siempre con `<EstadoTag>`, que toma el
  texto y el color de `utiles/estados.js`. Si el backend agrega un estado, se agrega ahí.
- Las funciones que se pasan a `useListado` o `useCarga` tienen que ser estables (definidas
  fuera del componente o con `useCallback`); si no, la tabla se recarga en cada render.
- Los formularios dentro de un modal usan `forceRender` y se reinician con `form.resetFields()`
  al abrirse, para que no queden datos de la vez anterior.
- Las reglas de negocio las valida el backend. El front solo valida formato (campos
  obligatorios, email, DNI numérico) y muestra el mensaje de error que devuelve la API.
