"""
A y B: «Señal nocturna», y en el móvil no se encogen.

Historia. En un teléfono de 375 px, B medía 624 px de ancho y A 389: Gmail los encogía para que cupieran y la
letra de 13 px se leía como de 8. Se arregló con tablas que flotan. Después A y B se rediseñaron («Señal
nocturna», 2026-09-30): A es una sucesión de vallas —cada foto a sangre y su placa debajo— y B pone un
espacio destacado a todo el ancho y los demás de dos en dos, que en el móvil bajan uno debajo de otro.

No hay <style> ni media queries: el correo se pega en Gmail, que tira la cabecera, y solo sobrevive el
estilo en línea. Por eso la prueba mira la estructura, que es lo que decide si algo puede ensancharse.
Se midió además en el navegador: las dos miden 375 px en un teléfono de 375.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

MOTOR = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "render.js"

GUION = r"""
const M = require(process.argv[2]);
const out = {};
['A', 'B'].forEach(function (k) {
  ['impar', 'par'].forEach(function (caso) {
    const st = M.defaultState(); st.plantilla = k;
    if (caso === 'par') { let n = 0; st.servicios.forEach(function (s) { if (s.on && ++n > 4) s.on = false; }); }
    out[k + '-' + caso] = M.render(st, k);
  });
});
process.stdout.write(JSON.stringify(out));
"""

# Lo más ancho que cabe en un teléfono de 375 px, quitando los márgenes del correo.
CABE = 300


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("ab") / "_ab.js"
    guion.write_text(GUION, encoding="utf-8")
    salida = subprocess.run(["node", str(guion), str(MOTOR)],
                            capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert salida.returncode == 0, "el motor falló:\n" + salida.stderr
    return json.loads(salida.stdout)


def test_ningun_ancho_fijo_impide_que_quepan_en_un_telefono(html):
    """
    Un ancho en píxeles mayor que la pantalla, sin tope, es lo que obligaba a Gmail a encoger el correo.
    Todo lo que pase de CABE tiene que poder bajar: max-width:100% o width:100%.
    """
    for caso, h in html.items():
        for estilo in re.findall(r'style="([^"]*)"', h):
            for px in re.findall(r'(?<![-\w])width:(\d+)px', estilo):
                if int(px) > CABE:
                    assert "max-width:100%" in estilo, "%s: width:%spx sin tope: %s" % (caso, px, estilo[:90])


def test_en_a_cada_espacio_es_una_foto_a_sangre(html):
    """La foto ocupa el ancho del correo, sin columna al lado: nada que apretar en el móvil."""
    a = html["A-impar"]
    fotos = re.findall(r'<img [^>]*width="600"[^>]*style="display:block;width:100%;max-width:100%;', a)
    assert len(fotos) >= 3
    # la forma vieja -foto y texto en dos columnas- no puede volver
    assert 'width="220" align="left"' not in a and '<td width="200" valign="top"' not in a


def test_en_b_uno_destacado_y_los_demas_de_dos_en_dos_flotando(html):
    """Las parejas flotan: lado a lado en el ordenador, una debajo de otra en el móvil."""
    for caso in ("B-impar", "B-par"):
        b = html[caso]
        assert len(re.findall(r'<img [^>]*width="544"', b)) >= 1, caso
        assert len(re.findall(r'width="264" align="left"', b)) >= 2, caso


def test_una_sola_accion_con_fondo(html):
    """El naranja es la luz de las pantallas: se usa una vez, en la acción. Lo demás es texto con flecha."""
    for caso, h in html.items():
        assert h.count('bgcolor="#F79131"') == 1, caso


def test_sin_rotulos_en_mayusculas_espaciadas(html):
    """
    Delataban plantilla. Solo queda la línea de servicios del logo, que es parte de la marca: una en la
    cabecera y otra en la firma.
    """
    for caso, h in html.items():
        assert h.count("text-transform:uppercase") == 2, caso
