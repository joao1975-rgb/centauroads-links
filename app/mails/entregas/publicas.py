"""
Lo que ve el cliente: sus imágenes y la página de su propuesta.

Está separado de `rutas.py` porque el público es otro. Ahí dentro todo exige sesión del panel;
aquí no hay sesión ninguna, y por eso las dos comprobaciones que quedan —que el nombre del
fichero sea suyo y que el enlace exista— son lo único que separa esto de servir cualquier cosa.

`/p/{slug}` existe aparte del acortador porque WhatsApp necesita una **página** con etiquetas
Open Graph para dibujar su tarjeta; una redirección 307 no le da nada que enseñar. Pero eso lo
necesita el robot que mira el enlace, no la persona que lo pulsa: a ella se la manda derecha a su
propuesta, sin pagar un clic de peaje para leer un resumen de lo que ya dice el correo.
"""

import html
import logging
import os
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from ...database import get_db
from ... import models
from . import almacen

log = logging.getLogger("centaurads.entregas")
router = APIRouter()


def _rellena(texto: str, contacto) -> str:
    """
    Sustituye los marcadores del texto, como hace `fill()` en el compositor.

    El texto se guarda CON sus marcadores —{destinatario}, {empresa}— porque el mismo texto sirve
    para el correo, para WhatsApp y para esta página, y quien redacta escribe una sola vez. Lo que
    no puede pasar es que lleguen sin rellenar a lo que ve el cliente: la tarjeta de WhatsApp
    decía "Preparamos esta propuesta para {empresa}", con las llaves y todo.

    "tu marca" es el mismo recambio que pone el correo cuando no hay empresa.
    """
    empresa = (getattr(contacto, "empresa", "") or "").strip() or "tu marca"
    nombre = (getattr(contacto, "nombre", "") or "").strip()
    return (texto or "").replace("{empresa}", empresa).replace("{destinatario}", nombre)


def _url_media(entrega_id: int, nombre: str) -> str:
    """
    La dirección pública de un fichero de la entrega, **con una marca de su versión**.

    Sin la marca esto era un fallo silencioso y caro: `carrusel.gif` se reescribe con el mismo
    nombre cada vez que se eligen otras páginas o se cambia el efecto, y se sirve como
    `immutable`. El navegador no vuelve a pedirlo nunca, así que el correo seguía enseñando el
    carrusel anterior mientras el servidor guardaba el nuevo. El proxy de imágenes de Gmail hace
    lo mismo, de modo que una propuesta corregida antes de enviarla habría salido mal.

    La marca sale del propio fichero (cuándo se escribió y cuánto ocupa), así que cambia sola
    cuando cambia el contenido y **no** cuando no cambia: la caché larga sigue valiendo, que es lo
    que quiere una imagen que viaja dentro de un correo.
    """
    base = "/media/entregas/%d/%s" % (entrega_id, nombre)
    destino = almacen.resuelve(entrega_id, nombre)
    if not destino:
        return base
    marca = os.stat(destino)
    return "%s?v=%x" % (base, (marca.st_mtime_ns & 0xFFFFFFFFFF) ^ marca.st_size)


def _existe(entrega_id: int, nombre: str):
    return _url_media(entrega_id, nombre) if almacen.resuelve(entrega_id, nombre) else None


@router.get("/media/entregas/{entrega_id}/{fichero}")
def media(entrega_id: int, fichero: str):
    """
    Las imágenes de una entrega, servidas desde el volumen.

    `almacen.resuelve` valida el nombre y comprueba que el fichero resultante no se sale de la
    carpeta de esa entrega. Aquí solo queda decidir el 404.
    """
    destino = almacen.resuelve(entrega_id, fichero)
    if not destino:
        raise HTTPException(status_code=404, detail="No encontrado")
    # Cacheable a largo plazo porque la dirección lleva marca de versión (`_url_media`): cuando
    # el fichero cambia, cambia la dirección. Sin esa marca esto guardaba para siempre un carrusel
    # que luego se rehacía, y el correo se quedaba con el viejo.
    return FileResponse(destino, headers={"Cache-Control": "public, max-age=31536000, immutable"})


_PAGINA = """<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{titulo}</title>
<meta property="og:type" content="website">
<meta property="og:title" content="{titulo}">
<meta property="og:description" content="{bajada}">
<meta property="og:site_name" content="Centauro ADS">
{og_imagen}
<meta name="twitter:card" content="summary_large_image">
<style>
  :root {{ color-scheme: light; }}
  body {{ margin:0; background:#F6F4F1; color:#1B1720;
         font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
  .caja {{ max-width:620px; margin:0 auto; padding:48px 20px 64px; }}
  .marca {{ font-size:11px; font-weight:800; letter-spacing:.24em; text-transform:uppercase;
           color:#6B4B78; }}
  h1 {{ font-size:clamp(28px,6vw,40px); line-height:1.1; letter-spacing:-.02em; margin:14px 0 18px; }}
  p {{ color:#4A4351; margin:0 0 26px; }}
  img {{ display:block; width:100%; height:auto; border-radius:12px; margin:0 0 28px; }}
  a.ir {{ display:inline-block; background:#85439A; color:#fff; text-decoration:none;
         font-weight:800; padding:15px 30px; border-radius:10px; }}
  a.ir:hover {{ background:#6B3480; }}
  footer {{ margin-top:40px; font-size:13px; color:#6F6878; }}
</style>
</head><body><main class="caja">
  <div class="marca">Centauro ADS</div>
  <h1>{titulo}</h1>
  <p>{bajada}</p>
  {imagen}
  <a class="ir" href="{destino}" rel="noopener">Ver la propuesta &rarr;</a>
  <footer>Visibilidad que conecta &middot; Caracas, Venezuela</footer>
</main></body></html>"""


