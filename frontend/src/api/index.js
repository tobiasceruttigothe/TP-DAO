import cliente, { limpiar } from './cliente'

const get = (url, params) => cliente.get(url, { params: limpiar(params) })

export const sedesApi = {
  listar: (params) => get('/sedes', params),
  crear: (datos) => cliente.post('/sedes', datos),
  actualizar: (id, datos) => cliente.put(`/sedes/${id}`, datos),
  darDeBaja: (id) => cliente.patch(`/sedes/${id}/baja`),
  darDeAlta: (id) => cliente.patch(`/sedes/${id}/alta`),
}

export const sociosApi = {
  listar: (params) => get('/socios', params),
  obtener: (id) => cliente.get(`/socios/${id}`),
  crear: (datos) => cliente.post('/socios', datos),
  actualizar: (id, datos) => cliente.put(`/socios/${id}`, datos),
  inhabilitar: (id, motivo) => cliente.patch(`/socios/${id}/inhabilitar`, { motivo }),
  habilitar: (id) => cliente.patch(`/socios/${id}/habilitar`),
  historial: (id, params) => get(`/socios/${id}/historial`, params),
}

export const librosApi = {
  listar: (params) => get('/libros', params),
  obtener: (id) => cliente.get(`/libros/${id}`),
  crear: (datos) => cliente.post('/libros', datos),
  actualizar: (id, datos) => cliente.put(`/libros/${id}`, datos),
  disponibilidad: (id) => cliente.get(`/libros/${id}/disponibilidad`),
}

export const ejemplaresApi = {
  listar: (params) => get('/ejemplares', params),
  crear: (datos) => cliente.post('/ejemplares', datos),
  darDeBaja: (id) => cliente.patch(`/ejemplares/${id}/baja`),
  marcarReparado: (id) => cliente.patch(`/ejemplares/${id}/reparado`),
}

export const prestamosApi = {
  listar: (params) => get('/prestamos', params),
  solicitar: (datos) => cliente.post('/prestamos', datos),
  devolver: (id, datos) => cliente.post(`/prestamos/${id}/devolucion`, datos),
  remitos: (id) => cliente.get(`/prestamos/${id}/remitos`),
}

export const remitosApi = {
  listar: (params) => get('/remitos', params),
  obtener: (id) => cliente.get(`/remitos/${id}`),
  empaquetar: (id, datos) => cliente.post(`/remitos/${id}/empaquetar`, datos),
  despachar: (id, datos) => cliente.post(`/remitos/${id}/despachar`, datos),
  recibir: (id, datos) => cliente.post(`/remitos/${id}/recibir`, datos),
  extraviar: (id, datos) => cliente.post(`/remitos/${id}/extraviar`, datos),
  cancelar: (id, datos) => cliente.post(`/remitos/${id}/cancelar`, datos),
}

export const incidenciasApi = {
  listar: (params) => get('/incidencias', params),
}

export const reservasApi = {
  listar: (params) => get('/reservas', params),
  crear: (datos) => cliente.post('/reservas', datos),
  cancelar: (id) => cliente.post(`/reservas/${id}/cancelar`),
  procesarVencidas: () => cliente.post('/reservas/procesar-vencidas'),
}

export const reportesApi = {
  activosYTransito: () => cliente.get('/reportes/prestamos-activos'),
  vencidosYMultas: (params) => get('/reportes/vencidos-multas', params),
  librosMasSolicitados: (params) => get('/reportes/libros-mas-solicitados', params),
  disponibilidadSedes: () => cliente.get('/reportes/disponibilidad-sedes'),
  envios: (params) => get('/reportes/envios', params),
  movimientosSedes: (params) => get('/reportes/movimientos-sedes', params),
}
