"""
Los textos de los perfiles en el servidor (especificación 005, contracts/api.md).

Lo que se fija aquí:

- **Solo cambios.** El servidor guarda los textos que el equipo cambió; lo demás es el de serie, que
  sale de `textos-perfil-serie.json` (y este, del motor). Guardar el de serie es volver a él.
- **Permisos (FR-504).** Cualquiera del panel los lee; solo un administrador los cambia.
- **Validación (FR-505).** Solo claves que existen; nunca vacío; con su límite de largo. El texto se
  guarda como texto: el motor lo escapa al pintarlo (FR-510).
- **Quién y cuándo (FR-507).**
"""

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import sesion
from app.database import SessionLocal

SERIE = json.loads((Path(__file__).resolve().parents[1] / "app" / "static" / "email"
                    / "textos-perfil-serie.json").read_text(encoding="utf-8"))
DE_SERIE = {t["clave"]: t for t in SERIE["textos"]}


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture(autouse=True)
def sin_cambios(db):
    """La base es la misma para toda la sesión de pruebas: cada prueba empieza y acaba sin cambios."""
    db.query(models.TextoPerfil).delete()
    db.commit()
    yield
    db.query(models.TextoPerfil).delete()
    db.commit()


def _persona(db, email, rol):
    u = db.query(models.PanelUser).filter(models.PanelUser.email == email).first()
    if not u:
        u = models.PanelUser(email=email, nombre=email.split("@")[0], rol=rol, activo=True)
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


def _cliente(usuario=None):
    c = TestClient(app_main.app)
    if usuario is not None:
        c.cookies.set(sesion.COOKIE, sesion.crear(usuario.id, usuario.email))
    return c


@pytest.fixture(scope="module")
def admin(db):
    return _cliente(_persona(db, "admin-txt@ejemplo.test", "admin"))


@pytest.fixture(scope="module")
def comercial(db):
    return _cliente(_persona(db, "comercial-txt@ejemplo.test", "comercial"))


def _pon(cliente, clave, valor, **kw):
    return cliente.put("/api/panel/textos/" + clave, json={"valor": valor}, **kw)


# --- Permisos ------------------------------------------------------------------------------------

def test_sin_sesion_no_se_lee_ni_se_cambia_nada():
    anonimo = _cliente()
    assert anonimo.get("/api/textos-perfil").status_code == 401
    assert anonimo.get("/api/panel/textos").status_code == 401
    assert _pon(anonimo, "agencia.titulo", "x").status_code == 401
    assert anonimo.delete("/api/panel/textos/agencia.titulo").status_code == 401


def test_un_comercial_los_lee_pero_no_los_cambia(comercial):
    assert comercial.get("/api/textos-perfil").json() == {}
    d = comercial.get("/api/panel/textos").json()
    assert [t["clave"] for t in d["textos"]] == list(DE_SERIE)
    assert d["perfiles"] == SERIE["perfiles"]
    assert _pon(comercial, "agencia.titulo", "x").status_code == 403
    assert comercial.delete("/api/panel/textos/agencia.titulo").status_code == 403


# --- Cambiar y volver al de serie ----------------------------------------------------------------

def test_un_administrador_cambia_un_texto_y_llega_a_todos(admin, comercial):
    r = _pon(admin, "agencia.titulo", "  Inventario de diciembre  ")
    assert r.status_code == 200
    t = r.json()
    assert t["valor"] == "Inventario de diciembre" and t["cambiado"] is True
    assert t["serie"] == "Inventario disponible"
    assert t["actualizado_por"] == "admin-txt@ejemplo.test" and t["actualizado_en"]
    # Lo que pide el compositor: solo los cambiados, en la forma que recibe ponTextos().
    assert comercial.get("/api/textos-perfil").json() == {"agencia.titulo": "Inventario de diciembre"}
    fila = [x for x in comercial.get("/api/panel/textos").json()["textos"] if x["clave"] == "agencia.titulo"][0]
    assert fila["cambiado"] is True and fila["actualizado_por"] == "admin-txt@ejemplo.test"


def test_cambiarlo_otra_vez_lo_reemplaza(admin):
    _pon(admin, "nuevo.cta", "Primero")
    _pon(admin, "nuevo.cta", "Segundo")
    assert admin.get("/api/textos-perfil").json() == {"nuevo.cta": "Segundo"}


def test_guardar_el_de_serie_es_volver_a_el(admin):
    _pon(admin, "agencia.titulo", "Otro")
    r = _pon(admin, "agencia.titulo", DE_SERIE["agencia.titulo"]["valor"])
    assert r.status_code == 200 and r.json()["cambiado"] is False
    assert admin.get("/api/textos-perfil").json() == {}


