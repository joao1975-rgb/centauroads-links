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

_NOMBRES_JS = "[" + ", ".join("['%s', '%s']" % (k, n) for k, n in _PLANTILLAS) + "]"

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
  .acciones { display:flex; gap:8px; justify-content:flex-end; flex-wrap:wrap; }
  button.flecha { background:#241F2E; color:#EEEDF2; font-weight:700; padding:6px 10px; font-size:14px; }
  button.flecha:hover { background:#2E2838; }
  button.peligro { background:transparent; border:1px solid #6B2B38; color:#F4C7CF;
                   font-weight:600; padding:7px 12px; font-size:13px; }
  button.peligro:hover { background:#3A1A22; }
  /* El editor de una linea se abre debajo de su fila, a todo lo ancho. */
  .editor { grid-column:1 / -1; padding:14px 14px 0; background:#1A1622; border:1px solid #2E2838; border-radius:10px; }
  .editor .botones { display:flex; gap:8px; margin:0 0 14px; }
  .retiradas .miniatura { opacity:.55; }
  /* Un grupo no lleva miniatura: dos columnas, quien y acciones. */
  .fila.grupo { grid-template-columns:minmax(0,1fr) auto; }
  #f-grupo { margin-top:18px; }
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

  <section id="retiradas" class="retiradas" aria-labelledby="t-retiradas" hidden>
    <h2 id="t-retiradas">Retiradas</h2>
    <p class="nota">No salen en los correos nuevos; los ya enviados no cambian. Se pueden devolver tal como estaban.</p>
    <ul class="lista" id="filas-retiradas"></ul>
  </section>

  <section id="grupos" aria-labelledby="t-grupos">
    <h2 id="t-grupos">Grupos de la plantilla D</h2>
    <p class="nota">La plantilla D presenta las líneas agrupadas, en este orden. Un grupo con una sola línea sale
      con el nombre de esa línea; las líneas sin grupo van al final, en «Otros servicios».</p>
    <ul class="lista" id="filas-grupos"></ul>
    <form id="f-grupo" autocomplete="off" hidden>
      <div class="rejilla">
        <div><label for="g-titulo">Título del grupo nuevo (lo lee el cliente)</label>
          <input id="g-titulo" type="text" maxlength="120" required></div>
      </div>
      <button type="submit">Añadir grupo</button>
    </form>
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
        <legend>Ficha técnica (opcional)</legend>
        <p class="nota">Con ubicación, medidas o tráfico, la línea entra en la tabla de agencias y en el
          inventario de la plantilla E. Sin ficha, no aparece en esas tablas.</p>
        <div class="rejilla">
          <div><label for="a-ficha-ubic">Ubicación</label>
            <input id="a-ficha-ubic" type="text" maxlength="120"></div>
          <div><label for="a-ficha-medida">Medidas</label>
            <input id="a-ficha-medida" type="text" maxlength="120"></div>
          <div><label for="a-ficha-trafico">Tráfico o audiencia</label>
            <input id="a-ficha-trafico" type="text" maxlength="120"></div>
          <div><label for="a-ficha-desde">Precio desde, $/mes (solo el número; sale con los precios activados)</label>
            <input id="a-ficha-desde" type="text" inputmode="decimal" maxlength="20"></div>
        </div>
      </fieldset>
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
  var todas = [], familias = [];
  var NOMBRES = """ + _NOMBRES_JS + """;

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
        // Un 422 de FastAPI trae la lista de campos, no una frase.
        if (!r.ok) throw new Error(typeof d.detail === 'string' ? d.detail : 'Revisa los datos del formulario');
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
    return [b, entrada];
  }

  function casillasPlantillas(caja, l) {
    var grupo = el('fieldset');
    grupo.appendChild(el('legend', null, 'Plantillas en que sale'));
    var rejilla = el('div', 'casillas');
    NOMBRES.forEach(function (par) {
      var etiqueta = el('label', 'casilla');
      var c = el('input'); c.type = 'checkbox'; c.value = par[0]; c.checked = l.plantillas.indexOf(par[0]) >= 0;
      etiqueta.appendChild(c); etiqueta.appendChild(el('b', null, par[0]));
      etiqueta.appendChild(document.createTextNode(' ' + par[1]));
      rejilla.appendChild(etiqueta);
    });
    grupo.appendChild(rejilla);
    caja.appendChild(grupo);
    return function () {
      return Array.prototype.filter.call(rejilla.querySelectorAll('input'), function (c) { return c.checked; })
        .map(function (c) { return c.value; }).join('');
    };
  }

  function campo(caja, id, texto, control) {
    var envoltura = el('div');
    var etiqueta = el('label', null, texto);
    etiqueta.htmlFor = id; control.id = id;
    envoltura.appendChild(etiqueta); envoltura.appendChild(control);
    caja.appendChild(envoltura);
    return control;
  }

  // Editar en la fila: solo se manda lo que cambio. El identificador no cambia aunque cambie el
  // nombre: es lo que reconoce el estado guardado de cada compositor.
  function formEdita(li, l) {
    if (li.querySelector('.editor')) return;
    var caja = el('div', 'editor');
    var rejilla = el('div', 'rejilla');
    var CAMPOS = [['nombre', 'Nombre', 120], ['eyebrow', 'Etiqueta corta', 60], ['cobertura', 'Cobertura o ubicación', 200],
                  ['nota', 'Nota (opcional)', 300], ['canva', 'Enlace de la presentación', 500],
                  ['cta', 'Texto de su botón (opcional)', 60], ['alt', 'Qué se ve en la foto', 200]];
    var entradas = {};
    CAMPOS.forEach(function (f) {
      var i = el('input'); i.type = f[0] === 'canva' ? 'url' : 'text'; i.maxLength = f[2]; i.value = l[f[0]] || '';
      entradas[f[0]] = campo(rejilla, 'e-' + l.id + '-' + f[0], f[1], i);
    });
    var familia = el('select');
    familia.appendChild(el('option', null, 'Ninguno · va a «Otros servicios»')).value = '';
    familias.forEach(function (f) {
      var o = el('option', null, f.titulo); o.value = f.id; o.selected = f.id === l.familia; familia.appendChild(o);
    });
    campo(rejilla, 'e-' + l.id + '-familia', 'Grupo en la plantilla D', familia);
    caja.appendChild(rejilla);
    var ficha = l.ficha || {}, entradasFicha = {};
    var grupoFicha = el('fieldset');
    grupoFicha.appendChild(el('legend', null, 'Ficha técnica (opcional)'));
    grupoFicha.appendChild(el('p', 'nota', 'Con ubicación, medidas o tráfico, entra en la tabla de agencias y en el inventario de la E. Vacía, no.'));
    var rejillaFicha = el('div', 'rejilla');
    [['ubic', 'Ubicación'], ['medida', 'Medidas'], ['trafico', 'Tráfico o audiencia'],
     ['desde', 'Precio desde, $/mes (solo el número)']].forEach(function (f) {
      var i = el('input'); i.type = 'text'; i.maxLength = 120; i.value = ficha[f[0]] || '';
      if (f[0] === 'desde') i.inputMode = 'decimal';
      entradasFicha[f[0]] = campo(rejillaFicha, 'e-' + l.id + '-ficha-' + f[0], f[1], i);
    });
    grupoFicha.appendChild(rejillaFicha);
    caja.appendChild(grupoFicha);
    var plantillas = casillasPlantillas(caja, l);
    var botones = el('div', 'botones');
    botones.appendChild(boton('Guardar cambios', '', function () {
      var cambios = {};
      Object.keys(entradas).forEach(function (k) {
        if (entradas[k].value.trim() !== (l[k] || '')) cambios[k] = entradas[k].value.trim();
      });
      if (familia.value !== (l.familia || '')) cambios.familia = familia.value;
      Object.keys(entradasFicha).forEach(function (k) {
        var v = entradasFicha[k].value.trim();
        if (v !== (ficha[k] || '')) { cambios.ficha = cambios.ficha || {}; cambios.ficha[k] = v; }
      });
      var letras = plantillas();
      if (letras !== l.plantillas) {
        if (!letras && !confirm('No has marcado ninguna plantilla: la línea no saldrá en ningún correo. ¿Seguir?')) return;
        cambios.plantillas = letras;
        if (!letras) cambios.confirmarSinPlantillas = true;
      }
      if (!Object.keys(cambios).length) { caja.remove(); return; }
      api('PATCH', '/api/panel/lineas/' + encodeURIComponent(l.id), cambios)
        .then(function (d) { di('Cambios guardados: ' + d.nombre + '. Los compositores del equipo los reciben al abrirse.', true); carga(); })
        .catch(function (e) { di(e.message, false); });
    }));
    botones.appendChild(boton('Cancelar', 'suave', function () { caja.remove(); li.querySelector('.acciones button').focus(); }));
    caja.appendChild(botones);
    li.appendChild(caja);
    entradas.nombre.focus();
  }

  function boton(texto, clase, accion, etiqueta) {
    var b = el('button', clase, texto);
    b.type = 'button';
    if (etiqueta) b.setAttribute('aria-label', etiqueta);
    b.addEventListener('click', accion);
    return b;
  }

  // Subir o bajar cambia el sitio con la activa de al lado. El orden se manda completo, con las
  // retiradas en su sitio: la API no acepta una lista a medias.
  function mueve(l, paso) {
    var activas = todas.filter(function (x) { return x.activa !== false; });
    var i = activas.indexOf(l), otra = activas[i + paso];
    if (!otra) return;
    var ids = todas.map(function (x) { return x.id; });
    var a = ids.indexOf(l.id), b = ids.indexOf(otra.id);
    ids[a] = otra.id; ids[b] = l.id;
    api('POST', '/api/panel/lineas/orden', { ids: ids }).then(function () {
      return carga();
    }).then(function () {
      // El foco sigue en la misma flecha; si llego al extremo y se apago, pasa a la otra.
      var fila = document.querySelector('[data-linea="' + l.id + '"]');
      var vuelta = fila && fila.querySelector('.flecha' + (paso < 0 ? '.sube' : '.baja'));
      if (vuelta && vuelta.disabled) vuelta = fila.querySelector('.flecha' + (paso < 0 ? '.baja' : '.sube'));
      if (vuelta && !vuelta.disabled) vuelta.focus();
    }).catch(function (e) { di(e.message, false); });
  }

  function activa(l, si) {
    if (!si && !confirm('¿Retirar «' + l.nombre + '»? Deja de salir en los correos nuevos; los ya enviados no cambian. Podrás devolverla.')) return;
    api('PATCH', '/api/panel/lineas/' + encodeURIComponent(l.id), { activa: si })
      .then(function () { di((si ? 'Devuelta: ' : 'Retirada: ') + l.nombre, true); carga(); })
      .catch(function (e) { di(e.message, false); });
  }

  function fila(l, i, n) {
      var li = el('li', 'fila');
      li.dataset.linea = l.id;
      li.appendChild(miniatura(l));
      var quien = el('div', 'quien');
      var nombre = el('b', null, l.nombre);
      if (l.activa === false) nombre.appendChild(el('span', 'etq', 'Retirada'));
      quien.appendChild(nombre);
      var detalle = [l.eyebrow, l.cobertura].filter(Boolean).join(' · ');
      if (detalle) quien.appendChild(el('span', 'detalle', detalle));
      if (l.ficha) quien.appendChild(el('span', 'detalle', 'Ficha: ' + [l.ficha.ubic, l.ficha.medida, l.ficha.trafico].filter(Boolean).join(' · ')));
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
      if (!esAdmin) return li;
      var acc = el('div', 'acciones');
      if (l.activa !== false) {
        var sube = boton('↑', 'flecha sube', function () { mueve(l, -1); }, 'Subir ' + l.nombre);
        var baja = boton('↓', 'flecha baja', function () { mueve(l, 1); }, 'Bajar ' + l.nombre);
        sube.disabled = i === 0; baja.disabled = i === n - 1;
        acc.appendChild(sube); acc.appendChild(baja);
        acc.appendChild(boton('Editar', 'suave', function () { formEdita(li, l); }, 'Editar ' + l.nombre));
        // Solo las fotos que se subieron aqui: las de serie van con su carrusel generado.
        if (!l.img || l.img.charAt(0) === '/') botonFoto(l).forEach(function (pieza) { acc.appendChild(pieza); });
        acc.appendChild(boton('Retirar', 'peligro', function () { activa(l, false); }, 'Retirar ' + l.nombre));
      } else {
        acc.appendChild(boton('Devolver', 'suave', function () { activa(l, true); }, 'Devolver ' + l.nombre));
      }
      li.appendChild(acc);
      return li;
  }

  function pinta(d) {
    todas = d.lineas;
    familias = d.familias;
    pintaGrupos(d);
    var activas = d.lineas.filter(function (l) { return l.activa !== false; });
    var fuera = d.lineas.filter(function (l) { return l.activa === false; });
    var ul = document.getElementById('filas');
    ul.textContent = '';
    activas.forEach(function (l, i) { ul.appendChild(fila(l, i, activas.length)); });
    var ur = document.getElementById('filas-retiradas');
    ur.textContent = '';
    fuera.forEach(function (l, i) { ur.appendChild(fila(l, i, fuera.length)); });
    document.getElementById('retiradas').hidden = !fuera.length;
    var sel = document.getElementById('a-familia');
    while (sel.options.length > 1) sel.remove(1);
    d.familias.forEach(function (f) {
      var o = el('option', null, f.titulo); o.value = f.id; sel.appendChild(o);
    });
  }

  // Los grupos de la D, cada uno con las lineas activas que lleva. Renombrar no cambia el id: las
  // lineas siguen en su grupo.
  function pintaGrupos(d) {
    var ul = document.getElementById('filas-grupos');
    ul.textContent = '';
    d.familias.forEach(function (f) {
      var suyas = d.lineas.filter(function (l) { return l.activa !== false && l.familia === f.id; });
      var li = el('li', 'fila grupo');
      li.dataset.grupo = f.id;
      var quien = el('div', 'quien');
      quien.appendChild(el('b', null, f.titulo));
      var lineas = suyas.length ? suyas.map(function (l) { return l.nombre; }).join(' · ') : 'Sin líneas: no sale en la plantilla D';
      quien.appendChild(el('span', 'detalle', lineas));
      li.appendChild(quien);
      if (esAdmin) {
        var acc = el('div', 'acciones');
        acc.appendChild(boton('Editar', 'suave', function () { formGrupo(li, f); }, 'Editar el grupo ' + f.titulo));
        li.appendChild(acc);
      }
      ul.appendChild(li);
    });
  }

  function formGrupo(li, f) {
    if (li.querySelector('.editor')) return;
    var caja = el('div', 'editor');
    var rejilla = el('div', 'rejilla');
    var titulo = el('input'); titulo.type = 'text'; titulo.maxLength = 120; titulo.value = f.titulo;
    // Solo el titulo: es lo unico del grupo que sale en el correo.
    campo(rejilla, 'g-' + f.id + '-titulo', 'Título (lo lee el cliente)', titulo);
    caja.appendChild(rejilla);
    var botones = el('div', 'botones');
    botones.appendChild(boton('Guardar cambios', '', function () {
      var cambios = {};
      if (titulo.value.trim() !== f.titulo) cambios.titulo = titulo.value.trim();
      if (!Object.keys(cambios).length) { caja.remove(); return; }
      api('PATCH', '/api/panel/familias/' + encodeURIComponent(f.id), cambios)
        .then(function (g) { di('Grupo guardado: ' + g.titulo + '.', true); carga(); })
        .catch(function (e) { di(e.message, false); });
    }));
    botones.appendChild(boton('Cancelar', 'suave', function () { caja.remove(); li.querySelector('.acciones button').focus(); }));
    caja.appendChild(botones);
    li.appendChild(caja);
    titulo.focus();
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
                   familia: valor('a-familia'), alt: valor('a-alt'), plantillas: plantillas,
                   ficha: { ubic: valor('a-ficha-ubic'), medida: valor('a-ficha-medida'),
                            trafico: valor('a-ficha-trafico'), desde: valor('a-ficha-desde') } };
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

  document.getElementById('f-grupo').addEventListener('submit', function (ev) {
    ev.preventDefault();
    var envio = ev.submitter || ev.target.querySelector('button[type=submit]');
    envio.disabled = true;
    api('POST', '/api/panel/familias', { titulo: document.getElementById('g-titulo').value.trim() })
      .then(function (g) {
        di('Grupo añadido: ' + g.titulo + '. Asígnale líneas al darlas de alta o al editarlas.', true);
        ev.target.reset();
        carga();
      }).catch(function (e) { di(e.message, false); })
      .then(function () { envio.disabled = false; });
  });

  api('GET', '/api/auth/yo').then(function (d) {
    esAdmin = d.rol === 'admin';
    if (esAdmin) { document.getElementById('alta').hidden = false; document.getElementById('f-grupo').hidden = false; }
    else document.getElementById('sub').textContent = 'Lo que el compositor ofrece como servicios. Solo un administrador añade o cambia líneas.';
    carga();
  }).catch(function (e) { di(e.message, false); });
})();
</script>
</body></html>"""
