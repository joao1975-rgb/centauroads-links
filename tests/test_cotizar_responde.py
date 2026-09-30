"""
El botón de cotizar, como una respuesta al correo (2026-09-30).

Un enlace no puede pulsar el «Responder» del programa del cliente: ninguno lo permite. Lo más cercano
es abrir un mensaje a la cuenta desde la que se envía —mercadeo@centauroads.com, siempre— con el asunto
«Re: <el del correo>». Antes abría un correo nuevo a la cuenta personal de la asesora, con un asunto
fijo que no casaba con nada de lo enviado.
"""

import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

import pytest

MOTOR = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "render.js"

GUION = r"""
const M = require(process.argv[2]);
const out = {};
// El de cotizar es el que lleva texto inicial (body=): en D va antes otro mailto, el del catalogo.
const cta = h => { const m = h.match(/href="(mailto:[^"]*subject=[^"]*&amp;body=[^"]+)"/); return m ? m[1].replace(/&amp;/g, '&') : null; };
['A', 'B', 'C', 'D', 'E', 'F', 'G'].forEach(function (k) {
  ['directo', 'beneficio'].forEach(function (a) {
    const st = M.defaultState(); st.plantilla = k; st.asunto3 = a;
    const listo = M.aplicaAsunto(M.aplicaPerfil(M.normaliza(JSON.parse(JSON.stringify(st)))));
    out[k + '-' + a] = { href: cta(M.render(st, k)), asunto: listo.asunto };
  });
});
const manual = M.defaultState(); manual.plantilla = 'A'; manual.bloques.cta.responder = false;
manual.bloques.cta.url = 'https://formulario.example/cotizar';
out.manual = M.render(manual, 'A').indexOf('href="https://formulario.example/cotizar"') >= 0;
const viejo = M.defaultState();
viejo.bloques.branding.url = 'mailto:equintero@centauroads.com?subject=Cat%C3%A1logo%20de%20branding%20y%20esculturas';
out.migrado = M.normaliza(viejo).bloques.branding.url;
const propio = M.defaultState(); propio.bloques.branding.url = 'https://otro.example/catalogo';
out.respetado = M.normaliza(propio).bloques.branding.url;
out.alternativa = ['A', 'B', 'C', 'D'].map(function (k) { const st = M.defaultState(); st.plantilla = k;
  return M.render(st, k).indexOf('responde directamente a este correo') >= 0; });
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def r(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("cot") / "_c.js"
    guion.write_text(GUION, encoding="utf-8")
    salida = subprocess.run(["node", str(guion), str(MOTOR)],
                            capture_output=True, text=True, encoding="utf-8", timeout=180)
    assert salida.returncode == 0, "el motor falló:\n" + salida.stderr
    return json.loads(salida.stdout)


def test_el_boton_escribe_a_mercadeo_con_re_y_el_asunto_del_correo(r):
    """En las siete plantillas de catálogo, y con el asunto que se haya elegido, no uno fijo."""
    for clave, v in r.items():
        if not isinstance(v, dict):
            continue
        assert v["href"], "%s: no hay botón de cotizar" % clave
        enlace = urlparse(v["href"])
        assert enlace.scheme == "mailto" and enlace.path == "mercadeo@centauroads.com", clave
        q = parse_qs(enlace.query)
        assert q["subject"] == ["Re: " + v["asunto"]], "%s: %s" % (clave, q["subject"])
        assert "cotización" in unquote(q["body"][0])


def test_cambiar_el_asunto_cambia_el_del_boton(r):
    assert r["A-directo"]["href"] != r["A-beneficio"]["href"]


def test_con_responder_apagado_manda_el_enlace_propio(r):
    assert r["manual"] is True


def test_los_enlaces_viejos_a_la_cuenta_personal_pasan_a_mercadeo(r):
    """Solo si siguen siendo exactamente los de antes: uno escrito a mano se respeta."""
    assert r["migrado"].startswith("mailto:mercadeo@centauroads.com")
    assert r["respetado"] == "https://otro.example/catalogo"


def test_a_d_invitan_tambien_a_responder_sin_mas(r):
    assert r["alternativa"] == [True, True, True, True]
