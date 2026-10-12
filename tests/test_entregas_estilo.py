"""
La entrega guarda el estilo de su título (especificación 007, US3).

La pareja de tipografías y el tamaño del título viajan con la entrega, como el rótulo y el texto corto
(004): así, al abrirla en otra computadora, el correo sale igual. Solo valen los valores que conoce el
motor; un PUT que no los manda no borra lo guardado, y "" vuelve a lo de hoy.
"""

import secrets

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import sesion
from app.database import SessionLocal

NUEVA = {"titulo": "Estilo (prueba)", "canva_url": "https://canva.link/estilo-prueba",
         "contacto": {"nombre": "Ana Estilo (prueba)", "empresa": "Empresa Estilo (prueba)",
                      "email": "", "origen": ""}}


@pytest.fixture(scope="module")
def cliente():
    with SessionLocal() as db:
        u = models.PanelUser(email="estilo-%s@ejemplo.test" % secrets.token_hex(4), nombre="Estilo",
                             rol="comercial", activo=True)
        db.add(u)
        db.commit()
        c = TestClient(app_main.app)
        c.cookies.set(sesion.COOKIE, sesion.crear(u.id, u.email))
        return c


def _crea(cliente, **extra):
    r = cliente.post("/api/entregas", json=dict(NUEVA, **extra))
    assert r.status_code == 200, r.text
    return r.json()


def test_la_entrega_guarda_y_devuelve_el_estilo_del_titulo(cliente):
    d = _crea(cliente, tipografia="editorial", tam_titulo="grande")
    assert d["tipografia"] == "editorial" and d["tam_titulo"] == "grande"
    leida = cliente.get("/api/entregas/%d" % d["id"]).json()
    assert leida["tipografia"] == "editorial" and leida["tam_titulo"] == "grande"


def test_sin_elegir_nada_queda_vacio_que_es_lo_de_hoy(cliente):
    d = _crea(cliente)
    assert d["tipografia"] is None and d["tam_titulo"] is None


@pytest.mark.parametrize("campo,valor", [("tipografia", "comic-sans"), ("tipografia", "constructor"),
                                         ("tam_titulo", "gigante")])
def test_solo_valen_los_valores_que_conoce_el_motor(cliente, campo, valor):
    r = cliente.post("/api/entregas", json=dict(NUEVA, **{campo: valor}))
    assert r.status_code == 422


def test_un_put_sin_estilo_no_lo_borra_y_vacio_vuelve_a_lo_de_hoy(cliente):
    d = _crea(cliente, tipografia="impacto", tam_titulo="maximo")
    r = cliente.put("/api/entregas/%d" % d["id"], json=dict(NUEVA, titulo="Otro título"))
    assert r.status_code == 200 and r.json()["tipografia"] == "impacto" and r.json()["tam_titulo"] == "maximo"
    r = cliente.put("/api/entregas/%d" % d["id"], json=dict(NUEVA, tipografia="", tam_titulo=""))
    assert r.json()["tipografia"] is None and r.json()["tam_titulo"] is None
