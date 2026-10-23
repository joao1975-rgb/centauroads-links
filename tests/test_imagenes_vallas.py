"""
Usar las imágenes de Vallas como imágenes de la propuesta (especificación 011).

El botón vive solo en la galería de la propuesta principal (paso 03 de la H) y sube las fotos por el
MISMO camino que el arrastre (`sube(ficheros)`): el servidor no cambia. Lo que hace de verdad —4 miniaturas
sin repetidas, carrusel armado— lo comprueba la demo en navegador.
"""

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module", params=["prototipos/mail/compositor.html", "app/static/email/compositor.html"])
def html(request):
    return (RAIZ / request.param).read_text(encoding="utf-8")


def _funcion(html, nombre):
    i = html.index("\n  function %s(" % nombre)
    return html[i:html.index("\n  }\n", i)]


def test_solo_la_galeria_principal_lleva_el_boton(html):
    assert html.count("desde: {") == 1
    i = html.index("desde: {")
    assert "galeriaDe('principal')" in html[html.rindex("galeria({", 0, i):i]
    assert "Usar las imágenes de Vallas" in html


def test_el_boton_usa_la_misma_subida_y_confirma_antes_de_reemplazar(html):
    g = _funcion(html, "galeria")
    assert "op.desde" in g and "sube(" in g
    assert "op.hayCarrusel()" in g and "confirm(" in g


def test_las_fotos_de_vallas_salen_del_catalogo_el_banco_y_la_portada(html):
    f = _funcion(html, "fotosDeVallas")
    for pieza in ("M.SERVICIOS", "'vallas'", "M.bancoDe(", ".img", ".cover", ".extra", ".fotos"):
        assert pieza in f, pieza
