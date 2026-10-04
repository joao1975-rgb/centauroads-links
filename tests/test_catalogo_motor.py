"""
El motor con un catálogo de líneas de negocio que llega del servidor (especificación 003).

`ponCatalogo()` reemplaza en sitio el catálogo de serie. Lo que se fija aquí:

- Sin catálogo del servidor, o con el catálogo de serie, los correos no cambian (SC-303).
- Una línea nueva sale en las ocho plantillas y los cuatro perfiles con su nombre, su foto, su texto
  alternativo y su enlace (US1); sin foto, no deja una imagen rota (FR-315).
- Una línea limitada a algunas plantillas sale en esas y en ninguna otra, también en el texto plano
  y en WhatsApp, sin tocar el estado de la persona (US2, SC-302).
- El estado guardado viejo incorpora la línea nueva, pierde la retirada y conserva lo escrito a mano
  (FR-321).

Cada escenario corre en su propio proceso de Node, porque `ponCatalogo` cambia el motor cargado.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

MOTOR = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "render.js"
FOTO = "https://mails.centauroads.com/media/lineas/alquiler-1a2b3c4d.jpg"

GUION = r"""
const M = require(process.argv[2]);
const escenario = process.argv[3];
const PLANTILLAS = Object.keys(M.TEMPLATES), PERFILES = Object.keys(M.PERFILES);
const NUEVA = { id: 'alquiler', nombre: 'Alquiler de pantallas', eyebrow: 'Renta de equipos',
  cta: 'Cotizar alquiler', cobertura: 'Eventos en todo el país', nota: 'Con operador', slug: '',
  canva: 'https://canva.link/alquiler-prueba', img: 'FOTO', alt: 'Pantalla de alquiler en un evento',
  cover: '', altCover: '', ficha: null, familia: '', plantillas: 'ABCDEFGH' };
NUEVA.img = process.argv[4];
const base = (k, pf) => { const st = M.defaultState(); st.plantilla = k; st.perfil = pf; st.cardAnim = true; return st; };
const todos = () => { const o = {}; PERFILES.forEach(pf => PLANTILLAS.forEach(k => {
  if (k === 'H' && pf !== 'general') return; o[k + '/' + pf] = M.render(base(k, pf), k); })); return o; };
