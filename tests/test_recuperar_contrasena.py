"""
Recuperar el acceso, y no dejar que se adivine (2026-10-03, petición del usuario).

Lo que pasó: mercadeo@ pulsó «Poner contraseña» en su propia fila y se cambió la contraseña sin
querer; Chrome seguía rellenando la vieja y nadie podía entrar. Se recuperó con la llave de
superadmin desde PowerShell. Ahora:

- En la pantalla del equipo, la fila propia ya no ofrece «Poner contraseña»: la tuya se cambia en
  «Tu contraseña», que pide la actual.
- La pantalla de entrada tiene «¿Olvidaste tu contraseña?», que abre una ventana: lo normal es
  pedírsela a un administrador; y la recuperación de emergencia, con la credencial de superadmin,
  es la misma ruta que se usó desde PowerShell. La app no envía correos: no hay enlace por email.
- Como esa ventana deja la llave a la vista, se limita: 5 fallos de superadmin (o 10 de contraseña
  normal) desde la misma dirección bloquean 15 minutos. Un acierto no borra el bloqueo ya activo.
"""

import os

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import intentos, local
from app.database import SessionLocal

ARRANQUE = "/api/panel/arranque/contrasena"
SUPER = {"user": os.environ["SUPERADMIN_USER"], "password": os.environ["SUPERADMIN_PASS"]}


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def cliente():
    return TestClient(app_main.app)


def _cuenta(db, email, clave=None):
    u = db.query(models.PanelUser).filter(models.PanelUser.email == email).first()
    if not u:
        u = models.PanelUser(email=email, nombre=email.split("@")[0], rol="comercial", activo=True)
        db.add(u)
    u.activo = True
    u.password_hash = local.hashear(clave) if clave else None
    db.commit()
    db.refresh(u)
    return u


# --- La ventana en la pantalla de entrada -------------------------------------------------------

def _ventana(html, ident):
    i = html.index('<dialog id="%s"' % ident)
    return html[i:html.index("</dialog>", i)]


def test_quien_olvida_su_contrasena_solo_ve_que_la_pida_a_un_administrador(cliente):
    """
    2026-10-07, petición de la propietaria: una persona del equipo que olvidó su contraseña no debe
    encontrarse un formulario de superadmin. «¿Olvidaste tu contraseña?» solo explica a quién pedirla.
    """
    html = cliente.get("/panel/entrar").text
    assert "¿Olvidaste tu contraseña?" in html
    olvido = _ventana(html, "olvido")
    assert "administrador" in olvido and "Equipo" in olvido
    assert "superadmin" not in olvido.lower() and "<input" not in olvido


def test_la_recuperacion_de_emergencia_va_aparte_y_para_el_responsable(cliente):
    html = cliente.get("/panel/entrar").text
    emergencia = _ventana(html, "emergencia")
    assert "superadmin" in emergencia.lower()
    assert 'id="abre-emergencia"' in html and "responsable del panel" in html
    assert ARRANQUE in html


def test_la_ventana_pide_lo_que_pide_la_ruta(cliente):
    html = cliente.get("/panel/entrar").text
    for campo in ('id="r-user"', 'id="r-pass"', 'id="r-email"', 'id="r-nueva"', 'id="r-otra"'):
        assert campo in html, campo


# --- La recuperación de emergencia funciona de punta a punta ------------------------------------

def test_recuperar_y_entrar_con_la_nueva(cliente, db):
    _cuenta(db, "perdida@ejemplo.test", "la-que-se-olvido-123")
    r = cliente.post(ARRANQUE, json={**SUPER, "email": "perdida@ejemplo.test",
                                      "nueva": "la-nueva-de-verdad-456"})
    assert r.status_code == 200, r.text
    assert cliente.post("/api/auth/local", json={"email": "perdida@ejemplo.test",
                                                 "password": "la-nueva-de-verdad-456"}).status_code == 200
    assert cliente.post("/api/auth/local", json={"email": "perdida@ejemplo.test",
                                                 "password": "la-que-se-olvido-123"}).status_code == 403  # gitleaks:allow (valor sintético de prueba)


# --- El límite de intentos ---------------------------------------------------------------------

