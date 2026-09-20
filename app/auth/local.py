"""
Usuarios de excepción: los que entran con contraseña propia porque no tienen cuenta del dominio.

Es el camino secundario (FR-001b). El principal es Google. Existe porque el cliente lo pidió
explícitamente: no todo el mundo del equipo tendrá cuenta `@centauroads.com`.

La contraseña nunca se guarda ni se registra en claro. Argon2id es el algoritmo recomendado hoy
para esto: está pensado para ser lento y caro en memoria, que es justo lo que desanima a quien
robe la base de datos e intente probar contraseñas a lo bruto.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

# Parámetros por defecto de argon2-cffi, que siguen la recomendación de la propia biblioteca.
# No se bajan "para que vaya más rápido": el coste es el mecanismo de defensa.
_hasher = PasswordHasher()

LARGO_MINIMO = 12


class ContrasenaDebil(ValueError):
    """La contraseña no cumple el mínimo. Se rechaza al darla de alta, no al usarla."""


def hashear(contrasena: str) -> str:
    """
    Devuelve el hash que se guarda en `panel_users.password_hash`.

    Comprueba el largo mínimo aquí, en el punto de entrada, para que no haya forma de colar una
    contraseña corta por otra vía.
    """
    if not contrasena or len(contrasena) < LARGO_MINIMO:
        raise ContrasenaDebil(
            f"La contraseña debe tener al menos {LARGO_MINIMO} caracteres"
        )
    return _hasher.hash(contrasena)


def verificar(hash_guardado: str, contrasena: str) -> bool:
    """
    ¿Corresponde la contraseña al hash?

    Devuelve False en vez de lanzar excepción para que quien llama no tenga que distinguir entre
    "contraseña incorrecta", "hash corrupto" y "usuario sin contraseña": desde fuera, los tres
    casos son el mismo — no entra.
    """
    if not hash_guardado or not contrasena:
        return False
    try:
        return _hasher.verify(hash_guardado, contrasena)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def necesita_rehash(hash_guardado: str) -> bool:
    """
    ¿Se generó ese hash con parámetros más flojos que los de ahora?

    Si la biblioteca sube sus recomendaciones, los hashes viejos se pueden actualizar
    aprovechando que en ese momento tenemos la contraseña en la mano.
    """
    if not hash_guardado:
        return False
    try:
        return _hasher.check_needs_rehash(hash_guardado)
    except InvalidHashError:
        return False