def test_volver_al_de_serie(admin):
    _pon(admin, "phygital.asunto.curiosidad", "⏱\ufe0f Otro asunto")
    r = admin.delete("/api/panel/textos/phygital.asunto.curiosidad")
    assert r.status_code == 200 and r.json()["cambiado"] is False
    assert r.json()["valor"] == DE_SERIE["phygital.asunto.curiosidad"]["valor"]
    assert admin.get("/api/textos-perfil").json() == {}
    # Sin cambio que quitar, no pasa nada.
    assert admin.delete("/api/panel/textos/phygital.asunto.curiosidad").status_code == 200


# --- Validación ----------------------------------------------------------------------------------

@pytest.mark.parametrize("clave", ["no.existe", "agencia", "constructor", "agencia.titulo.x", "agencia.asunto"])
def test_solo_claves_que_existen(admin, clave):
    assert _pon(admin, clave, "x").status_code == 404
    assert admin.delete("/api/panel/textos/" + clave).status_code == 404


@pytest.mark.parametrize("valor", ["", "   ", "\n\t"])
def test_un_texto_vacio_no_se_guarda(admin, valor):
    r = _pon(admin, "agencia.cta", valor)
    assert r.status_code == 400 and "serie" in r.json()["detail"]
    assert admin.get("/api/textos-perfil").json() == {}


def test_cada_texto_tiene_su_limite(admin):
    limite = DE_SERIE["agencia.cta"]["limite"]
    assert _pon(admin, "agencia.cta", "x" * limite).status_code == 200
    r = _pon(admin, "agencia.cta", "x" * (limite + 1))
    assert r.status_code == 422 and str(limite) in r.json()["detail"]


def test_sin_valor_o_con_otro_tipo_no_se_guarda(admin):
    assert admin.put("/api/panel/textos/agencia.cta", json={}).status_code == 422
    assert admin.put("/api/panel/textos/agencia.cta", json={"valor": 42}).status_code == 422


def test_el_texto_se_guarda_tal_cual_lo_escribieron_con_emoji_y_simbolos(admin):
    valor = "🎯 <b>Tarifas</b> & {empresa}"
    assert _pon(admin, "agencia.cta", valor).json()["valor"] == valor
    assert admin.get("/api/textos-perfil").json() == {"agencia.cta": valor}


@pytest.mark.parametrize("valor", ["Hola\u202emundo", "Hola\u200bmundo", "Hola\x07mundo", "Hola\tmundo"])
def test_sin_caracteres_invisibles_ni_de_control(admin, valor):
    """Un \u202e da la vuelta al asunto en la bandeja del cliente: no se acepta."""
    r = _pon(admin, "agencia.titulo", valor)
    assert r.status_code == 400 and "invisibles" in r.json()["detail"]


def test_los_emojis_compuestos_si_valen(admin):
    valor = "\U0001F468\u200d\U0001F4BB Para tu equipo \u2764\ufe0f"
    assert _pon(admin, "agencia.titulo", valor).status_code == 200


def test_solo_la_entrada_y_el_cierre_llevan_saltos_de_linea(admin):
    assert _pon(admin, "agencia.intro", "Primera línea\r\nSegunda línea").json()["valor"] == "Primera línea\nSegunda línea"
    assert _pon(admin, "agencia.cierre", "Uno\nDos").status_code == 200
    for clave in ("agencia.titulo", "agencia.cta", "agencia.preheader", "general.asunto.directo"):
        r = _pon(admin, clave, "Uno\nDos")
        assert r.status_code == 400 and "una sola línea" in r.json()["detail"], clave


def test_cada_cambio_queda_en_el_registro_con_lo_que_habia(admin, caplog):
    import logging
    with caplog.at_level(logging.INFO, logger="centaurads.textos"):
        _pon(admin, "agencia.cta", "Primero")
        _pon(admin, "agencia.cta", "Segundo")
        admin.delete("/api/panel/textos/agencia.cta")
    lineas = [r.getMessage() for r in caplog.records]
    assert any("agencia.cta" in x and "admin-txt@ejemplo.test" in x and "'Primero'" in x for x in lineas)
    assert any("agencia.cta" in x and "de serie" in x and "'Segundo'" in x for x in lineas)


def test_desde_otro_sitio_no_se_cambia_nada(admin):
    r = _pon(admin, "agencia.cta", "x", headers={"Origin": "https://evil.example"})
    assert r.status_code == 403
    assert admin.get("/api/textos-perfil").json() == {}