def test_cinco_fallos_de_superadmin_bloquean_aunque_luego_acierte(cliente, db):
    _cuenta(db, "objetivo@ejemplo.test", "una-clave-cualquiera-1")
    malo = {"user": SUPER["user"], "password": "no-es-esta", "email": "objetivo@ejemplo.test",
            "nueva": "intento-de-intruso-99"}
    for _ in range(intentos.MAX_SUPERADMIN):
        assert cliente.post(ARRANQUE, json=malo).status_code == 401
    r = cliente.post(ARRANQUE, json={**SUPER, "email": "objetivo@ejemplo.test",
                                      "nueva": "ahora-si-la-buena-77"})
    assert r.status_code == 429
    assert "minutos" in r.json()["detail"]


def test_los_fallos_de_una_direccion_no_bloquean_a_otra(cliente, db):
    _cuenta(db, "otra.dir@ejemplo.test", "una-clave-cualquiera-2")
    malo = {"user": "x", "password": "y", "email": "otra.dir@ejemplo.test", "nueva": "z" * 12}
    for _ in range(intentos.MAX_SUPERADMIN):
        cliente.post(ARRANQUE, json=malo, headers={"x-forwarded-for": "203.0.113.7"})
    r = cliente.post(ARRANQUE, json={**SUPER, "email": "otra.dir@ejemplo.test",
                                      "nueva": "desde-otro-sitio-1"},
                     headers={"x-forwarded-for": "198.51.100.9"})
    assert r.status_code == 200


def test_la_direccion_es_la_que_pone_el_proxy_no_la_que_inventa_el_cliente(cliente, db):
    """El proxy (Traefik) AÑADE la dirección real al final de X-Forwarded-For. Lo de delante lo
    escribe quien llama: si contara eso, bastaría con cambiarlo en cada intento para no bloquearse."""
    malo = {"user": "x", "password": "y", "email": "nadie@ejemplo.test", "nueva": "z" * 12}
    for n in range(intentos.MAX_SUPERADMIN):
        cliente.post(ARRANQUE, json=malo, headers={"x-forwarded-for": f"10.0.0.{n}, 203.0.113.50"})
    r = cliente.post(ARRANQUE, json=malo, headers={"x-forwarded-for": "10.9.9.9, 203.0.113.50"})
    assert r.status_code == 429


def test_diez_fallos_de_contrasena_normal_bloquean(cliente, db):
    _cuenta(db, "tecleo@ejemplo.test", "la-buena-de-tecleo-1")
    for _ in range(intentos.MAX_ENTRADA):
        assert cliente.post("/api/auth/local", json={"email": "tecleo@ejemplo.test",
                                                     "password": "mal"}).status_code == 403
    r = cliente.post("/api/auth/local", json={"email": "tecleo@ejemplo.test",
                                              "password": "la-buena-de-tecleo-1"})
    assert r.status_code == 429


def test_un_acierto_antes_del_limite_borra_los_fallos(cliente, db):
    _cuenta(db, "despistado@ejemplo.test", "la-buena-de-despiste-1")
    for _ in range(intentos.MAX_ENTRADA - 1):
        cliente.post("/api/auth/local", json={"email": "despistado@ejemplo.test", "password": "mal"})
    assert cliente.post("/api/auth/local", json={"email": "despistado@ejemplo.test",
                                                 "password": "la-buena-de-despiste-1"}).status_code == 200
    for _ in range(intentos.MAX_ENTRADA - 1):
        assert cliente.post("/api/auth/local", json={"email": "despistado@ejemplo.test",
                                                     "password": "mal"}).status_code == 403


def test_el_bloqueo_caduca(cliente, db, monkeypatch):
    _cuenta(db, "paciente@ejemplo.test", "la-buena-de-paciente-1")
    reloj = [1000.0]
    monkeypatch.setattr(intentos, "_ahora", lambda: reloj[0])
    for _ in range(intentos.MAX_ENTRADA):
        cliente.post("/api/auth/local", json={"email": "paciente@ejemplo.test", "password": "mal"})
    buena = {"email": "paciente@ejemplo.test", "password": "la-buena-de-paciente-1"}
    assert cliente.post("/api/auth/local", json=buena).status_code == 429
    reloj[0] += intentos.VENTANA_SEGUNDOS + 1
    assert cliente.post("/api/auth/local", json=buena).status_code == 200


# --- La fila propia ya no se cambia la contraseña sin pedir la actual ---------------------------

def test_la_fila_propia_no_ofrece_poner_contrasena():
    """La comprobación vive en el navegador (la lista la pinta el JS); se fija aquí su forma."""
    from app.auth.equipo import _PAGINA
    i = _PAGINA.index("boton('Poner contraseña'")
    assert "!esYo(u)" in _PAGINA[i - 200:i], "el botón tiene que ir dentro de la condición !esYo(u)"
