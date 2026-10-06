"""
El enlace de cada presentación base: editable, y de Canva o del acortador propio.

Hasta ahora estaba fijo en el código. La única forma de usar enlaces de Centauro era una base
global que componía `<base>/<slug>` con slugs que no existían en el acortador: puesta, mandaba
los cinco "Ver presentación" a un 404. Se comprobó contra producción antes de quitarla.

El enlace sale en las ocho plantillas y en el texto plano, y todos pasan por `linkFor`. Por eso
se prueba en todas: un solo sitio que se salte la función y el cliente abre la presentación vieja.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MOTOR = RAIZ / "prototipos" / "mail" / "render.js"

CANVA_NUEVO = "https://canva.link/otra-presentacion-2026"
CORTO = "https://links.centauroads.com/vallas2026"

GUION = r"""
const M = require(process.argv[2]);
const CANVA_NUEVO = process.argv[3], CORTO = process.argv[4];
const salida = { plantillas: {}, texto: '' };

// El enlace de Vallas, el primer servicio, cambiado a mano como lo hace el panel.
function conEnlace(url, token) {
  const st = M.defaultState();
  st.servicios[0].canva = url;
  st.token = token || '';
  return st;
}

Object.keys(M.TEMPLATES).forEach(function (k) {
  const st = conEnlace(CANVA_NUEVO); st.plantilla = k;
  salida.plantillas[k] = M.render(st, k);
});
const txt = conEnlace(CANVA_NUEVO); txt.plantilla = 'A';
salida.texto = M.renderText(txt);

// El token por destinatario: en el acortador si, en Canva no.
salida.cortoConToken = M.linkFor(conEnlace(CORTO, 'cliente 7'), { canva: CORTO });
salida.canvaConToken = M.linkFor(conEnlace(CANVA_NUEVO, 'cliente 7'), { canva: CANVA_NUEVO });

// Un estado guardado de antes, con la base global puesta.
const viejo = M.defaultState(); viejo.linkBase = 'https://links.centauroads.com';
const n = M.normaliza(JSON.parse(JSON.stringify(viejo)));
salida.linkBaseTrasMigrar = n.linkBase === undefined ? null : n.linkBase;
const tras = M.render(n, 'A');
salida.migradoLlevaElDeCanva = tras.indexOf(M.SERVICIOS[0].canva) >= 0;
salida.migradoLlevaSlugRoto = tras.indexOf('links.centauroads.com/vallas"') >= 0;

process.stdout.write(JSON.stringify(salida));
"""


@pytest.fixture(scope="module")
def r(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible")
    guion = tmp_path_factory.mktemp("enl") / "_e.js"
    guion.write_text(GUION, encoding="utf-8")
    salida = subprocess.run(["node", str(guion), str(MOTOR), CANVA_NUEVO, CORTO],
                            capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert salida.returncode == 0, "el motor no pudo renderizar:\n" + salida.stderr
    return json.loads(salida.stdout)


def test_el_enlace_cambiado_sale_en_todas_las_plantillas(r):
    """
    Las ocho plantillas usan el enlace de Vallas, y las ocho tienen que llevar el nuevo. Basta
    una que lo tuviera escrito a mano para que un cliente abriera la presentación vieja.
    """
    viejo = "canva.link/fgsgrl8vj329ue0"
    for k, html in r["plantillas"].items():
        # H lleva los servicios en «Lo que la acompaña»: también ahí.
        assert CANVA_NUEVO in html, "la plantilla %s no usa el enlace cambiado" % k
        assert viejo not in html, "la plantilla %s sigue llevando el enlace viejo" % k


def test_el_texto_plano_tambien(r):
    """La versión en texto va con el correo: si ahí queda el viejo, medio cliente abre ese."""
    assert CANVA_NUEVO in r["texto"]


def test_el_token_solo_va_en_los_enlaces_del_acortador(r):
    """
    El token (?c=) registra quién pulsó, y eso solo lo hace el acortador propio. A un enlace de
    Canva no le sirve, y meterle parámetros a un corto de canva.link es arriesgar que no resuelva.
    """
    assert r["cortoConToken"] == CORTO + "?c=cliente%207"
    assert r["canvaConToken"] == CANVA_NUEVO


def test_la_base_global_rota_se_retira_del_estado_guardado(r):
    """
    Quien tuviera puesta la base global mandaba cinco 404: sus slugs no existían en el
    acortador. Al migrar, desaparece y vuelve el enlace de cada servicio.
    """
    assert r["linkBaseTrasMigrar"] is None
    assert r["migradoLlevaElDeCanva"]
    assert not r["migradoLlevaSlugRoto"]
