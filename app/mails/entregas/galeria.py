"""
Subir las páginas de una presentación y armar su carrusel, para cualquier carpeta.

La principal de la entrega y cada espacio que la acompaña (004) hacen exactamente lo mismo: leer
el PDF o las imágenes, guardar `p{i}.jpg`, elegir de 2 a 4 y armar `carrusel.gif`. Vive aquí, una
sola vez, porque la especificación pide que el espacio se comporte **igual** que la principal, y
dos copias del flujo acabarían divergiendo (research R6). `linea=None` es la principal.

Lo que NO está aquí es la base de datos: la principal guarda filas en `entrega_paginas` y un
espacio guarda JSON en su fila. Cada ruta decide eso; esto solo toca ficheros.
"""

import logging
from typing import List, Optional

from fastapi import HTTPException, UploadFile
from pydantic import BaseModel, Field

from . import almacen, carrusel, paginas as mod_paginas
from .publicas import _url_media

log = logging.getLogger("centaurads.entregas")

MIN_PAGINAS = 2
MAX_PAGINAS = 4

# Esto no es un adorno: el aviso de precios lee texto y no ve un precio dibujado dentro de una
# imagen. Quien entrega tiene que saberlo (constitución, principio IV).
AVISO = ("El aviso de precio solo detecta precios escritos como texto. "
         "Si en la presentación el precio es parte de una imagen, no se detecta: "
         "míralas antes de entregar.")


class Seleccion(BaseModel):
    indices: List[int] = Field(min_length=MIN_PAGINAS, max_length=MAX_PAGINAS)
    # El mismo banco de efectos que las plantillas A-G. Si llega uno que no existe, `arma` cae en
    # barrido en vez de fallar: una transicion distinta de la pedida es un mal menor frente a
    # quedarse sin carrusel.
    efecto: str = "barrido"


async def sube(entrega, ficheros: List[UploadFile],
               linea: Optional[str] = None) -> List[dict]:
    """
    Rasteriza lo subido, vacía la carpeta y guarda las páginas. Devuelve las miniaturas elegibles.

    Se lee todo **antes** de borrar nada: un fichero no válido no puede dejar la carpeta vacía.
    `entrega` es la fila (`models.Entrega`): las direcciones de las miniaturas salen de su clave.
    """
    entrega_id = entrega.id
    # Cada fichero aporta al menos una página, así que más ficheros que el límite de páginas ya
    # se sabe que no cabe. Se dice antes de leer ninguno: leerlos todos para contar después era
    # dejar que una sola petición con cientos de ficheros ocupara memoria y CPU a placer.
    if len(ficheros) > mod_paginas.LIMITE_PAGINAS:
        raise HTTPException(
            status_code=400,
            detail="Son %d ficheros y el límite son %d páginas."
                   % (len(ficheros), mod_paginas.LIMITE_PAGINAS))
    encontradas = []
    for subido in ficheros:
        # Un byte más que el límite basta para que `valida` lo rechace: leer el fichero entero
        # antes de mirar su tamaño era cargar en memoria lo que mandaran, fuera lo que fuera.
        datos = await subido.read(mod_paginas.LIMITE_BYTES + 1)
        try:
            encontradas.extend(mod_paginas.lee(datos))
        except mod_paginas.FicheroNoValido as e:
            raise HTTPException(status_code=400, detail=str(e))
    if len(encontradas) > mod_paginas.LIMITE_PAGINAS:
        raise HTTPException(
            status_code=400,
            detail="Entre todo suman %d páginas y el límite son %d."
                   % (len(encontradas), mod_paginas.LIMITE_PAGINAS))

    almacen.borra_entrega(entrega_id, linea)
    salida = []
    for i, pagina in enumerate(encontradas):
        nombre = "p%d.jpg" % i
        almacen.guarda(entrega_id, nombre, carrusel.a_jpeg(pagina.imagen), linea)
        salida.append({
            "indice": i,
            "url": _url_media(entrega, nombre, linea),
            "ancho": pagina.ancho, "alto": pagina.alto,
            "rotulo": pagina.rotulo or ("Página %d" % (i + 1)),
            "aviso_precio": pagina.aviso_precio,
            "origen": pagina.origen,
            "pagina_pdf": pagina.numero,
        })
    return salida


def respuesta(salida: List[dict]) -> dict:
    """Lo que devuelve el `POST …/paginas`, sea de la principal o de un espacio."""
    return {"paginas": salida, "minimo": MIN_PAGINAS, "maximo": MAX_PAGINAS, "aviso": AVISO}


def arma(entrega_id: int, seleccion: Seleccion, linea: Optional[str] = None,
         con_portada: bool = False) -> List[tuple]:
    """
    Arma `carrusel.gif` con las páginas elegidas, en ese orden. Devuelve `[(indice, imagen)]`.

    `con_portada` es solo para la principal: la tarjeta de WhatsApp (`og.jpg`) es de la entrega,
    no de cada espacio.
    """
    from PIL import Image

    if len(set(seleccion.indices)) != len(seleccion.indices):
        raise HTTPException(status_code=400, detail="Hay una página repetida en la selección")

    elegidas = []
    for i in seleccion.indices:
        destino = almacen.resuelve(entrega_id, "p%d.jpg" % i, linea)
        if not destino:
            raise HTTPException(
                status_code=400,
                detail="La página %d ya no está; vuelve a subir el PDF" % i)
        # Con `Image.open` a secas, PIL deja el fichero **abierto** hasta que se recoge el
        # objeto. En Windows eso impide borrarlo después —lo descubrió una prueba, con un
        # «Acceso denegado» al rearmar el carrusel— y en Linux no falla pero va acumulando
        # descriptores en un servidor que no se reinicia. `convert` ya devuelve una copia
        # independiente, así que el original se puede cerrar en cuanto se sale del `with`.
        with Image.open(destino) as bruta:
            elegidas.append((i, bruta.convert("RGB")))

    imagenes = [im for _, im in elegidas]
    tira = carrusel.arma(imagenes, efecto=seleccion.efecto)
    almacen.guarda(entrega_id, "carrusel.gif", tira.datos, linea)
    if con_portada:
        almacen.guarda(entrega_id, "og.jpg", carrusel.portada(imagenes[0]))
    if not tira.dentro_de_presupuesto:
        log.warning("entrega %d%s: carrusel de %d KB, por encima del presupuesto",
                    entrega_id, " (espacio %s)" % linea if linea else "",
                    round(tira.bytes / 1024))
    return elegidas
