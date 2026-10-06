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

import ipaddress
import threading
import time
from collections import deque
from typing import Deque, Dict, Optional, Tuple

from fastapi import HTTPException, Request

MAX_SUPERADMIN = 5
MAX_ENTRADA = 10
VENTANA_SEGUNDOS = 15 * 60
# Direcciones con fallos recientes que se vigilan a la vez. Con mas, se olvida la mas antigua:
# el contador no puede comerse la memoria aunque alguien pruebe desde miles de direcciones.
# ponytail: cada direccion olvidada vuelve a tener 10 intentos; con tantas direcciones el freno
# real seria un cortafuegos delante, no este contador.
MAX_DIRECCIONES = 10_000

# Solo direcciones con fallos dentro de la ventana. Una que solo se comprobo no deja rastro.
_fallos: Dict[Tuple[str, str], Deque[float]] = {}
# Las redes desde las que conecta nuestro proxy (Traefik, en la red interna de Docker).
_REDES_DEL_PROXY = [ipaddress.ip_network(r) for r in (
    "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16", "127.0.0.0/8", "::1/128", "fc00::/7")]
_cerrojo = threading.Lock()


def _ahora() -> float:
    return time.monotonic()


def direccion(request: Request) -> str:
    """
    De dónde viene la petición. Detrás de Traefik, `request.client` es el propio proxy, y la
    dirección real va en X-Forwarded-For. Se toma la ÚLTIMA: es la que añade nuestro proxy. Las
    de delante las escribe quien llama y podría cambiarlas en cada intento para no bloquearse.

    Pero la cabecera solo se cree si quien conecta ES el proxy (una direccion de la red interna):
    quien llegara directo al puerto de la app la escribiria a su gusto y no se bloquearia nunca.
    Hoy ese puerto no responde desde fuera (comprobado el 2026-10-06); esto lo cubre si cambia.
    """
    cliente = request.client.host if request.client else "desconocida"
    reenviada = request.headers.get("x-forwarded-for", "")
    if reenviada.strip() and _es_el_proxy(cliente):
        return reenviada.split(",")[-1].strip()
    return cliente


def _es_el_proxy(cliente: str) -> bool:
    try:
        ip = ipaddress.ip_address(cliente)
    except ValueError:
        # No es una direccion (el cliente de las pruebas se llama «testclient»): no llega de fuera.
        return True
    return any(ip in red for red in _REDES_DEL_PROXY)


def _recientes(clave: Tuple[str, str]) -> Optional[Deque[float]]:
    """Los fallos de esa clave dentro de la ventana, o None si no queda ninguno (y se borra)."""
    cola = _fallos.get(clave)
    if cola is None:
        return None
    limite = _ahora() - VENTANA_SEGUNDOS
    while cola and cola[0] < limite:
        cola.popleft()
    if not cola:
        del _fallos[clave]
        return None
    return cola


def comprueba(request: Request, puerta: str, maximo: int) -> None:
    """Lanza 429 si esa dirección ya agotó los intentos de esa puerta."""
    with _cerrojo:
        cola = _recientes((puerta, direccion(request)))
        if cola is not None and len(cola) >= maximo:
            raise HTTPException(
                status_code=429,
                detail="Demasiados intentos fallidos. Espera 15 minutos antes de volver a probar.")


def fallo(request: Request, puerta: str) -> None:
    with _cerrojo:
        # Al apuntar un fallo se barren los caducados de todos: los fallos son raros y la lista,
        # corta, asi que no hace falta un proceso aparte.
        for clave in list(_fallos):
            _recientes(clave)
        clave = (puerta, direccion(request))
        _fallos.setdefault(clave, deque()).append(_ahora())
        while len(_fallos) > MAX_DIRECCIONES:
            del _fallos[next(iter(_fallos))]


def acierto(request: Request, puerta: str) -> None:
    with _cerrojo:
        _fallos.pop((puerta, direccion(request)), None)


def reinicia() -> None:
    """Para las pruebas: todas llegan desde la misma dirección."""
    with _cerrojo:
        _fallos.clear()
