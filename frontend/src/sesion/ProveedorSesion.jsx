import { useCallback, useEffect, useMemo, useState } from 'react'
import { cuentaApi } from '../api'
import { EVENTO_SESION_VENCIDA, tokenGuardado } from '../api/cliente'
import { SesionContexto } from './contexto'

/**
 * Guarda quien esta conectado. Al abrir la pagina, si hay un token guardado, pide los datos
 * del usuario a la API; si el token ya no sirve, la sesion queda cerrada.
 */
export function ProveedorSesion({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [cargando, setCargando] = useState(Boolean(tokenGuardado.leer()))

  useEffect(() => {
    if (!tokenGuardado.leer()) return
    cuentaApi
      .yo()
      .then(setUsuario)
      .catch(() => tokenGuardado.borrar())
      .finally(() => setCargando(false))
  }, [])

  useEffect(() => {
    const alVencer = () => setUsuario(null)
    window.addEventListener(EVENTO_SESION_VENCIDA, alVencer)
    return () => window.removeEventListener(EVENTO_SESION_VENCIDA, alVencer)
  }, [])

  const ingresar = useCallback(async (email, contrasena) => {
    const sesion = await cuentaApi.ingresar(email, contrasena)
    tokenGuardado.guardar(sesion.token)
    setUsuario(sesion.usuario)
    return sesion.usuario
  }, [])

  const salir = useCallback(() => {
    tokenGuardado.borrar()
    setUsuario(null)
  }, [])

  const valor = useMemo(
    () => ({
      usuario,
      cargando,
      esAdmin: usuario?.rol === 'ADMIN',
      esSocio: usuario?.rol === 'SOCIO',
      ingresar,
      salir,
    }),
    [usuario, cargando, ingresar, salir],
  )

  return <SesionContexto.Provider value={valor}>{children}</SesionContexto.Provider>
}
