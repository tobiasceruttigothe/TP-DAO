import { ArrowRightOutlined } from '@ant-design/icons'
import { Space } from 'antd'

/** Muestra "Origen -> Destino" para prestamos y remitos. */
export default function Ruta({ origen, destino }) {
  if (!origen) return '-'
  if (origen.id === destino?.id) return origen.nombre
  return (
    <Space size={4} wrap>
      {origen.nombre}
      <ArrowRightOutlined style={{ fontSize: 11 }} />
      {destino?.nombre}
    </Space>
  )
}
