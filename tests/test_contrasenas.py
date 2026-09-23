"""
Poner contraseñas del panel.

Este fichero existe por un agujero que se vio al desplegar, no al programar: había una ruta para
**entrar** con contraseña y ninguna para **ponerla**. Con Google todavía sin configurar, eso
dejaba el panel entero inalcanzable y FR-001b sin forma de cumplirse.

Lo que más importa aquí no es que las contraseñas se guarden: es **quién puede ponerlas**.

- La credencial de superadmin es una llave de emergencia, no una puerta trasera: sirve para darle
  contraseña a alguien que **ya está en la lista**, y no puede dar de alta a nadie.
- Cambiar la propia exige la actual. Una sesión robada no debe poder dejar fuera a su dueño.
- La contraseña nunca se guarda en claro, y eso se comprueba mirando la fila.
"""

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import local, sesion
from app.database import SessionLocal

SUPER = {"user": "super@ejemplo.test", "password": "contrasena-de-prueba"}
BUENA = "una-contrasena-larga-de-verdad"


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def cliente():
    return TestClient(app_main.app)


def _alta(db, email, rol="comercial", activo=True):
    u = db.query(models.PanelUser).filter(models.PanelUser.email == email).first()
    if u:
        u.activo, u.rol = activo, rol
    else:
        u = models.PanelUser(email=email, nombre=email.split("@")[0], rol=rol, activo=activo)
        db.add(u)
    db.commit()
    db.refresh(u)
    return u


# --- El arranque en frío --------------------------------------------------------------

def test_con_la_credencial_de_superadmin_se_pone_la_primera_contrasena(cliente, db):
    """Sin esto no entra nadie nunca: es el caso que dejó el panel inalcanzable al desplegar."""
    _alta(db, "primera@ejemplo.test")
    r = cliente.post("/api/panel/arranque/contrasena",
                     json=dict(SUPER, email="primera@ejemplo.test", nueva=BUENA))
    assert r.status_code == 200, r.text

    entra = cliente.post("/api/auth/local",
                         json={"email": "primera@ejemplo.test", "password": BUENA})
    assert entra.status_code == 200
    assert sesion.COOKIE in entra.cookies


def test_la_contrasena_no_se_guarda_en_claro(cliente, db):
    usuario = _alta(db, "enclaro@ejemplo.test")
    cliente.post("/api/panel/arranque/contrasena",
                 json=dict(SUPER, email="enclaro@ejemplo.test", nueva=BUENA))
    db.refresh(usuario)
    assert usuario.password_hash
    assert BUENA not in usuario.password_hash
    assert local.verificar(usuario.password_hash, BUENA)


def test_la_credencial_de_superadmin_no_puede_dar_de_alta_a_nadie(cliente, db):
    """
    Es una llave de emergencia, no una puerta trasera. Si esta ruta pudiera crear cuentas, quien
    tuviera esa credencial se haría a sí mismo un acceso al panel sin que nadie lo autorizara.
    """
    r = cliente.post("/api/panel/arranque/contrasena",
                     json=dict(SUPER, email="jamas.autorizado@ejemplo.test", nueva=BUENA))
    assert r.status_code == 404
    assert db.query(models.PanelUser).filter(
        models.PanelUser.email == "jamas.autorizado@ejemplo.test").first() is None


def test_a_quien_esta_de_baja_tampoco(cliente, db):
    """Dar de baja tiene que ser efectivo también por esta vía, o no sirve de nada."""
    _alta(db, "debaja@ejemplo.test", activo=False)
    r = cliente.post("/api/panel/arranque/contrasena",
                     json=dict(SUPER, email="debaja@ejemplo.test", nueva=BUENA))
    assert r.status_code == 404


def test_con_la_credencial_equivocada_no(cliente, db):
    _alta(db, "protegida@ejemplo.test")
    r = cliente.post("/api/panel/arranque/contrasena",
                     json={"user": SUPER["user"], "password": "me-la-invento",
                           "email": "protegida@ejemplo.test", "nueva": BUENA})
    assert r.status_code == 401


def test_sin_superadmin_configurado_responde_503_y_no_401(cliente, db, monkeypatch):
    """
    No es lo mismo «tu credencial es incorrecta» que «este servidor no tiene ninguna». Decir 401
    mandaría a quien lo intenta a buscar una contraseña que no existe.
    """
    _alta(db, "otra@ejemplo.test")
    monkeypatch.setenv("SUPERADMIN_USER", "")
    monkeypatch.setenv("SUPERADMIN_PASS", "")
    r = cliente.post("/api/panel/arranque/contrasena",
                     json=dict(SUPER, email="otra@ejemplo.test", nueva=BUENA))
    assert r.status_code == 503


def test_una_contrasena_corta_se_rechaza(cliente, db):
    _alta(db, "corta@ejemplo.test")
    r = cliente.post("/api/panel/arranque/contrasena",
                     json=dict(SUPER, email="corta@ejemplo.test", nueva="1234"))
    assert r.status_code == 400
    assert "caracteres" in r.json()["detail"]


