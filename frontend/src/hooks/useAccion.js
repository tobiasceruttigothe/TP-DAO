import { useState } from 'react'
import { App } from 'antd'

/**
 * Ejecuta una operacion contra la API mostrando el resultado.
 * Devuelve true si salio bien, para poder cerrar modales o recargar.
 */
export default function useAccion() {
  const { message } = App.useApp()
  const [ejecutando, setEjecutando] = useState(false)

  async function ejecutar(operacion, mensajeExito) {
    setEjecutando(true)
    try {
      const resultado = await operacion()
      if (mensajeExito) message.success(mensajeExito)
      // Una respuesta sin cuerpo (204) llega como '': igual cuenta como exito
      return resultado || true
    } catch (error) {
      message.error(error.message)
      return false
    } finally {
      setEjecutando(false)
    }
  }

  return { ejecutar, ejecutando }
}
