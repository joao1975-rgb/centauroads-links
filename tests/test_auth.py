"""
Pruebas de la identidad del panel (T017).

Lo que se comprueba aquí es lo que sustituye a la clave única compartida: que cada persona es
alguien distinto, que la baja tiene efecto, y que **nadie firma un correo con el nombre de otra**.

Esa última es la que más importa. La decisión del cliente fue "cada quien su cuenta, mercadeo@
compartida", y si esa regla se cae, un correo puede salir firmado por Elizabeth sin que Elizabeth
lo haya escrito.
"""

import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import models
from app.auth import local, sesion
from app.auth import dependencias as dep
from app.database import get_db
from app.migracion import migrar


@pytest.fixture()
def db(tmp_path):
    """Base de datos limpia, ya migrada."""
    motor = create_engine(f"sqlite:///{(tmp_path / 'auth.db').as_posix()}",
                          connect_args={"check_same_thread": False})
    migrar(motor)
    Sesion = sessionmaker(bind=motor, autocommit=False, autoflush=False)
    s = Sesion()
    yield s
    s.close()


@pytest.fixture()
def gente(db):
    """Elizabeth con su cuenta personal, Ana en mercadeo, y los permisos correctos."""
    elizabeth = models.PanelUser(email="equintero@centauroads.com", nombre="Elizabeth",
                                 rol="admin", activo=True)
    ana = models.PanelUser(email="ana@centauroads.com", nombre="Ana",
                           rol="comercial", activo=True)
    db.add_all([elizabeth, ana])
    db.flush()

    personal = models.SenderAccount(email="equintero@centauroads.com", tipo="personal",
                                    etiqueta="Elizabeth", activa=True)
    compartida = models.SenderAccount(email="mercadeo@centauroads.com", tipo="compartida",
                                      etiqueta="Mercadeo", activa=True)
    db.add_all([personal, compartida])
    db.flush()

    db.add_all([
        models.SenderPermission(panel_user_id=elizabeth.id, sender_account_id=personal.id),
        models.SenderPermission(panel_user_id=elizabeth.id, sender_account_id=compartida.id),
        models.SenderPermission(panel_user_id=ana.id, sender_account_id=compartida.id),
    ])
    db.commit()
    return {"elizabeth": elizabeth, "ana": ana,
            "personal": personal, "compartida": compartida}


# --- Contraseñas de los usuarios de excepción ---------------------------------------

def test_la_contrasena_no_se_guarda_en_claro():
    clave = "una-contrasena-larga"
    h = local.hashear(clave)
    assert clave not in h
    assert h.startswith("$argon2")


def test_la_contrasena_correcta_verifica():
    h = local.hashear("una-contrasena-larga")
    assert local.verificar(h, "una-contrasena-larga")


def test_la_contrasena_incorrecta_no_verifica():
    h = local.hashear("una-contrasena-larga")
    assert not local.verificar(h, "otra-contrasena-larga")


def test_dos_hashes_de_la_misma_contrasena_son_distintos():
    """Con sal: dos personas con la misma contraseña no comparten hash."""
    assert local.hashear("una-contrasena-larga") != local.hashear("una-contrasena-larga")


def test_una_contrasena_corta_se_rechaza_al_darla_de_alta():
    with pytest.raises(local.ContrasenaDebil):
        local.hashear("corta")


def test_un_usuario_sin_contrasena_no_entra():
    """Quien entra por Google tiene password_hash vacío: esa vía no puede servirle de atajo."""
    assert not local.verificar(None, "lo-que-sea")
    assert not local.verificar("", "lo-que-sea")


# --- Sesiones -------------------------------------------------------------------------

def test_la_sesion_va_y_vuelve():
    datos = sesion.leer(sesion.crear(7, "ana@centauroads.com"))
    assert datos["uid"] == 7
    assert datos["email"] == "ana@centauroads.com"


def test_una_cookie_manipulada_se_descarta():
    valor = sesion.crear(7, "ana@centauroads.com")
    assert sesion.leer(valor[:-4] + "xxxx") is None


def test_una_cookie_inventada_se_descarta():
    assert sesion.leer("no-es-una-sesion") is None
    assert sesion.leer(None) is None


# --- La regla que protege la firma de cada quien --------------------------------------

def test_elizabeth_puede_usar_su_cuenta(db, gente):
    cuenta = dep.exigir_cuenta(db, gente["elizabeth"], gente["personal"].id)
    assert cuenta.email == "equintero@centauroads.com"


def test_ana_puede_usar_la_compartida(db, gente):
    cuenta = dep.exigir_cuenta(db, gente["ana"], gente["compartida"].id)
    assert cuenta.email == "mercadeo@centauroads.com"


def test_ana_no_puede_usar_la_cuenta_personal_de_elizabeth(db, gente):
    """La prueba central: sin esto, un correo puede salir firmado por quien no lo escribió."""
    with pytest.raises(HTTPException) as e:
        dep.exigir_cuenta(db, gente["ana"], gente["personal"].id)
    assert e.value.status_code == 403


def test_ni_aunque_alguien_le_conceda_el_permiso_por_error(db, gente):
    """
    Segunda capa. Se le da a Ana permiso explícito sobre la cuenta personal de Elizabeth —un error
    humano perfectamente posible— y aun así debe rechazarse.
    """
    db.add(models.SenderPermission(panel_user_id=gente["ana"].id,
                                   sender_account_id=gente["personal"].id))
    db.commit()

    with pytest.raises(HTTPException) as e:
        dep.exigir_cuenta(db, gente["ana"], gente["personal"].id)
    assert e.value.status_code == 403
    assert "personal" in e.value.detail


