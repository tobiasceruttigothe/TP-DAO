import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Form, Input, Modal, Table } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { inventariosApi } from '../../api'
import useListado from '../../hooks/useListado'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import { SelectorSede } from '../../componentes/Selectores'
import { fechaHora } from '../../utiles/formato'
import { validar } from '../../utiles/reglas'

export default function Inventarios() {
  const navegar = useNavigate()
  const [sedeId, setSedeId] = useState()
  const [iniciando, setIniciando] = useState(false)
  const [form] = Form.useForm()
  const { items, cargando, paginacion } = useListado(inventariosApi.listar, { sede_id: sedeId })
  const { ejecutar, ejecutando } = useAccion()

  async function iniciar() {
    const valores = await validar(form)
    if (!valores) return
    const inventario = await ejecutar(() => inventariosApi.iniciar(valores), 'Inventario iniciado')
    if (inventario) navegar(`/panel/inventarios/${inventario.id}`)
  }

  return (
    <>
      <Encabezado titulo="Inventario" descripcion="Recuento físico de los estantes de cada sede">
        <SelectorSede soloActivas={false} style={{ width: 200 }} onChange={setSedeId} />
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            form.resetFields()
            setIniciando(true)
          }}
        >
          Iniciar inventario
        </Button>
      </Encabezado>
      <Table
        rowKey="id"
        loading={cargando}
        dataSource={items}
        pagination={paginacion}
        scroll={{ x: true }}
        onRow={(i) => ({ onClick: () => navegar(`/panel/inventarios/${i.id}`), style: { cursor: 'pointer' } })}
        columns={[
          { title: 'Sede', render: (_, i) => i.sede.nombre },
          { title: 'Estado', dataIndex: 'estado', render: (v) => <EstadoTag tipo="inventario" valor={v} /> },
          { title: 'Inicio', dataIndex: 'fecha_inicio', render: fechaHora },
          { title: 'Cierre', dataIndex: 'fecha_cierre', render: fechaHora },
          { title: 'Códigos leídos', dataIndex: 'cantidad_registrados' },
          { title: 'Observación', dataIndex: 'observacion', render: (v) => v ?? '-' },
        ]}
      />

      <Modal
        title="Iniciar inventario"
        open={iniciando}
        onOk={iniciar}
        onCancel={() => setIniciando(false)}
        okText="Iniciar"
        confirmLoading={ejecutando}
        forceRender
      >
        <Form form={form} layout="vertical">
          <Form.Item name="sede_id" label="Sede" rules={[{ required: true, message: 'Elegí la sede' }]}>
            <SelectorSede />
          </Form.Item>
          <Form.Item name="observacion" label="Observación (opcional)" rules={[{ max: 300, message: 'Máximo 300 caracteres' }]}>
            <Input placeholder="Recuento mensual" maxLength={300} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
