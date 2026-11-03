"""
/c/<slug>: el enlace corto que abre el destino con ?click_id= (fbc de Meta o huella del dispositivo).

Dos mitades: la ruta del servidor (página, clic contado, 404, respaldo sin JavaScript) y el script
`app/static/click-id.js`, que es donde se calcula el valor. El script se prueba con Node, igual que el
motor de correo; sin Node esas pruebas se saltan.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app.click_id import con_click_id, fbc_de

SCRIPT = Path(__file__).resolve().parents[1] / "app" / "static" / "click-id.js"

ENLACE = {
    "slug": "prueba-click-id",
    "target_url": "https://destino.ejemplo.test/landing?utm_source=meta#oferta",
    "name": "Prueba click_id",
}


@pytest.fixture(scope="module")
def cliente():
    c = TestClient(app_main.app)
    admin = {"X-Admin-Key": app_main.get_admin_password()}
    r = c.post("/api/links", json=ENLACE, headers=admin)
    assert r.status_code == 200, r.text
    return c


# --- La ruta ------------------------------------------------------------------------------

def test_sirve_la_pagina_que_carga_el_script(cliente):
    r = cliente.get(f"/c/{ENLACE['slug']}", follow_redirects=False)
    assert r.status_code == 200
    assert '<script src="/static/click-id.js"' in r.text
    assert 'data-destino="https://destino.ejemplo.test/landing?utm_source=meta#oferta"' in r.text
    assert r.headers["cache-control"] == "no-store"


def test_el_script_se_sirve(cliente):
    r = cliente.get("/static/click-id.js")
    assert r.status_code == 200
    assert "calculaFbc" in r.text


def test_cuenta_el_clic_como_el_redirect(cliente):
    admin = {"X-Admin-Key": app_main.get_admin_password()}
    antes = next(l for l in cliente.get("/api/links", headers=admin).json()
                 if l["slug"] == ENLACE["slug"])["click_count"]
    cliente.get(f"/c/{ENLACE['slug']}")
    despues = next(l for l in cliente.get("/api/links", headers=admin).json()
                   if l["slug"] == ENLACE["slug"])["click_count"]
    assert despues == antes + 1


def test_slug_inexistente_da_404(cliente):
    assert cliente.get("/c/no-existe-este-slug").status_code == 404


def test_sin_javascript_con_fbclid_lleva_el_fbc(cliente):
    r = cliente.get(f"/c/{ENLACE['slug']}?fbclid=IwAR_prueba-1")
    assert 'http-equiv="refresh"' in r.text
    assert "click_id=fb.1." in r.text and ".IwAR_prueba-1" in r.text


def test_un_fbclid_raro_no_se_cuela_en_la_pagina(cliente):
    r = cliente.get(f"/c/{ENLACE['slug']}", params={"fbclid": '"><script>alert(1)</script>'})
    assert r.status_code == 200
    assert "<script>alert(1)" not in r.text
    assert "click_id=" not in r.text


def test_el_redirect_de_siempre_no_cambia(cliente):
    r = cliente.get(f"/{ENLACE['slug']}", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == ENLACE["target_url"]


# --- Las funciones del servidor -----------------------------------------------------------

def test_fbc_de():
    assert fbc_de("AbC_1-2", ahora_ms=1700000000000) == "fb.1.1700000000000.AbC_1-2"
    assert fbc_de(None) is None
    assert fbc_de("") is None
    assert fbc_de("con espacio") is None


def test_con_click_id_conserva_parametros_y_ancla():
    url = con_click_id("https://x.test/a?utm=1&click_id=viejo#ancla", "fb.1.5.Z")
    assert url == "https://x.test/a?utm=1&click_id=fb.1.5.Z#ancla"


# --- El script (Node) ---------------------------------------------------------------------

GUION = r"""
const M = require(process.argv[2]);
const out = {};
out.fbcNuevo = M.calculaFbc('?fbclid=AbC', '', 1700000000000);
out.fbcMismaCookie = M.calculaFbc('?fbclid=AbC', 'fb.1.1600000000000.AbC', 1700000000000);
out.fbcOtroClic = M.calculaFbc('?fbclid=XyZ', 'fb.1.1600000000000.AbC', 1700000000000);
out.fbcSoloCookie = M.calculaFbc('', 'fb.1.1600000000000.AbC', 1700000000000);
out.fbcNada = M.calculaFbc('?utm=1', '', 1700000000000);
out.fbcRaro = M.calculaFbc('?fbclid=%22%3E%3Cx', '', 1700000000000);
const s = ['Mozilla/5.0 (Linux; Android 14)', 'Linux armv8l', 'es-VE', 'America/Caracas',
           '412x915', 2.625, 8, 'Qualcomm', 'Adreno (TM) 730', 5];
