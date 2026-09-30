"""
A y B en el móvil: las columnas bajan en vez de que Gmail encoja el correo entero.

En un teléfono de 375 px, B medía 624 px de ancho y A 389: Gmail los encogía para que cupieran y la letra
de 13 px se leía como de 8. El motivo era un ancho fijo que no podía bajar: la tarjeta sola de B fijaba
544 px, y A ponía foto y texto en dos celdas de la misma fila. Ahora son tablas que flotan: en el ordenador
caben lado a lado, exactamente como antes (se comparó píxel a píxel), y en el móvil bajan.

No hay <style> ni media queries: el correo se pega en Gmail, que tira la cabecera, y solo sobrevive el
estilo en línea. Por eso la prueba mira la estructura, que es lo que decide si una columna puede bajar.
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


def test_la_tarjeta_sola_de_b_no_fija_544_px(html):
    """Era la que obligaba a Gmail a encoger el correo entero: 544 px no caben en un teléfono."""
    b = html["B-impar"]
    assert "width:544px" not in b and 'width="544" align' not in b
    # y sigue habiendo una tarjeta que ocupa la fila entera, que es lo que se ve en el ordenador
    assert 'width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;margin:0 0 16px 0;"' in b


def test_las_tarjetas_de_b_de_dos_en_dos_flotan(html):
    """Si no flotan, no bajan: dos de 264 más el hueco de 16 son 544 fijos."""
    for caso in ("B-impar", "B-par"):
        assert len(re.findall(r'width="264" align="left"', html[caso])) >= 2, caso


def test_en_a_foto_y_texto_son_dos_columnas_que_flotan(html):
    """
    Una fila por servicio, y en cada una la foto (220: 202 con su borde, más 18 de hueco) y el texto
    (324) flotan. Suman 544, el ancho de la fila: en el ordenador quedan lado a lado como antes.
    """
    a = html["A-impar"]
    fotos = re.findall(r'<table role="presentation" width="220" align="left"[^>]*style="width:220px;max-width:100%;"', a)
    textos = re.findall(r'<table role="presentation" width="324" align="left"[^>]*style="width:100%;max-width:324px;"', a)
    assert len(fotos) >= 3 and len(fotos) == len(textos)
    assert 220 + 324 == 600 - 2 * 28
    # la forma vieja -foto y texto en dos celdas de la misma fila- no puede volver
    assert not re.search(r'<td width="200" valign="top" style="padding:0 18px 0 0;">', a)


def test_el_hueco_del_movil_no_cambia_la_fila_en_el_ordenador(html):
    """
    En el móvil hacen falta 14 px entre la foto y el texto que baja. Van como relleno inferior de las dos
    columnas y se quitan del margen de la fila (18 -> 4): en el ordenador la fila mide lo mismo, sea más
    alta la foto o el texto.
    """
    a = html["A-impar"]
    assert a.count('style="padding:0 18px 14px 0;"') == a.count('style="padding:0 0 14px 0;"') >= 3
    assert "padding:18px 28px 4px 28px;background:" in a
