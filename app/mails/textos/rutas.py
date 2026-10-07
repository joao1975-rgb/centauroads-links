"""
La API de los textos de los perfiles (especificación 005, contracts/api.md).

- `GET /api/textos-perfil`: lo que pide el compositor al abrir. Cualquier sesión. Solo los textos
  cambiados, `{clave: valor}`, en la forma exacta que recibe `ponTextos()` del motor.
- `/api/panel/textos…`: la pantalla. Leer, cualquier sesión; cambiar o volver al de serie, solo un
  administrador.

Las claves que existen, su texto de serie y su límite salen de `textos-perfil-serie.json`, que
`build.js` exporta del motor: el servidor no guarda una copia de los textos de serie que pueda
desviarse de la del motor.
"""

import json
import logging
import os
import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, StrictStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ... import models
from ...auth.dependencias import solo_admin, usuario_actual
from ...database import get_db

log = logging.getLogger("centaurads.textos")

router = APIRouter()

FICHERO_SERIE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                             "static", "email", "textos-perfil-serie.json")


def _lee_serie(fichero: str = FICHERO_SERIE) -> dict:
    try:
        with open(fichero, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        # Sin el archivo no se puede validar ninguna clave: no se cambia nada y el compositor sigue
        # con los de serie. Es un fallo a corregir, no motivo para que la aplicación no arranque.
        log.warning("no se pudo leer %s: los textos de los perfiles no se pueden cambiar", fichero)
        return {"perfiles": [], "textos": []}


SERIE = _lee_serie()
DE_SERIE = {t["clave"]: t for t in SERIE["textos"]}


# Caracteres que no se ven pero cambian lo que se lee: de control, de ancho cero y los que invierten la
# dirección del texto (un asunto «al revés» en la bandeja del cliente). El de unión de emojis compuestos
# (U+200D) sí vale.
_INVISIBLES = re.compile("[\x00-\x09\x0b-\x1f\x7f\u200b\u200e\u200f\u202a-\u202e\u2066-\u2069]")
# Solo la entrada y el cierre son párrafos; los demás textos van en una sola línea.
_PARRAFOS = (".intro", ".cierre")


class Texto(BaseModel):
    valor: StrictStr


def _de_serie(clave: str) -> dict:
    t = DE_SERIE.get(clave)
    if t is None:
        raise HTTPException(status_code=404, detail="Ese texto no existe")
    return t


def _fila(t: dict, cambio) -> dict:
    return {
        "clave": t["clave"], "perfil": t["perfil"], "grupo": t["grupo"], "etiqueta": t["etiqueta"],
        "limite": t["limite"], "serie": t["valor"],
        "valor": cambio.valor if cambio else t["valor"], "cambiado": cambio is not None,
        "actualizado_por": cambio.actualizado_por if cambio else None,
        "actualizado_en": cambio.actualizado_en.isoformat() if cambio and cambio.actualizado_en else None,
    }


def _cambios(db: Session) -> dict:
    # Una clave que el motor ya no tiene (un texto retirado de la serie) se ignora, no se borra.
    return {c.clave: c for c in db.query(models.TextoPerfil).all() if c.clave in DE_SERIE}


@router.get("/api/textos-perfil")
def textos_para_el_compositor(db: Session = Depends(get_db), _: models.PanelUser = Depends(usuario_actual)):
    return {clave: c.valor for clave, c in _cambios(db).items()}


@router.get("/api/panel/textos")
def lista(db: Session = Depends(get_db), _: models.PanelUser = Depends(usuario_actual)):
    cambios = _cambios(db)
    return {"perfiles": SERIE["perfiles"],
            "textos": [_fila(t, cambios.get(t["clave"])) for t in SERIE["textos"]]}


@router.put("/api/panel/textos/{clave}")
def cambia(clave: str, cuerpo: Texto, db: Session = Depends(get_db),
           usuario: models.PanelUser = Depends(solo_admin)):
    t = _de_serie(clave)
    valor = cuerpo.valor.replace("\r\n", "\n").strip()
    if not valor:
        raise HTTPException(status_code=400,
                            detail="Un texto no puede quedar vacío. Para quitar el cambio, vuelve al de serie.")
    if _INVISIBLES.search(valor):
        raise HTTPException(status_code=400, detail="Este texto lleva caracteres invisibles o de control. "
                                                    "Escríbelo de nuevo en vez de pegarlo.")
    if "\n" in valor and not clave.endswith(_PARRAFOS):
        raise HTTPException(status_code=400, detail="Este texto va en una sola línea")
    if len(valor) > t["limite"]:
        raise HTTPException(status_code=422, detail="Este texto admite hasta %d caracteres" % t["limite"])
    if valor == t["valor"]:
        return _vuelve(t, db, usuario)

    for intento in (1, 2):
        cambio = db.get(models.TextoPerfil, clave)
        if cambio is None:
            cambio = models.TextoPerfil(clave=clave)
            db.add(cambio)
        # Registro: lo que había y quién lo cambió. Sale en todos los correos del equipo, así que si
        # alguien lo usa mal tiene que quedar rastro y poder recuperarse el texto anterior.
        log.info("texto %s cambiado por %s: %r -> %r", clave, usuario.email, cambio.valor or t["valor"], valor)
        cambio.valor = valor
        cambio.actualizado_por = usuario.email
        try:
            db.commit()
            break
        except IntegrityError:
            # Dos administradores guardaron a la vez el mismo texto, que no estaba cambiado: la fila ya
            # la creó el otro. Gana el último que guarda: se relee y se reaplica.
            db.rollback()
            if intento == 2:
                raise
    db.refresh(cambio)
    return _fila(t, cambio)


@router.delete("/api/panel/textos/{clave}")
def vuelve_al_de_serie(clave: str, db: Session = Depends(get_db),
                       usuario: models.PanelUser = Depends(solo_admin)):
    return _vuelve(_de_serie(clave), db, usuario)


def _vuelve(t: dict, db: Session, usuario: models.PanelUser) -> dict:
    cambio = db.get(models.TextoPerfil, t["clave"])
    if cambio is not None:
        log.info("texto %s vuelve al de serie por %s: era %r", t["clave"], usuario.email, cambio.valor)
        db.delete(cambio)
        db.commit()
    return _fila(t, None)
