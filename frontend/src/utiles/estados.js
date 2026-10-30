// Texto y color de cada estado que devuelve la API, para mostrarlos de forma uniforme.
export const ESTADOS = {
  ejemplar: {
    DISPONIBLE: { texto: 'Disponible', color: 'green' },
    RESERVADO: { texto: 'Reservado', color: 'purple' },
    PRESTADO: { texto: 'Prestado', color: 'blue' },
    EN_TRANSITO: { texto: 'En tránsito', color: 'cyan' },
    EN_REPARACION: { texto: 'En reparación', color: 'orange' },
    EXTRAVIADO: { texto: 'Extraviado', color: 'red' },
    BAJA: { texto: 'Baja', color: 'default' },
  },
  fisico: {
    BUENO: { texto: 'Bueno', color: 'green' },
    REGULAR: { texto: 'Regular', color: 'gold' },
    DANADO: { texto: 'Dañado', color: 'orange' },
    DESTRUIDO: { texto: 'Destruido', color: 'red' },
  },
  prestamo: {
    SOLICITADO: { texto: 'Solicitado', color: 'gold' },
    EN_TRANSITO: { texto: 'En tránsito', color: 'cyan' },
    ACTIVO: { texto: 'Activo', color: 'blue' },
    DEVUELTO: { texto: 'Devuelto', color: 'green' },
    CANCELADO: { texto: 'Cancelado', color: 'default' },
  },
  tipoPrestamo: {
    LOCAL: { texto: 'Local', color: 'default' },
    INTERBIBLIOTECARIO: { texto: 'Inter-sede', color: 'geekblue' },
  },
  remito: {
    PENDIENTE: { texto: 'Pendiente', color: 'gold' },
    EMPAQUETADO: { texto: 'Empaquetado', color: 'purple' },
    DESPACHADO: { texto: 'Despachado', color: 'cyan' },
    RECIBIDO: { texto: 'Recibido', color: 'green' },
    EXTRAVIADO: { texto: 'Extraviado', color: 'red' },
    CANCELADO: { texto: 'Cancelado', color: 'default' },
  },
  tipoRemito: {
    IDA: { texto: 'Ida', color: 'geekblue' },
    RETORNO: { texto: 'Retorno', color: 'default' },
  },
  reserva: {
    PENDIENTE: { texto: 'En espera', color: 'gold' },
    DISPONIBLE: { texto: 'Lista para retirar', color: 'green' },
    CUMPLIDA: { texto: 'Cumplida', color: 'blue' },
    CANCELADA: { texto: 'Cancelada', color: 'default' },
    VENCIDA: { texto: 'Vencida', color: 'red' },
  },
  incidencia: {
    DANIO: { texto: 'Daño', color: 'orange' },
    DESTRUCCION: { texto: 'Destrucción', color: 'red' },
    EXTRAVIO: { texto: 'Extravío', color: 'volcano' },
  },
}

export function opcionesDe(tipo) {
  return Object.entries(ESTADOS[tipo]).map(([valor, { texto }]) => ({ value: valor, label: texto }))
}
