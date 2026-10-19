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
