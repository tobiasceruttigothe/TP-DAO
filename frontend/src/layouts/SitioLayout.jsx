import { Suspense } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Button, Flex, Layout, Menu, Spin, Typography } from 'antd'
import { BookOutlined, SettingOutlined } from '@ant-design/icons'
import useSesion from '../sesion/useSesion'
import CampanaNotificaciones from '../componentes/CampanaNotificaciones'
import MenuUsuario from '../componentes/MenuUsuario'

const SECCIONES_SOCIO = [
  { key: '/', label: 'Catálogo' },
  { key: '/socio', label: 'Mis préstamos' },
  { key: '/socio/pedidos', label: 'Mis pedidos' },
  { key: '/socio/historial', label: 'Historial de lectura' },
  { key: '/socio/notificaciones', label: 'Notificaciones' },
]

/** Marco del sitio publico (catalogo, ingreso, registro) y del area del socio. */
export default function SitioLayout() {
  const { usuario, esAdmin, esSocio } = useSesion()
  const { pathname } = useLocation()
  const navegar = useNavigate()

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Header style={{ background: '#fff', padding: '0 16px', height: 'auto', lineHeight: 'normal' }}>
        <Flex justify="space-between" align="center" wrap gap={8} style={{ minHeight: 64, maxWidth: 1100, margin: '0 auto' }}>
          <Link to="/">
            <Typography.Title level={4} style={{ margin: 0 }}>
              <BookOutlined /> Red de Bibliotecas
            </Typography.Title>
          </Link>
          <Flex gap={8} align="center" wrap>
            {!usuario && (
              <>
                <Button onClick={() => navegar('/ingresar')}>Ingresar</Button>
                <Button type="primary" onClick={() => navegar('/registro')}>
                  Hacerme socio
                </Button>
              </>
            )}
            {esAdmin && (
              <Button icon={<SettingOutlined />} onClick={() => navegar('/panel')}>
                Ir al panel
              </Button>
            )}
            {esSocio && <CampanaNotificaciones verTodas="/socio/notificaciones" />}
            {usuario && <MenuUsuario />}
          </Flex>
        </Flex>
        {esSocio && (
          <Menu
            mode="horizontal"
            selectedKeys={[pathname]}
            items={SECCIONES_SOCIO}
            onClick={({ key }) => navegar(key)}
            style={{ maxWidth: 1100, margin: '0 auto', borderBottom: 'none' }}
          />
        )}
      </Layout.Header>
      <Layout.Content style={{ padding: '24px 16px', maxWidth: 1100, width: '100%', margin: '0 auto' }}>
        <Suspense fallback={<Spin style={{ display: 'block', marginTop: 80 }} />}>
          <Outlet />
        </Suspense>
      </Layout.Content>
    </Layout>
  )
}
