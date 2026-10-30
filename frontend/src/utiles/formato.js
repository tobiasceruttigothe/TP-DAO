import dayjs from 'dayjs'

export const fecha = (valor) => (valor ? dayjs(valor).format('DD/MM/YYYY') : '-')

export const fechaHora = (valor) => (valor ? dayjs(valor).format('DD/MM/YYYY HH:mm') : '-')

const formatoMoneda = new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS' })
export const moneda = (valor) => formatoMoneda.format(valor ?? 0)

export const nombreSocio = (socio) => (socio ? `${socio.apellido}, ${socio.nombre}` : '-')

// Para mandar fechas a la API (formato ISO sin hora)
export const fechaApi = (valor) => (valor ? dayjs(valor).format('YYYY-MM-DD') : undefined)

export function diasHasta(valor) {
  return dayjs(valor).startOf('day').diff(dayjs().startOf('day'), 'day')
}
