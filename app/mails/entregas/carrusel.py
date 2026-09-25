"""
De las páginas elegidas al carrusel que viaja en el correo, y a la portada de WhatsApp.

## Dos reglas que no son estéticas

**El fotograma 0 es lo que ve Outlook.** Outlook de escritorio no anima los GIF: enseña el primer
fotograma y ahí se queda. Así que el fotograma 0 es la primera página elegida, entera y quieta, y
tiene que entenderse sola (constitución, restricciones de correo HTML).

**El peso tiene un techo.** Un correo que tarda en cargar no lo lee nadie. El presupuesto es ~1 MB
por pieza, y aquí no se da por supuesto: `arma()` **comprueba el resultado** y, si se pasa, vuelve
a intentarlo con menos pasos de transición y menos colores, hasta que entra. Es preferible un
barrido más brusco que un correo que no abre.

## Por qué Pillow y no FFmpeg

El carrusel de las plantillas A-G se arma con FFmpeg, pero en el portátil de quien diseña. Este se
arma **en el servidor**, y meter FFmpeg en la imagen del contenedor que sirve el acortador son
unos 70 MB y una dependencia de sistema nueva en la máquina que más importa. Pillow ya hace falta
para recortar y redimensionar, y sabe escribir GIF animado.

Esa decisión tenía una condición escrita en el plan (D4): **medirlo**. Medido el 2026-09-23, con
páginas fotográficas reales del inventario a 600 px:

    2 páginas ->  791 KB · 8 pasos de barrido · 128 colores · 4,5 s
    3 páginas ->  971 KB · 4 pasos            · 128 colores · 6,0 s
    4 páginas ->  842 KB · 2 pasos            · 128 colores · 8,3 s

Entra en presupuesto sin bajar de 128 colores, así que **no hace falta FFmpeg**. Lo que se paga
es transición: con cuatro páginas fotográficas el barrido queda en dos pasos, casi un corte. Es el
intercambio correcto —quien lee pasa 2,2 s en cada página quieta y medio segundo en el barrido—,
pero conviene saberlo antes de prometer animación.

Queda un margen estrecho: tres páginas se quedan a 29 KB del techo. Si un deck más pesado se
pasara, el siguiente paso sigue siendo el de D4: añadir `ffmpeg` al `Dockerfile`.
"""

import io
from typing import List, Optional

# Anchura real del correo. Las páginas llegan a 1200 px; aquí bajan a 600 para pesar la mitad de
# la mitad, que en GIF es más que proporcional.
ANCHO = 600
PRESUPUESTO_BYTES = 1_000_000

# Cuánto se queda quieta cada página, y cuánto dura cada paso de la transición.
#
# Son los de los GIF de A-G, sacados de su generador (`prototipos/mail/carrusel_gif.py`): dos
# segundos quieta y 15 fotogramas por segundo, que es donde su propio código pone la frontera
# —"por debajo de 12 la transición se percibe a saltos"—. Doce pasos de 70 ms son 840 ms, que es
# el `TRANS = 0.85` de allí. En un correo que enseña los dos carruseles, el del cliente arriba y
# los de los espacios debajo, cualquier diferencia de compás se nota.
# Cuántos fotogramas se miran para construir la paleta común. Bastan unos pocos
# repartidos por toda la secuencia; mirarlos todos cuesta memoria y no cambia el
# resultado, porque lo que aporta color nuevo son las páginas y las mezclas, no cada
# paso intermedio.
_MUESTRA_PALETA = 8

PAUSA_MS = 2000
PASO_MS = 70

# Intentos, del más vistoso al más pobre.
#
# Empieza en **12 pasos y 256 colores**, y las dos cifras son deliberadas:
#
# - 12 pasos es lo que usan los GIF de A-G. Con 2 la transición dura 180 ms y el ojo la lee como
#   un corte —se vio al poner los dos carruseles en el mismo correo—; con 12 dura un segundo.
# - 256 es el máximo que admite el formato. Antes no tenía sentido pedirlo, porque con una paleta
#   por fotograma más colores significaba una tabla más gorda en CADA fotograma. Con la paleta
#   común (`_escribe`) la tabla es una sola: pasar de 128 a 256 cuesta 62 KB en un barrido de
#   12 pasos y baja el desvío de color de 3,5 a 2,8 niveles sobre 255, que es lo que se ve como
#   bandas en los degradados.
#
# Primero se recortan colores y solo después pasos, al revés que antes. El motivo también cambió:
# ahora el peso lo manda el número de pasos —bajar de 12 a 4 ahorra ocho veces más que bajar de
# 256 a 128— así que empezar por los colores deja la suavidad intacta durante más escalones.
# `pasos` 0 es el corte seco, y queda como último recurso.
_INTENTOS = (
    (12, 256),
    (12, 192),
    (12, 128),
    (12, 96),
    (8, 128),
    (8, 96),
    (6, 128),
    (6, 96),
    (4, 128),
    (4, 96),
    (4, 64),
    (3, 96),
    (3, 64),
    (2, 64),
    (0, 128),
    (0, 96),
)


