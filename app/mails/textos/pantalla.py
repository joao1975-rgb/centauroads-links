"""
La pantalla «Textos de los perfiles» (/panel/textos, especificación 005).

Es la cara de la API de textos, con el mismo patrón que Líneas de negocio: la página no lleva datos,
los pide el navegador y los escribe como TEXTO (los teclea gente). Las reglas —quién cambia, qué se
valida— siguen en la API.

Un comercial la ve en solo lectura: le sirve para saber qué dice cada perfil.
"""

from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from ... import models
from ...auth.dependencias import usuario_actual_opcional

router = APIRouter()

PANTALLA = "/panel/textos"


@router.get(PANTALLA)
def pantalla_de_textos(usuario: Optional[models.PanelUser] = Depends(usuario_actual_opcional)):
    if usuario is None:
        respuesta = RedirectResponse(url="/panel/entrar?destino=" + quote(PANTALLA, safe=""),
                                     status_code=307)
    else:
        respuesta = HTMLResponse(_PAGINA)
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


_PAGINA = """<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Textos de los perfiles · Centauro ADS</title>
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
  p.sub { color:#9A93A6; margin:0 0 24px; font-size:14px; max-width:62ch; }
  h2 { font-size:17px; margin:0 0 4px; }
  section { border-top:1px solid #2E2838; padding:26px 0 6px; }
  .nota { color:#9A93A6; font-size:13px; margin:0 0 18px; max-width:66ch; }
  .perfiles { display:flex; gap:8px; flex-wrap:wrap; margin:0 0 22px; }
  .perfiles button { background:#1E1A26; color:#D9D5E0; font-weight:600; border:1px solid #2E2838; }
  .perfiles button:hover { background:#2E2838; }
  .perfiles button[aria-pressed=true] { background:#3B2547; border-color:#85439A; color:#fff; }
  .cuenta { display:inline-block; margin-left:8px; font-size:11px; font-weight:700; padding:1px 7px;
            border-radius:999px; background:#4A2E12; color:#F7C08A; }
  .texto { padding:0 0 20px; margin:0 0 20px; border-bottom:1px solid #221E2B; }
  .texto:last-child { border-bottom:0; }
  label { display:block; font-size:13px; font-weight:700; color:#D9D5E0; margin:0 0 6px; }
  textarea { width:100%; background:#1E1A26; border:1px solid #6B6885; color:#EEEDF2; border-radius:8px;
             padding:10px 12px; font-size:14px; line-height:1.5; font-family:inherit; resize:vertical; }
  textarea:focus { outline:2px solid #B98FC7; outline-offset:1px; border-color:#B98FC7; }
  textarea[readonly] { border-color:#2E2838; color:#C9C4D2; }
  .cambiado textarea { border-color:#B5732C; }
  .pie { display:flex; justify-content:space-between; gap:12px; font-size:12px; color:#9A93A6; margin:6px 0 0; }
  .pie span:last-child { white-space:nowrap; }
  .cambiado .estado { color:#F7C08A; }
  .serie { font-size:12px; color:#9A93A6; margin:6px 0 0; overflow-wrap:anywhere; }
  .serie b { color:#C9C4D2; font-weight:600; }
  .botones { display:flex; gap:8px; margin:10px 0 0; flex-wrap:wrap; }
  .hecho { font-size:13px; margin:8px 0 0; color:#BFE8D2; }
  .hecho:empty { display:none; }
  .hecho.mal { color:#F4C7CF; }
  button { border:0; border-radius:8px; padding:9px 14px; font-size:14px; font-weight:800;
           cursor:pointer; background:#85439A; color:#fff; font-family:inherit; }
  button:hover { background:#9A50B2; }
  button.suave { background:#241F2E; color:#EEEDF2; font-weight:600; font-size:13px; }
  button.suave:hover { background:#2E2838; }
  button:focus-visible, a:focus-visible { outline:2px solid #EEEDF2; outline-offset:2px; }
  button:disabled { opacity:.5; cursor:default; }
  .msg { margin:0 0 16px; padding:11px 13px; border-radius:8px; font-size:13px; }
  .msg.mal { background:#3A1A22; border:1px solid #6B2B38; color:#F4C7CF; }
</style>
</head><body><main class="caja">
  <div class="arriba">
    <div class="marca">Centauro ADS</div>
    <nav class="nav" aria-label="Panel">
      <a href="/static/email/compositor.html">Volver al compositor</a>
      <a href="/panel/lineas">Líneas de negocio</a>
      <a href="/panel/equipo">Equipo</a>
      <a href="/panel/salir">Salir</a>
    </nav>
  </div>
  <h1>Textos de los perfiles</h1>
  <p class="sub" id="sub">Lo que dice el correo para cada tipo de cliente. Un texto cambiado sale en los
    correos de todo el equipo desde el próximo que se arme, sin desplegar nada.</p>

  <div class="msg" id="aviso" role="alert" hidden></div>
  <div class="perfiles" id="perfiles" role="group" aria-label="Perfil"></div>
  <div id="cuerpo"></div>
</main>
<script>
(function () {
  var aviso = document.getElementById('aviso');
  var esAdmin = false, datos = null, perfil = null;
  var NOTAS = {
    Mensaje: 'Lo que dice el correo con este perfil. Puedes escribir {destinatario} y {empresa}: en el correo ' +
      'se cambian por el nombre de quien lo recibe y el de su empresa.',
    Asuntos: 'Los tres asuntos que ofrece el compositor con este perfil. La etiqueta no cambia; el texto sí.',
    'Ruta de tres pasos': 'Los tres peldaños que ve el cliente nuevo. El formato sale en mayúsculas, y el precio ' +
      'se le añade solo cuando el correo muestra precios.',
    'Puente': 'Las tres casillas calle → puente → móvil y la nota de debajo. Las casillas son estrechas y sus ' +
      'títulos van en mayúsculas: mejor cortos.',
    'Tabla de disponibilidad': 'Las cabeceras de la tabla de espacios. Lo que dice cada espacio (ubicación, ' +
      'medidas, tráfico) se cambia en Líneas de negocio.'
  };

  function di(texto) {
    aviso.textContent = texto;
    aviso.className = 'msg mal';
    aviso.hidden = false;
  }

  function api(metodo, ruta, cuerpo) {
    var op = { method: metodo, headers: {} };
    if (cuerpo) { op.headers['Content-Type'] = 'application/json'; op.body = JSON.stringify(cuerpo); }
    return fetch(ruta, op).then(function (r) {
      if (r.status === 401) { location.href = '/panel/entrar?destino=%2Fpanel%2Ftextos'; throw new Error('Hay que entrar de nuevo'); }
      return r.json().catch(function () { return {}; }).then(function (d) {
        if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : 'No se pudo guardar');
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

  // La hora llega en UTC y sin zona: se muestra tal cual, diciendo que es UTC.
  function cuando(iso) { return iso ? iso.slice(0, 16).replace('T', ' ') + ' UTC' : ''; }

  function suyos() { return datos.textos.filter(function (t) { return t.perfil === perfil; }); }

  function reemplaza(n) {
    datos.textos = datos.textos.map(function (t) { return t.clave === n.clave ? n : t; });
  }

  function pestanas() {
    var caja = document.getElementById('perfiles');
    caja.textContent = '';
    datos.perfiles.forEach(function (p) {
      var n = datos.textos.filter(function (t) { return t.perfil === p.id && t.cambiado; }).length;
      var b = el('button', null, p.nombre);
      b.type = 'button';
      b.setAttribute('aria-pressed', String(p.id === perfil));
      if (n) b.appendChild(el('span', 'cuenta', n + (n === 1 ? ' cambiado' : ' cambiados')));
      b.addEventListener('click', function () { perfil = p.id; pinta(); });
      caja.appendChild(b);
    });
  }

  // Un texto: su campo, si es el de serie o quién lo cambió, y (para un administrador) guardar o volver.
  function texto(t, hecho) {
    var caja = el('div', 'texto' + (t.cambiado ? ' cambiado' : ''));
    var id = 't-' + t.clave.split('.').join('-');
    var etiqueta = el('label', null, t.etiqueta);
    etiqueta.htmlFor = id;
    var area = el('textarea');
    area.id = id; area.value = t.valor; area.maxLength = t.limite; area.rows = t.limite > 200 ? 4 : 2;
    area.readOnly = !esAdmin;
    var cuenta = el('span', null, t.valor.length + ' / ' + t.limite);
    area.addEventListener('input', function () { cuenta.textContent = area.value.length + ' / ' + t.limite; });
    var pie = el('div', 'pie');
    pie.appendChild(el('span', 'estado', t.cambiado ? 'Cambiado por ' + t.actualizado_por + ' · ' + cuando(t.actualizado_en) : 'De serie'));
    pie.appendChild(cuenta);
    caja.appendChild(etiqueta); caja.appendChild(area); caja.appendChild(pie);
    if (t.cambiado) {
      var serie = el('p', 'serie');
      serie.appendChild(el('b', null, 'De serie: '));
      serie.appendChild(document.createTextNode(t.serie));
      caja.appendChild(serie);
    }
    var msg = el('p', 'hecho' + (hecho && hecho.mal ? ' mal' : ''), hecho ? hecho.texto : '');
    msg.setAttribute('role', 'status');
    if (esAdmin) {
      var botones = el('div', 'botones');
      var guardar = el('button', null, 'Guardar');
      guardar.type = 'button';
      guardar.addEventListener('click', function () {
        guardar.disabled = true;
        api('PUT', '/api/panel/textos/' + encodeURIComponent(t.clave), { valor: area.value })
          .then(function (n) {
            cambia(caja, n, n.cambiado ? 'Guardado. Sale en los correos desde el próximo que se arme.'
                                       : 'Es igual al de serie: queda como de serie.');
          })
          .catch(function (e) { msg.textContent = e.message; msg.className = 'hecho mal'; guardar.disabled = false; });
      });
      botones.appendChild(guardar);
      if (t.cambiado) {
        var vuelve = el('button', 'suave', 'Volver al de serie');
        vuelve.type = 'button';
        vuelve.addEventListener('click', function () {
          vuelve.disabled = true;
          api('DELETE', '/api/panel/textos/' + encodeURIComponent(t.clave))
            .then(function (n) { cambia(caja, n, 'De vuelta al texto de serie.'); })
            .catch(function (e) { msg.textContent = e.message; msg.className = 'hecho mal'; vuelve.disabled = false; });
        });
        botones.appendChild(vuelve);
      }
      caja.appendChild(botones);
    }
    caja.appendChild(msg);
    return caja;
  }

  // Tras guardar se rehace solo ese texto, sin mover la página, y se deja el foco donde estaba.
  function cambia(caja, n, mensaje) {
    reemplaza(n);
    var nueva = texto(n, { texto: mensaje });
    caja.parentNode.replaceChild(nueva, caja);
    nueva.querySelector('textarea').focus({ preventScroll: true });
    pestanas();
  }

  function pinta() {
    pestanas();
    var cuerpo = document.getElementById('cuerpo');
    cuerpo.textContent = '';
    if (perfil === 'general') {
      cuerpo.appendChild(el('p', 'nota', 'El perfil General usa los textos que se escriben en el compositor; ' +
        'aquí solo están sus tres asuntos.'));
    }
    // Los grupos, en el orden en que llegan: Mensaje, el bloque propio del perfil y Asuntos.
    var grupos = [];
    suyos().forEach(function (t) { if (grupos.indexOf(t.grupo) < 0) grupos.push(t.grupo); });
    grupos.forEach(function (g) {
      var deGrupo = suyos().filter(function (t) { return t.grupo === g; });
      var sec = el('section');
      sec.appendChild(el('h2', null, g));
      if (NOTAS[g]) sec.appendChild(el('p', 'nota', NOTAS[g]));
      deGrupo.forEach(function (t) { sec.appendChild(texto(t)); });
      cuerpo.appendChild(sec);
    });
  }

  api('GET', '/api/auth/yo').then(function (d) {
    esAdmin = d.rol === 'admin';
    if (!esAdmin) document.getElementById('sub').textContent =
      'Lo que dice el correo para cada tipo de cliente. Solo un administrador cambia estos textos.';
    return api('GET', '/api/panel/textos');
  }).then(function (d) {
    datos = d;
    perfil = (d.perfiles[1] || d.perfiles[0] || {}).id;
    pinta();
  }).catch(function (e) { di(e.message); });
})();
</script>
</body></html>"""
