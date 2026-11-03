# Patrones de diseño

La consigna exige al menos dos patrones. Se aplicaron tres: **State**, **Strategy** y
**Repository**. Se evaluó también **Singleton** y se descartó; los motivos están al final.

| Patrón | Dónde | Problema que resuelve |
|---|---|---|
| State | `app/domain/estados_remito.py`, `app/models/remito.py` | Ciclo de vida del remito |
| Strategy | `app/domain/multas.py` | Cálculo de multas según atraso y estado de devolución |
| Repository | `app/repositories/` | Separar el acceso a datos de la lógica de negocio |

---

## State: ciclo de vida del remito

### Problema

Un remito pasa por varios estados (pendiente, empaquetado, despachado, recibido, extraviado,
cancelado), y en cada uno solo algunas operaciones son válidas. Por ejemplo, no se puede
despachar algo que no se empaquetó, ni recibir algo que no se despachó. La consigna aclara que
"el ciclo de vida del remito y sus estados será evaluado críticamente".

Sin el patrón, cada operación necesitaría un condicional sobre el estado:

```python
def despachar(self):
    if self.estado == "EMPAQUETADO":
        self.estado = "DESPACHADO"
    elif self.estado in ("PENDIENTE", "RECIBIDO", "EXTRAVIADO", "CANCELADO"):
        raise Exception(...)
```

Ese bloque se repetiría en las cinco operaciones. Agregar un estado nuevo obligaría a revisar
todas, y es fácil olvidarse una combinación y permitir una transición inválida.

### Solución

Cada estado es una clase. El remito (el **contexto**) delega cada operación en su estado actual,
y el estado decide si la acepta y a qué estado pasa.

```mermaid
classDiagram
    class Remito {
        +estado: str
        +estado_actual: EstadoRemito
        +cambiar_estado(nuevo, observacion)
        +empaquetar(observacion)
        +despachar(observacion)
        +recibir(observacion)
        +marcar_extraviado(observacion)
        +cancelar(observacion)
    }
    class EstadoRemito {
        <<abstract>>
        +nombre: str
        +es_final: bool
        +entrar(remito)
        +empaquetar(remito, observacion)
        +despachar(remito, observacion)
        +recibir(remito, observacion)
        +marcar_extraviado(remito, observacion)
        +cancelar(remito, observacion)
    }
    class Pendiente {
        +empaquetar()
        +cancelar()
    }
    class Empaquetado {
        +despachar()
        +cancelar()
    }
    class Despachado {
        +entrar()
        +recibir()
        +marcar_extraviado()
    }
    class Recibido {
        +entrar()
    }
    class Extraviado
    class Cancelado
    Remito --> EstadoRemito : estado actual
    EstadoRemito <|-- Pendiente
    EstadoRemito <|-- Empaquetado
    EstadoRemito <|-- Despachado
    EstadoRemito <|-- Recibido
    EstadoRemito <|-- Extraviado
    EstadoRemito <|-- Cancelado
```

### Máquina de estados

Cada flecha es una operación que el estado de origen sobrescribe. Lo que no tiene flecha no está
programado y, por lo tanto, se rechaza.

```mermaid
stateDiagram-v2
    [*] --> Pendiente: se genera el remito
    Pendiente --> Empaquetado: empaquetar()
    Pendiente --> Cancelado: cancelar()
    Empaquetado --> Despachado: despachar()
    Empaquetado --> Cancelado: cancelar()
    Despachado --> Recibido: recibir()
    Despachado --> Extraviado: marcar_extraviado()
    Recibido --> [*]
    Extraviado --> [*]
    Cancelado --> [*]
```

Qué puede hacer cada estado. "→ X" indica a qué estado pasa; "rechaza" significa que la operación
lanza `TransicionInvalidaError` y el remito queda como estaba.

