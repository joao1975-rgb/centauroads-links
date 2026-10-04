"""
Arreglos rápidos de la auditoría del 2026-10-03 (impeccable, web-design-guidelines y AccessLint).

Cada prueba fija un arreglo concreto para que no se pierda en el próximo cambio:

- Plantillas E–H: el naranja de etiquetas daba 4,2:1 sobre la arena; había texto de 9–10 px; los
  enlaces «Ver presentación» medían 12 px de alto; y en el móvil las filas de E y F dejaban una
  columna de 70 px con una palabra por línea.
- Compositor: a 375 px las plantillas E–H quedaban fuera de la pantalla; la subida del PDF no se
  podía hacer con teclado; 20 interruptores se llamaban igual; los desplegables no decían si
  estaban abiertos; y la Personalizada se podía copiar con el botón principal apuntando a «#».
- Panel: el borde de los campos tenía 1,3:1 frente al fondo.

Las medidas reales (desborde a 375 px, alto de 44 px, contraste) se comprobaron en navegador; aquí
se fija la forma del código que las produce.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MOTOR = RAIZ / "prototipos" / "mail" / "render.js"
PANEL = RAIZ / "prototipos" / "mail" / "compositor.html"

GUION = r"""
const M = require(process.argv[2]);
const out = {};
['E', 'F', 'G', 'H'].forEach(function (k) {
  const st = M.defaultState(); st.plantilla = k; st.cardAnim = false; st.heroAnim = false;
  out[k] = M.render(st, k);
});
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def correos(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("arreglos") / "_r.js"
    guion.write_text(GUION, encoding="utf-8")
    salida = subprocess.run(["node", str(guion), str(MOTOR)],
                            capture_output=True, text=True, encoding="utf-8", timeout=180)
    assert salida.returncode == 0, "el motor falló:\n" + salida.stderr
    return json.loads(salida.stdout)


@pytest.mark.parametrize("k", list("EFGH"))
def test_sin_texto_de_9_o_10_px(correos, k):
    assert not re.search(r"font-size:(9|10)px", correos[k]), k


@pytest.mark.parametrize("k", list("EFG"))
def test_el_naranja_de_etiquetas_tiene_contraste(correos, k):
    """En la paleta clara de E–G las etiquetas usan #8F4A06 (5,9:1); #B35E0A daba 4,2:1."""
    assert "#8F4A06" in correos[k], k


@pytest.mark.parametrize("k", list("EFGH"))
def test_ver_presentacion_es_facil_de_tocar(correos, k):
    enlaces = re.findall(r'<a [^>]*style="([^"]*)"[^>]*>Ver presentaci', correos[k])
    assert enlaces, "no hay enlaces «Ver presentación» en " + k
    for estilo in enlaces:
        assert "padding:12px 0" in estilo and "font-size:14px" in estilo, estilo


@pytest.mark.parametrize("k,minimo", [("E", 5), ("F", 3)])
def test_e_y_f_se_apilan_en_el_movil(correos, k, minimo):
    """Bloques flotantes de 264 px como mucho: caben en el hueco útil de un móvil de 352 px."""
    flotantes = re.findall(r'width="(\d+)" align="left"', correos[k])
    assert len(flotantes) >= minimo
    assert all(int(w) <= 264 for w in flotantes), flotantes


# --- Compositor ----------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def panel():
    return PANEL.read_text(encoding="utf-8")


def test_la_barra_de_plantillas_se_parte_en_el_movil(panel):
    assert "#tpl { flex-wrap:wrap; }" in panel
    assert "@media (max-width:900px) { html, body { height:auto; } body { overflow:auto; }" in panel


def test_la_subida_se_hace_con_teclado(panel):
    assert "el('button', 'suelta')" in panel
    assert "el('div', 'suelta')" not in panel


def test_cada_interruptor_tiene_su_nombre(panel):
    assert "'Mostrar ' + nombre" in panel
    for llamada in ("s.nombre));", "def.label));", "apagado, nombre));", "() => {}, etiqueta));"):
        assert llamada in panel, llamada


def test_los_desplegables_dicen_si_estan_abiertos(panel):
    assert "aria-expanded" in panel
    assert panel.count("plegable(t, ") == 3


def test_los_mensajes_de_estado_se_anuncian(panel):
    assert "p.setAttribute('role', 'status')" in panel


def test_la_personalizada_sin_enlace_no_se_copia(panel):
    assert "function faltaEnlaceH()" in panel
    for boton in ("#copyGmail", "#copyHtml", "#copyText"):
        i = panel.index("$('" + boton + "').addEventListener('click'")
        assert "faltaEnlaceH()" in panel[i:i + 160], boton
    i = panel.index("async function copiaWhatsApp()")
    assert "faltaEnlaceH()" in panel[i:i + 120]


def test_los_campos_que_no_cambian_el_correo_conservan_el_contraste(panel):
    assert ".fld.nousa, .sw.nousa { opacity:.45; }" not in panel


# --- Panel ---------------------------------------------------------------------------------------

def test_el_borde_de_los_campos_del_panel_se_ve():
    from app.auth import equipo, rutas
    assert "border:1px solid #6B6885" in rutas._ENTRADA
    assert "border:1px solid #6B6885" in equipo._PAGINA


def test_los_botones_de_cada_fila_llevan_contexto():
    from app.auth.equipo import _PAGINA
    assert "'Editar a ' + u.email" in _PAGINA
    assert "'Poner contraseña a ' + u.email" in _PAGINA
