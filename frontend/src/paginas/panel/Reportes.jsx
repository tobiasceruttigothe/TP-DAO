import { useCallback, useState } from 'react'
import { Card, Col, DatePicker, Flex, InputNumber, Row, Statistic, Table, Tabs, Tag } from 'antd'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { reportesApi } from '../../api'
import useCarga from '../../hooks/useCarga'
import Encabezado from '../../componentes/Encabezado'
import { fecha, fechaApi, fechaHora, moneda } from '../../utiles/formato'

// Paleta categorica en orden fijo (validada para daltonismo). La serie unica usa el primer color.
const COLORES = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100']
const GRILLA = '#f0f0f0'
const EJE = { fontSize: 12, fill: '#595959' }

function FiltroFechas({ onChange }) {
  return (
    <DatePicker.RangePicker
      format="DD/MM/YYYY"
      allowEmpty={[true, true]}
      onChange={(rango) => onChange({ desde: fechaApi(rango?.[0]), hasta: fechaApi(rango?.[1]) })}
    />
  )
}

function ActivosYTransito() {
  const { datos, cargando } = useCarga(reportesApi.activosYTransito)
  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} xl={14}>
        <Card title={`Préstamos activos (${datos?.total_prestamos_activos ?? 0})`}>
          <Table
            size="small"
            rowKey="prestamo_id"
            loading={cargando}
            dataSource={datos?.prestamos_activos ?? []}
            pagination={{ pageSize: 10, hideOnSinglePage: true }}
            scroll={{ x: true }}
            columns={[
              { title: 'Socio', dataIndex: 'socio' },
              { title: 'Libro', dataIndex: 'libro' },
              { title: 'Ejemplar', dataIndex: 'codigo_ejemplar' },
              { title: 'Retira en', dataIndex: 'sede_retiro' },
              {
                title: 'Vence',
                dataIndex: 'fecha_vencimiento',
                render: (v, p) => (p.vencido ? <Tag color="red">{fecha(v)} · vencido</Tag> : fecha(v)),
              },
            ]}
          />
        </Card>
      </Col>
      <Col xs={24} xl={10}>
        <Card title={`Material en tránsito (${datos?.total_en_transito ?? 0})`}>
          <Table
            size="small"
            rowKey="remito"
            loading={cargando}
            dataSource={datos?.en_transito ?? []}
            pagination={{ pageSize: 10, hideOnSinglePage: true }}
            scroll={{ x: true }}
            columns={[
              { title: 'Remito', dataIndex: 'remito' },
              { title: 'Libro', dataIndex: 'libro' },
              { title: 'Destino', dataIndex: 'sede_destino' },
              { title: 'Despachado', dataIndex: 'fecha_despacho', render: fechaHora },
              { title: 'Horas de viaje', dataIndex: 'horas_en_viaje' },
            ]}
          />
        </Card>
      </Col>
    </Row>
  )
}

function VencidosYMultas() {
  const [dia, setDia] = useState()
  const cargar = useCallback((f) => reportesApi.vencidosYMultas({ fecha: f }), [])
  const { datos, cargando } = useCarga(cargar, [dia])

  return (
    <>
      <Flex gap={16} wrap align="center" style={{ marginBottom: 16 }}>
        <span>Calcular a la fecha:</span>
        <DatePicker format="DD/MM/YYYY" placeholder="Hoy" onChange={(d) => setDia(fechaApi(d))} />
      </Flex>
      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} md={8}>
          <Card loading={cargando}>
            <Statistic title="Préstamos vencidos" value={datos?.total_prestamos_vencidos} />
          </Card>
        </Col>
        <Col xs={12} md={8}>
          <Card loading={cargando}>
            <Statistic title="Multas pendientes (estimadas)" value={moneda(datos?.total_multas_pendientes)} />
          </Card>
        </Col>
        <Col xs={12} md={8}>
          <Card loading={cargando}>
            <Statistic title="Multas cobradas" value={moneda(datos?.total_multas_cobradas)} />
          </Card>
        </Col>
      </Row>
      <Table
        rowKey="socio_id"
        loading={cargando}
        dataSource={datos?.socios ?? []}
        pagination={{ pageSize: 10, hideOnSinglePage: true }}
        expandable={{
          rowExpandable: (s) => s.prestamos_vencidos.length > 0,
          expandedRowRender: (s) => (
            <Table
              size="small"
              rowKey="prestamo_id"
              dataSource={s.prestamos_vencidos}
              pagination={false}
              columns={[
                { title: 'Libro', dataIndex: 'libro' },
                { title: 'Venció', dataIndex: 'fecha_vencimiento', render: fecha },
                { title: 'Días de atraso', dataIndex: 'dias_atraso' },
                { title: 'Multa estimada', dataIndex: 'multa_estimada', render: moneda },
              ]}
            />
          ),
        }}
        columns={[
          { title: 'Socio', dataIndex: 'socio' },
          { title: 'DNI', dataIndex: 'dni' },
          { title: 'Vencidos', render: (_, s) => s.prestamos_vencidos.length },
          { title: 'Cobradas', dataIndex: 'multas_cobradas', render: moneda },
          { title: 'Pendientes', dataIndex: 'multas_pendientes', render: moneda },
          { title: 'Total acumulado', dataIndex: 'total_acumulado', render: (v) => <b>{moneda(v)}</b> },
        ]}
      />
    </>
  )
}

