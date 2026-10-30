import { useCallback, useEffect, useState } from 'react'
import { App } from 'antd'

/** Carga un dato de la API al montar el componente y permite recargarlo. */
export default function useCarga(cargar, dependencias = []) {
  const { message } = App.useApp()
  const [datos, setDatos] = useState(null)
  const [cargando, setCargando] = useState(true)
  const clave = JSON.stringify(dependencias)

  const recargar = useCallback(async () => {
    setCargando(true)
    try {
      setDatos(await cargar(...JSON.parse(clave)))
    } catch (error) {
      message.error(error.message)
    } finally {
      setCargando(false)
    }
  }, [cargar, clave, message])

  useEffect(() => {
    recargar()
  }, [recargar])

  return { datos, cargando, recargar }
}
