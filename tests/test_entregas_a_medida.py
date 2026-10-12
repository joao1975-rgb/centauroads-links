"""
Productos a medida en la entrega H (especificación 008, servidor).

Un producto a medida es un espacio más de la entrega (tabla de la 004) con un id `medida--…` que el
catálogo no puede producir. Lo que vigila este fichero:

1. **Solo de su entrega.** Un id a medida de otra entrega —o inventado— da 404 en todas las rutas,
   igual que una línea que no está en el catálogo.
2. **Sus reglas**: nombre obligatorio, enlace con la regla de siempre, como mucho 5.
3. **Pasar al catálogo** lo hace solo un administrador, no duplica nombres y deja el espacio de la
   entrega convertido en el del catálogo con su carrusel.
"""

import os
import secrets

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import sesion
from tests.test_entregas_espacios import _elige, _espacio, _fichero, _sube

ENLACE = "https://www.canva.com/design/AMEDIDA/view"


@pytest.fixture(scope="module")
def db():
    from app.database import SessionLocal
    s = SessionLocal()
    yield s
    s.close()


def _cliente(db, rol):
    usuario = models.PanelUser(email="med-%s@ejemplo.test" % secrets.token_hex(4),
                               nombre="Prueba", rol=rol, activo=True)
    db.add(usuario)
    db.commit()
    c = TestClient(app_main.app)
    c.cookies.set(sesion.COOKIE, sesion.crear(usuario.id, usuario.email))
    return c


@pytest.fixture(scope="module")
def cliente(db):
    return _cliente(db, "comercial")


@pytest.fixture(scope="module")
def admin(db):
    return _cliente(db, "admin")


@pytest.fixture(scope="module")
def ajeno(db):
    return _cliente(db, "comercial")


def _nueva_entrega(cliente, db):
    contacto = models.Contact(nombre="Cliente A Medida", email="m@ejemplo.test",
                              empresa="A Medida C.A.", token=secrets.token_urlsafe(24))
    db.add(contacto)
    db.commit()
    r = cliente.post("/api/entregas", json={
        "titulo": "Propuesta a medida", "canva_url": ENLACE, "contact_id": contacto.id})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture
def entrega(cliente, db):
    return _nueva_entrega(cliente, db)


def _alta(cliente, entrega_id, **campos):
    return cliente.post("/api/entregas/%d/espacios" % entrega_id, json=campos)


def _nombre():
    return "Pantalla en evento %s (prueba)" % secrets.token_hex(3)


def _a_medida(salida):
    return [e for e in salida["espacios"] if e["a_medida"]]


def _producto(cliente, entrega_id, **campos):
    """Da de alta uno y devuelve su id."""
    campos.setdefault("nombre", _nombre())
    r = _alta(cliente, entrega_id, **campos)
    assert r.status_code == 201, r.text
    return _a_medida(r.json())[-1]["linea"]


# --- US1: añadirlo ----------------------------------------------------------------------------

def test_alta_con_nombre_texto_y_enlace(cliente, entrega):
    nombre = _nombre()
    r = _alta(cliente, entrega["id"], nombre=nombre, cobertura="Feria de prueba", canva_url=ENLACE)
    assert r.status_code == 201, r.text
    [p] = _a_medida(r.json())
    assert p["linea"].startswith("medida--")
    assert (p["nombre"], p["cobertura"], p["canva_url"]) == (nombre, "Feria de prueba", ENLACE)
    assert p["carrusel"] is None and p["paginas"] == []


def test_un_espacio_del_catalogo_no_es_a_medida(cliente, entrega, db):
    linea = models.LineaNegocio(id="med-%s" % secrets.token_hex(4), nombre=_nombre(),
                                cobertura="De serie", canva=ENLACE)
    db.add(linea)
    db.commit()
    r = cliente.put("/api/entregas/%d/espacios/%s" % (entrega["id"], linea.id),
                    json={"cobertura": "Propia"})
    assert r.status_code == 200, r.text
    assert _espacio(r.json(), linea.id)["a_medida"] is False


@pytest.mark.parametrize("nombre", ["", "   "])
def test_sin_nombre_no_se_crea(cliente, entrega, nombre):
    r = _alta(cliente, entrega["id"], nombre=nombre)
    assert r.status_code == 400
    assert _a_medida(cliente.get("/api/entregas/%d" % entrega["id"]).json()) == []


def test_un_enlace_sin_https_se_rechaza(cliente, entrega):
    r = _alta(cliente, entrega["id"], nombre=_nombre(), canva_url="canva.com/algo")
    assert r.status_code == 400
    assert "https://" in r.json()["detail"]