function MasSolicitados() {
  const [filtros, setFiltros] = useState({ limite: 10 })
  const { datos, cargando } = useCarga(reportesApi.librosMasSolicitados, [filtros])
  const filas = datos ?? []

  return (
    <>
      <Flex gap={16} wrap align="center" style={{ marginBottom: 16 }}>
        <FiltroFechas onChange={(rango) => setFiltros((f) => ({ ...f, ...rango }))} />
        <span>
          Mostrar{' '}
          <InputNumber min={1} max={50} value={filtros.limite} onChange={(limite) => setFiltros((f) => ({ ...f, limite: limite || 10 }))} />{' '}
          libros
        </span>
      </Flex>
      <Row gutter={[16, 16]}>
        <Col xs={24} xl={14}>
          <Card title="Préstamos inter-sede por libro" loading={cargando}>
            <ResponsiveContainer width="100%" height={Math.max(160, filas.length * 36 + 40)}>
              <BarChart data={filas} layout="vertical" margin={{ left: 8, right: 24 }}>
                <CartesianGrid horizontal={false} stroke={GRILLA} />
                <XAxis type="number" allowDecimals={false} tick={EJE} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="titulo" width={170} tick={EJE} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: '#f5f5f5' }} formatter={(v) => [v, 'Préstamos']} />
                <Bar dataKey="cantidad_prestamos" fill={COLORES[0]} radius={[0, 4, 4, 0]} maxBarSize={22} />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} xl={10}>
          <Card title="Detalle">
            <Table
              size="small"
              rowKey="libro_id"
              loading={cargando}
              dataSource={filas}
              pagination={false}
              columns={[
                { title: '#', render: (_, __, i) => i + 1, width: 40 },
                { title: 'Libro', dataIndex: 'titulo' },
                { title: 'Autor', dataIndex: 'autor' },
                { title: 'Préstamos', dataIndex: 'cantidad_prestamos' },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </>
  )
}

// Los estados del ejemplar se agrupan en cuatro para que el grafico se pueda leer
const GRUPOS = [
  { clave: 'disponibles', texto: 'Disponibles', estados: ['DISPONIBLE'] },
  { clave: 'en_uso', texto: 'Prestados o reservados', estados: ['PRESTADO', 'RESERVADO'] },
  { clave: 'en_transito', texto: 'En tránsito', estados: ['EN_TRANSITO'] },
  { clave: 'fuera', texto: 'Fuera de circulación', estados: ['EN_REPARACION', 'EXTRAVIADO'] },
]

