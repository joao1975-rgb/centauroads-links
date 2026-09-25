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


# --- El ritmo, que es lo que se compara con los carruseles de al lado ------------------
#
# En el mismo correo van dos carruseles: el de la propuesta del cliente arriba y los de los
# espacios debajo. Si no van al mismo compás se nota, y lo que se ve es que el de arriba "da un
# golpe". Las cifras son las de los GIF de A-G, medidas sobre los propios ficheros.

def _duraciones(datos):
    gif = Image.open(io.BytesIO(datos))
    fuera = []
    for i in range(gif.n_frames):
        gif.seek(i)
        fuera.append(gif.info.get("duration"))
    return fuera


def test_cada_pagina_se_queda_quieta_dos_segundos():
    """
    2000 ms, como los de A-G. Se compara con el número, no con la constante: si alguien cambia la
    constante, esta prueba tiene que enterarse — que es justo lo que no pasaba.
    """
    datos = carrusel.arma([_pagina(ROJA), _pagina(VERDE), _pagina(AZUL)]).datos
    assert _duraciones(datos)[0] == 2000


def test_cada_paso_dura_lo_que_marca_el_generador_de_los_otros():
    """
    70 ms. `prototipos/mail/carrusel_gif.py` va a 15 fps y pone ahí la frontera —"por debajo de
    12 la transición se percibe a saltos"—; doce pasos de 70 ms son 840 ms, que es su `TRANS`.
    """
    datos = carrusel.arma([_pagina(ROJA), _pagina(VERDE), _pagina(AZUL)]).datos
    intermedios = [d for d in _duraciones(datos) if d != 2000]
    assert intermedios, "no hay ningún fotograma de transición"
    assert set(intermedios) == {70}


def _avance_del_barrido(datos):
    """
    Dónde va el filo del barrido en cada fotograma, de 0 a 1.

    Se mira una fila de píxeles y se cuenta cuántos son ya de la página siguiente. Es la forma
    directa de ver la CURVA del movimiento, que es lo que ninguna cifra de duración enseña.
    """
    gif = Image.open(io.BytesIO(datos))
    fuera = []
    for i in range(gif.n_frames):
        gif.seek(i)
        fila = list(gif.convert("RGB").crop((0, 100, gif.width, 101)).getdata())
        verdes = sum(1 for px in fila if px[1] > px[0])
        fuera.append(verdes / float(gif.width))
    return fuera


def test_la_transicion_acelera_y_frena():
    """
    Una transición lineal se nota mecánica: la página nueva sale disparada en el primer fotograma
    y se para en seco en el último. `suave()` la hace arrancar despacio, correr por el medio y
    frenar al llegar — la misma curva que usa el generador de los carruseles de los espacios,
    porque los dos van en el mismo correo.

    Esto es lo que las duraciones no enseñaban: el ritmo ya era el correcto y aun así se veía
    como un golpe.
    """
    datos = carrusel.arma([_pagina(ROJA), _pagina(VERDE)], efecto="barrido").datos
    avances = _avance_del_barrido(datos)
    # Los pasos de la PRIMERA transición: del fotograma 1 hasta antes de la página quieta.
    tramo = avances[1:avances.index(max(avances)) + 1]
    assert len(tramo) >= 6, "hacen falta pasos suficientes para ver la curva: %d" % len(tramo)
    paso = [b - a for a, b in zip(tramo, tramo[1:])]
    medio = paso[len(paso) // 2]
    assert medio > paso[0] * 1.5, (
        "el primer paso avanza %.3f y el del medio %.3f: eso es una recta, no una curva"
        % (paso[0], medio))
    assert medio > paso[-1] * 1.5, (
        "no frena al llegar: paso del medio %.3f, último %.3f" % (medio, paso[-1]))


def test_la_transicion_no_se_lee_como_un_corte():
    """
    Con dos pasos la transición dura 160 ms y el ojo la lee como un cambio seco: es lo que se vio
    al ponerla al lado de los carruseles de A-G, que usan doce. Con páginas que caben de sobra no
    hay excusa para recortar.
    """
    r = carrusel.arma([_pagina(ROJA), _pagina(VERDE), _pagina(AZUL)], efecto="barrido")
    assert r.pasos >= 12, "el barrido se quedó en %d pasos (%d ms de transición)" % (
        r.pasos, r.pasos * 80)


def test_el_carrusel_se_repite_sin_fin():
    """`loop=0` es infinito. Con cualquier otro número el cliente se queda mirando la última."""
    datos = carrusel.arma([_pagina(ROJA), _pagina(VERDE)]).datos
    assert Image.open(io.BytesIO(datos)).info.get("loop") == 0


def _degradado(c1, c2):
    """
    Una página con degradado, que es lo que son las de verdad.

    Con colores planos esta prueba no sirve: comprimen igual de bien con paleta común que sin
    ella, y las dos roturas que tiene que cazar pasaban desapercibidas. Se construye pequeña y se
    amplía: sale un degradado suave, con cientos de tonos, en un parpadeo.
    """
    chico = Image.new("RGB", (32, 32))
    px = chico.load()
    for y in range(32):
        for x in range(32):
            t = (x + y) / 62
            px[x, y] = tuple(round(a + (b - a) * t) for a, b in zip(c1, c2))
    return chico.resize((600, 338), Image.BILINEAR)


def test_el_gif_lleva_una_sola_paleta_y_sin_tramado():
    """
    Las dos decisiones que hicieron posible la transición suave, y las dos se pueden deshacer sin
    que nada más se entere.

    Con **una paleta por fotograma**, cada uno lleva su tabla de color y hay que reescribirlo
    entero. Con **tramado**, el ruido que reparte el error de color cambia en cada fotograma
    aunque la imagen no cambie, y convierte en diferencia lo que era idéntico. Cualquiera de las
    dos agota el presupuesto en cuatro pasos y devuelve el golpe seco.

    Medido sobre estas mismas páginas: 1,10 MB con paleta propia y tramado, 362 KB con paleta
    común pero tramando, y 126 KB como está. El techo va entre medias de las dos últimas, que es
    lo que hace que la prueba muerda también cuando solo se deshace una de las dos.
    """
    paginas = [_degradado((60, 20, 90), (240, 150, 40)),
               _degradado((20, 80, 60), (200, 220, 240)),
               _degradado((90, 10, 10), (250, 240, 200))]
    r = carrusel.arma(paginas, efecto="barrido")
    assert r.pasos >= 12, "no cupieron los 12 pasos: %d" % r.pasos
    assert r.bytes < 250_000, (
        "%d bytes para 12 pasos: el GIF no está guardando diferencias, así que o cada fotograma "
        "lleva su propia paleta o se está tramando" % r.bytes)


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
