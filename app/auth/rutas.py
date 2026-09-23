"""
Entrar al panel, salir, y administrar quién puede entrar.

Aquí vive **la puerta**: la decisión de si una persona pasa o no. La identidad la da Google
(`google.py`) o una contraseña propia (`local.py`); la autorización la da esta lista.

## La regla, en una frase

Entra quien tenga una fila **activa** en `panel_users`. Ni el dominio del correo ni tener cuenta
de Google conceden nada por sí solos (FR-119).

Tres consecuencias que no son detalles:

- **Sacar a alguien de la lista es un paso obligatorio de su baja.** Su cuenta de Gmail sigue
  existiendo fuera de la empresa; lo único que le corta el paso es esta tabla (FR-120).
- **Nunca se dice si un correo está en la lista.** Un rechazo dice lo mismo tanto si la cuenta no
  existe como si existe y está desactivada. Contarlo convertiría la pantalla de entrada en una
  forma de averiguar quién trabaja aquí.
- **Retirar el acceso es `activo = False`, nunca borrar la fila.** La bitácora tiene que seguir
  señalando a alguien.

## El arranque en frío

Con la tabla vacía no entra nadie, ni siquiera para añadir al primero. `PANEL_BOOTSTRAP` —una
lista de correos separados por comas, por variable de entorno— asegura esas filas como
administradores al arrancar. Es configuración, no un secreto, y por eso puede ir en el entorno
sin violar el principio V.
"""

import logging
import os
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from .. import models
from . import google, local, sesion
from .dependencias import usuario_actual, solo_admin

log = logging.getLogger("centaurads.auth")
router = APIRouter()

# Un rechazo dice siempre esto, pase lo que pase. Ver la nota de arriba.
_RECHAZO = "Esa cuenta no tiene acceso al panel"


def _autorizado(db: Session, email: str) -> Optional[models.PanelUser]:
    """La fila activa de esa persona, o None. Aquí está toda la puerta."""
    return db.query(models.PanelUser).filter(
        models.PanelUser.email == (email or "").strip().lower(),
        models.PanelUser.activo.is_(True),
    ).first()


def asegura_bootstrap(db: Session) -> int:
    """
    Asegura como administradores los correos de `PANEL_BOOTSTRAP`. Devuelve cuántos creó.

    Idempotente: a quien ya está, no lo toca. Tampoco reactiva a nadie que se haya dado de baja
    a propósito — si alguien sale de la empresa y además está en la variable, la baja manda, y lo
    que hay que corregir es la variable.
    """
    crudo = os.getenv("PANEL_BOOTSTRAP", "")
    creados = 0
    for email in [e.strip().lower() for e in crudo.split(",") if e.strip()]:
        if db.query(models.PanelUser).filter(models.PanelUser.email == email).first():
            continue
        db.add(models.PanelUser(email=email, nombre=email.split("@")[0], rol="admin",
                                activo=True))
        creados += 1
        log.info("PANEL_BOOTSTRAP: se da de alta a %s como administrador", email)
    if creados:
        db.commit()
    return creados


# ---------------------------------------------------------------------------
# Entrar y salir
# ---------------------------------------------------------------------------

class EntradaGoogle(BaseModel):
    credential: str = Field(min_length=1)


class EntradaLocal(BaseModel):
    email: str = Field(min_length=1, max_length=200)
    password: str = Field(min_length=1)


def _entra(db: Session, usuario: models.PanelUser) -> JSONResponse:
    usuario.last_login_at = datetime.now(timezone.utc)
    db.commit()
    respuesta = JSONResponse({"email": usuario.email, "nombre": usuario.nombre,
                              "rol": usuario.rol})
    sesion.poner(respuesta, usuario.id, usuario.email)
    log.info("entra al panel: %s", usuario.email)
    return respuesta


@router.post("/api/auth/google")
def entrar_con_google(datos: EntradaGoogle, db: Session = Depends(get_db)):
    try:
        quien = google.verificar_identidad(datos.credential)
    except google.IdentidadRechazada as e:
        # Aquí sí se puede ser concreto: el problema es el identificador, no la persona.
        raise HTTPException(status_code=401, detail=str(e))

    usuario = _autorizado(db, quien["email"])
    if not usuario:
        log.warning("entrada rechazada: %s no está en la lista de autorizados", quien["email"])
        raise HTTPException(status_code=403, detail=_RECHAZO)

    # El nombre que da Google es mejor que el que se tecleó al darla de alta.
    if quien.get("nombre") and usuario.nombre != quien["nombre"]:
        usuario.nombre = quien["nombre"]
    return _entra(db, usuario)


