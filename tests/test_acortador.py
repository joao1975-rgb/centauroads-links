"""
La red que protege el acortador.

El Principio I de la constitución dice que el acortador no se toca. Esto es lo que lo comprueba:
las rutas que existían antes del módulo de mails siguen ahí y siguen comportándose igual, sobre
un esquema ya migrado.

Lo que más importa de este fichero es `test_la_redireccion_sigue_funcionando`: un enlace roto no
es un fallo de software, es una valla impresa apuntando a ninguna parte.

La aplicación se importa con DATABASE_URL apuntando a una base de datos temporal, porque
`app.main` crea tablas y migra en tiempo de importación.
"""

import pytest
from fastapi.testclient import TestClient

# conftest.py ya apuntó DATABASE_URL y las claves a un directorio temporal antes de que esto se
# importe, así que basta con importar la aplicación tal cual.
from app import main as app_main


@pytest.fixture(scope="module")
def entorno():
    """La aplicación entera, sobre la base de datos desechable que preparó conftest."""
    cliente = TestClient(app_main.app)
    cabecera = {"X-Admin-Key": app_main.get_admin_password()}
    return cliente, cabecera


@pytest.fixture()
def cliente(entorno):
    return entorno[0]


@pytest.fixture()
def admin(entorno):
    return entorno[1]


# --- Rutas públicas -------------------------------------------------------------------

def test_health_responde(cliente):
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["service"] == "centaurads-links"


def test_la_portada_responde(cliente):
    assert cliente.get("/").status_code == 200


def test_el_panel_responde(cliente):
    assert cliente.get("/admin").status_code == 200


# --- La API exige clave, igual que antes ---------------------------------------------

def test_listar_enlaces_sin_clave_da_401(cliente):
    assert cliente.get("/api/links").status_code == 401


def test_listar_enlaces_con_clave_mala_da_401(cliente):
    assert cliente.get("/api/links", headers={"X-Admin-Key": "no"}).status_code == 401


def test_listar_enlaces_con_clave_buena(cliente, admin):
    r = cliente.get("/api/links", headers=admin)
    assert r.status_code == 200
    assert isinstance(r.json(), list)


# --- Ciclo completo de un enlace ------------------------------------------------------

ENLACE = {
    "slug": "prueba-led",
    "target_url": "https://www.canva.com/design/EJEMPLO/view",
    "name": "Pantallas LED",
    "description": "Prueba",
    "category": "DOOH",
}


def test_crear_enlace(cliente, admin):
    r = cliente.post("/api/links", json=ENLACE, headers=admin)
    assert r.status_code == 200, r.text
    assert r.json()["slug"] == ENLACE["slug"]


def test_slug_repetido_da_409(cliente, admin):
    r = cliente.post("/api/links", json=ENLACE, headers=admin)
    assert r.status_code == 409


def test_url_repetida_da_409(cliente, admin):
    otro = dict(ENLACE, slug="otro-slug")
    r = cliente.post("/api/links", json=otro, headers=admin)
    assert r.status_code == 409, "La prohibición de destinos repetidos dejó de funcionar"


def test_slug_reservado_se_rechaza(cliente, admin):
    malo = dict(ENLACE, slug="admin", target_url="https://ejemplo.test/otro")
    assert cliente.post("/api/links", json=malo, headers=admin).status_code == 422


def test_slug_con_mayusculas_se_rechaza(cliente, admin):
    malo = dict(ENLACE, slug="MalSlug", target_url="https://ejemplo.test/mayusculas")
    assert cliente.post("/api/links", json=malo, headers=admin).status_code == 422


def test_la_redireccion_sigue_funcionando(cliente):
    """
    La ruta que sostiene todo lo impreso en la calle. 307 al destino, sin intersticial.
    """
    r = cliente.get(f"/{ENLACE['slug']}", follow_redirects=False)
    assert r.status_code == 307, "La redirección cambió de código"
    assert r.headers["location"] == ENLACE["target_url"]


def test_la_redireccion_cuenta_el_clic(cliente, admin):
    antes = cliente.get("/api/links", headers=admin).json()[0]["click_count"]
    cliente.get(f"/{ENLACE['slug']}", follow_redirects=False)
    despues = cliente.get("/api/links", headers=admin).json()[0]["click_count"]
    assert despues == antes + 1, "El contador de clics dejó de subir"


def test_slug_inexistente_da_404(cliente):
    assert cliente.get("/no-existe-este-slug", follow_redirects=False).status_code == 404


def test_estadisticas(cliente, admin):
    link_id = cliente.get("/api/links", headers=admin).json()[0]["id"]
    r = cliente.get(f"/api/links/{link_id}/stats", headers=admin)
    assert r.status_code == 200
    cuerpo = r.json()
    for campo in ("total_clicks", "unique_clicks", "deliveries_count", "ctr", "recent_clicks"):
        assert campo in cuerpo, f"Las estadísticas perdieron el campo {campo}"


def test_registrar_entrega(cliente, admin):
    r = cliente.post(f"/api/links/{ENLACE['slug']}/deliver?channel=whatsapp", headers=admin)
    assert r.status_code == 200
    assert r.json()["channel"] == "whatsapp"


def test_actualizar_enlace(cliente, admin):
    link_id = cliente.get("/api/links", headers=admin).json()[0]["id"]
    r = cliente.put(f"/api/links/{link_id}", json={"name": "Renombrado"}, headers=admin)
    assert r.status_code == 200
    assert r.json()["name"] == "Renombrado"


def test_superadmin_login(cliente):
    r = cliente.post("/api/superadmin/login",
                     json={"user": "super@ejemplo.test", "password": "contrasena-de-prueba"})
    assert r.status_code == 200
    assert "current_password" in r.json()


def test_superadmin_credenciales_malas(cliente):
    r = cliente.post("/api/superadmin/login",
                     json={"user": "super@ejemplo.test", "password": "mal"})
    assert r.status_code == 401


def test_borrar_enlace(cliente, admin):
    link_id = cliente.get("/api/links", headers=admin).json()[0]["id"]
    assert cliente.delete(f"/api/links/{link_id}", headers=admin).status_code == 200
    assert cliente.delete(f"/api/links/{link_id}", headers=admin).status_code == 404


# --- El módulo de mails no se ha colado en el camino del acortador --------------------

def test_las_rutas_del_acortador_siguen_todas_presentes():
    """
    Inventario explícito. Si alguien retira una ruta sin darse cuenta, esto lo caza.
    """
    rutas = {r.path for r in app_main.app.routes}
    esperadas = {
        "/health", "/admin", "/", "/{slug}",
        "/api/links", "/api/links/{link_id}", "/api/links/{link_id}/stats",
        "/api/links/{slug}/deliver",
        "/api/superadmin/login", "/api/superadmin/change",
    }
    faltan = esperadas - rutas
    assert not faltan, f"Desaparecieron rutas del acortador: {faltan}"
