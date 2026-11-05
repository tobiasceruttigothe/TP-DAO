"""Las contrasenas nunca se guardan: se guarda su hash bcrypt, que incluye una sal aleatoria."""
import bcrypt

from app.config import settings


def generar_hash(contrasena: str) -> str:
    return bcrypt.hashpw(contrasena.encode("utf-8"), bcrypt.gensalt(rounds=settings.bcrypt_rondas)).decode("utf-8")


def verificar(contrasena: str, hash_guardado: str) -> bool:
    try:
        return bcrypt.checkpw(contrasena.encode("utf-8"), hash_guardado.encode("utf-8"))
    except ValueError:
        return False
