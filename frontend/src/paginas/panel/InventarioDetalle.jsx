import { useRef, useState } from 'react'
import { useParams } from 'react-router-dom'
import { Alert, Button, Card, Col, Input, List, Popconfirm, Progress, Row, Statistic, Table, Tabs, Tag, Typography } from 'antd'
import { BarcodeOutlined } from '@ant-design/icons'
import { ejemplaresApi, inventariosApi } from '../../api'
import useCarga from '../../hooks/useCarga'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import { fechaHora } from '../../utiles/formato'

const COLOR_RESULTADO = { ENCONTRADO: 'green', FUERA_DE_LUGAR: 'orange', DESCONOCIDO: 'red' }
const TEXTO_RESULTADO = { ENCONTRADO: 'Encontrado', FUERA_DE_LUGAR: 'Fuera de lugar', DESCONOCIDO: 'Desconocido' }

/**
 * Lector de codigos: un lector de codigo de barras funciona como un teclado que escribe el
 * codigo y aprieta Enter, asi que alcanza con un campo que quede siempre con el foco.
 */
function Lector({ inventarioId, onLeido }) {
  const [codigo, setCodigo] = useState('')
  const [lecturas, setLecturas] = useState([])
  const [error, setError] = useState(null)
  const campo = useRef(null)
  const { ejecutar } = useAccion()

  async function registrar() {
    const texto = codigo.trim()
    if (!texto) return
    setCodigo('')
    setError(null)
    try {
      const resultado = await inventariosApi.registrar(inventarioId, texto)
      setLecturas((anteriores) => [resultado, ...anteriores].slice(0, 15))
      onLeido()
    } catch (e) {
      setError(e.message)
    } finally {
      campo.current?.focus()
    }
  }

  async function deshacer(lectura) {
    if (await ejecutar(() => inventariosApi.quitar(inventarioId, lectura.item_id), `Se quitó ${lectura.codigo}`)) {
      setLecturas((anteriores) => anteriores.filter((l) => l.item_id !== lectura.item_id))
      onLeido()
    }
    campo.current?.focus()
  }

  return (
    <Card title="Leer códigos" style={{ marginBottom: 16 }}>
      <Input
        ref={campo}
        size="large"
        autoFocus
        prefix={<BarcodeOutlined />}
        placeholder="Escaneá el código o escribilo y apretá Enter"
        value={codigo}
        onChange={(e) => setCodigo(e.target.value)}
        onPressEnter={registrar}
        maxLength={30}
      />
      {error && <Alert type="warning" showIcon message={error} style={{ marginTop: 12 }} />}
      {lecturas.length > 0 && (
        <List
          size="small"
          style={{ marginTop: 12 }}
          header={<Typography.Text type="secondary">Últimas lecturas</Typography.Text>}
          dataSource={lecturas}
          renderItem={(l) => (
            <List.Item actions={[<a key="deshacer" onClick={() => deshacer(l)}>Deshacer</a>]}>
              <Tag color={COLOR_RESULTADO[l.resultado]}>{TEXTO_RESULTADO[l.resultado]}</Tag>
              <Typography.Text code>{l.codigo}</Typography.Text> {l.detalle}
            </List.Item>
          )}
        />
      )}
    </Card>
  )
}

