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
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

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


def _url_media(entrega: models.Entrega, nombre: str, linea: Optional[str] = None) -> str:
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

    Con `linea`, la de un fichero de ese espacio (004), con la misma marca.

    Va por la clave de la entrega (`/media/e/<clave>/…`) y no por su número, que se podía
    recorrer en bucle. Solo una entrega anterior, sin clave, sigue saliendo por número: es la
    dirección que llevan sus correos ya enviados. Los ficheros no se mueven; cambia la dirección.
    """
    espacio = "espacios/%s/" % linea if linea is not None else ""
    if entrega.clave:
        base = "/media/e/%s/%s%s" % (entrega.clave, espacio, nombre)
    else:
        base = "/media/entregas/%d/%s%s" % (entrega.id, espacio, nombre)
    destino = almacen.resuelve(entrega.id, nombre, linea)
    if not destino:
        return base
    marca = os.stat(destino)
    return "%s?v=%x" % (base, (marca.st_mtime_ns & 0xFFFFFFFFFF) ^ marca.st_size)


def _existe(entrega: models.Entrega, nombre: str, linea: Optional[str] = None):
    return (_url_media(entrega, nombre, linea)
            if almacen.resuelve(entrega.id, nombre, linea) else None)


_INMUTABLE = {"Cache-Control": "public, max-age=31536000, immutable"}

# Lo que genera `secrets.token_hex(16)`. Se mira la forma antes de tocar la base de datos.
_CLAVE = re.compile(r"[0-9a-f]{32}")


def _sirve(entrega: Optional[models.Entrega], fichero: str, linea: Optional[str] = None):
    """
    El fichero, o 404. `almacen.resuelve` valida nombre y línea por forma y el destino por ruta
    real; aquí solo se decide si hay entrega de la que servirlo.
    """
    destino = almacen.resuelve(entrega.id, fichero, linea) if entrega else None
    if not destino:
        raise HTTPException(status_code=404, detail="No encontrado")
    # Cacheable a largo plazo porque la dirección lleva marca de versión (`_url_media`): cuando
    # el fichero cambia, cambia la dirección. Sin esa marca esto guardaba para siempre un carrusel
    # que luego se rehacía, y el correo se quedaba con el viejo.
    return FileResponse(destino, headers=_INMUTABLE)


def _por_clave(db: Session, clave: str) -> Optional[models.Entrega]:
    if not _CLAVE.fullmatch(clave or ""):
        return None
    return db.query(models.Entrega).filter(models.Entrega.clave == clave).first()


def _anterior(db: Session, entrega_id: int) -> Optional[models.Entrega]:
    """
    La entrega por número, SOLO si es de antes de la clave. Una con clave por aquí daría 200 a
    quien recorre números, que es justo lo que la clave vino a cerrar.
    """
    entrega = db.get(models.Entrega, entrega_id)
    return entrega if entrega and entrega.clave is None else None


@router.get("/media/e/{clave}/{fichero}")
def media(clave: str, fichero: str, db: Session = Depends(get_db)):
    """Las imágenes de una entrega, servidas desde el volumen, por su clave."""
    return _sirve(_por_clave(db, clave), fichero)


@router.get("/media/e/{clave}/espacios/{linea}/{fichero}")
def media_espacio(clave: str, linea: str, fichero: str, db: Session = Depends(get_db)):
    """
    Las imágenes de un espacio que acompaña a la entrega (004). Aquí entran TRES trozos de ruta
    desde fuera: la clave se mira aquí por forma; línea y fichero, en `almacen.resuelve`.
    """
    return _sirve(_por_clave(db, clave), fichero, linea)


@router.get("/media/entregas/{entrega_id}/{fichero}")
def media_anterior(entrega_id: int, fichero: str, db: Session = Depends(get_db)):
    """Las de antes de la clave, por número: lo que llevan sus correos ya enviados."""
    return _sirve(_anterior(db, entrega_id), fichero)


@router.get("/media/entregas/{entrega_id}/espacios/{linea}/{fichero}")
def media_espacio_anterior(entrega_id: int, linea: str, fichero: str,
                           db: Session = Depends(get_db)):
    return _sirve(_anterior(db, entrega_id), fichero, linea)


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
  <a class="ir" href="{destino}" rel="noopener">{boton} &rarr;</a>
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


def _de_slug(db: Session, slug: str):
    """El enlace activo y su entrega, o 404."""
    enlace = db.query(models.Link).filter(
        models.Link.slug == slug, models.Link.is_active.is_(True)).first()
    entrega = enlace and db.query(models.Entrega).filter(models.Entrega.link_id == enlace.id).first()
    if not entrega:
        raise HTTPException(status_code=404, detail="No encontrado")
    return enlace, entrega


def _ip(request: Request) -> str:
    ip = request.headers.get("X-Forwarded-For")
    return ip.split(",")[0].strip() if ip else (
        request.headers.get("X-Real-IP") or (request.client.host if request.client else "unknown"))


# Lo que se guarda de cada apertura, recortado: la petición es anónima y sus cabeceras no tienen
# tope (revisión de seguridad de la 010).
_agente = lambda request: request.headers.get("user-agent", "")[:300]
_distintivo = lambda request: (request.query_params.get("c") or "")[:64] or None


def _cuenta_clic(db: Session, enlace: models.Link, request: Request) -> None:
    """El clic de la entrega, como el acortador. Lo que se añada a la sesión se guarda con él."""
    db.add(models.Click(
        link_id=enlace.id, ip=_ip(request)[:50],
        user_agent=_agente(request),
        referer=request.headers.get("referer", "")[:500],
        contact_token=_distintivo(request),
    ))
    enlace.click_count = (enlace.click_count or 0) + 1
    enlace.last_clicked_at = datetime.now(timezone.utc)
    db.commit()


def _base(request: Request) -> str:
    """
    La raíz pública para las imágenes de la tarjeta. El esquema sale de lo que diga el proxy, no de
    lo que crea uvicorn: TLS lo termina EasyPanel, así que `base_url` dice "http://" para una página
    que el cliente pidió por https. La tarjeta anunciaba entonces su imagen en claro, y WhatsApp
    descarta el contenido mixto: la tarjeta salía sin foto. Sin la cabecera —en local— se queda lo
    de siempre.
    """
    base = str(request.base_url).rstrip("/")
    proto = (request.headers.get("X-Forwarded-Proto") or "").split(",")[0].strip().lower()
    if proto in ("http", "https"):
        base = "%s://%s" % (proto, base.split("://", 1)[-1])
    return base


@router.get("/p/{slug}", response_class=HTMLResponse)
def previa(slug: str, request: Request, db: Session = Depends(get_db)):
    """
    La página que lee WhatsApp para dibujar su tarjeta. Las personas no la ven: pasan de largo.

    Registra el clic igual que el acortador, y por las mismas razones. Si el registro fallara, la
    página se sirve de todos modos: el cliente no puede quedarse sin su propuesta porque a
    nosotros nos falle la contabilidad.
    """
    enlace, entrega = _de_slug(db, slug)

    # Una persona: se cuenta su apertura y se la manda a su propuesta. Que WhatsApp mire el
    # enlace al pegarlo no es que el cliente lo haya abierto -contarlo inflaba las estadísticas y
    # disparaba el aviso de interés por algo que hizo quien envía-, así que el robot no cuenta.
    if not _es_robot(request.headers.get("user-agent", "")):
        try:
            _cuenta_clic(db, enlace, request)
        except Exception:
            db.rollback()
            log.exception("no se pudo registrar la apertura de %s", slug)

        # Y se va derecho a su propuesta. Quien pulsa quiere verla, no un resumen de lo que ya le
        # dijimos en el correo: la página existe por la tarjeta, y ese peaje no lo paga el cliente.
        return RedirectResponse(entrega.canva_url, status_code=307)

    e = html.escape
    bajada = " ".join(_rellena(entrega.texto, entrega.contacto).split())[:200] or \
        "La propuesta que preparamos para tu marca."
    portada = _existe(entrega, "og.jpg")
    base = _base(request)
    return HTMLResponse(_PAGINA.format(
        titulo=e(entrega.titulo),
        bajada=e(bajada),
        destino=e(entrega.canva_url),
        boton="Ver la propuesta",
        og_imagen=('<meta property="og:image" content="%s%s">' % (e(base), e(portada))
                   if portada else ""),
        imagen=('<img src="%s" alt="%s">' % (e(portada), e(entrega.titulo))) if portada else "",
    ))


# Los productos a medida (008) llevan este prefijo. No se importa de rutas.py: rutas importa de aquí.
_A_MEDIDA = "medida--"


def _espacio_de(db: Session, entrega: models.Entrega, espacio: str) -> Optional[dict]:
    """
    El espacio `espacio` de ESTA entrega, ya resuelto (nombre, línea, destino e imagen), o None.

    Es de la entrega si es un producto a medida suyo (fila propia) o una línea activa del catálogo
    incluida en sus servicios. Lo propio de la entrega (004) manda sobre el catálogo; la imagen es
    la primera página elegida de su carrusel, si lo tiene, o la foto de la línea.
    """
    if not almacen.linea_valida(espacio):
        return None
    fila = db.query(models.EntregaEspacio).filter(
        models.EntregaEspacio.entrega_id == entrega.id,
        models.EntregaEspacio.linea_id == espacio).first()
    linea = None
    if espacio.startswith(_A_MEDIDA):
        if not fila:
            return None
    else:
        if espacio not in (entrega.servicios or "").split(","):
            return None
        linea = db.get(models.LineaNegocio, espacio)
        if not linea or not linea.activa:
            return None
    propio = lambda campo: (getattr(fila, campo) or "").strip() if fila else ""
    imagen = ""
    paginas = sorted(json.loads(fila.paginas or "[]"), key=lambda p: p["orden"]) if fila else []
    if paginas:
        # Su portada ligera (og.jpg, desde la 010); un carrusel armado antes, su primera página.
        imagen = _existe(entrega, "og.jpg", espacio) or \
            _url_media(entrega, paginas[0]["ruta"].rsplit("/", 1)[-1], espacio)
    elif linea and (linea.img or "").strip():
        img = linea.img.strip()
        imagen = img if re.match(r"^(https?:)?//|^/", img) else "/static/email/" + img
    return {
        "nombre": propio("nombre") or (linea.nombre if linea else ""),
        "cobertura": propio("cobertura") or (linea.cobertura if linea else ""),
        "destino": propio("canva_url") or ((linea.canva or "").strip() if linea else "") or entrega.canva_url,
        "imagen": imagen,
    }


@router.get("/p/{slug}/{espacio}", response_class=HTMLResponse)
def previa_espacio(slug: str, espacio: str, request: Request, db: Session = Depends(get_db)):
    """
    El enlace propio de un espacio de la entrega (010). WhatsApp dibuja la tarjeta solo del PRIMER
    enlace de cada mensaje, así que cada servicio va en su mensaje con este enlace: su tarjeta lleva
    nuestra foto, su nombre y su ubicación, en vez del título interno del diseño de Canva.

    Como `/p/{slug}`: el robot lee la tarjeta; la persona se apunta y pasa a su presentación.
    """
    enlace, entrega = _de_slug(db, slug)
    datos = _espacio_de(db, entrega, espacio)
    if not datos:
        raise HTTPException(status_code=404, detail="No encontrado")

    if not _es_robot(request.headers.get("user-agent", "")):
        try:
            db.add(models.AperturaEspacio(
                entrega_id=entrega.id, linea=espacio, ip=_ip(request)[:50],
                user_agent=_agente(request), contact_token=_distintivo(request)))
            _cuenta_clic(db, enlace, request)
        except Exception:
            db.rollback()
            log.exception("no se pudo registrar la apertura de %s/%s", slug, espacio)
        return RedirectResponse(datos["destino"], status_code=307)

    e = html.escape
    imagen = datos["imagen"]
    absoluta = imagen if re.match(r"^https?://", imagen) else (_base(request) + imagen if imagen else "")
    return HTMLResponse(_PAGINA.format(
        titulo=e(datos["nombre"]),
        bajada=e(datos["cobertura"]),
        destino=e(datos["destino"]),
        boton="Ver la presentación",
        og_imagen=('<meta property="og:image" content="%s">' % e(absoluta)) if absoluta else "",
        imagen=('<img src="%s" alt="%s">' % (e(imagen), e(datos["nombre"]))) if imagen else "",
    ))
