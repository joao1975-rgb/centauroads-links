"""
El superadministrador entra al panel y llega al Centro de control (especificación 006).

Decisiones de la propietaria (2026-10-07):
- La credencial de superadmin (SUPERADMIN_USER / SUPERADMIN_PASS, en EasyPanel) abre sesión desde la
  pantalla de entrada normal. El superadmin es una fila más de la lista, rol admin, **sin contraseña
  guardada**: la suya se comprueba siempre contra el entorno.
- Tras entrar, superadmin y administradores llegan al Centro de control (/panel/inicio); los
  comerciales, al compositor.
- Su cuenta no se puede dar de baja, cambiar de rol o de correo, ni recibir contraseña desde el panel.
"""

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import intentos, local, rutas, sesion
from app.database import SessionLocal

RAIZ = Path(__file__).resolve().parents[1]
SUPER_U = os.environ["SUPERADMIN_USER"]
SUPER_P = os.environ["SUPERADMIN_PASS"]


@pytest.fixture(autouse=True)
def sin_bloqueos():
    """Los intentos fallidos de estas pruebas no deben bloquear a las siguientes."""
    intentos._fallos.clear()
    yield
    intentos._fallos.clear()


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


def _fila(db, email):
    db.expire_all()
    return db.query(models.PanelUser).filter(models.PanelUser.email == email.lower()).first()


def _persona(db, email, rol):
    u = _fila(db, email)
    if not u:
        u = models.PanelUser(email=email, nombre=email.split("@")[0], rol=rol, activo=True)
        db.add(u)
    u.rol, u.activo = rol, True
    db.commit()
    db.refresh(u)
    return u


def _cliente(usuario=None):
    c = TestClient(app_main.app)
    if usuario is not None:
        c.cookies.set(sesion.COOKIE, sesion.crear(usuario.id, usuario.email))
    return c


def _entra(c, email, password):
    return c.post("/api/auth/local", json={"email": email, "password": password})


# --- US1: entrar con la credencial de superadmin -------------------------------------------------

def test_la_credencial_de_superadmin_abre_sesion_sin_contrasena_guardada(db):
    c = TestClient(app_main.app)
    r = _entra(c, "  " + SUPER_U.upper() + " ", SUPER_P)
    assert r.status_code == 200, r.text
    assert r.json()["rol"] == "admin" and r.json()["superadmin"] is True
    assert sesion.COOKIE in r.headers["set-cookie"]
    u = _fila(db, SUPER_U)
    assert u.activo and u.rol == "admin" and u.password_hash is None
    assert c.get("/api/auth/yo").json()["superadmin"] is True


def test_si_estaba_de_baja_o_como_comercial_vuelve_activa_y_administradora(db):
    u = _persona(db, SUPER_U, "comercial")
    u.activo = False
    db.commit()
    assert _entra(TestClient(app_main.app), SUPER_U, SUPER_P).status_code == 200
    u = _fila(db, SUPER_U)
    assert u.activo and u.rol == "admin"


def test_con_otra_contrasena_no_entra_y_cuenta_como_fallo():
    r = _entra(TestClient(app_main.app), SUPER_U, "no-es-la-de-easypanel")
    assert r.status_code == 403 and r.json()["detail"] == rutas._RECHAZO
    assert any(k[0] == "entrada" for k in intentos._fallos)


def test_la_contrasena_guardada_no_vale_para_el_superadmin(db):
    """Manda EasyPanel: una contraseña puesta en la base (p. ej. de antes) no abre su cuenta."""
    u = _persona(db, SUPER_U, "admin")
    u.password_hash = local.hashear("otra-clave-larga-de-prueba-123")
    db.commit()
    try:
        assert _entra(TestClient(app_main.app), SUPER_U, "otra-clave-larga-de-prueba-123").status_code == 403
    finally:
        u.password_hash = None
        db.commit()


def test_sin_la_credencial_configurada_nadie_entra_como_superadmin(monkeypatch):
    monkeypatch.delenv("SUPERADMIN_PASS")
    assert _entra(TestClient(app_main.app), SUPER_U, SUPER_P).status_code == 403


def test_el_usuario_de_superadmin_puede_no_ser_un_correo(monkeypatch, db):
    monkeypatch.setenv("SUPERADMIN_USER", "responsable")
    try:
        r = _entra(TestClient(app_main.app), "Responsable", SUPER_P)
        assert r.status_code == 200 and r.json()["superadmin"] is True
    finally:
        u = _fila(db, "responsable")
        if u:
            db.delete(u)
            db.commit()


def test_la_entrada_acepta_un_usuario_y_ya_no_tiene_ventana_de_emergencia():
    html = TestClient(app_main.app).get("/panel/entrar").text
    assert '<input id="email" name="email" type="text"' in html
    assert 'id="emergencia"' not in html and 'id="abre-emergencia"' not in html
    assert "¿Olvidaste tu contraseña?" in html


