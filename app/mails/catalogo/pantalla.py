"""
La pantalla «Líneas de negocio» (/panel/lineas, especificación 003).

Es la cara de la API del catálogo, con el mismo patrón que la del equipo: la página no lleva datos,
los pide el navegador y los escribe como TEXTO (los nombres los teclea gente). Las reglas —quién
da de alta, qué se valida— siguen en la API.

Un comercial la ve en solo lectura: le sirve para saber qué líneas hay y en qué plantillas salen.
"""

from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from ... import models
from ...auth.dependencias import usuario_actual_opcional

router = APIRouter()

PANTALLA = "/panel/lineas"


@router.get(PANTALLA)
def pantalla_de_lineas(usuario: Optional[models.PanelUser] = Depends(usuario_actual_opcional)):
    if usuario is None:
        respuesta = RedirectResponse(url="/panel/entrar?destino=" + quote(PANTALLA, safe=""),
                                     status_code=307)
    else:
        respuesta = HTMLResponse(_PAGINA)
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


_PLANTILLAS = [("A", "Cartelera"), ("B", "Catálogo"), ("C", "Nota"), ("D", "Cartelera móvil"),
               ("E", "Inventario"), ("F", "Guía"), ("G", "Phygital"), ("H", "Personalizada")]

_CASILLAS = "\n".join(
    '        <label class="casilla"><input type="checkbox" name="plantilla" value="%s" checked>'
    '<b>%s</b> %s</label>' % (k, k, n) for k, n in _PLANTILLAS)

