import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { Alert, Button, Card, Col, Descriptions, Form, Input, Modal, Radio, Row, Steps, Timeline } from 'antd'
import { remitosApi } from '../../api'
import useCarga from '../../hooks/useCarga'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import { ESTADOS, opcionesDe } from '../../utiles/estados'
import { fechaHora } from '../../utiles/formato'

const RECORRIDO = ['PENDIENTE', 'EMPAQUETADO', 'DESPACHADO', 'RECIBIDO']

// Acciones posibles en cada estado (las mismas transiciones que valida el backend)
const ACCIONES = {
  empaquetar: { texto: 'Empaquetar', exito: 'Remito empaquetado' },
  despachar: { texto: 'Despachar', exito: 'Remito despachado' },
  recibir: { texto: 'Registrar recepción', exito: 'Recepción registrada' },
  extraviar: { texto: 'Marcar extraviado', exito: 'Remito marcado como extraviado', peligro: true },
  cancelar: { texto: 'Cancelar envío', exito: 'Envío cancelado', peligro: true },
}

function accionesDisponibles(remito) {
  const cancelable = remito.tipo === 'IDA'
  switch (remito.estado) {
    case 'PENDIENTE':
      return ['empaquetar', ...(cancelable ? ['cancelar'] : [])]
    case 'EMPAQUETADO':
      return ['despachar', ...(cancelable ? ['cancelar'] : [])]
    case 'DESPACHADO':
      return ['recibir', 'extraviar']
    default:
      return []
  }
}

function pasos(remito) {
  const finalNormal = RECORRIDO.indexOf(remito.estado)
  if (finalNormal >= 0) {
    return { actual: finalNormal, estado: remito.estado === 'RECIBIDO' ? 'finish' : 'process' }
  }
  // Extraviado o cancelado: se marca en error el paso donde se corto
  const anterior = remito.movimientos.at(-1)?.estado_anterior
  return { actual: Math.max(RECORRIDO.indexOf(anterior) + 1, 0), estado: 'error' }
}

export default function RemitoDetalle() {
  const { id } = useParams()
  const { datos: remito, cargando, recargar } = useCarga(remitosApi.obtener, [Number(id)])
  const [accion, setAccion] = useState(null)
  const [form] = Form.useForm()
  const { ejecutar, ejecutando } = useAccion()

  function abrirAccion(nombre) {
    form.resetFields()
    setAccion(nombre)
  }

  async function confirmar() {
    const valores = await form.validateFields()
    const ok = await ejecutar(() => remitosApi[accion](remito.id, valores), ACCIONES[accion].exito)
    if (ok) {
      setAccion(null)
      recargar()
    }
  }

  if (!remito) return <Card loading={cargando} />

  const { actual, estado } = pasos(remito)
  const titulos = RECORRIDO.map((e) => ({ title: ESTADOS.remito[e].texto }))
  if (estado === 'error') titulos[actual] = { title: ESTADOS.remito[remito.estado].texto }

  return (
    <>
      <Encabezado titulo={`Remito ${remito.numero}`} descripcion={`${remito.tipo === 'IDA' ? 'Envío' : 'Retorno'} del préstamo N° ${remito.prestamo_id}`}>
        {accionesDisponibles(remito).map((a) => (
          <Button key={a} danger={ACCIONES[a].peligro} type={ACCIONES[a].peligro ? 'default' : 'primary'} onClick={() => abrirAccion(a)}>
            {ACCIONES[a].texto}
          </Button>
        ))}
      </Encabezado>

      <Card style={{ marginBottom: 16 }}>
        <Steps current={actual} status={estado} items={titulos} />
      </Card>

      {remito.incidencias.map((i) => (
        <Alert
          key={i.id}
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          message={`Incidencia: ${ESTADOS.incidencia[i.tipo].texto}`}
          description={`${fechaHora(i.fecha)}${i.descripcion ? ` — ${i.descripcion}` : ''}`}
        />
      ))}

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}>
          <Card title="Datos del envío">
            <Descriptions
              column={1}
              size="small"
              items={[
                { key: 'estado', label: 'Estado', children: <EstadoTag tipo="remito" valor={remito.estado} /> },
                { key: 'libro', label: 'Libro', children: remito.ejemplar.libro.titulo },
                { key: 'ejemplar', label: 'Ejemplar', children: remito.ejemplar.codigo_inventario },
                { key: 'origen', label: 'Origen', children: remito.sede_origen.nombre },
                { key: 'destino', label: 'Destino', children: remito.sede_destino.nombre },
                { key: 'creado', label: 'Creado', children: fechaHora(remito.fecha_creacion) },
                { key: 'despacho', label: 'Despachado', children: fechaHora(remito.fecha_despacho) },
                { key: 'recepcion', label: 'Recibido', children: fechaHora(remito.fecha_recepcion) },
                {
                  key: 'fisico',
                  label: 'Estado al llegar',
                  children: remito.estado_fisico_recepcion ? <EstadoTag tipo="fisico" valor={remito.estado_fisico_recepcion} /> : '-',
                },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} lg={12}>
          <Card title="Trazabilidad">
            <Timeline
              items={remito.movimientos.map((m) => ({
                key: m.fecha + m.estado_nuevo,
                color: ['EXTRAVIADO', 'CANCELADO'].includes(m.estado_nuevo) ? 'red' : m.estado_nuevo === 'RECIBIDO' ? 'green' : 'blue',
                children: (
                  <>
                    <b>{ESTADOS.remito[m.estado_nuevo]?.texto ?? m.estado_nuevo}</b>
                    <div style={{ color: '#888', fontSize: 12 }}>{fechaHora(m.fecha)}</div>
                    {m.observacion && <div>{m.observacion}</div>}
                  </>
                ),
              }))}
            />
          </Card>
        </Col>
      </Row>

      <Modal
        title={accion ? ACCIONES[accion].texto : ''}
        open={accion !== null}
        onOk={confirmar}
        onCancel={() => setAccion(null)}
        confirmLoading={ejecutando}
        okText="Confirmar"
        okButtonProps={{ danger: accion && ACCIONES[accion].peligro }}
        forceRender
      >
        {accion === 'cancelar' && <p>Se cancelará el préstamo y el ejemplar volverá a estar disponible.</p>}
        {accion === 'extraviar' && <p>El ejemplar quedará como extraviado y se cancelará el préstamo si es un envío de ida.</p>}
        <Form form={form} layout="vertical" initialValues={{ estado_fisico: 'BUENO' }}>
          {accion === 'recibir' && (
            <Form.Item
              name="estado_fisico"
              label="Revisión del ejemplar"
              extra="Dañado o destruido registran una incidencia. Destruido da de baja el ejemplar."
            >
              <Radio.Group options={opcionesDe('fisico')} optionType="button" />
            </Form.Item>
          )}
          <Form.Item name="observacion" label="Observación">
            <Input.TextArea rows={2} maxLength={300} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
