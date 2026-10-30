import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { DatePicker, Select, Table } from 'antd'
import { incidenciasApi } from '../../api'
import useListado from '../../hooks/useListado'
import Encabezado from '../../componentes/Encabezado'
import EstadoTag from '../../componentes/EstadoTag'
import Ruta from '../../componentes/Ruta'
import { SelectorSede } from '../../componentes/Selectores'
import { opcionesDe } from '../../utiles/estados'
import { fechaApi, fechaHora } from '../../utiles/formato'

export default function Incidencias() {
  const navegar = useNavigate()
  const [filtros, setFiltros] = useState({})
  const { items, cargando, paginacion } = useListado(incidenciasApi.listar, filtros)

  return (
    <>
      <Encabezado titulo="Incidencias" descripcion="Daños, destrucciones y extravíos detectados en los envíos">
        <DatePicker.RangePicker
          format="DD/MM/YYYY"
          onChange={(rango) => setFiltros((f) => ({ ...f, desde: fechaApi(rango?.[0]), hasta: fechaApi(rango?.[1]) }))}
        />
        <SelectorSede soloActivas={false} style={{ width: 200 }} onChange={(sede_id) => setFiltros((f) => ({ ...f, sede_id }))} />
        <Select
          allowClear
          placeholder="Tipo"
          style={{ width: 150 }}
          options={opcionesDe('incidencia')}
          onChange={(tipo) => setFiltros((f) => ({ ...f, tipo }))}
        />
      </Encabezado>

      <Table
        rowKey="id"
        loading={cargando}
        dataSource={items}
        pagination={paginacion}
        scroll={{ x: true }}
        columns={[
          { title: 'Fecha', dataIndex: 'fecha', render: fechaHora },
          { title: 'Tipo', dataIndex: 'tipo', render: (v) => <EstadoTag tipo="incidencia" valor={v} /> },
          { title: 'Remito', render: (_, i) => <a onClick={() => navegar(`/remitos/${i.remito.id}`)}>{i.remito.numero}</a> },
          { title: 'Recorrido', render: (_, i) => <Ruta origen={i.remito.sede_origen} destino={i.remito.sede_destino} /> },
          { title: 'Descripción', dataIndex: 'descripcion', render: (d) => d ?? '-' },
        ]}
      />
    </>
  )
}
