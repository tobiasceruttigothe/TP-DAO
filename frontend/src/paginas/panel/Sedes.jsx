import { useState } from 'react'
import { Button, Form, Input, Modal, Popconfirm, Segmented, Space, Table, Tag } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { sedesApi } from '../../api'
import useCarga from '../../hooks/useCarga'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import { normalizarPrefijo, reglasPrefijo, reglasTelefono, reglasTexto, soloDigitos, validar } from '../../utiles/reglas'

const FILTROS = { todas: undefined, activas: true, baja: false }

const listarSedes = (activa) => sedesApi.listar({ activa })

export default function Sedes() {
  const [filtro, setFiltro] = useState('todas')
  const { datos, cargando, recargar } = useCarga(listarSedes, [FILTROS[filtro]])
  const [edicion, setEdicion] = useState(null) // null: cerrado, {}: nueva, sede: editar
  const [form] = Form.useForm()
  const { ejecutar, ejecutando } = useAccion()

  function abrir(sede) {
    form.resetFields()
    form.setFieldsValue(sede ?? {})
    setEdicion(sede ?? {})
  }

  async function guardar() {
    const valores = await validar(form)
    if (!valores) return
    const datosSede = { ...valores, email: valores.email || null }
    // El prefijo solo se elige al crear la sede: ya esta impreso en las etiquetas de sus ejemplares
    if (edicion.id) delete datosSede.prefijo
    const ok = await ejecutar(
      () => (edicion.id ? sedesApi.actualizar(edicion.id, datosSede) : sedesApi.crear(datosSede)),
      edicion.id ? 'Sede actualizada' : 'Sede creada',
    )
    if (ok) {
      setEdicion(null)
      recargar()
    }
  }

  async function cambiarEstado(sede) {
    const ok = await ejecutar(
      () => (sede.activa ? sedesApi.darDeBaja(sede.id) : sedesApi.darDeAlta(sede.id)),
      sede.activa ? 'Sede dada de baja' : 'Sede reactivada',
    )
    if (ok) recargar()
  }

  return (
    <>
      <Encabezado titulo="Sedes" descripcion="Bibliotecas que forman la red">
        <Segmented
          value={filtro}
          onChange={setFiltro}
          options={[
            { value: 'todas', label: 'Todas' },
            { value: 'activas', label: 'Activas' },
            { value: 'baja', label: 'Dadas de baja' },
          ]}
        />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => abrir()}>
          Nueva sede
        </Button>
      </Encabezado>

      <Table
        rowKey="id"
        loading={cargando}
        dataSource={datos ?? []}
        pagination={false}
        scroll={{ x: true }}
        columns={[
          { title: 'Nombre', dataIndex: 'nombre' },
          { title: 'Prefijo', dataIndex: 'prefijo', render: (prefijo) => <Tag>{prefijo}</Tag> },
          { title: 'Dirección', dataIndex: 'direccion' },
          { title: 'Teléfono', dataIndex: 'telefono' },
          { title: 'Email', dataIndex: 'email' },
          { title: 'Horario', dataIndex: 'horario' },
          {
            title: 'Estado',
            dataIndex: 'activa',
            render: (activa) => (activa ? <Tag color="green">Activa</Tag> : <Tag>Dada de baja</Tag>),
          },
          {
            title: '',
            key: 'acciones',
            render: (_, sede) => (
              <Space>
                <a onClick={() => abrir(sede)}>Editar</a>
                <Popconfirm
                  title={sede.activa ? '¿Dar de baja la sede?' : '¿Reactivar la sede?'}
                  description={sede.activa ? 'No podrá iniciar préstamos, reservas ni envíos.' : undefined}
                  onConfirm={() => cambiarEstado(sede)}
                >
                  <a>{sede.activa ? 'Dar de baja' : 'Reactivar'}</a>
                </Popconfirm>
              </Space>
            ),
          },
        ]}
      />

      <Modal
        title={edicion?.id ? 'Editar sede' : 'Nueva sede'}
        open={edicion !== null}
        onOk={guardar}
        onCancel={() => setEdicion(null)}
        confirmLoading={ejecutando}
        okText="Guardar"
        forceRender
      >
        <Form form={form} layout="vertical">
          <Form.Item name="nombre" label="Nombre" rules={reglasTexto('el nombre', 2, 100)}>
            <Input maxLength={100} />
          </Form.Item>
          <Form.Item
            name="prefijo"
            label="Prefijo de los códigos"
            rules={edicion?.id ? [] : reglasPrefijo}
            normalize={normalizarPrefijo}
            extra={
              edicion?.id
                ? 'No se puede cambiar: ya está en las etiquetas de los ejemplares'
                : 'De 2 a 5 letras. Los ejemplares de la sede se numeran solos: CEN-0001, CEN-0002...'
            }
          >
            <Input maxLength={5} placeholder="CEN" disabled={Boolean(edicion?.id)} style={{ width: 120 }} />
          </Form.Item>
          <Form.Item name="direccion" label="Dirección" rules={reglasTexto('la dirección', 3, 200)}>
            <Input maxLength={200} />
          </Form.Item>
          <Form.Item name="telefono" label="Teléfono" rules={reglasTelefono} normalize={soloDigitos} extra="Opcional. Solo números">
            <Input inputMode="numeric" maxLength={20} />
          </Form.Item>
          <Form.Item name="email" label="Email" rules={[{ type: 'email', message: 'Ingresá un email válido' }]}>
            <Input />
          </Form.Item>
          <Form.Item name="horario" label="Horario" rules={[{ max: 200, message: 'Máximo 200 caracteres' }]}>
            <Input placeholder="Lun a Vie 8 a 20" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  )
}
