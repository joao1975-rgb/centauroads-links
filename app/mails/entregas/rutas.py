"""
Las rutas de las entregas a medida.

Tres grupos, con públicos distintos:

  `/api/entregas…`               el panel. Exige sesión de persona, no la clave compartida.
  `/media/entregas/{id}/{f}`     las imágenes, servidas desde el volumen. Público.
  `/p/{slug}`                    la página que ve el cliente, y la que lee WhatsApp. Público.

## Por qué cada entrega crea un enlace del acortador

No es un rodeo. Al crear la fila en `links`, el acortador de siempre resuelve `/{slug}` hacia la
presentación, sus clics se registran donde ya se registran, y la regla de aviso por interés
repetido funciona sobre `alerts` sin una línea nueva. El acortador no se toca y hace el trabajo
(constitución, principio I).

`/p/{slug}` existe aparte porque WhatsApp necesita una **página** con etiquetas Open Graph para
dibujar la tarjeta; una redirección 307 no le da nada que enseñar. Esa página registra el clic
igual y lleva a la presentación.

## El envío es manual, y aquí se nota

No hay ninguna ruta que mande un correo. Es deliberado: *"deja que el proceso se siga haciendo
manual el copiar y pegar en el mail"*. Marcar una entrega como entregada es un gesto de la
persona que ya la pegó y la envió, no un envío.
"""

import html
import logging
import secrets
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database import get_db
from ... import models
from ...auth.dependencias import usuario_actual, exigir_cuenta
from . import almacen, carrusel, paginas as mod_paginas

log = logging.getLogger("centaurads.entregas")
router = APIRouter()

MIN_PAGINAS = 2
MAX_PAGINAS = 4
_ALFABETO = "abcdefghijkmnopqrstuvwxyz23456789"   # sin l/1/0/o: estos enlaces se leen en voz alta


# ---------------------------------------------------------------------------
# Lo que entra y lo que sale
# ---------------------------------------------------------------------------

class ContactoRapido(BaseModel):
    """Crear el contacto sin salir del flujo (FR-102)."""
    nombre: str = Field(min_length=1, max_length=200)
    email: str = Field(default="", max_length=200)
    empresa: str = Field(default="", max_length=200)
    origen: str = Field(default="", max_length=50)


class EntregaEntrada(BaseModel):
    titulo: str = Field(min_length=1, max_length=200)
    canva_url: str = Field(min_length=1, max_length=500)
    texto: str = ""
    servicios: str = ""
    contact_id: Optional[int] = None
    contacto: Optional[ContactoRapido] = None
    sender_account_id: Optional[int] = None
    firma_cargo: Optional[str] = None


class EntregaSalida(BaseModel):
    id: int
    slug: str
    titulo: str
    canva_url: str
    texto: str
    servicios: str
    estado: str
    contact_id: int
    contacto_nombre: str
    enlace: str
    carrusel: Optional[str] = None
    portada: Optional[str] = None
    paginas: List[dict] = []


# ---------------------------------------------------------------------------
# Piezas comunes
# ---------------------------------------------------------------------------

def _slug_libre(db: Session) -> str:
    """Un slug corto que no choque con ninguno del acortador."""
    for _ in range(20):
        s = "e" + "".join(secrets.choice(_ALFABETO) for _ in range(7))
        if not db.query(models.Link).filter(models.Link.slug == s).first():
            return s
    raise HTTPException(status_code=500, detail="No se pudo generar un enlace único")


def _resuelve_contacto(db: Session, datos: EntregaEntrada) -> models.Contact:
    """
    El contacto de la entrega. **Obligatorio**: sin él no hay seguimiento ni aviso (FR-102).

    Se acepta uno existente por `contact_id` o uno nuevo en `contacto`. Si no viene ninguno, se
    rechaza aquí y no más adelante: es más barato explicarlo antes de haber subido un PDF.
    """
    if datos.contact_id:
        contacto = db.query(models.Contact).filter(
            models.Contact.id == datos.contact_id).first()
        if not contacto:
            raise HTTPException(status_code=404, detail="Ese contacto no existe")
        return contacto

    if datos.contacto and datos.contacto.nombre.strip():
        contacto = models.Contact(
            nombre=datos.contacto.nombre.strip(),
            email=(datos.contacto.email or "").strip(),
            empresa=(datos.contacto.empresa or "").strip(),
            origen=(datos.contacto.origen or "").strip(),
            token=secrets.token_urlsafe(24),
        )
        db.add(contacto)
        db.flush()
        return contacto

    raise HTTPException(
        status_code=400,
        detail="Una entrega necesita un contacto: elige uno o crea uno con su nombre y correo.",
    )


def _busca(db: Session, entrega_id: int) -> models.Entrega:
    entrega = db.query(models.Entrega).filter(models.Entrega.id == entrega_id).first()
    if not entrega:
        raise HTTPException(status_code=404, detail="Entrega no encontrada")
    return entrega


def _url_media(entrega_id: int, nombre: str) -> str:
    return "/media/entregas/%d/%s" % (entrega_id, nombre)


