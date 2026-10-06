"""
El compositor y los espacios que acompañan la entrega (especificación 004).

Lo que se fija aquí, mirando el código del compositor (el comportamiento se prueba en el navegador):

- La presentación principal y cada espacio usan **la misma galería** de páginas: la especificación
  pide que se comporten igual, y dos copias del flujo acabarían separándose.
- En la H, los espacios escriben en `bloques.entrega` (`incluidos`, `espacios`) y no en
  `st.servicios`, que es de las plantillas A–G.
- La entrega se guarda con los espacios que la acompañan, no con el `on` de A–G.
"""

import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module", params=["prototipos/mail/compositor.html", "app/static/email/compositor.html"])
def html(request):
    return (RAIZ / request.param).read_text(encoding="utf-8").replace("\r\n", "\n")


def _funcion(html, nombre):
    """Una funcion de primer nivel del compositor (sangria de dos espacios), entera."""
    i = html.index("\n  function %s(" % nombre)
    return html[i:html.index("\n  }\n", i)]


def test_principal_y_espacios_usan_la_misma_galeria(html):
    assert html.count("function galeria(op)") == 1
    assert "g: galeriaDe('principal')" in html
    assert "g: galeriaDe('espacio:' + sv.id)" in html
    # Ni rastro del flujo viejo, atado a la principal con variables globales.
    for viejo in ("\n  function sube(", "\n  function pintaMinis(", "\n  function armaCarrusel(", "paginasSubidas"):
        assert viejo not in html


def test_la_galeria_de_un_espacio_va_a_sus_propias_rutas(html):
    espacio = _funcion(html, "espacioEl")
    assert "'/espacios/' + encodeURIComponent(sv.id) + '/paginas'" in espacio
    assert "method: 'DELETE'" in espacio


def test_en_la_h_los_espacios_no_tocan_el_estado_de_a_g(html):
    espacio = _funcion(html, "espacioEl")
    assert "E.incluidos" in espacio and "E.espacios" in espacio
    assert not re.search(r"st\.servicios", espacio)
    rama_h = html[html.index("if (st.plantilla === 'H') {"):html.index("p.appendChild(buildPerfil());")]
    assert "espacioEl(sv)" in rama_h and "servicioEl(" not in rama_h


def test_la_entrega_se_guarda_con_sus_espacios(html):
    guarda = _funcion(html, "guardaEntrega")
    assert "servicios: (E.incluidos || []).join(',')" in guarda
    assert "x.on" not in guarda