const out = {};
if (escenario === 'serie') {
  out.antes = todos();
  out.puesto = M.ponCatalogo(M.catalogoActual());
  out.despues = todos();
} else if (escenario === 'nueva' || escenario === 'sinfoto') {
  const cat = M.catalogoActual();
  const n = Object.assign({}, NUEVA); if (escenario === 'sinfoto') n.img = '';
  cat.lineas.push(n); M.ponCatalogo(cat);
  out.correos = todos();
} else if (escenario === 'ah') {
  const cat = M.catalogoActual();
  cat.lineas.push(Object.assign({}, NUEVA, { plantillas: 'AH' })); M.ponCatalogo(cat);
  out.correos = todos();
  const st = base('B', 'general'); const antes = JSON.stringify(st);
  out.textoB = M.renderText(st); out.waB = M.renderWhatsApp(st);
  out.textoA = M.renderText(base('A', 'general'));
  M.render(st, 'B'); out.estadoIntacto = JSON.stringify(st) === antes;
} else if (escenario === 'migracion') {
  const vieja = M.defaultState();   // guardada con el catalogo de serie
  vieja.servicios.find(s => s.id === 'vallas').cobertura = 'MI TEXTO A MANO';
  const cat = M.catalogoActual();
  cat.lineas = cat.lineas.filter(l => l.id !== 'rider');   // retirada
  cat.lineas.push(Object.assign({}, NUEVA));                // nueva
  M.ponCatalogo(cat);
  const st = M.normaliza(JSON.parse(JSON.stringify(vieja)));
  out.ids = st.servicios.map(s => s.id);
  out.cobertura = st.servicios.find(s => s.id === 'vallas').cobertura;
}
process.stdout.write(JSON.stringify(out));
"""


def _corre(tmp_path_factory, escenario, foto=FOTO):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("cat") / "_c.js"
    guion.write_text(GUION, encoding="utf-8")
    r = subprocess.run(["node", str(guion), str(MOTOR), escenario, foto],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert r.returncode == 0, "el motor falló:\n" + r.stderr
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def serie(tmp_path_factory):
    return _corre(tmp_path_factory, "serie")


@pytest.fixture(scope="module")
def nueva(tmp_path_factory):
    return _corre(tmp_path_factory, "nueva")


@pytest.fixture(scope="module")
def sinfoto(tmp_path_factory):
    return _corre(tmp_path_factory, "sinfoto")


@pytest.fixture(scope="module")
def ah(tmp_path_factory):
    return _corre(tmp_path_factory, "ah")


@pytest.fixture(scope="module")
def migracion(tmp_path_factory):
    return _corre(tmp_path_factory, "migracion")


# --- Sin catálogo nuevo, nada cambia (SC-303) ----------------------------------------------------

def test_el_catalogo_de_serie_no_cambia_ningun_correo(serie):
    assert serie["puesto"] is True
    assert set(serie["antes"]) == set(serie["despues"])
    distintos = [k for k in serie["antes"] if serie["antes"][k] != serie["despues"][k]]
    assert distintos == [], "cambian: %s" % distintos


# --- Una línea nueva sale con todo lo suyo (US1) -------------------------------------------------

def test_la_linea_nueva_sale_en_las_ocho_plantillas_y_cuatro_perfiles(nueva):
    faltan = [k for k, html in nueva["correos"].items() if "Alquiler de pantallas" not in html]
    assert faltan == [], "no sale en: %s" % faltan


def test_sale_con_su_foto_su_alt_y_su_enlace(nueva):
    for k, html in nueva["correos"].items():
        assert FOTO in html, k + ": falta la foto"
        assert "Pantalla de alquiler en un evento" in html, k + ": falta el texto alternativo"
        assert "canva.link/alquiler-prueba" in html, k + ": falta el enlace"


def test_una_linea_nueva_no_pide_un_gif_que_no_existe(nueva):
    for k, html in nueva["correos"].items():
        assert "carousel_alquiler" not in html, k


def test_sin_foto_no_hay_imagen_rota(sinfoto):
    for k, html in sinfoto["correos"].items():
        assert "Alquiler de pantallas" in html, k
        assert 'src="img/"' not in html and 'src="https://links.centauroads.com/static/email/"' not in html, k
        assert 'alt="Pantalla de alquiler en un evento"' not in html, k


# --- Solo en las plantillas marcadas (US2, SC-302) -----------------------------------------------

def test_una_linea_en_ah_sale_solo_en_a_y_h(ah):
    for clave, html in ah["correos"].items():
        plantilla = clave.split("/")[0]
        esta = "Alquiler de pantallas" in html
        assert esta == (plantilla in "AH"), "%s: %s" % (clave, "sale y no debería" if esta else "no sale")


def test_tambien_en_el_texto_plano_y_whatsapp(ah):
    assert "Alquiler de pantallas" not in ah["textoB"]
    assert "Alquiler de pantallas" not in ah["waB"]
    assert "Alquiler de pantallas" in ah["textoA"]


def test_el_estado_de_la_persona_no_se_toca(ah):
    assert ah["estadoIntacto"] is True


# --- El estado guardado se migra sin perder lo escrito a mano (FR-321) ---------------------------

def test_la_sesion_vieja_recibe_la_nueva_pierde_la_retirada_y_conserva_lo_suyo(migracion):
    assert "alquiler" in migracion["ids"]
    assert "rider" not in migracion["ids"]
    assert migracion["cobertura"] == "MI TEXTO A MANO"
