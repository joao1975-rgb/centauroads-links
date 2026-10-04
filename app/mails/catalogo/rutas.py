"""
La API del catálogo de líneas de negocio (especificación 003, contracts/api.md).

- `GET /api/catalogo`: lo que pide el compositor al abrir. Cualquier sesión. Solo las líneas
  activas, en su orden, en la forma exacta que recibe `ponCatalogo()` del motor.
- `/api/panel/lineas…`: administración. Solo administradores, como el equipo.
- `GET /media/lineas/{archivo}`: las fotos, públicas porque las piden los correos.

Las reglas viven aquí y no en la pantalla: la pantalla es una cara de esta API, y cualquiera
puede llamar a la API sin pasar por ella.
"""

import re
import unicodedata
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ... import models
from ...auth.dependencias import solo_admin, usuario_actual
from ...database import get_db
from . import fotos

router = APIRouter()

LETRAS = "ABCDEFGH"
# Límites de data-model.md. El nombre aparte: es obligatorio.
LIMITES = {"eyebrow": 60, "cta": 60, "cobertura": 200, "nota": 300, "canva": 500, "slug": 80,
           "alt": 200}


class LineaNueva(BaseModel):
    nombre: str = ""
    eyebrow: str = ""
    cta: str = ""
    cobertura: str = ""
    nota: str = ""
    canva: str = ""
    slug: str = ""
    alt: str = ""
    familia: Optional[str] = None
    plantillas: Optional[str] = None
    confirmarSinPlantillas: bool = False


# --- Forma de salida -----------------------------------------------------------------------------

def _ficha(l: models.LineaNegocio):
    # Hay ficha si al menos ubicación, medidas o tráfico tienen valor (data-model.md).
    if not (l.ficha_ubic or l.ficha_medida or l.ficha_trafico):
        return None
    return {"ubic": l.ficha_ubic, "medida": l.ficha_medida, "trafico": l.ficha_trafico,
            "desde": l.ficha_desde}


def _para_motor(l: models.LineaNegocio) -> dict:
    return {"id": l.id, "nombre": l.nombre, "eyebrow": l.eyebrow, "cta": l.cta,
            "cobertura": l.cobertura, "nota": l.nota, "slug": l.slug, "canva": l.canva,
            "img": l.img, "alt": l.alt, "cover": l.cover, "altCover": l.alt_cover,
            "ficha": _ficha(l), "familia": l.familia_id or "", "plantillas": l.plantillas}


def _para_panel(l: models.LineaNegocio) -> dict:
    d = _para_motor(l)
    d.update({"activa": bool(l.activa), "orden": l.orden, "actualizado_por": l.actualizado_por,
              "actualizado_en": l.actualizado_en.isoformat() if l.actualizado_en else None})
    return d


def _familias(db: Session) -> list:
    return [{"id": f.id, "eyebrow": f.eyebrow, "titulo": f.titulo}
            for f in db.query(models.FamiliaD).order_by(models.FamiliaD.orden, models.FamiliaD.id)]


def _lineas(db: Session, solo_activas: bool):
    q = db.query(models.LineaNegocio)
    if solo_activas:
        q = q.filter(models.LineaNegocio.activa.is_(True))
    return q.order_by(models.LineaNegocio.orden, models.LineaNegocio.id).all()


def catalogo_activo(db: Session) -> dict:
    """El catálogo vigente, en la forma de `ponCatalogo()`."""
    return {"lineas": [_para_motor(l) for l in _lineas(db, True)], "familias": _familias(db)}


# --- Validación ----------------------------------------------------------------------------------

def _id_desde(nombre: str, db: Session) -> str:
    """`Producción audiovisual` → `produccion-audiovisual`; si ya existe, `-2`, `-3`…"""
    plano = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode("ascii")
    base = re.sub(r"[^a-z0-9]+", "-", plano.lower()).strip("-")[:40].rstrip("-") or "linea"
    candidato, n = base, 2
    while db.get(models.LineaNegocio, candidato) is not None:
        candidato, n = "%s-%d" % (base, n), n + 1
    return candidato


def _plantillas(valor: Optional[str], confirmado: bool) -> str:
    if valor is None:
        return LETRAS
    valor = valor.strip()
    if any(c not in LETRAS for c in valor) or len(set(valor)) != len(valor):
        raise HTTPException(status_code=400,
                            detail="Las plantillas son letras de la A a la H, sin repetir.")
    if not valor and not confirmado:
        raise HTTPException(status_code=400,
                            detail="La línea no sale en ninguna plantilla. Confírmalo si es lo que quieres.")
    return "".join(c for c in LETRAS if c in valor)


