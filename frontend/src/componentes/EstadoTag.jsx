import { Tag } from 'antd'
import { ESTADOS } from '../utiles/estados'

export default function EstadoTag({ tipo, valor }) {
  if (!valor) return null
  const estado = ESTADOS[tipo]?.[valor] ?? { texto: valor, color: 'default' }
  return <Tag color={estado.color}>{estado.texto}</Tag>
}
