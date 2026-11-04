import { useNavigate } from 'react-router-dom'
import { Button, Dropdown } from 'antd'
import { LogoutOutlined, UserOutlined } from '@ant-design/icons'
import useSesion from '../sesion/useSesion'

export default function MenuUsuario() {
  const { usuario, salir } = useSesion()
  const navegar = useNavigate()

  return (
    <Dropdown
      menu={{
        items: [
          { key: 'email', label: usuario.email, disabled: true },
          { type: 'divider' },
          { key: 'salir', icon: <LogoutOutlined />, label: 'Cerrar sesión' },
        ],
        onClick: ({ key }) => {
          if (key === 'salir') {
            salir()
            navegar('/')
          }
        },
      }}
    >
      <Button type="text" icon={<UserOutlined />}>
        {usuario.nombre}
      </Button>
    </Dropdown>
  )
}
