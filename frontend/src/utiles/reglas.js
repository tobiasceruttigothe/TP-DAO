// Reglas de formato de los formularios. Son las mismas que valida la API
// (app/schemas/validaciones.py): el formulario avisa antes de enviar, y la API
// vuelve a controlar por si algo llega por otro lado.

// Palabras de letras (con tildes y ñ) separadas por un espacio, apostrofe o guion
const PALABRAS = /^\p{L}+(?:[ '-]\p{L}+)*$/u

export const soloDigitos = (valor) => (valor ?? '').replace(/\D/g, '')

const limpiar = (valor) => (valor ?? '').trim().replace(/\s+/g, ' ')

export const reglasNombre = (campo) => [
  { required: true, message: `Ingresá el ${campo}` },
  {
    validator: (_, valor) => {
      const texto = limpiar(valor)
      if (!texto) return Promise.resolve()
      if (texto.length < 2) return Promise.reject(new Error('Al menos 2 caracteres'))
      if (texto.length > 50) return Promise.reject(new Error('Máximo 50 caracteres'))
      if (!PALABRAS.test(texto)) return Promise.reject(new Error('Solo letras, espacios, apóstrofes o guiones'))
      return Promise.resolve()
    },
  },
]

export const reglasDni = [
  { required: true, message: 'Ingresá el DNI' },
  { pattern: /^\d{7,8}$/, message: 'Debe tener 7 u 8 dígitos' },
]

export const reglasTelefono = [{ pattern: /^\d{6,15}$/, message: 'Solo números, entre 6 y 15 dígitos' }]

export function isbnValido(isbn) {
  if (/^\d{13}$/.test(isbn)) {
    const suma = [...isbn.slice(0, 12)].reduce((total, d, i) => total + Number(d) * (i % 2 === 0 ? 1 : 3), 0)
    return (10 - (suma % 10)) % 10 === Number(isbn[12])
  }
  if (/^\d{9}[\dX]$/.test(isbn)) {
    const suma = [...isbn].reduce((total, d, i) => total + (d === 'X' ? 10 : Number(d)) * (10 - i), 0)
    return suma % 11 === 0
  }
  return false
}

// Deja solo digitos y X (se pueden escribir guiones, que se quitan)
export const normalizarIsbn = (valor) => (valor ?? '').toUpperCase().replace(/[^\dX]/g, '')

export const reglasIsbn = [
  { required: true, message: 'Ingresá el ISBN' },
  {
    validator: (_, valor) =>
      !valor || isbnValido(valor)
        ? Promise.resolve()
        : Promise.reject(new Error('ISBN-10 o ISBN-13 inválido: revisá los dígitos')),
  },
]

export const reglasAnio = [
  {
    validator: (_, valor) => {
      if (valor === null || valor === undefined) return Promise.resolve()
      if (valor < 1400) return Promise.reject(new Error('Debe ser 1400 o posterior'))
      if (valor > new Date().getFullYear()) return Promise.reject(new Error('No puede ser posterior al año actual'))
      return Promise.resolve()
    },
  },
]

export const reglasTexto = (campo, minimo, maximo) => [
  { required: true, whitespace: true, message: `Ingresá ${campo}` },
  { min: minimo, message: `Al menos ${minimo} caracteres` },
  { max: maximo, message: `Máximo ${maximo} caracteres` },
]

// Misma regla que Contrasena en validaciones.py
export const reglasContrasena = [
  { required: true, message: 'Ingresá una contraseña' },
  {
    validator: (_, valor) => {
      if (!valor) return Promise.resolve()
      if (valor.length < 8) return Promise.reject(new Error('Al menos 8 caracteres'))
      if (new TextEncoder().encode(valor).length > 72) return Promise.reject(new Error('Máximo 72 caracteres'))
      if (!/[A-Za-z]/.test(valor) || !/\d/.test(valor)) return Promise.reject(new Error('Debe tener letras y números'))
      return Promise.resolve()
    },
  },
]

export const reglasEmail = [
  { required: true, message: 'Ingresá el email' },
  { type: 'email', message: 'No es un email válido' },
  { max: 120, message: 'Máximo 120 caracteres' },
]

/**
 * Valida un formulario de Ant Design. Devuelve los valores, o null si hay errores
 * (los errores ya se muestran debajo de cada campo; no hace falta tratarlos aparte).
 */
export async function validar(form) {
  try {
    return await form.validateFields()
  } catch {
    return null
  }
}
