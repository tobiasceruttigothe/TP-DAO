# Manual del administrador

Este manual es para el **personal de la biblioteca**. Recorre el panel de gestión: cómo atender
los pedidos de los socios, registrar préstamos y devoluciones, seguir los envíos entre sedes,
administrar el catálogo, hacer inventarios y consultar los reportes.

Usuario de prueba: `admin@example.com` / `admin123`.

Índice:

1. [Ingresar y moverse por el panel](#1-ingresar-y-moverse-por-el-panel)
2. [Inicio](#2-inicio)
3. [Pedidos de socios](#3-pedidos-de-socios)
4. [Préstamos](#4-préstamos)
5. [Remitos: envíos entre sedes](#5-remitos-envíos-entre-sedes)
6. [Reservas](#6-reservas)
7. [Catálogo y ejemplares](#7-catálogo-y-ejemplares)
8. [Inventario](#8-inventario)
9. [Etiquetas](#9-etiquetas)
10. [Socios](#10-socios)
11. [Usuarios](#11-usuarios)
12. [Sedes](#12-sedes)
13. [Incidencias](#13-incidencias)
14. [Reportes](#14-reportes)
15. [Notificaciones y correos](#15-notificaciones-y-correos)
16. [Circuito completo de un préstamo entre sedes](#16-circuito-completo-de-un-préstamo-entre-sedes)

---

## 1. Ingresar y moverse por el panel

El administrador ingresa desde la misma pantalla que los socios. Al ingresar, el sistema lo lleva
directo al panel.

![Ingreso del administrador](img/admin/01-ingresar.png)

El panel tiene:

- **Menú lateral** con todas las secciones. La flecha de abajo lo achica para ganar espacio.
- **Sitio público**: abre el catálogo tal como lo ve un visitante.
- **Campana**: los avisos sin leer (nuevos socios para aprobar, nuevos pedidos).
- **Administrador**: muestra el email de la cuenta y la opción **Cerrar sesión**.

![Menú del usuario](img/admin/06-menu-usuario.png)

Todos los listados del panel están **paginados** y la mayoría tiene filtros arriba a la derecha
(búsqueda, estado, sede o fechas).

## 2. Inicio

Es el resumen del estado de la red:

- **Préstamos activos**, **Ejemplares en tránsito**, **Préstamos vencidos** y **Multas
  pendientes** (lo que se cobraría si hoy se devolvieran los vencidos).
- **Próximos vencimientos**: los préstamos que vencen primero; los vencidos se marcan en rojo con
  los días de atraso.
- **En viaje entre sedes**: los remitos despachados que todavía no llegaron.
- **Envíos exitosos** y **Con incidencias**: porcentaje de envíos sin problemas y con daños,
  destrucciones o extravíos.

![Inicio del panel](img/admin/02-inicio.png)

Arriba están los accesos **Nuevo préstamo** y **Procesar vencimientos**.

### Procesar vencimientos

Algunas reglas dependen del paso del tiempo y el sistema las aplica solo cada hora:

1. Vence las reservas que no se retiraron a tiempo y ofrece el ejemplar al siguiente en espera.
2. Inhabilita a los socios con un préstamo vencido hace más de 30 días.
3. Avisa a los socios cuyos préstamos están por vencer o ya vencieron.

El botón **Procesar vencimientos** lo corre en el momento. Pide confirmación:

![Confirmar procesar vencimientos](img/admin/03-procesar-vencimientos.png)

Y muestra el resultado:

![Vencimientos procesados](img/admin/04-vencimientos-procesados.png)

### La campana

Muestra los últimos avisos. Desde ahí se pueden marcar todos como leídos o ir a *Ver todas*.

![Campana de notificaciones](img/admin/05-campana.png)

## 3. Pedidos de socios

Los socios no reservan directamente: piden un libro desde el catálogo y eligen la sede donde
quieren retirarlo. Los pedidos llegan a esta pantalla, que por defecto muestra los
**pendientes**. El filtro de arriba a la derecha permite ver los de otro estado.

![Pedidos pendientes](img/admin/07-pedidos.png)

Con **Resolver** se abre el pedido, con el socio, la sede pedida, la fecha y el comentario, si lo
dejó. Hay tres formas de atenderlo:

![Resolver un pedido](img/admin/08-resolver-pedido.png)

| Opción | Qué hace el sistema |
|---|---|
| **Reservar** en la sede pedida | Crea una reserva. Si hay un ejemplar libre, queda apartado para el socio; si no, el botón dice **Reservar en espera** y el socio entra en la lista de espera |
| **Traer desde otra sede** (*Enviar desde acá*) | Crea un préstamo inter-sede desde la sede elegida hasta la del pedido, con su remito. Solo se listan las sedes con ejemplares libres |
| **Rechazar pedido** | Pide un motivo, que le llega al socio |

Al resolverlo, el pedido sale de la lista de pendientes y el socio recibe el aviso:

![Pedido resuelto](img/admin/09-pedido-resuelto.png)

Para rechazar, se escribe el motivo y se confirma con **Confirmar rechazo**:

![Rechazar un pedido](img/admin/10-rechazar-pedido.png)

## 4. Préstamos

Lista todos los préstamos con su número, socio, libro y código de ejemplar, tipo (**Local** o
**Inter-sede**), sedes, estado, fechas, atraso y multa. Los vencidos se resaltan en rojo y
muestran la **multa a la fecha**.

![Listado de préstamos](img/admin/11-prestamos.png)

Arriba se filtra por socio (buscando por apellido, nombre o DNI) y por estado:

![Préstamos de un socio](img/admin/12-prestamos-busqueda.png)

Estados de un préstamo:

| Estado | Qué significa |
|---|---|
| **Solicitado** | Préstamo inter-sede creado; el ejemplar todavía no salió de la sede de origen |
| **En tránsito** | El remito de ida se despachó y el ejemplar está viajando |
| **Activo** | El socio tiene el libro. En los inter-sede, el plazo empieza al llegar |
| **Devuelto** | Ya se registró la devolución |
| **Cancelado** | Se canceló el envío, o el ejemplar se extravió o llegó destruido |

### Registrar un préstamo

Con **Nuevo préstamo** se carga un préstamo en el mostrador:

1. **Socio**: se busca por apellido, nombre o DNI.
2. **Libro**: se busca por título o autor. Aparece una tabla con los ejemplares libres de cada
   sede.
3. **Sede de origen**: la sede dueña del ejemplar (solo se listan las que tienen libres).
4. **Ejemplar**: el código del ejemplar que se entrega.
5. **Sede donde retira el socio**. Si es la misma que la de origen, es un **préstamo local**: el
   socio se lo lleva en el momento. Si es otra, es un **préstamo inter-sede** y se genera el
   remito de envío.

![Nuevo préstamo](img/admin/16-nuevo-prestamo.png)

Con **Registrar préstamo** queda creado:

![Préstamo registrado](img/admin/17-prestamo-registrado.png)

El sistema no deja prestar si el socio está inhabilitado, si tiene préstamos vencidos, si ya
tiene 3 préstamos en curso o si el ejemplar no está disponible (o está reservado para otro
socio).

### Registrar una devolución

En el préstamo activo, **Devolver** abre la ventana de devolución. Muestra el vencimiento y, si
hay atraso, la multa a la fecha. Se completa:

- **Estado físico**: Bueno, Regular, Dañado o Destruido.
- **Fecha de devolución** (por defecto, hoy).
- **Observaciones** (opcional).

![Registrar devolución](img/admin/13-devolucion.png)

Al registrarla, el sistema muestra la multa calculada con su detalle:

![Devolución registrada con multa](img/admin/14-devolucion-registrada.png)

| Situación | Multa |
|---|---|
| Atraso de 1 a 7 días | $500 por día |
| Atraso de 8 días o más | Los primeros 7 días a $500 y los siguientes a $1.000 |
| Devuelto dañado | Se suman $5.000 |
| Devuelto destruido | Se suman $20.000 |

Qué pasa con el ejemplar después de la devolución:

- **Préstamo local**: vuelve a estar disponible (o pasa a *en reparación* si volvió dañado) y se
  le ofrece a la primera reserva en espera.
- **Préstamo inter-sede**: se genera el **remito de retorno** hacia la sede de origen.
- **Destruido**: el ejemplar se da de baja y no se genera retorno.

### Ver los remitos de un préstamo

En los préstamos inter-sede, **Remitos** muestra los envíos asociados (ida y retorno) con su
estado, y **Ver** lleva al detalle de cada uno.

![Remitos de un préstamo](img/admin/15-remitos-de-prestamo.png)

## 5. Remitos: envíos entre sedes

Cada préstamo inter-sede genera un **remito de ida** al crearse y un **remito de retorno** al
devolverse. Esta pantalla los lista con su número, tipo, libro, recorrido, estado y fechas. Se
puede filtrar por sede (origen o destino) y por estado.

![Listado de remitos](img/admin/18-remitos.png)

Al hacer clic en el número se abre el detalle, que muestra:

- El **avance** del envío: Pendiente → Empaquetado → Despachado → Recibido.
- Los **datos del envío**: libro, ejemplar, sedes, fechas y estado del ejemplar al llegar.
- La **trazabilidad**: cada cambio de estado con su fecha y observación.
- Arriba, los botones de las acciones posibles en el estado actual.

![Remito pendiente](img/admin/19-remito-pendiente.png)

### Avanzar el envío

Cada acción pide una observación opcional y confirmación:

1. **Empaquetar**: la sede de origen preparó el paquete.

   ![Empaquetar](img/admin/20-empaquetar.png)

2. **Despachar**: el paquete salió. El préstamo y el ejemplar pasan a *en tránsito*.

   ![Remito despachado](img/admin/21-remito-despachado.png)

3. **Registrar recepción**: la sede de destino lo recibió. Se indica la **revisión del
   ejemplar** (Bueno, Regular, Dañado o Destruido).

   ![Registrar recepción](img/admin/22-registrar-recepcion.png)

   Con el remito de ida recibido, el préstamo queda **activo**, empieza a correr el plazo y el
   socio recibe el aviso de que puede retirarlo. Con el de retorno, el ejemplar vuelve a estar
   disponible en su sede.

   ![Remito recibido](img/admin/23-remito-recibido.png)

### Situaciones excepcionales

| Acción | Cuándo se puede | Qué pasa |
|---|---|---|
| **Cancelar envío** | Solo el remito de ida, antes de despacharlo | Se cancela el préstamo y el ejemplar vuelve a estar disponible |
| **Marcar extraviado** | Con el remito despachado | El ejemplar queda extraviado, se registra una incidencia y, si era el de ida, se cancela el préstamo |
| Recibir **Dañado** | Al registrar la recepción | Se registra una incidencia de daño. En la ida, el socio igual puede usarlo; en el retorno, el ejemplar pasa a reparación |
| Recibir **Destruido** | Al registrar la recepción | Se registra la incidencia, el ejemplar se da de baja y, si era la ida, se cancela el préstamo |

## 6. Reservas

Una reserva aparta un ejemplar de una sede para un socio. Se listan con el socio, el libro, la
sede, el estado, el ejemplar apartado y la fecha límite para retirarlo. Se filtra por socio y
por estado.

![Reservas](img/admin/24-reservas.png)

| Estado | Qué significa |
|---|---|
| **En espera** | No había ejemplares libres en la sede; el socio está en la lista de espera |
| **Lista para retirar** | Hay un ejemplar apartado; el socio tiene 3 días para retirarlo |
| **Cumplida** | El socio retiró el libro (se registró el préstamo) |
| **Vencida** | Pasaron los 3 días sin retirarlo; el ejemplar pasó al siguiente en espera |
| **Cancelada** | La canceló el socio o un administrador |

### Nueva reserva

Con **Nueva reserva** se elige el socio, el libro y la sede. Cada sede indica cuántos ejemplares
libres tiene y si se aparta uno en el momento.

![Nueva reserva](img/admin/25-nueva-reserva.png)

![Reserva creada](img/admin/26-reserva-creada.png)

### Prestar una reserva

Cuando el socio viene a buscar el libro, **Prestar** registra el préstamo del ejemplar apartado
y la reserva pasa a *cumplida*. Pide confirmación:

![Prestar el ejemplar apartado](img/admin/27-prestar-reserva.png)

**Procesar vencidas** vence en el momento las reservas cuyo plazo pasó (el sistema también lo
hace solo cada hora).

## 7. Catálogo y ejemplares

El **libro** es la obra (ISBN, título, autor) y el **ejemplar** es cada copia física, con su
código de inventario y su sede. El catálogo lista los libros y se busca por título o autor.

![Catálogo](img/admin/28-catalogo.png)

### Nuevo libro

**Nuevo libro** pide ISBN (ISBN-10 o ISBN-13 con dígito verificador válido; los guiones se
quitan solos), título y autor, y opcionalmente editorial, año de publicación y género. No se
puede repetir un ISBN. **Editar** permite corregir los datos de un libro.

![Nuevo libro](img/admin/29-nuevo-libro.png)

### Detalle del libro

Al hacer clic en el título (o en **Ejemplares**) se abre el detalle del libro:

- **Datos** del libro.
- **Disponibilidad** por sede: cuántos ejemplares libres hay y sus códigos.
- **Ejemplares**: cada copia con su sede, estado y estado físico.
- Arriba, los atajos **Editar**, **Reservar** y **Prestar**.

![Detalle del libro](img/admin/30-libro-detalle.png)

Acciones sobre cada ejemplar:

| Acción | Qué hace |
|---|---|
| **Extraviado** | Lo marca como perdido; deja de figurar como disponible |
| **Apareció** | Un ejemplar extraviado que se encontró vuelve a circular (y se asigna a la primera reserva en espera) |
| **Dar de baja** | Lo saca de circulación. Solo si está disponible o en reparación |

### Agregar un ejemplar

**Agregar ejemplar** pide el código de inventario (único en toda la red), la sede y el estado
físico.

![Agregar ejemplar](img/admin/31-agregar-ejemplar.png)

## 8. Inventario

El inventario es el **recuento físico** de los estantes de una sede: se lee el código de cada
ejemplar (con lector de código de barras o escribiéndolo) y el sistema lo compara con lo que
debería estar ahí.

![Inventarios](img/admin/36-inventarios.png)

### Iniciar un inventario

**Iniciar inventario** pide la sede y una observación opcional. Solo puede haber un inventario en
curso por sede.

![Iniciar inventario](img/admin/32-iniciar-inventario.png)

### Leer los códigos

En el campo **Leer códigos** se escanea o escribe cada código y se aprieta Enter. Cada lectura
responde en el momento:

| Resultado | Significado |
|---|---|
| **Encontrado** | El ejemplar es de esta sede y debería estar en el estante |
| **Fuera de lugar** | Existe, pero no debería estar acá (es de otra sede, figura prestado, en tránsito, extraviado o de baja) |
| **Desconocido** | El código no corresponde a ningún ejemplar |

Un código repetido se avisa y no se cuenta dos veces. Una lectura equivocada se puede
**Deshacer**. Arriba se ve el avance (cuántos de los esperados se leyeron) y abajo el informe en
vivo, con los **faltantes**: ejemplares que deberían estar en el estante y no se leyeron.

![Lecturas del inventario](img/admin/33-inventario-lecturas.png)

### Cerrar el inventario

**Cerrar inventario** guarda el informe tal como está y no acepta más lecturas:

![Cerrar inventario](img/admin/34-cerrar-inventario.png)

![Inventario cerrado](img/admin/35-inventario-cerrado.png)

Desde el informe se puede actuar: un faltante se marca como **extraviado**, y un ejemplar
extraviado que apareció se marca como **recuperado**.

## 9. Etiquetas

Genera los **códigos de barras** de los ejemplares, listos para imprimir y pegar en los libros.
Se filtra por sede, por libro o por estado, y **Imprimir** abre la impresión del navegador con
las etiquetas.

![Etiquetas con códigos de barras](img/admin/37-etiquetas.png)

## 10. Socios

Lista los socios con DNI, email, teléfono, fecha de alta y estado. Se busca por nombre, apellido
o DNI y se filtra por estado.

![Socios](img/admin/38-socios.png)

En la columna **Estado** se ve:

- **Habilitado** o **Inhabilitado** (con el motivo debajo).
- **Con vencidos**: tiene préstamos vencidos y no puede pedir otro hasta devolverlos. No cambia
  su estado: es una traba temporal.

### Nuevo socio y edición

**Nuevo socio** da de alta a un socio desde el mostrador: DNI, nombre, apellido, email y
teléfono opcional. No se pueden repetir el DNI ni el email. **Editar** corrige los datos.

![Nuevo socio](img/admin/39-nuevo-socio.png)

### Ficha del socio

Al hacer clic en el nombre se abre su ficha, con los **préstamos** y el **historial de
lecturas** (los libros que ya devolvió).

![Ficha del socio](img/admin/40-ficha-socio.png)

### Inhabilitar y habilitar

**Inhabilitar** pide un motivo; un socio inhabilitado no puede pedir, reservar ni recibir
préstamos. **Habilitar** lo vuelve a la normalidad. El sistema también inhabilita solo a quien
tiene un préstamo vencido hace más de 30 días.

![Inhabilitar socio](img/admin/41-inhabilitar-socio.png)

## 11. Usuarios

Administra las **cuentas** del sistema (socios y administradores).

### Por aprobar

Las personas que se registraron y confirmaron su email esperan acá la aprobación:

![Cuentas por aprobar](img/admin/42-usuarios-por-aprobar.png)

- **Aprobar** habilita al socio y le manda el correo *Tu cuenta fue aprobada*.

  ![Aprobar cuenta](img/admin/43-aprobar-cuenta.png)

- **Rechazar** pide un motivo, que se le informa por correo.

  ![Rechazar cuenta](img/admin/44-rechazar-cuenta.png)

### Todas las cuentas

Lista todas las cuentas con su rol y estado (*Sin confirmar email*, *Esperando aprobación*,
*Activa*, *Rechazada*) y se filtra por texto, rol y estado.

![Todas las cuentas](img/admin/45-todas-las-cuentas.png)

### Nuevo administrador

Los administradores no se registran solos: los crea otro administrador con **Nuevo
administrador** (nombre, email y contraseña de al menos 8 caracteres, con letras y números).

![Nuevo administrador](img/admin/46-nuevo-administrador.png)

## 12. Sedes

Lista las bibliotecas de la red con dirección, teléfono, email, horario y estado. Arriba se
eligen **Todas**, **Activas** o **Dadas de baja**.

![Sedes](img/admin/47-sedes.png)

- **Nueva sede** y **Editar**: nombre y dirección obligatorios; teléfono, email y horario
  opcionales.

  ![Editar sede](img/admin/48-editar-sede.png)

- **Dar de baja**: la sede deja de usarse para nuevos préstamos, reservas y envíos, pero se
  conserva para el historial y los reportes. **Reactivar** la vuelve a habilitar. Los remitos de
  retorno se despachan igual aunque una sede esté de baja, para que ningún ejemplar quede varado.

## 13. Incidencias

Registra los problemas detectados en los envíos: **daño**, **destrucción** y **extravío**. Cada
una muestra la fecha, el tipo, el remito (con enlace al detalle), el recorrido y la descripción.
Se filtra por rango de fechas, sede y tipo.

![Incidencias](img/admin/49-incidencias.png)

Las incidencias no se cargan a mano: las genera el sistema al recibir un remito dañado o
destruido, o al marcarlo extraviado.

## 14. Reportes

Seis reportes, cada uno en su pestaña:

### Activos y en tránsito

Los préstamos activos (con la marca de vencido) y el material que está viajando, con las horas
que lleva en viaje.

![Reporte: activos y en tránsito](img/admin/50-reporte-1.png)

### Vencidos y multas

Por socio: préstamos vencidos, multas cobradas, multas pendientes estimadas y total acumulado.
Se puede calcular a otra fecha con **Calcular a la fecha**, y el **+** despliega el detalle de
cada socio.

![Reporte: vencidos y multas](img/admin/51-reporte-2.png)

### Más solicitados

Ranking de libros por cantidad de préstamos inter-sede, con gráfico y tabla. Se filtra por
período y se elige cuántos libros mostrar.

![Reporte: más solicitados](img/admin/52-reporte-3.png)

### Disponibilidad por sede

Por sede: títulos distintos, ejemplares y su reparto entre disponibles, prestados o reservados,
en tránsito y fuera de circulación, con el porcentaje disponible.

![Reporte: disponibilidad por sede](img/admin/53-reporte-4.png)

### Envíos e incidencias

Tasa de envíos exitosos y con incidencias, y la cantidad de remitos por resultado. Los
cancelados no cuentan para la tasa porque no llegaron a viajar.

![Reporte: envíos e incidencias](img/admin/54-reporte-5.png)

### Movimientos entre sedes

Por cada ruta origen → destino: envíos, recibidos, incidencias y tiempo promedio de tránsito. Se
filtra por período y las columnas se pueden ordenar.

![Reporte: movimientos entre sedes](img/admin/55-reporte-6.png)

## 15. Notificaciones y correos

La pantalla de notificaciones (desde *Ver todas* en la campana) lista todos los avisos del
administrador, con los filtros **Todas** y **Sin leer** y el botón **Marcar todas como leídas**.

![Notificaciones del administrador](img/admin/56-notificaciones.png)

| Aviso para los administradores | Cuándo llega |
|---|---|
| Nuevo socio para aprobar | Cuando alguien se registra y confirma su email |
| Nuevo pedido de un socio | Cuando un socio pide un libro |

Los avisos también salen por correo. En este proyecto los correos van a **Mailpit**
(http://localhost:8025), una bandeja de prueba que guarda todo lo que manda el sistema sin
enviarlo a internet. Ahí se ven tanto los correos para los administradores como los que reciben
los socios (confirmación de email, cuenta aprobada, etc.).

![Bandeja de Mailpit](img/admin/57-mailpit.png)

## 16. Circuito completo de un préstamo entre sedes

Resumen de cómo se combinan las pantallas cuando un socio pide un libro que está en otra sede:

```mermaid
sequenceDiagram
    participant S as Socio
    participant A as Administrador
    participant O as Sede de origen
    participant D as Sede de retiro
    S->>A: Pide el libro desde el catálogo (Pedidos)
    A->>O: Resolver → Enviar desde acá (se crea el préstamo y el remito de ida)
    O->>O: Remito: Empaquetar
    O->>D: Remito: Despachar (préstamo en tránsito)
    D->>D: Remito: Registrar recepción (préstamo activo, empieza el plazo)
    D-->>S: Aviso "llegó a la sede"
    S->>D: Retira y después devuelve el libro (Préstamos → Devolver)
    D->>O: Remito de retorno: Empaquetar, Despachar
    O->>O: Registrar recepción (el ejemplar vuelve a estar disponible)
```
