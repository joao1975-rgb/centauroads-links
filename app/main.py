"""
CentauroADS Links — Acortador de URLs corporativo
Proyecto standalone para Easypanel / DigitalOcean
"""

from fastapi import FastAPI, Request, Depends, HTTPException, Form, Query, Header
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlparse
import secrets
import os
import logging
from pydantic import BaseModel

from .database import engine, get_db, Base, SessionLocal
from . import models, schemas
from .migracion import migrar
from .auth import superadmin

# ---------------------------------------------------------------------------
# Crear tablas y poner el esquema al día
#   migrar() es idempotente y solo añade: nunca borra, renombra ni cambia tipos. Corre ANTES de
#   servir tráfico para que ninguna petición llegue a un esquema a medias. En una instalación
#   nueva no encuentra nada que ampliar y se limita a crear las tablas.
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)
migrar(engine)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="CentauroADS Links",
    description="Acortador de URLs corporativo — Centauro ADS",
    version="1.0.0",
)

def origenes_cors(valor: Optional[str]) -> list[str]:
    """
    Orígenes permitidos a partir de CORS_ORIGINS (separados por comas).

    Vacía = ningún origen cruzado: el panel se sirve desde el mismo dominio y no los necesita.
    El comodín «*» se descarta siempre (Principio V: CORS solo a dominios propios).
    """
    origenes = []
    for trozo in (valor or "").split(","):
        origen = trozo.strip().rstrip("/")
        if origen and origen != "*" and origen not in origenes:
            origenes.append(origen)
    return origenes


# CORS restringido (spec 001 del ecosistema, T059). Sin allow_credentials: el panel usa su
# cookie en el mismo dominio y la API de administración va con cabecera, no con cookies cruzadas.
app.add_middleware(
    CORSMiddleware,
    allow_origins=origenes_cors(os.getenv("CORS_ORIGINS")),
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Key", "Authorization"],
)

# CSRF desde un subdominio hermano (revisión de seguridad, 2026-10-06). CORS no lo para: un
# formulario o un `fetch` sin lectura de respuesta desde otro subdominio de centauroads.com es del
# MISMO SITIO, así que el navegador le pone la cookie del panel y la petición llega con sesión.
# Lo que sí delata al navegador es `Origin`, que lo manda en todo POST/PUT/PATCH/DELETE. Sin él
# —curl, scripts con X-Admin-Key, de servidor a servidor— no hay cookie de un tercero que robar,
# y pasan como siempre.
_METODOS_QUE_ESCRIBEN = {"POST", "PUT", "PATCH", "DELETE"}
_ORIGENES_PERMITIDOS = {o.lower() for o in origenes_cors(os.getenv("CORS_ORIGINS"))}


def _origen_ajeno(request: Request) -> bool:
    origen = request.headers.get("origin")
    if origen is None:
        # Un navegador que no mandó Origin pero sí dice que viene de otro sitio (o de un
        # subdominio hermano, «same-site») tampoco pasa. Ninguno de los nuestros lo hace.
        return request.headers.get("sec-fetch-site") in ("cross-site", "same-site")
    origen = origen.strip().rstrip("/").lower()
    propio = (request.headers.get("host") or "").lower()
    return urlparse(origen).netloc != propio and origen not in _ORIGENES_PERMITIDOS


@app.middleware("http")
async def solo_desde_el_propio_origen(request: Request, call_next):
    if (request.method in _METODOS_QUE_ESCRIBEN and request.url.path.startswith("/api/")
            and _origen_ajeno(request)):
        logging.getLogger("centaurads").warning(
            "%s %s rechazada: origen %r", request.method, request.url.path,
            request.headers.get("origin") or request.headers.get("sec-fetch-site"))
        return JSONResponse({"detail": "Origen no permitido"}, status_code=403)
    return await call_next(request)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ---------------------------------------------------------------------------
# Identidad del panel (001) y entregas a medida (002)
#   Se montan aqui, y no al final, para que quede claro que sus rutas existen antes que el
#   catch-all "/{slug}". No colisionan -las suyas tienen dos segmentos- pero el orden en el
#   fichero es lo que lo cuenta a quien lo lea.
# ---------------------------------------------------------------------------
from .auth.rutas import router as router_auth, asegura_bootstrap  # noqa: E402
from .auth.equipo import router as router_equipo  # noqa: E402
from .mails.entregas import router as router_entregas  # noqa: E402
from .mails.catalogo import router as router_catalogo  # noqa: E402
from .mails.catalogo.siembra import siembra as siembra_catalogo  # noqa: E402
from .mails.textos import router as router_textos  # noqa: E402

