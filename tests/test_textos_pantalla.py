"""
La pantalla «Textos de los perfiles» (/panel/textos, especificación 005).

La página no lleva datos: los pide a la API y los escribe como texto (los teclea gente). Lo que se
fija aquí, mirando lo que se sirve (el comportamiento se prueba en el navegador):

- Sin sesión, a la entrada, y de vuelta aquí al entrar.
- Pide los textos a la API y los pinta con `textContent`/`value`, nunca como HTML.
- Para un comercial queda en solo lectura: los botones de cambiar solo salen con rol de administrador.
- Se llega desde el compositor y desde Líneas de negocio.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import sesion
from app.database import SessionLocal

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def pagina():
    with SessionLocal() as db:
        u = db.query(models.PanelUser).filter(models.PanelUser.email == "comercial-txt@ejemplo.test").first()
        if not u:
            u = models.PanelUser(email="comercial-txt@ejemplo.test", nombre="comercial-txt", rol="comercial", activo=True)
            db.add(u)
            db.commit()
            db.refresh(u)
        c = TestClient(app_main.app)
        c.cookies.set(sesion.COOKIE, sesion.crear(u.id, u.email))
    r = c.get("/panel/textos")
    assert r.status_code == 200
    assert r.headers["cache-control"] == "no-store"
    return r.text


def test_sin_sesion_lleva_a_la_entrada_y_vuelve_aqui():
    r = TestClient(app_main.app).get("/panel/textos", follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/panel/entrar?destino=%2Fpanel%2Ftextos"


def test_pide_los_textos_a_la_api_y_los_pinta_como_texto(pagina):
    assert "<h1>Textos de los perfiles</h1>" in pagina
    assert "'/api/panel/textos'" in pagina and "'/api/auth/yo'" in pagina
    assert "innerHTML" not in pagina
    assert "Inventario disponible" not in pagina  # los datos no van en la página


def test_solo_un_administrador_ve_como_cambiar(pagina):
    assert "esAdmin = d.rol === 'admin'" in pagina
    assert "readOnly = !esAdmin" in pagina
    assert "if (esAdmin)" in pagina
    assert "'PUT', '/api/panel/textos/' + encodeURIComponent(t.clave)" in pagina
    assert "'DELETE', '/api/panel/textos/' + encodeURIComponent(t.clave)" in pagina


@pytest.mark.parametrize("archivo", ["prototipos/mail/compositor.html", "app/static/email/compositor.html",
                                     "app/mails/catalogo/pantalla.py"])
def test_se_llega_desde_el_compositor_y_desde_lineas(archivo):
    assert '<a href="/panel/textos">Textos de los perfiles</a>' in (RAIZ / archivo).read_text(encoding="utf-8")
