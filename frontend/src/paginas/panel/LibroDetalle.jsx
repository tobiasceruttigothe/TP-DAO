import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card, Col, Descriptions, Form, InputNumber, Modal, Popconfirm, Row, Select, Space, Table, Tag, Typography } from 'antd'
import { PlusOutlined, PrinterOutlined } from '@ant-design/icons'
import { ejemplaresApi, librosApi } from '../../api'
import useCarga from '../../hooks/useCarga'
import useListado from '../../hooks/useListado'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import { SelectorSede } from '../../componentes/Selectores'
import { opcionesDe } from '../../utiles/estados'
import { validar } from '../../utiles/reglas'
import FormularioLibro from './FormularioLibro'

// Mismo tope que MAXIMO_EJEMPLARES_POR_CARGA en app/schemas/libro.py
const MAXIMO_POR_CARGA = 50

/** "CEN-0021" y 3 -> "CEN-0021 a CEN-0023" */
function rangoDeCodigos(primero, cantidad) {
  if (cantidad <= 1) return primero
  const [, prefijo, numero] = primero.match(/^(.*-)(\d+)$/)
  const ultimo = String(Number(numero) + cantidad - 1).padStart(numero.length, '0')
  return `${primero} a ${prefijo}${ultimo}`
}

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
  const [creados, setCreados] = useState(null) // { sedeId, codigos } de la ultima carga
  const [form] = Form.useForm()
  const sedeElegida = Form.useWatch('sede_id', form)
  const cantidad = Form.useWatch('cantidad', form)
  const [proximoCodigo, setProximoCodigo] = useState(null)
  const { ejecutar, ejecutando } = useAccion()

  // El codigo lo asigna el sistema: se muestra cuales va a recibir antes de confirmar
  useEffect(() => {
    setProximoCodigo(null)
    if (!agregando || !sedeElegida) return
    ejemplaresApi.proximoCodigo(sedeElegida).then((r) => setProximoCodigo(r.codigo)).catch(() => {})
  }, [agregando, sedeElegida])

  function recargarTodo() {
    ejemplares.recargar()
    disponibilidad.recargar()
  }

  function abrirAgregar() {
    form.resetFields()
    setAgregando(true)
  }

  async function agregarEjemplar() {
    const valores = await validar(form)
    if (!valores) return
    const nuevos = await ejecutar(() => ejemplaresApi.crear({ ...valores, libro_id: libroId }))
    if (nuevos) {
      setAgregando(false)
      setCreados({ sedeId: valores.sede_id, codigos: nuevos.map((e) => e.codigo_inventario) })
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
        <Button onClick={() => navegar(`/panel/reservas?libro=${libroId}`)}>Reservar</Button>
        <Button type="primary" onClick={() => navegar(`/panel/prestamos/nuevo?libro=${libroId}`)}>
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
                      title="¿Marcar el ejemplar como extraviado?"
                      description="Deja de figurar como disponible hasta que aparezca."
                      onConfirm={() => accion(() => ejemplaresApi.marcarExtraviado(e.id), 'Ejemplar marcado como extraviado')}
                    >
                      <a>Extraviado</a>
                    </Popconfirm>
                  )}
                  {e.estado === 'EXTRAVIADO' && (
                    <a onClick={() => accion(() => ejemplaresApi.marcarRecuperado(e.id), 'Ejemplar recuperado')}>Apareció</a>
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
        <Form form={form} layout="vertical" initialValues={{ estado_fisico: 'BUENO', cantidad: 1 }}>
          <Form.Item name="sede_id" label="Sede" rules={[{ required: true, message: 'Elegí la sede' }]}>
            <SelectorSede />
          </Form.Item>
          <Row gutter={16}>
            <Col span={14}>
              <Form.Item name="estado_fisico" label="Estado físico">
                <Select options={opcionesDe('fisico').filter((o) => o.value !== 'DESTRUIDO')} />
              </Form.Item>
            </Col>
            <Col span={10}>
              <Form.Item
                name="cantidad"
                label="Cantidad"
                rules={[{ required: true, message: 'Ingresá la cantidad' }]}
                extra="Todos con la misma sede y estado"
              >
                <InputNumber min={1} max={MAXIMO_POR_CARGA} precision={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
        <Alert
          type="info"
          showIcon
          message={
            proximoCodigo
              ? `Códigos que se asignan: ${rangoDeCodigos(proximoCodigo, cantidad || 1)}`
              : 'El código de inventario lo asigna el sistema con el prefijo de la sede.'
          }
        />
      </Modal>

      <Modal
        title={creados ? `${creados.codigos.length} ejemplar(es) agregado(s)` : ''}
        open={creados !== null}
        onCancel={() => setCreados(null)}
        footer={[
          <Button key="cerrar" onClick={() => setCreados(null)}>
            Cerrar
          </Button>,
          <Button
            key="imprimir"
            type="primary"
            icon={<PrinterOutlined />}
            onClick={() => navegar(`/panel/etiquetas?libro=${libroId}&sede=${creados.sedeId}`)}
          >
            Imprimir etiquetas
          </Button>,
        ]}
      >
        <Typography.Paragraph>Códigos asignados (los que van en las etiquetas):</Typography.Paragraph>
        <Space wrap>
          {creados?.codigos.map((codigo) => (
            <Tag key={codigo}>{codigo}</Tag>
          ))}
        </Space>
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