app.include_router(router_auth)
app.include_router(router_equipo)
app.include_router(router_entregas)
app.include_router(router_catalogo)
app.include_router(router_textos)

# Primero se entra, luego se usa la herramienta. El compositor es un fichero estatico y se
# abria sin preguntar quien eras: solo al pulsar algo que hablaba con el servidor salia
# "Hay que entrar al panel", que es el orden al reves. Sin sesion, a la pantalla de entrada,
# que despues devuelve aqui. Basta la firma de la cookie: la pagina no trae datos, y cada
# llamada al servidor vuelve a comprobar a la persona (y si sigue activa).
# Las imagenes de /static siguen publicas: las cargan los correos de los clientes.
from urllib.parse import quote  # noqa: E402
from .auth import sesion as _sesion  # noqa: E402
from .auth.rutas import COMPOSITOR as _COMPOSITOR  # noqa: E402


@app.middleware("http")
async def entrar_antes_del_compositor(request: Request, call_next):
    if request.url.path != _COMPOSITOR:
        return await call_next(request)
    if not _sesion.leer(request.cookies.get(_sesion.COOKIE)):
        respuesta = RedirectResponse(url="/panel/entrar?destino=" + quote(_COMPOSITOR, safe=""),
                                     status_code=307)
    else:
        respuesta = await call_next(request)
    # Sin esto el navegador guarda la pagina y, tras salir, la sigue abriendo de su cache sin
    # preguntar al servidor: la puerta existia pero nadie llamaba a ella. Se vio probandolo.
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


# Definido el ultimo para quedar por fuera de todos: tambien cubre las redirecciones y los 403.
@app.middleware("http")
async def cabeceras_de_seguridad(request: Request, call_next):
    """
    Que ningun otro sitio meta estas paginas en un marco (clickjacking): un sitio ajeno podia cargar
    el panel invisible encima del suyo y hacer que alguien con sesion pulsara donde no queria. El
    propio sitio si puede (SAMEORIGIN): la vista previa del compositor es un marco suyo.
    """
    respuesta = await call_next(request)
    respuesta.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    respuesta.headers.setdefault("Content-Security-Policy", "frame-ancestors 'self'")
    respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
    respuesta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return respuesta

# Con la lista de autorizados vacia no entra nadie, ni siquiera para anadir al primero.
# PANEL_BOOTSTRAP asegura esos correos como administradores. Es configuracion, no un secreto.
# `asegura_bootstrap` ya registra por su cuenta a quien da de alta. Aqui no se vuelve a
# registrar: el logger de este modulo se define MAS ABAJO, y usarlo desde aqui hacia que la
# aplicacion no arrancara -NameError- en cuanto la variable tuviera algo. Las pruebas no lo
# cogian porque no la ponen; lo cogio levantar la aplicacion de verdad.
with SessionLocal() as _db:
    asegura_bootstrap(_db)
    # El catalogo de lineas (003) nace igual que el de serie, y solo con la base vacia.
    siembra_catalogo(_db)

# ---------------------------------------------------------------------------
# Autenticación de administración
#   - ADMIN_KEY: clave operativa del panel. Origen: data/admin.key (persistente) > variable ADMIN_KEY >
#     si no hay ninguna, se genera una aleatoria al arrancar y se guarda en data/admin.key (permisos 600).
#     El log solo dice DÓNDE quedó guardada: la clave nunca se escribe en el log.
#   - SUPERADMIN_USER / SUPERADMIN_PASS: solo por variables de entorno (nunca en el código). Si faltan, los
#     endpoints de superadmin responden 503.
#   - La clave viaja SOLO en la cabecera X-Admin-Key. `?admin_key=` se retiró (T075/T076): quedaba en los
#     logs de acceso y en el historial del navegador, y ni el panel ni los scripts del repo lo usaban.
# ---------------------------------------------------------------------------
log = logging.getLogger("centaurads")
KEY_FILE = os.getenv("ADMIN_KEY_FILE", "data/admin.key")
SUPERADMIN_USER = os.getenv("SUPERADMIN_USER", "").strip()
SUPERADMIN_PASS = os.getenv("SUPERADMIN_PASS", "").strip()

def get_admin_password():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            pwd = f.read().strip()
            if pwd:
                return pwd
    env_key = os.getenv("ADMIN_KEY", "").strip()
    if env_key:
        return env_key
    generated = secrets.token_urlsafe(24)
    set_admin_password(generated)
    log.warning("ADMIN_KEY no configurada: se generó una clave aleatoria y se guardó en %s "
                "(léela de ese fichero; no se escribe en el log).", KEY_FILE)
    return generated

