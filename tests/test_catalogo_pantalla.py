"""
La pantalla «Líneas de negocio» (/panel/lineas, especificación 003) y su enlace en el compositor.

La pantalla es solo la cara de la API: las reglas (quién da de alta, qué se valida) siguen allí.
Lo que se fija aquí es que no se abre sin sesión, que no mete datos como HTML —los nombres los
teclea gente— y que el compositor pide el catálogo al servidor antes de usar el de serie.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import sesion
from app.database import SessionLocal

PANTALLA = "/panel/lineas"
RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def comercial():
    with SessionLocal() as db:
        u = db.query(models.PanelUser).filter(models.PanelUser.email == "lee-lineas@ejemplo.test").first()
        if not u:
            u = models.PanelUser(email="lee-lineas@ejemplo.test", nombre="Lee", rol="comercial", activo=True)
            db.add(u)
            db.commit()
            db.refresh(u)
        c = TestClient(app_main.app)
        c.cookies.set(sesion.COOKIE, sesion.crear(u.id, u.email))
        return c


def test_sin_sesion_lleva_a_la_entrada():
    r = TestClient(app_main.app).get(PANTALLA, follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/panel/entrar?destino=%2Fpanel%2Flineas"


def test_con_sesion_se_ve_y_no_se_guarda_en_cache(comercial):
    r = comercial.get(PANTALLA)
    assert r.status_code == 200
    assert "Líneas de negocio" in r.text
    assert r.headers["cache-control"] == "no-store"


def test_el_alta_solo_se_ensena_a_administradores(comercial):
    html = comercial.get(PANTALLA).text
    assert '<section id="alta" aria-labelledby="t-alta" hidden>' in html
    assert "d.rol === 'admin'" in html


def test_la_pagina_no_mete_datos_como_html(comercial):
    assert "innerHTML" not in comercial.get(PANTALLA).text


def test_se_eligen_las_plantillas_a_a_h(comercial):
    html = comercial.get(PANTALLA).text
    for letra in "ABCDEFGH":
        assert 'value="%s"' % letra in html


def test_editar_ordenar_y_retirar_estan_en_la_pantalla(comercial):
    """US3: editar en la fila, subir/bajar y retirar/devolver; las retiradas, aparte."""
    html = comercial.get(PANTALLA).text
    assert '<section id="retiradas"' in html
    assert "api('PATCH', '/api/panel/lineas/'" in html
    assert "api('POST', '/api/panel/lineas/orden'" in html
    for texto in ("'Subir ' + l.nombre", "'Bajar ' + l.nombre", "'Retirar ' + l.nombre", "'Devolver ' + l.nombre"):
        assert texto in html
    assert "if (!esAdmin) return li;" in html


@pytest.mark.parametrize("compositor", ["prototipos/mail/compositor.html",
                                        "app/static/email/compositor.html"])
def test_el_compositor_enlaza_la_pantalla_y_pide_el_catalogo(compositor):
    html = (RAIZ / compositor).read_text(encoding="utf-8")
    assert 'href="/panel/lineas"' in html
    assert "api('/api/catalogo')" in html
    assert "M.ponCatalogo(" in html
