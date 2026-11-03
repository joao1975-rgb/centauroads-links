"""
/c/<slug> — el enlace corto con click_id.

Es la misma dirección corta, con `/c/` delante. En vez de redirigir en el servidor, sirve una página
mínima que carga `/static/click-id.js`; ese script calcula el fbc de Meta (o, sin fbclid, la huella
del dispositivo) y abre el destino con `?click_id=<valor>`.

Va aparte del redirect de siempre, `/{slug}`, que no se toca (constitución, principio I): ese sigue
siendo un 307 directo. Quien quiera el click_id usa `/c/<slug>`; los enlaces ya impresos no cambian.
"""

import os
import re
import time
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from . import models
from .database import get_db

router = APIRouter()
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates"))

# Lo que puede traer un fbclid de verdad. Lo demás se ignora: va a parar a una URL ajena.
FBCLID_VALIDO = re.compile(r"^[A-Za-z0-9_-]{1,500}$")


def fbc_de(fbclid: Optional[str], ahora_ms: Optional[int] = None) -> Optional[str]:
    """El fbc de Meta, `fb.1.<milisegundos>.<fbclid>`. None si el fbclid falta o no es válido."""
    if not fbclid or not FBCLID_VALIDO.match(fbclid):
        return None
    return f"fb.1.{ahora_ms if ahora_ms is not None else int(time.time() * 1000)}.{fbclid}"


def con_click_id(destino: str, valor: str) -> str:
    """El destino con `click_id` añadido (o sustituido), conservando lo demás."""
    partes = urlparse(destino)
    query = [(k, v) for k, v in parse_qsl(partes.query, keep_blank_values=True) if k != "click_id"]
    query.append(("click_id", valor))
    return urlunparse(partes._replace(query=urlencode(query)))


def _ip_real(request: Request) -> str:
    # Igual que el redirect de siempre: detrás de Traefik la IP real llega en X-Forwarded-For.
    ip = request.headers.get("X-Forwarded-For")
    if ip:
        return ip.split(",")[0].strip()
    return request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown")


@router.get("/c/{slug}", response_class=HTMLResponse, include_in_schema=False)
async def enlace_con_click_id(
    slug: str,
    request: Request,
    fbclid: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    link = db.query(models.Link).filter(
        models.Link.slug == slug, models.Link.is_active == True  # noqa: E712
    ).first()
    if not link:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")

    # El clic cuenta igual que en /{slug}: mismas estadísticas, mismo panel.
    db.add(models.Click(
        link_id=link.id,
        ip=_ip_real(request),
        user_agent=request.headers.get("user-agent", ""),
        referer=request.headers.get("referer", ""),
    ))
    link.click_count += 1
    link.last_clicked_at = datetime.now(timezone.utc)
    db.commit()

    # Sin JavaScript no hay huella; con fbclid, el fbc sí se puede calcular aquí.
    fbc = fbc_de(fbclid)
    sin_js = con_click_id(link.target_url, fbc) if fbc else link.target_url

    respuesta = templates.TemplateResponse(
        request, "click_id.html", {"destino": link.target_url, "destino_sin_js": sin_js},
    )
    # Cada visita calcula su propio click_id: que ningún navegador ni proxy guarde la página.
    respuesta.headers["Cache-Control"] = "no-store"
    respuesta.headers["X-Robots-Tag"] = "noindex"
    return respuesta
