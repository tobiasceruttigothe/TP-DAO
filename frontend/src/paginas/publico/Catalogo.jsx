import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Button, List, Table, Tag, Typography } from 'antd'
import { librosApi } from '../../api'
import useListado from '../../hooks/useListado'
import useSesion from '../../sesion/useSesion'
import Buscador from '../../componentes/Buscador'
import ModalPedido from '../../componentes/ModalPedido'

function DisponibilidadLibro({ libroId }) {
  const [datos, setDatos] = useState(null)

  useEffect(() => {
    librosApi.disponibilidad(libroId).then(setDatos).catch(() => setDatos({ sedes: [] }))
  }, [libroId])

  if (datos === null) return <Typography.Text type="secondary">Consultando...</Typography.Text>
  if (!datos.sedes.length) return <Typography.Text type="secondary">No hay ejemplares en la red.</Typography.Text>
  return (
    <List
      size="small"
      dataSource={datos.sedes}
      renderItem={(s) => (
        <List.Item>
          {s.sede}
          {s.disponibles > 0 ? <Tag color="green">{s.disponibles} disponible(s)</Tag> : <Tag>Sin ejemplares libres</Tag>}
        </List.Item>
      )}
    />
  )
}

/** Catalogo publico: cualquiera puede buscar; para pedir un libro hay que ser socio. */
export default function Catalogo() {
  const { usuario, esSocio } = useSesion()
  const navegar = useNavigate()
  const [q, setQ] = useState()
  const [pidiendo, setPidiendo] = useState(null)
  const { items, cargando, paginacion } = useListado(librosApi.listar, { q })

  function pedir(libro) {
    if (esSocio) setPidiendo(libro)
    else navegar('/ingresar?volver=/')
  }

  return (
    <>
      <Typography.Title level={3}>Catálogo de la red</Typography.Title>
      {!usuario && (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message="Cualquiera puede consultar el catálogo. Para pedir un libro, ver tus préstamos o tu historial, ingresá con tu cuenta de socio."
        />
      )}
      <Buscador size="large" placeholder="Buscá por título o autor" onBuscar={setQ} style={{ marginBottom: 16 }} />
      <Table
        rowKey="id"
        loading={cargando}
        dataSource={items}
        pagination={paginacion}
        scroll={{ x: true }}
        expandable={{
          expandRowByClick: true,
          expandedRowRender: (libro) => <DisponibilidadLibro libroId={libro.id} />,
        }}
        columns={[
          { title: 'Título', dataIndex: 'titulo' },
          { title: 'Autor', dataIndex: 'autor' },
          { title: 'Género', dataIndex: 'genero', responsive: ['md'] },
          {
            title: '',
            key: 'pedir',
            align: 'right',
            render: (_, libro) =>
              usuario?.rol === 'ADMIN' ? null : (
                <Button
                  size="small"
                  onClick={(evento) => {
                    evento.stopPropagation()
                    pedir(libro)
                  }}
                >
                  Pedir
                </Button>
              ),
          },
        ]}
      />
      <Typography.Text type="secondary">Tocá un libro para ver en qué sedes está disponible.</Typography.Text>

      <ModalPedido
        libro={pidiendo}
        onCerrar={() => setPidiendo(null)}
        onPedido={() => {
          setPidiendo(null)
          navegar('/socio/pedidos')
        }}
      />
    </>
  )
}
