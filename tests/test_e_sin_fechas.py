"""
La plantilla E sin datos de negocio inventados (2026-10-03, petición del usuario).

E salía por defecto con «Q1 2026 · AGENCIAS», «Disponibilidad al 19-sep», «Cerramos programación de Q1
el 15 de noviembre» y el botón «Solicitar disponibilidad Q1». Son datos del negocio que caducan y
que nadie había dado: el usuario pidió quitarlos. Ahora:

- Por defecto no hay trimestre, ni fecha, ni cierre; el botón dice «Solicitar disponibilidad».
- Sin fecha, el rótulo dice «Disponibilidad» (no «Disponibilidad al» colgando). Sin ningún dato de
  disponibilidad, el recuadro no sale.
- Quien ya usó la herramienta tiene esos valores guardados: se limpian solos, pero solo si siguen
  siendo los de antes. Lo que alguien escribió a mano se respeta.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

MOTOR = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "render.js"

GUION = r"""
const M = require(process.argv[2]);
const base = () => { const st = M.defaultState(); st.plantilla = 'E'; st.cardAnim = false; st.heroAnim = false; return st; };
const out = {};
out.defecto = M.render(base(), 'E');
// Una sesion guardada antes de este cambio: lleva los valores viejos.
const vieja = base(); const a = vieja.bloques.asesor;
a.etiquetaMeta = 'Q1 2026 · AGENCIAS'; a.dispoFecha = '19-sep';
a.cierreTexto = 'Cerramos programación de Q1 el 15 de noviembre.'; a.botonTexto = 'Solicitar disponibilidad Q1';
out.vieja = M.render(vieja, 'E');
out.viejaDatos = M.normaliza(vieja).bloques.asesor;
// Alguien que si escribio sus datos: se respetan.
const propia = base(); const p = propia.bloques.asesor;
p.etiquetaMeta = 'Q2 2027 · AGENCIAS'; p.dispoFecha = '3-mar'; p.cierreTexto = 'Cerramos el 20 de marzo.';
p.botonTexto = 'Reservar Q2';
out.propia = M.render(propia, 'E');
// Sin ningun dato de disponibilidad: el recuadro no sale.
const vacia = base(); out.vacia = M.render(vacia, 'E');
const conDato = base(); conDato.bloques.asesor.dispoTexto = 'Quedan dos espacios.'; out.conDato = M.render(conDato, 'E');
// Con periodo escrito, el epigrafe lo lleva; sin el, no queda «Inventario ·» colgando.
const conPeriodo = base(); conPeriodo.bloques.asesor.periodo = 'Enero – Marzo 2027'; out.conPeriodo = M.render(conPeriodo, 'E');
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def r(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("e") / "_e.js"
    guion.write_text(GUION, encoding="utf-8")
    salida = subprocess.run(["node", str(guion), str(MOTOR)],
                            capture_output=True, text=True, encoding="utf-8", timeout=180)
    assert salida.returncode == 0, "el motor falló:\n" + salida.stderr
    return json.loads(salida.stdout)


@pytest.mark.parametrize("caso", ["defecto", "vieja"])
def test_sin_trimestre_ni_fecha_ni_cierre_inventados(r, caso):
    html = r[caso]
    for viejo in ("Q1 2026", "19-sep", "15 de noviembre", "Solicitar disponibilidad Q1", "Disponibilidad al",
                  "Octubre – Diciembre 2026", "slots libres en octubre", "3 SLOTS", "Inventario · <"):
        assert viejo not in html, (caso, viejo)
    assert "Solicitar disponibilidad" in html


def test_la_sesion_vieja_se_limpia(r):
    a = r["viejaDatos"]
    assert a["etiquetaMeta"] == "AGENCIAS"
    assert a["dispoFecha"] == "" and a["cierreTexto"] == ""
    assert a["botonTexto"] == "Solicitar disponibilidad"
    assert a["periodo"] == "" and a["dispoTexto"] == "" and a["slotsLed"] == ""


def test_lo_escrito_a_mano_se_respeta(r):
    html = r["propia"]
    for propio in ("Q2 2027", "Disponibilidad al 3-mar", "Cerramos el 20 de marzo.", "Reservar Q2"):
        assert propio in html, propio


def test_sin_datos_de_disponibilidad_el_recuadro_no_sale(r):
    assert "●" not in r["vacia"], "el recuadro de disponibilidad sale vacío"
    assert "●" in r["conDato"] and "Quedan dos espacios." in r["conDato"]


def test_el_periodo_sale_solo_si_se_escribe(r):
    assert "Inventario · Enero – Marzo 2027" in r["conPeriodo"]
    assert "Inventario ·" not in r["defecto"]
    assert "Inventario<" in r["defecto"]
