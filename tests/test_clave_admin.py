"""
T075/T076 · La clave de administración (ADMIN_KEY) no debe filtrarse.

- Si no hay ADMIN_KEY, la app genera una y la guarda en data/admin.key. El log debe decir DÓNDE
  quedó, nunca la clave: los logs acaban en EasyPanel, en agregadores y en capturas de pantalla.
- El fichero de la clave se deja con permisos 600 (solo el dueño lo lee).
- La clave solo se acepta en la cabecera X-Admin-Key. `?admin_key=` en la URL queda en los logs
  de acceso del proxy y en el historial del navegador; ni el panel ni ningún script del repo lo
  usaban, así que se retiró.
"""

import logging
import os
import stat

import pytest
from fastapi.testclient import TestClient

from app import main as app_main


@pytest.fixture
def sin_clave(tmp_path, monkeypatch):
    """Arranque sin ADMIN_KEY ni fichero: obliga a generar una clave nueva."""
    ruta = tmp_path / "datos" / "admin.key"
    monkeypatch.setattr(app_main, "KEY_FILE", str(ruta))
    monkeypatch.delenv("ADMIN_KEY", raising=False)
    return ruta


def test_la_clave_generada_no_se_escribe_en_el_log(sin_clave, caplog):
    with caplog.at_level(logging.DEBUG):
        generada = app_main.get_admin_password()

    assert sin_clave.read_text() == generada
    assert generada not in caplog.text, "la clave no debe aparecer en el log"
    assert str(sin_clave) in caplog.text, "el log debe indicar dónde quedó guardada"


def test_el_fichero_de_la_clave_queda_con_permisos_600(sin_clave, monkeypatch):
    llamadas = []
    chmod_real = os.chmod

    def espia(ruta, modo, *args, **kwargs):
        llamadas.append((os.fspath(ruta), modo))
        return chmod_real(ruta, modo, *args, **kwargs)

    monkeypatch.setattr(app_main.os, "chmod", espia)
    app_main.get_admin_password()

    assert (str(sin_clave), 0o600) in llamadas
    if os.name != "nt":  # En Windows chmod solo cambia el atributo de solo lectura.
        assert stat.S_IMODE(sin_clave.stat().st_mode) == 0o600


def test_cambiar_la_clave_tambien_deja_permisos_600(sin_clave, monkeypatch):
    llamadas = []
    monkeypatch.setattr(app_main.os, "chmod", lambda ruta, modo: llamadas.append((os.fspath(ruta), modo)))
    app_main.set_admin_password("otra-clave-sintetica")
    assert (str(sin_clave), 0o600) in llamadas


def test_la_clave_en_la_query_ya_no_autentica():
    cliente = TestClient(app_main.app)
    clave = app_main.get_admin_password()

    assert cliente.get("/api/links", params={"admin_key": clave}).status_code == 401
    assert cliente.get("/api/links", headers={"X-Admin-Key": clave}).status_code == 200
