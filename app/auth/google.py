"""
Entrada con la cuenta de Google del dominio (FR-001a).

Es el camino principal: `centauroads.com` está en Google Workspace, así que el alta y la baja de
una persona se hacen desde el admin de Google y aquí no hay contraseñas que guardar. Si alguien
pierde el portátil, se le corta el acceso en un solo sitio.

Lo único delicado de este fichero es lo que NO hace: no se fía del correo que venga en el cuerpo
de la petición. El navegador puede decir lo que quiera. La única fuente válida es el identificador
firmado por Google, verificado contra sus claves públicas, y de ahí se saca el correo.
"""

import os
import logging

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

log = logging.getLogger("centaurads.auth")

# El dominio de la empresa. Configurable, pero con el valor correcto por defecto para que no
# dependa de que alguien se acuerde de ponerlo.
DOMINIO = os.getenv("GOOGLE_DOMINIO", "centauroads.com").strip().lower()

EMISORES_VALIDOS = {"accounts.google.com", "https://accounts.google.com"}


class IdentidadRechazada(Exception):
    """El identificador no vale, o vale pero la cuenta no es de las nuestras."""


def _client_id() -> str:
    return os.getenv("GOOGLE_CLIENT_ID", "").strip()


def esta_configurado() -> bool:
    """
    ¿Se puede ofrecer el botón de Google?

    Si no hay GOOGLE_CLIENT_ID, la pantalla de entrada debe mostrar solo la vía de contraseña, en
    vez de enseñar un botón que fallaría al pulsarlo.
    """
    return bool(_client_id())


def verificar_identidad(token: str) -> dict:
    """
    Comprueba el identificador que devuelve Google Sign-In y devuelve a quién pertenece.

    Devuelve {"email", "nombre"}. Lanza IdentidadRechazada si algo no cuadra.
    """
    if not esta_configurado():
        raise IdentidadRechazada("La entrada con Google no está configurada en este servidor")
    if not token:
        raise IdentidadRechazada("No llegó el identificador de Google")

    try:
        datos = google_id_token.verify_oauth2_token(
            token, google_requests.Request(), _client_id()
        )
    except ValueError as e:
        # Firma inválida, caducado, o destinado a otra aplicación.
        log.warning("Identificador de Google rechazado: %s", e)
        raise IdentidadRechazada("El identificador de Google no es válido") from e

    if datos.get("iss") not in EMISORES_VALIDOS:
        raise IdentidadRechazada("El identificador no lo emitió Google")

    # Una cuenta con el correo sin verificar no prueba nada sobre quién la usa.
    if not datos.get("email_verified"):
        raise IdentidadRechazada("La cuenta de Google no tiene el correo verificado")

    email = (datos.get("email") or "").strip().lower()
    if not email:
        raise IdentidadRechazada("El identificador no trae correo")

    # La restricción de dominio. Se comprueba sobre el correo verificado por Google, nunca sobre
    # lo que diga el cliente. `hd` es la pista de Workspace; el sufijo del correo es la garantía.
    dominio_cuenta = (datos.get("hd") or "").strip().lower()
    if not email.endswith("@" + DOMINIO) or (dominio_cuenta and dominio_cuenta != DOMINIO):
        log.warning("Entrada rechazada: %s no pertenece a %s", email, DOMINIO)
        raise IdentidadRechazada(f"Solo se admiten cuentas de {DOMINIO}")

    return {"email": email, "nombre": datos.get("name", "") or email.split("@")[0]}