class Resultado:
    """El GIF y cómo se consiguió, para poder contarlo en vez de suponerlo."""

    def __init__(self, datos: bytes, pasos: int, colores: int, intentos: int,
                 presupuesto: int = PRESUPUESTO_BYTES, efecto: str = 'barrido'):
        self.efecto = efecto
        self.datos = datos
        self.pasos = pasos
        self.colores = colores
        self.intentos = intentos
        # El presupuesto con el que se armó ESTE carrusel, no el de por defecto. Comparar contra
        # la constante del módulo hacía que un resultado dijera «entra» cuando se le había pedido
        # un techo más bajo: la propiedad mentía en el único caso en que importaba.
        self.presupuesto = presupuesto

    @property
    def bytes(self) -> int:
        return len(self.datos)

    @property
    def dentro_de_presupuesto(self) -> bool:
        return self.bytes <= self.presupuesto

    def __repr__(self):
        return "<Carrusel %d KB, %d pasos, %d colores, %d intento(s)%s>" % (
            round(self.bytes / 1024), self.pasos, self.colores, self.intentos,
            "" if self.dentro_de_presupuesto else ", FUERA DE PRESUPUESTO")


def _uniforma(imagenes, ancho: int):
    """
    Todas las páginas al mismo tamaño, que es lo que un GIF exige.

    Se usa el alto de la primera: es la que manda porque es el fotograma 0. Las demás se ajustan
    recortando desde el centro, no deformando — una propuesta estirada se nota.
    """
    from PIL import Image

    base = imagenes[0]
    alto = max(1, round(base.height * ancho / base.width))
    salida = []
    for im in imagenes:
        escala = max(ancho / im.width, alto / im.height)
        nuevo = (max(ancho, round(im.width * escala)), max(alto, round(im.height * escala)))
        im = im.resize(nuevo, Image.LANCZOS)
        izq = (im.width - ancho) // 2
        arr = (im.height - alto) // 2
        salida.append(im.crop((izq, arr, izq + ancho, arr + alto)).convert("RGB"))
    return salida


# Los mismos efectos que el banco de las plantillas A-G. Que se pueda elegir uno y el carrusel
# haga siempre lo mismo es peor que no poder elegir: promete algo que no cumple.
EFECTOS = ('corte', 'barrido', 'persiana', 'fundido', 'deslizar', 'destello', 'zoom')


def suave(t: float) -> float:
    """
    Aceleración y frenada. Una transición lineal se nota mecánica.

    Es la misma curva —y el mismo nombre— que `prototipos/mail/carrusel_gif.py`, el generador de
    los carruseles de los espacios. No una parecida: los dos van en el mismo correo, uno encima
    del otro, y cualquier diferencia de movimiento se lee como que el de arriba "da un golpe".

    Aquí estaba el fallo que las cifras no enseñaban: la duración ya era la correcta —840 ms
    contra los 850 de allí— y aun así parecía un corte, porque en línea recta la página nueva
    sale disparada en el primer fotograma y se para en seco en el último.
    """
    return t * t * (3 - 2 * t)


