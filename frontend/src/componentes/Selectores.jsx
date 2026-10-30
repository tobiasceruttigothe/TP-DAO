import { useEffect, useState } from 'react'
import { Select } from 'antd'
import { librosApi, sedesApi, sociosApi } from '../api'
import SelectorRemoto from './SelectorRemoto'

async function buscarSocios(texto) {
  const pagina = await sociosApi.listar({ q: texto, habilitado: true, tamanio: 15 })
  return pagina.items.map((s) => ({ value: s.id, label: `${s.apellido}, ${s.nombre} (DNI ${s.dni})` }))
}

async function buscarLibros(texto) {
  const pagina = await librosApi.listar({ q: texto, tamanio: 15 })
  return pagina.items.map((l) => ({ value: l.id, label: `${l.titulo} - ${l.autor}` }))
}

export function SelectorSocio(props) {
  return <SelectorRemoto buscar={buscarSocios} placeholder="Buscar por apellido, nombre o DNI" {...props} />
}

export function SelectorLibro(props) {
  return <SelectorRemoto buscar={buscarLibros} placeholder="Buscar por título o autor" {...props} />
}

/** Lista de sedes. Por defecto solo las activas, que son las que pueden operar. */
export function SelectorSede({ soloActivas = true, ...props }) {
  const [sedes, setSedes] = useState([])

  useEffect(() => {
    sedesApi.listar(soloActivas ? { activa: true } : {}).then(setSedes).catch(() => setSedes([]))
  }, [soloActivas])

  return (
    <Select
      allowClear
      placeholder="Sede"
      options={sedes.map((s) => ({ value: s.id, label: s.activa ? s.nombre : `${s.nombre} (baja)` }))}
      {...props}
    />
  )
}