def test_la_credencial_se_compara_en_tiempo_constante():
    """
    Una prueba sobre el **código**, no sobre el comportamiento, y conviene decir por qué.

    `secrets.compare_digest` y `==` hacen exactamente lo mismo desde fuera: ninguna prueba
    funcional puede distinguirlos, porque la diferencia no está en el resultado sino en el
    tiempo. `==` se corta en el primer byte distinto, y eso deja medir cuántos aciertas y sacar
    la credencial byte a byte.

    Se comprobó cambiando uno por otro: las 29 pruebas siguieron en verde. Así que esta mira el
    código. Es más floja que una prueba de comportamiento —mide la forma, no el efecto— pero es
    lo único que protege la propiedad, y sin ella el cambio pasa inadvertido en cualquier
    revisión apresurada.
    """
    from pathlib import Path

    fuente = (Path(__file__).resolve().parent.parent
              / "app" / "auth" / "superadmin.py").read_text(encoding="utf-8")

    # Se mira la comparacion en si, no el fichero entero: la primera version de esta prueba
    # buscaba "compare_digest" en todo el texto y lo encontraba en un COMENTARIO, asi que daba
    # por buena una version que ya comparaba con ==. Lo cazo volver a mutar el codigo.
    cuerpo = fuente.split("def verifica")[1]
    comparacion = [l for l in cuerpo.splitlines()
                   if "_valor(" in l and ("bien" in l or "compare_digest" in l or "==" in l)]
    assert comparacion, "no encuentro la comparación de la credencial en verifica()"
    junto = " ".join(comparacion)
    assert "compare_digest" in junto, (
        "la credencial se compara sin compare_digest: " + junto.strip())
    assert "==" not in junto.replace("!=", ""), (
        "la credencial se compara con ==: " + junto.strip())


# --- Un administrador se la pone a alguien --------------------------------------------

@pytest.fixture()
def admin(db, cliente):
    u = _alta(db, "jefa.claves@ejemplo.test", rol="admin")
    cliente.cookies.set(sesion.COOKIE, sesion.crear(u.id, u.email))
    return u


def test_un_administrador_pone_la_contrasena_de_otro(cliente, db, admin):
    otra = _alta(db, "nueva.persona@ejemplo.test")
    r = cliente.post("/api/panel/usuarios/%d/contrasena" % otra.id, json={"password": BUENA})
    assert r.status_code == 200, r.text
    db.refresh(otra)
    assert local.verificar(otra.password_hash, BUENA)


def test_alguien_del_equipo_no_puede_cambiar_la_de_otro(cliente, db):
    """Si esto se cayera, cualquiera podría entrar con el nombre de quien quisiera."""
    victima = _alta(db, "victima@ejemplo.test")
    comercial = _alta(db, "curioso@ejemplo.test", rol="comercial")
    cliente.cookies.set(sesion.COOKIE, sesion.crear(comercial.id, comercial.email))
    r = cliente.post("/api/panel/usuarios/%d/contrasena" % victima.id,
                     json={"password": BUENA})
    assert r.status_code == 403


def test_sin_sesion_tampoco(cliente, db):
    alguien = _alta(db, "alguien@ejemplo.test")
    anonimo = TestClient(app_main.app)
    r = anonimo.post("/api/panel/usuarios/%d/contrasena" % alguien.id, json={"password": BUENA})
    assert r.status_code == 401


# --- Cada quien la suya ----------------------------------------------------------------

def test_cada_quien_cambia_la_suya_dando_la_actual(cliente, db):
    """Una contraseña que puso otra persona la conoce otra persona."""
    u = _alta(db, "cambia@ejemplo.test")
    cliente.post("/api/panel/arranque/contrasena",
                 json=dict(SUPER, email="cambia@ejemplo.test", nueva=BUENA))
    db.refresh(u)
    cliente.cookies.set(sesion.COOKIE, sesion.crear(u.id, u.email))

    r = cliente.post("/api/auth/contrasena",
                     json={"actual": BUENA, "nueva": "otra-contrasena-bien-larga"})
    assert r.status_code == 200, r.text
    db.refresh(u)
    assert local.verificar(u.password_hash, "otra-contrasena-bien-larga")
    assert not local.verificar(u.password_hash, BUENA)


def test_sin_la_actual_no_se_cambia(cliente, db):
    """
    Una sesión robada no debe poder dejar fuera a su dueño. La cookie es válida y aun así hace
    falta saber la contraseña de ahora.
    """
    u = _alta(db, "robada@ejemplo.test")
    cliente.post("/api/panel/arranque/contrasena",
                 json=dict(SUPER, email="robada@ejemplo.test", nueva=BUENA))
    db.refresh(u)
    cliente.cookies.set(sesion.COOKIE, sesion.crear(u.id, u.email))

    r = cliente.post("/api/auth/contrasena",
                     json={"actual": "me-la-invento", "nueva": "otra-contrasena-bien-larga"})
    assert r.status_code == 403
    db.refresh(u)
    assert local.verificar(u.password_hash, BUENA), "la contraseña no debería haber cambiado"
