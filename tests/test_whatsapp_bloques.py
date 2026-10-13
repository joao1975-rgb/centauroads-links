"""
El enlace propio de cada servicio de una entrega: `/p/<slug>/<espacio>` (especificación 010).

WhatsApp dibuja la tarjeta solo del primer enlace de cada mensaje, así que cada servicio va en su propio
mensaje con su enlace. Este fichero vigila:

1. **La tarjeta** (lo que lee el robot): nombre, línea y foto del espacio, con lo propio de la entrega
   (004) o la primera página de su carrusel; imagen siempre absoluta.
2. **El destino** (la persona): la presentación del espacio, o la de la propuesta si no tiene; la
   apertura se apunta con su espacio y cuenta como clic de la entrega. El robot no cuenta.
3. **Solo sus espacios**: uno no incluido, de otra entrega o inventado da 404.
"""

import re
import secrets

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import sesion
from app.database import SessionLocal
from tests.test_entregas_espacios import _elige, _sube

ROBOT = {"User-Agent": "WhatsApp/2.23.20 A"}
PERSONA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}
PROPUESTA = "https://canva.link/propuesta-bloques"
CANVA_LINEA = "https://canva.link/linea-bloques"


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture(scope="module")
def cliente(db):
    u = models.PanelUser(email="bloques-%s@ejemplo.test" % secrets.token_hex(4), nombre="Bloques",
                         rol="comercial", activo=True)
    db.add(u)
    db.commit()
    c = TestClient(app_main.app)
    c.cookies.set(sesion.COOKIE, sesion.crear(u.id, u.email))
    return c


@pytest.fixture(scope="module")
def linea(db):
    l = models.LineaNegocio(id="bloq-%s" % secrets.token_hex(4), nombre="Pantalla de bloques (prueba)",
                            cobertura="Ubicación: Calle de prueba", canva=CANVA_LINEA, img="svc_led.jpg")
    db.add(l)
    db.commit()
    return l.id


@pytest.fixture(scope="module")
def no_incluida(db):
    l = models.LineaNegocio(id="bloq-%s" % secrets.token_hex(4), nombre="Otra (prueba)", canva=CANVA_LINEA)
    db.add(l)
    db.commit()
    return l.id


def _entrega(cliente, db, servicios):
    contacto = models.Contact(nombre="Cliente Bloques (prueba)", email="", empresa="Bloques C.A.",
                              token=secrets.token_urlsafe(24))
    db.add(contacto)
    db.commit()
    r = cliente.post("/api/entregas", json={"titulo": "Propuesta bloques (prueba)", "canva_url": PROPUESTA,
                                            "contact_id": contacto.id, "servicios": servicios})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
def entrega(cliente, db, linea):
    return _entrega(cliente, db, linea)


def _og(html, prop):
    m = re.search(r'<meta property="og:%s" content="([^"]*)">' % prop, html)
    return m.group(1) if m else None


def _publico():
    return TestClient(app_main.app)


# --- La tarjeta (robot) --------------------------------------------------------------------------

def test_la_tarjeta_de_un_espacio_del_catalogo(entrega, linea):
    r = _publico().get("%s/%s" % (entrega["enlace"], linea), headers=ROBOT, follow_redirects=False)
    assert r.status_code == 200
    assert _og(r.text, "title") == "Pantalla de bloques (prueba)"
    assert _og(r.text, "description") == "Ubicación: Calle de prueba"
    assert _og(r.text, "image") == "http://testserver/static/email/svc_led.jpg"


def test_la_imagen_va_con_el_esquema_del_proxy(entrega, linea):
    r = _publico().get("%s/%s" % (entrega["enlace"], linea),
                       headers=dict(ROBOT, **{"X-Forwarded-Proto": "https"}), follow_redirects=False)
    assert _og(r.text, "image").startswith("https://testserver/static/email/")


def test_la_tarjeta_usa_lo_propio_de_la_entrega_y_su_carrusel(cliente, entrega, linea):
    cliente.put("/api/entregas/%d/espacios/%s" % (entrega["id"], linea),
                json={"nombre": "Nombre propio (prueba)", "cobertura": "Línea propia"})
    _sube(cliente, entrega["id"], linea)
    _elige(cliente, entrega["id"], linea, indices=(2, 0))
    r = _publico().get("%s/%s" % (entrega["enlace"], linea), headers=ROBOT, follow_redirects=False)
    assert _og(r.text, "title") == "Nombre propio (prueba)"
    assert _og(r.text, "description") == "Línea propia"
    imagen = _og(r.text, "image")
    # Su portada ligera, hecha al armar el carrusel: una página a 1200 px puede pesar más de lo
    # que WhatsApp acepta para la vista previa.
    assert re.match(r"http://testserver/media/e/[0-9a-f]{32}/espacios/%s/og\.jpg\?v=" % linea, imagen), imagen
    assert _publico().get(imagen.replace("http://testserver", "")).status_code == 200


