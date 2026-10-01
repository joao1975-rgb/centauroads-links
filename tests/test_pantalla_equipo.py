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
