import { useState } from 'react'
import { Button, Form, Input, Modal, Popconfirm, Select, Space, Table, Tabs } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { usuariosApi } from '../../api'
import useListado from '../../hooks/useListado'
import useAccion from '../../hooks/useAccion'
import Buscador from '../../componentes/Buscador'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import { opcionesDe } from '../../utiles/estados'
import { fechaHora } from '../../utiles/formato'
import { reglasContrasena, reglasEmail, reglasNombre, reglasTexto, validar } from '../../utiles/reglas'

function TablaUsuarios({ filtros, conAcciones, onRechazar, accion }) {
  const { items, cargando, paginacion, recargar } = useListado(usuariosApi.listar, filtros)
  return (
    <Table
      rowKey="id"
      loading={cargando}
      dataSource={items}
      pagination={paginacion}
      scroll={{ x: true }}
      locale={{ emptyText: conAcciones ? 'No hay registros esperando aprobación' : 'Sin resultados' }}
      columns={[
        { title: 'Nombre', dataIndex: 'nombre' },
        { title: 'Email', dataIndex: 'email' },
        { title: 'DNI', render: (_, u) => u.socio?.dni ?? '-' },
        { title: 'Rol', dataIndex: 'rol', render: (v) => <EstadoTag tipo="rol" valor={v} /> },
        { title: 'Estado', dataIndex: 'estado', render: (v) => <EstadoTag tipo="usuario" valor={v} /> },
        { title: 'Alta', dataIndex: 'fecha_alta', render: fechaHora },
        ...(conAcciones
          ? [
              {
                title: '',
                key: 'acciones',
                render: (_, u) => (
                  <Space>
                    <Popconfirm title={`¿Aprobar la cuenta de ${u.nombre}?`} onConfirm={() => accion(() => usuariosApi.aprobar(u.id), 'Cuenta aprobada', recargar)}>
                      <a>Aprobar</a>
                    </Popconfirm>
                    <a onClick={() => onRechazar(u, recargar)}>Rechazar</a>
                  </Space>
                ),
              },
            ]
          : [{ title: 'Motivo de rechazo', dataIndex: 'motivo_rechazo', render: (v) => v ?? '-' }]),
      ]}
    />
  )
}

export default function Usuarios() {
  const [filtros, setFiltros] = useState({})
  const [rechazando, setRechazando] = useState(null)
  const [creandoAdmin, setCreandoAdmin] = useState(false)
  const [formRechazo] = Form.useForm()
  const [formAdmin] = Form.useForm()
  const [version, setVersion] = useState(0)
  const { ejecutar, ejecutando } = useAccion()

  async function accion(operacion, mensaje, recargar) {
    if (await ejecutar(operacion, mensaje)) recargar()
  }

  function abrirRechazo(usuario, recargar) {
    formRechazo.resetFields()
    setRechazando({ usuario, recargar })
  }

  async function rechazar() {
    const valores = await validar(formRechazo)
    if (!valores) return
    if (await ejecutar(() => usuariosApi.rechazar(rechazando.usuario.id, valores.motivo), 'Registro rechazado')) {
      rechazando.recargar()
      setRechazando(null)
    }
  }

  async function crearAdmin() {
    const valores = await validar(formAdmin)
    if (!valores) return
    if (await ejecutar(() => usuariosApi.crearAdministrador(valores), 'Administrador creado')) {
      setCreandoAdmin(false)
      setVersion((v) => v + 1)
    }
  }

  const cambiar = (campo) => (valor) => setFiltros((f) => ({ ...f, [campo]: valor }))

  return (
    <>
      <Encabezado titulo="Usuarios" descripcion="Cuentas de socios y administradores">
        <Button
          icon={<PlusOutlined />}
          onClick={() => {
            formAdmin.resetFields()
            setCreandoAdmin(true)
          }}
        >
          Nuevo administrador
        </Button>
      </Encabezado>
      <Tabs
        destroyOnHidden
        items={[
          {
            key: 'pendientes',
            label: 'Por aprobar',
            children: <TablaUsuarios filtros={{ estado: 'PENDIENTE_APROBACION' }} conAcciones onRechazar={abrirRechazo} accion={accion} />,
          },
          {
            key: 'todos',
            label: 'Todas las cuentas',
            children: (
              <>
                <Space wrap style={{ marginBottom: 16 }}>
                  <Buscador placeholder="Nombre o email" onBuscar={cambiar('q')} style={{ width: 260 }} />
                  <Select allowClear placeholder="Rol" style={{ width: 160 }} options={opcionesDe('rol')} onChange={cambiar('rol')} />
                  <Select allowClear placeholder="Estado" style={{ width: 200 }} options={opcionesDe('usuario')} onChange={cambiar('estado')} />
                </Space>
                <TablaUsuarios key={version} filtros={filtros} />
              </>
            ),
          },
        ]}
      />

      <Modal
        title={`Rechazar el registro de ${rechazando?.usuario.nombre ?? ''}`}
        open={Boolean(rechazando)}
        onOk={rechazar}
        onCancel={() => setRechazando(null)}
        okText="Rechazar"
        okButtonProps={{ danger: true }}
        confirmLoading={ejecutando}
        forceRender
      >
        <Form form={formRechazo} layout="vertical">
          <Form.Item name="motivo" label="Motivo (se le informa por correo)" rules={reglasTexto('el motivo', 3, 200)}>
            <Input.TextArea rows={2} maxLength={200} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Nuevo administrador"
        open={creandoAdmin}
        onOk={crearAdmin}
        onCancel={() => setCreandoAdmin(false)}
        okText="Crear"
        confirmLoading={ejecutando}
        forceRender
      >
        <Form form={formAdmin} layout="vertical">
          <Form.Item name="nombre" label="Nombre" rules={reglasNombre('nombre')}>
            <Input maxLength={50} />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={reglasEmail}>
            <Input />
          </Form.Item>
          <Form.Item name="contrasena" label="Contraseña" rules={reglasContrasena} extra="Al menos 8 caracteres, con letras y números">
            <Input.Password autoComplete="new-password" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