def set_admin_password(new_pass: str):
    os.makedirs(os.path.dirname(KEY_FILE) or ".", exist_ok=True)
    # Se crea ya con 0600, sin ventana en la que otro usuario pueda leerla, y se fuerza con chmod por
    # si el fichero existía antes con permisos más abiertos (os.open no los cambia en ese caso).
    fd = os.open(KEY_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(new_pass.strip())
    os.chmod(KEY_FILE, 0o600)

def verify_admin(admin_key: Optional[str]):
    if not admin_key or not secrets.compare_digest(admin_key, get_admin_password()):
        raise HTTPException(status_code=401, detail="Clave de administración inválida")

def require_admin(x_admin_key: Optional[str] = Header(None, alias="X-Admin-Key")):
    verify_admin(x_admin_key)

def check_superadmin(user: str, password: str):
    # La comprobacion vive en app/auth/superadmin.py: la usan tambien las rutas del panel, y dos
    # copias de lo mismo acaban divergiendo justo en el detalle que importa (compare_digest).
    superadmin.verifica(user, password)

# Resolver la clave al arrancar: si no existe, se genera y se avisa por log una sola vez.
get_admin_password()

class SuperAdminLogin(BaseModel):
    user: str
    password: str

class SuperAdminChange(BaseModel):
    user: str
    password: str
    new_password: str

@app.post("/api/superadmin/login")
def superadmin_login(payload: SuperAdminLogin):
    check_superadmin(payload.user, payload.password)
    return {"status": "ok", "current_password": get_admin_password()}

@app.post("/api/superadmin/change")
def superadmin_change(payload: SuperAdminChange):
    check_superadmin(payload.user, payload.password)
    if not payload.new_password.strip():
        raise HTTPException(status_code=400, detail="La nueva clave no puede estar vacía")
    set_admin_password(payload.new_password)
    return {"status": "ok", "message": "Contraseña actualizada"}

# ---------------------------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------------------------
@app.get("/health", response_class=JSONResponse, include_in_schema=False)
async def health():
    return {"status": "ok", "service": "centaurads-links", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# PANEL DE ADMINISTRACIÓN (HTML)
# ---------------------------------------------------------------------------
@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})


# ---------------------------------------------------------------------------
# API — CRUD de enlaces
# ---------------------------------------------------------------------------