| Estado | `empaquetar()` | `despachar()` | `recibir()` | `marcar_extraviado()` | `cancelar()` | Final |
|---|---|---|---|---|---|---|
| **Pendiente** | → Empaquetado | rechaza | rechaza | rechaza | → Cancelado | No |
| **Empaquetado** | rechaza | → Despachado | rechaza | rechaza | → Cancelado | No |
| **Despachado** | rechaza | rechaza | → Recibido | → Extraviado | rechaza | No |
| **Recibido** | rechaza | rechaza | rechaza | rechaza | rechaza | Sí |
| **Extraviado** | rechaza | rechaza | rechaza | rechaza | rechaza | Sí |
| **Cancelado** | rechaza | rechaza | rechaza | rechaza | rechaza | Sí |

Cada transición dispara, además, efectos sobre otras entidades. No los decide el estado sino
`RemitoService`, porque dependen de si el remito es de **ida** (sede origen → sede destino del
préstamo) o de **retorno** (vuelta del ejemplar a su sede):

| Transición | Ida | Retorno |
|---|---|---|
| `empaquetar()` | Solo cambia el remito | Solo cambia el remito |
| `despachar()` | Se valida que las dos sedes estén activas. Ejemplar y préstamo pasan a EN_TRANSITO | Ejemplar EN_TRANSITO (no se bloquea por sedes de baja: el ejemplar tiene que volver) |
| `recibir()` | Préstamo ACTIVO (empieza a correr el plazo) y ejemplar PRESTADO | El ejemplar vuelve a estar disponible en su sede y se ofrece a la primera reserva pendiente |
| `recibir()` con daño | Igual, y se registra una incidencia | Ejemplar EN_REPARACION y se registra una incidencia |
| `recibir()` destruido | Ejemplar de BAJA, préstamo CANCELADO e incidencia | Ejemplar de BAJA e incidencia |
| `marcar_extraviado()` | Ejemplar EXTRAVIADO, préstamo CANCELADO e incidencia | Ejemplar EXTRAVIADO e incidencia |
| `cancelar()` | Préstamo CANCELADO; el ejemplar se libera | No permitido: lo rechaza el servicio antes de llegar al estado, porque el ejemplar tiene que volver a su sede |

**Comportamiento por defecto en la clase base.** `EstadoRemito` implementa todas las operaciones
lanzando `TransicionInvalidaError`. Cada estado concreto sobrescribe solo las que admite:

```python
class EstadoRemito(ABC):
    def despachar(self, remito, observacion=None):
        self._rechazar("despachar")


class Empaquetado(EstadoRemito):
    nombre = "EMPAQUETADO"

    def despachar(self, remito, observacion=None):
        remito.cambiar_estado(Despachado(), observacion)
```

Así, una transición que no está programada es imposible: no hay que acordarse de prohibirla.
Los estados finales (Recibido, Extraviado, Cancelado) no sobrescriben ninguna operación.

**Gancho `entrar`.** Igual que en el ejemplo del semáforo visto en clase, cada estado puede
ejecutar algo al activarse. `Despachado.entrar` registra la fecha de despacho y `Recibido.entrar`
la de recepción. Con esas fechas se calcula el tiempo promedio de tránsito del reporte.

**Trazabilidad.** El cambio de estado pasa siempre por `Remito.cambiar_estado`, que además de
actualizar el estado agrega un `MovimientoRemito` al historial. Como no hay otra forma de cambiar
el estado, no puede haber un cambio sin registrar.

### Persistencia del estado

Los objetos estado no se guardan en la base. Se guarda el nombre (`remitos.estado = "DESPACHADO"`)
y la propiedad `Remito.estado_actual` reconstruye el objeto a partir de ese nombre:

```python
_ESTADOS = {cls.nombre: cls for cls in (Pendiente, Empaquetado, Despachado, Recibido, Extraviado, Cancelado)}

def estado_desde_nombre(nombre):
    return _ESTADOS[nombre]()
```

Los estados no tienen atributos propios, así que crear una instancia nueva cada vez no pierde
información.

### Reparto de responsabilidades

El patrón solo decide qué transiciones son válidas y deja registro de cada una. Los efectos
sobre otras entidades (el préstamo pasa a ACTIVO, el ejemplar a EN_TRANSITO, se asigna una
reserva) los coordina `RemitoService`, porque dependen de si el remito es de ida o de retorno y
de otras entidades que el estado no debería conocer.

