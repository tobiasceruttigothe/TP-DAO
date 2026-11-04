import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import { Button, Result, Spin } from 'antd'
import RutaProtegida from './sesion/RutaProtegida'

const PanelLayout = lazy(() => import('./layouts/PanelLayout'))
const SitioLayout = lazy(() => import('./layouts/SitioLayout'))

// Panel del administrador
const Inicio = lazy(() => import('./paginas/panel/Inicio'))
const Sedes = lazy(() => import('./paginas/panel/Sedes'))
const Socios = lazy(() => import('./paginas/panel/Socios'))
const Libros = lazy(() => import('./paginas/panel/Libros'))
const LibroDetalle = lazy(() => import('./paginas/panel/LibroDetalle'))
const Prestamos = lazy(() => import('./paginas/panel/Prestamos'))
const NuevoPrestamo = lazy(() => import('./paginas/panel/NuevoPrestamo'))
const Remitos = lazy(() => import('./paginas/panel/Remitos'))
const RemitoDetalle = lazy(() => import('./paginas/panel/RemitoDetalle'))
const Reservas = lazy(() => import('./paginas/panel/Reservas'))
const Incidencias = lazy(() => import('./paginas/panel/Incidencias'))
const Reportes = lazy(() => import('./paginas/panel/Reportes'))
const Pedidos = lazy(() => import('./paginas/panel/Pedidos'))
const Usuarios = lazy(() => import('./paginas/panel/Usuarios'))
const Inventarios = lazy(() => import('./paginas/panel/Inventarios'))
const InventarioDetalle = lazy(() => import('./paginas/panel/InventarioDetalle'))
const Etiquetas = lazy(() => import('./paginas/panel/Etiquetas'))

// Sitio publico
const Catalogo = lazy(() => import('./paginas/publico/Catalogo'))
const Ingresar = lazy(() => import('./paginas/publico/Ingresar'))
const Registro = lazy(() => import('./paginas/publico/Registro'))
const Confirmar = lazy(() => import('./paginas/publico/Confirmar'))

// Area del socio
const MisPrestamos = lazy(() => import('./paginas/socio/MisPrestamos'))
const MisPedidos = lazy(() => import('./paginas/socio/MisPedidos'))
const Historial = lazy(() => import('./paginas/socio/Historial'))
const Notificaciones = lazy(() => import('./paginas/compartido/Notificaciones'))

function NoEncontrada() {
  return <Result status="404" title="Página no encontrada" extra={<Button href="/">Volver al inicio</Button>} />
}

function Cargando() {
  return <Spin size="large" style={{ display: 'block', margin: '20vh auto' }} />
}

export default function App() {
  return (
    <Suspense fallback={<Cargando />}>
      <Routes>
        <Route element={<SitioLayout />}>
          <Route index element={<Catalogo />} />
          <Route path="ingresar" element={<Ingresar />} />
          <Route path="registro" element={<Registro />} />
          <Route path="confirmar" element={<Confirmar />} />
          <Route path="consulta" element={<Navigate to="/" replace />} />
          <Route path="socio" element={<RutaProtegida rol="SOCIO" />}>
            <Route index element={<MisPrestamos />} />
            <Route path="pedidos" element={<MisPedidos />} />
            <Route path="historial" element={<Historial />} />
            <Route path="notificaciones" element={<Notificaciones />} />
          </Route>
        </Route>

        <Route path="panel" element={<RutaProtegida rol="ADMIN" />}>
          <Route element={<PanelLayout />}>
            <Route index element={<Inicio />} />
            <Route path="pedidos" element={<Pedidos />} />
            <Route path="sedes" element={<Sedes />} />
            <Route path="socios" element={<Socios />} />
            <Route path="usuarios" element={<Usuarios />} />
            <Route path="libros" element={<Libros />} />
            <Route path="libros/:id" element={<LibroDetalle />} />
            <Route path="prestamos" element={<Prestamos />} />
            <Route path="prestamos/nuevo" element={<NuevoPrestamo />} />
            <Route path="remitos" element={<Remitos />} />
            <Route path="remitos/:id" element={<RemitoDetalle />} />
            <Route path="reservas" element={<Reservas />} />
            <Route path="inventarios" element={<Inventarios />} />
            <Route path="inventarios/:id" element={<InventarioDetalle />} />
            <Route path="etiquetas" element={<Etiquetas />} />
            <Route path="incidencias" element={<Incidencias />} />
            <Route path="reportes" element={<Reportes />} />
            <Route path="notificaciones" element={<Notificaciones />} />
          </Route>
        </Route>

        <Route path="*" element={<NoEncontrada />} />
      </Routes>
    </Suspense>
  )
}
