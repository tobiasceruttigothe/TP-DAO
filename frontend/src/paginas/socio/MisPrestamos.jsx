import { Alert, Card, Col, Empty, List, Popconfirm, Row, Statistic, Tag } from 'antd'
import { miApi } from '../../api'
import useCarga from '../../hooks/useCarga'
import useAccion from '../../hooks/useAccion'
import EstadoTag from '../../componentes/EstadoTag'
import { diasHasta, fecha, moneda } from '../../utiles/formato'

const PRESTAMOS_EN_CURSO = ['SOLICITADO', 'EN_TRANSITO', 'ACTIVO']
const RESERVAS_ACTIVAS = ['PENDIENTE', 'DISPONIBLE']

async function cargarResumen() {
  const [socio, prestamos, reservas] = await Promise.all([
    miApi.socio(),
    miApi.prestamos({ tamanio: 100 }),
    miApi.reservas({ tamanio: 100 }),
  ])
  return {
    socio,
    prestamos: prestamos.items.filter((p) => PRESTAMOS_EN_CURSO.includes(p.estado)),
    reservas: reservas.items.filter((r) => RESERVAS_ACTIVAS.includes(r.estado)),
  }
}

function Vencimiento({ prestamo }) {
  if (prestamo.estado !== 'ACTIVO') return <EstadoTag tipo="prestamo" valor={prestamo.estado} />
  const dias = diasHasta(prestamo.fecha_vencimiento)
  if (dias < 0) return <Tag color="red">Vencido hace {-dias} día(s) · multa {moneda(prestamo.multa_actual)}</Tag>
  if (dias === 0) return <Tag color="orange">Vence hoy</Tag>
  return <Tag color={dias <= 3 ? 'orange' : 'blue'}>Vence el {fecha(prestamo.fecha_vencimiento)}</Tag>
}

export default function MisPrestamos() {
  const { datos, cargando, recargar } = useCarga(cargarResumen)
  const { ejecutar } = useAccion()

  async function cancelarReserva(id) {
    if (await ejecutar(() => miApi.cancelarReserva(id), 'Reserva cancelada')) recargar()
  }

  if (cargando && !datos) return <Card loading />
  if (!datos) return null
  const { socio, prestamos, reservas } = datos

  return (
    <>
      {!socio.habilitado && (
        <Alert
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          message="Tu cuenta está inhabilitada para nuevos préstamos."
          description={`${socio.motivo_inhabilitacion ?? ''}. Acercate a cualquier sede para regularizar tu situación.`}
        />
      )}
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Préstamos en curso" value={prestamos.length} />
          </Card>
        </Col>
        <Col xs={12} md={6}>
          <Card>
            <Statistic title="Reservas activas" value={reservas.length} />
          </Card>
        </Col>
      </Row>

      <Card title="Mis préstamos" style={{ marginBottom: 16 }}>
        {prestamos.length === 0 ? (
          <Empty description="No tenés préstamos en curso" />
        ) : (
          <List
            dataSource={prestamos}
            renderItem={(p) => (
              <List.Item extra={<Vencimiento prestamo={p} />}>
                <List.Item.Meta
                  title={p.ejemplar.libro.titulo}
                  description={p.estado === 'ACTIVO' ? `Retirado en ${p.sede_destino.nombre}` : `En camino a ${p.sede_destino.nombre}`}
                />
              </List.Item>
            )}
          />
        )}
      </Card>

      <Card title="Mis reservas">
        {reservas.length === 0 ? (
          <Empty description="No tenés reservas activas" />
        ) : (
          <List
            dataSource={reservas}
            renderItem={(r) => (
              <List.Item
                actions={[
                  <Popconfirm key="cancelar" title="¿Cancelar la reserva?" onConfirm={() => cancelarReserva(r.id)}>
                    <a>Cancelar</a>
                  </Popconfirm>,
                ]}
                extra={<EstadoTag tipo="reserva" valor={r.estado} />}
              >
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
  )
}