# Quienes piden el enlace para DIBUJAR una tarjeta, no para leerla. Son los unicos que necesitan
# la pagina; cualquier otro va derecho a su propuesta. La lista no tiene que ser exhaustiva: a un
# robot que no este aqui solo le pasa que su tarjeta sale sin adornos.
_ROBOTS = (
    "whatsapp", "facebookexternalhit", "facebot", "twitterbot", "telegrambot", "slackbot",
    "slack-imgproxy", "linkedinbot", "discordbot", "skypeuripreview", "embedly", "redditbot",
    "pinterest", "applebot", "googlebot", "bingbot", "vkshare", "quora link preview",
)


def _es_robot(agente: str) -> bool:
    a = (agente or "").lower()
    return any(r in a for r in _ROBOTS)


@router.get("/p/{slug}", response_class=HTMLResponse)
def previa(slug: str, request: Request, db: Session = Depends(get_db)):
    """
    La página que lee WhatsApp para dibujar su tarjeta. Las personas no la ven: pasan de largo.

    Registra el clic igual que el acortador, y por las mismas razones. Si el registro fallara, la
    página se sirve de todos modos: el cliente no puede quedarse sin su propuesta porque a
    nosotros nos falle la contabilidad.
    """
    enlace = db.query(models.Link).filter(
        models.Link.slug == slug, models.Link.is_active.is_(True)).first()
    if not enlace:
        raise HTTPException(status_code=404, detail="No encontrado")
    entrega = db.query(models.Entrega).filter(models.Entrega.link_id == enlace.id).first()
    if not entrega:
        raise HTTPException(status_code=404, detail="No encontrado")

    # Una persona: se cuenta su apertura y se la manda a su propuesta. Que WhatsApp mire el
    # enlace al pegarlo no es que el cliente lo haya abierto -contarlo inflaba las estadísticas y
    # disparaba el aviso de interés por algo que hizo quien envía-, así que el robot no cuenta.
    if not _es_robot(request.headers.get("user-agent", "")):
        try:
            ip = request.headers.get("X-Forwarded-For")
            ip = ip.split(",")[0].strip() if ip else (
                request.headers.get("X-Real-IP")
                or (request.client.host if request.client else "unknown"))
            db.add(models.Click(
                link_id=enlace.id, ip=ip,
                user_agent=request.headers.get("user-agent", ""),
                referer=request.headers.get("referer", ""),
                contact_token=request.query_params.get("c") or None,
            ))
            enlace.click_count = (enlace.click_count or 0) + 1
            enlace.last_clicked_at = datetime.now(timezone.utc)
            db.commit()
        except Exception:
            db.rollback()
            log.exception("no se pudo registrar la apertura de %s", slug)

        # Y se va derecho a su propuesta. Quien pulsa quiere verla, no un resumen de lo que ya le
        # dijimos en el correo: la página existe por la tarjeta, y ese peaje no lo paga el cliente.
        return RedirectResponse(entrega.canva_url, status_code=307)

    e = html.escape
    bajada = " ".join(_rellena(entrega.texto, entrega.contacto).split())[:200] or \
        "La propuesta que preparamos para tu marca."
    portada = _existe(entrega.id, "og.jpg")
    # El esquema sale de lo que diga el proxy, no de lo que crea uvicorn: TLS lo termina
    # EasyPanel, así que `base_url` dice "http://" para una página que el cliente pidió por
    # https. La tarjeta anunciaba entonces su imagen en claro, y WhatsApp descarta el contenido
    # mixto: la tarjeta salía sin foto. Sin la cabecera —en local— se queda lo de siempre.
    base = str(request.base_url).rstrip("/")
    proto = (request.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip().lower()
    if proto in ("http", "https"):
        base = "%s://%s" % (proto, base.split("://", 1)[-1])
    return HTMLResponse(_PAGINA.format(
        titulo=e(entrega.titulo),
        bajada=e(bajada),
        destino=e(entrega.canva_url),
        og_imagen=('<meta property="og:image" content="%s%s">' % (e(base), e(portada))
                   if portada else ""),
        imagen=('<img src="%s" alt="%s">' % (e(portada), e(entrega.titulo))) if portada else "",
    ))