def test_la_tarjeta_de_un_producto_a_medida(cliente, entrega):
    r = cliente.post("/api/entregas/%d/espacios" % entrega["id"],
                     json={"nombre": "Producto bloques (prueba)", "cobertura": "Feria de prueba"})
    pid = [e for e in r.json()["espacios"] if e["a_medida"]][0]["linea"]
    sin = _publico().get("%s/%s" % (entrega["enlace"], pid), headers=ROBOT, follow_redirects=False)
    assert _og(sin.text, "title") == "Producto bloques (prueba)" and _og(sin.text, "image") is None
    _sube(cliente, entrega["id"], pid)
    _elige(cliente, entrega["id"], pid, indices=(1, 0))
    con = _publico().get("%s/%s" % (entrega["enlace"], pid), headers=ROBOT, follow_redirects=False)
    assert "/espacios/%s/og.jpg" % pid in _og(con.text, "image")


def test_un_carrusel_armado_antes_usa_su_primera_pagina(cliente, entrega, linea):
    """Los armados antes de la 010 no tienen og.jpg: la tarjeta usa su primera página elegida."""
    import os
    from tests.test_entregas_espacios import _fichero
    _sube(cliente, entrega["id"], linea)
    _elige(cliente, entrega["id"], linea, indices=(1, 0))
    os.remove(_fichero(entrega["id"], "og.jpg", linea))
    r = _publico().get("%s/%s" % (entrega["enlace"], linea), headers=ROBOT, follow_redirects=False)
    assert "/espacios/%s/p1.jpg" % linea in _og(r.text, "image")


def test_el_robot_no_cuenta_como_apertura(entrega, linea, db):
    _publico().get("%s/%s" % (entrega["enlace"], linea), headers=ROBOT, follow_redirects=False)
    assert db.query(models.AperturaEspacio).filter(
        models.AperturaEspacio.entrega_id == entrega["id"]).count() == 0


# --- El destino (persona) ------------------------------------------------------------------------

def test_la_persona_va_a_la_presentacion_del_espacio_y_se_apunta(entrega, linea, db):
    antes = db.get(models.Entrega, entrega["id"]).link.click_count or 0
    r = _publico().get("%s/%s?c=tok123" % (entrega["enlace"], linea), headers=PERSONA, follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == CANVA_LINEA
    db.expire_all()
    ap = db.query(models.AperturaEspacio).filter(models.AperturaEspacio.entrega_id == entrega["id"]).all()
    assert [(a.linea, a.contact_token) for a in ap] == [(linea, "tok123")]
    assert db.get(models.Entrega, entrega["id"]).link.click_count == antes + 1


def test_con_enlace_propio_va_a_ese(cliente, entrega, linea):
    cliente.put("/api/entregas/%d/espacios/%s" % (entrega["id"], linea),
                json={"canva_url": "https://canva.link/propio-bloques"})
    r = _publico().get("%s/%s" % (entrega["enlace"], linea), headers=PERSONA, follow_redirects=False)
    assert r.headers["location"] == "https://canva.link/propio-bloques"


def test_sin_enlace_va_a_la_propuesta(cliente, entrega):
    r = cliente.post("/api/entregas/%d/espacios" % entrega["id"], json={"nombre": "Sin enlace (prueba)"})
    pid = [e for e in r.json()["espacios"] if e["a_medida"]][0]["linea"]
    r = _publico().get("%s/%s" % (entrega["enlace"], pid), headers=PERSONA, follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == PROPUESTA


# --- Solo sus espacios ---------------------------------------------------------------------------

def test_un_espacio_no_incluido_da_404(entrega, no_incluida):
    for h in (ROBOT, PERSONA):
        assert _publico().get("%s/%s" % (entrega["enlace"], no_incluida), headers=h,
                              follow_redirects=False).status_code == 404


def test_un_producto_de_otra_entrega_da_404(cliente, entrega, db, linea):
    r = cliente.post("/api/entregas/%d/espacios" % entrega["id"], json={"nombre": "Ajeno (prueba)"})
    pid = [e for e in r.json()["espacios"] if e["a_medida"]][0]["linea"]
    otra = _entrega(cliente, db, linea)
    assert _publico().get("%s/%s" % (otra["enlace"], pid), headers=ROBOT,
                          follow_redirects=False).status_code == 404


@pytest.mark.parametrize("raro", ["no-existe", "medida--000000000000", "..%2F..%2Fetc", "MAYUS"])
def test_un_espacio_inventado_da_404(entrega, raro):
    assert _publico().get("%s/%s" % (entrega["enlace"], raro), headers=PERSONA,
                          follow_redirects=False).status_code == 404


def test_un_enlace_inactivo_da_404(entrega, linea, db):
    e = db.get(models.Entrega, entrega["id"])
    e.link.is_active = False
    db.commit()
    assert _publico().get("%s/%s" % (entrega["enlace"], linea), headers=ROBOT,
                          follow_redirects=False).status_code == 404
