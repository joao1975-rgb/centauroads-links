"""
Entrada con Google: **quién eres**, no si puedes pasar.

Este fichero hace una sola cosa: comprobar que el identificador lo firmó Google, que no ha
caducado y que el correo está verificado. Devuelve de quién es. Nada más.

Lo único delicado es lo que NO hace: no se fía del correo que venga en el cuerpo de la petición.
El navegador puede decir lo que quiera. La única fuente válida es el identificador firmado por
Google, verificado contra sus claves públicas.

## Por qué ya no comprueba el dominio

Hasta la 002 esto exigía que el correo terminara en `@centauroads.com` (FR-001a). Ya no, y el
cambio es deliberado: el equipo entra con **su propia cuenta de Gmail**, la misma con la que usa
Canva (FR-119). Muchos no tienen cuenta del dominio.

La puerta no desaparece, se mueve: pasa a ser una **lista de autorizados**, que es
`panel_users` con `activo` en cierto. Eso es más estricto que un dominio, no menos —hay que
añadir a cada persona a mano— y tiene una consecuencia que conviene tener presente: como la
cuenta de Gmail sigue existiendo fuera de la empresa, **sacar a alguien de la lista es un paso
obligatorio de su baja** (FR-120).

Quien decide es `app/auth/rutas.py`, con la base de datos delante. Aquí no hay forma de saberlo.
"""

import os
import logging

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token

log = logging.getLogger("centaurads.auth")

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

    Devuelve {"email", "nombre"}. Lanza IdentidadRechazada si el identificador no vale.

    Que el correo sea auténtico **no significa que esa persona pueda entrar**: eso lo decide la
    lista de autorizados, en `app/auth/rutas.py`.
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

    return {"email": email, "nombre": datos.get("name", "") or email.split("@")[0]}