export default function InventarioDetalle() {
  const { id } = useParams()
  const inventarioId = Number(id)
  const { datos: inventario, cargando, recargar } = useCarga(inventariosApi.obtener, [inventarioId])
  const { ejecutar, ejecutando } = useAccion()

  if (!inventario) return <Card loading={cargando} />

  const { informe, esperados } = inventario
  const enCurso = inventario.estado === 'EN_CURSO'
  const avance = esperados ? Math.round((informe.encontrados.length / esperados) * 100) : 100

  async function accion(operacion, mensaje) {
    if (await ejecutar(operacion, mensaje)) recargar()
  }

  const columnas = (extra = []) => [
    { title: 'Código', dataIndex: 'codigo', render: (c) => <Typography.Text code>{c}</Typography.Text> },
    { title: 'Libro', dataIndex: 'titulo', render: (t) => t ?? '-' },
    { title: 'Estado en el sistema', dataIndex: 'estado', render: (v) => <EstadoTag tipo="ejemplar" valor={v} /> },
    { title: 'Detalle', dataIndex: 'detalle', render: (d) => d ?? '-' },
    ...extra,
  ]

  const accionFaltante = {
    title: '',
    key: 'accion',
    render: (_, fila) =>
      ['DISPONIBLE', 'EN_REPARACION'].includes(fila.estado) && (
        <Popconfirm
          title={`¿Marcar ${fila.codigo} como extraviado?`}
          description="Deja de figurar como disponible hasta que aparezca."
          onConfirm={() => accion(() => ejemplaresApi.marcarExtraviado(fila.ejemplar_id), 'Ejemplar marcado como extraviado')}
        >
          <a>Marcar extraviado</a>
        </Popconfirm>
      ),
  }

  const accionFueraDeLugar = {
    title: '',
    key: 'accion',
    render: (_, fila) =>
      fila.estado === 'EXTRAVIADO' && (
        <a onClick={() => accion(() => ejemplaresApi.marcarRecuperado(fila.ejemplar_id), 'Ejemplar recuperado')}>Recuperar</a>
      ),
  }

  const tabla = (filas, extra, vacio) => (
    <Table size="small" rowKey="codigo" dataSource={filas} columns={columnas(extra)} pagination={{ pageSize: 10, hideOnSinglePage: true }} locale={{ emptyText: vacio }} scroll={{ x: true }} />
  )

  return (
    <>
      <Encabezado
        titulo={`Inventario de ${inventario.sede.nombre}`}
        descripcion={`Iniciado el ${fechaHora(inventario.fecha_inicio)}${inventario.observacion ? ` · ${inventario.observacion}` : ''}`}
      >
        <EstadoTag tipo="inventario" valor={inventario.estado} />
        {enCurso && (
          <Popconfirm
            title="¿Cerrar el inventario?"
            description="El informe queda guardado tal como está y no se pueden leer más códigos."
            onConfirm={() => accion(() => inventariosApi.cerrar(inventarioId), 'Inventario cerrado')}
          >
            <Button type="primary" loading={ejecutando}>
              Cerrar inventario
            </Button>
          </Popconfirm>
        )}
      </Encabezado>

      {!enCurso && (
        <Alert
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
          message={`Cerrado el ${fechaHora(inventario.fecha_cierre)}. El informe muestra cómo estaba todo en ese momento.`}
        />
      )}

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={24} md={6}>
          <Card>
            <Progress type="circle" percent={avance} size={90} />
            <Typography.Paragraph type="secondary" style={{ marginTop: 8, marginBottom: 0 }}>
              {informe.encontrados.length} de {esperados} esperados
            </Typography.Paragraph>
          </Card>
        </Col>
        <Col xs={8} md={6}>
          <Card>
            <Statistic title="Faltantes" value={informe.faltantes.length} valueStyle={{ color: informe.faltantes.length ? '#cf1322' : undefined }} />
          </Card>
        </Col>
        <Col xs={8} md={6}>
          <Card>
            <Statistic title="Fuera de lugar" value={informe.fuera_de_lugar.length} valueStyle={{ color: informe.fuera_de_lugar.length ? '#d46b08' : undefined }} />
          </Card>
        </Col>
        <Col xs={8} md={6}>
          <Card>
            <Statistic title="Desconocidos" value={informe.desconocidos.length} />
          </Card>
        </Col>
      </Row>

      {enCurso && <Lector inventarioId={inventarioId} onLeido={recargar} />}

      <Card>
        <Tabs
          items={[
            {
              key: 'faltantes',
              label: `Faltantes (${informe.faltantes.length})`,
              children: tabla(informe.faltantes, [accionFaltante], 'No falta ningún ejemplar'),
            },
            {
              key: 'fuera',
              label: `Fuera de lugar (${informe.fuera_de_lugar.length})`,
              children: tabla(informe.fuera_de_lugar, [accionFueraDeLugar], 'Nada fuera de lugar'),
            },
            {
              key: 'desconocidos',
              label: `Desconocidos (${informe.desconocidos.length})`,
              children: tabla(informe.desconocidos, [], 'Ningún código desconocido'),
            },
            {
              key: 'encontrados',
              label: `Encontrados (${informe.encontrados.length})`,
              children: tabla(informe.encontrados, [], 'Todavía no se leyó ningún código'),
            },
          ]}
        />
      </Card>
    </>
  )
}
