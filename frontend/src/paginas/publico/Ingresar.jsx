import { useState } from 'react'
import { Link, Navigate, useNavigate, useSearchParams } from 'react-router-dom'
import { Alert, Button, Card, Form, Input, Typography } from 'antd'
import { cuentaApi } from '../../api'
import useAccion from '../../hooks/useAccion'
import useSesion, { inicioDe } from '../../sesion/useSesion'
import { reglasEmail, validar } from '../../utiles/reglas'

// Solo se vuelve a rutas internas, para no redirigir a otro sitio
const rutaInterna = (ruta) => (ruta?.startsWith('/') && !ruta.startsWith('//') ? ruta : null)

export default function Ingresar() {
  const { usuario, ingresar } = useSesion()
  const navegar = useNavigate()
  const [parametros] = useSearchParams()
  const [form] = Form.useForm()
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)
  const [reenviando, setReenviando] = useState(false)
  const reenvio = useAccion()

  if (usuario) return <Navigate to={inicioDe(usuario)} replace />

  async function enviar() {
    const valores = await validar(form)
    if (!valores) return
    setEnviando(true)
    setError(null)
    try {
      const conectado = await ingresar(valores.email, valores.contrasena)
      const volver = rutaInterna(parametros.get('volver'))
      // Un socio vuelve a donde estaba; el admin va siempre a su panel
      navegar(conectado.rol === 'SOCIO' && volver ? volver : inicioDe(conectado), { replace: true })
    } catch (e) {
      setError(e.message)
    } finally {
      setEnviando(false)
    }
  }

  async function reenviar() {
    const email = form.getFieldValue('email')
    if (!email) {
      form.validateFields(['email']).catch(() => {})
      return
    }
    setReenviando(true)
    await reenvio.ejecutar(() => cuentaApi.reenviarConfirmacion(email), 'Si la cuenta existe y no está confirmada, te reenviamos el correo.')
    setReenviando(false)
  }

  return (
    <Card style={{ maxWidth: 420, margin: '40px auto' }}>
      <Typography.Title level={3}>Ingresar</Typography.Title>
      {error && <Alert type="error" showIcon message={error} style={{ marginBottom: 16 }} />}
      <Form form={form} layout="vertical" onFinish={enviar} requiredMark={false}>
        <Form.Item name="email" label="Email" rules={reglasEmail}>
          <Input autoComplete="username" autoFocus />
        </Form.Item>
        <Form.Item name="contrasena" label="Contraseña" rules={[{ required: true, message: 'Ingresá la contraseña' }]}>
          <Input.Password autoComplete="current-password" />
        </Form.Item>
        <Button type="primary" htmlType="submit" block loading={enviando}>
          Ingresar
        </Button>
      </Form>
      <Typography.Paragraph style={{ marginTop: 16, marginBottom: 4 }}>
        ¿Todavía no tenés cuenta? <Link to="/registro">Registrate como socio</Link>
      </Typography.Paragraph>
      <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
        ¿No te llegó el correo de confirmación?{' '}
        <Button type="link" size="small" style={{ padding: 0 }} loading={reenviando} onClick={reenviar}>
          Reenviarlo
        </Button>
      </Typography.Paragraph>
    </Card>
  )
}