def test_como_mucho_cinco(cliente, entrega):
    for _ in range(5):
        _producto(cliente, entrega["id"])
    r = _alta(cliente, entrega["id"], nombre=_nombre())
    assert r.status_code == 409
    assert "5" in r.json()["detail"]
    assert len(_a_medida(cliente.get("/api/entregas/%d" % entrega["id"]).json())) == 5


def test_salen_en_el_orden_en_que_se_anadieron(cliente, entrega):
    ids = [_producto(cliente, entrega["id"]) for _ in range(3)]
    salida = cliente.get("/api/entregas/%d" % entrega["id"]).json()
    assert [e["linea"] for e in _a_medida(salida)] == ids


def test_su_carrusel_se_arma_con_la_galeria(cliente, entrega):
    linea = _producto(cliente, entrega["id"])
    assert _sube(cliente, entrega["id"], linea).status_code == 200
    r = _elige(cliente, entrega["id"], linea, indices=(1, 0))
    assert r.status_code == 200, r.text
    p = _espacio(r.json(), linea)
    assert p["a_medida"] is True and p["efecto"] == "barrido"
    assert p["carrusel"] and "/espacios/%s/carrusel.gif" % linea in p["carrusel"]
    assert [x["orden"] for x in p["paginas"]] == [0, 1]
    assert os.path.isfile(_fichero(entrega["id"], "carrusel.gif", linea))


def test_el_de_otra_entrega_da_404_en_todas_las_rutas(cliente, entrega, db):
    linea = _producto(cliente, entrega["id"])
    otra = _nueva_entrega(cliente, db)["id"]
    base = "/api/entregas/%d/espacios/%s" % (otra, linea)
    assert cliente.put(base, json={"nombre": "x"}).status_code == 404
    assert cliente.delete(base).status_code == 404
    assert _sube(cliente, otra, linea).status_code == 404
    assert _elige(cliente, otra, linea).status_code == 404
    # Y en la suya sigue intacto.
    assert _espacio(cliente.get("/api/entregas/%d" % entrega["id"]).json(), linea)


def test_un_id_a_medida_inventado_da_404(cliente, entrega):
    r = cliente.put("/api/entregas/%d/espacios/medida--00000000" % entrega["id"], json={"nombre": "x"})
    assert r.status_code == 404


def test_quien_no_es_dueno_no_lo_ve_ni_lo_toca(cliente, ajeno, entrega):
    linea = _producto(cliente, entrega["id"])
    assert _alta(ajeno, entrega["id"], nombre=_nombre()).status_code == 404
    assert ajeno.put("/api/entregas/%d/espacios/%s" % (entrega["id"], linea),
                     json={"nombre": "x"}).status_code == 404
    assert ajeno.delete("/api/entregas/%d/espacios/%s" % (entrega["id"], linea)).status_code == 404


def test_sin_sesion_nada(entrega):
    r = TestClient(app_main.app).post("/api/entregas/%d/espacios" % entrega["id"], json={"nombre": "x"})
    assert r.status_code == 401


# --- US2: editarlo, quitarlo, recuperarlo ------------------------------------------------------

def test_editar_nombre_texto_y_enlace(cliente, entrega):
    linea = _producto(cliente, entrega["id"], cobertura="Antes")
    ruta = "/api/entregas/%d/espacios/%s" % (entrega["id"], linea)
    r = cliente.put(ruta, json={"nombre": "Nuevo nombre (prueba)", "canva_url": ENLACE})
    assert r.status_code == 200, r.text
    p = _espacio(r.json(), linea)
    assert (p["nombre"], p["cobertura"], p["canva_url"]) == ("Nuevo nombre (prueba)", "Antes", ENLACE)
    # Vaciar el texto lo deja vacío; la fila sigue (no hay catálogo al que volver).
    p = _espacio(cliente.put(ruta, json={"cobertura": "", "canva_url": ""}).json(), linea)
    assert p is not None and p["cobertura"] is None and p["canva_url"] is None


def test_el_nombre_no_se_puede_vaciar(cliente, entrega):
    nombre = _nombre()
    linea = _producto(cliente, entrega["id"], nombre=nombre)
    r = cliente.put("/api/entregas/%d/espacios/%s" % (entrega["id"], linea), json={"nombre": "  "})
    assert r.status_code == 400
    assert _espacio(cliente.get("/api/entregas/%d" % entrega["id"]).json(), linea)["nombre"] == nombre


