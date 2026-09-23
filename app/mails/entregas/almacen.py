"""
Dónde viven los ficheros de una entrega, y cómo se llega a ellos sin salirse.

Las imágenes de una entrega son **material de un cliente**: la presentación que se le armó. No
pueden entrar al repositorio, que es público, ni vivir en `app/static/`, que se reemplaza entero
en cada despliegue. Viven en el volumen persistente, junto a la base de datos:

    <DATA_DIR>/entregas/<id>/p0.jpg        las páginas elegidas, en orden
    <DATA_DIR>/entregas/<id>/carrusel.gif  el carrusel armado con ellas
    <DATA_DIR>/entregas/<id>/og.jpg        la portada de la tarjeta de WhatsApp

En la base de datos se guarda la ruta **relativa** (`entregas/7/p0.jpg`), nunca la absoluta:
mover el volumen o cambiar `DATA_DIR` no puede invalidar las filas.

El PDF original no se guarda. Se rasteriza y se descarta: conservar el material completo de un
cliente sin que nadie lo haya pedido es una decisión, y no se ha tomado.

**Lo que más importa de este módulo** es `resuelve()`. La ruta pública `/media/entregas/{id}/{f}`
recibe un nombre de fichero desde fuera, y un nombre de fichero desde fuera es una entrada no
confiable. Aquí se comprueba dos veces: por forma —una lista de caracteres permitidos que no
incluye `/`, `\\` ni `.`— y por destino, resolviendo la ruta real y exigiendo que siga dentro de
la carpeta de esa entrega. Lo segundo es lo que atrapa lo que la primera no previó.
"""

import logging
import os
import re
from typing import Optional

log = logging.getLogger("centaurads.entregas")

# Mismo criterio que `app/database.py`, que hace `os.makedirs("data")` relativo al directorio de
# trabajo: en el contenedor es `/app`, de modo que esto resuelve a `/app/data`, el volumen.
DIRECTORIO_DATOS = os.getenv("DATA_DIR", "data")
SUBCARPETA = "entregas"

# Nombres que aceptamos servir. Minúsculas, dígitos, guion, guion bajo y un punto de extensión.
# Deliberadamente NO admite `/`, `\`, `..`, espacios ni mayúsculas: el conjunto de lo permitido se
# escribe entero, en vez de intentar enumerar lo prohibido.
_NOMBRE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,48}\.(jpg|png|gif)$")


def raiz() -> str:
    """La carpeta que contiene todas las entregas."""
    return os.path.join(DIRECTORIO_DATOS, SUBCARPETA)


def carpeta(entrega_id: int, crear: bool = True) -> str:
    """La carpeta de una entrega. La crea si hace falta."""
    ruta = os.path.join(raiz(), str(int(entrega_id)))
    if crear:
        os.makedirs(ruta, exist_ok=True)
    return ruta


def ruta_relativa(entrega_id: int, nombre: str) -> str:
    """Lo que se guarda en `entrega_paginas.ruta`. Con `/`, también en Windows."""
    return "%s/%d/%s" % (SUBCARPETA, int(entrega_id), nombre)


def ruta_absoluta(relativa: str) -> str:
    """De lo guardado en la base de datos al fichero en disco."""
    return os.path.join(DIRECTORIO_DATOS, *relativa.split("/"))


def nombre_valido(nombre: str) -> bool:
    return bool(_NOMBRE.match(nombre or ""))


def resuelve(entrega_id: int, nombre: str) -> Optional[str]:
    """
    La ruta en disco de un fichero pedido desde fuera, o `None` si no se debe servir.

    Devuelve `None` —y no una excepción— porque quien llama es una ruta HTTP y lo único que puede
    hacer con esto es un 404. Distinguir "nombre inválido" de "no existe" solo le diría a quien
    prueba qué está probando.
    """
    if not nombre_valido(nombre):
        return None
    try:
        base = os.path.realpath(carpeta(entrega_id, crear=False))
        destino = os.path.realpath(os.path.join(base, nombre))
    except (ValueError, OSError):
        return None
    # Segunda comprobación, por destino y no por forma: aunque el nombre pasara el filtro, el
    # fichero resultante tiene que quedar dentro de la carpeta de esta entrega.
    if destino != base and not destino.startswith(base + os.sep):
        return None
    if not os.path.isfile(destino):
        return None
    return destino


def guarda(entrega_id: int, nombre: str, datos: bytes) -> str:
    """Escribe un fichero de la entrega y devuelve su ruta relativa."""
    if not nombre_valido(nombre):
        raise ValueError("nombre de fichero no permitido: %r" % (nombre,))
    destino = os.path.join(carpeta(entrega_id), nombre)
    with open(destino, "wb") as f:
        f.write(datos)
    return ruta_relativa(entrega_id, nombre)


def borra_entrega(entrega_id: int) -> int:
    """
    Borra los ficheros de una entrega. Devuelve cuántos borró.

    Solo borra ficheros con nombre válido y la carpeta si queda vacía: si alguien dejó algo ahí a
    mano, se queda, y el borrado no se lleva por delante lo que no reconoce.
    """
    base = os.path.join(raiz(), str(int(entrega_id)))
    if not os.path.isdir(base):
        return 0
    borrados = 0
    for nombre in os.listdir(base):
        if not nombre_valido(nombre):
            continue
        try:
            os.remove(os.path.join(base, nombre))
            borrados += 1
        except OSError:
            # Un fichero que el sistema no deja borrar ahora mismo no puede tumbar la petición:
            # quien llama viene a rehacer el carrusel, y `guarda()` lo sobrescribirá igual. Se
            # registra para que no pase inadvertido si se vuelve costumbre.
            log.warning("no se pudo borrar %s de la entrega %s", nombre, entrega_id)
    try:
        if not os.listdir(base):
            os.rmdir(base)
    except OSError:
        pass
    return borrados
