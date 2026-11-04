"""
/c/<slug> — el enlace corto con click_id y fingerprint.

Es la misma dirección corta, con `/c/` delante. Funciona en dos pasos:

  1. `GET /c/<slug>` sirve una página mínima que carga `/static/click-id.js`. El script calcula el
     fbc de Meta (si la persona viene de un anuncio) y la huella del dispositivo.
  2. El script sigue a `GET /c/<slug>/ir?click_id=…&fingerprint=…&q=…`, que guarda el clic con los
     dos valores y redirige al destino con esos mismos parámetros. `q` lleva los parámetros con los
     que se llamó al link (utm_*, fbclid…) y también se reenvían al destino.

El clic se cuenta en el paso 2: así se guarda con lo que se calculó, y los robots que solo leen la
página (vistas previas de WhatsApp, buscadores) no inflan las estadísticas.

Va aparte del redirect de siempre, `/{slug}`, que no se toca (constitución, principio I): ese sigue
siendo un 307 directo. Quien quiera el click_id usa `/c/<slug>`; los enlaces ya impresos no cambian.
"""

import os
import re
import time
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import parse_qsl, quote, urlencode, urlparse, urlunparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models
from .database import get_db

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))

# Lo que puede traer un fbclid de verdad. Lo demás se ignora: va a parar a una URL ajena.
FBCLID_VALIDO = re.compile(r"^[A-Za-z0-9_-]{1,500}$")
# Lo que el script puede mandar. Cualquier otra cosa no se guarda ni se reenvía.
FBC_VALIDO = re.compile(r"^fb\.\d\.\d{1,16}\.[A-Za-z0-9_-]{1,500}$")
HUELLA_VALIDA = re.compile(r"^fp\.[0-9a-f]{28}$")


def fbc_de(fbclid: Optional[str], ahora_ms: Optional[int] = None) -> Optional[str]:
    """El fbc de Meta, `fb.1.<milisegundos>.<fbclid>`. None si el fbclid falta o no es válido."""
    if not fbclid or not FBCLID_VALIDO.match(fbclid):
        return None
    return f"fb.1.{ahora_ms if ahora_ms is not None else int(time.time() * 1000)}.{fbclid}"


def valores_validos(click_id: Optional[str], fingerprint: Optional[str]) -> tuple:
    """(click_id, fingerprint) limpios. Sin click_id pero con huella, el click_id es la huella."""
    huella = fingerprint if fingerprint and HUELLA_VALIDA.match(fingerprint) else None
    cid = click_id if click_id and (FBC_VALIDO.match(click_id) or HUELLA_VALIDA.match(click_id)) else None
    return (cid or huella), huella


def con_parametros(destino: str, valores: dict) -> str:
    """El destino con esos parámetros añadidos (o sustituidos), conservando lo demás."""
    valores = {k: v for k, v in valores.items() if v}
    partes = urlparse(destino)
    query = [(k, v) for k, v in parse_qsl(partes.query, keep_blank_values=True) if k not in valores]
    query.extend(valores.items())
    return urlunparse(partes._replace(query=urlencode(query)))


def con_click_id(destino: str, valor: str) -> str:
    return con_parametros(destino, {"click_id": valor})


# Los que calcula este módulo: si llegan en la llamada, se ignoran (nadie puede imponer su valor).
PROPIOS = {"click_id", "fingerprint"}
MAX_REENVIADOS = 30


def parametros_a_reenviar(query: Optional[str]) -> list:
    """Los parámetros con los que se llamó a /c/<slug> (utm_*, fbclid…), limpios y acotados."""
    pares = []
    for k, v in parse_qsl(query or "", keep_blank_values=True):
        if k in PROPIOS or not k or len(k) > 100:
            continue
        pares.append((k, v[:1000]))
        if len(pares) == MAX_REENVIADOS:
            break
    return pares


def destino_final(destino: str, reenviados: list, click_id: Optional[str], huella: Optional[str]) -> str:
    """
    El destino guardado + los parámetros de la llamada + click_id y fingerprint. Si un parámetro de la
    llamada ya está en el destino, gana el de la llamada: es el que trae la campaña concreta.
    """
    partes = urlparse(destino)
    nuevos = {k for k, _ in reenviados}
    query = [(k, v) for k, v in parse_qsl(partes.query, keep_blank_values=True) if k not in nuevos]
    query.extend(reenviados)
    url = urlunparse(partes._replace(query=urlencode(query)))
    return con_parametros(url, {"click_id": click_id, "fingerprint": huella})


def _ip_real(request: Request) -> str:
    # Igual que el redirect de siempre: detrás de Traefik la IP real llega en X-Forwarded-For.
    ip = request.headers.get("X-Forwarded-For")
    if ip:
        return ip.split(",")[0].strip()
    return request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")


def _enlace_activo(db: Session, slug: str) -> models.Link:
    link = db.query(models.Link).filter(
        models.Link.slug == slug, models.Link.is_active == True  # noqa: E712
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")
    return link


@router.get("/c/{slug}", response_class=HTMLResponse, include_in_schema=False)
async def enlace_con_click_id(
    slug: str,
    request: Request,
    fbclid: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    _enlace_activo(db, slug)
    ir = f"/c/{quote(slug, safe='')}/ir"
    # Sin JavaScript no hay huella; con fbclid, el fbc sí se puede calcular aquí. Los parámetros de
    # la llamada viajan enteros en `q` (el script hace lo mismo con location.search).
    fbc = fbc_de(fbclid)
    valores = {"click_id": fbc, "q": request.url.query}
    sin_js = ir + "?" + urlencode({k: v for k, v in valores.items() if v}) if any(valores.values()) else ir

    respuesta = templates.TemplateResponse(request, "click_id.html", {"ir": ir, "ir_sin_js": sin_js})
    # Cada visita calcula sus propios valores: que ningún navegador ni proxy guarde la página.
    respuesta.headers["Cache-Control"] = "no-store"
    respuesta.headers["X-Robots-Tag"] = "noindex"
    return respuesta


@router.get("/c/{slug}/ir", include_in_schema=False)
async def ir_al_destino(
    slug: str,
    request: Request,
    click_id: Optional[str] = Query(None),
    fingerprint: Optional[str] = Query(None),
    ref: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    link = _enlace_activo(db, slug)
    cid, huella = valores_validos(click_id, fingerprint)
    # Aquí la cabecera Referer es la propia página /c/<slug>; la procedencia real (Instagram, un
    # anuncio…) la vio esa página y la manda el script en `ref`. Sin ella, no hay procedencia.
    referer = request.headers.get("referer", "")
    if urlparse(referer).path == f"/c/{slug}":
        referer = (ref or "")[:1000]

    # El clic cuenta igual que en /{slug} (mismas estadísticas, mismo panel) y además guarda los dos.
    db.add(models.Click(
        link_id=link.id,
        ip=_ip_real(request),
        user_agent=request.headers.get("user-agent", ""),
        referer=referer,
        click_id=cid,
        fingerprint=huella,
    ))
    link.click_count += 1
    link.last_clicked_at = datetime.now(timezone.utc)
    db.commit()

    # `q` = los parámetros con los que se llamó a /c/<slug> (utm_*, fbclid…): se reenvían al destino.
    destino = destino_final(link.target_url, parametros_a_reenviar(q), cid, huella)
    respuesta = RedirectResponse(url=destino, status_code=307)
    respuesta.headers["Cache-Control"] = "no-store"
    respuesta.headers["X-Robots-Tag"] = "noindex"
    return respuesta
