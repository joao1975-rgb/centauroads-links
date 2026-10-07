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


def _igual(a: str, b: str) -> bool:
    # En bytes: con texto, `compare_digest` falla si hay letras fuera de ASCII (una ñ, una tilde).
    return secrets.compare_digest((a or "").encode("utf-8"), (b or "").encode("utf-8"))


# --- El superadmin como cuenta del panel (especificación 006) ------------------------------------
# Desde 2026-10-07 la credencial también abre sesión desde la pantalla de entrada normal. El
# superadmin es una fila más de la lista (rol admin) cuyo correo es SUPERADMIN_USER, **sin
# contraseña guardada**: la suya se comprueba siempre aquí, contra el entorno.

def usuario() -> str:
    """El identificador de su cuenta en la lista: SUPERADMIN_USER, en minúsculas."""
    return _valor("SUPERADMIN_USER").lower()


def es_superadmin(email: str) -> bool:
    """¿Es esa la cuenta del superadmin? Nunca, si la credencial no está configurada."""
    return esta_configurado() and _igual((email or "").strip().lower(), usuario())


def contrasena_valida(contrasena: str) -> bool:
    return esta_configurado() and _igual(contrasena, _valor("SUPERADMIN_PASS"))


def verifica(usuario: str, contrasena: str) -> None:
    """Deja pasar, o lanza. No devuelve nada: no hay nada que devolver."""
    if not esta_configurado():
        raise HTTPException(
            status_code=503,
            detail="Superadmin no configurado (SUPERADMIN_USER / SUPERADMIN_PASS)")
    # `compare_digest` y no `==`: la comparación normal se corta en el primer byte distinto, y
    # eso deja medir cuántos aciertas.
    bien = (_igual(usuario, _valor("SUPERADMIN_USER"))
            and _igual(contrasena, _valor("SUPERADMIN_PASS")))
    if not bien:
        raise HTTPException(status_code=401, detail="Credenciales inválidas")