def test_quitar_lo_borra_y_deja_sus_imagenes(cliente, entrega):
    linea = _producto(cliente, entrega["id"])
    _sube(cliente, entrega["id"], linea)
    _elige(cliente, entrega["id"], linea)
    r = cliente.delete("/api/entregas/%d/espacios/%s" % (entrega["id"], linea))
    assert r.status_code == 200
    assert _espacio(r.json(), linea) is None
    # Un correo ya enviado puede apuntar a ellas.
    assert os.path.isfile(_fichero(entrega["id"], "carrusel.gif", linea))
    # Y ya no es de esta entrega: sus rutas dan 404.
    assert _elige(cliente, entrega["id"], linea).status_code == 404


def test_abrir_la_entrega_los_devuelve_con_su_carrusel(cliente, entrega):
    linea = _producto(cliente, entrega["id"], cobertura="Con carrusel")
    _sube(cliente, entrega["id"], linea)
    _elige(cliente, entrega["id"], linea)
    p = _espacio(cliente.get("/api/entregas/%d" % entrega["id"]).json(), linea)
    assert p["a_medida"] and p["cobertura"] == "Con carrusel" and p["carrusel"]
    assert cliente.get(p["carrusel"]).status_code == 200


# --- US3: pasar al catálogo --------------------------------------------------------------------

def _pasa(cliente, entrega_id, linea):
    return cliente.post("/api/entregas/%d/espacios/%s/catalogo" % (entrega_id, linea))


def test_un_administrador_lo_pasa_al_catalogo(cliente, admin, entrega, db):
    nombre = _nombre()
    linea = _producto(cliente, entrega["id"], nombre=nombre, cobertura="Feria de prueba",
                      canva_url=ENLACE)
    _sube(cliente, entrega["id"], linea)
    _elige(cliente, entrega["id"], linea)

    r = _pasa(admin, entrega["id"], linea)
    assert r.status_code == 200, r.text
    nueva = r.json()["linea"]
    assert not nueva.startswith("medida--")

    db.expire_all()
    fila = db.get(models.LineaNegocio, nueva)
    assert (fila.nombre, fila.cobertura, fila.canva) == (nombre, "Feria de prueba", ENLACE)
    assert fila.plantillas == "ABCDEFGH" and fila.activa
    assert fila.img.startswith("/media/lineas/") and fila.alt == nombre
    assert admin.get(fila.img).status_code == 200

    salida = r.json()["entrega"]
    assert _espacio(salida, linea) is None
    p = _espacio(salida, nueva)
    assert p["a_medida"] is False
    # Sus textos son ya los del catálogo: la fila no guarda nada propio salvo el carrusel.
    assert p["nombre"] is None and p["cobertura"] is None and p["canva_url"] is None
    assert p["carrusel"] and "/espacios/%s/carrusel.gif" % nueva in p["carrusel"]
    assert admin.get(p["carrusel"]).status_code == 200
    assert nueva in salida["servicios"].split(",")
    # La carpeta vieja sigue: un correo ya enviado puede apuntar a ella.
    assert os.path.isfile(_fichero(entrega["id"], "carrusel.gif", linea))
    # Y la línea ya sale en el catálogo de todo el equipo.
    assert any(l["id"] == nueva for l in cliente.get("/api/catalogo").json()["lineas"])


def test_sin_carrusel_la_linea_queda_sin_foto(cliente, admin, entrega, db):
    linea = _producto(cliente, entrega["id"])
    r = _pasa(admin, entrega["id"], linea)
    assert r.status_code == 200, r.text
    db.expire_all()
    assert db.get(models.LineaNegocio, r.json()["linea"]).img == ""


def test_un_nombre_que_ya_esta_en_el_catalogo_no_se_duplica(cliente, admin, entrega, db):
    nombre = _nombre()
    db.add(models.LineaNegocio(id="med-%s" % secrets.token_hex(4), nombre=nombre))
    db.commit()
    linea = _producto(cliente, entrega["id"], nombre=nombre.upper())
    antes = db.query(models.LineaNegocio).count()
    r = _pasa(admin, entrega["id"], linea)
    assert r.status_code == 409
    assert db.query(models.LineaNegocio).count() == antes
    assert _espacio(cliente.get("/api/entregas/%d" % entrega["id"]).json(), linea)["a_medida"]


def test_un_comercial_no_puede_pasarlo(cliente, entrega):
    linea = _producto(cliente, entrega["id"])
    assert _pasa(cliente, entrega["id"], linea).status_code == 403


def test_un_espacio_del_catalogo_no_se_pasa(admin, cliente, entrega, db):
    linea = models.LineaNegocio(id="med-%s" % secrets.token_hex(4), nombre=_nombre())
    db.add(linea)
    db.commit()
    assert _pasa(admin, entrega["id"], linea.id).status_code == 400