_PAGINA = """<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Líneas de negocio · Centauro ADS</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin:0; background:#14111A; color:#EEEDF2;
         font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  .caja { max-width:820px; margin:0 auto; padding:28px 16px 64px; }
  .arriba { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
  .marca { font-size:11px; font-weight:800; letter-spacing:.24em; text-transform:uppercase; color:#B98FC7; }
  .nav { display:flex; gap:16px; font-size:13px; flex-wrap:wrap; }
  .nav a { color:#C9A3D8; text-underline-offset:3px; }
  h1 { font-size:28px; line-height:1.2; letter-spacing:-.02em; margin:14px 0 6px; }
  p.sub { color:#9A93A6; margin:0 0 30px; font-size:14px; max-width:62ch; }
  h2 { font-size:17px; margin:0 0 4px; }
  section { border-top:1px solid #2E2838; padding:26px 0; }
  .nota { color:#9A93A6; font-size:13px; margin:0 0 16px; }
  ul.lista { list-style:none; margin:0; padding:0; }
  .fila { display:grid; grid-template-columns:88px minmax(0,1fr) auto; align-items:center; gap:10px 16px;
          padding:14px 0; border-bottom:1px solid #221E2B; }
  .miniatura { width:88px; height:58px; border-radius:6px; object-fit:cover; background:#1E1A26;
               display:flex; align-items:center; justify-content:center; color:#8C8598; font-size:11px; text-align:center; }
  .quien { min-width:0; }
  .quien b { display:block; font-size:14px; }
  .detalle { display:block; color:#A9A2B5; font-size:13px; overflow-wrap:anywhere; }
  .letras { display:flex; gap:4px; margin-top:6px; flex-wrap:wrap; }
  .letra { font-size:11px; font-weight:800; width:22px; height:22px; border-radius:5px; display:inline-flex;
           align-items:center; justify-content:center; background:#3B2547; color:#E2C6EC; }
  .letra.no { background:transparent; color:#5E5869; border:1px dashed #3A3445; font-weight:600; }
  .etq { font-size:11px; font-weight:700; letter-spacing:.06em; text-transform:uppercase; padding:3px 8px;
         border-radius:999px; background:#3A1A22; color:#F4C7CF; margin-left:8px; }
  .acciones { display:flex; gap:8px; justify-content:flex-end; }
  @media (max-width:560px) { .fila { grid-template-columns:72px minmax(0,1fr); }
    .miniatura { width:72px; height:48px; } .acciones { grid-column:1 / -1; justify-content:flex-start; } }
  label { display:block; font-size:12px; color:#A9A2B5; margin:0 0 4px; }
  input[type=text], input[type=url], input[type=file], select { width:100%; background:#1E1A26; border:1px solid #6B6885;
         color:#EEEDF2; border-radius:8px; padding:11px 12px; font-size:14px; margin:0 0 14px; font-family:inherit; }
  input:focus, select:focus { outline:2px solid #B98FC7; outline-offset:1px; border-color:#B98FC7; }
  .rejilla { display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:0 16px; }
  fieldset { border:1px solid #2E2838; border-radius:10px; padding:12px 14px 6px; margin:0 0 18px; }
  legend { font-size:12px; color:#A9A2B5; padding:0 6px; }
  .casillas { display:grid; grid-template-columns:repeat(auto-fit, minmax(170px, 1fr)); gap:2px 12px; }
  .casilla { display:flex; align-items:center; gap:8px; font-size:13px; color:#D9D5E0; margin:0 0 8px; cursor:pointer; }
  .casilla input { width:18px; height:18px; margin:0; accent-color:#B98FC7; }
  .casilla b { color:#E2C6EC; }
  button { border:0; border-radius:8px; padding:11px 16px; font-size:14px; font-weight:800;
           cursor:pointer; background:#85439A; color:#fff; font-family:inherit; }
  button:hover { background:#9A50B2; }
  button.suave { background:#241F2E; color:#EEEDF2; font-weight:600; padding:8px 12px; font-size:13px; }
  button.suave:hover { background:#2E2838; }
  button:focus-visible, a:focus-visible { outline:2px solid #EEEDF2; outline-offset:2px; }
  button:disabled { opacity:.5; cursor:default; }
  .msg { margin:0 0 16px; padding:11px 13px; border-radius:8px; font-size:13px; }
  .msg.ok { background:#16271F; border:1px solid #2C5A43; color:#BFE8D2; }
  .msg.mal { background:#3A1A22; border:1px solid #6B2B38; color:#F4C7CF; }
  .oculto { position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); }
</style>
</head><body><main class="caja">
  <div class="arriba">
    <div class="marca">Centauro ADS</div>
    <nav class="nav" aria-label="Panel">
      <a href="/static/email/compositor.html">Volver al compositor</a>
      <a href="/panel/equipo">Equipo</a>
      <a href="/panel/salir">Salir</a>
    </nav>
  </div>
  <h1>Líneas de negocio</h1>
  <p class="sub" id="sub">Lo que el compositor ofrece como servicios. Una línea nueva sale en los correos
    del equipo en cuanto se guarda, sin desplegar nada.</p>

  <div class="msg" id="aviso" role="status" aria-live="polite" tabindex="-1" hidden></div>

  <section aria-labelledby="t-lista">
    <h2 id="t-lista">Líneas del catálogo</h2>
    <p class="nota">Las letras son las plantillas en que sale cada una.</p>
    <ul class="lista" id="filas"></ul>
  </section>

  <section id="alta" aria-labelledby="t-alta" hidden>
    <h2 id="t-alta">Añadir una línea</h2>
    <p class="nota">Sale en las plantillas marcadas, para todo el equipo, desde el próximo correo que se arme.</p>
    <form id="f-alta" autocomplete="off">
      <div class="rejilla">
        <div><label for="a-nombre">Nombre</label>
          <input id="a-nombre" type="text" maxlength="120" required></div>
        <div><label for="a-eyebrow">Etiqueta corta (sobre el nombre)</label>
          <input id="a-eyebrow" type="text" maxlength="60"></div>
        <div><label for="a-cobertura">Cobertura o ubicación</label>
          <input id="a-cobertura" type="text" maxlength="200"></div>
        <div><label for="a-nota">Nota (opcional)</label>
          <input id="a-nota" type="text" maxlength="300"></div>
        <div><label for="a-canva">Enlace de la presentación</label>
          <input id="a-canva" type="url" maxlength="500" placeholder="https://"></div>
        <div><label for="a-cta">Texto de su botón (opcional)</label>
          <input id="a-cta" type="text" maxlength="60"></div>
        <div><label for="a-familia">Grupo en la plantilla D</label>
          <select id="a-familia"><option value="">Ninguno · va a «Otros servicios»</option></select></div>
        <div><label for="a-foto">Foto (JPG o PNG, hasta 8 MB)</label>
          <input id="a-foto" type="file" accept="image/jpeg,image/png,image/webp"></div>
        <div><label for="a-alt">Qué se ve en la foto (para quien no ve imágenes)</label>
          <input id="a-alt" type="text" maxlength="200"></div>
      </div>
      <fieldset>
        <legend>Plantillas en que sale</legend>
        <div class="casillas">
""" + _CASILLAS + """
        </div>
      </fieldset>
      <button type="submit">Añadir la línea</button>
    </form>
  </section>
</main>
<script>
(function () {
  var aviso = document.getElementById('aviso');
  var LETRAS = 'ABCDEFGH';
  var esAdmin = false;

  function di(texto, bien) {
    aviso.textContent = texto;
    aviso.className = 'msg ' + (bien ? 'ok' : 'mal');
    aviso.hidden = false;
    aviso.scrollIntoView({ block: 'nearest' });
    aviso.focus({ preventScroll: true });
  }

  function api(metodo, ruta, cuerpo) {
    var op = { method: metodo, headers: {} };
    if (cuerpo instanceof FormData) op.body = cuerpo;
    else if (cuerpo) { op.headers['Content-Type'] = 'application/json'; op.body = JSON.stringify(cuerpo); }
    return fetch(ruta, op).then(function (r) {
      if (r.status === 401) { location.href = '/panel/entrar?destino=%2Fpanel%2Flineas'; throw new Error('Hay que entrar de nuevo'); }
      return r.json().catch(function () { return {}; }).then(function (d) {
        if (!r.ok) throw new Error(d.detail || 'No se pudo completar');
        return d;
      });
    });
  }

  function el(tag, clase, texto) {
    var n = document.createElement(tag);
    if (clase) n.className = clase;
    if (texto !== undefined) n.textContent = texto;
    return n;
  }

  // Las fotos de serie son nombres de archivo junto al compositor; las subidas, rutas /media/...
  function fuenteFoto(img) {
    if (!img) return '';
    return /^(https?:)?\\/\\//.test(img) || img.charAt(0) === '/' ? img : '/static/email/' + img;
  }

  function subeFoto(id, fichero, alt) {
    var datos = new FormData();
    datos.append('fichero', fichero);
    if (alt) datos.append('alt', alt);
    return api('POST', '/api/panel/lineas/' + encodeURIComponent(id) + '/foto', datos);
  }

  function miniatura(l) {
    if (!l.img) return el('div', 'miniatura', 'Sin foto');
    var im = el('img', 'miniatura');
    im.src = fuenteFoto(l.img); im.alt = l.alt || ''; im.width = 88; im.height = 58; im.loading = 'lazy';
    return im;
  }

  function botonFoto(l) {
    var entrada = el('input', 'oculto');
    entrada.type = 'file'; entrada.accept = 'image/jpeg,image/png,image/webp';
    entrada.setAttribute('aria-label', 'Foto para ' + l.nombre);
    var b = el('button', 'suave', l.img ? 'Cambiar foto' : 'Poner foto');
    b.type = 'button';
    b.setAttribute('aria-label', (l.img ? 'Cambiar la foto de ' : 'Poner foto a ') + l.nombre);
    b.addEventListener('click', function () { entrada.click(); });
    entrada.addEventListener('change', function () {
      if (!entrada.files.length) return;
      var alt = l.alt || prompt('Qué se ve en la foto (para quien no ve imágenes):', '');
      if (!alt) { di('Sin texto alternativo no se sube la foto.', false); return; }
      b.disabled = true;
      subeFoto(l.id, entrada.files[0], alt)
        .then(function () { di('Foto guardada: ' + l.nombre, true); carga(); })
        .catch(function (e) { di(e.message, false); b.disabled = false; });
    });
    var caja = el('div', 'acciones');
    caja.appendChild(b); caja.appendChild(entrada);
    return caja;
  }

  function pinta(d) {
    var ul = document.getElementById('filas');
    ul.textContent = '';
    d.lineas.forEach(function (l) {
      var li = el('li', 'fila');
      li.appendChild(miniatura(l));
      var quien = el('div', 'quien');
      var nombre = el('b', null, l.nombre);
      if (l.activa === false) nombre.appendChild(el('span', 'etq', 'Retirada'));
      quien.appendChild(nombre);
      var detalle = [l.eyebrow, l.cobertura].filter(Boolean).join(' · ');
      if (detalle) quien.appendChild(el('span', 'detalle', detalle));
      var letras = el('div', 'letras');
      letras.setAttribute('aria-label', l.plantillas ? 'Sale en las plantillas ' + l.plantillas.split('').join(', ') : 'No sale en ninguna plantilla');
      LETRAS.split('').forEach(function (k) {
        var dentro = l.plantillas.indexOf(k) >= 0;
        var s = el('span', 'letra' + (dentro ? '' : ' no'), k);
        s.setAttribute('aria-hidden', 'true');
        letras.appendChild(s);
      });
      quien.appendChild(letras);
      li.appendChild(quien);
      // Solo las fotos que se subieron aqui: las de serie van con su carrusel generado.
      if (esAdmin && (!l.img || l.img.charAt(0) === '/')) li.appendChild(botonFoto(l));
      ul.appendChild(li);
    });
    var sel = document.getElementById('a-familia');
    while (sel.options.length > 1) sel.remove(1);
    d.familias.forEach(function (f) {
      var o = el('option', null, f.titulo); o.value = f.id; sel.appendChild(o);
    });
  }

  function carga() {
    return api('GET', esAdmin ? '/api/panel/lineas' : '/api/catalogo').then(pinta)
      .catch(function (e) { di(e.message, false); });
  }

  document.getElementById('f-alta').addEventListener('submit', function (ev) {
    ev.preventDefault();
    var valor = function (id) { return document.getElementById(id).value.trim(); };
    var plantillas = Array.prototype.filter.call(document.querySelectorAll('input[name=plantilla]'),
      function (c) { return c.checked; }).map(function (c) { return c.value; }).join('');
    var cuerpo = { nombre: valor('a-nombre'), eyebrow: valor('a-eyebrow'), cobertura: valor('a-cobertura'),
                   nota: valor('a-nota'), canva: valor('a-canva'), cta: valor('a-cta'),
                   familia: valor('a-familia'), alt: valor('a-alt'), plantillas: plantillas };
    if (!plantillas) {
      if (!confirm('No has marcado ninguna plantilla: la línea quedará guardada pero no saldrá en ningún correo. ¿Seguir?')) return;
      cuerpo.confirmarSinPlantillas = true;
    }
    var fichero = document.getElementById('a-foto').files[0];
    if (fichero && !cuerpo.alt) { di('Escribe qué se ve en la foto: es lo que lee quien no ve imágenes.', false); return; }
    var envio = ev.submitter || ev.target.querySelector('button[type=submit]');
    envio.disabled = true;
    api('POST', '/api/panel/lineas', cuerpo).then(function (l) {
      return fichero ? subeFoto(l.id, fichero, cuerpo.alt) : l;
    }).then(function (l) {
      di('Añadida: ' + l.nombre + '. Ya sale en ' + (l.plantillas ? 'las plantillas ' + l.plantillas.split('').join(', ') : 'ninguna plantilla') + '.', true);
      ev.target.reset();
      carga();
    }).catch(function (e) { di(e.message, false); carga(); })
      .then(function () { envio.disabled = false; });
  });

  api('GET', '/api/auth/yo').then(function (d) {
    esAdmin = d.rol === 'admin';
    if (esAdmin) document.getElementById('alta').hidden = false;
    else document.getElementById('sub').textContent = 'Lo que el compositor ofrece como servicios. Solo un administrador añade o cambia líneas.';
    carga();
  }).catch(function (e) { di(e.message, false); });
})();
</script>
</body></html>"""
