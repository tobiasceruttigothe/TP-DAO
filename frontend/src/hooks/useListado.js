import { useCallback, useEffect, useState } from 'react'
import { App } from 'antd'

/**
 * Maneja un listado paginado de la API: pagina actual, tamanio, filtros y recarga.
 * `cargar` es una funcion de la API que recibe los parametros y devuelve una Pagina.
 */
export default function useListado(cargar, filtros = {}, tamanioInicial = 10) {
  const { message } = App.useApp()
  const [pagina, setPagina] = useState(1)
  const [tamanio, setTamanio] = useState(tamanioInicial)
  const [datos, setDatos] = useState({ items: [], total: 0 })
  const [cargando, setCargando] = useState(false)
  const claveFiltros = JSON.stringify(filtros)

  const recargar = useCallback(async () => {
    setCargando(true)
    try {
      setDatos(await cargar({ ...JSON.parse(claveFiltros), pagina, tamanio }))
    } catch (error) {
      message.error(error.message)
    } finally {
      setCargando(false)
    }
  }, [cargar, claveFiltros, pagina, tamanio, message])

  useEffect(() => {
    recargar()
  }, [recargar])

  // Al cambiar un filtro se vuelve a la primera pagina
  useEffect(() => {
    setPagina(1)
  }, [claveFiltros])

  return {
    items: datos.items,
    cargando,
    recargar,
    paginacion: {
      current: pagina,
      pageSize: tamanio,
      total: datos.total,
      showSizeChanger: true,
      showTotal: (total) => `${total} en total`,
      onChange: (nuevaPagina, nuevoTamanio) => {
        setPagina(nuevaPagina)
        setTamanio(nuevoTamanio)
      },
    },
  }
}