@router.post("/api/auth/local")
def entrar_con_contrasena(datos: EntradaLocal, db: Session = Depends(get_db)):
    """La excepción para quien no tenga cuenta de Google (FR-001b)."""
    usuario = _autorizado(db, datos.email)
    if not usuario or not usuario.password_hash:
        raise HTTPException(status_code=403, detail=_RECHAZO)
    if not local.verificar(usuario.password_hash, datos.password):
        log.warning("contraseña incorrecta para %s", usuario.email)
        raise HTTPException(status_code=403, detail=_RECHAZO)
    return _entra(db, usuario)


@router.post("/api/auth/salir")
def salir():
    respuesta = JSONResponse({"ok": True})
    sesion.quitar(respuesta)
    return respuesta


@router.get("/api/auth/yo")
def quien_soy(usuario: models.PanelUser = Depends(usuario_actual)):
    return {"email": usuario.email, "nombre": usuario.nombre, "rol": usuario.rol}


# ---------------------------------------------------------------------------
# La lista de autorizados
# ---------------------------------------------------------------------------

class UsuarioEntrada(BaseModel):
    email: str = Field(min_length=3, max_length=200)
    nombre: str = Field(default="", max_length=200)
    rol: str = Field(default="comercial")


@router.get("/api/panel/usuarios")
def listar_usuarios(db: Session = Depends(get_db),
                    _: models.PanelUser = Depends(solo_admin)) -> List[dict]:
    return [{"id": u.id, "email": u.email, "nombre": u.nombre, "rol": u.rol,
             "activo": u.activo,
             "ultima_entrada": u.last_login_at.isoformat() if u.last_login_at else None}
            for u in db.query(models.PanelUser).order_by(models.PanelUser.email).all()]


@router.post("/api/panel/usuarios")
def alta_usuario(datos: UsuarioEntrada, db: Session = Depends(get_db),
                 _: models.PanelUser = Depends(solo_admin)):
    email = datos.email.strip().lower()
    if datos.rol not in ("admin", "comercial"):
        raise HTTPException(status_code=400, detail="El rol solo puede ser admin o comercial")
    existente = db.query(models.PanelUser).filter(models.PanelUser.email == email).first()
    if existente:
        # Volver a dar de alta a quien ya estuvo es reactivar su fila, no crear otra: así su
        # historial sigue apuntando a la misma persona.
        existente.activo = True
        existente.rol = datos.rol
        if datos.nombre:
            existente.nombre = datos.nombre
        db.commit()
        return {"id": existente.id, "email": existente.email, "reactivado": True}
    usuario = models.PanelUser(email=email, nombre=datos.nombre or email.split("@")[0],
                               rol=datos.rol, activo=True)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return {"id": usuario.id, "email": usuario.email, "reactivado": False}


@router.delete("/api/panel/usuarios/{usuario_id}")
def baja_usuario(usuario_id: int, db: Session = Depends(get_db),
                 quien: models.PanelUser = Depends(solo_admin)):
    """
    Retira el acceso. **No borra la fila**: la bitácora tiene que seguir señalando a alguien.
    """
    usuario = db.query(models.PanelUser).filter(models.PanelUser.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="No encontrado")
    if usuario.id == quien.id:
        raise HTTPException(status_code=400,
                            detail="No puedes retirarte el acceso a ti mismo")
    usuario.activo = False
    db.commit()
    log.info("%s retira el acceso de %s", quien.email, usuario.email)
    return {"ok": True, "email": usuario.email}


# ---------------------------------------------------------------------------
# La pantalla de entrada
# ---------------------------------------------------------------------------