### Cómo agregar un estado

Por ejemplo, un estado `EN_ADUANA` entre despachado y recibido:

1. Crear la clase `EnAduana(EstadoRemito)` con las operaciones que admite.
2. Cambiar `Despachado` para que su transición vaya a `EnAduana`.
3. Agregarla al diccionario `_ESTADOS`.

No hace falta tocar el remito, los servicios ni la base: la columna `estado` ya es texto.

### Tests

`tests/test_estados_remito.py` prueba el patrón sin base de datos: el recorrido completo, que
cada transición inválida se rechace sin modificar el remito, que los estados finales no acepten
ninguna operación y que el historial quede completo.

---

## Strategy: cálculo de multas

### Problema

Al devolver un préstamo se puede cobrar una multa, y no todos los casos se cobran igual: no es
lo mismo un atraso de dos días que uno de un mes, ni devolver el libro en buen estado que
dañado. Si todas esas reglas estuvieran escritas dentro de la devolución, quedaría un método
lleno de condicionales, y cada cambio de política (otro monto, un tramo nuevo, un recargo)
obligaría a tocar el proceso de préstamos.

### Solución

Cada forma de multar es una estrategia: una clase con la misma interfaz (`calcular`) que sabe
calcular **su parte** de la multa. Las tres estrategias **conviven**, y en cada devolución el
contexto (`CalculadorMulta`) mira la situación y elige cuáles aplicar.

```mermaid
classDiagram
    class EstrategiaMulta {
        <<abstract>>
        +calcular(datos) ConceptoMulta
    }
    class MultaAtrasoLeve {
        +monto_diario: float
        +calcular(datos) ConceptoMulta
    }
    class MultaAtrasoGrave {
        +monto_diario: float
        +monto_diario_grave: float
        +dias_leves: int
        +calcular(datos) ConceptoMulta
    }
    class MultaPorDanio {
        +cargos: dict
        +cobra(estado_fisico) bool
        +calcular(datos) ConceptoMulta
    }
    class CalculadorMulta {
        +estrategias_para(datos) list
        +calcular(datos) ResultadoMulta
    }
    class DatosMulta {
        +dias_atraso: int
        +estado_fisico
    }
    class PrestamoService {
        +calculador: CalculadorMulta
        +devolver(prestamo_id, datos)
    }
    EstrategiaMulta <|-- MultaAtrasoLeve
    EstrategiaMulta <|-- MultaAtrasoGrave
    EstrategiaMulta <|-- MultaPorDanio
    CalculadorMulta o--> EstrategiaMulta : tiene las tres
    CalculadorMulta ..> DatosMulta : decide según
    PrestamoService --> CalculadorMulta
```

| Estrategia | Cuándo se aplica | Cómo calcula (valores por defecto) |
|---|---|---|
| `MultaAtrasoLeve` | Atraso de 1 a 7 días | días × $500 |
| `MultaAtrasoGrave` | Atraso de 8 días o más | 7 días × $500 + los días siguientes × $1.000 |
| `MultaPorDanio` | Se devuelve dañado o destruido | Cargo fijo: $5.000 dañado, $20.000 destruido (reposición) |

Las dos de atraso se excluyen entre sí. La de daño se **suma** a la de atraso, si la hay.

### Quién elige la estrategia

Como explica el apunte (16.5.1), la diferencia clave entre State y Strategy es **quién decide el
cambio**. En State, el propio estado decide a qué estado pasa. En Strategy, la elige alguien de
afuera de la estrategia. Acá la elige el contexto, `CalculadorMulta`, según los datos de cada
devolución:

```python
def estrategias_para(self, datos: DatosMulta) -> list[EstrategiaMulta]:
    elegidas = []
    if datos.dias_atraso > self.atraso_grave.dias_leves:
        elegidas.append(self.atraso_grave)
    elif datos.dias_atraso > 0:
        elegidas.append(self.atraso_leve)
    if self.por_danio.cobra(datos.estado_fisico):
        elegidas.append(self.por_danio)
    return elegidas
```

