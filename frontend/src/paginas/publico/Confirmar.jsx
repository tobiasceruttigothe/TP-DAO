import { useEffect, useRef, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Result, Spin } from 'antd'
import { cuentaApi } from '../../api'

/** Destino del enlace que llega por correo al registrarse. */
export default function Confirmar() {
  const [parametros] = useSearchParams()
  const token = parametros.get('token')
  const [estado, setEstado] = useState({ cargando: Boolean(token) })
  const enviado = useRef(false)

  useEffect(() => {
    // El token se usa una sola vez: evita mandarlo dos veces si el efecto se repite
    if (!token || enviado.current) return
    enviado.current = true
    cuentaApi
      .confirmar(token)
      .then((usuario) => setEstado({ usuario }))
      .catch((error) => setEstado({ error: error.message }))
  }, [token])

  if (estado.cargando) return <Spin size="large" style={{ display: 'block', marginTop: 80 }} />

  if (!token || estado.error) {
    return (
      <Result
        status="warning"
        title="No pudimos confirmar tu email"
        subTitle={estado.error ?? 'El enlace está incompleto.'}
        extra={<Link to="/ingresar">Ir a ingresar (desde ahí podés pedir otro correo)</Link>}
      />
    )
  }

  if (estado.usuario.estado === 'ACTIVO') {
    return (
      <Result
        status="success"
        title="¡Email confirmado!"
        subTitle="Tu cuenta ya está activa."
        extra={<Link to="/ingresar">Ingresar</Link>}
      />
    )
  }

  return (
    <Result
      status="success"
      title="¡Email confirmado!"
      subTitle="La biblioteca va a revisar tus datos. Te avisamos por correo cuando tu cuenta esté aprobada."
      extra={<Link to="/">Volver al catálogo</Link>}
    />
  )
}
