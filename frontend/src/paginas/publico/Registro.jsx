import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Button, Card, Col, Form, Input, Result, Row, Typography } from 'antd'
import { cuentaApi } from '../../api'
import useAccion from '../../hooks/useAccion'
import { reglasContrasena, reglasDni, reglasEmail, reglasNombre, reglasTelefono, soloDigitos, validar } from '../../utiles/reglas'

export default function Registro() {
  const [form] = Form.useForm()
  const { ejecutar, ejecutando } = useAccion()
  const [registrado, setRegistrado] = useState(null)

  async function enviar() {
    const valores = await validar(form)
    if (!valores) return
    const { repetir: _repetir, ...datos } = valores
    if (await ejecutar(() => cuentaApi.registrar(datos))) setRegistrado(datos.email)
  }

  if (registrado) {
    return (
      <Result
        status="success"
        title="Revisá tu correo"
        subTitle={`Te mandamos un enlace a ${registrado} para confirmar tu email. Después, la biblioteca revisa tus datos y te avisa cuando tu cuenta esté aprobada.`}
        extra={<Link to="/">Volver al catálogo</Link>}
      />
    )
  }

  return (
    <Card style={{ maxWidth: 560, margin: '24px auto' }}>
      <Typography.Title level={3}>Hacerme socio</Typography.Title>
      <Typography.Paragraph type="secondary">
        Completá tus datos. Vas a recibir un correo para confirmar tu email y, una vez aprobada tu cuenta, vas a
        poder pedir libros y ver tu historial.
      </Typography.Paragraph>
      <Form form={form} layout="vertical" onFinish={enviar}>
        <Row gutter={12}>
          <Col xs={24} sm={12}>
            <Form.Item name="nombre" label="Nombre" rules={reglasNombre('nombre')}>
              <Input maxLength={50} />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item name="apellido" label="Apellido" rules={reglasNombre('apellido')}>
              <Input maxLength={50} />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item name="dni" label="DNI" rules={reglasDni} normalize={soloDigitos}>
              <Input inputMode="numeric" maxLength={10} />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item name="telefono" label="Teléfono (opcional)" rules={reglasTelefono} normalize={soloDigitos}>
              <Input inputMode="numeric" maxLength={20} />
            </Form.Item>
          </Col>
        </Row>
        <Form.Item name="email" label="Email" rules={reglasEmail}>
          <Input autoComplete="email" />
        </Form.Item>
        <Row gutter={12}>
          <Col xs={24} sm={12}>
            <Form.Item name="contrasena" label="Contraseña" rules={reglasContrasena} extra="Al menos 8 caracteres, con letras y números">
              <Input.Password autoComplete="new-password" />
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item
              name="repetir"
              label="Repetir contraseña"
              dependencies={['contrasena']}
              rules={[
                { required: true, message: 'Repetí la contraseña' },
                ({ getFieldValue }) => ({
                  validator: (_, valor) =>
                    !valor || valor === getFieldValue('contrasena')
                      ? Promise.resolve()
                      : Promise.reject(new Error('Las contraseñas no coinciden')),
                }),
              ]}
            >
              <Input.Password autoComplete="new-password" />
            </Form.Item>
          </Col>
        </Row>
        <Button type="primary" htmlType="submit" block loading={ejecutando}>
          Registrarme
        </Button>
      </Form>
      <Typography.Paragraph style={{ marginTop: 16, marginBottom: 0 }}>
        ¿Ya tenés cuenta? <Link to="/ingresar">Ingresá</Link>
      </Typography.Paragraph>
    </Card>
  )
}