Las estrategias no saben cuándo se aplican, solo cómo calcular. La decisión está en un único
lugar, y el servicio de préstamos no conoce ninguna estrategia concreta: le pasa los datos al
calculador y guarda el resultado.

| Caso | Estrategias elegidas | Multa |
|---|---|---|
| 5 días de atraso, devuelto bien | Atraso leve | 5 × $500 = **$2.500** |
| 7 días de atraso, devuelto bien | Atraso leve | 7 × $500 = **$3.500** |
| 10 días de atraso, devuelto bien | Atraso grave | 7 × $500 + 3 × $1.000 = **$6.500** |
| 3 días de atraso, devuelto dañado | Atraso leve + daño | $1.500 + $5.000 = **$6.500** |
| En término, devuelto destruido | Daño | **$20.000** |
| Activo, 36 días vencido (multa a la fecha) | Atraso grave | 7 × $500 + 29 × $1.000 = **$32.500** |

Mientras el préstamo no se devuelve, la multa a la fecha solo incluye el atraso: el estado
físico recién se conoce al devolverlo.

### Detalle de la multa

`calcular` devuelve un `ResultadoMulta` con un renglón por estrategia aplicada (concepto y
monto) y el total. Al devolver se guardan los dos en el préstamo (`multa` y `detalle_multa`),
así el detalle no cambia aunque después se modifiquen los montos. El frontend lo muestra al
registrar la devolución y al pasar el mouse sobre cualquier multa.

### Por qué no un diccionario de funciones

El apunte muestra que Strategy también se puede implementar con funciones en un diccionario
(16.6). Se eligieron clases porque las estrategias tienen parámetros propios (montos, días del
tramo leve, cargos por estado) y con una clase quedan encapsulados junto al cálculo. Con
funciones habría que pasarlos en cada llamada o usar clausuras.

### Configuración

Los montos se configuran por variables de entorno, sin tocar código: `MULTA_MONTO_DIARIO`,
`MULTA_MONTO_DIARIO_GRAVE`, `MULTA_DIAS_LEVES`, `MULTA_CARGO_DANADO` y `MULTA_CARGO_DESTRUIDO`.
`calculador_configurado()` arma el calculador con esos valores.

### Cómo agregar una estrategia

Por ejemplo, un recargo para socios reincidentes:

1. Crear una subclase de `EstrategiaMulta` que implemente `calcular`.
2. Dársela al `CalculadorMulta` y agregar en `estrategias_para` la condición que la elige.

Ni el servicio de préstamos ni las otras estrategias cambian.

### Tests

`tests/test_multas.py` prueba cada estrategia por separado, qué estrategias elige el calculador
en cada caso (incluidos los límites de 7 y 8 días) y el detalle generado. `tests/test_prestamos.py`
verifica la devolución con atraso y daño, y la devolución destruida en término.

---

## Repository: acceso a datos

### Problema

