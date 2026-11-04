import { useState } from 'react'
import { Alert, Button, Empty, Select, Space, Spin, Typography } from 'antd'
import { PrinterOutlined } from '@ant-design/icons'
import { ejemplaresApi } from '../../api'
import useListado from '../../hooks/useListado'
import Encabezado from '../../componentes/Encabezado'
import CodigoBarras from '../../componentes/CodigoBarras'
import { SelectorLibro, SelectorSede } from '../../componentes/Selectores'
import { opcionesDe } from '../../utiles/estados'

/** Etiquetas con codigo de barras para pegar en los ejemplares y leerlas en el inventario. */
export default function Etiquetas() {
  const [filtros, setFiltros] = useState({})
  const elegido = Boolean(filtros.sede_id || filtros.libro_id)
  const { items, cargando, paginacion } = useListado(elegido ? ejemplaresApi.listar : sinFiltro, filtros, 100)
  const cambiar = (campo) => (valor) => setFiltros((f) => ({ ...f, [campo]: valor }))

  return (
    <>
      <div className="no-imprimir">
        <Encabezado titulo="Etiquetas" descripcion="Códigos de barras de los ejemplares, listos para imprimir y pegar">
          <Button type="primary" icon={<PrinterOutlined />} disabled={!items.length} onClick={() => window.print()}>
            Imprimir
          </Button>
        </Encabezado>
        <Space wrap style={{ marginBottom: 16 }}>
          <SelectorSede soloActivas={false} style={{ width: 200 }} onChange={cambiar('sede_id')} />
          <SelectorLibro style={{ width: 300 }} onChange={cambiar('libro_id')} allowClear />
          <Select allowClear placeholder="Estado" style={{ width: 170 }} options={opcionesDe('ejemplar')} onChange={cambiar('estado')} />
        </Space>
        {paginacion.total > items.length && (
          <Alert
            type="info"
            showIcon
            style={{ marginBottom: 16 }}
            message={`Se muestran ${items.length} de ${paginacion.total}. Filtrá por libro o estado para imprimir el resto.`}
          />
        )}
      </div>

      {!elegido ? (
        <Empty description="Elegí una sede o un libro" />
      ) : cargando ? (
        <Spin style={{ display: 'block', marginTop: 40 }} />
      ) : items.length === 0 ? (
        <Empty description="No hay ejemplares con esos filtros" />
      ) : (
        <div className="etiquetas">
          {items.map((e) => (
            <div key={e.id} className="etiqueta">
              <Typography.Text strong ellipsis style={{ display: 'block' }}>
                {e.libro.titulo}
              </Typography.Text>
              <Typography.Text type="secondary" style={{ fontSize: 12, display: 'block' }}>
                {e.sede.nombre}
              </Typography.Text>
              <CodigoBarras valor={e.codigo_inventario} />
            </div>
          ))}
        </div>
      )}
    </>
  )
}

async function sinFiltro() {
  return { items: [], total: 0 }
}
