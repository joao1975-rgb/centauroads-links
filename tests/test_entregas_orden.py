"""
La entrega guarda el orden de sus espacios y su enlace manda en `/p/` (especificación 009).

- `orden_espacios` es una lista de ids separados por comas, con la forma de las líneas (y de los
  productos a medida). Un PUT que no lo manda no lo borra; "" vuelve al orden de siempre.
- El enlace del cliente (`/p/<slug>`) lleva a lo último guardado: es lo que el guardado automático del
  compositor mantiene al día.
"""

import secrets

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import sesion
from app.database import SessionLocal

NUEVA = {"titulo": "Orden (prueba)", "canva_url": "https://canva.link/orden-prueba",
         "contacto": {"nombre": "Ana Orden (prueba)", "empresa": "Empresa Orden (prueba)",
                      "email": "", "origen": ""}}
NAVEGADOR = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}


@pytest.fixture(scope="module")
def cliente():
    with SessionLocal() as db:
        u = models.PanelUser(email="orden-%s@ejemplo.test" % secrets.token_hex(4), nombre="Orden",
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


def test_la_entrega_guarda_y_devuelve_el_orden(cliente):
    orden = "totem,medida--aaaa00000001,vallas"
    d = _crea(cliente, orden_espacios=orden)
    assert d["orden_espacios"] == orden
    assert cliente.get("/api/entregas/%d" % d["id"]).json()["orden_espacios"] == orden


def test_sin_orden_queda_vacio(cliente):
    assert _crea(cliente)["orden_espacios"] == ""


@pytest.mark.parametrize("malo", ["../etc", "Vallas", "a b", ",".join(["x%d" % i for i in range(61)])])
def test_un_orden_con_ids_raros_se_rechaza(cliente, malo):
    r = cliente.post("/api/entregas", json=dict(NUEVA, orden_espacios=malo))
    assert r.status_code == 422


def test_un_put_sin_orden_no_lo_borra_y_vacio_lo_quita(cliente):
    d = _crea(cliente, orden_espacios="led,vallas")
    r = cliente.put("/api/entregas/%d" % d["id"], json=dict(NUEVA, titulo="Otro título"))
    assert r.status_code == 200 and r.json()["orden_espacios"] == "led,vallas"
    r = cliente.put("/api/entregas/%d" % d["id"], json=dict(NUEVA, orden_espacios=""))
    assert r.json()["orden_espacios"] == ""


def test_cambiar_el_enlace_cambia_adonde_lleva_el_enlace_del_cliente(cliente):
    d = _crea(cliente)
    publico = TestClient(app_main.app)
    r = publico.get(d["enlace"], headers=NAVEGADOR, follow_redirects=False)
    assert r.headers["location"] == "https://canva.link/orden-prueba"
    cliente.put("/api/entregas/%d" % d["id"], json=dict(NUEVA, canva_url="https://canva.link/la-nueva"))
    r = publico.get(d["enlace"], headers=NAVEGADOR, follow_redirects=False)
    assert r.headers["location"] == "https://canva.link/la-nueva"
