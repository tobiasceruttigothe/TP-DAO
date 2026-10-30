import { useEffect, useState } from 'react'
import { Alert, Card, Descriptions, Empty, Input, List, Table, Tabs, Tag, Typography } from 'antd'
import { librosApi, prestamosApi, reservasApi, sociosApi } from '../../api'
import useListado from '../../hooks/useListado'
import useAccion from '../../hooks/useAccion'
import EstadoTag from '../../componentes/EstadoTag'
import { diasHasta, fecha } from '../../utiles/formato'

const PRESTAMOS_EN_CURSO = ['SOLICITADO', 'EN_TRANSITO', 'ACTIVO']
const RESERVAS_ACTIVAS = ['PENDIENTE', 'DISPONIBLE']

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

function BuscarLibros() {
  const [q, setQ] = useState()
  const { items, cargando, paginacion } = useListado(librosApi.listar, { q })
  return (
    <>
      <Input.Search
        allowClear
        enterButton="Buscar"
        size="large"
        placeholder="Título o autor"
        onSearch={setQ}
        style={{ marginBottom: 16 }}
      />
      <Table
        rowKey="id"
        loading={cargando}
        dataSource={items}
        pagination={paginacion}
        expandable={{
          expandRowByClick: true,
          expandedRowRender: (libro) => <DisponibilidadLibro libroId={libro.id} />,
        }}
        columns={[
          { title: 'Título', dataIndex: 'titulo' },
          { title: 'Autor', dataIndex: 'autor' },
          { title: 'Género', dataIndex: 'genero' },
        ]}
      />
      <Typography.Text type="secondary">Tocá un libro para ver en qué sedes está disponible.</Typography.Text>
    </>
  )
}

function Vencimiento({ prestamo }) {
  if (prestamo.estado !== 'ACTIVO') return <EstadoTag tipo="prestamo" valor={prestamo.estado} />
  const dias = diasHasta(prestamo.fecha_vencimiento)
  if (dias < 0) return <Tag color="red">Vencido hace {-dias} día(s)</Tag>
  if (dias === 0) return <Tag color="orange">Vence hoy</Tag>
  return <Tag color={dias <= 3 ? 'orange' : 'blue'}>Vence el {fecha(prestamo.fecha_vencimiento)}</Tag>
}

async function consultarSocio(dni) {
  // La busqueda es por coincidencia parcial: nos quedamos con el DNI exacto
  const { items } = await sociosApi.listar({ q: dni, tamanio: 50 })
  const socio = items.find((s) => s.dni === dni)
  if (!socio) return { socio: null }
  const [prestamos, reservas] = await Promise.all([
    prestamosApi.listar({ socio_id: socio.id, tamanio: 100 }),
    reservasApi.listar({ socio_id: socio.id, tamanio: 100 }),
  ])
  return {
    socio,
    prestamos: prestamos.items.filter((p) => PRESTAMOS_EN_CURSO.includes(p.estado)),
    reservas: reservas.items.filter((r) => RESERVAS_ACTIVAS.includes(r.estado)),
  }
}

function MisPrestamos() {
  const [resultado, setResultado] = useState(null)
  const { ejecutar, ejecutando } = useAccion()

  async function buscar(dni) {
    const limpio = dni.replace(/\D/g, '')
    if (!limpio) return
    const datos = await ejecutar(() => consultarSocio(limpio))
    if (datos) setResultado(datos)
  }

  return (
    <>
      <Input.Search
        size="large"
        enterButton="Consultar"
        placeholder="Ingresá tu DNI"
        inputMode="numeric"
        loading={ejecutando}
        onSearch={buscar}
        style={{ marginBottom: 16, maxWidth: 400 }}
      />

      {resultado && !resultado.socio && <Alert type="warning" showIcon message="No encontramos un socio con ese DNI." />}

      {resultado?.socio && (
        <>
          {!resultado.socio.habilitado && (
            <Alert
              type="error"
              showIcon
              style={{ marginBottom: 16 }}
              message="Tu cuenta está inhabilitada para nuevos préstamos."
              description="Acercate a cualquier sede para regularizar tu situación."
            />
          )}
          <Card title={`${resultado.socio.nombre} ${resultado.socio.apellido}`} style={{ marginBottom: 16 }}>
            <Descriptions
              size="small"
              column={1}
              items={[{ key: 'prestamos', label: 'Préstamos en curso', children: resultado.prestamos.length }]}
            />
          </Card>

          <Card title="Mis préstamos" style={{ marginBottom: 16 }}>
            {resultado.prestamos.length === 0 ? (
              <Empty description="No tenés préstamos en curso" />
            ) : (
              <List
                dataSource={resultado.prestamos}
                renderItem={(p) => (
                  <List.Item extra={<Vencimiento prestamo={p} />}>
                    <List.Item.Meta
                      title={p.ejemplar.libro.titulo}
                      description={
                        p.estado === 'ACTIVO'
                          ? `Retirado en ${p.sede_destino.nombre}`
                          : `En camino a ${p.sede_destino.nombre}`
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>

          <Card title="Mis reservas">
            {resultado.reservas.length === 0 ? (
              <Empty description="No tenés reservas activas" />
            ) : (
              <List
                dataSource={resultado.reservas}
                renderItem={(r) => (
                  <List.Item extra={<EstadoTag tipo="reserva" valor={r.estado} />}>
                    <List.Item.Meta
                      title={r.libro.titulo}
                      description={
                        r.estado === 'DISPONIBLE'
                          ? `Retiralo en ${r.sede.nombre} hasta el ${fecha(r.fecha_expiracion)}`
                          : `En espera de un ejemplar en ${r.sede.nombre}`
                      }
                    />
                  </List.Item>
                )}
              />
            )}
          </Card>
        </>
      )}
    </>
  )
}

export default function Consulta() {
  return (
    <Tabs
      size="large"
      items={[
        { key: 'catalogo', label: 'Buscar libros', children: <BuscarLibros /> },
        { key: 'prestamos', label: 'Mis préstamos y reservas', children: <MisPrestamos /> },
      ]}
    />
  )
}
