"""
La pantalla del equipo: /panel/equipo (2026-10-01, T126 de la 002).

La API de la lista (alta, baja, contraseñas) existía desde la 002, pero solo se podía usar a mano.
Con Google sin configurar, eso significaba que nadie más que quien conociera la API podía dar
acceso a otra persona, y la herramienta no se podía repartir al equipo. Esta pantalla es la cara
de esa API: no añade permisos nuevos, así que las reglas siguen siendo las de la API (solo un
administrador administra; cada quien cambia la suya dando la actual).
"""

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import rutas, sesion
from app.database import SessionLocal

PANTALLA = "/panel/equipo"


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def cliente():
    return TestClient(app_main.app)


def _alta(db, email, rol):
    u = db.query(models.PanelUser).filter(models.PanelUser.email == email).first()
    if not u:
        u = models.PanelUser(email=email, nombre=email.split("@")[0], rol=rol, activo=True)
        db.add(u)
    u.rol, u.activo = rol, True
    db.commit()
    db.refresh(u)
    return u


def _entra(cliente, u):
    cliente.cookies.set(sesion.COOKIE, sesion.crear(u.id, u.email))


def test_sin_sesion_lleva_a_la_entrada_y_vuelve_a_la_pantalla(cliente):
    cliente.cookies.clear()
    r = cliente.get(PANTALLA, follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/panel/entrar?destino=%2Fpanel%2Fequipo"


def test_con_sesion_se_abre_y_no_se_guarda_en_cache(cliente, db):
    _entra(cliente, _alta(db, "jefa.equipo@gmail.com", "admin"))
    r = cliente.get(PANTALLA)
    assert r.status_code == 200
    assert r.headers.get("cache-control") == "no-store"
    assert "<title>Equipo · Centauro ADS</title>" in r.text


def test_la_pantalla_tiene_las_tres_partes(cliente, db):
    _entra(cliente, _alta(db, "jefa.equipo@gmail.com", "admin"))
    html = cliente.get(PANTALLA).text
    for marca in ('id="lista"', 'id="alta"', 'id="mia"'):
        assert marca in html, marca


def test_un_comercial_tambien_entra_para_cambiar_la_suya(cliente, db):
    """La pantalla no es solo de administradores: la parte de la contraseña propia es de todos.
    La lista la pide el navegador a la API, que a un comercial le contesta 403."""
    _entra(cliente, _alta(db, "vendedor.equipo@gmail.com", "comercial"))
    assert cliente.get(PANTALLA).status_code == 200
    assert cliente.get("/api/panel/usuarios").status_code == 403


def test_no_pinta_datos_con_innerhtml(cliente, db):
    """Nombres y correos los escribe gente: se ponen como texto, nunca como HTML."""
    _entra(cliente, _alta(db, "jefa.equipo@gmail.com", "admin"))
    assert "innerHTML" not in cliente.get(PANTALLA).text


def test_la_entrada_acepta_volver_a_la_pantalla(cliente):
    cliente.cookies.clear()
    html = cliente.get("/panel/entrar", params={"destino": PANTALLA}).text
    assert '"/panel/equipo"' in html


def test_el_compositor_enlaza_la_pantalla_y_la_salida(cliente, db):
    _entra(cliente, _alta(db, "jefa.equipo@gmail.com", "admin"))
    html = cliente.get(rutas.COMPOSITOR).text
    assert 'href="/panel/equipo"' in html
    assert 'href="/panel/salir"' in html


def test_el_recorrido_completo_por_la_api_que_usa_la_pantalla(cliente, db):
    """Lo que hace la pantalla al añadir a alguien: alta + contraseña, y esa persona entra."""
    _entra(cliente, _alta(db, "jefa.equipo@gmail.com", "admin"))
    nuevo = cliente.post("/api/panel/usuarios",
                         json={"email": "nueva.equipo@gmail.com", "nombre": "Nueva", "rol": "comercial"}).json()
    assert cliente.post(f"/api/panel/usuarios/{nuevo['id']}/contrasena",
                        json={"password": "una-clave-larga-de-prueba"}).status_code == 200
    cliente.cookies.clear()
    r = cliente.post("/api/auth/local",
                     json={"email": "nueva.equipo@gmail.com", "password": "una-clave-larga-de-prueba"})
    assert r.status_code == 200


# --- Editar a quien ya está (2026-10-01, petición del usuario) ---------------------------------
# Corregir un correo mal escrito, el nombre, o pasar a alguien de comercial a administrador sin
# darle de baja y de alta. La sesión va por el número de la persona, no por su correo, así que
# cambiarle el correo no le cierra la sesión.

def _ruta(u):
    return f"/api/panel/usuarios/{u.id}"


def test_un_administrador_edita_correo_nombre_y_rol(cliente, db):
    _entra(cliente, _alta(db, "jefa.equipo@gmail.com", "admin"))
    otro = _alta(db, "mal.escrito@gmail.con", "comercial")
    r = cliente.patch(_ruta(otro), json={"email": " Bien.Escrito@Gmail.com ", "nombre": "Bien Escrito",
                                         "rol": "admin"})
    assert r.status_code == 200, r.text
    assert r.json() == {"id": otro.id, "email": "bien.escrito@gmail.com", "nombre": "Bien Escrito",
                        "rol": "admin", "activo": True}
    db.refresh(otro)
    assert (otro.email, otro.nombre, otro.rol) == ("bien.escrito@gmail.com", "Bien Escrito", "admin")


def test_solo_cambia_lo_que_se_manda(cliente, db):
    _entra(cliente, _alta(db, "jefa.equipo@gmail.com", "admin"))
    otro = _alta(db, "parcial.equipo@gmail.com", "comercial")
    assert cliente.patch(_ruta(otro), json={"rol": "admin"}).status_code == 200
    db.refresh(otro)
    assert (otro.email, otro.rol) == ("parcial.equipo@gmail.com", "admin")


def test_un_comercial_no_puede_editar(cliente, db):
    otro = _alta(db, "victima.equipo@gmail.com", "comercial")
    _entra(cliente, _alta(db, "vendedor.equipo@gmail.com", "comercial"))
    assert cliente.patch(_ruta(otro), json={"rol": "admin"}).status_code == 403


def test_el_correo_no_puede_repetirse(cliente, db):
    _entra(cliente, _alta(db, "jefa.equipo@gmail.com", "admin"))
    _alta(db, "ocupado.equipo@gmail.com", "comercial")
    otro = _alta(db, "libre.equipo@gmail.com", "comercial")
    r = cliente.patch(_ruta(otro), json={"email": "OCUPADO.equipo@gmail.com"})
    assert r.status_code == 409


@pytest.mark.parametrize("malo", ["sin-arroba", "a@b", "@gmail.com", "uno dos@gmail.com", ""])
def test_el_correo_tiene_que_parecer_un_correo(cliente, db, malo):
    _entra(cliente, _alta(db, "jefa.equipo@gmail.com", "admin"))
    otro = _alta(db, "formato.equipo@gmail.com", "comercial")
    assert cliente.patch(_ruta(otro), json={"email": malo}).status_code in (400, 422)


def test_el_rol_solo_admin_o_comercial(cliente, db):
    _entra(cliente, _alta(db, "jefa.equipo@gmail.com", "admin"))
    otro = _alta(db, "rol.equipo@gmail.com", "comercial")
    assert cliente.patch(_ruta(otro), json={"rol": "dueño"}).status_code == 400


def test_nadie_se_quita_a_si_mismo_el_rol_de_administrador(cliente, db):
    """Así siempre queda al menos un administrador: nadie puede dejar el panel sin quien lo gestione."""
    jefa = _alta(db, "jefa.equipo@gmail.com", "admin")
    _entra(cliente, jefa)
    r = cliente.patch(_ruta(jefa), json={"rol": "comercial"})
    assert r.status_code == 400
    db.refresh(jefa)
    assert jefa.rol == "admin"


def test_cambiarse_el_propio_correo_no_cierra_la_sesion(cliente, db):
    jefa = _alta(db, "jefa.vieja@gmail.com", "admin")
    _entra(cliente, jefa)
    assert cliente.patch(_ruta(jefa), json={"email": "jefa.nueva@gmail.com"}).status_code == 200
    assert cliente.get("/api/auth/yo").json()["email"] == "jefa.nueva@gmail.com"


def test_editar_a_quien_no_existe_da_404(cliente, db):
    _entra(cliente, _alta(db, "jefa.equipo@gmail.com", "admin"))
    assert cliente.patch("/api/panel/usuarios/999999", json={"rol": "admin"}).status_code == 404


def test_la_pantalla_trae_el_editor_con_el_rol_desplegable(cliente, db):
    _entra(cliente, _alta(db, "jefa.equipo@gmail.com", "admin"))
    html = cliente.get(PANTALLA).text
    assert "'Editar'" in html
    assert "createElement('select')" in html or "el('select'" in html
    assert "'PATCH'" in html
