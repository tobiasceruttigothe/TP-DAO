import { Tag, Tooltip, Typography } from 'antd'
import { moneda } from '../utiles/formato'

/** Dias de atraso de un prestamo (a hoy si sigue activo, o el que tuvo si se devolvio). */
export function Atraso({ prestamo }) {
  const dias = prestamo.dias_atraso_actual
  if (!dias) return '-'
  if (prestamo.estado === 'ACTIVO') return <Tag color="red">{dias} días</Tag>
  return `${dias} días`
}

/** Renglones de la multa: "Atraso grave: ... $6.500", "Devuelto dañado $5.000". */
export function DesgloseMulta({ conceptos }) {
  if (!conceptos?.length) return null
  return (
    <ul style={{ margin: 0, paddingLeft: 18 }}>
      {conceptos.map((c) => (
        <li key={c.concepto}>
          {c.concepto}: <b>{moneda(c.monto)}</b>
        </li>
      ))}
    </ul>
  )
}

/** Multa cobrada, o la acumulada hasta hoy si todavia no se devolvio. Al pasar el mouse muestra el detalle. */
export function Multa({ prestamo }) {
  if (!prestamo.multa_actual) return '-'
  const activo = prestamo.estado === 'ACTIVO'
  return (
    <Tooltip title={<DesgloseMulta conceptos={prestamo.desglose_multa} />}>
      <span style={{ cursor: 'help' }}>
        <Typography.Text type={activo ? 'danger' : undefined} underline>
          {moneda(prestamo.multa_actual)}
        </Typography.Text>
        {activo && <div style={{ fontSize: 12, color: '#8c8c8c' }}>a la fecha</div>}
      </span>
    </Tooltip>
  )
}
