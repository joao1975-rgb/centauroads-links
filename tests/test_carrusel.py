"""
Pruebas del carrusel de una entrega.

Existe este fichero por una razón concreta: al romper a propósito el orden de los fotogramas,
**ninguna prueba se enteraba**. La prueba de la API comprobaba el orden de las filas en la base de
datos, que es otra cosa. FR-111 —el fotograma 0 es la primera página elegida— es lo que ve medio
Outlook, que no anima los GIF, y tenía que estar comprobado sobre el GIF de verdad.

Se prueba `carrusel.arma()` a solas, sin FastAPI ni base de datos: es código puro y merece pruebas
puras, que además corren en menos de un segundo.
"""

import io

import pytest
from PIL import Image

from app.mails.entregas import carrusel


def _pagina(color, ancho=1200, alto=675):
    """Una página inventada, de un color plano. Basta para distinguir unas de otras."""
    return Image.new("RGB", (ancho, alto), color)


ROJA = (200, 30, 30)
VERDE = (30, 160, 60)
AZUL = (40, 60, 200)


def _color_medio(im):
    return im.convert("RGB").resize((1, 1)).getpixel((0, 0))


def _cerca(a, b, margen=40):
    """El GIF pasa por paleta y el color se mueve un poco. Se compara con holgura."""
    return all(abs(x - y) <= margen for x, y in zip(a, b))


# --- Los límites son los del requisito, no los de la implementación -------------------

def test_una_sola_pagina_no_es_un_carrusel():
    with pytest.raises(ValueError):
        carrusel.arma([_pagina(ROJA)])


def test_mas_de_cuatro_paginas_se_rechaza():
    with pytest.raises(ValueError):
        carrusel.arma([_pagina(ROJA), _pagina(VERDE), _pagina(AZUL),
                       _pagina(ROJA), _pagina(VERDE)])


# --- FR-111: el fotograma 0 es lo que ve Outlook --------------------------------------

def test_el_fotograma_cero_es_la_primera_pagina_elegida():
    """
    Lo que Outlook enseña y ahí se queda. Si el fotograma 0 fuera otro, el correo abriría por la
    página equivocada en la mitad de los clientes de correo, sin que nadie lo notara aquí.
    """
    resultado = carrusel.arma([_pagina(ROJA), _pagina(VERDE), _pagina(AZUL)])
    gif = Image.open(io.BytesIO(resultado.datos))
    gif.seek(0)
    assert _cerca(_color_medio(gif), ROJA), \
        "el fotograma 0 debería ser la primera página (roja), y es %r" % (_color_medio(gif),)


def test_el_orden_de_las_paginas_es_el_que_se_pide():
    """Invertido el orden de entrada, el fotograma 0 cambia con él."""
    resultado = carrusel.arma([_pagina(AZUL), _pagina(ROJA)])
    gif = Image.open(io.BytesIO(resultado.datos))
    gif.seek(0)
    assert _cerca(_color_medio(gif), AZUL)


def test_el_gif_tiene_mas_de_un_fotograma():
    resultado = carrusel.arma([_pagina(ROJA), _pagina(VERDE)])
    gif = Image.open(io.BytesIO(resultado.datos))
    assert getattr(gif, "n_frames", 1) > 1, "un carrusel de un solo fotograma no es un carrusel"


def test_las_paginas_siguientes_aparecen_en_el_carrusel():
    """No basta con que el primero esté bien: las demás tienen que salir."""
    resultado = carrusel.arma([_pagina(ROJA), _pagina(VERDE)])
    gif = Image.open(io.BytesIO(resultado.datos))
    vistos = []
    for i in range(gif.n_frames):
        gif.seek(i)
        vistos.append(_color_medio(gif))
    assert any(_cerca(c, VERDE, margen=60) for c in vistos), \
        "la segunda página no aparece en ningún fotograma"


# --- Los efectos ----------------------------------------------------------------------

