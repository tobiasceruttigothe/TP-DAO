import { Suspense, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Button, Layout, Menu, Spin, Typography } from 'antd'
import {
  AlertOutlined,
  BarChartOutlined,
  BookOutlined,
  CarOutlined,
  ClockCircleOutlined,
  HomeOutlined,
  SearchOutlined,
  ShopOutlined,
  SwapOutlined,
  TeamOutlined,
} from '@ant-design/icons'

const SECCIONES = [
  { key: '/', icon: <HomeOutlined />, label: 'Inicio' },
  { key: '/prestamos', icon: <SwapOutlined />, label: 'Préstamos' },
  { key: '/remitos', icon: <CarOutlined />, label: 'Remitos' },
  { key: '/reservas', icon: <ClockCircleOutlined />, label: 'Reservas' },
  { key: '/libros', icon: <BookOutlined />, label: 'Catálogo' },
  { key: '/socios', icon: <TeamOutlined />, label: 'Socios' },
  { key: '/sedes', icon: <ShopOutlined />, label: 'Sedes' },
  { key: '/incidencias', icon: <AlertOutlined />, label: 'Incidencias' },
  { key: '/reportes', icon: <BarChartOutlined />, label: 'Reportes' },
]

function seccionActual(ruta) {
  if (ruta === '/') return '/'
  return SECCIONES.find((s) => s.key !== '/' && ruta.startsWith(s.key))?.key ?? '/'
}

export default function PanelLayout() {
  const navegar = useNavigate()
  const { pathname } = useLocation()
  const [colapsado, setColapsado] = useState(false)

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Sider breakpoint="lg" collapsible collapsed={colapsado} onCollapse={setColapsado} theme="light">
        <Typography.Title level={5} style={{ padding: '20px 16px 8px', margin: 0, whiteSpace: 'nowrap', overflow: 'hidden' }}>
          <BookOutlined /> {!colapsado && 'Red de Bibliotecas'}
        </Typography.Title>
        <Menu mode="inline" selectedKeys={[seccionActual(pathname)]} items={SECCIONES} onClick={({ key }) => navegar(key)} />
      </Layout.Sider>
      <Layout>
        <Layout.Header
          style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'flex-end', alignItems: 'center' }}
        >
          <Button icon={<SearchOutlined />} onClick={() => navegar('/consulta')}>
            Consulta para socios
          </Button>
        </Layout.Header>
        <Layout.Content style={{ margin: 24 }}>
          <Suspense fallback={<Spin style={{ display: 'block', marginTop: 80 }} />}>
            <Outlet />
          </Suspense>
        </Layout.Content>
      </Layout>
    </Layout>
  )
}
