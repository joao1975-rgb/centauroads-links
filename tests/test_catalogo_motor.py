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
} else if (escenario === 'edicion') {
  // Lo que el panel edita llega a quien ya uso el compositor, sin pisar lo escrito a mano (US3).
  const copia = o => JSON.parse(JSON.stringify(o));
  const vieja = M.defaultState();
  vieja.servicios.find(s => s.id === 'vallas').cobertura = 'MI TEXTO A MANO';
  const sinVisto = copia(vieja); delete sinVisto.catalogoVisto;   // sesion de antes de la 003
  const cat = M.catalogoActual();
  cat.lineas.find(l => l.id === 'led').nombre = 'LED EDITADA EN EL PANEL';
  cat.lineas.find(l => l.id === 'vallas').cobertura = 'COBERTURA DEL PANEL';
  const rider = cat.lineas.splice(cat.lineas.findIndex(l => l.id === 'rider'), 1)[0];
  cat.lineas.unshift(rider);                                      // reordenada: rider primero
  M.ponCatalogo(cat);
  const st = M.normaliza(copia(vieja));
  out.led = st.servicios.find(s => s.id === 'led').nombre;
  out.vallas = st.servicios.find(s => s.id === 'vallas').cobertura;
  out.ids = st.servicios.map(s => s.id);
  out.ledSinVisto = M.normaliza(sinVisto).servicios.find(s => s.id === 'led').nombre;
  // Segunda vuelta: la persona cambia a mano la cobertura de led; el panel la cambia otra vez,
  // y tambien el nombre. El nombre llega; la cobertura suya se queda.
  st.servicios.find(s => s.id === 'led').cobertura = 'LED A MANO';
  const cat2 = M.catalogoActual();
  cat2.lineas.find(l => l.id === 'led').nombre = 'LED OTRA VEZ';
  cat2.lineas.find(l => l.id === 'led').cobertura = 'COBERTURA OTRA VEZ';
  M.ponCatalogo(cat2);
  const st2 = M.normaliza(copia(st));
  out.led2 = st2.servicios.find(s => s.id === 'led').nombre;
  out.ledCobertura2 = st2.servicios.find(s => s.id === 'led').cobertura;
} else if (escenario === 'perfil') {
  // Un perfil con orden propio deja detras, en el orden del catalogo, las lineas que no nombra.
  const cat = M.catalogoActual();
  cat.lineas.unshift(Object.assign({}, NUEVA));
  M.ponCatalogo(cat);
  const st = M.defaultState(); st.perfil = 'agencia';
  out.orden = M.aplicaPerfil(M.normaliza(st)).servicios.map(s => s.id);
  out.ordenPerfil = M.PERFILES.agencia.orden;
} else if (escenario === 'ficha') {
  // Ficha tecnica opcional (US4): con ficha, fila en la tabla de agencias y en el inventario de E;
  // sin ficha, en ninguna. El precio "desde" solo con el modo de precios.
  const cat = M.catalogoActual();
  cat.lineas.push(Object.assign({}, NUEVA, { ficha: { ubic: 'UBIC-CON-FICHA', medida: 'MEDIDA-CON-FICHA',
    trafico: 'TRAFICO-CON-FICHA', desde: '987' } }));
  cat.lineas.push(Object.assign({}, NUEVA, { id: 'sinficha', nombre: 'LINEA-SIN-FICHA', ficha: null }));
  M.ponCatalogo(cat);
  const con = (k, pf, precios) => { const st = base(k, pf); if (precios) st.precios = 'desde'; return M.render(st, k); };
  out.agencias = con('A', 'agencia');
  out.agenciasPrecio = con('A', 'agencia', true);
  out.e = con('E', 'general');
  out.ePrecio = con('E', 'general', true);
} else if (escenario === 'familias') {
  // Familias de la D (US5): una existente, una nueva y sin familia («Otros servicios»).
  const cat = M.catalogoActual();
  const linea = (id, nombre, familia) => Object.assign({}, NUEVA, { id: id, nombre: nombre, familia: familia });
  cat.familias.push({ id: 'renta', eyebrow: 'Renta', titulo: 'FAMILIA-NUEVA-RENTA' });
  cat.lineas.push(linea('en-dooh', 'LINEA-EN-DOOH', 'dooh'));
  cat.lineas.push(linea('renta-1', 'LINEA-RENTA-1', 'renta'), linea('renta-2', 'LINEA-RENTA-2', 'renta'));
  cat.lineas.push(linea('suelta-1', 'LINEA-SUELTA-1', ''), linea('suelta-2', 'LINEA-SUELTA-2', 'no-existe'));
  M.ponCatalogo(cat);
  out.d = M.render(base('D', 'general'), 'D');
  // Una familia nueva con una sola linea: sale con el nombre de la linea, como las de serie.
  const cat2 = M.catalogoActual();
  cat2.lineas = cat2.lineas.filter(l => l.id !== 'renta-2');
  M.ponCatalogo(cat2);
  out.dUna = M.render(base('D', 'general'), 'D');
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


# --- Editar y ordenar desde el panel llega a las sesiones guardadas (US3, T324) ------------------

@pytest.fixture(scope="module")
def edicion(tmp_path_factory):
    return _corre(tmp_path_factory, "edicion")


def test_una_edicion_del_panel_llega_a_la_sesion_guardada(edicion):
    assert edicion["led"] == "LED EDITADA EN EL PANEL"


def test_lo_escrito_a_mano_no_lo_pisa_el_panel(edicion):
    assert edicion["vallas"] == "MI TEXTO A MANO"


def test_la_sesion_sigue_el_orden_del_catalogo(edicion):
    assert edicion["ids"][0] == "rider"


def test_una_sesion_anterior_a_la_003_tambien_recibe_la_edicion(edicion):
    assert edicion["ledSinVisto"] == "LED EDITADA EN EL PANEL"


def test_la_segunda_edicion_llega_y_respeta_lo_cambiado_entre_medias(edicion):
    assert edicion["led2"] == "LED OTRA VEZ"
    assert edicion["ledCobertura2"] == "LED A MANO"


def test_un_perfil_con_orden_propio_deja_detras_las_lineas_que_no_nombra(tmp_path_factory):
    r = _corre(tmp_path_factory, "perfil")
    assert r["orden"][:len(r["ordenPerfil"])] == r["ordenPerfil"]
    assert r["orden"][-1] == "alquiler"


# --- Ficha tecnica opcional (US4, T328) ----------------------------------------------------------

@pytest.fixture(scope="module")
def ficha(tmp_path_factory):
    return _corre(tmp_path_factory, "ficha")


def test_con_ficha_entra_en_la_tabla_de_agencias(ficha):
    assert "UBIC-CON-FICHA" in ficha["agencias"]
    assert "MEDIDA-CON-FICHA" in ficha["agencias"] and "TRAFICO-CON-FICHA" in ficha["agencias"]


def test_con_ficha_entra_en_el_inventario_de_la_e(ficha):
    assert "Alquiler de pantallas" in ficha["e"]
    assert "UBIC-CON-FICHA" in ficha["e"] and "TRAFICO-CON-FICHA" in ficha["e"]
    assert ">06<" in ficha["e"], "numerada detras de las cinco de serie"


def _tabla_agencias(html):
    """La tabla de disponibilidad del perfil agencia: de su cabecera «Espacio» a su cierre."""
    i = html.index(">Espacio</td>")
    return html[i:html.index("</table>", i)]


def test_sin_ficha_no_entra_en_ninguna_tabla(ficha):
    # Fuera de las tablas si sale, como cualquier linea («Tambien disponible» de la E, tarjetas).
    assert "LINEA-SIN-FICHA" not in _tabla_agencias(ficha["agencias"])
    assert "Alquiler de pantallas" in _tabla_agencias(ficha["agencias"])
    assert ">07<" not in ficha["e"], "la linea sin ficha no tiene fila en el inventario"


def test_el_precio_desde_solo_sale_con_el_modo_de_precios(ficha):
    assert "987" not in ficha["e"] and "987" not in ficha["agencias"]
    assert "987 $/mes" in ficha["ePrecio"]
    assert "987 $/mes" in ficha["agenciasPrecio"]


# --- Familias de la plantilla D (US5, T331) ------------------------------------------------------

@pytest.fixture(scope="module")
def familias(tmp_path_factory):
    return _corre(tmp_path_factory, "familias")


def test_una_linea_en_una_familia_existente_sale_dentro_de_ella(familias):
    d = familias["d"]
    dooh = d.index("Pantallas LED y Tótem (DOOH)")
    assert dooh < d.index("LINEA-EN-DOOH") < d.index("Publicidad móvil · Rider Clon")


def test_una_familia_nueva_sale_con_su_titulo_y_sus_lineas(familias):
    d = familias["d"]
    titulo = d.index("FAMILIA-NUEVA-RENTA")
    assert titulo < d.index("LINEA-RENTA-1") and titulo < d.index("LINEA-RENTA-2")


def test_sin_familia_va_a_otros_servicios(familias):
    d = familias["d"]
    otros = d.index("Otros servicios")
    assert otros < d.index("LINEA-SUELTA-1") and otros < d.index("LINEA-SUELTA-2")
    assert otros > d.index("FAMILIA-NUEVA-RENTA"), "Otros servicios va al final"


def test_una_familia_con_una_sola_linea_sale_con_el_nombre_de_la_linea(familias):
    assert "LINEA-RENTA-1" in familias["dUna"]
    assert "FAMILIA-NUEVA-RENTA" not in familias["dUna"]

