import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Badge, Button, List, Segmented, Typography } from 'antd'
import { notificacionesApi } from '../../api'
import useListado from '../../hooks/useListado'
import useAccion from '../../hooks/useAccion'
import Encabezado from '../../componentes/Encabezado'
import { fechaHora } from '../../utiles/formato'

/** Todas las notificaciones del usuario conectado (socio o administrador). */
export default function Notificaciones() {
  const navegar = useNavigate()
  const [soloNoLeidas, setSoloNoLeidas] = useState(false)
  const { items, cargando, paginacion, recargar } = useListado(notificacionesApi.listar, { solo_no_leidas: soloNoLeidas })
  const { ejecutar } = useAccion()

  async function abrir(n) {
    if (!n.leida) await ejecutar(() => notificacionesApi.marcarLeida(n.id))
    if (n.enlace) navegar(n.enlace)
    else recargar()
  }

  async function leerTodas() {
    if (await ejecutar(() => notificacionesApi.leerTodas(), 'Listo')) recargar()
  }

  return (
    <>
      <Encabezado titulo="Notificaciones">
        <Segmented
          value={soloNoLeidas}
          onChange={setSoloNoLeidas}
          options={[
            { value: false, label: 'Todas' },
            { value: true, label: 'Sin leer' },
          ]}
        />
        <Button onClick={leerTodas}>Marcar todas como leídas</Button>
      </Encabezado>
      <List
        loading={cargando}
        dataSource={items}
        pagination={{ ...paginacion, align: 'center' }}
        locale={{ emptyText: 'No hay notificaciones' }}
        renderItem={(n) => (
          <List.Item
            style={{ cursor: 'pointer', background: n.leida ? '#fff' : '#e6f4ff', padding: '12px 16px' }}
            onClick={() => abrir(n)}
            extra={<Typography.Text type="secondary">{fechaHora(n.fecha)}</Typography.Text>}
          >
            <List.Item.Meta
              title={
                <Badge dot={!n.leida} offset={[6, 0]}>
                  <Typography.Text strong={!n.leida}>{n.titulo}</Typography.Text>
                </Badge>
              }
              description={n.mensaje}
            />
          </List.Item>
        )}
      />
    </>
  )
}
