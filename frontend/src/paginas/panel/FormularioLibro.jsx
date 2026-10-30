import { useEffect } from 'react'
import { Form, Input, InputNumber, Modal } from 'antd'
import { librosApi } from '../../api'
import useAccion from '../../hooks/useAccion'

/** Alta o edicion de un libro. `libro` vacio ({}) es alta; null cierra el modal. */
export default function FormularioLibro({ libro, onCerrar, onGuardado }) {
  const [form] = Form.useForm()
  const { ejecutar, ejecutando } = useAccion()

  // Cada vez que se abre se limpia el formulario y se cargan los datos del libro a editar
  useEffect(() => {
    if (!libro) return
    form.resetFields()
    form.setFieldsValue(libro)
  }, [libro, form])

  async function guardar() {
    const valores = await form.validateFields()
    const ok = await ejecutar(
      () => (libro.id ? librosApi.actualizar(libro.id, valores) : librosApi.crear(valores)),
      libro.id ? 'Libro actualizado' : 'Libro agregado al catálogo',
    )
    if (ok) onGuardado(ok)
  }

  return (
    <Modal
      title={libro?.id ? 'Editar libro' : 'Nuevo libro'}
      open={libro !== null}
      onOk={guardar}
      onCancel={onCerrar}
      confirmLoading={ejecutando}
      okText="Guardar"
      forceRender
    >
      <Form form={form} layout="vertical">
        <Form.Item name="isbn" label="ISBN" rules={[{ required: true, min: 10, max: 20 }]}>
          <Input />
        </Form.Item>
        <Form.Item name="titulo" label="Título" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="autor" label="Autor" rules={[{ required: true }]}>
          <Input />
        </Form.Item>
        <Form.Item name="editorial" label="Editorial">
          <Input />
        </Form.Item>
        <Form.Item name="anio_publicacion" label="Año de publicación">
          <InputNumber min={1400} max={2100} style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="genero" label="Género">
          <Input />
        </Form.Item>
      </Form>
    </Modal>
  )
}
