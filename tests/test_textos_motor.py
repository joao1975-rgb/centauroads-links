"""
El motor con los textos de los perfiles que llegan del servidor (especificación 005).

`ponTextos()` aplica en sitio los textos cambiados sobre los de serie. Lo que se fija aquí:

- Los textos de serie salen del propio motor (`textosActuales()`), con clave estable, y `build.js` los
  exporta tal cual a `textos-perfil-serie.json`: una sola fuente (R1).
- Sin cambios, o con los de serie, los correos no cambian (FR-511). `ponTextos({})` devuelve el motor a
  como estaba (volver al de serie sin recargar).
- Un texto cambiado sale en los correos de su perfil y en ningún otro (SC-503).
- Los marcadores `{destinatario}` y `{empresa}` funcionan en los textos del perfil (FR-509), y un texto
  nunca se interpreta como HTML (FR-510).
- Los tres asuntos conservan clave y etiqueta; solo cambia el texto (FR-502).

Cada escenario corre en su propio proceso de Node, porque `ponTextos` cambia el motor cargado.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MOTOR = RAIZ / "prototipos" / "mail" / "render.js"
SERIE = RAIZ / "app" / "static" / "email" / "textos-perfil-serie.json"

# El asunto propio del perfil no se ofrece: uno de los tres asuntos siempre lo sustituye (y el que
# escribe quien redacta manda sobre todos), asi que editarlo no cambiaria ningun correo.
CAMPOS = ["preheader", "titulo", "sub", "intro", "cierre", "cta"]
CLAVES_MVP = ({"%s.%s" % (p, c) for p in ("agencia", "nuevo", "phygital") for c in CAMPOS}
              | {"%s.asunto.%s" % (p, a) for p in ("general", "agencia", "nuevo", "phygital")
                 for a in ("directo", "beneficio", "curiosidad")})

GUION = r"""
const M = require(process.argv[2]);
const escenario = process.argv[3];
const PLANTILLAS = Object.keys(M.TEMPLATES).filter(k => k !== 'H'), PERFILES = Object.keys(M.PERFILES);
const base = (k, pf) => { const st = M.defaultState(); st.plantilla = k; st.perfil = pf; return st; };
const todos = () => { const o = {}; PERFILES.forEach(pf => PLANTILLAS.forEach(k => {
  const st = base(k, pf); o[k + '/' + pf] = { html: M.render(st, k), texto: M.renderText(st) }; })); return o; };
