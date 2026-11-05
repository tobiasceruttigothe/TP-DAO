class BibliotecaError(Exception):
    """Base de los errores de la aplicacion."""

    def __init__(self, mensaje: str):
        super().__init__(mensaje)
        self.mensaje = mensaje


class NoEncontradoError(BibliotecaError):
    pass


class DuplicadoError(BibliotecaError):
    pass


class ReglaNegocioError(BibliotecaError):
    pass


class TransicionInvalidaError(ReglaNegocioError):
    pass


class NoAutorizadoError(BibliotecaError):
    """Falta iniciar sesion, o las credenciales no son validas (401)."""


class SinPermisoError(BibliotecaError):
    """La sesion es valida pero el usuario no puede hacer esto (403)."""
