"""
Los textos de E, F y G se editan desde el panel.

Eran literales en el código: el titular, los párrafos, las fases de F, las escenas de G, la tabla de
inventario de E... Ahora viven en cuatro bloques de datos (inventario, tablaInventario, guia, phygital).
Con los valores por defecto el correo sale idéntico byte a byte: lo vigila la guardia de las
plantillas de referencia, y al hacer el cambio se comparó además contra 768 correos del código viejo.

Aquí se prueba lo que la guardia no ve: que cada campo llega al correo, que el realce *así* y los
huecos {…} funcionan, que lo escrito nunca se cuela como HTML y que un estado guardado de antes,
sin estos bloques, sigue dando el mismo correo.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

MOTOR = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "render.js"
PANEL = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "compositor.html"
BLOQUES = {"E": ["inventario", "tablaInventario"], "F": ["guia"], "G": ["phygital"]}

GUION = r"""
const M = require(process.argv[2]);
const BLOQUES = JSON.parse(process.argv[3]);
const base = k => { const st = M.defaultState(); st.plantilla = k; st.destinatario = 'Ana'; return st; };
const out = { noLlegan: [], realce: {}, huecos: {}, escape: {}, viejo: {}, campos: {} };

// 1. Cada campo llega al correo de su plantilla.
Object.keys(BLOQUES).forEach(function (k) {
  BLOQUES[k].forEach(function (b) {
    out.campos[b] = Object.keys(M.defaultState().bloques[b]);
    Object.keys(M.defaultState().bloques[b]).forEach(function (c) {
      const st = base(k); st.bloques[b][c] = 'MRC' + c + 'ZQ';
      if (M.render(st, k).indexOf('MRC' + c + 'ZQ') < 0) out.noLlegan.push(k + ':' + b + '.' + c);
    });
  });
});

// 2. *asi* es el realce: color de acento en los titulares, negrita en los parrafos.
let st = base('E'); st.bloques.inventario.titulo = 'Uno *DOS* tres';
out.realce.titularE = /Uno <span style="color:[^"]+;">DOS<\/span> tres/.test(M.render(st, 'E'));
st = base('F'); st.bloques.guia.fase2Texto = 'Uno *DOS* tres';
out.realce.parrafoF = M.render(st, 'F').indexOf('Uno <b>DOS</b> tres') >= 0;
st = base('G'); st.bloques.phygital.titulo = 'Linea uno\nLinea *dos*';
out.realce.saltoG = /Linea uno<br>Linea <span style="color:[^"]+;">dos<\/span>/.test(M.render(st, 'G'));
// En un titulo que ya va en negrita, la negrita no se notaria: ahi el realce es el color.
st = base('G'); st.bloques.phygital.remate = 'La calle *es* feed';
out.realce.tituloNegritaG = /La calle <span style="color:[^"]+;">es<\/span> feed/.test(M.render(st, 'G'));
st = base('F'); st.bloques.guia.cajaTitulo = 'Sin *nada*';
out.realce.tituloNegritaF = /Sin <span style="color:[^"]+;">nada<\/span>/.test(M.render(st, 'F'));

// 3. Huecos: los rellena el motor.
st = base('E'); st.bloques.asesor.periodo = 'PERIODO-X';
st.bloques.inventario.entrada = '[{frentes}|{n}|{periodo}|{destinatario}|{desconocido}]';
st.bloques.tablaInventario.led_detalle = 'medida {medida}';
const e = M.render(st, 'E');
const n = st.servicios.filter(function (s) { return s.on; }).length;
out.huecos.entrada = e.indexOf('[' + ['cero','un','dos','tres','cuatro','cinco','seis','siete'][n] + '|' + n + '|PERIODO-X|Ana|{desconocido}]') >= 0;
out.huecos.medida = e.indexOf('medida ' + M.FICHA.led.medida) >= 0;
st = base('F'); st.destinatario = '';
out.huecos.sinNombre = M.render(st, 'F').indexOf('Hola [Nombre],') >= 0;

// 4. Lo escrito es texto, nunca HTML.
st = base('G'); st.bloques.phygital.comentario = '<script>alert(1)</script> & *<img src=x>*';
const g = M.render(st, 'G');
out.escape.g = g.indexOf('<script>alert(1)') < 0 && g.indexOf('<img src=x>') < 0 &&
  g.indexOf('&lt;script&gt;alert(1)&lt;/script&gt; &amp; <b>&lt;img src=x&gt;</b>') >= 0;

// 5. Un estado guardado ANTES de que existieran estos bloques da el mismo correo.
['E', 'F', 'G'].forEach(function (k) {
  const viejo = base(k); BLOQUES[k].forEach(function (b) { delete viejo.bloques[b]; });
  delete viejo.bloques.asesor.botonTexto;
  out.viejo[k] = M.render(viejo, k) === M.render(base(k), k);
});
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def r(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("efg") / "_efg.js"
    guion.write_text(GUION, encoding="utf-8")
    salida = subprocess.run(["node", str(guion), str(MOTOR), json.dumps(BLOQUES)],
                            capture_output=True, text=True, encoding="utf-8", timeout=180)
    assert salida.returncode == 0, "el motor falló:\n" + salida.stderr
    return json.loads(salida.stdout)


def test_cada_campo_llega_al_correo_de_su_plantilla(r):
    """Un campo que no llega al correo sería un control que miente: se escribe y no pasa nada."""
    assert r["noLlegan"] == [], "no llegan al correo: %s" % r["noLlegan"]


def test_cada_campo_tiene_su_control_en_el_panel(r):
    """Y al revés: un texto que llega al correo pero no tiene control es otro literal escondido."""
    panel = PANEL.read_text(encoding="utf-8")
    for bloque, campos in r["campos"].items():
        i = panel.index("{ k: '%s'" % bloque)
        trozo = panel[i:panel.index("] },", i)]
        faltan = [c for c in campos if "['%s', '" % c not in trozo]
        assert faltan == [], "%s: sin control en el panel: %s" % (bloque, faltan)


def test_los_bloques_solo_salen_con_su_plantilla():
    """En las otras plantillas no cambian nada: enseñarlos sería ruido."""
    panel = PANEL.read_text(encoding="utf-8")
    for plantilla, bloques in BLOQUES.items():
        for b in bloques:
            assert "{ k: '%s', soloPara: '%s'" % (b, plantilla) in panel
    assert "BLOQUES.filter(d => !d.soloPara || d.soloPara === M.pick(st))" in panel


def test_el_realce_se_escribe_con_asteriscos(r):
    assert r["realce"] == {"titularE": True, "parrafoF": True, "saltoG": True,
                           "tituloNegritaG": True, "tituloNegritaF": True}, r["realce"]


def test_los_huecos_los_rellena_el_motor(r):
    """{medida} sale de la ficha oficial; uno desconocido se queda a la vista, no desaparece."""
    assert r["huecos"] == {"entrada": True, "medida": True, "sinNombre": True}, r["huecos"]


def test_lo_escrito_nunca_es_html(r):
    """Se escapa antes de poner el realce: ni una etiqueta escrita en el panel llega viva al correo."""
    assert r["escape"]["g"] is True


def test_un_estado_guardado_de_antes_da_el_mismo_correo(r):
    """Quien ya usaba el compositor no tiene estos bloques: normaliza los rellena, sin perder nada."""
    assert r["viejo"] == {"E": True, "F": True, "G": True}, r["viejo"]