const out = {};
if (escenario === 'serie') {
  out.textos = M.textosActuales();
  out.antes = todos();
  out.vacio = M.ponTextos({});
  out.trasVacio = todos();
  const deSerie = {}; out.textos.forEach(t => { deSerie[t.clave] = t.valor; });
  M.ponTextos(deSerie);
  out.trasSerie = todos();
} else if (escenario === 'mensaje') {
  out.antes = todos();
  out.puestos = M.ponTextos({ 'agencia.titulo': 'TITULO NUEVO X', 'agencia.cta': 'BOTON NUEVO Y' });
  out.despues = todos();
  out.serieIntacta = M.textosActuales().filter(t => t.clave === 'agencia.titulo')[0].valor;
  M.ponTextos({});
  out.vuelta = todos();
} else if (escenario === 'marcadores') {
  M.ponTextos({ 'agencia.asunto.directo': 'Asunto para {empresa}', 'agencia.preheader': 'Previo {destinatario}',
    'agencia.titulo': 'Titulo {empresa}', 'agencia.sub': 'Sub {destinatario}', 'agencia.intro': 'Entrada {empresa}',
    'agencia.cierre': 'Cierre {destinatario}', 'agencia.cta': 'Boton {empresa}' });
  const st = base('A', 'agencia'); st.destinatario = 'Ana Prueba';
  st.bloques.entrega.empresa = 'Empresa Prueba';
  out.html = M.render(st, 'A'); out.texto = M.renderText(st);
} else if (escenario === 'propio') {
  const st = base('A', 'agencia'); st.asunto3 = 'propio'; st.asunto = 'Mi asunto escrito a mano';
  out.html = M.render(st, 'A');
} else if (escenario === 'escape') {
  M.ponTextos({ 'agencia.titulo': 'Uno <b>dos</b>', 'agencia.cta': '<script>x()</script>' });
  out.html = M.render(base('A', 'agencia'), 'A');
} else if (escenario === 'asuntos') {
  M.ponTextos({ 'general.asunto.curiosidad': 'CURIOSO 🎯 nuevo para {empresa}' });
  out.lista = M.asuntosDe(base('A', 'general'));
  out.otros = M.asuntosDe(base('A', 'agencia'));
  const st = base('A', 'general'); st.asunto3 = 'curiosidad';
  out.html = M.render(st, 'A');
} else if (escenario === 'basura') {
  out.antes = todos();
  out.puestos = M.ponTextos({ 'no.existe': 'x', 'agencia.titulo': '   ', 'agencia.cta': 42, constructor: 'x' });
  out.despues = todos();
  out.nulo = M.ponTextos(null);
}
process.stdout.write(JSON.stringify(out));
"""


def _corre(tmp_path_factory, escenario):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("txt") / "_t.js"
    guion.write_text(GUION, encoding="utf-8")
    r = subprocess.run(["node", str(guion), str(MOTOR), escenario],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert r.returncode == 0, "el motor falló:\n" + r.stderr
    return json.loads(r.stdout)


@pytest.fixture(scope="module")
def serie(tmp_path_factory):
    return _corre(tmp_path_factory, "serie")


# --- Los textos de serie: una sola fuente ---------------------------------------------------------

def test_los_textos_de_serie_tienen_clave_estable_y_todo_lo_que_pide_la_pantalla(serie):
    textos = serie["textos"]
    assert {t["clave"] for t in textos} == CLAVES_MVP
    assert len(textos) == len(CLAVES_MVP)
    for t in textos:
        assert t["perfil"] == t["clave"].split(".")[0]
        assert t["grupo"] in ("Mensaje", "Asuntos")
        assert t["etiqueta"] and t["valor"].strip(), t
        assert isinstance(t["limite"], int) and len(t["valor"]) <= t["limite"], t


def test_build_exporta_los_textos_de_serie_tal_cual(serie):
    exportado = json.loads(SERIE.read_text(encoding="utf-8"))
    assert exportado["textos"] == serie["textos"]
    assert {p["id"] for p in exportado["perfiles"]} == {"general", "agencia", "nuevo", "phygital"}


def test_sin_cambios_o_con_los_de_serie_los_correos_no_cambian(serie):
    assert serie["vacio"] == 0
    assert serie["trasVacio"] == serie["antes"]
    assert serie["trasSerie"] == serie["antes"]


# --- Un texto cambiado sale en su perfil y en ningún otro ----------------------------------------

def _cambia(s, viejo, nuevo):
    """Lo que el correo deberia ser con el texto nuevo: tambien donde va codificado (el asunto del botón)."""
    from urllib.parse import quote
    return s.replace(viejo, nuevo).replace(quote(viejo, safe=""), quote(nuevo, safe=""))


def test_el_titulo_y_el_boton_cambiados_salen_en_su_perfil_y_en_ningun_otro(tmp_path_factory):
    r = _corre(tmp_path_factory, "mensaje")
    assert r["puestos"] == 2
    for clave, antes in r["antes"].items():
        despues = r["despues"][clave]
        if clave.endswith("/agencia"):
            for forma in ("html", "texto"):
                esperado = _cambia(_cambia(antes[forma], "Inventario disponible", "TITULO NUEVO X"),
                                   "Pedir tarifas y disponibilidad", "BOTON NUEVO Y")
                esperado = _cambia(esperado, "INVENTARIO DISPONIBLE", "TITULO NUEVO X")
                assert despues[forma] == esperado, clave + " " + forma
            if "Inventario disponible" in antes["html"]:  # la C (Nota) no lleva titulo
                assert "TITULO NUEVO X" in despues["html"], clave
        else:
            assert despues == antes, clave
    # Lo de serie sigue siendo lo de serie, y volver a él deja los correos como estaban.
    assert r["serieIntacta"] == "Inventario disponible"
    assert r["vuelta"] == r["antes"]


def test_los_marcadores_se_sustituyen_en_todos_los_textos_del_perfil(tmp_path_factory):
    r = _corre(tmp_path_factory, "marcadores")
    html, texto = r["html"], r["texto"]
    for esperado in ("Asunto para Empresa Prueba", "Previo Ana Prueba", "Titulo Empresa Prueba",
                     "Sub Ana Prueba", "Entrada Empresa Prueba", "Cierre Ana Prueba", "Boton Empresa Prueba"):
        assert esperado in html, esperado
    assert "{empresa}" not in html and "{destinatario}" not in html
    assert "{empresa}" not in texto and "{destinatario}" not in texto


def test_el_asunto_escrito_a_mano_manda_tambien_con_un_perfil(tmp_path_factory):
    """Antes el perfil lo pisaba con su asunto propio: quien redacta no tenia la ultima palabra."""
    html = _corre(tmp_path_factory, "propio")["html"]
    assert "<title>Mi asunto escrito a mano</title>" in html


def test_un_texto_nunca_se_interpreta_como_html(tmp_path_factory):
    html = _corre(tmp_path_factory, "escape")["html"]
    assert "Uno &lt;b&gt;dos&lt;/b&gt;" in html and "<b>dos</b>" not in html
    assert "<script>" not in html


def test_lo_que_no_es_un_texto_valido_no_cambia_nada(tmp_path_factory):
    r = _corre(tmp_path_factory, "basura")
    assert r["puestos"] == 0 and r["nulo"] == 0
    assert r["despues"] == r["antes"]


# --- Los tres asuntos -----------------------------------------------------------------------------

def test_un_asunto_cambiado_conserva_clave_y_etiqueta_y_el_emoji(tmp_path_factory):
    r = _corre(tmp_path_factory, "asuntos")
    curiosidad = [a for a in r["lista"] if a["clave"] == "curiosidad"][0]
    assert curiosidad == {"clave": "curiosidad", "etiqueta": "Curiosidad", "texto": "CURIOSO 🎯 nuevo para {empresa}"}
    assert [a["clave"] for a in r["lista"]] == ["directo", "beneficio", "curiosidad"]
    assert "CURIOSO" not in json.dumps(r["otros"], ensure_ascii=False)
    # Elegido en el compositor, va al correo, con el marcador sustituido.
    assert "<title>CURIOSO 🎯 nuevo para tu marca</title>" in r["html"]
