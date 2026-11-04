# CLAUDE.md

Guía para trabajar en este repo. TP de la materia DAO (Desarrollo de Aplicaciones con Objetos):
sistema de préstamos interbibliotecarios (consigna: Tema 1). Backend en Python (`app/`) y
frontend en React (`frontend/`, con su propio README y convenciones).

## Comandos

```bash
docker compose up --build              # web :3000, API :8000, Mailpit :8025, pgAdmin :5050, Postgres
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
- Permisos en los routers con las dependencias de `app/routers/dependencias.py`: `SOLO_ADMIN` para
  el panel, `socio_actual` para `/mi/...`. Un endpoint nuevo del panel lleva `SOLO_ADMIN` y su
  caso en `tests/test_permisos.py`.
- Los avisos a usuarios se publican como eventos (`app/services/eventos.py`), nunca mandando el
  correo desde el servicio. Los correos salen recién después del commit.
- En los tests, `client` es un administrador, `anonimo` no tiene sesión y `socio_conectado` da
  (cliente, socio). Los correos enviados quedan en el fixture `correos`.
- Las búsquedas por texto usan `contiene()` de `app/repositories/base.py` (ignora tildes).
- Las reglas de formato están en `app/schemas/validaciones.py` y su espejo en
  `frontend/src/utiles/reglas.js`: si se cambia una, cambiar la otra. Los DTO de respuesta no
  heredan de los de entrada (no tienen que validar datos que ya están en la base).

## Patrones aplicados

- State: `app/domain/estados_remito.py` (ciclo de vida del remito).
- Strategy: `app/domain/multas.py` (cálculo de multas).
- Repository: `app/repositories/`.
- Observer: `app/services/eventos.py` y `app/services/notificaciones.py` (notificaciones y correo).
- Singleton descartado a propósito; la justificación está en el README. Keycloak también
  (ver `docs/patrones-de-diseno.md`): el login es propio con JWT + bcrypt.

## Pendientes / ideas

- Opcional de la consigna no encarado: recomendaciones.
- Las multas se registran pero no hay circuito de pago; podría inhabilitarse automáticamente
  al socio con multas impagas.
- No hay "olvidé mi contraseña": se podría reutilizar el token de confirmación por correo.
