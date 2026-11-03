import { useEffect } from 'react'
import { Form, Input, InputNumber, Modal } from 'antd'
import { librosApi } from '../../api'
import useAccion from '../../hooks/useAccion'
import { normalizarIsbn, reglasAnio, reglasIsbn, reglasTexto, validar } from '../../utiles/reglas'

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
    const valores = await validar(form)
    if (!valores) return
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
        <Form.Item
          name="isbn"
          label="ISBN"
          rules={reglasIsbn}
          normalize={normalizarIsbn}
          extra="ISBN-10 o ISBN-13. Los guiones se quitan solos."
        >
          <Input maxLength={17} />
        </Form.Item>
        <Form.Item name="titulo" label="Título" rules={reglasTexto('el título', 1, 200)}>
          <Input maxLength={200} />
        </Form.Item>
        <Form.Item name="autor" label="Autor" rules={reglasTexto('el autor', 2, 150)}>
          <Input maxLength={150} />
        </Form.Item>
        <Form.Item name="editorial" label="Editorial">
          <Input />
        </Form.Item>
        <Form.Item name="anio_publicacion" label="Año de publicación" rules={reglasAnio}>
          <InputNumber style={{ width: '100%' }} />
        </Form.Item>
        <Form.Item name="genero" label="Género">
          <Input />
        </Form.Item>
      </Form>
    </Modal>
  )
}