def _existe(entrega_id: int, nombre: str) -> Optional[str]:
    return _url_media(entrega_id, nombre) if almacen.resuelve(entrega_id, nombre) else None


def _a_salida(db: Session, entrega: models.Entrega) -> EntregaSalida:
    return EntregaSalida(
        id=entrega.id,
        slug=entrega.link.slug,
        titulo=entrega.titulo,
        canva_url=entrega.canva_url,
        texto=entrega.texto,
        servicios=entrega.servicios,
        estado=entrega.estado,
        contact_id=entrega.contact_id,
        contacto_nombre=entrega.contacto.nombre if entrega.contacto else "",
        enlace="/p/%s" % entrega.link.slug,
        carrusel=_existe(entrega.id, "carrusel.gif"),
        portada=_existe(entrega.id, "og.jpg"),
        paginas=[{
            "orden": p.orden, "url": _url_media(entrega.id, p.ruta.rsplit("/", 1)[-1]),
            "ancho": p.ancho, "alto": p.alto, "rotulo": p.rotulo or "",
            "aviso_precio": p.aviso_precio, "origen": p.origen,
        } for p in entrega.paginas],
    )


# ---------------------------------------------------------------------------
# API del panel
# ---------------------------------------------------------------------------

@router.post("/api/entregas", response_model=EntregaSalida)
def crear(datos: EntregaEntrada,
          db: Session = Depends(get_db),
          usuario: models.PanelUser = Depends(usuario_actual)):
    contacto = _resuelve_contacto(db, datos)

    if datos.sender_account_id:
        exigir_cuenta(db, usuario, datos.sender_account_id)

    enlace = models.Link(
        slug=_slug_libre(db),
        target_url=datos.canva_url,
        name="Entrega · %s" % datos.titulo[:150],
        description="Presentación propia entregada a %s" % contacto.nombre,
        category="entrega",
        is_active=True,
    )
    db.add(enlace)
    db.flush()

    entrega = models.Entrega(
        link_id=enlace.id,
        contact_id=contacto.id,
        titulo=datos.titulo.strip(),
        canva_url=datos.canva_url.strip(),
        texto=datos.texto or "",
        servicios=datos.servicios or "",
        sender_account_id=datos.sender_account_id,
        firma_cargo=datos.firma_cargo,
        panel_user_id=usuario.id,
        estado="borrador",
    )
    db.add(entrega)
    db.commit()
    db.refresh(entrega)
    log.info("entrega %d creada por %s para %s", entrega.id, usuario.email, contacto.nombre)
    return _a_salida(db, entrega)


@router.get("/api/entregas", response_model=List[EntregaSalida])
def listar(db: Session = Depends(get_db),
           usuario: models.PanelUser = Depends(usuario_actual)):
    filas = db.query(models.Entrega).order_by(models.Entrega.created_at.desc()).limit(200).all()
    return [_a_salida(db, e) for e in filas]


@router.get("/api/entregas/{entrega_id}", response_model=EntregaSalida)
def leer(entrega_id: int,
         db: Session = Depends(get_db),
         usuario: models.PanelUser = Depends(usuario_actual)):
    return _a_salida(db, _busca(db, entrega_id))


@router.put("/api/entregas/{entrega_id}", response_model=EntregaSalida)
def actualizar(entrega_id: int, datos: EntregaEntrada,
               db: Session = Depends(get_db),
               usuario: models.PanelUser = Depends(usuario_actual)):
    entrega = _busca(db, entrega_id)
    if datos.sender_account_id:
        exigir_cuenta(db, usuario, datos.sender_account_id)
        entrega.sender_account_id = datos.sender_account_id

    entrega.titulo = datos.titulo.strip()
    entrega.texto = datos.texto or ""
    entrega.servicios = datos.servicios or ""
    entrega.firma_cargo = datos.firma_cargo
    if datos.canva_url and datos.canva_url != entrega.canva_url:
        entrega.canva_url = datos.canva_url.strip()
        # El enlace corto ya puede estar en manos del cliente: se actualiza su destino en vez de
        # crear otro, para que lo que ya se envió siga llevando a la presentación correcta.
        entrega.link.target_url = entrega.canva_url
    if datos.contact_id or datos.contacto:
        entrega.contact_id = _resuelve_contacto(db, datos).id
    db.commit()
    db.refresh(entrega)
    return _a_salida(db, entrega)


