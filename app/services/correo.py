"""Envio de correos. La implementacion se elige por configuracion (CORREO_MODO)."""
import logging
import smtplib
import threading
from abc import ABC, abstractmethod
from dataclasses import dataclass
from email.message import EmailMessage

from app.config import settings

log = logging.getLogger("uvicorn.error")


@dataclass
class Correo:
    destinatario: str
    asunto: str
    texto: str
    html: str


class ServicioCorreo(ABC):
    @abstractmethod
    def enviar(self, correo: Correo):
        pass


class CorreoSmtp(ServicioCorreo):
    """Envia por SMTP en un hilo aparte, asi la respuesta de la API no espera al servidor de correo."""

    def enviar(self, correo: Correo):
        threading.Thread(target=self._enviar, args=(correo,), daemon=True).start()

    def _enviar(self, correo: Correo):
        mensaje = EmailMessage()
        mensaje["From"] = settings.correo_remitente
        mensaje["To"] = correo.destinatario
        mensaje["Subject"] = correo.asunto
        mensaje.set_content(correo.texto)
        mensaje.add_alternative(correo.html, subtype="html")
        try:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_puerto, timeout=15) as smtp:
                if settings.smtp_tls:
                    smtp.starttls()
                if settings.smtp_usuario:
                    smtp.login(settings.smtp_usuario, settings.smtp_contrasena)
                smtp.send_message(mensaje)
        except Exception:
            # Un correo que no sale no debe romper la operacion que lo genero
            log.exception("No se pudo enviar el correo a %s", correo.destinatario)


class CorreoEnMemoria(ServicioCorreo):
    """Guarda los correos en una lista. Se usa en los tests."""

    enviados: list[Correo] = []

    def enviar(self, correo: Correo):
        CorreoEnMemoria.enviados.append(correo)


class CorreoDesactivado(ServicioCorreo):
    def enviar(self, correo: Correo):
        pass


def correo_configurado() -> ServicioCorreo:
    modos = {"smtp": CorreoSmtp, "memoria": CorreoEnMemoria, "desactivado": CorreoDesactivado}
    return modos.get(settings.correo_modo, CorreoDesactivado)()


def armar_correo(destinatario: str, titulo: str, mensaje: str, enlace: str | None = None) -> Correo:
    """Correo con el formato comun del sistema: titulo, mensaje y un boton opcional."""
    url = f"{settings.url_frontend}{enlace}" if enlace else None
    boton = (
        f'<p><a href="{url}" style="background:#1677ff;color:#fff;padding:10px 18px;'
        f'border-radius:6px;text-decoration:none;display:inline-block">Ir al sistema</a></p>'
        if url
        else ""
    )
    html = f"""<div style="font-family:Arial,sans-serif;max-width:520px;margin:auto;color:#262626">
  <h2 style="color:#1677ff">Red de Bibliotecas</h2>
  <h3>{titulo}</h3>
  <p>{mensaje}</p>
  {boton}
  <p style="color:#8c8c8c;font-size:12px">Este es un mensaje automático, no hace falta responderlo.</p>
</div>"""
    texto = f"{titulo}\n\n{mensaje}" + (f"\n\n{url}" if url else "")
    return Correo(destinatario=destinatario, asunto=titulo, texto=texto, html=html)
