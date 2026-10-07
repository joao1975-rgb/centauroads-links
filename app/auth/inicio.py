"""
El Centro de control (/panel/inicio, especificación 006).

A donde llegan el superadmin y los administradores al entrar: tres salidas —el compositor, la
administración del contenido (líneas de negocio y textos de los perfiles) y los accesos (el equipo)—.
Un comercial solo usa el compositor, así que si llega aquí se le lleva allí.

La página no lleva datos: pide quién ha entrado y lo escribe como texto.
"""

from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import models
from .dependencias import usuario_actual_opcional
from .rutas import COMPOSITOR

router = APIRouter()

PANTALLA = "/panel/inicio"


@router.get(PANTALLA)
def centro_de_control(usuario: Optional[models.PanelUser] = Depends(usuario_actual_opcional)):
    if usuario is None:
        respuesta = RedirectResponse(url="/panel/entrar?destino=" + quote(PANTALLA, safe=""),
                                     status_code=307)
    elif usuario.rol != "admin":
        respuesta = RedirectResponse(url=COMPOSITOR, status_code=307)
    else:
        respuesta = HTMLResponse(_PAGINA)
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


_PAGINA = """<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Centro de control · Centauro ADS</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin:0; background:#14111A; color:#EEEDF2;
         font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  .caja { max-width:880px; margin:0 auto; padding:28px 16px 64px; }
  .arriba { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
  .marca { font-size:11px; font-weight:800; letter-spacing:.24em; text-transform:uppercase; color:#B98FC7; }
  .nav { display:flex; gap:16px; font-size:13px; }
  .nav a { color:#C9A3D8; text-underline-offset:3px; }
  h1 { font-size:30px; line-height:1.2; letter-spacing:-.02em; margin:14px 0 6px; }
  p.sub { color:#9A93A6; margin:0 0 30px; font-size:14px; min-height:1.6em; }
  .etq { font-size:11px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; padding:2px 8px;
         border-radius:999px; background:#4A2E12; color:#F7C08A; margin-left:6px; }
  .salidas { display:grid; grid-template-columns:repeat(auto-fit, minmax(240px, 1fr)); gap:16px; }
  .salida { display:flex; flex-direction:column; gap:10px; padding:22px 20px; border:1px solid #2E2838;
            border-radius:12px; background:#1A1622; }
  .salida.principal { border-color:#85439A; background:linear-gradient(180deg, #241830, #1A1622); }
  .salida h2 { font-size:19px; margin:0; }
  .salida p { color:#A9A2B5; font-size:13px; margin:0; flex:1; }
  .salida a.ir { display:block; text-align:center; text-decoration:none; font-weight:800; font-size:14px;
                 padding:11px 14px; border-radius:8px; background:#241F2E; color:#EEEDF2; }
  .salida a.ir:hover { background:#2E2838; }
  .salida.principal a.ir { background:#85439A; color:#fff; }
  .salida.principal a.ir:hover { background:#9A50B2; }
  a:focus-visible { outline:2px solid #EEEDF2; outline-offset:2px; }
</style>
</head><body><main class="caja">
  <div class="arriba">
    <div class="marca">Centauro ADS</div>
    <nav class="nav" aria-label="Panel">
      <a href="/panel/salir">Salir</a>
    </nav>
  </div>
  <h1>Centro de control</h1>
  <p class="sub" id="quien"></p>

  <div class="salidas">
    <section class="salida principal" aria-labelledby="t-compositor">
      <h2 id="t-compositor">Compositor</h2>
      <p>Armar los correos de servicios y las propuestas personalizadas, y copiarlos para Gmail o WhatsApp.</p>
      <a class="ir" href="/static/email/compositor.html">Abrir el compositor</a>
    </section>
    <section class="salida" aria-labelledby="t-admin">
      <h2 id="t-admin">Administración</h2>
      <p>Lo que ofrecen y dicen los correos de todo el equipo.</p>
      <a class="ir" href="/panel/lineas">Líneas de negocio</a>
      <a class="ir" href="/panel/textos">Textos de los perfiles</a>
    </section>
    <section class="salida" aria-labelledby="t-accesos">
      <h2 id="t-accesos">Accesos</h2>
      <p>Quién entra al panel: crear cuentas, cambiar roles y poner contraseñas.</p>
      <a class="ir" href="/panel/equipo">Equipo</a>
    </section>
  </div>
</main>
<script>
(function () {
  fetch('/api/auth/yo').then(function (r) { return r.ok ? r.json() : null; }).then(function (d) {
    if (!d) return;
    var quien = document.getElementById('quien');
    quien.textContent = 'Has entrado como ' + d.email;
    if (d.superadmin) {
      var etq = document.createElement('span');
      etq.className = 'etq'; etq.textContent = 'Superadmin';
      quien.appendChild(etq);
    }
  }).catch(function () {});
})();
</script>
</body></html>"""
