"""
Editar, ordenar, retirar y devolver líneas de negocio (especificación 003, US3).

- `PATCH /api/panel/lineas/{id}` cambia solo lo que se manda, con las mismas reglas que el alta; el
  identificador no cambia al renombrar (el estado guardado de cada compositor lo usa).
- Retirar es `activa: false`: la línea deja de salir en `/api/catalogo` y en la pantalla queda
  aparte, nunca se borra; devolverla la trae igual que estaba.
- `POST /api/panel/lineas/orden` recibe el orden completo y nada más.
"""

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


def _cliente(db, email, rol):
    u = db.query(models.PanelUser).filter(models.PanelUser.email == email).first()
    if not u:
        u = models.PanelUser(email=email, nombre=email.split("@")[0], rol=rol, activo=True)
        db.add(u)
        db.commit()
        db.refresh(u)
    c = TestClient(app_main.app)
    c.cookies.set(sesion.COOKIE, sesion.crear(u.id, u.email))
    return c


@pytest.fixture(scope="module")
def admin(db):
    return _cliente(db, "admin-edita@ejemplo.test", "admin")


@pytest.fixture(scope="module")
def comercial(db):
    return _cliente(db, "comercial-edita@ejemplo.test", "comercial")


@pytest.fixture(scope="module")
def linea(admin):
    r = admin.post("/api/panel/lineas", json={
        "nombre": "Línea para editar", "cobertura": "Cobertura original",
        "canva": "https://canva.link/editar", "nota": "Nota original"})
    assert r.status_code == 201, r.text
    return r.json()


def _activas(cliente):
    return [l["id"] for l in cliente.get("/api/catalogo").json()["lineas"]]


# --- Editar --------------------------------------------------------------------------------------

def test_editar_cambia_solo_lo_que_se_manda(admin, linea):
    r = admin.patch("/api/panel/lineas/" + linea["id"], json={"cobertura": "Cobertura nueva"})
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["cobertura"] == "Cobertura nueva"
    assert d["nota"] == "Nota original" and d["canva"] == "https://canva.link/editar"
    assert d["actualizado_por"] == "admin-edita@ejemplo.test"


def test_renombrar_no_cambia_el_identificador(admin, linea):
    r = admin.patch("/api/panel/lineas/" + linea["id"], json={"nombre": "Línea ya renombrada"})
    assert r.status_code == 200
    assert r.json()["id"] == linea["id"] and r.json()["nombre"] == "Línea ya renombrada"


def test_renombrar_con_un_nombre_que_ya_existe_da_409(admin, linea):
    r = admin.patch("/api/panel/lineas/" + linea["id"], json={"nombre": "pantalla led chacao"})
    assert r.status_code == 409


def test_guardar_su_propio_nombre_no_es_un_duplicado(admin, linea):
    actual = admin.get("/api/panel/lineas").json()["lineas"]
    nombre = next(l["nombre"] for l in actual if l["id"] == linea["id"])
    assert admin.patch("/api/panel/lineas/" + linea["id"], json={"nombre": nombre.upper()}).status_code == 200


def test_editar_aplica_las_reglas_del_alta(admin, linea):
    ruta = "/api/panel/lineas/" + linea["id"]
    assert admin.patch(ruta, json={"canva": "canva.link/sin-protocolo"}).status_code == 400
    assert admin.patch(ruta, json={"nombre": "  "}).status_code == 400
    assert admin.patch(ruta, json={"plantillas": "AX"}).status_code == 400
    assert admin.patch(ruta, json={"plantillas": ""}).status_code == 400
    r = admin.patch(ruta, json={"plantillas": "", "confirmarSinPlantillas": True})
    assert r.status_code == 200 and r.json()["plantillas"] == ""
    r = admin.patch(ruta, json={"plantillas": "HB"})
    assert r.status_code == 200 and r.json()["plantillas"] == "BH"
    assert admin.patch(ruta, json={"familia": "no-existe"}).status_code == 400
    r = admin.patch(ruta, json={"familia": ""})
    assert r.status_code == 200 and r.json()["familia"] == ""


def test_una_linea_de_serie_tambien_se_edita(admin):
    antes = next(l for l in admin.get("/api/catalogo").json()["lineas"] if l["id"] == "totem")["nota"]
    r = admin.patch("/api/panel/lineas/totem", json={"nota": "Nota escrita desde el panel"})
    assert r.status_code == 200
    totem = next(l for l in admin.get("/api/catalogo").json()["lineas"] if l["id"] == "totem")
    assert totem["nota"] == "Nota escrita desde el panel"
    # La base es de toda la sesion de pruebas: otras comparan el catalogo de serie.
    assert admin.patch("/api/panel/lineas/totem", json={"nota": antes}).status_code == 200


def test_editar_una_linea_que_no_existe_da_404(admin):
    assert admin.patch("/api/panel/lineas/no-existe", json={"nota": "x"}).status_code == 404


def test_un_comercial_no_edita(comercial, linea):
    assert comercial.patch("/api/panel/lineas/" + linea["id"], json={"nota": "x"}).status_code == 403


# --- Retirar y devolver --------------------------------------------------------------------------

