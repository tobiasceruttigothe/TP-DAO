import { lazy, Suspense } from 'react'
import { Route, Routes } from 'react-router-dom'
import { Button, Result, Spin } from 'antd'
import PanelLayout from './layouts/PanelLayout'
import ConsultaLayout from './layouts/ConsultaLayout'

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
const Consulta = lazy(() => import('./paginas/consulta/Consulta'))

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
        <Route element={<PanelLayout />}>
          <Route index element={<Inicio />} />
          <Route path="sedes" element={<Sedes />} />
          <Route path="socios" element={<Socios />} />
          <Route path="libros" element={<Libros />} />
          <Route path="libros/:id" element={<LibroDetalle />} />
          <Route path="prestamos" element={<Prestamos />} />
          <Route path="prestamos/nuevo" element={<NuevoPrestamo />} />
          <Route path="remitos" element={<Remitos />} />
          <Route path="remitos/:id" element={<RemitoDetalle />} />
          <Route path="reservas" element={<Reservas />} />
          <Route path="incidencias" element={<Incidencias />} />
          <Route path="reportes" element={<Reportes />} />
        </Route>
        <Route path="consulta" element={<ConsultaLayout />}>
          <Route index element={<Consulta />} />
        </Route>
        <Route path="*" element={<NoEncontrada />} />
      </Routes>
    </Suspense>
  )
}
