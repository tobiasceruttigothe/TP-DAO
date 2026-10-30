import { useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Button, Card, Col, Descriptions, Form, Input, Modal, Popconfirm, Row, Select, Space, Table } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { ejemplaresApi, librosApi } from '../../api'
import useCarga from '../../hooks/useCarga'
import useListado from '../../hooks/useListado'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import { SelectorSede } from '../../componentes/Selectores'
import { opcionesDe } from '../../utiles/estados'
import FormularioLibro from './FormularioLibro'

export default function LibroDetalle() {
  const { id } = useParams()
  const libroId = Number(id)
  const navegar = useNavigate()
  const libro = useCarga(librosApi.obtener, [libroId])
  const disponibilidad = useCarga(librosApi.disponibilidad, [libroId])
  const [filtroEstado, setFiltroEstado] = useState()
  const ejemplares = useListado(ejemplaresApi.listar, { libro_id: libroId, estado: filtroEstado })
  const [editando, setEditando] = useState(null)
  const [agregando, setAgregando] = useState(false)
  const [form] = Form.useForm()
  const { ejecutar, ejecutando } = useAccion()

  function recargarTodo() {
    ejemplares.recargar()
    disponibilidad.recargar()
  }

  function abrirAgregar() {
    form.resetFields()
    setAgregando(true)
  }

  async function agregarEjemplar() {
    const valores = await form.validateFields()
    const ok = await ejecutar(() => ejemplaresApi.crear({ ...valores, libro_id: libroId }), 'Ejemplar agregado')
    if (ok) {
      setAgregando(false)
      recargarTodo()
    }
  }

  async function accion(operacion, mensaje) {
    if (await ejecutar(operacion, mensaje)) recargarTodo()
  }

  const datosLibro = libro.datos

  return (
    <>
      <Encabezado titulo={datosLibro?.titulo ?? 'Libro'} descripcion={datosLibro?.autor}>
        <Button onClick={() => setEditando(datosLibro)}>Editar</Button>
        <Button onClick={() => navegar(`/reservas?libro=${libroId}`)}>Reservar</Button>
        <Button type="primary" onClick={() => navegar(`/prestamos/nuevo?libro=${libroId}`)}>
          Prestar
        </Button>
      </Encabezado>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={10}>
          <Card title="Datos" loading={libro.cargando}>
            <Descriptions
              column={1}
              size="small"
              items={[
                { key: 'isbn', label: 'ISBN', children: datosLibro?.isbn },
                { key: 'editorial', label: 'Editorial', children: datosLibro?.editorial ?? '-' },
                { key: 'anio', label: 'Año', children: datosLibro?.anio_publicacion ?? '-' },
                { key: 'genero', label: 'Género', children: datosLibro?.genero ?? '-' },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={14}>
          <Card title={`Disponibilidad: ${disponibilidad.datos?.total_disponibles ?? 0} ejemplares libres`}>
            <Table
              size="small"
              rowKey="sede_id"
              loading={disponibilidad.cargando}
              dataSource={disponibilidad.datos?.sedes ?? []}
              pagination={false}
              locale={{ emptyText: 'No hay ejemplares en sedes activas' }}
              columns={[
                { title: 'Sede', dataIndex: 'sede' },
                { title: 'Disponibles', render: (_, s) => `${s.disponibles} de ${s.total}` },
                { title: 'Códigos libres', dataIndex: 'ejemplares_disponibles', render: (c) => c.join(', ') || '-' },
              ]}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="Ejemplares"
        style={{ marginTop: 16 }}
        extra={
          <Space>
            <Select allowClear placeholder="Estado" style={{ width: 170 }} options={opcionesDe('ejemplar')} onChange={setFiltroEstado} />
            <Button icon={<PlusOutlined />} onClick={abrirAgregar}>
              Agregar ejemplar
            </Button>
          </Space>
        }
      >
        <Table
          rowKey="id"
          loading={ejemplares.cargando}
          dataSource={ejemplares.items}
          pagination={ejemplares.paginacion}
          scroll={{ x: true }}
          columns={[
            { title: 'Código', dataIndex: 'codigo_inventario' },
            { title: 'Sede', render: (_, e) => e.sede.nombre },
            { title: 'Estado', dataIndex: 'estado', render: (v) => <EstadoTag tipo="ejemplar" valor={v} /> },
            { title: 'Estado físico', dataIndex: 'estado_fisico', render: (v) => <EstadoTag tipo="fisico" valor={v} /> },
            {
              title: '',
              key: 'acciones',
              render: (_, e) => (
                <Space>
                  {e.estado === 'EN_REPARACION' && (
                    <a onClick={() => accion(() => ejemplaresApi.marcarReparado(e.id), 'Ejemplar disponible nuevamente')}>
                      Marcar reparado
                    </a>
                  )}
                  {['DISPONIBLE', 'EN_REPARACION'].includes(e.estado) && (
                    <Popconfirm
                      title="¿Dar de baja el ejemplar?"
                      onConfirm={() => accion(() => ejemplaresApi.darDeBaja(e.id), 'Ejemplar dado de baja')}
                    >
                      <a>Dar de baja</a>
                    </Popconfirm>
                  )}
                </Space>
              ),
            },
          ]}
        />
      </Card>

      <Modal
        title="Agregar ejemplar"
        open={agregando}
        onOk={agregarEjemplar}
        onCancel={() => setAgregando(false)}
        confirmLoading={ejecutando}
        okText="Agregar"
        forceRender
      >
        <Form form={form} layout="vertical" initialValues={{ estado_fisico: 'BUENO' }}>
          <Form.Item name="codigo_inventario" label="Código de inventario" rules={[{ required: true }]}>
            <Input placeholder="CEN-0123" />
          </Form.Item>
          <Form.Item name="sede_id" label="Sede" rules={[{ required: true }]}>
            <SelectorSede />
          </Form.Item>
          <Form.Item name="estado_fisico" label="Estado físico">
            <Select options={opcionesDe('fisico').filter((o) => o.value !== 'DESTRUIDO')} />
          </Form.Item>
        </Form>
      </Modal>

      <FormularioLibro
        libro={editando}
        onCerrar={() => setEditando(null)}
        onGuardado={() => {
          setEditando(null)
          libro.recargar()
        }}
      />
    </>
  )
}