def test_conceder_permiso_valida_la_misma_regla(db, gente):
    assert dep.puede_conceder(gente["compartida"], gente["ana"])
    assert dep.puede_conceder(gente["personal"], gente["elizabeth"])
    assert not dep.puede_conceder(gente["personal"], gente["ana"])


def test_cada_quien_ve_solo_sus_cuentas(db, gente):
    de_ana = {c.email for c in dep.cuentas_permitidas(db, gente["ana"])}
    de_eli = {c.email for c in dep.cuentas_permitidas(db, gente["elizabeth"])}
    assert de_ana == {"mercadeo@centauroads.com"}
    assert de_eli == {"mercadeo@centauroads.com", "equintero@centauroads.com"}


def test_una_cuenta_desactivada_no_se_puede_usar(db, gente):
    gente["compartida"].activa = False
    db.commit()
    with pytest.raises(HTTPException) as e:
        dep.exigir_cuenta(db, gente["ana"], gente["compartida"].id)
    assert e.value.status_code == 404


# --- La sesión de alguien dado de baja deja de valer en el acto -----------------------

def _app_de_prueba(db):
    app = FastAPI()

    @app.get("/privado")
    def privado(usuario: models.PanelUser = Depends(dep.usuario_actual)):
        return {"email": usuario.email}

    @app.get("/solo-admin")
    def solo_admin(usuario: models.PanelUser = Depends(dep.solo_admin)):
        return {"email": usuario.email}

    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def test_sin_sesion_no_se_entra(db, gente):
    assert _app_de_prueba(db).get("/privado").status_code == 401


def test_con_sesion_se_entra(db, gente):
    cliente = _app_de_prueba(db)
    cliente.cookies.set(sesion.COOKIE, sesion.crear(gente["ana"].id, gente["ana"].email))
    r = cliente.get("/privado")
    assert r.status_code == 200
    assert r.json()["email"] == "ana@centauroads.com"


def test_dar_de_baja_corta_el_acceso_aunque_la_sesion_siga_viva(db, gente):
    """
    El caso del equipo perdido. La cookie sigue siendo válida y bien firmada, pero la persona ya
    no está activa: no debe entrar. Por eso se comprueba en cada petición, no solo al entrar.
    """
    cliente = _app_de_prueba(db)
    cliente.cookies.set(sesion.COOKIE, sesion.crear(gente["ana"].id, gente["ana"].email))
    assert cliente.get("/privado").status_code == 200

    gente["ana"].activo = False
    db.commit()

    assert cliente.get("/privado").status_code == 401


def test_el_rol_comercial_no_administra(db, gente):
    cliente = _app_de_prueba(db)
    cliente.cookies.set(sesion.COOKIE, sesion.crear(gente["ana"].id, gente["ana"].email))
    assert cliente.get("/solo-admin").status_code == 403


def test_el_rol_admin_si_administra(db, gente):
    cliente = _app_de_prueba(db)
    cliente.cookies.set(sesion.COOKIE,
                        sesion.crear(gente["elizabeth"].id, gente["elizabeth"].email))
    assert cliente.get("/solo-admin").status_code == 200


# --- Google: la restricción de dominio -------------------------------------------------

def test_sin_client_id_no_se_ofrece_google(monkeypatch):
    from app.auth import google
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    assert not google.esta_configurado()


def test_sin_configurar_rechaza_cualquier_token(monkeypatch):
    from app.auth import google
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    with pytest.raises(google.IdentidadRechazada):
        google.verificar_identidad("lo-que-sea")


def test_una_cuenta_de_otro_dominio_se_rechaza(monkeypatch):
    """
    El corazón de FR-001a. Se simula que Google valida el identificador y devuelve una cuenta de
    gmail.com: aunque la firma sea buena, esa persona no es del equipo.
    """
    from app.auth import google
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cliente-de-prueba")
    monkeypatch.setattr(
        google.google_id_token, "verify_oauth2_token",
        lambda *a, **k: {"iss": "https://accounts.google.com", "email_verified": True,
                         "email": "cualquiera@gmail.com", "name": "Cualquiera"},
    )
    with pytest.raises(google.IdentidadRechazada) as e:
        google.verificar_identidad("token")
    assert "centauroads.com" in str(e.value)


def test_una_cuenta_del_dominio_se_acepta(monkeypatch):
    from app.auth import google
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cliente-de-prueba")
    monkeypatch.setattr(
        google.google_id_token, "verify_oauth2_token",
        lambda *a, **k: {"iss": "https://accounts.google.com", "email_verified": True,
                         "hd": "centauroads.com", "email": "ana@centauroads.com", "name": "Ana"},
    )
    quien = google.verificar_identidad("token")
    assert quien["email"] == "ana@centauroads.com"
    assert quien["nombre"] == "Ana"


def test_un_correo_sin_verificar_se_rechaza(monkeypatch):
    from app.auth import google
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cliente-de-prueba")
    monkeypatch.setattr(
        google.google_id_token, "verify_oauth2_token",
        lambda *a, **k: {"iss": "https://accounts.google.com", "email_verified": False,
                         "email": "ana@centauroads.com"},
    )
    with pytest.raises(google.IdentidadRechazada):
        google.verificar_identidad("token")


def test_un_emisor_que_no_es_google_se_rechaza(monkeypatch):
    from app.auth import google
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cliente-de-prueba")
    monkeypatch.setattr(
        google.google_id_token, "verify_oauth2_token",
        lambda *a, **k: {"iss": "https://impostor.example", "email_verified": True,
                         "email": "ana@centauroads.com"},
    )
    with pytest.raises(google.IdentidadRechazada):
        google.verificar_identidad("token")
