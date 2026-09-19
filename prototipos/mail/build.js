/*
 * build.js — genera los entregables del prototipo a partir de render.js:
 *   plantilla-A-cartelera.html / plantilla-B-catalogo.html / plantilla-C-nota.html
 *     (mail renderizado con el contenido por defecto; imágenes relativas a img/)
 *   compositor.standalone.html
 *     (compositor.html con render.js e imágenes embebidas como data URI,
 *      para publicarlo como Artifact o abrirlo sin servidor)
 * Uso: node build.js
 */
'use strict';
const fs = require('fs');
const path = require('path');
const M = require('./render.js');

const here = __dirname;
const imgDir = path.join(here, 'img');
const slug = { A: 'cartelera', B: 'catalogo', C: 'nota', D: 'movil' };

// 1. Plantillas estáticas: con fotos reales (por defecto) y con portadas de Canva (sufijo -portadas)
for (const key of Object.keys(M.TEMPLATES)) {
  for (const set of Object.keys(M.IMG_SETS)) {
    const st = M.defaultState();
    st.plantilla = key; st.imgSet = set;
    // Las imagenes ya estan publicadas: los HTML entregables apuntan a produccion (lo que vera Gmail).
    st.assetBase = st.assetBaseProd;
    const suffix = set === 'fotos' ? '' : '-' + set;
    const out = path.join(here, 'plantilla-' + key + '-' + slug[key] + suffix + '.html');
    fs.writeFileSync(out, M.render(st), 'utf8');
    console.log('OK', path.basename(out), fs.statSync(out).size, 'bytes');
  }
}

// 2. Compositor autónomo (render.js + imágenes embebidas)
const IMG_DATA = {};
for (const f of fs.readdirSync(imgDir)) {
  const ext = path.extname(f).slice(1).toLowerCase();
  if (!['png', 'jpg', 'jpeg', 'gif'].includes(ext)) continue;
  const mime = ext === 'png' ? 'image/png' : ext === 'gif' ? 'image/gif' : 'image/jpeg';
  IMG_DATA[f] = 'data:' + mime + ';base64,' + fs.readFileSync(path.join(imgDir, f)).toString('base64');
}
let html = fs.readFileSync(path.join(here, 'compositor.html'), 'utf8');
const renderSrc = fs.readFileSync(path.join(here, 'render.js'), 'utf8');
html = html.replace('<script src="render.js"></script>',
  '<script>window.IMG_DATA=' + JSON.stringify(IMG_DATA) + ';</script>\n<script>\n' + renderSrc + '\n</script>');
const out = path.join(here, 'compositor.standalone.html');
fs.writeFileSync(out, html, 'utf8');
console.log('OK', path.basename(out), Math.round(fs.statSync(out).size / 1024), 'KB');

// 3. Guardia de contenido: la construcción falla si reaparece un dato de contacto retirado, o si falta uno vigente.
const PROHIBIDO = ['412 000 0000', '412 1003559', 'www.centauroads.com', 'contacto@centauroads'];
const OBLIGATORIO = ['+58 412 100 3559', 'linktr.ee/centauroadss', 'mercadeo@centauroads.com'];
let fallos = 0;
for (const f of fs.readdirSync(here).filter(n => /^plantilla-.*\.html$/.test(n) || n === 'compositor.standalone.html')) {
  // Quitar la linea de la lista RETIRADOS del compositor: contiene esos valores a proposito (es el detector).
  const txt = fs.readFileSync(path.join(here, f), 'utf8').replace(/^\s*const RETIRADOS = \[.*$/m, '');
  for (const v of PROHIBIDO) if (txt.includes(v)) { console.error('FALLO', f, 'contiene dato retirado:', v); fallos++; }
  for (const v of OBLIGATORIO) if (!txt.includes(v)) { console.error('FALLO', f, 'no contiene:', v); fallos++; }
}
if (fallos) { console.error(fallos + ' fallo(s) de contenido. Corrige render.js (y sube CONTENT_VERSION).'); process.exit(1); }
console.log('OK guardia de contenido: contacto vigente en todos los entregables');

// 4. Versión publicable como página privada de Claude (Artifact): mismo compositor SIN el envoltorio exterior
//    (doctype/html/head/body), que la plataforma añade. OJO: quitar solo el envoltorio; el motor contiene
//    '<html>' y '<body>' dentro de cadenas JS y un reemplazo global lo rompería.
{
  const full = fs.readFileSync(path.join(here, 'compositor.standalone.html'), 'utf8');
  const i = full.indexOf('<title>'), j = full.indexOf('<script');
  if (i < 0 || j < i) { console.error('FALLO artifact: estructura inesperada'); process.exit(1); }
  const top = full.slice(i, j).replace(/<\/head>\s*/i, '').replace(/<body[^>]*>\s*/i, '');
  const tail = full.slice(j).replace(/\s*<\/body>\s*<\/html>\s*$/i, '\n');
  const art = top + tail;
  if (!art.includes("'<!DOCTYPE html><html lang=\"es\"><head>")) { console.error('FALLO artifact: se dañó el motor'); process.exit(1); }
  fs.writeFileSync(path.join(here, 'compositor.artifact.html'), art, 'utf8');
  console.log('OK compositor.artifact.html', Math.round(art.length / 1024), 'KB (publicar con Artifact url=cc5618a8-…)');
}
