import axios from 'axios'

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const cliente = axios.create({ baseURL: API_URL })

// El token de la sesion se guarda en el navegador para no pedir el login en cada recarga
const CLAVE_TOKEN = 'biblioteca.token'

export const tokenGuardado = {
  leer: () => localStorage.getItem(CLAVE_TOKEN),
  guardar: (token) => localStorage.setItem(CLAVE_TOKEN, token),
  borrar: () => localStorage.removeItem(CLAVE_TOKEN),
}

// Se avisa a la sesion cuando la API rechaza el token (vencido o cuenta dada de baja)
export const EVENTO_SESION_VENCIDA = 'biblioteca:sesion-vencida'

cliente.interceptors.request.use((config) => {
  const token = tokenGuardado.leer()
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

function mensajeDeError(error) {
  if (!error.response) return 'No se pudo conectar con el servidor'
  const detalle = error.response.data?.detail
  if (typeof detalle === 'string') return detalle
  if (Array.isArray(detalle)) {
    return detalle.map((d) => `${d.loc.slice(1).join('.')}: ${d.msg.replace(/^Value error, /, '')}`).join(' | ')
  }
  return `Error ${error.response.status}`
}

// Devuelve directamente el cuerpo de la respuesta y convierte los errores de la API
// en un Error con el mensaje que manda el backend.
cliente.interceptors.response.use(
  (respuesta) => respuesta.data,
  (error) => {
    const conToken = Boolean(error.config?.headers?.Authorization)
    if (error.response?.status === 401 && conToken) {
      tokenGuardado.borrar()
      window.dispatchEvent(new Event(EVENTO_SESION_VENCIDA))
    }
    return Promise.reject(new Error(mensajeDeError(error)))
  },
)

// Quita los filtros vacios para no mandar "estado=" y que la API lo rechace
export function limpiar(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, valor]) => valor !== undefined && valor !== null && valor !== ''),
  )
}

export default cliente
