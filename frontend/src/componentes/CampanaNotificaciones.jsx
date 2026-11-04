import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Badge, Button, Empty, List, Popover, Typography } from 'antd'
import { BellOutlined } from '@ant-design/icons'
import { notificacionesApi } from '../api'
import { fechaHora } from '../utiles/formato'

// Cada cuanto se consulta si llegaron notificaciones nuevas
const INTERVALO_MS = 30_000

/** Campana con la cantidad de notificaciones sin leer y las ultimas recibidas. */
export default function CampanaNotificaciones({ verTodas }) {
  const navegar = useNavigate()
  const [noLeidas, setNoLeidas] = useState(0)
  const [ultimas, setUltimas] = useState(null)
  const [abierta, setAbierta] = useState(false)

  const contar = useCallback(() => {
    notificacionesApi
      .noLeidas()
      .then((r) => setNoLeidas(r.no_leidas))
      .catch(() => {})
  }, [])

  useEffect(() => {
    contar()
    const intervalo = setInterval(contar, INTERVALO_MS)
    return () => clearInterval(intervalo)
  }, [contar])

  async function abrir(visible) {
    setAbierta(visible)
    if (visible) {
      setUltimas(null)
      const pagina = await notificacionesApi.listar({ tamanio: 6 }).catch(() => ({ items: [] }))
      setUltimas(pagina.items)
    }
  }

  async function elegir(notificacion) {
    setAbierta(false)
    if (!notificacion.leida) {
      await notificacionesApi.marcarLeida(notificacion.id).catch(() => {})
      contar()
    }
    navegar(notificacion.enlace || verTodas)
  }

  async function leerTodas() {
    await notificacionesApi.leerTodas().catch(() => {})
    setUltimas((lista) => lista?.map((n) => ({ ...n, leida: true })))
    contar()
  }

  const contenido = (
    <div style={{ width: 340 }}>
      <List
        size="small"
        loading={ultimas === null}
        dataSource={ultimas ?? []}
        locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Sin notificaciones" /> }}
        renderItem={(n) => (
          <List.Item style={{ cursor: 'pointer', background: n.leida ? undefined : '#e6f4ff' }} onClick={() => elegir(n)}>
            <List.Item.Meta
              title={<Typography.Text strong={!n.leida}>{n.titulo}</Typography.Text>}
              description={
                <>
                  <Typography.Paragraph ellipsis={{ rows: 2 }} style={{ marginBottom: 0 }}>
                    {n.mensaje}
                  </Typography.Paragraph>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {fechaHora(n.fecha)}
                  </Typography.Text>
                </>
              }
            />
          </List.Item>
        )}
      />
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 8 }}>
        <Button size="small" type="link" disabled={!noLeidas} onClick={leerTodas}>
          Marcar todas como leídas
        </Button>
        <Button
          size="small"
          type="link"
          onClick={() => {
            setAbierta(false)
            navegar(verTodas)
          }}
        >
          Ver todas
        </Button>
      </div>
    </div>
  )

  return (
    <Popover trigger="click" placement="bottomRight" title="Notificaciones" content={contenido} open={abierta} onOpenChange={abrir}>
      <Badge count={noLeidas} size="small">
        <Button type="text" shape="circle" icon={<BellOutlined style={{ fontSize: 18 }} />} aria-label="Notificaciones" />
      </Badge>
    </Popover>
  )
}
