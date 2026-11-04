import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Popconfirm, Select, Table, Typography } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { miApi } from '../../api'
import useListado from '../../hooks/useListado'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import { opcionesDe } from '../../utiles/estados'
import { fechaHora } from '../../utiles/formato'

export default function MisPedidos() {
  const navegar = useNavigate()
  const [estado, setEstado] = useState()
  const { items, cargando, paginacion, recargar } = useListado(miApi.pedidos, { estado })
  const { ejecutar } = useAccion()

  async function cancelar(id) {
    if (await ejecutar(() => miApi.cancelarPedido(id), 'Pedido cancelado')) recargar()
  }

  return (
    <>
      <Encabezado titulo="Mis pedidos" descripcion="Libros que pediste a la biblioteca y qué decidió con cada uno">
        <Select allowClear placeholder="Estado" style={{ width: 160 }} options={opcionesDe('pedido')} onChange={setEstado} />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navegar('/')}>
          Pedir un libro
        </Button>
      </Encabezado>
      <Table
        rowKey="id"
        loading={cargando}
        dataSource={items}
        pagination={paginacion}
        scroll={{ x: true }}
        columns={[
          { title: 'Fecha', dataIndex: 'fecha', render: fechaHora },
          { title: 'Libro', render: (_, p) => p.libro.titulo },
          { title: 'Retiro en', render: (_, p) => p.sede.nombre },
          { title: 'Estado', dataIndex: 'estado', render: (v) => <EstadoTag tipo="pedido" valor={v} /> },
          {
            title: 'Respuesta de la biblioteca',
            render: (_, p) => p.resolucion ?? <Typography.Text type="secondary">{p.comentario ? `Tu comentario: ${p.comentario}` : '-'}</Typography.Text>,
          },
          {
            title: '',
            key: 'acciones',
            render: (_, p) =>
              p.estado === 'PENDIENTE' && (
                <Popconfirm title="¿Cancelar el pedido?" onConfirm={() => cancelar(p.id)}>
                  <a>Cancelar</a>
                </Popconfirm>
              ),
          },
        ]}
      />
    </>
  )
}
