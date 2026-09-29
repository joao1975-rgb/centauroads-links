"""
CORS restringido a dominios propios (spec 001 del ecosistema, tareas T054 y T059).

Antes, `allow_origins=["*"]` dejaba que cualquier web llamara a la API desde el navegador de un
visitante. Ahora la lista sale de la variable `CORS_ORIGINS` (orígenes separados por comas). Vacía
significa «sin orígenes cruzados»: el panel se sirve desde el mismo dominio y no los necesita.

La conftest fija CORS_ORIGINS con un origen propio de prueba antes de importar la app.
"""

import os

from fastapi.testclient import TestClient

from app.main import app, origenes_cors

PROPIO = os.environ["CORS_ORIGINS"].split(",")[0].strip()
AJENO = "https://sitio-ajeno.example"


def _cliente():
    return TestClient(app)


# ---------------------------------------------------------------------------
# Lectura de la variable
# ---------------------------------------------------------------------------

def test_variable_vacia_no_permite_ningun_origen():
    assert origenes_cors("") == []
    assert origenes_cors("   ") == []
    assert origenes_cors(None) == []


def test_variable_con_varios_origenes_se_normaliza():
    valor = " https://links.centauroads.com , https://centauroads.com/ ,,"
    assert origenes_cors(valor) == ["https://links.centauroads.com", "https://centauroads.com"]


def test_el_comodin_nunca_se_acepta():
    assert origenes_cors("*") == []
    assert origenes_cors("*, https://centauroads.com") == ["https://centauroads.com"]


# ---------------------------------------------------------------------------
# Comportamiento de la app real
# ---------------------------------------------------------------------------

def test_origen_ajeno_no_recibe_cabeceras_de_permiso():
    respuesta = _cliente().get("/health", headers={"Origin": AJENO})

    assert "access-control-allow-origin" not in respuesta.headers


def test_preflight_de_origen_ajeno_es_rechazado():
    respuesta = _cliente().options(
        "/api/links",
        headers={"Origin": AJENO, "Access-Control-Request-Method": "POST"},
    )

    assert respuesta.headers.get("access-control-allow-origin") != AJENO
    assert respuesta.headers.get("access-control-allow-origin") != "*"
    assert respuesta.status_code >= 400


def test_origen_propio_recibe_permiso():
    respuesta = _cliente().get("/health", headers={"Origin": PROPIO})

    assert respuesta.headers.get("access-control-allow-origin") == PROPIO


def test_preflight_de_origen_propio_es_aceptado():
    respuesta = _cliente().options(
        "/api/links",
        headers={"Origin": PROPIO, "Access-Control-Request-Method": "POST"},
    )

    assert respuesta.status_code == 200
    assert respuesta.headers.get("access-control-allow-origin") == PROPIO
