import { Flex, Typography } from 'antd'

/** Titulo de pagina con acciones a la derecha. */
export default function Encabezado({ titulo, descripcion, children }) {
  return (
    <Flex justify="space-between" align="flex-start" wrap gap={12} style={{ marginBottom: 16 }}>
      <div>
        <Typography.Title level={3} style={{ margin: 0 }}>
          {titulo}
        </Typography.Title>
        {descripcion && <Typography.Text type="secondary">{descripcion}</Typography.Text>}
      </div>
      <Flex gap={8} wrap>
        {children}
      </Flex>
    </Flex>
  )
}
