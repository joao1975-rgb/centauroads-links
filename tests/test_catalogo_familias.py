"""
Familias de la plantilla D (especificación 003, US5).

La D presenta las líneas agrupadas. Un administrador puede crear un grupo nuevo y renombrar uno que
ya existe (el título es lo que lee el cliente); una línea se asigna a su grupo al darla de alta o al
editarla. `otros` está reservado: es el grupo que el motor arma solo con las líneas sin familia.
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
    return _cliente(db, "admin-familias@ejemplo.test", "admin")


@pytest.fixture(scope="module")
def comercial(db):
    return _cliente(db, "comercial-familias@ejemplo.test", "comercial")


def _familias(cliente):
    return cliente.get("/api/catalogo").json()["familias"]


def test_un_administrador_crea_un_grupo(admin):
    r = admin.post("/api/panel/familias", json={"titulo": "Renta de equipos", "eyebrow": "Alquiler"})
    assert r.status_code == 201, r.text
    assert r.json() == {"id": "renta-de-equipos", "titulo": "Renta de equipos", "eyebrow": "Alquiler"}
    assert _familias(admin)[-1]["id"] == "renta-de-equipos", "va detras de los que ya estaban"


def test_una_linea_se_asigna_al_grupo_nuevo(admin):
    r = admin.post("/api/panel/lineas", json={"nombre": "Línea del grupo nuevo", "familia": "renta-de-equipos"})
    assert r.status_code == 201 and r.json()["familia"] == "renta-de-equipos"


def test_el_titulo_no_se_repite(admin):
    r = admin.post("/api/panel/familias", json={"titulo": "RENTA DE EQUIPOS"})
    assert r.status_code == 409


@pytest.mark.parametrize("titulo", ["", "   ", "x" * 121])
def test_el_titulo_es_obligatorio_y_con_limite(admin, titulo):
    assert admin.post("/api/panel/familias", json={"titulo": titulo}).status_code == 400


def test_otros_esta_reservado(admin):
    """`otros` es el grupo que arma el motor con las líneas sin familia."""
    r = admin.post("/api/panel/familias", json={"titulo": "Otros"})
    assert r.status_code == 201 and r.json()["id"] == "familia-otros"


def test_renombrar_un_grupo_cambia_lo_que_lee_el_cliente(admin):
    r = admin.patch("/api/panel/familias/renta-de-equipos", json={"titulo": "Renta y eventos"})
    assert r.status_code == 200
    assert r.json()["id"] == "renta-de-equipos" and r.json()["titulo"] == "Renta y eventos"
    assert any(f["titulo"] == "Renta y eventos" for f in _familias(admin))


def test_renombrar_con_un_titulo_ajeno_da_409_y_el_propio_no(admin):
    assert admin.patch("/api/panel/familias/renta-de-equipos", json={"titulo": "Vallas (OOH)"}).status_code == 409
    assert admin.patch("/api/panel/familias/renta-de-equipos", json={"titulo": "RENTA Y EVENTOS"}).status_code == 200


def test_renombrar_un_grupo_que_no_existe_da_404(admin):
    assert admin.patch("/api/panel/familias/no-existe", json={"titulo": "X"}).status_code == 404


def test_un_comercial_no_crea_ni_renombra(comercial):
    assert comercial.post("/api/panel/familias", json={"titulo": "Otro grupo"}).status_code == 403
    assert comercial.patch("/api/panel/familias/dooh", json={"titulo": "X"}).status_code == 403


def test_sin_sesion_no_hay_nada(db):
    anonimo = TestClient(app_main.app)
    assert anonimo.post("/api/panel/familias", json={"titulo": "Otro grupo"}).status_code == 401
