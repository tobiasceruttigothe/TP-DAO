import { Suspense } from 'react'
import { Link, Outlet } from 'react-router-dom'
import { Layout, Spin, Typography } from 'antd'
import { BookOutlined } from '@ant-design/icons'

export default function ConsultaLayout() {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Header style={{ background: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <Typography.Title level={4} style={{ margin: 0 }}>
          <BookOutlined /> Red de Bibliotecas
        </Typography.Title>
        <Link to="/">Acceso personal</Link>
      </Layout.Header>
      <Layout.Content style={{ padding: 24, maxWidth: 1000, width: '100%', margin: '0 auto' }}>
        <Suspense fallback={<Spin style={{ display: 'block', marginTop: 80 }} />}>
          <Outlet />
        </Suspense>
      </Layout.Content>
    </Layout>
  )
}