@router.post("/api/entregas/{entrega_id}/paginas")
async def subir(entrega_id: int, fichero: UploadFile = File(...),
                db: Session = Depends(get_db),
                usuario: models.PanelUser = Depends(usuario_actual)):
    """
    Sube el PDF (o una imagen) y devuelve sus páginas como miniaturas elegibles.

    Todavía no se elige nada: esto solo rasteriza y guarda. La elección va en el `PUT`.
    """
    entrega = _busca(db, entrega_id)
    datos = await fichero.read()
    try:
        encontradas = mod_paginas.lee(datos)
    except mod_paginas.FicheroNoValido as e:
        raise HTTPException(status_code=400, detail=str(e))

    almacen.borra_entrega(entrega.id)
    entrega.paginas.clear()
    db.flush()

    salida = []
    for i, pagina in enumerate(encontradas):
        nombre = "p%d.jpg" % i
        almacen.guarda(entrega.id, nombre, carrusel.a_jpeg(pagina.imagen))
        salida.append({
            "indice": i,
            "url": _url_media(entrega.id, nombre),
            "ancho": pagina.ancho, "alto": pagina.alto,
            "rotulo": pagina.rotulo or ("Página %d" % (i + 1)),
            "aviso_precio": pagina.aviso_precio,
            "origen": pagina.origen,
            "pagina_pdf": pagina.numero,
        })
    db.commit()
    return {
        "paginas": salida,
        "minimo": MIN_PAGINAS, "maximo": MAX_PAGINAS,
        # Esto no es un adorno: el aviso de precios lee texto y no ve un precio dibujado dentro
        # de una imagen. Quien entrega tiene que saberlo (constitución, principio IV).
        "aviso": ("El aviso de precio solo detecta precios escritos como texto. "
                  "Si en la presentación el precio es parte de una imagen, no se detecta: "
                  "míralas antes de entregar."),
    }


class Seleccion(BaseModel):
    indices: List[int] = Field(min_length=MIN_PAGINAS, max_length=MAX_PAGINAS)


@router.put("/api/entregas/{entrega_id}/paginas", response_model=EntregaSalida)
def elegir(entrega_id: int, seleccion: Seleccion,
           db: Session = Depends(get_db),
           usuario: models.PanelUser = Depends(usuario_actual)):
    """Fija qué páginas van al carrusel y en qué orden, y lo arma."""
    from PIL import Image

    entrega = _busca(db, entrega_id)
    if len(set(seleccion.indices)) != len(seleccion.indices):
        raise HTTPException(status_code=400, detail="Hay una página repetida en la selección")

    imagenes, elegidas = [], []
    for i in seleccion.indices:
        destino = almacen.resuelve(entrega.id, "p%d.jpg" % i)
        if not destino:
            raise HTTPException(
                status_code=400,
                detail="La página %d ya no está; vuelve a subir el PDF" % i)
        imagenes.append(Image.open(destino).convert("RGB"))
        elegidas.append(i)

    tira = carrusel.arma(imagenes)
    almacen.guarda(entrega.id, "carrusel.gif", tira.datos)
    almacen.guarda(entrega.id, "og.jpg", carrusel.portada(imagenes[0]))
    if not tira.dentro_de_presupuesto:
        log.warning("entrega %d: carrusel de %d KB, por encima del presupuesto",
                    entrega.id, round(tira.bytes / 1024))

    entrega.paginas.clear()
    db.flush()
    for orden, i in enumerate(elegidas):
        im = imagenes[orden]
        db.add(models.EntregaPagina(
            entrega_id=entrega.id, orden=orden,
            ruta=almacen.ruta_relativa(entrega.id, "p%d.jpg" % i),
            ancho=im.width, alto=im.height, origen="pdf", pagina_pdf=i + 1,
        ))
    db.commit()
    db.refresh(entrega)
    return _a_salida(db, entrega)


@router.post("/api/entregas/{entrega_id}/entregada", response_model=EntregaSalida)
def marcar_entregada(entrega_id: int, canal: str = "email",
                     db: Session = Depends(get_db),
                     usuario: models.PanelUser = Depends(usuario_actual)):
    """
    La persona ya la pegó y la envió. Esto **no envía nada**: deja constancia de que salió.
    """
    entrega = _busca(db, entrega_id)
    entrega.estado = "entregada"
    entrega.entregada_en = datetime.now(timezone.utc)
    db.add(models.Delivery(
        link_id=entrega.link_id, channel=canal, contact_id=entrega.contact_id,
        formato="H", sender_account_id=entrega.sender_account_id,
        panel_user_id=usuario.id,
    ))
    db.commit()
    db.refresh(entrega)
    return _a_salida(db, entrega)


# ---------------------------------------------------------------------------
# Públicas
# ---------------------------------------------------------------------------

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
    # Los ficheros de una entrega no cambian una vez escritos: si cambian las páginas, cambia la
    # entrega entera. Se pueden cachear con tranquilidad.
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


@router.get("/p/{slug}", response_class=HTMLResponse)
def previa(slug: str, request: Request, db: Session = Depends(get_db)):
    """
    La página que ve el cliente y la que lee WhatsApp para dibujar su tarjeta.

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

    e = html.escape
    bajada = " ".join((entrega.texto or "").split())[:200] or \
        "La propuesta que preparamos para tu marca."
    portada = _existe(entrega.id, "og.jpg")
    base = str(request.base_url).rstrip("/")
    return HTMLResponse(_PAGINA.format(
        titulo=e(entrega.titulo),
        bajada=e(bajada),
        destino=e(entrega.canva_url),
        og_imagen=('<meta property="og:image" content="%s%s">' % (e(base), e(portada))
                   if portada else ""),
        imagen=('<img src="%s" alt="%s">' % (e(portada), e(entrega.titulo))) if portada else "",
    ))
