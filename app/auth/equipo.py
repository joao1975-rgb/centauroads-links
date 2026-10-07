"""
La pantalla del equipo: quién entra al panel, y la contraseña de cada quien (T126 de la 002).

La API de la lista existía desde la 002 (`/api/panel/usuarios` y sus contraseñas), pero sin
pantalla: dar acceso a alguien exigía llamar a la API a mano, y con Google sin configurar eso
dejaba la herramienta sin forma de repartirse al equipo. Esta página es solo la cara de esa API.
No decide nada por su cuenta: las reglas (solo un administrador administra, nadie se retira a sí
mismo, la propia se cambia dando la actual, 12 caracteres como mínimo) siguen en la API.

La página no lleva datos de nadie: los pide el navegador y los escribe como TEXTO. Nombres y
correos los teclea gente, y meterlos como HTML sería abrir la puerta a que uno de ellos se
ejecute en el navegador de un administrador.
"""

from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from .. import models
from .dependencias import usuario_actual_opcional

router = APIRouter()

PANTALLA = "/panel/equipo"


@router.get(PANTALLA)
def pantalla_del_equipo(usuario: Optional[models.PanelUser] = Depends(usuario_actual_opcional)):
    if usuario is None:
        respuesta = RedirectResponse(url="/panel/entrar?destino=" + quote(PANTALLA, safe=""),
                                     status_code=307)
    else:
        respuesta = HTMLResponse(_PAGINA)
    # Como el compositor: tras salir, el navegador no debe seguir enseñándola de su caché.
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