# --- US2: el Centro de control -------------------------------------------------------------------

def test_el_centro_de_control_solo_para_administradores(db):
    r = TestClient(app_main.app).get("/panel/inicio", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == "/panel/entrar?destino=%2Fpanel%2Finicio"
    comercial = _cliente(_persona(db, "comercial-inicio@ejemplo.test", "comercial"))
    r = comercial.get("/panel/inicio", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == rutas.COMPOSITOR
    admin = _cliente(_persona(db, "admin-inicio@ejemplo.test", "admin"))
    r = admin.get("/panel/inicio")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    for destino in (rutas.COMPOSITOR, "/panel/lineas", "/panel/textos", "/panel/equipo"):
        assert 'href="%s"' % destino in r.text, destino
    for titulo in ("Compositor", "Administración", "Accesos"):
        assert titulo in r.text


def test_tras_entrar_sin_destino_el_administrador_va_al_centro_de_control():
    sin = TestClient(app_main.app).get("/panel/entrar").text
    assert "var porDefecto = true;" in sin
    assert "porDefecto && d.rol === 'admin' ? '/panel/inicio' : destino" in sin
    con = TestClient(app_main.app).get("/panel/entrar", params={"destino": "/panel/textos"}).text
    assert "var porDefecto = false;" in con and 'var destino = "/panel/textos";' in con


@pytest.mark.parametrize("archivo", ["prototipos/mail/compositor.html", "app/static/email/compositor.html",
                                     "app/mails/catalogo/pantalla.py", "app/mails/textos/pantalla.py",
                                     "app/auth/equipo.py"])
def test_las_pantallas_ofrecen_volver_al_inicio(archivo):
    assert '<a href="/panel/inicio">Inicio</a>' in (RAIZ / archivo).read_text(encoding="utf-8")


# --- US3: la cuenta de superadmin protegida ------------------------------------------------------

def test_la_cuenta_de_superadmin_no_se_toca_desde_el_panel(db):
    sup = _persona(db, SUPER_U, "admin")
    admin = _cliente(_persona(db, "admin-protege@ejemplo.test", "admin"))
    base = "/api/panel/usuarios/%d" % sup.id
    for r in (admin.delete(base),
              admin.patch(base, json={"rol": "comercial"}),
              admin.patch(base, json={"email": "otro@ejemplo.test"}),
              admin.post(base + "/contrasena", json={"password": "una-clave-larga-de-prueba"})):
        assert r.status_code == 403 and "EasyPanel" in r.json()["detail"], r.text
    # El nombre sí se puede corregir.
    assert admin.patch(base, json={"nombre": "Responsable del panel"}).status_code == 200
    fila = _fila(db, SUPER_U)
    assert fila.activo and fila.rol == "admin" and fila.email == SUPER_U.lower() and fila.password_hash is None
    lista = admin.get("/api/panel/usuarios").json()
    assert [u["superadmin"] for u in lista if u["email"] == SUPER_U.lower()] == [True]
    assert all(u["superadmin"] is False for u in lista if u["email"] != SUPER_U.lower())


def test_el_superadmin_cambia_su_contrasena_en_easypanel(db):
    sup = _cliente(_persona(db, SUPER_U, "admin"))
    r = sup.post("/api/auth/contrasena", json={"actual": SUPER_P, "nueva": "otra-clave-larga-de-prueba"})
    assert r.status_code == 400 and "EasyPanel" in r.json()["detail"]


# --- Revisión de seguridad (2026-10-07) ----------------------------------------------------------

def test_nadie_se_apropia_del_correo_del_superadmin_renombrando_su_cuenta(db):
    """
    M1: antes de que el superadmin entre por primera vez no hay fila con su correo, y un
    administrador podía renombrar la suya (o la de otro) a ese correo: quedaba como una cuenta
    imposible de dar de baja desde el panel.
    """
    fila = _fila(db, SUPER_U)
    if fila:
        db.delete(fila)
        db.commit()
    admin = _cliente(_persona(db, "admin-renombra@ejemplo.test", "admin"))
    otro = _persona(db, "otro-renombra@ejemplo.test", "comercial")
    r = admin.patch("/api/panel/usuarios/%d" % otro.id, json={"email": SUPER_U.upper()})
    assert r.status_code == 403 and "EasyPanel" in r.json()["detail"]
    assert _fila(db, "otro-renombra@ejemplo.test") is not None


def test_la_contrasena_de_superadmin_tiene_su_propio_limite_de_intentos():
    """L1: la credencial de superadmin conserva el límite más estricto que ya tenía (5, no 10)."""
    c = TestClient(app_main.app)
    for _ in range(intentos.MAX_SUPERADMIN):
        assert _entra(c, SUPER_U, "no-es-la-de-easypanel").status_code == 403
    assert _entra(c, SUPER_U, SUPER_P).status_code == 429