function DisponibilidadSedes() {
  const { datos, cargando } = useCarga(reportesApi.disponibilidadSedes)
  const filas = (datos ?? []).map((sede) => ({
    ...sede,
    ...Object.fromEntries(
      GRUPOS.map((g) => [g.clave, g.estados.reduce((suma, e) => suma + (sede.por_estado[e] ?? 0), 0)]),
    ),
  }))

  return (
    <Row gutter={[16, 16]}>
      <Col span={24}>
        <Card title="Ejemplares por sede" loading={cargando}>
          <ResponsiveContainer width="100%" height={Math.max(180, filas.length * 48 + 70)}>
            <BarChart data={filas} layout="vertical" margin={{ left: 8, right: 24 }}>
              <CartesianGrid horizontal={false} stroke={GRILLA} />
              <XAxis type="number" allowDecimals={false} tick={EJE} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="sede" width={130} tick={EJE} axisLine={false} tickLine={false} />
              <Tooltip cursor={{ fill: '#f5f5f5' }} />
              <Legend
                itemSorter={null}
                wrapperStyle={{ fontSize: 12 }}
                formatter={(texto) => <span style={{ color: '#595959' }}>{texto}</span>}
              />
              {GRUPOS.map((g, i) => (
                <Bar
                  key={g.clave}
                  dataKey={g.clave}
                  name={g.texto}
                  stackId="estado"
                  fill={COLORES[i]}
                  stroke="#fff"
                  strokeWidth={2}
                  maxBarSize={26}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </Col>
      <Col span={24}>
        <Card title="Detalle">
          <Table
            size="small"
            rowKey="sede_id"
            loading={cargando}
            dataSource={filas}
            pagination={false}
            scroll={{ x: true }}
            columns={[
              { title: 'Sede', dataIndex: 'sede', render: (n, s) => (s.activa ? n : <>{n} <Tag>baja</Tag></>) },
              { title: 'Títulos', dataIndex: 'titulos_distintos' },
              { title: 'Ejemplares', dataIndex: 'total_ejemplares' },
              ...GRUPOS.map((g) => ({ title: g.texto, dataIndex: g.clave })),
              { title: '% disponible', dataIndex: 'porcentaje_disponible', render: (p) => `${p}%` },
            ]}
          />
        </Card>
      </Col>
    </Row>
  )
}

function Envios() {
  const [rango, setRango] = useState({})
  const { datos, cargando } = useCarga(reportesApi.envios, [rango])
  const resultados = datos
    ? [
        { resultado: 'Recibidos sin problemas', cantidad: datos.recibidos_ok },
        { resultado: 'Recibidos con daño', cantidad: datos.recibidos_con_danio },
        { resultado: 'Destruidos', cantidad: datos.recibidos_destruidos },
        { resultado: 'Extraviados', cantidad: datos.extraviados },
        { resultado: 'Cancelados', cantidad: datos.cancelados },
        { resultado: 'En curso', cantidad: datos.en_curso },
      ]
    : []

  return (
    <>
      <Flex style={{ marginBottom: 16 }}>
        <FiltroFechas onChange={setRango} />
      </Flex>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Flex vertical gap={16}>
            <Card loading={cargando}>
              <Statistic title="Envíos exitosos" value={datos?.tasa_exito} suffix="%" />
              <div style={{ color: '#8c8c8c', fontSize: 12 }}>Recibidos sin problemas sobre los que viajaron</div>
            </Card>
            <Card loading={cargando}>
              <Statistic title="Envíos con incidencias" value={datos?.tasa_incidencias} suffix="%" />
              <div style={{ color: '#8c8c8c', fontSize: 12 }}>Daños, destrucciones y extravíos</div>
            </Card>
          </Flex>
        </Col>
        <Col xs={24} lg={16}>
          <Card title="Remitos por resultado" loading={cargando}>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={resultados} layout="vertical" margin={{ left: 8, right: 24 }}>
                <CartesianGrid horizontal={false} stroke={GRILLA} />
                <XAxis type="number" allowDecimals={false} tick={EJE} axisLine={false} tickLine={false} />
                <YAxis type="category" dataKey="resultado" width={170} tick={EJE} axisLine={false} tickLine={false} />
                <Tooltip cursor={{ fill: '#f5f5f5' }} formatter={(v) => [v, 'Remitos']} />
                <Bar dataKey="cantidad" fill={COLORES[0]} radius={[0, 4, 4, 0]} maxBarSize={22} />
              </BarChart>
            </ResponsiveContainer>
            <Table
              size="small"
              rowKey="resultado"
              dataSource={resultados}
              pagination={false}
              columns={[
                { title: 'Resultado', dataIndex: 'resultado' },
                { title: 'Remitos', dataIndex: 'cantidad' },
              ]}
            />
          </Card>
        </Col>
      </Row>
    </>
  )
}

function MovimientosSedes() {
  const [rango, setRango] = useState({})
  const { datos, cargando } = useCarga(reportesApi.movimientosSedes, [rango])
  return (
    <>
      <Flex style={{ marginBottom: 16 }}>
        <FiltroFechas onChange={setRango} />
      </Flex>
      <Table
        rowKey={(m) => `${m.sede_origen}-${m.sede_destino}`}
        loading={cargando}
        dataSource={datos ?? []}
        pagination={false}
        scroll={{ x: true }}
        columns={[
          { title: 'Origen', dataIndex: 'sede_origen' },
          { title: 'Destino', dataIndex: 'sede_destino' },
          { title: 'Envíos', dataIndex: 'envios', sorter: (a, b) => a.envios - b.envios },
          { title: 'Recibidos', dataIndex: 'recibidos' },
          { title: 'Incidencias', dataIndex: 'incidencias' },
          {
            title: 'Tránsito promedio',
            dataIndex: 'promedio_horas_transito',
            sorter: (a, b) => (a.promedio_horas_transito ?? 0) - (b.promedio_horas_transito ?? 0),
            render: (h) => (h === null ? '-' : `${h} h`),
          },
        ]}
      />
    </>
  )
}

export default function Reportes() {
  return (
    <>
      <Encabezado titulo="Reportes" />
      <Tabs
        items={[
          { key: 'activos', label: 'Activos y en tránsito', children: <ActivosYTransito /> },
          { key: 'vencidos', label: 'Vencidos y multas', children: <VencidosYMultas /> },
          { key: 'solicitados', label: 'Más solicitados', children: <MasSolicitados /> },
          { key: 'disponibilidad', label: 'Disponibilidad por sede', children: <DisponibilidadSedes /> },
          { key: 'envios', label: 'Envíos e incidencias', children: <Envios /> },
          { key: 'movimientos', label: 'Movimientos entre sedes', children: <MovimientosSedes /> },
        ]}
      />
    </>
  )
}
