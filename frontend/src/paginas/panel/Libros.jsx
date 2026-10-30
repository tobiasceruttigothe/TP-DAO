import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button, Input, Space, Table } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { librosApi } from '../../api'
import useListado from '../../hooks/useListado'
import Encabezado from '../../componentes/Encabezado'
import FormularioLibro from './FormularioLibro'

export default function Libros() {
  const navegar = useNavigate()
  const [q, setQ] = useState()
  const { items, cargando, paginacion, recargar } = useListado(librosApi.listar, { q })
  const [edicion, setEdicion] = useState(null)

  return (
    <>
      <Encabezado titulo="Catálogo" descripcion="Libros de la red. Cada libro puede tener ejemplares en varias sedes.">
        <Input.Search allowClear placeholder="Título o autor" onSearch={setQ} style={{ width: 260 }} />
        <Button type="primary" icon={<PlusOutlined />} onClick={() => setEdicion({})}>
          Nuevo libro
        </Button>
      </Encabezado>

      <Table
        rowKey="id"
        loading={cargando}
        dataSource={items}
        pagination={paginacion}
        scroll={{ x: true }}
        columns={[
          { title: 'Título', dataIndex: 'titulo', render: (t, l) => <a onClick={() => navegar(`/libros/${l.id}`)}>{t}</a> },
          { title: 'Autor', dataIndex: 'autor' },
          { title: 'ISBN', dataIndex: 'isbn' },
          { title: 'Editorial', dataIndex: 'editorial' },
          { title: 'Año', dataIndex: 'anio_publicacion' },
          { title: 'Género', dataIndex: 'genero' },
          {
            title: '',
            key: 'acciones',
            render: (_, libro) => (
              <Space>
                <a onClick={() => navegar(`/libros/${libro.id}`)}>Ejemplares</a>
                <a onClick={() => setEdicion(libro)}>Editar</a>
              </Space>
            ),
          },
        ]}
      />

      <FormularioLibro
        libro={edicion}
        onCerrar={() => setEdicion(null)}
        onGuardado={() => {
          setEdicion(null)
          recargar()
        }}
      />
    </>
  )
}