@app.get("/api/links", response_model=list[schemas.LinkOut])
async def list_links(
    _auth: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    links = db.query(models.Link).order_by(models.Link.created_at.desc()).all()
    return links


@app.post("/api/links", response_model=schemas.LinkOut)
async def create_link(
    payload: schemas.LinkCreate,
    _auth: None = Depends(require_admin),
    db: Session = Depends(get_db),
):

    # Verificar slug único
    exists_slug = db.query(models.Link).filter(models.Link.slug == payload.slug).first()
    if exists_slug:
        raise HTTPException(status_code=409, detail=f"El slug '{payload.slug}' ya existe")

    # Verificar URL destino único (prohibición de repetidos)
    exists_url = db.query(models.Link).filter(models.Link.target_url == str(payload.target_url)).first()
    if exists_url:
        raise HTTPException(
            status_code=409, 
            detail=f"Prohibido: Este link ya fue acortado bajo el slug '/{exists_url.slug}'. Debes eliminarlo antes de crear uno nuevo."
        )

    # Validar slug limpio
    import re
    if not re.match(r'^[a-z0-9]([a-z0-9\-]*[a-z0-9])?$', payload.slug):
        raise HTTPException(
            status_code=422,
            detail="El slug solo puede contener letras minúsculas, números y guiones"
        )

    reserved = {"admin", "api", "static", "health", "favicon.ico"}
    if payload.slug in reserved:
        raise HTTPException(status_code=422, detail="Slug reservado por el sistema")

    link = models.Link(
        slug=payload.slug,
        target_url=str(payload.target_url),
        name=payload.name,
        description=payload.description,
        category=payload.category,
    )
    db.add(link)
    db.commit()
    db.refresh(link)
    return link


@app.put("/api/links/{link_id}", response_model=schemas.LinkOut)
async def update_link(
    link_id: int,
    payload: schemas.LinkUpdate,
    _auth: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    link = db.query(models.Link).filter(models.Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")

    if payload.target_url is not None:
        link.target_url = str(payload.target_url)
    if payload.name is not None:
        link.name = payload.name
    if payload.description is not None:
        link.description = payload.description
    if payload.category is not None:
        link.category = payload.category
    if payload.is_active is not None:
        link.is_active = payload.is_active

    db.commit()
    db.refresh(link)
    return link


@app.delete("/api/links/{link_id}")
async def delete_link(
    link_id: int,
    _auth: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    link = db.query(models.Link).filter(models.Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")

    # Borrar clics asociados
    db.query(models.Click).filter(models.Click.link_id == link_id).delete()
    db.delete(link)
    db.commit()
    return {"detail": "Enlace eliminado", "id": link_id}


@app.get("/api/links/{link_id}/stats", response_model=schemas.LinkStats)
async def link_stats(
    link_id: int,
    _auth: None = Depends(require_admin),
    db: Session = Depends(get_db),
):
    link = db.query(models.Link).filter(models.Link.id == link_id).first()
    if not link:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")

    clicks = db.query(models.Click).filter(models.Click.link_id == link_id).all()
    unique_clicks = len(set(c.ip for c in clicks if c.ip and c.ip != "unknown"))
    
    deliveries = db.query(models.Delivery).filter(models.Delivery.link_id == link_id).count()
    ctr = round((float(unique_clicks) / float(deliveries) * 100.0), 2) if deliveries > 0 else 0.0

    return schemas.LinkStats(
        link=link,
        total_clicks=len(clicks),
        unique_clicks=unique_clicks,
        deliveries_count=deliveries,
        ctr=round(ctr, 2),
        recent_clicks=[
            schemas.ClickOut(
                id=c.id,
                ip=c.ip,
                user_agent=c.user_agent,
                referer=c.referer,
                clicked_at=c.clicked_at,
            )
            for c in sorted(clicks, key=lambda x: x.clicked_at, reverse=True)[:50]
        ],
    )

@app.post("/api/links/{slug}/deliver")
@app.get("/api/links/{slug}/deliver")
async def register_delivery(
    slug: str,
    request: Request,
    _auth: None = Depends(require_admin),
    channel: str = Query("facebook"),
    db: Session = Depends(get_db),
):
    link = db.query(models.Link).filter(models.Link.slug == slug).first()
    if not link:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")
    
    delivery = models.Delivery(
        link_id=link.id,
        channel=channel
    )
    db.add(delivery)
    db.commit()
    return {"status": "ok", "detail": "Entrega registrada exitosamente", "channel": channel}


# ---------------------------------------------------------------------------
# PORTADA / LANDING PAGE
# ---------------------------------------------------------------------------
# El mismo servicio responde a dos nombres. `links.` es el del acortador y su portada no cambia: los
# enlaces cortos que ya circulan dependen de el. `mails.` es la direccion que se da al equipo, y
# quien la escribe a secas va a la pantalla de entrada.
NOMBRE_DEL_PANEL = "mails."


@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
    if (request.url.hostname or "").startswith(NOMBRE_DEL_PANEL):
        return RedirectResponse(url="/panel/entrar", status_code=307)
    return templates.TemplateResponse("index.html", {"request": request})

# ---------------------------------------------------------------------------
# REDIRECT PÚBLICO — Catch-all (DEBE ser la ÚLTIMA ruta)
# ---------------------------------------------------------------------------
@app.get("/{slug}", response_class=RedirectResponse)
async def redirect_to_target(slug: str, request: Request, db: Session = Depends(get_db)):
    """Redirige un slug corto a la URL destino (Canva, etc.)"""

    link = db.query(models.Link).filter(
        models.Link.slug == slug,
        models.Link.is_active == True
    ).first()

    if not link:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")

    # Registrar clic
    # Extraer la IP real a traves del proxy Traefik o usar la Conexion Directa
    real_ip = request.headers.get("X-Forwarded-For")
    if real_ip:
        real_ip = real_ip.split(",")[0].strip()
    else:
        real_ip = request.headers.get("X-Real-IP")
    if not real_ip:
        real_ip = request.client.host if request.client else "unknown"

    click = models.Click(
        link_id=link.id,
        ip=real_ip,
        user_agent=request.headers.get("user-agent", ""),
        referer=request.headers.get("referer", ""),
    )
    db.add(click)

    # Actualizar contador
    link.click_count += 1
    link.last_clicked_at = datetime.now(timezone.utc)
    db.commit()

    # Devolver redirect bruto 307 en lugar de puente intersticial para evitar bloqueos en Google Ads
    return RedirectResponse(url=link.target_url, status_code=307)