_PAGINA = """<!DOCTYPE html>
<html lang="es"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Equipo · Centauro ADS</title>
<style>
  :root { color-scheme: dark; }
  * { box-sizing: border-box; }
  body { margin:0; background:#14111A; color:#EEEDF2;
         font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif; }
  .caja { max-width:760px; margin:0 auto; padding:28px 16px 64px; }
  .arriba { display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; }
  .marca { font-size:11px; font-weight:800; letter-spacing:.24em; text-transform:uppercase; color:#B98FC7; }
  .nav { display:flex; gap:16px; font-size:13px; }
  .nav a { color:#C9A3D8; text-underline-offset:3px; }
  h1 { font-size:28px; line-height:1.2; letter-spacing:-.02em; margin:14px 0 6px; }
  p.sub { color:#9A93A6; margin:0 0 30px; font-size:14px; }
  h2 { font-size:17px; margin:0 0 4px; }
  section { border-top:1px solid #2E2838; padding:26px 0; }
  .nota { color:#9A93A6; font-size:13px; margin:0 0 16px; }
  ul.lista { list-style:none; margin:0; padding:0; }
  /* Dos columnas fijas -quien a la izquierda, acciones a la derecha- para que todas las filas
     alineen igual tengan uno o dos botones. En el movil, una sola columna. */
  .fila { display:grid; grid-template-columns:minmax(0,1fr) auto; align-items:center; gap:10px 16px;
          padding:14px 0; border-bottom:1px solid #221E2B; }
  .quien { min-width:0; }
  .quien b { display:block; font-size:14px; }
  .correo { display:block; color:#A9A2B5; font-size:13px; overflow-wrap:anywhere; }
  .meta { display:flex; flex-wrap:wrap; align-items:center; gap:6px 10px; margin-top:6px; }
  .etq { font-size:11px; font-weight:700; letter-spacing:.06em; text-transform:uppercase;
         padding:3px 8px; border-radius:999px; background:#241F2E; color:#C9C3D3; white-space:nowrap; }
  .etq.admin { background:#3B2547; color:#E2C6EC; }
  .etq.fuera { background:#3A1A22; color:#F4C7CF; }
  .cuando { color:#8C8598; font-size:12px; }
  .acciones { display:flex; gap:8px; flex-wrap:wrap; justify-content:flex-end; }
  .clave-otro { grid-column:1 / -1; display:flex; gap:8px; flex-wrap:wrap; }
  .clave-otro input { flex:1 1 220px; margin:0; }
  label { display:block; font-size:12px; color:#A9A2B5; margin:0 0 4px; }
  input, select { width:100%; background:#1E1A26; border:1px solid #6B6885; color:#EEEDF2;
                  border-radius:8px; padding:11px 12px; font-size:14px; margin:0 0 14px; font-family:inherit; }
  input:focus, select:focus { outline:2px solid #B98FC7; outline-offset:1px; border-color:#B98FC7; }
  .rejilla { display:grid; grid-template-columns:repeat(auto-fit, minmax(300px, 1fr)); gap:0 16px; }
  .con-boton { display:flex; gap:8px; align-items:stretch; margin:0 0 14px; }
  .con-boton input { flex:1; margin:0; min-width:0; }
  @media (max-width:560px) { .fila { grid-template-columns:1fr; } .acciones { justify-content:flex-start; } }
  button { border:0; border-radius:8px; padding:11px 16px; font-size:14px; font-weight:800;
           cursor:pointer; background:#85439A; color:#fff; font-family:inherit; }
  button:hover { background:#9A50B2; }
  button.suave { background:#241F2E; color:#EEEDF2; font-weight:600; padding:8px 12px; font-size:13px; }
  button.suave:hover { background:#2E2838; }
  button.peligro { background:transparent; border:1px solid #6B2B38; color:#F4C7CF;
                   font-weight:600; padding:7px 12px; font-size:13px; }
  button.peligro:hover { background:#3A1A22; }
  /* El editor de una persona se abre debajo de su fila, ocupando las dos columnas. */
  .editor { grid-column:1 / -1; display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr));
            gap:0 12px; padding:14px 14px 0; background:#1A1622; border:1px solid #2E2838; border-radius:10px; }
  .editor .botones { grid-column:1 / -1; display:flex; gap:8px; margin:0 0 14px; }
  .editor .nota { grid-column:1 / -1; margin:-6px 0 12px; }
  button:focus-visible, a:focus-visible { outline:2px solid #EEEDF2; outline-offset:2px; }
  button:disabled { opacity:.5; cursor:default; }
  .msg { margin:0 0 16px; padding:11px 13px; border-radius:8px; font-size:13px; }
  .msg.ok { background:#16271F; border:1px solid #2C5A43; color:#BFE8D2; }
  .msg.mal { background:#3A1A22; border:1px solid #6B2B38; color:#F4C7CF; }
  .msg code { font-size:14px; color:#fff; overflow-wrap:anywhere; }
</style>
</head><body><main class="caja">
  <div class="arriba">
    <div class="marca">Centauro ADS</div>
    <nav class="nav" aria-label="Panel">
      <a href="/panel/inicio">Inicio</a>
      <a href="/static/email/compositor.html">Volver al compositor</a>
      <a href="/panel/salir">Salir</a>
    </nav>
  </div>
  <h1>Equipo</h1>
  <p class="sub" id="soy">Quién puede entrar al panel, y tu contraseña.</p>

  <div class="msg" id="aviso" role="status" aria-live="polite" tabindex="-1" hidden></div>

  <section id="lista" aria-labelledby="t-lista" hidden>
    <h2 id="t-lista">Personas con acceso</h2>
    <p class="nota">Retirar el acceso no borra a nadie: su historial se conserva y se puede devolver.</p>
    <ul class="lista" id="filas"></ul>
  </section>

  <section id="alta" aria-labelledby="t-alta" hidden>
    <h2 id="t-alta">Añadir a alguien</h2>
    <p class="nota">Entrará con este correo y la contraseña que le pongas. Pásasela por un canal privado
      y pídele que la cambie al entrar, aquí abajo.</p>
    <form id="f-alta" autocomplete="off">
      <div class="rejilla">
        <div><label for="a-email">Correo</label>
          <input id="a-email" type="email" required autocomplete="off"></div>
        <div><label for="a-nombre">Nombre</label>
          <input id="a-nombre" type="text" maxlength="200" autocomplete="off"></div>
        <div><label for="a-rol">Rol</label>
          <select id="a-rol">
            <option value="comercial">Comercial: prepara y envía correos</option>
            <option value="admin">Administrador: además gestiona el equipo</option>
          </select></div>
        <div><label for="a-clave">Contraseña inicial (12 caracteres o más)</label>
          <div class="con-boton">
            <input id="a-clave" type="text" minlength="12" required autocomplete="new-password" spellcheck="false">
            <button type="button" class="suave" id="generar">Generar</button>
          </div></div>
      </div>
      <button type="submit">Dar acceso</button>
    </form>
  </section>

  <section id="mia" aria-labelledby="t-mia">
    <h2 id="t-mia">Tu contraseña</h2>
    <p class="nota">Si te la puso otra persona, cámbiala: una contraseña que conoce alguien más ya no es solo tuya.</p>
    <form id="f-mia">
      <div class="rejilla">
        <div><label for="m-actual">Contraseña actual</label>
          <input id="m-actual" type="password" required autocomplete="current-password"></div>
        <div><label for="m-nueva">Nueva (12 caracteres o más)</label>
          <input id="m-nueva" type="password" minlength="12" required autocomplete="new-password"></div>
        <div><label for="m-otra">Repite la nueva</label>
          <input id="m-otra" type="password" minlength="12" required autocomplete="new-password"></div>
      </div>
      <button type="submit">Cambiar mi contraseña</button>
    </form>
  </section>
</main>
<script>
(function () {
  var aviso = document.getElementById('aviso');
  var yo = null;
  // La fila propia: tu contrasena se cambia en «Tu contrasena», que pide la actual. Ofrecer
  // «Poner contrasena» en tu fila permitia cambiartela de un clic sin querer (paso el 2026-10-03).
  function esYo(u) { return !!yo && yo.email === u.email; }

  function di(texto, bien, clave) {
    aviso.textContent = texto;
    if (clave) {
      var c = document.createElement('code');
      c.textContent = ' ' + clave;
      aviso.appendChild(c);
    }
    aviso.className = 'msg ' + (bien ? 'ok' : 'mal');
    aviso.hidden = false;
    aviso.scrollIntoView({ block: 'nearest' });
    aviso.focus({ preventScroll: true });
  }

  function api(metodo, ruta, cuerpo) {
    var op = { method: metodo, headers: {} };
    if (cuerpo) { op.headers['Content-Type'] = 'application/json'; op.body = JSON.stringify(cuerpo); }
    return fetch(ruta, op).then(function (r) {
      if (r.status === 401) { location.href = '/panel/entrar?destino=%2Fpanel%2Fequipo'; throw new Error('Hay que entrar de nuevo'); }
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

  function boton(texto, clase, accion, etiqueta) {
    var b = el('button', clase, texto);
    if (etiqueta) b.setAttribute('aria-label', etiqueta);
    b.type = 'button';
    b.addEventListener('click', accion);
    return b;
  }

  function fecha(iso) {
    if (!iso) return 'Aún no ha entrado';
    // La base guarda la hora en UTC sin marcarlo; sin la Z, el navegador la toma por hora local
    // y de noche en Venezuela la fecha salia un dia adelantada.
    var d = new Date(/(Z|[+-][0-9][0-9]:?[0-9][0-9])$/.test(iso) ? iso : iso + 'Z');
    return 'Última entrada: ' + d.toLocaleDateString('es', { day: 'numeric', month: 'short', year: 'numeric' });
  }

  function claveAzar() {
    var letras = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789';
    var n = new Uint32Array(16), s = '';
    crypto.getRandomValues(n);
    for (var i = 0; i < n.length; i++) s += letras[n[i] % letras.length];
    return s.slice(0, 4) + '-' + s.slice(4, 8) + '-' + s.slice(8, 12) + '-' + s.slice(12);
  }

  function formClave(fila, u) {
    if (fila.querySelector('.clave-otro')) return;
    var editor = fila.querySelector('.editor');
    if (editor) editor.remove();
    var caja = el('div', 'clave-otro');
    var entrada = el('input');
    entrada.type = 'text'; entrada.minLength = 12; entrada.spellcheck = false;
    entrada.setAttribute('aria-label', 'Nueva contraseña para ' + u.email);
    entrada.value = claveAzar();
    caja.appendChild(entrada);
    caja.appendChild(boton('Guardar', '', function () {
      api('POST', '/api/panel/usuarios/' + u.id + '/contrasena', { password: entrada.value })
        .then(function () { caja.remove(); di('Contraseña nueva de ' + u.email + ':', true, entrada.value); })
        .catch(function (e) { di(e.message, false); });
    }));
    caja.appendChild(boton('Cancelar', 'suave', function () { caja.remove(); fila.querySelector('.acciones button').focus(); }));
    fila.appendChild(caja);
    entrada.focus(); entrada.select();
  }

  function campo(caja, id, texto, control) {
    var envoltura = el('div');
    var etiqueta = el('label', null, texto);
    etiqueta.htmlFor = id; control.id = id;
    envoltura.appendChild(etiqueta); envoltura.appendChild(control);
    caja.appendChild(envoltura);
    return control;
  }

  // Editar a quien ya esta: corregir su correo o su nombre, o cambiarle el rol. Solo se manda lo
  // que cambio. El rol propio no se puede tocar: la API lo rechaza para que siempre quede alguien
  // que administre, y aqui se dice antes de intentarlo.
  function formEdita(fila, u) {
    if (fila.querySelector('.editor')) return;
    var abierto = fila.querySelector('.clave-otro');
    if (abierto) abierto.remove();
    var soyYo = esYo(u);
    var caja = el('div', 'editor');
    var correo = el('input'); correo.type = 'email'; correo.value = u.email; correo.required = true;
    var nombre = el('input'); nombre.type = 'text'; nombre.maxLength = 200; nombre.value = u.nombre || '';
    var rol = el('select');
    [['comercial', 'Comercial'], ['admin', 'Administrador']].forEach(function (o) {
      var opcion = el('option', null, o[1]); opcion.value = o[0];
      if (o[0] === u.rol) opcion.selected = true;
      rol.appendChild(opcion);
    });
    campo(caja, 'e-' + u.id + '-correo', 'Correo', correo);
    campo(caja, 'e-' + u.id + '-nombre', 'Nombre', nombre);
    campo(caja, 'e-' + u.id + '-rol', 'Rol', rol);
    if (u.superadmin) {
      correo.disabled = true; rol.disabled = true;
      caja.appendChild(el('p', 'nota', 'Es la cuenta del superadmin: su correo, su rol y su contraseña se gestionan en EasyPanel. Aquí solo se cambia el nombre.'));
    } else if (soyYo) {
      rol.disabled = true;
      caja.appendChild(el('p', 'nota', 'Tu propio rol no se puede cambiar: así siempre queda alguien que administre el equipo.'));
    }
    var botones = el('div', 'botones');
    botones.appendChild(boton('Guardar cambios', '', function () {
      var cambios = {};
      if (!u.superadmin && correo.value.trim().toLowerCase() !== u.email) cambios.email = correo.value.trim();
      if (nombre.value.trim() !== (u.nombre || '')) cambios.nombre = nombre.value.trim();
      if (!soyYo && !u.superadmin && rol.value !== u.rol) cambios.rol = rol.value;
      if (!Object.keys(cambios).length) { caja.remove(); return; }
      api('PATCH', '/api/panel/usuarios/' + u.id, cambios).then(function (d) {
        if (soyYo) { yo.email = d.email; document.getElementById('soy').textContent = 'Has entrado como ' + d.email + '.'; }
        di('Cambios guardados: ' + d.email + ' · ' + (d.rol === 'admin' ? 'Administrador' : 'Comercial'), true);
        carga();
      }).catch(function (e) { di(e.message, false); });
    }));
    botones.appendChild(boton('Cancelar', 'suave', function () { caja.remove(); fila.querySelector('.acciones button').focus(); }));
    caja.appendChild(botones);
    fila.appendChild(caja);
    correo.focus();
  }

  function pinta(lista) {
    var ul = document.getElementById('filas');
    ul.textContent = '';
    lista.forEach(function (u) {
      var li = el('li', 'fila');
      var quien = el('div', 'quien');
      quien.appendChild(el('b', null, u.nombre || u.email));
      quien.appendChild(el('span', 'correo', u.email));
      var meta = el('div', 'meta');
      // El superadmin es la cuenta de la credencial de EasyPanel (006): se dice, y no se le ofrece
      // ni contraseña ni retirar el acceso, que la API rechazaría.
      meta.appendChild(el('span', 'etq' + (u.rol === 'admin' ? ' admin' : ''),
        u.superadmin ? 'Superadmin' : u.rol === 'admin' ? 'Administrador' : 'Comercial'));
      if (!u.activo) meta.appendChild(el('span', 'etq fuera', 'Sin acceso'));
      meta.appendChild(el('span', 'cuando', fecha(u.ultima_entrada)));
      quien.appendChild(meta);
      li.appendChild(quien);
      var acc = el('div', 'acciones');
      acc.appendChild(boton('Editar', 'suave', function () { formEdita(li, u); }, 'Editar a ' + u.email));
      if (u.superadmin) {
        // nada más: su contraseña y su acceso los manda EasyPanel
      } else if (u.activo) {
        if (!esYo(u)) acc.appendChild(boton('Poner contraseña', 'suave', function () { formClave(li, u); }, 'Poner contraseña a ' + u.email));
        if (!esYo(u)) {
          acc.appendChild(boton('Retirar acceso', 'peligro', function () {
            if (!confirm('¿Retirar el acceso de ' + u.email + '? Podrás devolvérselo después.')) return;
            api('DELETE', '/api/panel/usuarios/' + u.id)
              .then(function () { di('Acceso retirado: ' + u.email, true); carga(); })
              .catch(function (e) { di(e.message, false); });
          }));
        }
      } else {
        acc.appendChild(boton('Devolver acceso', 'suave', function () {
          api('POST', '/api/panel/usuarios', { email: u.email, nombre: u.nombre, rol: u.rol })
            .then(function () { di('Acceso devuelto: ' + u.email + '. Su contraseña anterior sigue valiendo.', true); carga(); })
            .catch(function (e) { di(e.message, false); });
        }));
      }
      li.appendChild(acc);
      ul.appendChild(li);
    });
  }

  function carga() {
    return api('GET', '/api/panel/usuarios').then(pinta).catch(function (e) { di(e.message, false); });
  }

  document.getElementById('generar').addEventListener('click', function () {
    document.getElementById('a-clave').value = claveAzar();
  });

  document.getElementById('f-alta').addEventListener('submit', function (ev) {
    ev.preventDefault();
    var email = document.getElementById('a-email').value.trim();
    var clave = document.getElementById('a-clave').value;
    if (clave.length < 12) { di('La contraseña debe tener al menos 12 caracteres', false); return; }
    var envio = ev.submitter || ev.target.querySelector('button[type=submit]');
    envio.disabled = true;
    api('POST', '/api/panel/usuarios', {
      email: email, nombre: document.getElementById('a-nombre').value.trim(),
      rol: document.getElementById('a-rol').value
    }).then(function (u) {
      return api('POST', '/api/panel/usuarios/' + u.id + '/contrasena', { password: clave }).then(function () { return u; });
    }).then(function (u) {
      di((u.reactivado ? 'Acceso devuelto a ' : 'Listo. ') + u.email + ' entra en mails.centauroads.com con la contraseña:', true, clave);
      ev.target.reset();
      carga();
    }).catch(function (e) { di(e.message, false); })
      .then(function () { envio.disabled = false; });
  });

  document.getElementById('f-mia').addEventListener('submit', function (ev) {
    ev.preventDefault();
    var nueva = document.getElementById('m-nueva').value;
    if (nueva !== document.getElementById('m-otra').value) { di('Las dos contraseñas nuevas no coinciden', false); return; }
    api('POST', '/api/auth/contrasena', { actual: document.getElementById('m-actual').value, nueva: nueva })
      .then(function () { ev.target.reset(); di('Tu contraseña está cambiada.', true); })
      .catch(function (e) { di(e.message, false); });
  });

  api('GET', '/api/auth/yo').then(function (d) {
    yo = d;
    document.getElementById('soy').textContent = 'Has entrado como ' + d.email + (d.superadmin ? ' (superadmin).' : '.');
    if (d.superadmin) {
      // Su contraseña es SUPERADMIN_PASS: aquí no se cambia (la API lo rechazaría).
      var f = document.getElementById('f-mia');
      f.hidden = true;
      f.parentNode.querySelector('.nota').textContent =
        'Eres el superadmin: tu contraseña es la de EasyPanel (SUPERADMIN_PASS) y se cambia allí, en el servicio centauro-links → Entorno.';
    }
    if (d.rol === 'admin') {
      document.getElementById('lista').hidden = false;
      document.getElementById('alta').hidden = false;
      carga();
    }
  }).catch(function (e) { di(e.message, false); });
})();
</script>
</body></html>"""
