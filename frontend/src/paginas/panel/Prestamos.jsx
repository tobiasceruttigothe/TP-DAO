import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { App, Button, DatePicker, Form, Input, List, Modal, Radio, Select, Space, Table } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import dayjs from 'dayjs'
import { prestamosApi } from '../../api'
import useListado from '../../hooks/useListado'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import Ruta from '../../componentes/Ruta'
import { SelectorSocio } from '../../componentes/Selectores'
import { opcionesDe } from '../../utiles/estados'
import { diasHasta, fecha, fechaApi, moneda, nombreSocio } from '../../utiles/formato'

const estaVencido = (p) => p.estado === 'ACTIVO' && diasHasta(p.fecha_vencimiento) < 0

function Devolucion({ prestamo, onCerrar, onDevuelto }) {
  const [form] = Form.useForm()
  const { ejecutar, ejecutando } = useAccion()
  const { modal } = App.useApp()

  useEffect(() => {
    if (prestamo) form.resetFields()
  }, [prestamo, form])

  async function registrar() {
    const valores = await form.validateFields()
    const resultado = await ejecutar(() =>
      prestamosApi.devolver(prestamo.id, { ...valores, fecha_devolucion: fechaApi(valores.fecha_devolucion) }),
    )
    if (!resultado) return
    modal.success({
      title: 'Devolución registrada',
      content: (
        <>
          <p>{resultado.multa > 0 ? `Multa por atraso: ${moneda(resultado.multa)}` : 'Sin multa.'}</p>
          {resultado.tipo === 'INTERBIBLIOTECARIO' && valores.estado_fisico !== 'DESTRUIDO' && (
            <p>Se generó el remito de retorno a {resultado.sede_origen.nombre}.</p>
          )}
        </>
      ),
    })
    onDevuelto()
  }

  return (
    <Modal
      title="Registrar devolución"
      open={prestamo !== null}
      onOk={registrar}
      onCancel={onCerrar}
      confirmLoading={ejecutando}
      okText="Registrar"
      forceRender
    >
      {prestamo && (
        <p>
          <b>{prestamo.ejemplar.libro.titulo}</b> ({prestamo.ejemplar.codigo_inventario}) — {nombreSocio(prestamo.socio)}
          <br />
          Vencimiento: {fecha(prestamo.fecha_vencimiento)}
        </p>
      )}
      <Form form={form} layout="vertical" initialValues={{ estado_fisico: 'BUENO', fecha_devolucion: dayjs() }}>
        <Form.Item name="estado_fisico" label="Estado físico" rules={[{ required: true }]}>
          <Radio.Group options={opcionesDe('fisico')} optionType="button" />
        </Form.Item>
        <Form.Item name="fecha_devolucion" label="Fecha de devolución">
          <DatePicker format="DD/MM/YYYY" disabledDate={(d) => d.isAfter(dayjs(), 'day')} />
        </Form.Item>
        <Form.Item name="observaciones" label="Observaciones">
          <Input.TextArea rows={2} maxLength={300} />
        </Form.Item>
      </Form>
    </Modal>
  )
}

function RemitosDelPrestamo({ prestamo, onCerrar }) {
  const navegar = useNavigate()
  const [remitos, setRemitos] = useState([])

  async function cargar() {
    setRemitos(await prestamosApi.remitos(prestamo.id))
  }

  return (
    <Modal
      title={`Remitos del préstamo ${prestamo?.id ?? ''}`}
      open={prestamo !== null}
      onCancel={onCerrar}
      footer={null}
      afterOpenChange={(abierto) => abierto && cargar()}
      destroyOnHidden
    >
      <List
        dataSource={remitos}
        locale={{ emptyText: 'Sin remitos' }}
        renderItem={(r) => (
          <List.Item actions={[<a key="ver" onClick={() => navegar(`/remitos/${r.id}`)}>Ver</a>]}>
            <Space>
              <b>{r.numero}</b>
              <EstadoTag tipo="tipoRemito" valor={r.tipo} />
              <Ruta origen={r.sede_origen} destino={r.sede_destino} />
              <EstadoTag tipo="remito" valor={r.estado} />
            </Space>
          </List.Item>
        )}
      />
    </Modal>
  )
}

export default function Prestamos() {
  const navegar = useNavigate()
  const [filtros, setFiltros] = useState({})
  const { items, cargando, paginacion, recargar } = useListado(prestamosApi.listar, filtros)
  const [devolviendo, setDevolviendo] = useState(null)
  const [viendoRemitos, setViendoRemitos] = useState(null)

  return (
    <>
      <Encabezado titulo="Préstamos">
        <SelectorSocio style={{ width: 280 }} onChange={(socio_id) => setFiltros((f) => ({ ...f, socio_id }))} />
        <Select
          allowClear
          placeholder="Estado"
          style={{ width: 150 }}
          options={opcionesDe('prestamo')}
          onChange={(estado) => setFiltros((f) => ({ ...f, estado }))}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navegar('/prestamos/nuevo')}>
          Nuevo préstamo
        </Button>
      </Encabezado>

      <Table
        rowKey="id"
        loading={cargando}
        dataSource={items}
        pagination={paginacion}
        scroll={{ x: true }}
        rowClassName={(p) => (estaVencido(p) ? 'fila-vencida' : '')}
        columns={[
          { title: 'N°', dataIndex: 'id', width: 60 },
          { title: 'Socio', render: (_, p) => nombreSocio(p.socio) },
          {
            title: 'Libro',
            render: (_, p) => (
              <>
                {p.ejemplar.libro.titulo}
                <div style={{ fontSize: 12, color: '#888' }}>{p.ejemplar.codigo_inventario}</div>
              </>
            ),
          },
          { title: 'Tipo', dataIndex: 'tipo', render: (v) => <EstadoTag tipo="tipoPrestamo" valor={v} /> },
          { title: 'Sedes', render: (_, p) => <Ruta origen={p.sede_origen} destino={p.sede_destino} /> },
          { title: 'Estado', dataIndex: 'estado', render: (v) => <EstadoTag tipo="prestamo" valor={v} /> },
          { title: 'Solicitado', dataIndex: 'fecha_solicitud', render: fecha },
          { title: 'Vence', dataIndex: 'fecha_vencimiento', render: fecha },
          { title: 'Multa', dataIndex: 'multa', render: (m) => (m ? moneda(m) : '-') },
          {
            title: '',
            key: 'acciones',
            render: (_, p) => (
              <Space>
                {p.estado === 'ACTIVO' && <a onClick={() => setDevolviendo(p)}>Devolver</a>}
                {p.tipo === 'INTERBIBLIOTECARIO' && <a onClick={() => setViendoRemitos(p)}>Remitos</a>}
              </Space>
            ),
          },
        ]}
      />

      <Devolucion
        prestamo={devolviendo}
        onCerrar={() => setDevolviendo(null)}
        onDevuelto={() => {
          setDevolviendo(null)
          recargar()
        }}
      />
      <RemitosDelPrestamo prestamo={viendoRemitos} onCerrar={() => setViendoRemitos(null)} />
    </>
  )
}
