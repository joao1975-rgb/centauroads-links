"""
Las fotos de las líneas de negocio: se validan, se reducen y se sirven a los correos.

Viven en el volumen persistente, junto a la base de datos y las entregas (`<DATA_DIR>/lineas/`),
no en `app/static/`, que se reemplaza en cada despliegue.

**Nunca se borran.** Cambiar la foto de una línea crea un archivo nuevo —su nombre lleva una huella
del contenido— y deja el anterior: un correo ya enviado sigue apuntando a él, y borrarlo dejaría
ese correo con un hueco donde iba la foto.

Lo delicado es la ruta pública `/media/lineas/{archivo}`: recibe un nombre desde fuera. Se
comprueba por forma (una lista blanca de caracteres que no admite `/`, `\\` ni `..`) y por destino
(la ruta real tiene que quedar dentro de la carpeta), como en `entregas/almacen.py`.
"""

import hashlib
import io
import os
import re
from typing import Optional

from PIL import Image, ImageOps

DIRECTORIO_DATOS = os.getenv("DATA_DIR", "data")
SUBCARPETA = "lineas"
RUTA_PUBLICA = "/media/lineas/"

MAXIMO_BYTES = 8 * 1024 * 1024
# El doble del ancho al que se pinta la foto más grande de un correo (536 px): nítida en pantallas
# de alta densidad sin que el correo pese de más.
ANCHO_MAXIMO = 1072
CALIDAD_JPEG = 82
# Una imagen de 8 MB puede declarar dimensiones enormes y reventar la memoria al cargarla: se mira
# el tamano declarado ANTES de cargar. Y solo formatos de foto: Pillow abre muchos mas (EPS llega a
# llamar a Ghostscript), y la pantalla promete JPG, PNG o WebP.
PIXELES_MAXIMOS = 40_000_000
FORMATOS = ["JPEG", "PNG", "WEBP"]

_NOMBRE = re.compile(r"^[a-z0-9][a-z0-9-]{0,60}-[0-9a-f]{8}\.jpg$")


class FotoNoValida(ValueError):
    """El fichero no es una imagen que se pueda usar. El mensaje es para la persona."""


def raiz() -> str:
    return os.path.join(DIRECTORIO_DATOS, SUBCARPETA)


def prepara(datos: bytes) -> bytes:
    """De lo que se subió a un JPEG listo para un correo: derecho, en RGB, ≤ 1072 px de ancho."""
    demasiado = FotoNoValida("La imagen es demasiado grande. Usa una de menos de 40 megapíxeles.")
    try:
        with Image.open(io.BytesIO(datos), formats=FORMATOS) as prueba:
            if prueba.width * prueba.height > PIXELES_MAXIMOS:
                raise demasiado
            prueba.verify()
        imagen = Image.open(io.BytesIO(datos), formats=FORMATOS)
        imagen.load()
    except FotoNoValida:
        raise
    except Image.DecompressionBombError:
        raise demasiado
    except Exception:
        raise FotoNoValida("El archivo no es una imagen que se pueda usar (JPG, PNG o WebP).")

    imagen = ImageOps.exif_transpose(imagen)
    if imagen.mode in ("RGBA", "LA", "P"):
        # Lo transparente, sobre blanco: en JPEG saldría negro.
        imagen = imagen.convert("RGBA")
        fondo = Image.new("RGB", imagen.size, (255, 255, 255))
        fondo.paste(imagen, mask=imagen.getchannel("A"))
        imagen = fondo
    else:
        imagen = imagen.convert("RGB")
    if imagen.width > ANCHO_MAXIMO:
        alto = round(imagen.height * ANCHO_MAXIMO / imagen.width)
        imagen = imagen.resize((ANCHO_MAXIMO, alto), Image.LANCZOS)

    salida = io.BytesIO()
    imagen.save(salida, "JPEG", quality=CALIDAD_JPEG, optimize=True, progressive=True)
    return salida.getvalue()


def guarda(linea_id: str, jpeg: bytes) -> str:
    """Escribe la foto y devuelve su ruta pública (`/media/lineas/<id>-<huella>.jpg`)."""
    nombre = "%s-%s.jpg" % (linea_id, hashlib.sha256(jpeg).hexdigest()[:8])
    if not _NOMBRE.fullmatch(nombre):
        raise ValueError("nombre de foto no permitido: %r" % (nombre,))
    os.makedirs(raiz(), exist_ok=True)
    with open(os.path.join(raiz(), nombre), "wb") as f:
        f.write(jpeg)
    return RUTA_PUBLICA + nombre


def resuelve(nombre: str) -> Optional[str]:
    """La ruta en disco de una foto pedida desde fuera, o None si no se debe servir."""
    if not _NOMBRE.fullmatch(nombre or ""):
        return None
    try:
        base = os.path.realpath(raiz())
        destino = os.path.realpath(os.path.join(base, nombre))
    except (ValueError, OSError):
        return None
    if not destino.startswith(base + os.sep) or not os.path.isfile(destino):
        return None
    return destino
