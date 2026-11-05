import { useEffect, useState } from 'react'
import { Alert, Form, Input, Modal, Select, Typography } from 'antd'
import { librosApi, miApi, sedesApi } from '../api'
import useAccion from '../hooks/useAccion'
import { validar } from '../utiles/reglas'

/**
 * El socio pide un libro para retirarlo en la sede que elija. El pedido le llega a la
 * biblioteca, que decide si lo reserva ahi o lo trae desde otra sede.
 */
export default function ModalPedido({ libro, onCerrar, onPedido }) {
  const [form] = Form.useForm()
  const [sedes, setSedes] = useState([])
  const [disponibles, setDisponibles] = useState({})
  const { ejecutar, ejecutando } = useAccion()

  useEffect(() => {
    if (!libro) return
    form.resetFields()
    Promise.all([sedesApi.listar({ activa: true }), librosApi.disponibilidad(libro.id)])
      .then(([listaSedes, disponibilidad]) => {
        setSedes(listaSedes)
        setDisponibles(Object.fromEntries(disponibilidad.sedes.map((s) => [s.sede_id, s.disponibles])))
      })
      .catch(() => setSedes([]))
  }, [libro, form])

  async function pedir() {
    const valores = await validar(form)
    if (!valores) return
    const pedido = await ejecutar(
      () => miApi.pedir({ ...valores, libro_id: libro.id }),
      'Pedido enviado. Te avisamos cuando la biblioteca lo resuelva.',
    )
    if (pedido) onPedido?.(pedido)
  }

  return (
    <Modal
      title={libro ? `Pedir «${libro.titulo}»` : ''}
      open={Boolean(libro)}
      onOk={pedir}
      onCancel={onCerrar}
      okText="Enviar pedido"
      confirmLoading={ejecutando}
      forceRender
    >
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="Elegí dónde querés retirarlo. Si en esa sede no hay ejemplares libres, la biblioteca puede traerlo desde otra."
      />
      <Form form={form} layout="vertical">
        <Form.Item name="sede_id" label="Sede donde lo retirás" rules={[{ required: true, message: 'Elegí una sede' }]}>
          <Select
            placeholder="Sede"
            options={sedes.map((s) => ({
              value: s.id,
              label: disponibles[s.id] ? `${s.nombre} (${disponibles[s.id]} libre/s)` : `${s.nombre} (sin ejemplares libres)`,
            }))}
          />
        </Form.Item>
        <Form.Item name="comentario" label="Comentario (opcional)" rules={[{ max: 300, message: 'Máximo 300 caracteres' }]}>
          <Input.TextArea rows={2} maxLength={300} placeholder="Por ejemplo: lo necesito antes del viernes" />
        </Form.Item>
      </Form>
      <Typography.Text type="secondary">Podés tener un solo pedido pendiente por libro.</Typography.Text>
    </Modal>
  )
}
