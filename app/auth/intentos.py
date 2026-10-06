"""
Límite de intentos fallidos al entrar y con la llave de superadmin (2026-10-03).

La pantalla de entrada enseña ahora la recuperación de emergencia (credencial de superadmin), y sin
límite cualquiera podría probar contraseñas sin fin contra ella o contra una cuenta del equipo.

Cuenta solo los FALLOS, por dirección y por puerta: 5 de superadmin o 10 de contraseña normal en
15 minutos bloquean esa puerta para esa dirección hasta que pasen los 15 minutos. Un acierto
antes del límite borra los fallos (quien se equivoca dos veces y luego acierta no arrastra nada),
pero un acierto con la puerta ya cerrada no la abre: si no, el bloqueo no protegería del intento
que por fin acierta.

Vive en memoria. Se pierde al reiniciar el servicio, y está bien así: lo que importa es frenar una
ráfaga, no llevar un registro. La app corre en un solo proceso (`run.py` sirve los dos puertos
desde el mismo), así que todas las peticiones ven el mismo contador.
"""

import threading
import time
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

from fastapi import HTTPException, Request

MAX_SUPERADMIN = 5
MAX_ENTRADA = 10
VENTANA_SEGUNDOS = 15 * 60

_fallos: Dict[Tuple[str, str], Deque[float]] = defaultdict(deque)
_cerrojo = threading.Lock()


def _ahora() -> float:
    return time.monotonic()


def direccion(request: Request) -> str:
    """
    De dónde viene la petición. Detrás de Traefik, `request.client` es el propio proxy, y la
    dirección real va en X-Forwarded-For. Se toma la ÚLTIMA: es la que añade nuestro proxy. Las
    de delante las escribe quien llama y podría cambiarlas en cada intento para no bloquearse.
    """
    reenviada = request.headers.get("x-forwarded-for", "")
    if reenviada.strip():
        return reenviada.split(",")[-1].strip()
    return request.client.host if request.client else "desconocida"


def _recientes(clave: Tuple[str, str]) -> Deque[float]:
    cola = _fallos[clave]
    limite = _ahora() - VENTANA_SEGUNDOS
    while cola and cola[0] < limite:
        cola.popleft()
    return cola


def comprueba(request: Request, puerta: str, maximo: int) -> None:
    """Lanza 429 si esa dirección ya agotó los intentos de esa puerta."""
    with _cerrojo:
        if len(_recientes((puerta, direccion(request)))) >= maximo:
            raise HTTPException(
                status_code=429,
                detail="Demasiados intentos fallidos. Espera 15 minutos antes de volver a probar.")


def fallo(request: Request, puerta: str) -> None:
    with _cerrojo:
        _recientes((puerta, direccion(request))).append(_ahora())


def acierto(request: Request, puerta: str) -> None:
    with _cerrojo:
        _fallos.pop((puerta, direccion(request)), None)


def reinicia() -> None:
    """Para las pruebas: todas llegan desde la misma dirección."""
    with _cerrojo:
        _fallos.clear()
