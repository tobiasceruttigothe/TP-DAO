# CLAUDE.md

Guía para trabajar en este repo. TP de la materia DAO (Desarrollo de Aplicaciones con Objetos):
sistema de préstamos interbibliotecarios (consigna: Tema 1). Backend en Python (`app/`) y
frontend en React (`frontend/`, con su propio README y convenciones).

## Comandos

```bash
docker compose up --build              # web en :3000, API en :8000, Postgres
docker compose exec api pytest         # tests
docker compose exec api python -m app.seed
alembic revision --autogenerate -m "descripcion"   # tras cambiar un modelo
alembic upgrade head
cd frontend && npm run dev             # front con recarga automatica en :5173
cd frontend && npm run lint
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
- Los listados nuevos se paginan con `BaseRepository.paginar` y responden `Pagina[...]`.
- Documentar endpoints con un docstring corto (aparece en Swagger), sin comentarios de más.
- Si un cambio afecta el modelo, un patrón, un proceso o una regla, actualizar el documento
  correspondiente en `docs/`. Los diagramas son Mermaid (GitHub los dibuja).
- Si se agrega un estado en un enum del backend, agregarlo también en `frontend/src/utiles/estados.js`.
- Las búsquedas por texto usan `contiene()` de `app/repositories/base.py` (ignora tildes).

## Patrones aplicados

- State: `app/domain/estados_remito.py` (ciclo de vida del remito).
- Strategy: `app/domain/multas.py` (cálculo de multas).
- Repository: `app/repositories/`.
- Singleton descartado a propósito; la justificación está en el README.

## Pendientes / ideas

- Opcionales de la consigna no encarados: notificaciones, recomendaciones, inventario con códigos.
- Las multas se registran pero no hay circuito de pago; podría inhabilitarse automáticamente
  al socio con multas impagas.
- `procesar-vencidas` de reservas se dispara a mano; podría correr al iniciar el día.
- El número de remito se calcula como el último id + 1: dos remitos creados al mismo tiempo
  pueden chocar. Usar una secuencia de la base.
