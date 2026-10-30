import { useNavigate } from 'react-router-dom'
import { Button, Card, Col, Row, Statistic, Table, Tag } from 'antd'
import { PlusOutlined } from '@ant-design/icons'
import { reportesApi } from '../../api'
import useCarga from '../../hooks/useCarga'
import Encabezado from '../../componentes/Encabezado'
import { diasHasta, fecha, fechaHora, moneda } from '../../utiles/formato'

async function cargarResumen() {
  const [activos, vencidos, envios] = await Promise.all([
    reportesApi.activosYTransito(),
    reportesApi.vencidosYMultas(),
    reportesApi.envios(),
  ])
  return { activos, vencidos, envios }
}

function Vencimiento({ valor }) {
  const dias = diasHasta(valor)
  if (dias < 0) return <Tag color="red">Vencido hace {-dias} d</Tag>
  if (dias <= 3) return <Tag color="orange">Vence en {dias} d</Tag>
  return fecha(valor)
}

export default function Inicio() {
  const navegar = useNavigate()
  const { datos, cargando } = useCarga(cargarResumen)
  const activos = datos?.activos
  const vencidos = datos?.vencidos
  const envios = datos?.envios

  return (
    <>
      <Encabezado titulo="Inicio" descripcion="Estado general de la red">
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navegar('/prestamos/nuevo')}>
          Nuevo préstamo
        </Button>
      </Encabezado>

      <Row gutter={[16, 16]}>
        <Col xs={12} lg={6}>
          <Card loading={cargando}>
            <Statistic title="Préstamos activos" value={activos?.total_prestamos_activos} />
          </Card>
        </Col>
        <Col xs={12} lg={6}>
          <Card loading={cargando}>
            <Statistic title="Ejemplares en tránsito" value={activos?.total_en_transito} />
          </Card>
        </Col>
        <Col xs={12} lg={6}>
          <Card loading={cargando}>
            <Statistic title="Préstamos vencidos" value={vencidos?.total_prestamos_vencidos} />
          </Card>
        </Col>
        <Col xs={12} lg={6}>
          <Card loading={cargando}>
            <Statistic title="Multas pendientes" value={moneda(vencidos?.total_multas_pendientes)} />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
        <Col xs={24} xl={14}>
          <Card title="Próximos vencimientos" extra={<a onClick={() => navegar('/prestamos')}>Ver préstamos</a>}>
            <Table
              size="small"
              rowKey="prestamo_id"
              loading={cargando}
              dataSource={activos?.prestamos_activos ?? []}
              pagination={{ pageSize: 6, hideOnSinglePage: true }}
              columns={[
                { title: 'Socio', dataIndex: 'socio' },
                { title: 'Libro', dataIndex: 'libro' },
                { title: 'Sede', dataIndex: 'sede_retiro' },
                { title: 'Vence', dataIndex: 'fecha_vencimiento', render: (v) => <Vencimiento valor={v} /> },
              ]}
            />
          </Card>
        </Col>
        <Col xs={24} xl={10}>
          <Card title="En viaje entre sedes" extra={<a onClick={() => navegar('/remitos')}>Ver remitos</a>}>
            <Table
              size="small"
              rowKey="remito"
              loading={cargando}
              dataSource={activos?.en_transito ?? []}
              pagination={{ pageSize: 6, hideOnSinglePage: true }}
              columns={[
                { title: 'Remito', dataIndex: 'remito' },
                { title: 'Destino', dataIndex: 'sede_destino' },
                { title: 'Despachado', dataIndex: 'fecha_despacho', render: fechaHora },
              ]}
            />
          </Card>
          <Card style={{ marginTop: 16 }} loading={cargando}>
            <Row>
              <Col span={12}>
                <Statistic title="Envíos exitosos" value={envios?.tasa_exito} suffix="%" />
              </Col>
              <Col span={12}>
                <Statistic title="Con incidencias" value={envios?.tasa_incidencias} suffix="%" />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>
    </>
  )
}
