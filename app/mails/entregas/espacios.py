"""
Los espacios que acompañan a una entrega, personalizados solo para ella (especificación 004).

Un espacio es una línea del catálogo (`lineas_negocio`). Lo que se le cambia aquí —su carrusel, su
enlace, su nombre, su cobertura— vale **solo** para esta entrega: las plantillas A–G y las demás
entregas siguen leyendo el catálogo (FR-402). Un espacio sin nada propio no tiene fila.

Las imágenes se suben y se arman con el mismo código que la principal (`galeria.py`), en la
subcarpeta del espacio. Todo exige sesión, como el resto de `/api/entregas` (FR-418).
"""

import json
import logging
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ...database import get_db
from ... import models
from ...auth.dependencias import usuario_actual
from . import almacen, carrusel, galeria
from .galeria import Seleccion
from .rutas import EntregaSalida, _a_salida, _busca, valida_enlace

log = logging.getLogger("centaurads.entregas")
router = APIRouter()

# Lo que se supo al subir y ya no se puede volver a leer de un JPG: qué página parecía tener un
# precio. El `PUT` lo necesita para las elegidas. Su nombre no pasa la lista blanca de `almacen`,
# así que `/media` nunca lo sirve.
_SUBIDA = "subida.json"

_TEXTOS = ("canva_url", "nombre", "cobertura")


def _catalogo(db: Session, linea: str) -> models.LineaNegocio:
    """La línea del catálogo, o 404. La forma se mira antes: `linea` acaba en una ruta de disco."""
    fila = db.get(models.LineaNegocio, linea) if almacen.linea_valida(linea) else None
    if not fila:
        raise HTTPException(status_code=404, detail="Ese espacio no está en el catálogo")
    return fila


def _fila(db: Session, entrega_id: int, linea: str) -> Optional[models.EntregaEspacio]:
    return db.query(models.EntregaEspacio).filter(
        models.EntregaEspacio.entrega_id == entrega_id,
        models.EntregaEspacio.linea_id == linea).first()


