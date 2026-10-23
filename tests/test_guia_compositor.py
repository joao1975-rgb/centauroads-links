"""
La guía personalizada (plantilla I) en el compositor (especificación 012, T1204 y T1205).

Lo que hace de verdad —crear, apagar una fase, cambiar el producto, subir imágenes, reabrir— lo
comprueba la demo en navegador. Aquí, las reglas que no pueden romperse sin que se note:
- H e I comparten `bloques.entrega`: al cambiar de pestaña la otra queda aparte, y el guardado
  automático solo escribe sobre una entrega de SU formato.
- Abrir una entrega la lleva a su formato.
- Cada fase usa la presentación del espacio de su producto (004), solo con el enlace.
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


def test_el_autoguardado_solo_escribe_en_una_entrega_de_su_formato(html):
    i = html.index("const puedeAutoguardar")
    assert "(st.entregaFormato || 'H') === st.plantilla" in html[i:i + 300]


def test_cambiar_de_pestana_deja_aparte_la_otra_entrega(html):
    f = _funcion(html, "cambiaFormato")
    assert "st.aparte[de]" in f and "entregaNueva(k)" in f and "st.entregaFormato = k" in f
    assert "cambiaFormato(k); st.plantilla = k" in _funcion(html, "buildSeg")


def test_abrir_una_entrega_la_lleva_a_su_formato(html):
    f = _funcion(html, "abreEntrega")
    assert "st.plantilla = d.formato === 'I' ? 'I' : 'H'" in f and "E.guia = d.guia" in f


def test_la_guia_viaja_con_la_entrega_y_cuenta_para_el_guardado(html):
    c = _funcion(html, "cuerpoEntrega")
    assert "formato: esI ? 'I' : 'H'" in c and "canonGuia(guiaE())" in c
    assert "d.guia)" in html[html.index("const firmaDe"):html.index("const firmaDe") + 250]


def test_cada_fase_usa_el_espacio_de_su_producto_solo_con_el_enlace(html):
    f = _funcion(html, "faseEl")
    assert "cuerpoEspacio(sv, ['canva']" in f
    assert "usados.indexOf(sv.id) < 0" in f      # un producto no se repite entre fases
