from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Pagina(BaseModel, Generic[T]):
    items: list[T]
    total: int
    pagina: int
    tamanio: int
    paginas: int

    @classmethod
    def desde(cls, resultado, items: list | None = None):
        """Arma la respuesta a partir del resultado del repositorio. `items` permite
        pasar los elementos ya convertidos cuando no se mapean directo del modelo."""
        return cls(
            items=resultado.items if items is None else items,
            total=resultado.total,
            pagina=resultado.pagina,
            tamanio=resultado.tamanio,
            paginas=resultado.paginas,
        )