def _valida(cuerpo: LineaNueva, db: Session) -> dict:
    nombre = cuerpo.nombre.strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="Falta el nombre de la línea.")
    if len(nombre) > 120:
        raise HTTPException(status_code=400, detail="El nombre admite 120 caracteres como mucho.")
    if any(l.nombre.strip().lower() == nombre.lower() for l in db.query(models.LineaNegocio)):
        raise HTTPException(status_code=409, detail="Ya existe una línea con ese nombre.")

    datos = {"nombre": nombre}
    for campo, limite in LIMITES.items():
        valor = getattr(cuerpo, campo).strip()
        if len(valor) > limite:
            raise HTTPException(status_code=400,
                                detail="«%s» admite %d caracteres como mucho." % (campo, limite))
        datos[campo] = valor
    if datos["canva"] and not re.match(r"^https?://[^\s]+$", datos["canva"], re.I):
        raise HTTPException(status_code=400,
                            detail="El enlace tiene que empezar por https:// (o http://).")

    familia = (cuerpo.familia or "").strip() or None
    if familia and db.get(models.FamiliaD, familia) is None:
        raise HTTPException(status_code=400, detail="Esa familia de la plantilla D no existe.")
    datos["familia_id"] = familia
    datos["plantillas"] = _plantillas(cuerpo.plantillas, cuerpo.confirmarSinPlantillas)
    return datos


# --- Rutas ---------------------------------------------------------------------------------------

@router.get("/api/catalogo")
def catalogo(db: Session = Depends(get_db), _: models.PanelUser = Depends(usuario_actual)):
    return catalogo_activo(db)


@router.get("/api/panel/lineas")
def lista(db: Session = Depends(get_db), _: models.PanelUser = Depends(solo_admin)):
    return {"lineas": [_para_panel(l) for l in _lineas(db, False)], "familias": _familias(db)}


@router.post("/api/panel/lineas", status_code=201)
def alta(cuerpo: LineaNueva, db: Session = Depends(get_db),
         usuario: models.PanelUser = Depends(solo_admin)):
    datos = _valida(cuerpo, db)
    ultima = db.query(models.LineaNegocio).order_by(models.LineaNegocio.orden.desc()).first()
    linea = models.LineaNegocio(id=_id_desde(datos["nombre"], db),
                                orden=(ultima.orden + 1) if ultima else 0,
                                activa=True, actualizado_por=usuario.email, **datos)
    db.add(linea)
    db.commit()
    db.refresh(linea)
    return _para_panel(linea)


@router.post("/api/panel/lineas/{linea_id}/foto")
def foto(linea_id: str, fichero: UploadFile = File(...), alt: str = Form(""),
         db: Session = Depends(get_db), usuario: models.PanelUser = Depends(solo_admin)):
    linea = db.get(models.LineaNegocio, linea_id)
    if linea is None:
        raise HTTPException(status_code=404, detail="Esa línea no existe.")
    alt = alt.strip() or linea.alt
    if not alt:
        raise HTTPException(status_code=400,
                            detail="Falta el texto alternativo: lo lee quien tiene las imágenes bloqueadas.")
    if len(alt) > LIMITES["alt"]:
        raise HTTPException(status_code=400, detail="El texto alternativo admite 200 caracteres como mucho.")
    datos = fichero.file.read(fotos.MAXIMO_BYTES + 1)
    if len(datos) > fotos.MAXIMO_BYTES:
        raise HTTPException(status_code=413, detail="La foto pesa más de 8 MB.")
    try:
        jpeg = fotos.prepara(datos)
    except fotos.FotoNoValida as e:
        raise HTTPException(status_code=400, detail=str(e))
    linea.img = fotos.guarda(linea.id, jpeg)
    linea.alt = alt
    linea.actualizado_por = usuario.email
    db.commit()
    db.refresh(linea)
    return _para_panel(linea)


@router.get("/media/lineas/{archivo}")
def media(archivo: str):
    destino = fotos.resuelve(archivo)
    if not destino:
        raise HTTPException(status_code=404, detail="No encontrado")
    # El nombre lleva la huella del contenido: el mismo nombre es siempre la misma foto.
    return FileResponse(destino, media_type="image/jpeg",
                        headers={"Cache-Control": "public, max-age=31536000, immutable"})
