import { useEffect, useRef } from 'react'
import { Input } from 'antd'

/**
 * Campo de busqueda que busca mientras se escribe: espera a que el usuario deje de
 * tipear un momento (`demora` en ms) para no consultar la API con cada letra.
 * Enter o la cruz de borrar buscan al instante.
 */
export default function Buscador({ onBuscar, demora = 350, ...props }) {
  const temporizador = useRef()

  useEffect(() => () => clearTimeout(temporizador.current), [])

  function alEscribir(evento) {
    const texto = evento.target.value
    clearTimeout(temporizador.current)
    temporizador.current = setTimeout(() => onBuscar(texto.trim()), demora)
  }

  function alConfirmar(texto) {
    clearTimeout(temporizador.current)
    onBuscar(texto.trim())
  }

  return <Input.Search allowClear onChange={alEscribir} onSearch={alConfirmar} {...props} />
}