out.huella1 = M.huella(s);
out.huella2 = M.huella(s.slice());
out.huellaOtra = M.huella(s.slice(0, 4).concat(['390x844'], s.slice(5)));
out.url = M.conClickId('https://x.test/a?utm=1&click_id=viejo#ancla', 'fp.abc');

// Un navegador de mentira para calculaClickId, que además escribe la cookie.
function nav(search, cookie) {
  const doc = { cookie: cookie || '', createElement: () => ({ getContext: () => null }) };
  return { document: doc, location: { search, protocol: 'https:' }, devicePixelRatio: 2,
           navigator: { userAgent: 'UA', platform: 'P', language: 'es', hardwareConcurrency: 4,
                        maxTouchPoints: 5 },
           screen: { width: 390, height: 844 } };
}
const conAnuncio = nav('?fbclid=AbC');
out.idAnuncio = M.calculaClickId(conAnuncio);
out.cookieEscrita = conAnuncio.document.cookie;
out.idSinAnuncio = M.calculaClickId(nav(''));
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def js(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("clickid") / "_clickid.js"
    guion.write_text(GUION, encoding="utf-8")
    salida = subprocess.run(["node", str(guion), str(SCRIPT)],
                            capture_output=True, text=True, encoding="utf-8", timeout=60)
    assert salida.returncode == 0, "el script falló:\n" + salida.stderr
    return json.loads(salida.stdout)


def test_js_con_fbclid_arma_el_fbc_de_meta(js):
    assert js["fbcNuevo"] == {"valor": "fb.1.1700000000000.AbC", "nuevo": True}


def test_js_mismo_fbclid_conserva_la_cookie(js):
    assert js["fbcMismaCookie"] == {"valor": "fb.1.1600000000000.AbC", "nuevo": False}


def test_js_un_clic_nuevo_reemplaza_la_cookie(js):
    assert js["fbcOtroClic"] == {"valor": "fb.1.1700000000000.XyZ", "nuevo": True}


def test_js_sin_fbclid_usa_la_cookie_si_existe(js):
    assert js["fbcSoloCookie"] == {"valor": "fb.1.1600000000000.AbC", "nuevo": False}


def test_js_sin_fbclid_ni_cookie_no_hay_fbc(js):
    assert js["fbcNada"] is None
    assert js["fbcRaro"] is None


def test_js_la_huella_es_estable_y_distingue_dispositivos(js):
    assert js["huella1"] == js["huella2"]
    assert js["huella1"] != js["huellaOtra"]
    assert js["huella1"].startswith("fp.") and len(js["huella1"]) == 3 + 28


def test_js_click_id_en_la_url(js):
    assert js["url"] == "https://x.test/a?utm=1&click_id=fp.abc#ancla"


def test_js_calcula_click_id_y_guarda_la_cookie(js):
    assert js["idAnuncio"].startswith("fb.1.") and js["idAnuncio"].endswith(".AbC")
    assert js["cookieEscrita"].startswith("_fbc=fb.1.")
    assert "max-age=7776000" in js["cookieEscrita"] and "Secure" in js["cookieEscrita"]
    assert js["idSinAnuncio"].startswith("fp.")
