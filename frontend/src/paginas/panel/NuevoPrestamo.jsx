import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Alert, Button, Card, Form, Select, Space, Table } from 'antd'
import { ejemplaresApi, librosApi, prestamosApi } from '../../api'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import { SelectorLibro, SelectorSede, SelectorSocio } from '../../componentes/Selectores'

export default function NuevoPrestamo() {
  const navegar = useNavigate()
  const [parametros] = useSearchParams()
  const libroInicial = Number(parametros.get('libro')) || undefined
  const [form] = Form.useForm()
  const libroId = Form.useWatch('libro_id', form)
  const origenId = Form.useWatch('sede_origen_id', form)
  const destinoId = Form.useWatch('sede_destino_id', form)
  const [libroFijo, setLibroFijo] = useState()
  const [disponibilidad, setDisponibilidad] = useState(null)
  const [ejemplares, setEjemplares] = useState([])
  const { ejecutar, ejecutando } = useAccion()

  // Si se llega desde el catalogo, el libro viene preseleccionado
  useEffect(() => {
    if (!libroInicial) return
    librosApi.obtener(libroInicial).then((l) => setLibroFijo({ value: l.id, label: `${l.titulo} - ${l.autor}` }))
  }, [libroInicial])

  // Al elegir libro: en que sedes hay ejemplares libres
  useEffect(() => {
    form.setFieldsValue({ sede_origen_id: undefined, ejemplar_id: undefined })
    setDisponibilidad(null)
    if (libroId) librosApi.disponibilidad(libroId).then(setDisponibilidad)
  }, [libroId, form])

  // Al elegir sede de origen: que ejemplares libres tiene
  useEffect(() => {
    form.setFieldsValue({ ejemplar_id: undefined })
    setEjemplares([])
    if (!libroId || !origenId) return
    ejemplaresApi.listar({ libro_id: libroId, sede_id: origenId, estado: 'DISPONIBLE', tamanio: 100 }).then((pagina) => {
      setEjemplares(pagina.items)
      if (pagina.items.length) form.setFieldsValue({ ejemplar_id: pagina.items[0].id })
    })
    if (!form.getFieldValue('sede_destino_id')) form.setFieldsValue({ sede_destino_id: origenId })
  }, [libroId, origenId, form])

  const sedesConStock = disponibilidad?.sedes.filter((s) => s.disponibles > 0) ?? []
  const esInterbibliotecario = origenId && destinoId && origenId !== destinoId

  async function confirmar(valores) {
    const { libro_id: _libro, ...datos } = valores
    const prestamo = await ejecutar(
      () => prestamosApi.solicitar(datos),
      esInterbibliotecario
        ? 'Préstamo solicitado. Se generó el remito de envío.'
        : 'Préstamo registrado. El socio ya puede retirar el ejemplar.',
    )
    if (prestamo) navegar('/prestamos')
  }

  return (
    <>
      <Encabezado titulo="Nuevo préstamo" />
      <Card style={{ maxWidth: 760 }}>
        <Form form={form} layout="vertical" onFinish={confirmar} initialValues={{ libro_id: libroInicial }}>
          <Form.Item name="socio_id" label="Socio" rules={[{ required: true, message: 'Elegí el socio' }]}>
            <SelectorSocio />
          </Form.Item>

          <Form.Item name="libro_id" label="Libro" rules={[{ required: true, message: 'Elegí el libro' }]}>
            <SelectorLibro opcionFija={libroFijo} />
          </Form.Item>

          {disponibilidad && (
            <Table
              size="small"
              rowKey="sede_id"
              style={{ marginBottom: 16 }}
              dataSource={disponibilidad.sedes}
              pagination={false}
              locale={{ emptyText: 'Ninguna sede activa tiene ejemplares de este libro' }}
              columns={[
                { title: 'Sede', dataIndex: 'sede' },
                { title: 'Ejemplares libres', render: (_, s) => `${s.disponibles} de ${s.total}` },
              ]}
            />
          )}

          {disponibilidad && sedesConStock.length === 0 && (
            <Alert
              type="warning"
              showIcon
              style={{ marginBottom: 16 }}
              message="No hay ejemplares libres de este libro."
              description={<a onClick={() => navegar(`/reservas?libro=${libroId}`)}>Registrar una reserva</a>}
            />
          )}

          <Space wrap style={{ width: '100%' }} size="middle">
            <Form.Item
              name="sede_origen_id"
              label="Sede de origen (dueña del ejemplar)"
              rules={[{ required: true, message: 'Elegí la sede' }]}
            >
              <Select
                style={{ width: 280 }}
                placeholder="Sede con ejemplares libres"
                options={sedesConStock.map((s) => ({ value: s.sede_id, label: `${s.sede} (${s.disponibles})` }))}
              />
            </Form.Item>
            <Form.Item name="ejemplar_id" label="Ejemplar" rules={[{ required: true, message: 'Elegí el ejemplar' }]}>
              <Select
                style={{ width: 200 }}
                options={ejemplares.map((e) => ({ value: e.id, label: e.codigo_inventario }))}
              />
            </Form.Item>
          </Space>

          <Form.Item
            name="sede_destino_id"
            label="Sede donde retira el socio"
            rules={[{ required: true, message: 'Elegí la sede' }]}
            extra={
              esInterbibliotecario
                ? 'Préstamo inter-sede: se generará un remito y el plazo empieza a correr cuando el ejemplar llegue.'
                : 'Préstamo local: el socio lo retira ahora.'
            }
          >
            <SelectorSede style={{ width: 280 }} />
          </Form.Item>

          <Space>
            <Button type="primary" htmlType="submit" loading={ejecutando}>
              Registrar préstamo
            </Button>
            <Button onClick={() => navegar(-1)}>Cancelar</Button>
          </Space>
        </Form>
      </Card>
    </>
  )
}
