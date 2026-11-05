import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { Spin } from 'antd'
import useSesion, { inicioDe } from './useSesion'

/** Deja pasar solo a usuarios conectados con el rol pedido; al resto los manda a ingresar. */
export default function RutaProtegida({ rol }) {
  const { usuario, cargando } = useSesion()
  const { pathname, search } = useLocation()

  if (cargando) return <Spin size="large" style={{ display: 'block', margin: '20vh auto' }} />
  if (!usuario) return <Navigate to={`/ingresar?volver=${encodeURIComponent(pathname + search)}`} replace />
  if (usuario.rol !== rol) return <Navigate to={inicioDe(usuario)} replace />
  return <Outlet />
}
