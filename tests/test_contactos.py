"""
Editar y borrar contactos (petición de la propietaria, 2026-10-07).

Decisiones:
- «Borrar» **retira** el contacto de la lista: deja de salir para elegir, pero no se borra la fila,
  porque sus entregas guardadas y el historial de aperturas dependen de él. Se puede devolver.
- Cualquiera del equipo puede editar y retirar (los contactos son del equipo, no de quien los creó).
- Nombre y empresa no pueden quedar vacíos: el correo los dice en el saludo y en el texto.
"""

import secrets

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import sesion
from app.database import SessionLocal


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def comercial(db):
    u = db.query(models.PanelUser).filter(models.PanelUser.email == "comercial-ctc@ejemplo.test").first()
    if not u:
        u = models.PanelUser(email="comercial-ctc@ejemplo.test", nombre="comercial-ctc", rol="comercial", activo=True)
        db.add(u)
        db.commit()
        db.refresh(u)
    c = TestClient(app_main.app)
    c.cookies.set(sesion.COOKIE, sesion.crear(u.id, u.email))
    return c


@pytest.fixture()
def contacto(db):
    c = models.Contact(nombre="Ana Prueba", empresa="Empresa Prueba", email="ana@ejemplo.test",
                       token=secrets.token_urlsafe(24))
    db.add(c)
    db.commit()
    db.refresh(c)
    yield c
    db.delete(c)
    db.commit()


def _ids(r):
    return [x["id"] for x in r.json()]


def test_sin_sesion_no_se_tocan_los_contactos(contacto):
    anonimo = TestClient(app_main.app)
    assert anonimo.put("/api/contactos/%d" % contacto.id, json={"nombre": "x"}).status_code == 401
    assert anonimo.delete("/api/contactos/%d" % contacto.id).status_code == 401


def test_cualquiera_del_equipo_edita_un_contacto(comercial, contacto):
    r = comercial.put("/api/contactos/%d" % contacto.id,
                      json={"nombre": "  Ana María Prueba ", "empresa": "Otra Empresa", "email": "ana.maria@ejemplo.test"})
    assert r.status_code == 200
    assert r.json() == {"id": contacto.id, "nombre": "Ana María Prueba", "empresa": "Otra Empresa",
                        "email": "ana.maria@ejemplo.test", "retirado": False}
    fila = [x for x in comercial.get("/api/contactos").json() if x["id"] == contacto.id][0]
    assert fila["nombre"] == "Ana María Prueba" and fila["empresa"] == "Otra Empresa"


def test_solo_cambia_lo_que_llega(comercial, contacto):
    r = comercial.put("/api/contactos/%d" % contacto.id, json={"email": ""})
    assert r.json()["nombre"] == "Ana Prueba" and r.json()["email"] == ""


@pytest.mark.parametrize("cambio,frase", [
    ({"nombre": "  "}, "nombre"), ({"empresa": ""}, "empresa"), ({"email": "no-es-un-correo"}, "correo"),
])
def test_nombre_y_empresa_no_quedan_vacios_y_el_correo_es_un_correo(comercial, contacto, cambio, frase):
    r = comercial.put("/api/contactos/%d" % contacto.id, json=cambio)
    assert r.status_code == 400 and frase in r.json()["detail"].lower()


def test_borrar_lo_retira_de_la_lista_sin_perderlo(comercial, contacto, db):
    assert contacto.id in _ids(comercial.get("/api/contactos"))
    r = comercial.delete("/api/contactos/%d" % contacto.id)
    assert r.status_code == 200 and r.json()["retirado"] is True
    assert contacto.id not in _ids(comercial.get("/api/contactos"))
    assert contacto.id in _ids(comercial.get("/api/contactos", params={"retirados": "true"}))
    # La fila sigue ahí: sus entregas y su historial no se rompen.
    db.expire_all()
    assert db.get(models.Contact, contacto.id) is not None


def test_un_retirado_se_puede_devolver(comercial, contacto):
    comercial.delete("/api/contactos/%d" % contacto.id)
    r = comercial.put("/api/contactos/%d" % contacto.id, json={"retirado": False})
    assert r.status_code == 200 and r.json()["retirado"] is False
    assert contacto.id in _ids(comercial.get("/api/contactos"))


def test_un_contacto_que_no_existe(comercial):
    assert comercial.put("/api/contactos/99999999", json={"nombre": "x"}).status_code == 404
    assert comercial.delete("/api/contactos/99999999").status_code == 404


def test_desde_otro_sitio_no_se_toca_nada(comercial, contacto):
    r = comercial.delete("/api/contactos/%d" % contacto.id, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    assert contacto.id in _ids(comercial.get("/api/contactos"))


# --- El compositor -------------------------------------------------------------------------------

@pytest.mark.parametrize("ruta", ["prototipos/mail/compositor.html", "app/static/email/compositor.html"])
def test_cada_contacto_lleva_editar_y_borrar_y_el_saludo_esta_junto_al_contacto(ruta):
    from pathlib import Path
    html = (Path(__file__).resolve().parents[1] / ruta).read_text(encoding="utf-8")
    i = html.index("const filaContacto = c =>")
    fila = html[i:html.index("return li;\n      };", i)]
    assert "botonEl('Editar'" in fila and "botonEl('Borrar'" in fila
    assert "confirm(" in fila and "cambiaContacto(c, 'DELETE')" in fila
    assert "'/api/contactos/' + c.id" in html
    # Ya no es un desplegable: un <option> no puede llevar botones.
    assert "'— elige un contacto —'" not in html
    # El saludo se edita en «Para quién», no plegado al final del panel.
    assert "inputEl('bloques.saludo.texto', 'Saludo', 'textarea')" in html
