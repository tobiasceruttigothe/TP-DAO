import { Table, Tag } from 'antd'
import { miApi } from '../../api'
import useListado from '../../hooks/useListado'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import { fecha, moneda } from '../../utiles/formato'

export default function Historial() {
  const { items, cargando, paginacion } = useListado(miApi.historial)

  return (
    <>
      <Encabezado titulo="Historial de lectura" descripcion="Libros que ya devolviste, del más reciente al más antiguo" />
      <Table
        rowKey="prestamo_id"
        loading={cargando}
        dataSource={items}
        pagination={paginacion}
        scroll={{ x: true }}
        locale={{ emptyText: 'Todavía no devolviste ningún libro' }}
        columns={[
          { title: 'Libro', dataIndex: 'titulo' },
          { title: 'Autor', dataIndex: 'autor' },
          { title: 'Retirado en', dataIndex: 'sede_retiro' },
          { title: 'Tipo', dataIndex: 'tipo', render: (v) => <EstadoTag tipo="tipoPrestamo" valor={v} /> },
          { title: 'Desde', dataIndex: 'fecha_inicio', render: fecha },
          { title: 'Devuelto', dataIndex: 'fecha_devolucion', render: fecha },
          {
            title: 'Atraso',
            render: (_, l) =>
              l.dias_atraso > 0 ? <Tag color="red">{l.dias_atraso} día(s) · {moneda(l.multa)}</Tag> : <Tag color="green">En término</Tag>,
          },
        ]}
      />
    </>
  )
}
