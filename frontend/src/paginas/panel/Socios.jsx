import { useCallback, useState } from 'react'
import { Button, Drawer, Form, Input, Modal, Select, Space, Table, Tabs, Tag } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { prestamosApi, sociosApi } from '../../api'
import useListado from '../../hooks/useListado'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import Ruta from '../../componentes/Ruta'
import { fecha, moneda, nombreSocio } from '../../utiles/formato'

function PrestamosDelSocio({ socioId }) {
  const { items, cargando, paginacion } = useListado(prestamosApi.listar, { socio_id: socioId }, 5)
  return (
    <Table
      size="small"
      rowKey="id"
      loading={cargando}
      dataSource={items}
      pagination={paginacion}
      columns={[
        { title: 'Libro', render: (_, p) => p.ejemplar.libro.titulo },
        { title: 'Estado', dataIndex: 'estado', render: (v) => <EstadoTag tipo="prestamo" valor={v} /> },
        { title: 'Vence', dataIndex: 'fecha_vencimiento', render: fecha },
        { title: 'Sedes', render: (_, p) => <Ruta origen={p.sede_origen} destino={p.sede_destino} /> },
      ]}
    />
  )
}

function HistorialDelSocio({ socioId }) {
  const cargar = useCallback((params) => sociosApi.historial(socioId, params), [socioId])
  const { items, cargando, paginacion } = useListado(cargar, {}, 5)
  return (
    <Table
      size="small"
      rowKey="prestamo_id"
      loading={cargando}
      dataSource={items}
      pagination={paginacion}
      columns={[
        { title: 'Libro', dataIndex: 'titulo' },
        { title: 'Autor', dataIndex: 'autor' },
        { title: 'Devuelto', dataIndex: 'fecha_devolucion', render: fecha },
        { title: 'Atraso', dataIndex: 'dias_atraso', render: (d) => (d ? `${d} días` : '-') },
        { title: 'Multa', dataIndex: 'multa', render: (m) => (m ? moneda(m) : '-') },
      ]}
    />
  )
}

export default function Socios() {
  const [filtros, setFiltros] = useState({})
  const { items, cargando, paginacion, recargar } = useListado(sociosApi.listar, filtros)
  const [edicion, setEdicion] = useState(null)
  const [inhabilitando, setInhabilitando] = useState(null)
  const [detalle, setDetalle] = useState(null)
  const [form] = Form.useForm()
  const [formMotivo] = Form.useForm()
  const { ejecutar, ejecutando } = useAccion()

  function abrir(socio) {
    form.resetFields()
    form.setFieldsValue(socio ?? {})
    setEdicion(socio ?? {})
  }

  function abrirInhabilitacion(socio) {
    formMotivo.resetFields()
    setInhabilitando(socio)
  }

  async function guardar() {
    const valores = await form.validateFields()
    const ok = await ejecutar(
      () => (edicion.id ? sociosApi.actualizar(edicion.id, valores) : sociosApi.crear(valores)),
      edicion.id ? 'Socio actualizado' : 'Socio registrado',
    )
    if (ok) {
      setEdicion(null)
      recargar()
    }
  }

  async function inhabilitar() {
    const { motivo } = await formMotivo.validateFields()
    const ok = await ejecutar(() => sociosApi.inhabilitar(inhabilitando.id, motivo), 'Socio inhabilitado')
    if (ok) {
      setInhabilitando(null)
      recargar()
    }
  }

  async function habilitar(socio) {
    if (await ejecutar(() => sociosApi.habilitar(socio.id), 'Socio habilitado')) recargar()
  }

  return (
    <>
      <Encabezado titulo="Socios">
        <Input.Search
          allowClear
          placeholder="Nombre, apellido o DNI"
          onSearch={(q) => setFiltros((f) => ({ ...f, q }))}
          style={{ width: 260 }}
        />
        <Select
          allowClear
          placeholder="Estado"
          style={{ width: 160 }}
          onChange={(habilitado) => setFiltros((f) => ({ ...f, habilitado }))}
          options={[
            { value: true, label: 'Habilitados' },
            { value: false, label: 'Inhabilitados' },
          ]}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => abrir()}>
          Nuevo socio
        </Button>
      </Encabezado>

      <Table
        rowKey="id"
        loading={cargando}
        dataSource={items}
        pagination={paginacion}
        scroll={{ x: true }}
        columns={[
          { title: 'Socio', render: (_, s) => <a onClick={() => setDetalle(s)}>{nombreSocio(s)}</a> },
          { title: 'DNI', dataIndex: 'dni' },
          { title: 'Email', dataIndex: 'email' },
          { title: 'Teléfono', dataIndex: 'telefono' },
          { title: 'Alta', dataIndex: 'fecha_alta', render: fecha },
          {
            title: 'Estado',
            render: (_, s) =>
              s.habilitado ? <Tag color="green">Habilitado</Tag> : <Tag color="red" title={s.motivo_inhabilitacion}>Inhabilitado</Tag>,
          },
          {
            title: '',
            key: 'acciones',
            render: (_, s) => (
              <Space>
                <a onClick={() => abrir(s)}>Editar</a>
                {s.habilitado ? (
                  <a onClick={() => abrirInhabilitacion(s)}>Inhabilitar</a>
                ) : (
                  <a onClick={() => habilitar(s)}>Habilitar</a>
                )}
              </Space>
            ),
          },
        ]}
      />

      <Modal
        title={edicion?.id ? 'Editar socio' : 'Nuevo socio'}
        open={edicion !== null}
        onOk={guardar}
        onCancel={() => setEdicion(null)}
        confirmLoading={ejecutando}
        okText="Guardar"
        forceRender
      >
        <Form form={form} layout="vertical">
          <Form.Item name="dni" label="DNI" rules={[{ required: true, pattern: /^\d{6,}$/, message: 'Solo números, al menos 6' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="nombre" label="Nombre" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="apellido" label="Apellido" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ required: true, type: 'email' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="telefono" label="Teléfono">
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={`Inhabilitar a ${nombreSocio(inhabilitando)}`}
        open={inhabilitando !== null}
        onOk={inhabilitar}
        onCancel={() => setInhabilitando(null)}
        confirmLoading={ejecutando}
        okText="Inhabilitar"
        okButtonProps={{ danger: true }}
        forceRender
      >
        <Form form={formMotivo} layout="vertical">
          <Form.Item name="motivo" label="Motivo" rules={[{ required: true, min: 3 }]}>
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>

      <Drawer title={nombreSocio(detalle)} open={detalle !== null} onClose={() => setDetalle(null)} width={720} destroyOnHidden>
        {detalle && (
          <Tabs
            items={[
              { key: 'prestamos', label: 'Préstamos', children: <PrestamosDelSocio socioId={detalle.id} /> },
              { key: 'historial', label: 'Historial de lecturas', children: <HistorialDelSocio socioId={detalle.id} /> },
            ]}
          />
        )}
      </Drawer>
    </>
  )
}