_ENTRADA = """<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Entrar · Centauro ADS</title>
{script_google}
<style>
  :root {{ color-scheme: dark; }}
  body {{ margin:0; min-height:100vh; display:flex; align-items:center; justify-content:center;
         background:#14111A; color:#EEEDF2;
         font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }}
  .caja {{ width:100%; max-width:380px; padding:32px 24px; }}
  .marca {{ font-size:11px; font-weight:800; letter-spacing:.24em; text-transform:uppercase;
           color:#B98FC7; }}
  h1 {{ font-size:26px; line-height:1.2; letter-spacing:-.02em; margin:12px 0 8px; }}
  p.sub {{ color:#9A93A6; margin:0 0 28px; font-size:14px; }}
  .sep {{ display:flex; align-items:center; gap:12px; color:#8C8598; font-size:12px; margin:26px 0; }}
  .sep::before, .sep::after {{ content:""; flex:1; height:1px; background:#2E2838; }}
  label {{ display:block; font-size:12px; color:#A9A2B5; margin:0 0 4px; }}
  input {{ width:100%; box-sizing:border-box; background:#1E1A26; border:1px solid #2E2838;
          color:#EEEDF2; border-radius:8px; padding:11px 12px; font-size:14px; margin:0 0 14px; }}
  input:focus {{ outline:2px solid #B98FC7; outline-offset:1px; border-color:#B98FC7; }}
  button {{ width:100%; background:#85439A; color:#fff; border:0; border-radius:8px;
           padding:13px; font-size:14px; font-weight:800; cursor:pointer; }}
  button:hover {{ background:#9A50B2; }}
  button:focus-visible {{ outline:2px solid #EEEDF2; outline-offset:2px; }}
  .aviso {{ margin:18px 0 0; padding:11px 13px; border-radius:8px; background:#3A1A22;
           border:1px solid #6B2B38; color:#F4C7CF; font-size:13px; }}
  .pie {{ margin-top:30px; font-size:12px; color:#8C8598; }}
</style>
</head><body><main class="caja">
  <div class="marca">Centauro ADS</div>
  <h1>Entrar al panel</h1>
  <p class="sub">Con la cuenta que te hayan autorizado.</p>

  {bloque_google}

  <form id="local" autocomplete="on">
    <label for="email">Correo</label>
    <input id="email" name="email" type="email" required autocomplete="username">
    <label for="clave">Contraseña</label>
    <input id="clave" name="password" type="password" required autocomplete="current-password">
    <button type="submit">Entrar</button>
  </form>

  <div class="aviso" id="aviso" role="alert" hidden></div>
  <p class="pie">Si no puedes entrar, pide que añadan tu correo a la lista del panel.</p>
</main>
<script>
  var aviso = document.getElementById('aviso');
  function falla(texto) {{ aviso.textContent = texto; aviso.hidden = false; }}
  function entra(ruta, cuerpo) {{
    aviso.hidden = true;
    return fetch(ruta, {{ method: 'POST', headers: {{ 'Content-Type': 'application/json' }},
                         body: JSON.stringify(cuerpo) }})
      .then(function (r) {{ return r.json().then(function (d) {{
        if (!r.ok) throw new Error(d.detail || 'No se pudo entrar');
        location.href = '{destino}';
      }}); }})
      .catch(function (e) {{ falla(e.message); }});
  }}
  document.getElementById('local').addEventListener('submit', function (ev) {{
    ev.preventDefault();
    entra('/api/auth/local', {{ email: document.getElementById('email').value,
                               password: document.getElementById('clave').value }});
  }});
  window.entrarConGoogle = function (respuesta) {{
    entra('/api/auth/google', {{ credential: respuesta.credential }});
  }};
</script>
</body></html>"""

_BLOQUE_GOOGLE = """<div id="g_id_onload" data-client_id="{client_id}"
     data-callback="entrarConGoogle" data-auto_prompt="false"></div>
<div class="g_id_signin" data-type="standard" data-theme="filled_black"
     data-text="signin_with" data-shape="rectangular" data-width="332"></div>
<div class="sep">o con tu contraseña</div>"""


@router.get("/panel/entrar", response_class=HTMLResponse)
def pantalla_de_entrada(request: Request, destino: str = "/admin/entregas"):
    """
    La pantalla de entrada. Ofrece Google solo si está configurado: enseñar un botón que fallaría
    al pulsarlo es peor que no enseñarlo.

    `destino` se limita a rutas internas. Sin esa comprobación, un enlace preparado podría llevar
    a alguien a entrar y acabar en otro sitio.
    """
    if not destino.startswith("/") or destino.startswith("//"):
        destino = "/admin/entregas"

    if google.esta_configurado():
        cid = os.getenv("GOOGLE_CLIENT_ID", "").strip()
        bloque = _BLOQUE_GOOGLE.format(client_id=cid)
        script = '<script src="https://accounts.google.com/gsi/client" async defer></script>'
    else:
        bloque, script = "", ""

    return HTMLResponse(_ENTRADA.format(script_google=script, bloque_google=bloque,
                                        destino=destino))


@router.get("/panel/salir")
def salir_y_volver():
    respuesta = RedirectResponse(url="/panel/entrar", status_code=303)
    sesion.quitar(respuesta)
    return respuesta
