"""
La tabla de disponibilidad del perfil agencia cabe en un teléfono (2026-10-06).

Medido a 375 px: sin precios, A se salía 9 px y D 1 px. «Medidas» no podía partirse en dos líneas
(`white-space:nowrap`), y eso empujaba el ancho mínimo de toda la tabla. Con precios era peor: una
cuarta columna «Desde» llevaba la tabla a 399 px, 104 px fuera de la pantalla. Cuatro columnas no
caben en 375 px sin media queries, y el correo no las tiene (Gmail tira el <style>).

El arreglo: ninguna celda de la tabla prohíbe partir el texto, y el precio va debajo de la ubicación
de cada espacio, no en una columna propia. La tabla tiene siempre tres columnas.
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
['A', 'B', 'C', 'D'].forEach(function (k) {
  [false, true].forEach(function (precios) {
    const st = M.defaultState(); st.plantilla = k; st.perfil = 'agencia';
    if (precios) st.precios = 'desde';
    out[k + (precios ? '-precios' : '')] = M.render(st, k);
  });
});
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def correos(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("agencias") / "_a.js"
    guion.write_text(GUION, encoding="utf-8")
    r = subprocess.run(["node", str(guion), str(MOTOR)], capture_output=True, text=True,
                       encoding="utf-8", timeout=300)
    assert r.returncode == 0, "el motor falló:\n" + r.stderr
    return json.loads(r.stdout)


def _tabla(html):
    """La tabla de disponibilidad: de su cabecera «Espacio» a su cierre."""
    i = html.index(">Espacio</td>")
    return html[html.rindex("<table", 0, i):html.index("</table>", i)]


@pytest.mark.parametrize("clave", ["A", "A-precios", "B", "B-precios", "C", "C-precios", "D", "D-precios"])
def test_ninguna_celda_impide_partir_el_texto(correos, clave):
    assert "nowrap" not in _tabla(correos[clave])


@pytest.mark.parametrize("clave", ["A-precios", "B-precios", "C-precios", "D-precios"])
def test_con_precios_sigue_teniendo_tres_columnas(correos, clave):
    tabla = _tabla(correos[clave])
    assert ">Desde</td>" not in tabla
    cabecera = tabla[:tabla.index("</tr>")]
    assert len(re.findall(r"<td", cabecera)) == 3


@pytest.mark.parametrize("clave", ["A-precios", "D-precios"])
def test_el_precio_va_debajo_de_la_ubicacion_de_su_espacio(correos, clave):
    tabla = _tabla(correos[clave])
    fila_led = tabla[tabla.index("Pantalla LED Chacao"):]
    fila_led = fila_led[:fila_led.index("</tr>")]
    primera_celda = fila_led[:fila_led.index("</td>")]
    # «1.500 $/mes» va unido (&nbsp;): partido, «$/mes» quedaba solo en otra linea.
    assert "1.500&nbsp;$/mes" in primera_celda
    assert "a cotizar" in tabla, "sin precio de entrada, lo dice"


@pytest.mark.parametrize("clave", ["A", "D"])
def test_sin_precios_no_sale_ningun_importe(correos, clave):
    tabla = _tabla(correos[clave])
    assert "$/mes" not in tabla and "a cotizar" not in tabla
