import axios from 'axios'

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const cliente = axios.create({ baseURL: API_URL })

function mensajeDeError(error) {
  if (!error.response) return 'No se pudo conectar con el servidor'
  const detalle = error.response.data?.detail
  if (typeof detalle === 'string') return detalle
  if (Array.isArray(detalle)) {
    return detalle.map((d) => `${d.loc.slice(1).join('.')}: ${d.msg}`).join(' | ')
  }
  return `Error ${error.response.status}`
}

// Devuelve directamente el cuerpo de la respuesta y convierte los errores de la API
// en un Error con el mensaje que manda el backend.
cliente.interceptors.response.use(
  (respuesta) => respuesta.data,
  (error) => Promise.reject(new Error(mensajeDeError(error))),
)

// Quita los filtros vacios para no mandar "estado=" y que la API lo rechace
export function limpiar(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, valor]) => valor !== undefined && valor !== null && valor !== ''),
  )
}

export default cliente
