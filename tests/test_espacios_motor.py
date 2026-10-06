"""
El motor con espacios propios de una entrega (especificación 004, T407, T409, T415).

Lo que se fija aquí:

- Un estado guardado de antes de la 004 (sin `incluidos` ni `espacios`) sobrevive a `normaliza()`
  e `incluidos` sale de los servicios encendidos, que es lo que la H enseñaba hasta ahora.
- En la H, cada espacio usa lo suyo de `bloques.entrega.espacios` (carrusel, enlace, nombre,
  cobertura) y los demás el estándar; con el MISMO estado, A–G salen con el catálogo.
- `incluidos` decide qué espacios lleva la H; A–G siguen con el `on` global.
- El texto plano y WhatsApp de la H usan lo propio; el estado de la persona no se toca.
- Una línea cuyo catálogo la limita a otras plantillas sigue fuera de la H aunque tenga carrusel.

Cada escenario corre en su propio proceso de Node, porque `ponCatalogo` cambia el motor cargado.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

MOTOR = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "render.js"

CARRUSEL = "https://x.test/c.gif"
CANVA_LED = "https://canva.link/led-de-esta-entrega"
NOMBRE_LED = "LED PARA ESTE CLIENTE"
COBERTURA_LED = "COBERTURA PARA ESTE CLIENTE"

GUION = r"""
const M = require(process.argv[2]);
const escenario = process.argv[3];
const copia = o => JSON.parse(JSON.stringify(o));
// Las fotos de un correo, como [src, alt]: asi se sabe de que espacio es cada una.
const fotos = html => { const r = /<img src="([^"]+)"[^>]* alt="([^"]*)"/g, o = []; let m;
  while ((m = r.exec(html))) o.push([m[1], m[2]]); return o; };
const conEspacios = () => {
  const st = M.defaultState(); st.cardAnim = true;
  st.bloques.entrega.espacios = {
    mercedes: { carrusel: 'CARRUSEL' },
    led: { canva: 'CANVA_LED', nombre: 'NOMBRE_LED', cobertura: 'COBERTURA_LED' },
  };
  return st;
};
const out = {};
if (escenario === 'viejo') {
  // Una sesion guardada antes de la 004: sin incluidos ni espacios, con un servicio apagado.
  const vieja = M.defaultState();
  delete vieja.bloques.entrega.incluidos; delete vieja.bloques.entrega.espacios;
  vieja.servicios.find(s => s.id === 'totem').on = false;
  const st = M.normaliza(copia(vieja));
  out.incluidos = st.bloques.entrega.incluidos;
  out.espacios = st.bloques.entrega.espacios;
  out.encendidos = st.servicios.filter(s => s.on).map(s => s.id);
  out.porDefecto = M.defaultState().bloques.entrega;
  // Sin entrega guardada, la H sale igual que antes: los encendidos, con el carrusel de serie.
  const h = copia(vieja); h.plantilla = 'H'; h.cardAnim = true;
  out.hViejo = M.render(h, 'H');
  // Los ids que la persona ya tenia se respetan aunque no existan (la H no los encontrara).
  const conRetirado = M.defaultState(); conRetirado.bloques.entrega.incluidos = ['led', 'retirado'];
  conRetirado.bloques.entrega.espacios = { retirado: { nombre: 'X' } };
  const n = M.normaliza(copia(conRetirado));
  out.retiradoIncluidos = n.bloques.entrega.incluidos;
  out.retiradoEspacios = n.bloques.entrega.espacios;
  conRetirado.plantilla = 'H';
  out.hRetirado = M.render(conRetirado, 'H');
} else if (escenario === 'propios') {
  const st = conEspacios(); st.plantilla = 'H';
  const antes = JSON.stringify(st);
  out.h = M.render(st, 'H');
  out.hFotos = fotos(out.h);
  out.textoH = M.renderText(st);
  out.waH = M.renderWhatsApp(st);
  out.estadoIntacto = JSON.stringify(st) === antes;
  out.otras = {};
  ['A', 'B', 'D'].forEach(k => { const s = conEspacios(); s.plantilla = k; out.otras[k] = M.render(s, k); });
  const a = conEspacios(); a.plantilla = 'A'; out.textoA = M.renderText(a);
  out.alts = {}; M.defaultState().servicios.forEach(s => { out.alts[s.id] = s.alt; });
  out.estandar = {}; M.defaultState().servicios.forEach(s => { out.estandar[s.id] = s; });
} else if (escenario === 'incluidos') {
  const st = M.defaultState(); st.cardAnim = true; st.plantilla = 'H';
  st.bloques.entrega.incluidos = ['led'];
  const antes = JSON.stringify(st);
  out.h = M.render(st, 'H');
  out.textoH = M.renderText(st);
  out.estadoIntacto = JSON.stringify(st) === antes;
  const a = copia(st); a.plantilla = 'A';
  out.a = M.render(a, 'A');
  out.textoA = M.renderText(a);
  out.nombres = {}; M.defaultState().servicios.forEach(s => { out.nombres[s.id] = s.nombre; });
} else if (escenario === 'limitada') {
  // El totem se limita a A y B en el catalogo: con carrusel propio, la H sigue sin el.
  const cat = M.catalogoActual();
  cat.lineas.find(l => l.id === 'totem').plantillas = 'AB';
  M.ponCatalogo(cat);
  const st = M.defaultState(); st.cardAnim = true; st.plantilla = 'H';
  st.bloques.entrega.espacios = { totem: { carrusel: 'CARRUSEL' } };
  out.h = M.render(st, 'H');
  out.textoH = M.renderText(st);
  out.totem = M.defaultState().servicios.find(s => s.id === 'totem').nombre;
}
process.stdout.write(JSON.stringify(out));
"""


def _corre(tmp_path_factory, escenario):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("esp") / "_e.js"
    texto = (GUION.replace("'CARRUSEL'", json.dumps(CARRUSEL))
             .replace("'CANVA_LED'", json.dumps(CANVA_LED))
             .replace("'NOMBRE_LED'", json.dumps(NOMBRE_LED))
             .replace("'COBERTURA_LED'", json.dumps(COBERTURA_LED)))
    guion.write_text(texto, encoding="utf-8")
    r = subprocess.run(["node", str(guion), str(MOTOR), escenario],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert r.returncode == 0, "el motor falló:\n" + r.stderr
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def viejo(tmp_path_factory):
    return _corre(tmp_path_factory, "viejo")


@pytest.fixture(scope="module")
def propios(tmp_path_factory):
    return _corre(tmp_path_factory, "propios")


@pytest.fixture(scope="module")
def incluidos(tmp_path_factory):
    return _corre(tmp_path_factory, "incluidos")


@pytest.fixture(scope="module")
def limitada(tmp_path_factory):
    return _corre(tmp_path_factory, "limitada")


# --- Estado guardado de antes de la 004 (T407) ---------------------------------------------------

def test_el_estado_por_defecto_trae_espacios_e_incluidos(viejo):
    e = viejo["porDefecto"]
    assert e["espacios"] == {}
    assert e["incluidos"] == ["vallas", "led", "mercedes", "totem", "rider"]


def test_un_estado_viejo_sobrevive_e_incluidos_sale_de_los_encendidos(viejo):
    assert viejo["espacios"] == {}
    assert viejo["incluidos"] == viejo["encendidos"]
    assert "totem" not in viejo["incluidos"]


def test_un_estado_viejo_sale_en_la_h_como_antes(viejo):
    h = viejo["hViejo"]
    assert "carousel_led_" in h and "carousel_mercedes_" in h
    assert "carousel_totem_" not in h


def test_los_ids_guardados_se_conservan_aunque_no_existan(viejo):
    assert viejo["retiradoIncluidos"] == ["led", "retirado"]
    assert viejo["retiradoEspacios"] == {"retirado": {"nombre": "X"}}
    assert "carousel_led_" in viejo["hRetirado"]
    assert "carousel_vallas_" not in viejo["hRetirado"]


# --- Carrusel propio solo en la H (T409) ---------------------------------------------------------

def test_la_h_usa_el_carrusel_propio_en_ese_espacio(propios):
    del_espacio = [f for f in propios["hFotos"] if f[0] == CARRUSEL]
    assert del_espacio == [[CARRUSEL, propios["alts"]["mercedes"]]]
    assert "carousel_mercedes_" not in propios["h"]


def test_los_demas_espacios_de_la_h_siguen_con_el_estandar(propios):
    for sid in ("vallas", "led", "totem", "rider"):
        assert "carousel_" + sid + "_barrido.gif" in propios["h"], sid


@pytest.mark.parametrize("k", ["A", "B", "D"])
def test_con_el_mismo_estado_las_otras_salen_estandar(propios, k):
    html = propios["otras"][k]
    assert CARRUSEL not in html
    assert CANVA_LED not in html and NOMBRE_LED not in html and COBERTURA_LED not in html
    assert propios["estandar"]["led"]["canva"] in html


# --- Enlace, nombre y cobertura propios; incluidos (T415) ----------------------------------------

def test_la_h_lleva_el_enlace_nombre_y_cobertura_propios(propios):
    h = propios["h"]
    assert CANVA_LED in h and NOMBRE_LED in h and COBERTURA_LED in h
    assert propios["estandar"]["led"]["nombre"] not in h


def test_texto_y_whatsapp_de_la_h_usan_lo_propio(propios):
    t = propios["textoH"]
    assert NOMBRE_LED in t and CANVA_LED in t and COBERTURA_LED in t
    assert NOMBRE_LED not in propios["textoA"] and CANVA_LED not in propios["textoA"]
    # WhatsApp solo lleva el enlace de la entrega: lo propio de un espacio no se cuela.
    assert CANVA_LED not in propios["waH"]


def test_el_estado_de_la_persona_no_se_modifica(propios, incluidos):
    assert propios["estadoIntacto"] is True
    assert incluidos["estadoIntacto"] is True


def test_incluidos_decide_los_espacios_de_la_h(incluidos):
    h, t = incluidos["h"], incluidos["textoH"]
    assert "carousel_led_" in h and incluidos["nombres"]["led"] in t
    for sid in ("vallas", "mercedes", "totem", "rider"):
        assert "carousel_" + sid + "_" not in h, sid
        assert incluidos["nombres"][sid] not in t, sid


def test_a_sigue_con_el_on_global(incluidos):
    for sid in ("vallas", "led", "mercedes", "totem", "rider"):
        assert "carousel_" + sid + "_" in incluidos["a"], sid
        assert incluidos["nombres"][sid] in incluidos["textoA"], sid


def test_una_linea_limitada_a_otras_plantillas_sigue_fuera_de_la_h(limitada):
    assert CARRUSEL not in limitada["h"]
    assert "carousel_totem_" not in limitada["h"]
    assert limitada["totem"] not in limitada["textoH"]
    assert "carousel_led_" in limitada["h"]