Los servicios necesitan consultar y guardar entidades. Si cada servicio armara sus consultas con
SQLAlchemy directamente, la lógica de negocio quedaría mezclada con detalles de persistencia, y
las mismas consultas se repetirían en varios lugares (por ejemplo, "préstamos en curso de un
socio").

### Solución

Es la evolución del patrón DAO visto en clase (13.10): una clase por entidad que concentra su
acceso a datos. Una clase genérica resuelve las operaciones comunes y cada repositorio concreto
agrega sus consultas.

```mermaid
classDiagram
    class BaseRepository~T~ {
        <<generic>>
        +modelo: type
        +db: Session
        +obtener(id) T
        +listar() list~T~
        +agregar(entidad) T
        +eliminar(entidad)
    }
    class SocioRepository {
        +buscar_por_dni(dni)
        +buscar_por_email(email)
        +listar_filtrado(texto, habilitado)
    }
    class PrestamoRepository {
        +listar_filtrado(socio_id, estado)
        +contar_en_curso(socio_id) int
        +tiene_vencidos(socio_id, fecha) bool
    }
    class ReservaRepository {
        +activa_de_socio(socio_id, libro_id)
        +primera_pendiente(libro_id, sede_id)
        +disponibles_vencidas(fecha)
    }
    class Otros["SedeRepository, LibroRepository,<br/>EjemplarRepository, RemitoRepository"]
    BaseRepository <|-- SocioRepository
    BaseRepository <|-- PrestamoRepository
    BaseRepository <|-- ReservaRepository
    BaseRepository <|-- Otros
```

Cada repositorio concreto solo indica su modelo y hereda el resto:

```python
class SocioRepository(BaseRepository[Socio]):
    modelo = Socio

    def buscar_por_dni(self, dni):
        return self.db.scalar(select(Socio).where(Socio.dni == dni))
```

### Regla: el repositorio no hace commit

Los repositorios solo hacen `flush` (envían los cambios a la base dentro de la transacción) y el
**servicio** decide cuándo confirmar. Esto importa porque una operación de negocio toca varias
entidades. Por ejemplo, solicitar un préstamo interbibliotecario crea el préstamo, cambia el
estado del ejemplar, genera el remito y cierra la reserva. Si un repositorio confirmara por su
cuenta y después fallara una validación, quedaría la mitad de la operación guardada. Con un solo
commit al final del servicio, la operación entera se confirma o se descarta (unidad de trabajo,
14.3.3 del apunte).

### Beneficios

- Los servicios se leen como reglas de negocio, sin SQL.
- Cada consulta está en un solo lugar.
- Cambiar una consulta (por ejemplo, para optimizarla) no afecta a los servicios.

---

## Singleton: evaluado y descartado

El apunte presenta Singleton con el ejemplo de la conexión a la base de datos (15.3.2). Se
analizó para este proyecto y se decidió no aplicarlo:

1. **El engine ya es único.** `app/database.py` crea el `engine` de SQLAlchemy una vez, al
   importarse el módulo, y Python carga cada módulo una sola vez por proceso. El engine además
   administra un pool de conexiones. Envolverlo en un Singleton no agrega nada.

2. **La sesión no debe ser única.** La sesión de SQLAlchemy no es thread-safe y FastAPI atiende
   varias peticiones en paralelo. Con una sesión compartida, dos peticiones simultáneas mezclarían
   sus transacciones: el commit de una confirmaría cambios a medio hacer de la otra, y un error
   en una revertiría la otra. Por eso `get_db()` abre una sesión por petición y la cierra al
   terminar.

3. **Dificulta los tests.** Un Singleton es estado global. Con inyección de dependencias
   (`Depends(get_db)`), los tests reemplazan la sesión por una de prueba que se revierte al final
   de cada test, sin modificar el código de la aplicación.

El propio apunte señala estos problemas en 15.5.1 (acoplamiento global, dificultad para
testear, concurrencia). Entre las alternativas de 15.5.2 propone "considerar inyección de
dependencias en lugar de acceso global" y "preferir el enfoque de módulo en Python": son
exactamente las dos que se usaron (sesión inyectada por petición y engine a nivel de módulo).

---

## Otros recursos de POO utilizados

Sin ser patrones de diseño, el código usa los temas de la materia:

| Tema | Dónde |
|---|---|
| Clases abstractas (`ABC`, `@abstractmethod`) | `EstadoRemito`, `EstrategiaMulta` |
| Herencia y polimorfismo | Estados del remito, estrategias de multa, repositorios |
| Encapsulamiento y métodos de negocio en la entidad | `Socio.inhabilitar()`, `Sede.dar_de_baja()`, `Ejemplar.liberar()`, `Prestamo.activar()` |
| Propiedades (`@property`) | `Socio.nombre_completo`, `Ejemplar.esta_disponible`, `Remito.horas_en_transito` |
| Métodos mágicos | `__str__` en las entidades |
| Composición | `CalculadorMulta` contiene una estrategia; `Remito` contiene sus movimientos |
| Excepciones propias con jerarquía | `app/exceptions.py` |
