"""
El estilo de los títulos en el motor (especificación 007).

- La pareja de tipografías (centauro · impacto · editorial · moderna) cambia título y texto de todo el
  correo; sin elegir nada, o con «centauro», los correos son los de hoy (FR-706).
- El título principal va en mayúsculas con Impacto y en itálica con Editorial.
- El tamaño del título principal es ×1 / ×1,25 / ×1,5 sobre el de cada plantilla y, si la palabra más
  larga no cabe en 327 px, baja lo justo sin bajar del base (FR-703, FR-704).
- Texto plano y WhatsApp no cambian (FR-708).
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

MOTOR = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "render.js"
BASES = {"A": 54, "B": 48, "D": 46, "E": 40, "F": 36, "G": 40, "H": 34}
PILAS = {
    "impacto": ("Impact,", "Georgia,"),
    "editorial": ("Georgia,", "Arial,Helvetica,sans-serif"),
    "moderna": ("'Arial Black'", "Verdana,"),
}
DE_HOY = ("'Montserrat'", "'Segoe UI'", "'DIN Condensed'")

GUION = r"""
const M = require(process.argv[2]);
const esc = process.argv[3];
const PL = 'ABCDEFGH'.split('');
const base = (k, extra) => {
  const st = M.defaultState(); st.plantilla = k; st.perfil = 'general';
  return Object.assign(st, extra || {});
};
// Pone el mismo titulo en el sitio de donde lo saca cada plantilla.
const conTitulo = (st, t) => {
  st.bloques.titulo.texto = t; st.bloques.inventario.titulo = t; st.bloques.guia.titulo = t;
  st.bloques.phygital.titulo = t; st.bloques.entrega.titulo = t; return st;
};
const out = {};
if (esc === 'serie') {
  PL.forEach(k => { out[k] = { hoy: M.render(base(k), k),
    explicito: M.render(base(k, { tipografia: 'centauro', tamTitulo: 'base' }), k),
    rara: M.render(base(k, { tipografia: 'no-existe', tamTitulo: 'enorme' }), k) }; });
} else if (esc === 'parejas') {
  ['impacto', 'editorial', 'moderna'].forEach(p => PL.forEach(k => {
    const st = conTitulo(base(k, { tipografia: p }), 'Titulo Prueba Unico');
    out[p + '/' + k] = { html: M.render(st, k), texto: M.renderText(st), wa: M.renderWhatsApp(st) };
  }));
  // Lo de despues no hereda la pareja: el motor la devuelve al terminar.
  out.despues = M.render(base('A'), 'A'); out.hoyA = out.despues;
  out.textoHoy = M.renderText(conTitulo(base('A'), 'Titulo Prueba Unico'));
  out.waHoy = M.renderWhatsApp(conTitulo(base('A'), 'Titulo Prueba Unico'));
} else if (esc === 'tamanos') {
  ['base', 'grande', 'maximo'].forEach(t => PL.forEach(k => {
    const st = conTitulo(base(k, { tamTitulo: t }), 'Hola');
    out[t + '/' + k] = { html: M.render(st, k), calc: M.tamanoTitulo(st, k) };
  }));
} else if (esc === 'ajuste') {
  ['centauro', 'impacto', 'editorial', 'moderna'].forEach(p => ['A', 'H'].forEach(k => {
    const st = conTitulo(base(k, { tipografia: p, tamTitulo: 'maximo' }), 'Supercalifragilisticoso');
    out[p + '/' + k] = { html: M.render(st, k), calc: M.tamanoTitulo(st, k) };
  }));
}
process.stdout.write(JSON.stringify(out));
"""


def _corre(tmp_path_factory, escenario):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible")
    guion = tmp_path_factory.mktemp("estilo") / "_e.js"
    guion.write_text(GUION, encoding="utf-8")
    r = subprocess.run(["node", str(guion), str(MOTOR), escenario],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    assert r.returncode == 0, "el motor falló:\n" + r.stderr
    return json.loads(r.stdout)


def _estilo_del_titulo(html, texto):
    """El style del elemento cuyo contenido empieza por el título."""
    m = re.search(r'style="([^"]*)">' + re.escape(texto), html)
    assert m, "no encuentro el título %r" % texto
    return m.group(1)


# --- Sin elección, todo como hoy -----------------------------------------------------------------

def test_sin_eleccion_o_con_centauro_y_base_los_correos_son_los_de_hoy(tmp_path_factory):
    r = _corre(tmp_path_factory, "serie")
    for k, v in r.items():
        assert v["explicito"] == v["hoy"], k
        assert v["rara"] == v["hoy"], k   # un valor desconocido se trata como el de hoy


# --- La pareja de tipografías ----------------------------------------------------------------------

def test_cada_pareja_cambia_titulo_y_texto_de_todo_el_correo(tmp_path_factory):
    r = _corre(tmp_path_factory, "parejas")
    for p, (titulo, texto) in PILAS.items():
        for k in "ABCDEFGH":
            html = r[p + "/" + k]["html"]
            assert titulo in html and texto in html, (p, k)
            for vieja in DE_HOY:
                assert vieja not in html, (p, k, vieja)
    assert r["despues"] == r["hoyA"]


def test_el_titulo_principal_lleva_el_estilo_de_su_pareja(tmp_path_factory):
    r = _corre(tmp_path_factory, "parejas")
    for k in BASES:
        assert "text-transform:uppercase" in _estilo_del_titulo(r["impacto/" + k]["html"], "Titulo Prueba Unico"), k
        assert "font-style:italic" in _estilo_del_titulo(r["editorial/" + k]["html"], "Titulo Prueba Unico"), k
        estilo = _estilo_del_titulo(r["moderna/" + k]["html"], "Titulo Prueba Unico")
        assert "uppercase" not in estilo and "italic" not in estilo, k


def test_el_texto_plano_y_whatsapp_no_cambian(tmp_path_factory):
    r = _corre(tmp_path_factory, "parejas")
    for p in PILAS:
        assert r[p + "/A"]["texto"] == r["textoHoy"], p
        assert r[p + "/A"]["wa"] == r["waHoy"], p


# --- El tamaño ---------------------------------------------------------------------------------------

def test_base_grande_y_maximo_sobre_el_tamano_de_cada_plantilla(tmp_path_factory):
    r = _corre(tmp_path_factory, "tamanos")
    for t, f in (("base", 1), ("grande", 1.25), ("maximo", 1.5)):
        for k, base in BASES.items():
            v = r[t + "/" + k]
            esperado = int(base * f + 0.5)   # como Math.round (Python redondea 42,5 a 42; JS, a 43)
            assert re.search(r"font-size:%dpx;[^\"]*\">Hola" % esperado, v["html"]), (t, k, esperado)
            assert v["calc"] == {"px": esperado, "base": base, "ajustado": False}, (t, k)


def test_una_palabra_larga_se_ajusta_hasta_el_60_por_ciento_del_base(tmp_path_factory):
    """
    La matriz en navegador (2026-10-12) mostró que con parejas anchas ni el tamaño de hoy cabe en el
    móvil: el ajuste puede bajar del base, hasta el 60 %. Se comprueba la cota y el aviso; que no
    desborde lo mide la demo en navegador real.
    """
    r = _corre(tmp_path_factory, "ajuste")
    for clave, v in r.items():
        k = clave.split("/")[1]
        c = v["calc"]
        assert c["base"] == BASES[k]
        assert int(BASES[k] * 0.6 + 0.5) <= c["px"] < int(BASES[k] * 1.5 + 0.5), clave
        assert c["ajustado"] is True, clave
        assert re.search(r"font-size:%dpx;" % c["px"], v["html"]), clave