def _avisos(entrega_id: int, linea: str) -> list:
    try:
        with open(os.path.join(almacen.carpeta(entrega_id, False, linea), _SUBIDA),
                  encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        # Sin el registro de la subida, ninguna avisa: el aviso es una ayuda, no una garantía, y
        # la interfaz ya dice que no ve precios dentro de imágenes.
        return []


def _con_fila(db: Session, entrega_id: int, linea: str, aplica) -> None:
    """
    Aplica `aplica(fila)` a la fila del espacio -la crea si no existe- y guarda.

    El compositor guarda cada campo por su lado, asi que el nombre y la cobertura de un espacio
    nuevo pueden llegar a la vez: los dos ven que no hay fila y los dos la crean. El segundo choca con
    UNIQUE(entrega_id, linea_id); en vez de un 500 que pierde su valor, relee la fila que ya creo el
    otro y vuelve a aplicar lo suyo, una vez (revision de seguridad, 2026-10-06).
    """
    for intento in (1, 2):
        fila = _fila(db, entrega_id, linea) or models.EntregaEspacio(entrega_id=entrega_id, linea_id=linea)
        aplica(fila)
        try:
            db.commit()
            return
        except IntegrityError:
            db.rollback()
            if intento == 2:
                raise


@router.post("/api/entregas/{entrega_id}/espacios/{linea}/paginas")
async def subir(entrega_id: int, linea: str, fichero: List[UploadFile] = File(...),
                db: Session = Depends(get_db),
                usuario: models.PanelUser = Depends(usuario_actual)):
    """Como el de la principal, en la subcarpeta del espacio. Solo vacía esa subcarpeta."""
    entrega = _busca(db, entrega_id)
    _catalogo(db, linea)
    salida = await galeria.sube(entrega.id, fichero, linea)
    with open(os.path.join(almacen.carpeta(entrega.id, linea=linea), _SUBIDA), "w",
              encoding="utf-8") as f:
        json.dump([p["aviso_precio"] for p in salida], f)
    return galeria.respuesta(salida)


@router.put("/api/entregas/{entrega_id}/espacios/{linea}/paginas", response_model=EntregaSalida)
def elegir(entrega_id: int, linea: str, seleccion: Seleccion,
           db: Session = Depends(get_db),
           usuario: models.PanelUser = Depends(usuario_actual)):
    """Arma el carrusel del espacio y lo apunta en su fila, con el efecto con que salió."""
    entrega = _busca(db, entrega_id)
    _catalogo(db, linea)
    elegidas = galeria.arma(entrega.id, seleccion, linea)
    avisos = _avisos(entrega.id, linea)

    paginas = json.dumps([{
        "orden": orden, "ruta": almacen.ruta_relativa(entrega.id, "p%d.jpg" % i, linea),
        "ancho": im.width, "alto": im.height,
        "aviso_precio": bool(avisos[i]) if i < len(avisos) else False,
    } for orden, (i, im) in enumerate(elegidas)])

    def aplica(fila):
        # `carrusel.arma` cae en barrido con un efecto que no conoce; se guarda el que salió.
        fila.efecto = seleccion.efecto if seleccion.efecto in carrusel.EFECTOS else "barrido"
        fila.paginas = paginas
        db.add(fila)

    _con_fila(db, entrega.id, linea, aplica)
    return _a_salida(db, entrega)


class EspacioEntrada(BaseModel):
    """Solo cambia lo que llega. Vacío (o nulo) = volver al del catálogo para ese campo."""
    canva_url: Optional[str] = Field(default=None, max_length=500)
    nombre: Optional[str] = Field(default=None, max_length=120)
    cobertura: Optional[str] = Field(default=None, max_length=200)


@router.put("/api/entregas/{entrega_id}/espacios/{linea}", response_model=EntregaSalida)
def guardar(entrega_id: int, linea: str, datos: EspacioEntrada,
            db: Session = Depends(get_db),
            usuario: models.PanelUser = Depends(usuario_actual)):
    """
    Guarda lo propio del espacio en esta entrega.

    Un valor igual al del catálogo se guarda nulo (R8): así «personalizado» tiene un solo criterio
    y, si el catálogo cambia después, ese campo sigue al catálogo como cualquier estándar.
    """
    entrega = _busca(db, entrega_id)
    serie = _catalogo(db, linea)
    de_serie = {"canva_url": serie.canva, "nombre": serie.nombre, "cobertura": serie.cobertura}

    # Se valida todo antes de tocar la fila: un enlace malo no deja nada a medias.
    cambios = {}
    for campo in datos.model_fields_set & set(_TEXTOS):
        valor = (getattr(datos, campo) or "").strip()
        if valor and campo == "canva_url":
            try:
                valor = valida_enlace(valor)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
        cambios[campo] = valor if valor and valor != (de_serie[campo] or "").strip() else None

    def aplica(fila):
        for campo, valor in cambios.items():
            setattr(fila, campo, valor)
        if any(getattr(fila, c) for c in _TEXTOS) or fila.efecto:
            db.add(fila)
        elif fila.id:
            # Sin nada propio ni carrusel, el espacio vuelve a ser estándar: sin fila.
            db.delete(fila)

    _con_fila(db, entrega.id, linea, aplica)
    return _a_salida(db, entrega)


@router.delete("/api/entregas/{entrega_id}/espacios/{linea}", response_model=EntregaSalida)
def volver_al_estandar(entrega_id: int, linea: str,
                       db: Session = Depends(get_db),
                       usuario: models.PanelUser = Depends(usuario_actual)):
    """
    Borra la fila. Las imágenes **se quedan** en disco: un correo ya enviado puede apuntar a ellas
    (FR-414), y se irán con la entrega.
    """
    entrega = _busca(db, entrega_id)
    _catalogo(db, linea)
    fila = _fila(db, entrega.id, linea)
    if fila:
        db.delete(fila)
        db.commit()
    return _a_salida(db, entrega)
