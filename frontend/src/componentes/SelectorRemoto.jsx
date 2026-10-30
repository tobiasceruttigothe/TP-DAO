import { useEffect, useRef, useState } from 'react'
import { Select, Spin } from 'antd'

/**
 * Select que busca en la API a medida que se escribe.
 * `buscar(texto)` devuelve una promesa con la lista de opciones { value, label }.
 * `opcionFija` se muestra siempre (sirve para un valor preseleccionado que no aparece en la busqueda).
 */
export default function SelectorRemoto({ buscar, placeholder, opcionFija, ...props }) {
  const [opciones, setOpciones] = useState([])
  const [cargando, setCargando] = useState(false)
  const temporizador = useRef()

  async function cargar(texto) {
    setCargando(true)
    try {
      setOpciones(await buscar(texto))
    } finally {
      setCargando(false)
    }
  }

  useEffect(() => {
    cargar('')
    return () => clearTimeout(temporizador.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  function alEscribir(texto) {
    clearTimeout(temporizador.current)
    temporizador.current = setTimeout(() => cargar(texto), 300)
  }

  const todas =
    opcionFija && !opciones.some((o) => o.value === opcionFija.value) ? [opcionFija, ...opciones] : opciones

  return (
    <Select
      showSearch
      allowClear
      filterOption={false}
      onSearch={alEscribir}
      options={todas}
      placeholder={placeholder}
      notFoundContent={cargando ? <Spin size="small" /> : 'Sin resultados'}
      {...props}
    />
  )
}
