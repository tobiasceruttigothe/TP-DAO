import { useEffect, useState } from 'react'
import { Alert, Button, Descriptions, Divider, Form, Input, Modal, Select, Space, Table, Tag, Typography } from 'antd'
import { librosApi, pedidosApi } from '../../api'
import useListado from '../../hooks/useListado'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import { opcionesDe } from '../../utiles/estados'
import { fechaHora, nombreSocio } from '../../utiles/formato'
import { reglasTexto, validar } from '../../utiles/reglas'

/**
 * Resolver un pedido: reservar en la sede que eligio el socio (queda apartado o en espera)
 * o traer un ejemplar libre desde otra sede con un prestamo inter-sede.
 */
function FormularioRechazo({ ejecutando, onRechazar, onVolver }) {
  const [form] = Form.useForm()

  async function confirmar() {
    const valores = await validar(form)
    if (valores) onRechazar(valores.motivo)
  }

  return (
    <Form form={form} layout="vertical">
      <Form.Item name="motivo" label="Motivo (le llega al socio)" rules={reglasTexto('el motivo', 3, 300)}>
        <Input.TextArea rows={2} maxLength={300} autoFocus />
      </Form.Item>
      <Space>
        <Button danger loading={ejecutando} onClick={confirmar}>
          Confirmar rechazo
        </Button>
        <Button onClick={onVolver}>Volver</Button>
      </Space>
    </Form>
  )
}

function ResolverPedido({ pedido, onCerrar, onResuelto }) {
  const [disponibilidad, setDisponibilidad] = useState(null)
  const [rechazando, setRechazando] = useState(false)
  const { ejecutar, ejecutando } = useAccion()

  useEffect(() => {
    if (!pedido) return
    setDisponibilidad(null)
    setRechazando(false)
    librosApi.disponibilidad(pedido.libro.id).then(setDisponibilidad).catch(() => setDisponibilidad({ sedes: [] }))
  }, [pedido])

  async function resolver(operacion, mensaje) {
    if (await ejecutar(operacion, mensaje)) onResuelto()
  }

  if (!pedido) return null
  const sedes = disponibilidad?.sedes ?? []
  const enSedePedida = sedes.find((s) => s.sede_id === pedido.sede.id)?.disponibles ?? 0
  const otrasSedes = sedes.filter((s) => s.sede_id !== pedido.sede.id && s.disponibles > 0)

  return (
    <Modal title={`Pedido de «${pedido.libro.titulo}»`} open onCancel={onCerrar} footer={null} width={640} destroyOnHidden>
      <Descriptions
        size="small"
        column={1}
        items={[
          { key: 'socio', label: 'Socio', children: `${nombreSocio(pedido.socio)} (DNI ${pedido.socio.dni})` },
          { key: 'sede', label: 'Quiere retirarlo en', children: pedido.sede.nombre },
          { key: 'fecha', label: 'Pedido el', children: fechaHora(pedido.fecha) },
          ...(pedido.comentario ? [{ key: 'comentario', label: 'Comentario', children: pedido.comentario }] : []),
        ]}
      />
      <Divider orientation="left">Reservar en {pedido.sede.nombre}</Divider>
      <Space direction="vertical" style={{ width: '100%' }}>
        <Typography.Text>
          {enSedePedida > 0
            ? `Hay ${enSedePedida} ejemplar(es) libre(s): se aparta uno y el socio tiene unos días para retirarlo.`
            : 'No hay ejemplares libres en esa sede: el socio queda en la lista de espera y se le avisa cuando se libere uno.'}
        </Typography.Text>
        <Button type="primary" loading={ejecutando} onClick={() => resolver(() => pedidosApi.reservar(pedido.id), 'Reserva registrada')}>
          {enSedePedida > 0 ? 'Reservar' : 'Reservar en espera'}
        </Button>
      </Space>

      <Divider orientation="left">Traer desde otra sede</Divider>
      {disponibilidad === null ? (
        <Typography.Text type="secondary">Consultando disponibilidad...</Typography.Text>
      ) : otrasSedes.length === 0 ? (
        <Typography.Text type="secondary">No hay ejemplares libres en otras sedes.</Typography.Text>
      ) : (
        <Table
          size="small"
          rowKey="sede_id"
          pagination={false}
          dataSource={otrasSedes}
          columns={[
            { title: 'Sede', dataIndex: 'sede' },
            { title: 'Libres', dataIndex: 'disponibles' },
            {
              title: '',
              key: 'enviar',
              align: 'right',
              render: (_, s) => (
                <Button
                  size="small"
                  loading={ejecutando}
                  onClick={() =>
                    resolver(() => pedidosApi.enviar(pedido.id, s.sede_id), `Préstamo inter-sede creado desde ${s.sede}`)
                  }
                >
                  Enviar desde acá
                </Button>
              ),
            },
          ]}
        />
      )}

      <Divider orientation="left">No se puede</Divider>
      {rechazando ? (
        <FormularioRechazo
          ejecutando={ejecutando}
          onVolver={() => setRechazando(false)}
          onRechazar={(motivo) => resolver(() => pedidosApi.rechazar(pedido.id, motivo), 'Pedido rechazado')}
        />
      ) : (
        <Button danger onClick={() => setRechazando(true)}>
          Rechazar pedido
        </Button>
      )}
    </Modal>
  )
}

export default function Pedidos() {
  const [estado, setEstado] = useState('PENDIENTE')
  const [resolviendo, setResolviendo] = useState(null)
  const { items, cargando, paginacion, recargar } = useListado(pedidosApi.listar, { estado })

  return (
    <>
      <Encabezado titulo="Pedidos de socios" descripcion="Los socios piden libros desde el catálogo; acá se decide cómo atenderlos">
        <Select allowClear placeholder="Estado" style={{ width: 160 }} value={estado} options={opcionesDe('pedido')} onChange={setEstado} />
      </Encabezado>
      {estado === 'PENDIENTE' && items.length > 0 && (
        <Alert type="info" showIcon style={{ marginBottom: 16 }} message={`Hay ${paginacion.total} pedido(s) esperando respuesta.`} />
      )}
      <Table
        rowKey="id"
        loading={cargando}
        dataSource={items}
        pagination={paginacion}
        scroll={{ x: true }}
        columns={[
          { title: 'Fecha', dataIndex: 'fecha', render: fechaHora },
          { title: 'Socio', render: (_, p) => nombreSocio(p.socio) },
          { title: 'Libro', render: (_, p) => p.libro.titulo },
          { title: 'Retiro en', render: (_, p) => p.sede.nombre },
          { title: 'Estado', dataIndex: 'estado', render: (v) => <EstadoTag tipo="pedido" valor={v} /> },
          {
            title: 'Resolución',
            render: (_, p) => p.resolucion ?? (p.comentario ? <Tag>Comentario: {p.comentario}</Tag> : '-'),
          },
          {
            title: '',
            key: 'acciones',
            render: (_, p) => p.estado === 'PENDIENTE' && <a onClick={() => setResolviendo(p)}>Resolver</a>,
          },
        ]}
      />
      <ResolverPedido
        pedido={resolviendo}
        onCerrar={() => setResolviendo(null)}
        onResuelto={() => {
          setResolviendo(null)
          recargar()
        }}
      />
    </>
  )
}
