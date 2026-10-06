"""
Los tres puntos medios de la auditoría del 2026-10-03 que quedaban abiertos (cerrados el 2026-10-06).

1. **Clickjacking**: ninguna respuesta decía que no se la podía meter dentro de otra página. Un sitio
   ajeno podía cargar el panel en un marco invisible y hacer que alguien con sesión pulsara donde no
   quería. Ahora todas dicen que solo el propio sitio puede enmarcarlas.
2. **X-Forwarded-For**: el contador de intentos toma la dirección de esa cabecera porque detrás de
   Traefik la conexión viene del proxy. Pero si alguien llegara directo al puerto de la app (hoy
   no responde desde fuera; se comprobó), podría escribir la cabecera a su gusto y no bloquearse
   nunca. Solo se cree cuando quien conecta es una dirección privada: la del proxy.
3. **El contador crecía sin límite**: bastaba con *comprobar* una dirección para dejarle una entrada
   vacía en memoria para siempre. Ahora solo guarda direcciones con fallos recientes, y tiene tope.
"""

import pytest
from fastapi.testclient import TestClient
from starlette.requests import Request

from app import main as app_main
from app.auth import intentos


# --- 1. Nadie mete el panel dentro de otra pagina ------------------------------------------------

@pytest.mark.parametrize("ruta", ["/panel/entrar", "/static/email/compositor.html", "/health", "/api/catalogo"])
def test_ninguna_respuesta_se_deja_enmarcar_por_otro_sitio(ruta):
    r = TestClient(app_main.app).get(ruta, follow_redirects=False)
    assert r.headers.get("x-frame-options") == "SAMEORIGIN"
    assert "frame-ancestors 'self'" in r.headers.get("content-security-policy", "")
    assert r.headers.get("x-content-type-options") == "nosniff"


# --- 2. X-Forwarded-For solo se cree si quien conecta es el proxy --------------------------------

def _peticion(cliente, reenviada):
    return Request({"type": "http", "method": "POST", "path": "/", "headers": [(b"x-forwarded-for", reenviada.encode())],
                    "client": (cliente, 40000), "query_string": b""})


def test_desde_el_proxy_vale_la_direccion_reenviada():
    assert intentos.direccion(_peticion("10.0.1.7", "203.0.113.50")) == "203.0.113.50"


def test_quien_llega_directo_no_elige_su_direccion():
    assert intentos.direccion(_peticion("198.51.100.20", "203.0.113.50")) == "198.51.100.20"


# --- 3. El contador no crece sin limite ----------------------------------------------------------

def test_comprobar_no_deja_rastro_de_quien_no_ha_fallado():
    for n in range(500):
        intentos.comprueba(_peticion("10.0.0.1", "203.0.113.%d" % (n % 250)), "entrada", intentos.MAX_ENTRADA)
    assert len(intentos._fallos) == 0


def test_los_fallos_viejos_se_olvidan(monkeypatch):
    reloj = [1000.0]
    monkeypatch.setattr(intentos, "_ahora", lambda: reloj[0])
    intentos.fallo(_peticion("10.0.0.1", "203.0.113.1"), "entrada")
    reloj[0] += intentos.VENTANA_SEGUNDOS + 1
    intentos.fallo(_peticion("10.0.0.1", "203.0.113.2"), "entrada")
    assert ("entrada", "203.0.113.1") not in intentos._fallos


def test_hay_un_tope_de_direcciones_vigiladas(monkeypatch):
    monkeypatch.setattr(intentos, "MAX_DIRECCIONES", 50)
    for n in range(200):
        intentos.fallo(_peticion("10.0.0.1", "198.51.100.%d" % n), "entrada")
    assert len(intentos._fallos) <= 50
