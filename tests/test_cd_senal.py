"""
C y D con «Señal nocturna» (2026-09-30), igual que A y B.

C sigue pareciendo un correo escrito a mano: sin rótulos en mayúsculas ni botón de campaña; la acción es
un enlace en negrita, como lo pondría una persona. D, la de las referencias Digitel y Cashea, pierde las
cajas dentro de cajas: foto a sangre por grupo, título en letra de señal y un único botón relleno.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

MOTOR = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "render.js"
CABE = 300  # lo más ancho que cabe en un teléfono de 375 px, quitando los márgenes

GUION = r"""
const M = require(process.argv[2]);
const out = {};
['C', 'D'].forEach(function (k) { const st = M.defaultState(); st.plantilla = k; out[k] = M.render(st, k); });
const sin = M.defaultState(); sin.plantilla = 'D'; sin.bloques.hero.on = false; out.Dsin = M.render(sin, 'D');
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("cd") / "_cd.js"
    guion.write_text(GUION, encoding="utf-8")
    salida = subprocess.run(["node", str(guion), str(MOTOR)],
                            capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert salida.returncode == 0, "el motor falló:\n" + salida.stderr
    return json.loads(salida.stdout)


def test_ningun_ancho_fijo_impide_que_quepan_en_un_telefono(html):
    for caso, h in html.items():
        for estilo in re.findall(r'style="([^"]*)"', h):
            for px in re.findall(r'(?<![-\w])width:(\d+)px', estilo):
                if int(px) > CABE:
                    assert "max-width:100%" in estilo, "%s: width:%spx sin tope" % (caso, px)


def test_c_parece_escrito_a_mano(html):
    """Ni botón relleno ni rótulos en mayúsculas: solo la línea de servicios del logo de la firma."""
    c = html["C"]
    assert 'bgcolor="#F79131"' not in c
    assert c.count("text-transform:uppercase") == 1
    assert re.search(r'font-weight:700;">Enviar informaci', c), "la acción va como enlace en negrita"


def test_d_un_solo_boton_relleno_y_sin_rotulos(html):
    d = html["D"]
    assert d.count('bgcolor="#F79131"') == 1
    assert d.count("text-transform:uppercase") == 2  # logo de la cabecera y de la firma
    assert "DISPONIBILIDAD" not in d


def test_d_no_repite_la_foto_de_la_cabecera(html):
    """La cabecera ya es la pantalla de Chacao: el grupo de pantallas abre con otra foto."""
    assert "carousel_led_" not in html["D"] and "svc_led.jpg" not in html["D"]
    # sin cabecera no hay repetición posible, y el grupo vuelve a abrir con Chacao
    assert "carousel_led_" in html["Dsin"] or "svc_led.jpg" in html["Dsin"]
