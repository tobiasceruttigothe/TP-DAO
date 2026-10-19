#!/bin/sh
set -e

# Aplica las migraciones pendientes antes de levantar la API
if [ "${RUN_MIGRATIONS:-1}" = "1" ]; then
    alembic upgrade head
fi

exec "$@"