def _paso(actual, siguiente, efecto: str, t: float):
    """
    Un fotograma intermedio entre dos páginas, con `t` de 0 a 1.

    Cada efecto es una forma distinta de contar lo mismo -que hay otra página detrás- y se elige
    por gusto, no por técnica. El único que se comporta distinto de verdad es `fundido`: mezcla
    los dos fotogramas enteros, así que ningún píxel se repite entre uno y el siguiente y el GIF
    no puede ahorrarse nada. Por eso pesa más, y por eso el presupuesto lo recorta antes.

    `t` entra lineal y se curva aquí, en un solo sitio: así ningún efecto puede olvidarse.
    """
    from PIL import Image

    t = suave(t)
    ancho, alto = actual.size

    if efecto == 'fundido':
        return Image.blend(actual, siguiente, t)

    if efecto == 'zoom':
        # La siguiente crece desde el centro hasta llenar el marco. Como el fundido, cambia cada
        # pixel del fotograma, asi que pesa; el presupuesto ya sabe recortarlo.
        escala = 0.62 + 0.38 * t
        ai, hi = max(1, round(ancho * escala)), max(1, round(alto * escala))
        marco = actual.copy()
        marco.paste(siguiente.resize((ai, hi), Image.LANCZOS), ((ancho - ai) // 2, (alto - hi) // 2))
        return marco

    if efecto == 'destello':
        # Sube a blanco y baja desde la siguiente. El fogonazo va en la mitad del recorrido.
        blanco = Image.new('RGB', (ancho, alto), (255, 255, 255))
        if t < 0.5:
            return Image.blend(actual, blanco, t * 2)
        return Image.blend(blanco, siguiente, (t - 0.5) * 2)

    if efecto == 'deslizar':
        # Las dos se mueven a la vez: la actual sale por la izquierda y la siguiente entra.
        corte = round(ancho * t)
        marco = Image.new('RGB', (ancho, alto))
        marco.paste(actual, (-corte, 0))
        marco.paste(siguiente, (ancho - corte, 0))
        return marco

    if efecto == 'persiana':
        # Ocho franjas horizontales que se abren a la vez. Cuesta lo mismo que el barrido:
        # lo que cambia es por dónde entra.
        marco = actual.copy()
        franjas = 8
        alto_franja = max(1, alto // franjas)
        visible = max(1, round(alto_franja * t))
        for f in range(franjas):
            y = f * alto_franja
            marco.paste(siguiente.crop((0, y, ancho, min(y + visible, alto))), (0, y))
        return marco

    # 'barrido' y cualquier otro: la siguiente se revela por la izquierda. Es la transición más
    # barata en un GIF, porque los fotogramas comparten casi todo con el anterior.
    corte = round(ancho * t)
    marco = actual.copy()
    if corte > 0:
        marco.paste(siguiente.crop((0, 0, corte, alto)), (0, 0))
    return marco


def _fotogramas(paginas, pasos: int, efecto: str = 'barrido'):
    """La secuencia completa: cada página quieta, y la transición que lleva a la siguiente."""
    fotogramas, duraciones = [], []
    total = len(paginas)
    # 'corte' es un cambio seco por definición: no tiene fotogramas intermedios.
    if efecto == 'corte':
        pasos = 0
    for i, actual in enumerate(paginas):
        fotogramas.append(actual)
        duraciones.append(PAUSA_MS)
        siguiente = paginas[(i + 1) % total]
        for p in range(1, pasos + 1):
            fotogramas.append(_paso(actual, siguiente, efecto, p / (pasos + 1)))
            duraciones.append(PASO_MS)
    return fotogramas, duraciones


def _paleta_comun(fotogramas, colores: int):
    """
    Una sola paleta para todo el GIF, sacada de una muestra de los fotogramas de verdad.

    De la muestra y no solo de las páginas: el fogonazo blanco del destello y las mezclas del
    fundido tienen tonos que no están en ninguna página, y una paleta que no los tuviera los
    pintaría a manchas.
    """
    from PIL import Image

    paso = max(1, len(fotogramas) // _MUESTRA_PALETA)
    muestra = fotogramas[::paso][:_MUESTRA_PALETA]
    ancho, alto = fotogramas[0].size
    montaje = Image.new("RGB", (ancho, alto * len(muestra)))
    for i, f in enumerate(muestra):
        montaje.paste(f, (0, i * alto))
    return montaje.convert("P", palette=Image.ADAPTIVE, colors=colores)


def _escribe(fotogramas, duraciones, colores: int) -> bytes:
    """
    El GIF, escrito para que cada fotograma pueda guardarse como **diferencia** del anterior.

    Dos decisiones, y las dos se midieron:

    - **Una paleta común.** Con una paleta por fotograma, cada uno lleva su propia tabla de color
      y hay que reescribirlo entero: un barrido de 12 pasos pesaba 3,1 MB. Compartiendo paleta,
      283 KB. El presupuesto se agotaba en cuatro pasos y la transición duraba 320 ms, que el ojo
      lee como un corte; con doce dura un segundo, igual que los carruseles de A-G.
    - **Sin tramado.** El tramado reparte el error de color con ruido, y ese ruido **cambia en
      cada fotograma aunque la imagen no cambie**: convierte en diferencia lo que era idéntico.
      Quitarlo es lo que más pesa de las dos (0,96 MB → 283 KB en el mismo barrido).
    """
    from PIL import Image

    base = _paleta_comun(fotogramas, colores)
    paleta = [f.quantize(palette=base, dither=Image.NONE) for f in fotogramas]
    buf = io.BytesIO()
    paleta[0].save(buf, format="GIF", save_all=True, append_images=paleta[1:],
                   duration=duraciones, loop=0, optimize=True, disposal=1)
    return buf.getvalue()


def arma(imagenes: List, ancho: int = ANCHO,
         presupuesto: int = PRESUPUESTO_BYTES, efecto: str = 'barrido') -> Resultado:
    """
    El carrusel de 2 a 4 páginas, garantizado bajo presupuesto o lo más cerca posible.

    `imagenes` son objetos PIL en el orden que eligió la persona. La primera es el fotograma 0.
    """
    if len(imagenes) < 2:
        raise ValueError("el carrusel necesita al menos 2 páginas (FR-110)")
    if len(imagenes) > 4:
        raise ValueError("el carrusel admite como mucho 4 páginas (FR-110)")

    paginas = _uniforma(imagenes, ancho)

    if efecto not in EFECTOS:
        efecto = 'barrido'

    def escribe(pasos, colores):
        fotogramas, duraciones = _fotogramas(paginas, pasos, efecto)
        return _escribe(fotogramas, duraciones, colores), len(fotogramas)

    # Primer intento, el bueno. Con páginas ligeras entra a la primera y aquí se acaba.
    pasos, colores = _INTENTOS[0]
    datos, fotogramas = escribe(pasos, colores)
    ultimo = Resultado(datos, pasos, colores, 1, presupuesto, efecto)
    if ultimo.bytes <= presupuesto:
        return ultimo

    # No entró. En vez de ir bajando de uno en uno —con páginas fotográficas eso son seis
    # codificaciones y doce segundos, medidos— se estima con lo que acaba de costar un fotograma
    # y se salta directamente al candidato que debería caber. Sigue verificándose: la estimación
    # elige por dónde empezar, no decide.
    por_fotograma = ultimo.bytes / max(1, fotogramas)
    resto = list(_INTENTOS[1:])
    for i, (p, c) in enumerate(resto):
        previsto = len(paginas) * (1 + p) * por_fotograma * (c / colores)
        if previsto <= presupuesto:
            resto = resto[i:]
            break

    for intento, (pasos, colores) in enumerate(resto, start=2):
        datos, _ = escribe(pasos, colores)
        ultimo = Resultado(datos, pasos, colores, intento, presupuesto, efecto)
        if ultimo.bytes <= presupuesto:
            return ultimo

    # Ni en su forma más pobre entra. Se devuelve igual, con el aviso puesto: quien llama decide
    # si lo entrega o si toca aplicar la salida de D4 (añadir ffmpeg).
    return ultimo


def portada(imagen, ancho: int = 1200, alto: int = 630, calidad: int = 82) -> bytes:
    """
    La imagen de la tarjeta que WhatsApp enseña al pegar el enlace (`og:image`).

    1200 × 630 es la proporción que esperan WhatsApp, Facebook y LinkedIn. Se recorta desde el
    centro en vez de deformar: una propuesta estirada da mala primera impresión, y esta imagen
    **es** la primera impresión.
    """
    from PIL import Image

    im = imagen.convert("RGB")
    escala = max(ancho / im.width, alto / im.height)
    im = im.resize((max(ancho, round(im.width * escala)),
                    max(alto, round(im.height * escala))), Image.LANCZOS)
    izq = (im.width - ancho) // 2
    arr = (im.height - alto) // 2
    im = im.crop((izq, arr, izq + ancho, arr + alto))

    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=calidad, optimize=True, progressive=True)
    return buf.getvalue()


def a_jpeg(imagen, ancho: Optional[int] = None, calidad: int = 85) -> bytes:
    """Una página suelta como JPEG, para guardarla en el volumen."""
    from PIL import Image

    im = imagen.convert("RGB")
    if ancho and im.width > ancho:
        im = im.resize((ancho, max(1, round(im.height * ancho / im.width))), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=calidad, optimize=True, progressive=True)
    return buf.getvalue()
