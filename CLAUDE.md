# CLAUDE.md

Guía para trabajar en este repo. TP de la materia DAO (Desarrollo de Aplicaciones con Objetos):
backend del sistema de préstamos interbibliotecarios (consigna: Tema 1). El frontend lo hace otra
parte del grupo y consume esta API.

## Comandos

```bash
docker compose up --build              # API en :8000 + Postgres
docker compose exec api pytest         # tests
docker compose exec api python -m app.seed
alembic revision --autogenerate -m "descripcion"   # tras cambiar un modelo
alembic upgrade head
```

## Convenciones

- Python orientado a objetos con el estilo visto en clase: modelos SQLAlchemy con `Column`,
  clases abstractas con `ABC`/`@abstractmethod`, tests con pytest.
- Todo el código y los nombres en español, sin tildes en identificadores.
- Capas: `routers` (HTTP, sin lógica) -> `services` (reglas de negocio, commit) ->
  `repositories` (consultas, solo flush) -> `models`.
- Los errores de negocio se lanzan con las excepciones de `app/exceptions.py`; `main.py` las
  traduce a códigos HTTP. No usar `HTTPException` dentro de los servicios.
- Cualquier cambio de modelo va acompañado de su migración de Alembic.
- Cada regla de negocio nueva lleva su test.
- Documentar endpoints con un docstring corto (aparece en Swagger), sin comentarios de más.

## Patrones aplicados

- State: `app/domain/estados_remito.py` (ciclo de vida del remito).
- Strategy: `app/domain/multas.py` (cálculo de multas).
- Repository: `app/repositories/`.
- Singleton descartado a propósito; la justificación está en el README.

## Pendientes / ideas

- Historial de lecturas del socio (proceso opcional): sale casi directo de los préstamos
  devueltos de un socio; agregar `GET /socios/{id}/historial`.
- Otros opcionales de la consigna no encarados: notificaciones, recomendaciones,
  revisión de estado de recepción (extravío/daño/destrucción) como proceso propio.
- Las multas se registran pero no hay circuito de pago; podría inhabilitarse automáticamente
  al socio con multas impagas.
- `procesar-vencidas` de reservas se dispara a mano; podría correr al iniciar el día.
