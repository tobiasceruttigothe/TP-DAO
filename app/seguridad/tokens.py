"""Tokens de sesion (JWT). El token lleva el id y el rol del usuario, firmado con el secreto
de la configuracion: el frontend lo manda en cada llamada y la API lo valida sin consultar
ninguna sesion guardada."""
import secrets
from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings

ALGORITMO = "HS256"


def crear_token_sesion(usuario_id: int, rol: str) -> str:
    vence = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_minutos)
    datos = {"sub": str(usuario_id), "rol": rol, "exp": vence}
    return jwt.encode(datos, settings.jwt_secreto, algorithm=ALGORITMO)


def leer_token_sesion(token: str) -> dict | None:
    """Devuelve los datos del token, o None si es invalido o vencio."""
    try:
        return jwt.decode(token, settings.jwt_secreto, algorithms=[ALGORITMO])
    except jwt.PyJWTError:
        return None


def crear_token_confirmacion() -> str:
    """Token aleatorio para el link de confirmacion de email."""
    return secrets.token_urlsafe(32)
