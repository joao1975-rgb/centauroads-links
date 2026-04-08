"""
CentauroADS Links — Acortador de URLs corporativo
Proyecto standalone para Easypanel / DigitalOcean
"""

from fastapi import FastAPI, Request, Depends, HTTPException, Form, Query
from fastapi.responses import RedirectResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional
import secrets
import os
from pydantic import BaseModel

from .database import engine, get_db, Base
from . import models, schemas

# ---------------------------------------------------------------------------
# Crear tablas
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="CentauroADS Links",
    description="Acortador de URLs corporativo — Centauro ADS",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# ---------------------------------------------------------------------------
# Clave admin (desde variable de entorno o disco persistente)
# ---------------------------------------------------------------------------
SUPERADMIN_USER = "centauroadss@gmail.com"
SUPERADMIN_PASS = "MERcentads2026!."
KEY_FILE = "data/admin.key"

def get_admin_password():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, "r") as f:
            pwd = f.read().strip()
            if pwd: return pwd
    return os.getenv("ADMIN_KEY", "centauro2026")

def set_admin_password(new_pass: str):
    import os
    os.makedirs(os.path.dirname(KEY_FILE) or ".", exist_ok=True)
    with open(KEY_FILE, "w") as f:
        f.write(new_pass.strip())

def verify_admin(admin_key: str):
    if admin_key != get_admin_password():
        raise HTTPException(status_code=401, detail="Clave de administración inválida")

class SuperAdminLogin(BaseModel):
    user: str
    password: str

class SuperAdminChange(BaseModel):
    user: str
    password: str
    new_password: str

@app.post("/api/superadmin/login")
def superadmin_login(payload: SuperAdminLogin):
    if payload.user == SUPERADMIN_USER and payload.password == SUPERADMIN_PASS:
        return {"status": "ok", "current_password": get_admin_password()}
    raise HTTPException(status_code=401, detail="Credenciales inválidas")

@app.post("/api/superadmin/change")
def superadmin_change(payload: SuperAdminChange):
    if payload.user == SUPERADMIN_USER and payload.password == SUPERADMIN_PASS:
        if not payload.new_password.strip():
            raise HTTPException(status_code=400, detail="La nueva clave no puede estar vacía")
        set_admin_password(payload.new_password)
        return {"status": "ok", "message": "Contraseña actualizada"}
    raise HTTPException(status_code=401, detail="Credenciales inválidas")

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
    admin_key: str = Query(...),
    db: Session = Depends(get_db),
):
    verify_admin(admin_key)
    links = db.query(models.Link).order_by(models.Link.created_at.desc()).all()
    return links


@app.post("/api/links", response_model=schemas.LinkOut)
async def create_link(
    payload: schemas.LinkCreate,
    admin_key: str = Query(...),
    db: Session = Depends(get_db),
):
    verify_admin(admin_key)

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
    admin_key: str = Query(...),
    db: Session = Depends(get_db),
):
    verify_admin(admin_key)
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
    admin_key: str = Query(...),
    db: Session = Depends(get_db),
):
    verify_admin(admin_key)
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
    admin_key: str = Query(...),
    db: Session = Depends(get_db),
):
    verify_admin(admin_key)
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
    admin_key: str = Query(...),
    channel: str = Query("facebook"),
    db: Session = Depends(get_db),
):
    verify_admin(admin_key)
    link = db.query(models.Link).filter(models.Link.slug == slug).first()
    if not link:
        raise HTTPException(status_code=404, detail="Enlace no encontrado")
    
    delivery = models.Delivery(
        link_id=link.id,
        channel=channel
    )
    db.add(delivery)
    db.commit()
    return {"status": "ok", "detail": "Entrega registrada exitosamente", "channel": payload.channel}


# ---------------------------------------------------------------------------
# PORTADA / LANDING PAGE
# ---------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def index_page(request: Request):
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

    # Devolver puente intersticial silencioso en lugar de redirect bruto 307
    return templates.TemplateResponse("redirect.html", {"request": request, "target_url": link.target_url})
