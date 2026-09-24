"""
Las rutas de las entregas a medida.

Todo lo de aquí exige sesión del panel:

  `/api/entregas…`  el panel. Exige sesión de persona, no la clave compartida.

## Por qué cada entrega crea un enlace del acortador

No es un rodeo. Al crear la fila en `links`, el acortador de siempre resuelve `/{slug}` hacia la
presentación, sus clics se registran donde ya se registran, y la regla de aviso por interés
repetido funciona sobre `alerts` sin una línea nueva. El acortador no se toca y hace el trabajo
(constitución, principio I).

Lo que ve el cliente —sus imágenes y la página de su propuesta— vive en `publicas.py`, porque
ahí no hay sesión y las reglas son otras.

## El envío es manual, y aquí se nota

No hay ninguna ruta que mande un correo. Es deliberado: *"deja que el proceso se siga haciendo
manual el copiar y pegar en el mail"*. Marcar una entrega como entregada es un gesto de la
persona que ya la pegó y la envió, no un envío.
"""

import logging
import secrets
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...database import get_db
from ... import models
from ...auth.dependencias import usuario_actual, exigir_cuenta
from . import almacen, carrusel, paginas as mod_paginas
from .publicas import _existe, _url_media

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
    contacto_empresa: str = ''
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
        if not (contacto.empresa or "").strip():
            raise HTTPException(
                status_code=400,
                detail="A %s le falta la empresa, y el correo la nombra. Complétala antes de "
                       "entregarle una propuesta." % contacto.nombre)
        return contacto

    if datos.contacto and datos.contacto.nombre.strip():
        # Nombre y empresa son obligatorios en una entrega: el correo saluda por el nombre y el
        # texto habla de la empresa. Una propuesta "personalizada" que no nombra a quien va
        # dirigida no lo es (petición del propietario, 2026-09-24).
        if not datos.contacto.empresa.strip():
            raise HTTPException(
                status_code=400,
                detail="Falta la empresa del contacto: el correo la nombra.")
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
        contacto_empresa=(entrega.contacto.empresa or "") if entrega.contacto else "",
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

# Dominios de Canva a los que el servidor acepta llamar. Es una lista corta y cerrada a
# propósito: comprobar una dirección que escribe otra persona significa que **el servidor** hace
# la petición, y sin esta restricción cualquiera podría usarlo para llamar a la red interna.
_DOMINIOS_CANVA = ("canva.com", "canva.link", "canva.site")


class Enlace(BaseModel):
    url: str = Field(min_length=1, max_length=500)


@router.post("/api/entregas/comprobar-enlace")
def comprobar_enlace(datos: Enlace, _: models.PanelUser = Depends(usuario_actual)):
    """
    ¿Ese enlace de Canva resuelve? (FR-101, escenario 4 de US1)

    Se comprueba **antes** de armar el correo, no después de enviarlo: un enlace muerto en una
    propuesta a medida se descubre cuando el cliente ya no puede abrirla.

    Un fallo aquí no bloquea nada. Devuelve el veredicto y quien decide es la persona: el enlace
    puede ser correcto y Canva estar lento, y no es asunto de esta herramienta impedirlo.
    """
    from urllib.parse import urlparse
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError

    partes = urlparse(datos.url.strip())
    if partes.scheme != "https":
        return {"ok": False, "motivo": "El enlace tiene que empezar por https://"}
    anfitrion = (partes.hostname or "").lower()
    if not any(anfitrion == d or anfitrion.endswith("." + d) for d in _DOMINIOS_CANVA):
        return {"ok": False,
                "motivo": "No parece un enlace de Canva. Se comprueban canva.com y canva.link."}

    peticion = Request(datos.url.strip(), method="GET",
                       headers={"User-Agent": "CentauroADS-Links/1.0"})
    try:
        with urlopen(peticion, timeout=6) as r:
            return {"ok": 200 <= r.status < 400, "estado": r.status}
    except HTTPError as e:
        if e.code in (401, 403):
            return {"ok": False, "estado": e.code,
                    "motivo": "Canva responde que la presentación no es pública. "
                              "Compruébalo en «Compartir» antes de entregarla."}
        return {"ok": False, "estado": e.code, "motivo": "Canva responde %d" % e.code}
    except (URLError, TimeoutError, OSError) as e:
        # No se pudo comprobar no es lo mismo que está roto, y decirlo así evita que alguien
        # cambie un enlace correcto por culpa de un corte de red.
        log.info("no se pudo comprobar %s: %s", datos.url, e)
        return {"ok": None, "motivo": "No se pudo comprobar ahora mismo. Ábrelo tú para estar seguro."}


@router.get("/api/contactos")
def buscar_contactos(q: str = "", db: Session = Depends(get_db),
                     _: models.PanelUser = Depends(usuario_actual)):
    """Los contactos, para elegir uno sin salir del flujo. `q` filtra por nombre o empresa."""
    consulta = db.query(models.Contact)
    if q.strip():
        patron = "%" + q.strip() + "%"
        consulta = consulta.filter(
            models.Contact.nombre.ilike(patron) | models.Contact.empresa.ilike(patron)
            | models.Contact.email.ilike(patron))
    filas = consulta.order_by(models.Contact.nombre).limit(50).all()
    return [{"id": c.id, "nombre": c.nombre, "email": c.email or "",
             "empresa": c.empresa or ""} for c in filas]


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
async def subir(entrega_id: int, fichero: List[UploadFile] = File(...),
                db: Session = Depends(get_db),
                usuario: models.PanelUser = Depends(usuario_actual)):
    """
    Sube el PDF —o varias imágenes— y devuelve las páginas como miniaturas elegibles.

    Todavía no se elige nada: esto solo rasteriza y guarda. La elección va en el `PUT`.

    **Admite varios ficheros a la vez, y no es un capricho.** Cada subida reemplaza a la anterior,
    así que aceptando uno solo la vía de imágenes sueltas (FR-109) nunca podía llegar al mínimo de
    dos páginas: la segunda imagen borraba a la primera. Un PDF aporta sus páginas; cada imagen,
    una. Lo descubrió intentar usarlo, no leerlo.
    """
    entrega = _busca(db, entrega_id)
    encontradas = []
    for subido in fichero:
        datos = await subido.read()
        try:
            encontradas.extend(mod_paginas.lee(datos))
        except mod_paginas.FicheroNoValido as e:
            raise HTTPException(status_code=400, detail=str(e))
    if len(encontradas) > mod_paginas.LIMITE_PAGINAS:
        raise HTTPException(
            status_code=400,
            detail="Entre todo suman %d páginas y el límite son %d."
                   % (len(encontradas), mod_paginas.LIMITE_PAGINAS))

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
        # Con `Image.open` a secas, PIL deja el fichero **abierto** hasta que se recoge el
        # objeto. En Windows eso impide borrarlo después —lo descubrió una prueba, con un
        # «Acceso denegado» al rearmar el carrusel— y en Linux no falla pero va acumulando
        # descriptores en un servidor que no se reinicia. `convert` ya devuelve una copia
        # independiente, así que el original se puede cerrar en cuanto se sale del `with`.
        with Image.open(destino) as bruta:
            imagenes.append(bruta.convert("RGB"))
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