def test_cada_efecto_produce_un_carrusel_distinto():
    """
    Poder elegir un efecto y que el carrusel haga siempre lo mismo es peor que no poder elegir:
    promete algo que no cumple. Aqui se comprueba que cada uno produce bytes distintos.
    """
    paginas = [_pagina(ROJA), _pagina(VERDE), _pagina(AZUL)]
    salidas = {}
    for efecto in carrusel.EFECTOS:
        salidas[efecto] = carrusel.arma(paginas, efecto=efecto).datos
    assert len(set(salidas.values())) == len(carrusel.EFECTOS), (
        'hay efectos que producen el mismo GIF: ' + repr(list(salidas)))


def test_corte_no_tiene_fotogramas_intermedios():
    """Un corte seco es eso: tantos fotogramas como paginas, ni uno mas."""
    paginas = [_pagina(ROJA), _pagina(VERDE), _pagina(AZUL)]
    gif = Image.open(io.BytesIO(carrusel.arma(paginas, efecto='corte').datos))
    assert gif.n_frames == len(paginas)


def test_un_efecto_inventado_cae_en_barrido():
    """
    Mejor una transicion distinta de la pedida que quedarse sin carrusel: quien entrega tiene una
    propuesta que mandar, y el nombre del efecto es lo de menos.
    """
    paginas = [_pagina(ROJA), _pagina(VERDE)]
    inventado = carrusel.arma(paginas, efecto='remolino')
    barrido = carrusel.arma(paginas, efecto='barrido')
    assert inventado.datos == barrido.datos


def test_el_fotograma_cero_no_depende_del_efecto():
    """Sea cual sea la transicion, lo que ve Outlook es la primera pagina."""
    paginas = [_pagina(AZUL), _pagina(ROJA)]
    for efecto in carrusel.EFECTOS:
        gif = Image.open(io.BytesIO(carrusel.arma(paginas, efecto=efecto).datos))
        gif.seek(0)
        assert _cerca(_color_medio(gif), AZUL), 'el efecto %s cambio el fotograma 0' % efecto


# --- El presupuesto se cumple, no se promete ------------------------------------------

def test_el_carrusel_entra_en_presupuesto():
    resultado = carrusel.arma([_pagina(ROJA), _pagina(VERDE), _pagina(AZUL), _pagina(ROJA)])
    assert resultado.dentro_de_presupuesto
    assert resultado.bytes <= carrusel.PRESUPUESTO_BYTES


def test_con_un_presupuesto_imposible_se_degrada_y_lo_dice():
    """
    Con un techo absurdo no hay forma de entrar. Lo que importa es que **no mienta**: devuelve el
    mejor intento y marca que se pasó, para que quien llama pueda avisar en vez de entregar a
    ciegas un correo que no abre.
    """
    resultado = carrusel.arma([_pagina(ROJA), _pagina(VERDE)], presupuesto=500)
    assert not resultado.dentro_de_presupuesto
    assert resultado.intentos > 1, "debería haber intentado degradarse antes de rendirse"


# --- La portada de WhatsApp ----------------------------------------------------------

def test_la_portada_tiene_la_proporcion_que_espera_whatsapp():
    datos = carrusel.portada(_pagina(ROJA, 1600, 900))
    im = Image.open(io.BytesIO(datos))
    assert (im.width, im.height) == (1200, 630)


def test_la_portada_recorta_en_vez_de_deformar():
    """
    Una página muy alta tiene que recortarse, no aplastarse. Se comprueba con una imagen de dos
    mitades: si se deformara, las dos seguirían visibles por igual.
    """
    alta = Image.new("RGB", (600, 2000), ROJA)
    alta.paste(Image.new("RGB", (600, 1000), VERDE), (0, 1000))
    im = Image.open(io.BytesIO(carrusel.portada(alta)))
    assert (im.width, im.height) == (1200, 630)
    arriba = _color_medio(im.crop((0, 0, im.width, 60)))
    abajo = _color_medio(im.crop((0, im.height - 60, im.width, im.height)))
    assert not _cerca(arriba, abajo, margen=30), \
        "el recorte central debería conservar las dos mitades, no una sola"
