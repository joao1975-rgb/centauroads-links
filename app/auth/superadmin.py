"""
La credencial de arranque: `SUPERADMIN_USER` y `SUPERADMIN_PASS`.

No es una persona ni entra al panel. Es la llave de emergencia para dos cosas que, por
definición, no se pueden hacer desde dentro del panel:

  - cambiar la clave de administración del acortador (lo usa `app/main.py` desde antes);
  - **darle la primera contraseña a alguien de la lista**, cuando aún no ha entrado nadie.

Vive en su propio módulo porque la usan dos sitios, y dos implementaciones de la misma
comprobación acaban divergiendo: basta con que una olvide el `compare_digest` y la comparación
pase a filtrar por tiempo.

Si las variables no están, las rutas que dependen de esto responden 503, no 401: no es que la
credencial sea incorrecta, es que el servidor no tiene ninguna configurada, y son cosas distintas
para quien lo está intentando.
"""

import os
import secrets

from fastapi import HTTPException


def _valor(nombre: str) -> str:
    return os.getenv(nombre, "").strip()


def esta_configurado() -> bool:
    return bool(_valor("SUPERADMIN_USER") and _valor("SUPERADMIN_PASS"))


def verifica(usuario: str, contrasena: str) -> None:
    """Deja pasar, o lanza. No devuelve nada: no hay nada que devolver."""
    if not esta_configurado():
        raise HTTPException(
            status_code=503,
            detail="Superadmin no configurado (SUPERADMIN_USER / SUPERADMIN_PASS)")
    # `compare_digest` y no `==`: la comparación normal se corta en el primer byte distinto, y
    # eso deja medir cuántos aciertas.
    bien = (secrets.compare_digest(usuario or "", _valor("SUPERADMIN_USER"))
            and secrets.compare_digest(contrasena or "", _valor("SUPERADMIN_PASS")))
    if not bien:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
