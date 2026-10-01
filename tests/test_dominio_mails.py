"""
mails.centauroads.com: la dirección de la herramienta (2026-09-30).

El mismo servicio responde a dos nombres. `links.` es el del acortador: los enlaces cortos que ya
viajan en correos y WhatsApp no pueden cambiar. `mails.` es la que se da al equipo, y quien la
escribe a secas tiene que llegar a la pantalla de entrada, no a la portada del acortador.
"""

import pytest
from fastapi.testclient import TestClient

from app import main as app_main


@pytest.fixture()
def cliente():
    return TestClient(app_main.app)


def test_mails_a_secas_lleva_a_la_entrada(cliente):
    r = cliente.get("/", headers={"host": "mails.centauroads.com"}, follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/panel/entrar"


def test_links_a_secas_sigue_mostrando_la_portada(cliente):
    r = cliente.get("/", headers={"host": "links.centauroads.com"}, follow_redirects=False)
    assert r.status_code == 200


def test_mails_con_puerto_tambien_lleva_a_la_entrada(cliente):
    r = cliente.get("/", headers={"host": "mails.centauroads.com:443"}, follow_redirects=False)
    assert r.headers.get("location") == "/panel/entrar"


def test_el_panel_responde_igual_en_los_dos_nombres(cliente):
    for host in ("mails.centauroads.com", "links.centauroads.com"):
        r = cliente.get("/panel", headers={"host": host}, follow_redirects=False)
        assert r.headers["location"] == "/panel/entrar", host
