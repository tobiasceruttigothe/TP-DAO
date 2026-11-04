import { Suspense, useState } from 'react'
import { Outlet, useLocation, useNavigate } from 'react-router-dom'
import { Button, Flex, Layout, Menu, Spin, Typography } from 'antd'
import {
  AlertOutlined,
  AuditOutlined,
  BarChartOutlined,
  BarcodeOutlined,
  BookOutlined,
  CarOutlined,
  ClockCircleOutlined,
  GlobalOutlined,
  HomeOutlined,
  InboxOutlined,
  ShopOutlined,
  SwapOutlined,
  TeamOutlined,
  UserOutlined,
} from '@ant-design/icons'
import CampanaNotificaciones from '../componentes/CampanaNotificaciones'
import MenuUsuario from '../componentes/MenuUsuario'

const SECCIONES = [
  { key: '/panel', icon: <HomeOutlined />, label: 'Inicio' },
  { key: '/panel/pedidos', icon: <InboxOutlined />, label: 'Pedidos' },
  { key: '/panel/prestamos', icon: <SwapOutlined />, label: 'Préstamos' },
  { key: '/panel/remitos', icon: <CarOutlined />, label: 'Remitos' },
  { key: '/panel/reservas', icon: <ClockCircleOutlined />, label: 'Reservas' },
  { key: '/panel/libros', icon: <BookOutlined />, label: 'Catálogo' },
  { key: '/panel/inventarios', icon: <AuditOutlined />, label: 'Inventario' },
  { key: '/panel/etiquetas', icon: <BarcodeOutlined />, label: 'Etiquetas' },
  { key: '/panel/socios', icon: <TeamOutlined />, label: 'Socios' },
  { key: '/panel/usuarios', icon: <UserOutlined />, label: 'Usuarios' },
  { key: '/panel/sedes', icon: <ShopOutlined />, label: 'Sedes' },
  { key: '/panel/incidencias', icon: <AlertOutlined />, label: 'Incidencias' },
  { key: '/panel/reportes', icon: <BarChartOutlined />, label: 'Reportes' },
]

function seccionActual(ruta) {
  const coincidencias = SECCIONES.filter((s) => ruta === s.key || ruta.startsWith(`${s.key}/`))
  // La mas especifica gana: /panel/pedidos antes que /panel
  return coincidencias.sort((a, b) => b.key.length - a.key.length)[0]?.key ?? '/panel'
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
          <Flex gap={8} align="center">
            <Button icon={<GlobalOutlined />} onClick={() => navegar('/')}>
              Sitio público
            </Button>
            <CampanaNotificaciones verTodas="/panel/notificaciones" />
            <MenuUsuario />
          </Flex>
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