def test_retirar_la_saca_del_catalogo_sin_borrarla(admin, linea):
    r = admin.patch("/api/panel/lineas/" + linea["id"], json={"activa": False})
    assert r.status_code == 200 and r.json()["activa"] is False
    assert linea["id"] not in _activas(admin)
    todas = admin.get("/api/panel/lineas").json()["lineas"]
    assert any(l["id"] == linea["id"] and l["activa"] is False for l in todas)


def test_devolverla_la_trae_igual(admin, linea):
    r = admin.patch("/api/panel/lineas/" + linea["id"], json={"activa": True})
    assert r.status_code == 200
    assert linea["id"] in _activas(admin)
    assert r.json()["cobertura"] == "Cobertura nueva"


def test_no_se_retiran_todas(admin, db):
    """Sin ninguna línea activa el compositor se quedaría con el catálogo de serie sin decirlo."""
    activas = _activas(admin)
    for i in activas[:-1]:
        assert admin.patch("/api/panel/lineas/" + i, json={"activa": False}).status_code == 200
    r = admin.patch("/api/panel/lineas/" + activas[-1], json={"activa": False})
    assert r.status_code == 400 and "al menos una" in r.json()["detail"]
    for i in activas[:-1]:
        admin.patch("/api/panel/lineas/" + i, json={"activa": True})


# --- Orden ---------------------------------------------------------------------------------------

def test_el_orden_nuevo_lo_siguen_el_catalogo_y_el_panel(admin):
    ids = [l["id"] for l in admin.get("/api/panel/lineas").json()["lineas"]]
    nuevo = list(reversed(ids))
    r = admin.post("/api/panel/lineas/orden", json={"ids": nuevo})
    assert r.status_code == 200, r.text
    assert [l["id"] for l in admin.get("/api/panel/lineas").json()["lineas"]] == nuevo
    activas = _activas(admin)
    assert activas == [i for i in nuevo if i in activas]
    assert admin.post("/api/panel/lineas/orden", json={"ids": ids}).status_code == 200


@pytest.mark.parametrize("cambio", ["falta", "sobra", "repetida"])
def test_el_orden_tiene_que_ser_completo(admin, cambio):
    ids = [l["id"] for l in admin.get("/api/panel/lineas").json()["lineas"]]
    malos = {"falta": ids[1:], "sobra": ids + ["no-existe"], "repetida": ids + ids[:1]}[cambio]
    assert admin.post("/api/panel/lineas/orden", json={"ids": malos}).status_code == 400


def test_un_comercial_no_ordena(comercial, admin):
    ids = [l["id"] for l in admin.get("/api/panel/lineas").json()["lineas"]]
    assert comercial.post("/api/panel/lineas/orden", json={"ids": ids}).status_code == 403


# --- Ficha tecnica opcional (US4, T330) ----------------------------------------------------------

FICHA = {"ubic": "Eventos · Caracas", "medida": "3 × 2 m", "trafico": "500 asistentes", "desde": "1.500"}


def _ficha_de(cliente, linea_id):
    return next(l for l in cliente.get("/api/catalogo").json()["lineas"] if l["id"] == linea_id)["ficha"]


def test_una_linea_nace_con_su_ficha(admin):
    r = admin.post("/api/panel/lineas", json={"nombre": "Con ficha técnica", "ficha": FICHA})
    assert r.status_code == 201, r.text
    assert _ficha_de(admin, r.json()["id"]) == FICHA


def test_una_ficha_vacia_es_no_tener_ficha(admin):
    vacia = {"ubic": " ", "medida": "", "trafico": "", "desde": ""}
    r = admin.post("/api/panel/lineas", json={"nombre": "Ficha en blanco", "ficha": vacia})
    assert r.status_code == 201 and _ficha_de(admin, r.json()["id"]) is None


@pytest.mark.parametrize("desde", ["mil", "1.500 USD", "$1500", "-5"])
def test_el_precio_desde_es_solo_el_numero(admin, desde):
    """El correo le añade « $/mes»: un texto o una moneda escritos aqui saldrian dos veces."""
    r = admin.post("/api/panel/lineas", json={"nombre": "Precio raro " + desde, "ficha": {"desde": desde}})
    assert r.status_code == 400


def test_un_dato_de_ficha_demasiado_largo_se_rechaza(admin):
    r = admin.post("/api/panel/lineas", json={"nombre": "Ficha larga", "ficha": {"ubic": "x" * 121}})
    assert r.status_code == 400


def test_editar_la_ficha_cambia_solo_lo_enviado_y_se_puede_quitar(admin):
    linea = admin.post("/api/panel/lineas", json={"nombre": "Ficha que se edita", "ficha": FICHA}).json()
    ruta = "/api/panel/lineas/" + linea["id"]
    assert admin.patch(ruta, json={"ficha": {"trafico": "800 asistentes"}}).status_code == 200
    assert _ficha_de(admin, linea["id"]) == dict(FICHA, trafico="800 asistentes")
    vacia = {"ubic": "", "medida": "", "trafico": "", "desde": ""}
    assert admin.patch(ruta, json={"ficha": vacia}).status_code == 200
    assert _ficha_de(admin, linea["id"]) is None

