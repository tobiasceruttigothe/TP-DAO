import { Tag, Typography } from 'antd'
import { moneda } from '../utiles/formato'

/** Dias de atraso de un prestamo (a hoy si sigue activo, o el que tuvo si se devolvio). */
export function Atraso({ prestamo }) {
  const dias = prestamo.dias_atraso_actual
  if (!dias) return '-'
  if (prestamo.estado === 'ACTIVO') return <Tag color="red">{dias} días</Tag>
  return `${dias} días`
}

/** Multa cobrada, o la acumulada hasta hoy si todavia no se devolvio. */
export function Multa({ prestamo }) {
  if (!prestamo.multa_actual) return '-'
  if (prestamo.estado === 'ACTIVO') {
    return (
      <>
        <Typography.Text type="danger">{moneda(prestamo.multa_actual)}</Typography.Text>
        <div style={{ fontSize: 12, color: '#8c8c8c' }}>a la fecha</div>
      </>
    )
  }
  return moneda(prestamo.multa_actual)
}
