"""
La guía personalizada (plantilla I) en el servidor (especificación 012, T1201).

- La entrega guarda su formato (`H` por defecto, `I`) y, en la I, la guía: textos y hasta tres fases,
  cada una con su producto (una línea del catálogo, sin repetir).
- Lo demás es la H: `servicios`/`orden_espacios` (las fases encendidas), el enlace `/p/<slug>` y los
  enlaces propios `/p/<slug>/<producto>` (010) funcionan igual.
- Una H sigue siendo una H: sin formato ni guía.
"""

import secrets

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import sesion
from app.database import SessionLocal

NUEVA = {"titulo": "Guía (prueba)", "canva_url": "https://canva.link/guia-prueba",
         "contacto": {"nombre": "Ana Guía (prueba)", "empresa": "Empresa Guía (prueba)",
                      "email": "", "origen": ""}}
ROBOT = {"User-Agent": "WhatsApp/2.23"}


def _fase(clave, linea, on=True, **extra):
    f = {"clave": clave, "on": on, "fase": "Fase (prueba)", "titulo": "Que te %s" % clave,
         "texto": "Texto (prueba)", "etiqueta": "Etiqueta", "detalle": "Detalle", "linea": linea}
    f.update(extra)
    return f


def _guia(*fases):
    return {"entrada": "Entrada (prueba)", "saludo": "Hola {destinatario},", "parrafo": "Párrafo",
            "caja_titulo": "Caja", "caja_texto": "Texto de la caja", "cta_texto": "Cuéntame",
            "boton": "Escríbeme", "fases": list(fases)}


GUIA = _guia(_fase("conozcan", "totem"), _fase("recuerden", "led"), _fase("compren", "rider", on=False))


@pytest.fixture(scope="module")
def cliente():
    with SessionLocal() as db:
        u = models.PanelUser(email="guia-%s@ejemplo.test" % secrets.token_hex(4), nombre="Guía",
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


def test_una_h_sigue_siendo_h(cliente):
    d = _crea(cliente)
    assert d["formato"] == "H" and d["guia"] is None


def test_la_guia_se_guarda_y_vuelve_igual(cliente):
    d = _crea(cliente, formato="I", guia=GUIA, servicios="totem,led", orden_espacios="totem,led")
    leida = cliente.get("/api/entregas/%d" % d["id"]).json()
    assert leida["formato"] == "I"
    assert leida["guia"]["entrada"] == "Entrada (prueba)"
    assert [f["linea"] for f in leida["guia"]["fases"]] == ["totem", "led", "rider"]
    assert [f["on"] for f in leida["guia"]["fases"]] == [True, True, False]
    assert leida["servicios"] == "totem,led"


def test_un_put_cambia_la_guia_y_sin_guia_no_la_borra(cliente):
    d = _crea(cliente, formato="I", guia=GUIA)
    otra = _guia(_fase("recuerden", "vallas", titulo="Título nuevo"))
    r = cliente.put("/api/entregas/%d" % d["id"], json=dict(NUEVA, formato="I", guia=otra))
    assert r.status_code == 200, r.text
    assert r.json()["guia"]["fases"][0]["titulo"] == "Título nuevo"
    r = cliente.put("/api/entregas/%d" % d["id"], json=dict(NUEVA, titulo="Otro"))
    assert r.json()["formato"] == "I" and r.json()["guia"]["fases"][0]["linea"] == "vallas"


@pytest.mark.parametrize("guia", [
    _guia(*[_fase("conozcan", "l%d" % i) for i in range(4)]),                  # más de tres
    _guia(_fase("conozcan", "totem"), _fase("recuerden", "totem")),             # producto repetido
    _guia(_fase("conozcan", "totem"), _fase("conozcan", "led")),                # fase repetida
    _guia(_fase("otra", "totem")),                                              # fase desconocida
    _guia(_fase("conozcan", "../etc")),                                         # línea con forma rara
    _guia(_fase("conozcan", "totem", titulo="x" * 301)),                        # texto desmedido
])
def test_una_guia_mal_formada_se_rechaza(cliente, guia):
    r = cliente.post("/api/entregas", json=dict(NUEVA, formato="I", guia=guia))
    assert r.status_code == 422, r.text


def test_un_formato_desconocido_se_rechaza(cliente):
    assert cliente.post("/api/entregas", json=dict(NUEVA, formato="Z")).status_code == 422


def test_el_enlace_propio_de_una_fase_funciona_como_en_la_h(cliente):
    d = _crea(cliente, formato="I", guia=GUIA, servicios="totem,led")
    publico = TestClient(app_main.app)
    r = publico.get(d["enlace"] + "/led", headers=ROBOT)
    assert r.status_code == 200 and "og:image" in r.text
    # Una fase apagada no está en los servicios: su enlace propio no existe.
    assert publico.get(d["enlace"] + "/rider", headers=ROBOT).status_code == 404


def test_marcar_entregada_anota_el_formato_i(cliente):
    d = _crea(cliente, formato="I", guia=GUIA)
    assert cliente.post("/api/entregas/%d/entregada" % d["id"]).status_code == 200
    with SessionLocal() as db:
        ultima = db.query(models.Delivery).filter(models.Delivery.link_id == db.get(
            models.Entrega, d["id"]).link_id).order_by(models.Delivery.id.desc()).first()
        assert ultima.formato == "I"
