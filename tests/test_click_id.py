"""
/c/<slug>: el enlace corto que abre el destino con ?click_id=…&fingerprint=… y los guarda con el clic.

Tres partes: la página (`/c/<slug>`), el paso que guarda y redirige (`/c/<slug>/ir`) y el script
`app/static/click-id.js`, que es donde se calculan los valores. El script se prueba con Node, igual
que el motor de correo; sin Node esas pruebas se saltan.
"""

import json
import shutil
import subprocess
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, inspect, text

from app import main as app_main
from app import models
from app.click_id import con_parametros, fbc_de, valores_validos
from app.database import SessionLocal
from app.migracion import migrar

SCRIPT = Path(__file__).resolve().parents[1] / "app" / "static" / "click-id.js"

ENLACE = {
    "slug": "prueba-click-id",
    "target_url": "https://destino.ejemplo.test/landing?utm_source=meta#oferta",
    "name": "Prueba click_id",
}
FBC = "fb.1.1700000000000.IwAR_prueba-1"
HUELLA = "fp." + "0123456789abcdef0123456789ab"


@pytest.fixture(scope="module")
def cliente():
    c = TestClient(app_main.app)
    admin = {"X-Admin-Key": app_main.get_admin_password()}
    r = c.post("/api/links", json=ENLACE, headers=admin)
    assert r.status_code == 200, r.text
    return c


def _clics():
    with SessionLocal() as db:
        link = db.query(models.Link).filter(models.Link.slug == ENLACE["slug"]).one()
        return link.click_count, db.query(models.Click).filter(
            models.Click.link_id == link.id).order_by(models.Click.id.desc()).first()


# --- La página ----------------------------------------------------------------------------

def test_sirve_la_pagina_que_carga_el_script(cliente):
    r = cliente.get(f"/c/{ENLACE['slug']}", follow_redirects=False)
    assert r.status_code == 200
    assert '<script src="/static/click-id.js" data-ir="/c/prueba-click-id/ir">' in r.text
    assert r.headers["cache-control"] == "no-store"


def test_la_pagina_no_cuenta_el_clic(cliente):
    # Lo cuenta /ir, con los valores. Un robot que solo lee la página no suma.
    antes, _ = _clics()
    cliente.get(f"/c/{ENLACE['slug']}")
    assert _clics()[0] == antes


def test_el_script_se_sirve(cliente):
    r = cliente.get("/static/click-id.js")
    assert r.status_code == 200
    assert "calculaValores" in r.text


def test_slug_inexistente_da_404(cliente):
    assert cliente.get("/c/no-existe-este-slug").status_code == 404
    assert cliente.get("/c/no-existe-este-slug/ir").status_code == 404


def test_sin_javascript_con_fbclid_lleva_el_fbc(cliente):
    r = cliente.get(f"/c/{ENLACE['slug']}?fbclid=IwAR_prueba-1")
    assert 'http-equiv="refresh"' in r.text
    assert "/c/prueba-click-id/ir?click_id=fb.1." in r.text and ".IwAR_prueba-1" in r.text


def test_un_fbclid_raro_no_se_cuela_en_la_pagina(cliente):
    r = cliente.get(f"/c/{ENLACE['slug']}", params={"fbclid": '"><script>alert(1)</script>'})
    assert r.status_code == 200
    assert "<script>alert(1)" not in r.text
    assert "click_id=" not in r.text


# --- /ir: guarda y redirige ---------------------------------------------------------------

def test_ir_guarda_los_dos_y_los_manda_al_destino(cliente):
    antes, _ = _clics()
    r = cliente.get(f"/c/{ENLACE['slug']}/ir",
                    params={"click_id": FBC, "fingerprint": HUELLA, "ref": "https://instagram.com/"},
                    headers={"referer": f"http://testserver/c/{ENLACE['slug']}"},
                    follow_redirects=False)
    assert r.status_code == 307
    destino = urlparse(r.headers["location"])
    assert (destino.netloc, destino.path, destino.fragment) == ("destino.ejemplo.test", "/landing", "oferta")
    assert parse_qs(destino.query) == {"utm_source": ["meta"], "click_id": [FBC], "fingerprint": [HUELLA]}
    cuenta, clic = _clics()
    assert cuenta == antes + 1
    assert (clic.click_id, clic.fingerprint) == (FBC, HUELLA)
    assert clic.referer == "https://instagram.com/"


def test_ir_sin_fbc_el_click_id_es_la_huella(cliente):
    r = cliente.get(f"/c/{ENLACE['slug']}/ir", params={"click_id": HUELLA, "fingerprint": HUELLA},
                    follow_redirects=False)
    q = parse_qs(urlparse(r.headers["location"]).query)
    assert q["click_id"] == [HUELLA] and q["fingerprint"] == [HUELLA]


