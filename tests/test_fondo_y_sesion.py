"""
Dos arreglos pedidos al ver los correos de verdad (2026-09-30).

1. Fuera del marco no se pinta nada. Abierto en Gmail en el ordenador, el fondo del tema llenaba toda
   la ventana: con el oscuro o el de la marca el correo dejaba de tener borde y parecía no terminar.
   Ahora solo el marco de 600 px lleva color; el pie legal, que iba fuera sobre ese fondo, va dentro.
2. «Hay que entrar al panel», a secas, junto al botón que falló, dejaba sin saber qué hacer. Ahora
   dice qué pasa y da el enlace para entrar y volver al compositor.
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
Object.keys(M.TEMPLATES).forEach(function (k) {
  ['claro', 'oscuro', 'centauro'].forEach(function (tema) {
    const st = M.defaultState(); st.plantilla = k; st.tema = tema === 'centauro' ? 'oscuro' : tema; st.temaEntrega = tema;
    out[k + '-' + tema] = M.render(st, k);
  });
});
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def correos(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("fondo") / "_f.js"
    guion.write_text(GUION, encoding="utf-8")
    salida = subprocess.run(["node", str(guion), str(MOTOR)],
                            capture_output=True, text=True, encoding="utf-8", timeout=180)
    assert salida.returncode == 0, "el motor falló:\n" + salida.stderr
    return json.loads(salida.stdout)


def test_fuera_del_marco_no_se_pinta_nada(correos):
    """Ni el <body> ni la tabla que envuelve el marco llevan color: el correo se apoya en el cliente."""
    for caso, h in correos.items():
        body = re.search(r"<body[^>]*>", h).group(0)
        assert "background" not in body, "%s: %s" % (caso, body)
        exterior = re.search(r"<body[^>]*>\s*<div[^>]*>.*?</div>\s*(<table[^>]*>)", h, re.S).group(1)
        assert "background" not in exterior and "bgcolor" not in exterior, "%s: %s" % (caso, exterior)


def test_el_pie_legal_va_dentro_del_marco(correos):
    """
    Sin fondo exterior, un pie fuera del marco quedaría en gris claro sobre el blanco del cliente. Cada
    pie tiene que llevar el fondo de su marco.
    """
    pie = "Recibes este correo porque"
    for caso, h in correos.items():
        i = h.find(pie)
        if i < 0:
            continue  # H no lleva pie legal
        # Las celdas que siguen ABIERTAS donde empieza el pie son las que lo envuelven: alguna tiene
        # que ser el marco, con su fondo.
        abiertas = []
        for m in re.finditer(r"<(/?)td\b[^>]*>", h[:i]):
            if m.group(1):
                abiertas.pop()
            else:
                abiertas.append(m.group(0))
        assert any("background" in td for td in abiertas), "%s: el pie va sin fondo" % caso


def test_el_error_de_sesion_trae_el_enlace_para_entrar():
    panel = PANEL.read_text(encoding="utf-8")
    assert "e.status = r.status" in panel, "api() tiene que decir el código de la respuesta"
    i = panel.index("function falla(est, e)")
    cuerpo = panel[i:panel.index("\n  }\n", i)]
    assert "e.status === 401" in cuerpo and "/panel/entrar?destino=" in cuerpo
    # y ningún error del servidor se pinta ya a mano, sin pasar por falla()
    assert "est.textContent = e.message; });" not in panel
