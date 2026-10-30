import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { App, Button, Form, Modal, Popconfirm, Select, Space, Table } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { librosApi, prestamosApi, reservasApi } from '../../api'
import useListado from '../../hooks/useListado'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import { SelectorLibro, SelectorSocio } from '../../componentes/Selectores'
import { opcionesDe } from '../../utiles/estados'
import { fecha, nombreSocio } from '../../utiles/formato'

function NuevaReserva({ abierta, libroInicial, onCerrar, onCreada }) {
  const [form] = Form.useForm()
  const libroId = Form.useWatch('libro_id', form)
  const [sedes, setSedes] = useState([])
  const [libroFijo, setLibroFijo] = useState()
  const { ejecutar, ejecutando } = useAccion()

  useEffect(() => {
    if (!libroInicial) return
    librosApi.obtener(libroInicial).then((l) => setLibroFijo({ value: l.id, label: `${l.titulo} - ${l.autor}` }))
  }, [libroInicial])

  useEffect(() => {
    if (abierta) form.resetFields()
  }, [abierta, form])

  // Solo se puede reservar en sedes que tienen ese libro
  useEffect(() => {
    setSedes([])
    if (libroId) librosApi.disponibilidad(libroId).then((d) => setSedes(d.sedes))
  }, [libroId])

  async function crear() {
    const valores = await form.validateFields()
    const reserva = await ejecutar(() => reservasApi.crear(valores))
    if (!reserva) return
    onCreada(
      reserva.estado === 'DISPONIBLE'
        ? `Reserva lista: se apartó el ejemplar ${reserva.ejemplar.codigo_inventario} hasta el ${fecha(reserva.fecha_expiracion)}`
        : 'Reserva registrada en espera: se asignará el primer ejemplar que se libere',
    )
  }

  return (
    <Modal
      title="Nueva reserva"
      open={abierta}
      onOk={crear}
      onCancel={onCerrar}
      confirmLoading={ejecutando}
      okText="Reservar"
      forceRender
    >
      <Form form={form} layout="vertical" initialValues={{ libro_id: libroInicial }}>
        <Form.Item name="socio_id" label="Socio" rules={[{ required: true }]}>
          <SelectorSocio />
        </Form.Item>
        <Form.Item name="libro_id" label="Libro" rules={[{ required: true }]}>
          <SelectorLibro opcionFija={libroFijo} />
        </Form.Item>
        <Form.Item name="sede_id" label="Sede donde retira" rules={[{ required: true }]}>
          <Select
            placeholder={libroId ? 'Sede' : 'Elegí primero el libro'}
            options={sedes.map((s) => ({
              value: s.sede_id,
              label: `${s.sede} — ${s.disponibles ? `${s.disponibles} libre(s), se aparta ahora` : 'sin libres, queda en espera'}`,
            }))}
          />
        </Form.Item>
      </Form>
    </Modal>
  )
}

export default function Reservas() {
  const { message } = App.useApp()
  const [parametros, setParametros] = useSearchParams()
  const libroInicial = Number(parametros.get('libro')) || undefined
  const [filtros, setFiltros] = useState({})
  const { items, cargando, paginacion, recargar } = useListado(reservasApi.listar, filtros)
  const [creando, setCreando] = useState(Boolean(libroInicial))
  const { ejecutar } = useAccion()

  function cerrarCreacion() {
    setCreando(false)
    if (libroInicial) setParametros({})
  }

  async function prestar(reserva) {
    const datos = {
      socio_id: reserva.socio_id,
      ejemplar_id: reserva.ejemplar_id,
      sede_origen_id: reserva.sede_id,
      sede_destino_id: reserva.sede_id,
    }
    if (await ejecutar(() => prestamosApi.solicitar(datos), 'Préstamo registrado. La reserva quedó cumplida.')) recargar()
  }

  async function cancelar(reserva) {
    if (await ejecutar(() => reservasApi.cancelar(reserva.id), 'Reserva cancelada')) recargar()
  }

  async function procesarVencidas() {
    const resultado = await ejecutar(() => reservasApi.procesarVencidas())
    if (resultado) {
      message.info(`${resultado.reservas_vencidas} reserva(s) vencida(s)`)
      recargar()
    }
  }

  return (
    <>
      <Encabezado titulo="Reservas">
        <SelectorSocio style={{ width: 260 }} onChange={(socio_id) => setFiltros((f) => ({ ...f, socio_id }))} />
        <Select
          allowClear
          placeholder="Estado"
          style={{ width: 180 }}
          options={opcionesDe('reserva')}
          onChange={(estado) => setFiltros((f) => ({ ...f, estado }))}
        />
        <Popconfirm
          title="¿Procesar reservas vencidas?"
          description="Las reservas no retiradas a tiempo se vencen y sus ejemplares se liberan."
          onConfirm={procesarVencidas}
        >
          <Button>Procesar vencidas</Button>
        </Popconfirm>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreando(true)}>
          Nueva reserva
        </Button>
      </Encabezado>

      <Table
        rowKey="id"
        loading={cargando}
        dataSource={items}
        pagination={paginacion}
        scroll={{ x: true }}
        columns={[
          { title: 'Socio', render: (_, r) => nombreSocio(r.socio) },
          { title: 'Libro', render: (_, r) => r.libro.titulo },
          { title: 'Sede', render: (_, r) => r.sede.nombre },
          { title: 'Estado', dataIndex: 'estado', render: (v) => <EstadoTag tipo="reserva" valor={v} /> },
          { title: 'Ejemplar', render: (_, r) => r.ejemplar?.codigo_inventario ?? '-' },
          { title: 'Reservado', dataIndex: 'fecha_reserva', render: fecha },
          { title: 'Retirar hasta', dataIndex: 'fecha_expiracion', render: fecha },
          {
            title: '',
            key: 'acciones',
            render: (_, r) => (
              <Space>
                {r.estado === 'DISPONIBLE' && (
                  <Popconfirm title="¿Registrar el préstamo del ejemplar apartado?" onConfirm={() => prestar(r)}>
                    <a>Prestar</a>
                  </Popconfirm>
                )}
                {['PENDIENTE', 'DISPONIBLE'].includes(r.estado) && (
                  <Popconfirm title="¿Cancelar la reserva?" onConfirm={() => cancelar(r)}>
                    <a>Cancelar</a>
                  </Popconfirm>
                )}
              </Space>
            ),
          },
        ]}
      />

      <NuevaReserva
        abierta={creando}
        libroInicial={libroInicial}
        onCerrar={cerrarCreacion}
        onCreada={(texto) => {
          message.success(texto)
          cerrarCreacion()
          recargar()
        }}
      />
    </>
  )
}
