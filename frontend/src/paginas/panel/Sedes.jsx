import { useState } from 'react'
import { Button, Form, Input, Modal, Popconfirm, Segmented, Space, Table, Tag } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { sedesApi } from '../../api'
import useCarga from '../../hooks/useCarga'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'

const FILTROS = { todas: undefined, activas: true, baja: false }

const listarSedes = (activa) => sedesApi.listar({ activa })

export default function Sedes() {
  const [filtro, setFiltro] = useState('todas')
  const { datos, cargando, recargar } = useCarga(listarSedes, [FILTROS[filtro]])
  const [edicion, setEdicion] = useState(null) // null: cerrado, {}: nueva, sede: editar
  const [form] = Form.useForm()
  const { ejecutar, ejecutando } = useAccion()

  function abrir(sede) {
    form.resetFields()
    form.setFieldsValue(sede ?? {})
    setEdicion(sede ?? {})
  }

  async function guardar() {
    const valores = await form.validateFields()
    const datosSede = { ...valores, email: valores.email || null }
    const ok = await ejecutar(
      () => (edicion.id ? sedesApi.actualizar(edicion.id, datosSede) : sedesApi.crear(datosSede)),
      edicion.id ? 'Sede actualizada' : 'Sede creada',
    )
    if (ok) {
      setEdicion(null)
      recargar()
    }
  }

  async function cambiarEstado(sede) {
    const ok = await ejecutar(
      () => (sede.activa ? sedesApi.darDeBaja(sede.id) : sedesApi.darDeAlta(sede.id)),
      sede.activa ? 'Sede dada de baja' : 'Sede reactivada',
    )
    if (ok) recargar()
  }

  return (
    <>
      <Encabezado titulo="Sedes" descripcion="Bibliotecas que forman la red">
        <Segmented
          value={filtro}
          onChange={setFiltro}
          options={[
            { value: 'todas', label: 'Todas' },
            { value: 'activas', label: 'Activas' },
            { value: 'baja', label: 'Dadas de baja' },
          ]}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => abrir()}>
          Nueva sede
        </Button>
      </Encabezado>

      <Table
        rowKey="id"
        loading={cargando}
        dataSource={datos ?? []}
        pagination={false}
        scroll={{ x: true }}
        columns={[
          { title: 'Nombre', dataIndex: 'nombre' },
          { title: 'Dirección', dataIndex: 'direccion' },
          { title: 'Teléfono', dataIndex: 'telefono' },
          { title: 'Email', dataIndex: 'email' },
          { title: 'Horario', dataIndex: 'horario' },
          {
            title: 'Estado',
            dataIndex: 'activa',
            render: (activa) => (activa ? <Tag color="green">Activa</Tag> : <Tag>Dada de baja</Tag>),
          },
          {
            title: '',
            key: 'acciones',
            render: (_, sede) => (
              <Space>
                <a onClick={() => abrir(sede)}>Editar</a>
                <Popconfirm
                  title={sede.activa ? '¿Dar de baja la sede?' : '¿Reactivar la sede?'}
                  description={sede.activa ? 'No podrá iniciar préstamos, reservas ni envíos.' : undefined}
                  onConfirm={() => cambiarEstado(sede)}
                >
                  <a>{sede.activa ? 'Dar de baja' : 'Reactivar'}</a>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal
        title={edicion?.id ? 'Editar sede' : 'Nueva sede'}
        open={edicion !== null}
        onOk={guardar}
        onCancel={() => setEdicion(null)}
        confirmLoading={ejecutando}
        okText="Guardar"
        forceRender
      >
        <Form form={form} layout="vertical">
          <Form.Item name="nombre" label="Nombre" rules={[{ required: true, min: 2 }]}>
            <Input />
          </Form.Item>
          <Form.Item name="direccion" label="Dirección" rules={[{ required: true, min: 3 }]}>
            <Input />
          </Form.Item>
          <Form.Item name="telefono" label="Teléfono">
            <Input />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="horario" label="Horario">
            <Input placeholder="Lun a Vie 8 a 20" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
