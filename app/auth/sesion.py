"""
Sesiones del panel.

Una cookie firmada con el identificador del usuario y el momento en que entró. Firmada, no
cifrada: el navegador puede leer quién es, pero no puede fabricar una sesión ajena sin la clave.
No guardamos nada sensible dentro, así que con la firma basta.

La clave de firma viene del entorno (Principio V: ningún secreto en el código). Si falta, se
genera una y se guarda en el volumen persistente, avisando por log: es una configuración que
alguien debería arreglar, no un estado normal.
"""

import os
import secrets
import logging
from typing import Optional

from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

log = logging.getLogger("centaurads.auth")

COOKIE = "centauro_sesion"
# Ocho horas: una jornada. Al día siguiente se vuelve a entrar, que en equipos compartidos
# importa más que la comodidad.
DURACION_SEGUNDOS = 8 * 60 * 60


def _clave_de_sesion() -> str:
    """
    La clave de firma. Orden: variable de entorno > fichero persistente > generada.

    En producción debe venir de SESSION_SECRET. Si no está, se genera una y se guarda junto a la
    base de datos, en el volumen persistente, para que las sesiones sobrevivan a un reinicio.
    """
    desde_entorno = os.getenv("SESSION_SECRET", "").strip()
    if desde_entorno:
        return desde_entorno

    ruta = os.getenv("SESSION_SECRET_FILE", "data/session.key")
    if os.path.exists(ruta):
        with open(ruta, "r") as f:
            guardada = f.read().strip()
            if guardada:
                return guardada

    generada = secrets.token_urlsafe(48)
    os.makedirs(os.path.dirname(ruta) or ".", exist_ok=True)
    with open(ruta, "w") as f:
        f.write(generada)
    log.warning(
        "SESSION_SECRET no configurada: se generó una y se guardó en %s. "
        "Definirla como variable de entorno para no depender del disco.", ruta
    )
    return generada


_serializador = URLSafeTimedSerializer(_clave_de_sesion(), salt="sesion-panel")


def crear(user_id: int, email: str) -> str:
    """Devuelve el valor firmado que va en la cookie."""
    return _serializador.dumps({"uid": user_id, "email": email})


def leer(valor: Optional[str]) -> Optional[dict]:
    """
    Devuelve el contenido de la sesión, o None si no vale.

    No distingue entre caducada y falsificada de cara a quien llama: en ambos casos hay que volver
    a entrar. La diferencia sí se registra, porque una firma inválida puede ser un intento real.
    """
    if not valor:
        return None
    try:
        return _serializador.loads(valor, max_age=DURACION_SEGUNDOS)
    except SignatureExpired:
        return None
    except BadSignature:
        log.warning("Cookie de sesión con firma inválida: se descarta")
        return None


def poner(respuesta, user_id: int, email: str) -> None:
    """Deja la cookie en la respuesta, con las protecciones habituales."""
    respuesta.set_cookie(
        COOKIE,
        crear(user_id, email),
        max_age=DURACION_SEGUNDOS,
        httponly=True,      # el JavaScript de la página no puede leerla
        samesite="lax",     # no viaja en peticiones desde otros sitios
        secure=os.getenv("COOKIE_INSEGURA", "") != "1",  # solo HTTPS, salvo en desarrollo local
        path="/",
    )


def quitar(respuesta) -> None:
    respuesta.delete_cookie(COOKIE, path="/")
