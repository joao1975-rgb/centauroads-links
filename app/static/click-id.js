/*
 * click-id.js — el script de la página /c/<slug> del acortador.
 *
 * Calcula dos valores y sigue a /c/<slug>/ir, que los guarda con el clic y abre el destino con
 * ?click_id=<valor>&fingerprint=<huella>, más los parámetros con los que se llamó al link (`q`):
 *   - fingerprint: siempre, la huella del dispositivo, `fp.<28 hex>` (mismo teléfono → mismo valor).
 *   - click_id: si la persona llega desde un anuncio de Meta (?fbclid=...), el fbc de Meta,
 *     `fb.1.<milisegundos>.<fbclid>`, que se guarda en la cookie `_fbc` 90 días, como hace el píxel.
 *     Si no trae fbclid pero ya tiene la cookie `_fbc` de una visita anterior, esa. Si no hay
 *     ninguna de las dos, la huella.
 *
 * La regla del fbc es la misma de meta-events (public/centauro-meta.js). Las señales de la huella
 * son las que ya recoge qr-tracking en su página /tracking (templates/tracking.html), quitando las
 * que cambian entre visitas del mismo teléfono (tamaño de ventana, conexión, modo oscuro).
 *
 * Uso: <script src="/static/click-id.js" data-ir="/c/<slug>/ir"></script>
 */
(function (root) {
  'use strict';

  var NOVENTA_DIAS = 7776000; // segundos
  var FBCLID_VALIDO = /^[A-Za-z0-9_-]{1,500}$/;

  function leeCookie(doc, nombre) {
    var m = (doc.cookie || '').match(new RegExp('(?:^|; )' + nombre + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : '';
  }

  // El fbc de Meta. Devuelve { valor, nuevo } o null si no hay fbclid ni cookie.
  function calculaFbc(search, cookieFbc, ahoraMs) {
    var fbclid = new URLSearchParams(search || '').get('fbclid') || '';
    if (fbclid && FBCLID_VALIDO.test(fbclid)) {
      // Mismo fbclid que la cookie: se conserva su marca de tiempo (así lo hace el píxel).
      if (cookieFbc && cookieFbc.split('.').slice(3).join('.') === fbclid) {
        return { valor: cookieFbc, nuevo: false };
      }
      return { valor: 'fb.1.' + ahoraMs + '.' + fbclid, nuevo: true };
    }
    if (/^fb\.\d\.\d+\..+/.test(cookieFbc || '')) return { valor: cookieFbc, nuevo: false };
    return null;
  }

  // cyrb53: hash de 53 bits, rápido y sin dependencias. Dos semillas = 106 bits, de sobra aquí.
  // No se usa crypto.subtle porque falta en algunos navegadores internos de apps y en http.
  function cyrb53(texto, semilla) {
    var h1 = 0xdeadbeef ^ semilla, h2 = 0x41c6ce57 ^ semilla;
    for (var i = 0; i < texto.length; i++) {
      var c = texto.charCodeAt(i);
      h1 = Math.imul(h1 ^ c, 2654435761);
      h2 = Math.imul(h2 ^ c, 1597334677);
    }
    h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
    h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
    return 4294967296 * (2097151 & h2) + (h1 >>> 0);
  }

  function hex14(n) {
    var s = n.toString(16);
    while (s.length < 14) s = '0' + s;
    return s;
  }

  // Las señales estables del dispositivo, en orden fijo.
  function senales(win) {
    var nav = win.navigator || {}, scr = win.screen || {};
    var gl = { vendor: '', renderer: '' };
    try {
      var canvas = win.document.createElement('canvas');
      var ctx = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
      var info = ctx && ctx.getExtension('WEBGL_debug_renderer_info');
      if (info) {
        gl.vendor = ctx.getParameter(info.UNMASKED_VENDOR_WEBGL) || '';
        gl.renderer = ctx.getParameter(info.UNMASKED_RENDERER_WEBGL) || '';
      }
    } catch (e) { /* sin WebGL: se queda vacío */ }
    var zona = '';
    try { zona = Intl.DateTimeFormat().resolvedOptions().timeZone || ''; } catch (e) { /* nada */ }
    return [
      nav.userAgent || '',
      nav.platform || '',
      nav.language || '',
      zona,
      (scr.width || 0) + 'x' + (scr.height || 0),
      win.devicePixelRatio || 1,
      nav.hardwareConcurrency || 0,
      gl.vendor,
      gl.renderer,
      nav.maxTouchPoints || 0
    ];
  }

  function huella(lista) {
    var texto = lista.join('|');
    return 'fp.' + hex14(cyrb53(texto, 1)) + hex14(cyrb53(texto, 2));
  }

  // La dirección `ir` con los parámetros puestos (los vacíos no van). `base` resuelve las relativas.
  function conParametros(ir, valores, base) {
    var u = new URL(ir, base);
    Object.keys(valores).forEach(function (k) {
      if (valores[k]) u.searchParams.set(k, valores[k]);
    });
    return u.toString();
  }

  // { click_id, fingerprint }. Escribe la cookie _fbc cuando hay un fbc nuevo.
  function calculaValores(win) {
    var doc = win.document;
    var fp = huella(senales(win));
    var fbc = calculaFbc(win.location.search, leeCookie(doc, '_fbc'), Date.now());
    if (fbc && fbc.nuevo) {
      var segura = win.location.protocol === 'https:' ? '; Secure' : '';
      doc.cookie = '_fbc=' + encodeURIComponent(fbc.valor) + '; path=/; max-age=' +
        NOVENTA_DIAS + '; SameSite=Lax' + segura;
    }
    return { click_id: fbc ? fbc.valor : fp, fingerprint: fp };
  }

  var api = {
    calculaFbc: calculaFbc,
    huella: huella,
    senales: senales,
    conParametros: conParametros,
    calculaValores: calculaValores
  };

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = api;
    return;
  }

  // En el navegador: calcular y seguir a /c/<slug>/ir, que guarda el clic y abre el destino.
  var guion = root.document.currentScript;
  var ir = guion && guion.getAttribute('data-ir');
  if (!ir) return;
  root.CentauroClickId = api;
  var salida = ir;
  try {
    var v = calculaValores(root);
    // La procedencia real la ve esta página; en /ir la cabecera Referer ya sería esta misma.
    v.ref = (root.document.referrer || '').slice(0, 1000);
    // Los parámetros con los que se llamó al link (utm_*, fbclid…): /ir los reenvía al destino.
    v.q = (root.location.search || '').replace(/^\?/, '');
    salida = conParametros(ir, v, root.location.href);
  } catch (e) { /* si algo falla, al destino igual (sin valores): nunca un enlace roto */ }
  root.__clickIdListo = true;
  root.location.replace(salida);
})(typeof window !== 'undefined' ? window : this);
