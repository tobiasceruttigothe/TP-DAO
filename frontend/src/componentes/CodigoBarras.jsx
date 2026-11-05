import { useEffect, useRef } from 'react'
import JsBarcode from 'jsbarcode'

/** Codigo de barras CODE128, el que leen los lectores comunes de mostrador. */
export default function CodigoBarras({ valor, alto = 50 }) {
  const svg = useRef(null)

  useEffect(() => {
    JsBarcode(svg.current, valor, { format: 'CODE128', height: alto, width: 1.6, fontSize: 14, margin: 4 })
  }, [valor, alto])

  return <svg ref={svg} />
}
