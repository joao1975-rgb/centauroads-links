"""
El catálogo nace igual que el de serie, y una sola vez.

La fuente es `app/static/email/catalogo-serie.json`, que `build.js` exporta de `render.js`. Así el
catálogo de serie vive en UN sitio —el motor— y el servidor no guarda una copia que pueda
desviarse de él.

Solo siembra con las dos tablas vacías. En cuanto alguien ha tocado el catálogo desde el panel, lo
que hay en la base es la verdad, y una siembra que lo pisara al reiniciar desharía su trabajo.
"""

import json
import logging
import os

from sqlalchemy.orm import Session

from ... import models

log = logging.getLogger("centaurads.catalogo")

FICHERO_SERIE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                             "static", "email", "catalogo-serie.json")


def siembra(db: Session, fichero: str = FICHERO_SERIE) -> bool:
    """Crea el catálogo de serie si no hay ninguno. Devuelve si sembró."""
    if db.query(models.LineaNegocio).count() or db.query(models.FamiliaD).count():
        return False
    try:
        with open(fichero, encoding="utf-8") as f:
            serie = json.load(f)
    except (OSError, ValueError):
        # Sin catálogo en la base, el compositor sigue con el de serie que trae el motor. Es un
        # fallo a corregir, no motivo para que la aplicación no arranque.
        log.warning("no se pudo leer %s: el catálogo queda sin sembrar", fichero)
        return False

    for i, f in enumerate(serie.get("familias", [])):
        db.add(models.FamiliaD(id=f["id"], titulo=f.get("titulo", ""), eyebrow=f.get("eyebrow", ""), orden=i))
    for i, l in enumerate(serie.get("lineas", [])):
        ficha = l.get("ficha") or {}
        db.add(models.LineaNegocio(
            id=l["id"], nombre=l["nombre"], eyebrow=l.get("eyebrow", ""), cta=l.get("cta", ""),
            cobertura=l.get("cobertura", ""), nota=l.get("nota", ""), canva=l.get("canva", ""),
            slug=l.get("slug", ""), img=l.get("img", ""), alt=l.get("alt", ""),
            cover=l.get("cover", ""), alt_cover=l.get("altCover", ""),
            ficha_ubic=ficha.get("ubic", ""), ficha_medida=ficha.get("medida", ""),
            ficha_trafico=ficha.get("trafico", ""), ficha_desde=ficha.get("desde", ""),
            familia_id=l.get("familia") or None, plantillas=l.get("plantillas", "ABCDEFGH"),
            orden=i, activa=True, actualizado_por="catálogo de serie",
        ))
    db.commit()
    log.info("catálogo de líneas sembrado con el de serie")
    return True
