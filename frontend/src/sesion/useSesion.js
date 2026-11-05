import { useContext } from 'react'
import { SesionContexto } from './contexto'

export default function useSesion() {
  return useContext(SesionContexto)
}

/** Pantalla de inicio de cada rol, a donde se va despues de ingresar. */
export const inicioDe = (usuario) => (usuario?.rol === 'ADMIN' ? '/panel' : '/socio')
