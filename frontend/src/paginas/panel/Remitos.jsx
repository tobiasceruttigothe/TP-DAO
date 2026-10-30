import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Select, Table } from 'antd'
import { remitosApi } from '../../api'
import useListado from '../../hooks/useListado'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import Ruta from '../../componentes/Ruta'
import { SelectorSede } from '../../componentes/Selectores'
import { opcionesDe } from '../../utiles/estados'
import { fechaHora } from '../../utiles/formato'

export default function Remitos() {
  const navegar = useNavigate()
  const [filtros, setFiltros] = useState({})
  const { items, cargando, paginacion } = useListado(remitosApi.listar, filtros)

  return (
    <>
      <Encabezado titulo="Remitos" descripcion="Envíos de ejemplares entre sedes">
        <SelectorSede
          soloActivas={false}
          style={{ width: 220 }}
          placeholder="Sede (origen o destino)"
          onChange={(sede_id) => setFiltros((f) => ({ ...f, sede_id }))}
        />
        <Select
          allowClear
          placeholder="Estado"
          style={{ width: 160 }}
          options={opcionesDe('remito')}
          onChange={(estado) => setFiltros((f) => ({ ...f, estado }))}
        />
      </Encabezado>

      <Table
        rowKey="id"
        loading={cargando}
        dataSource={items}
        pagination={paginacion}
        scroll={{ x: true }}
        onRow={(r) => ({ onClick: () => navegar(`/remitos/${r.id}`), style: { cursor: 'pointer' } })}
        columns={[
          { title: 'Número', dataIndex: 'numero', render: (n) => <a>{n}</a> },
          { title: 'Tipo', dataIndex: 'tipo', render: (v) => <EstadoTag tipo="tipoRemito" valor={v} /> },
          {
            title: 'Libro',
            render: (_, r) => (
              <>
                {r.ejemplar.libro.titulo}
                <div style={{ fontSize: 12, color: '#888' }}>{r.ejemplar.codigo_inventario}</div>
              </>
            ),
          },
          { title: 'Recorrido', render: (_, r) => <Ruta origen={r.sede_origen} destino={r.sede_destino} /> },
          { title: 'Estado', dataIndex: 'estado', render: (v) => <EstadoTag tipo="remito" valor={v} /> },
          { title: 'Creado', dataIndex: 'fecha_creacion', render: fechaHora },
          { title: 'Despachado', dataIndex: 'fecha_despacho', render: fechaHora },
          { title: 'Recibido', dataIndex: 'fecha_recepcion', render: fechaHora },
        ]}
      />
    </>
  )
}