def test_ir_descarta_valores_raros_pero_redirige(cliente):
    r = cliente.get(f"/c/{ENLACE['slug']}/ir",
                    params={"click_id": "<x>", "fingerprint": "fp.NO"}, follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == ENLACE["target_url"]
    _, clic = _clics()
    assert (clic.click_id, clic.fingerprint) == (None, None)


def test_las_estadisticas_los_muestran(cliente):
    admin = {"X-Admin-Key": app_main.get_admin_password()}
    cliente.get(f"/c/{ENLACE['slug']}/ir", params={"click_id": FBC, "fingerprint": HUELLA},
                follow_redirects=False)
    link_id = next(l["id"] for l in cliente.get("/api/links", headers=admin).json()
                   if l["slug"] == ENLACE["slug"])
    ultimo = cliente.get(f"/api/links/{link_id}/stats", headers=admin).json()["recent_clicks"][0]
    assert (ultimo["click_id"], ultimo["fingerprint"]) == (FBC, HUELLA)


def test_el_redirect_de_siempre_no_cambia(cliente):
    r = cliente.get(f"/{ENLACE['slug']}", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == ENLACE["target_url"]


def test_la_migracion_anade_las_columnas_a_una_base_anterior(tmp_path):
    # Una tabla clicks como la de producción antes de este cambio: sin las dos columnas.
    motor = create_engine(f"sqlite:///{(tmp_path / 'vieja.db').as_posix()}")
    with motor.begin() as con:
        con.execute(text("CREATE TABLE links (id INTEGER PRIMARY KEY, slug VARCHAR(100))"))
        con.execute(text("CREATE TABLE clicks (id INTEGER PRIMARY KEY, link_id INTEGER, ip VARCHAR(50), "
                         "contact_token VARCHAR(64))"))
        con.execute(text("INSERT INTO clicks (link_id, ip) VALUES (1, '1.2.3.4')"))
    hecho = migrar(motor)
    assert {"clicks.click_id", "clicks.fingerprint"} <= set(hecho["columnas"])
    columnas = {c["name"] for c in inspect(motor).get_columns("clicks")}
    assert {"click_id", "fingerprint"} <= columnas
    with motor.connect() as con:
        assert con.execute(text("SELECT ip, click_id FROM clicks")).one() == ("1.2.3.4", None)
    assert migrar(motor)["columnas"] == []   # la segunda vez no hace nada


# --- Las funciones del servidor -----------------------------------------------------------

def test_fbc_de():
    assert fbc_de("AbC_1-2", ahora_ms=1700000000000) == "fb.1.1700000000000.AbC_1-2"
    assert fbc_de(None) is None
    assert fbc_de("") is None
    assert fbc_de("con espacio") is None


def test_valores_validos():
    assert valores_validos(FBC, HUELLA) == (FBC, HUELLA)
    assert valores_validos(None, HUELLA) == (HUELLA, HUELLA)
    assert valores_validos("fb.1.x.y", "fp.mal") == (None, None)


def test_con_parametros_conserva_lo_demas():
    url = con_parametros("https://x.test/a?utm=1&click_id=viejo#ancla",
                         {"click_id": "fb.1.5.Z", "fingerprint": None})
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
out.url = M.conParametros('/c/x/ir', { click_id: 'fb.1.5.Z', fingerprint: 'fp.abc', ref: '' },
                          'https://links.ejemplo.test/c/x?fbclid=Z');

// Un navegador de mentira para calculaValores, que además escribe la cookie.
function nav(search, cookie) {
  const doc = { cookie: cookie || '', createElement: () => ({ getContext: () => null }) };
  return { document: doc, location: { search, protocol: 'https:' }, devicePixelRatio: 2,
           navigator: { userAgent: 'UA', platform: 'P', language: 'es', hardwareConcurrency: 4,
                        maxTouchPoints: 5 },
           screen: { width: 390, height: 844 } };
}
const conAnuncio = nav('?fbclid=AbC');
out.conAnuncio = M.calculaValores(conAnuncio);
out.cookieEscrita = conAnuncio.document.cookie;
out.sinAnuncio = M.calculaValores(nav(''));
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


def test_js_la_salida_lleva_los_dos_parametros(js):
    assert js["url"] == "https://links.ejemplo.test/c/x/ir?click_id=fb.1.5.Z&fingerprint=fp.abc"


def test_js_con_anuncio_manda_fbc_y_huella(js):
    v = js["conAnuncio"]
    assert v["click_id"].startswith("fb.1.") and v["click_id"].endswith(".AbC")
    assert v["fingerprint"].startswith("fp.")
    assert js["cookieEscrita"].startswith("_fbc=fb.1.")
    assert "max-age=7776000" in js["cookieEscrita"] and "Secure" in js["cookieEscrita"]


def test_js_sin_anuncio_la_huella_va_en_los_dos(js):
    v = js["sinAnuncio"]
    assert v["click_id"] == v["fingerprint"] and v["fingerprint"].startswith("fp.")
