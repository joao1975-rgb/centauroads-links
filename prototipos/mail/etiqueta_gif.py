#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generador de la etiqueta promocional animada, en GIF.

Por que un GIF y no CSS: el correo no ejecuta JavaScript y las animaciones CSS no llegan a Gmail
ni a Outlook. Lo unico que se mueve de verdad en todos los clientes es un GIF. Y hay un premio
extra: lo que en HTML de correo es imposible -inclinar una pieza, un barrido de brillo, un rebote-
dentro de una imagen sale gratis.

REGLA QUE MANDA SOBRE TODO (constitucion del proyecto, principio III):
    el fotograma 0 es lo que ve Outlook.
Asi que la animacion NO empieza vacia. Arranca en el estado final, hace su numero y vuelve. Quien
no vea el movimiento ve una etiqueta acabada, no un hueco.

Los efectos, con su nombre propio:
  - Shimmer   : un barrido de luz diagonal cruza el naranja. Lee como papel metalizado.
  - Anticipation + Pop : el numero se encoge un pelo antes de saltar, y rebasa el tamano final
                antes de asentarse. El encogimiento previo es lo que hace que el salto se sienta.
  - Hold      : un descanso largo al final. Es lo que evita que el bucle canse: quien lee el correo
                va a ver esto muchas veces, y cuanto mas se repite un movimiento, mas corto y mas
                espaciado tiene que ser.

Uso:
    python etiqueta_gif.py --descuento "15%" --hasta "31/10/2026" --salida img/etq_promo.gif
    python etiqueta_gif.py --descuento "2x1" --salida img/etq_dto.gif       (solo descuento)
    python etiqueta_gif.py --hasta "05/12/2026" --salida img/etq_fecha.gif  (solo fecha)
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

# -- Marca --------------------------------------------------------------------------------
NARANJA = (247, 145, 49)
MORADO = (133, 67, 154)
TINTA = (20, 16, 22)        # texto sobre naranja
BLANCO = (255, 255, 255)
LILA = (232, 213, 239)      # rotulo sobre morado: 5,5:1 de contraste

# Se dibuja al doble de resolucion y se muestra a la mitad, para que no se vea blando en
# pantallas densas. El ancho logico (264 px) es el de la tarjeta del catalogo B.
ESCALA = 2
ANCHO, ALTO = 264 * ESCALA, 58 * ESCALA

FPS = 15
DUR_SHIMMER = 0.75
DUR_POP = 0.55
DUR_DESCANSO = 2.1          # el descanso largo que evita el cansancio del bucle
RUTA_FUENTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes")


def fuente(nombre, tam):
    ruta = os.path.join(RUTA_FUENTES, nombre)
    if not os.path.exists(ruta):
        sys.exit(
            "Falta la tipografia: %s\n"
            "Descargar Montserrat (SIL OFL) a %s:\n"
            "  curl -sSL -o %s \\\n"
            "    https://raw.githubusercontent.com/JulietaUla/Montserrat/master/fonts/ttf/%s"
            % (ruta, RUTA_FUENTES, ruta, nombre)
        )
    return ImageFont.truetype(ruta, tam)


def texto_espaciado(draw, xy, txt, fnt, color, tracking=0, anclaje="mm"):
    """
    Dibuja con espaciado entre letras. PIL no lo hace, y sin tracking los rotulos en mayuscula
    pequena se apelmazan y pierden justo el aire que los hace leerse como etiqueta.
    """
    if not tracking:
        draw.text(xy, txt, font=fnt, fill=color, anchor=anclaje)
        return
    anchos = [draw.textlength(c, font=fnt) for c in txt]
    total = sum(anchos) + tracking * (len(txt) - 1)
    x = xy[0] - total / 2 if anclaje[0] == "m" else xy[0]
    for c, w in zip(txt, anchos):
        draw.text((x, xy[1]), c, font=fnt, fill=color, anchor="l" + anclaje[1])
        x += w + tracking


def celda_descuento(img, numero, x0, ancho, escala_num):
    """El premio. El numero manda; la palabra lo acompana."""
    d = ImageDraw.Draw(img)
    d.rectangle([x0, 0, x0 + ancho, ALTO], fill=NARANJA)
    cx = x0 + ancho / 2

    tam = max(int(22 * ESCALA * escala_num), 8)
    f_num = fuente("Montserrat-ExtraBold.ttf", tam)
    d.text((cx, ALTO * 0.40), numero, font=f_num, fill=TINTA, anchor="mm")

    f_lbl = fuente("Montserrat-Bold.ttf", int(9.5 * ESCALA))
    texto_espaciado(d, (cx, ALTO * 0.74), "DE DESCUENTO", f_lbl, TINTA, tracking=1.6 * ESCALA)


def celda_fecha(img, fecha, x0, ancho):
    """El contrapunto: la prisa. Mas pequeno a proposito, no compite con el numero."""
    d = ImageDraw.Draw(img)
    d.rectangle([x0, 0, x0 + ancho, ALTO], fill=MORADO)
    cx = x0 + ancho / 2

    f_lbl = fuente("Montserrat-Bold.ttf", int(9.5 * ESCALA))
    texto_espaciado(d, (cx, ALTO * 0.30), "SOLO HASTA EL", f_lbl, LILA, tracking=1.6 * ESCALA)

    f_val = fuente("Montserrat-ExtraBold.ttf", int(15 * ESCALA))
    d.text((cx, ALTO * 0.66), fecha, font=f_val, fill=BLANCO, anchor="mm")


def brillo(img, avance, x0, ancho):
    """
    Shimmer: banda de luz diagonal que cruza la celda. Se compone en una capa aparte con mascara
    para que el borde quede suave; una banda de canto duro parece un fallo de render, no un brillo.
    """
    capa = Image.new("RGBA", (ANCHO, ALTO), (255, 255, 255, 0))
    d = ImageDraw.Draw(capa)
    ancho_banda = 34 * ESCALA
    x = x0 - ancho_banda * 2 + avance * (ancho + ancho_banda * 4)
    inclinacion = 16 * ESCALA
    # Tres franjas concentricas: la del medio mas opaca. Barato y convincente.
    for desp, alfa in ((0, 62), (ancho_banda * 0.45, 30), (-ancho_banda * 0.45, 30)):
        d.polygon(
            [
                (x + desp, ALTO), (x + desp + inclinacion, 0),
                (x + desp + inclinacion + ancho_banda * 0.5, 0),
                (x + desp + ancho_banda * 0.5, ALTO),
            ],
            fill=(255, 255, 255, alfa),
        )
    recorte = Image.new("L", (ANCHO, ALTO), 0)
    ImageDraw.Draw(recorte).rectangle([x0, 0, x0 + ancho, ALTO], fill=255)
    capa.putalpha(Image.composite(capa.split()[3], Image.new("L", capa.size, 0), recorte))
    return Image.alpha_composite(img.convert("RGBA"), capa).convert("RGB")


def curva_pop(t):
    """
    Anticipation + overshoot. Primer tramo: se encoge (la toma de impulso). Resto: sale disparado,
    rebasa y se asienta. Sin el encogimiento previo el salto no se siente, solo se ve.
    """
    if t < 0.28:
        return 1.0 - 0.07 * (t / 0.28)
    u = (t - 0.28) / 0.72
    if u >= 1:
        return 1.0
    return 1.0 + 0.20 * (1 - u) * (1 - u) * (2.2 - u)


def construir(descuento, fecha, salida):
    hay_dto, hay_fecha = bool(descuento), bool(fecha)
    if not (hay_dto or hay_fecha):
        sys.exit("Hace falta al menos --descuento o --hasta")

    if hay_dto and hay_fecha:
        ancho_dto = int(ANCHO * 0.52)
        cajas = [("dto", 0, ancho_dto), ("fecha", ancho_dto, ANCHO - ancho_dto)]
    elif hay_dto:
        cajas = [("dto", 0, ANCHO)]
    else:
        cajas = [("fecha", 0, ANCHO)]

    caja_dto = next((c for c in cajas if c[0] == "dto"), None)

    def pinta(escala_num=1.0, avance_brillo=None):
        img = Image.new("RGB", (ANCHO, ALTO), NARANJA)
        for tipo, x0, w in cajas:
            if tipo == "dto":
                celda_descuento(img, descuento, x0, w, escala_num)
            else:
                celda_fecha(img, fecha, x0, w)
        if avance_brillo is not None and caja_dto:
            img = brillo(img, avance_brillo, caja_dto[1], caja_dto[2])
        return img

    fotogramas = [pinta()]                                   # fotograma 0: estado final (Outlook)

    n = max(int(DUR_SHIMMER * FPS), 1)
    for i in range(n):
        fotogramas.append(pinta(avance_brillo=(i + 1) / n))

    if caja_dto:                                             # el pop solo tiene sentido en el numero
        n = max(int(DUR_POP * FPS), 1)
        for i in range(n):
            fotogramas.append(pinta(escala_num=curva_pop((i + 1) / n)))

    fotogramas.append(pinta())
    descanso = max(int(DUR_DESCANSO * FPS), 1)

    tmp = tempfile.mkdtemp(prefix="etq-")
    try:
        for i, f in enumerate(fotogramas):
            f.save(os.path.join(tmp, "f%04d.png" % i))
        ultimo = len(fotogramas) - 1
        for k in range(descanso):                            # el descanso, repitiendo el reposo
            fotogramas[-1].save(os.path.join(tmp, "f%04d.png" % (ultimo + 1 + k)))

        paleta = os.path.join(tmp, "paleta.png")
        entrada = os.path.join(tmp, "f%04d.png")
        # stats_mode=diff concentra la paleta en lo que cambia entre fotogramas, que aqui es el
        # brillo y el numero; diff_mode=rectangle solo reescribe el rectangulo que cambia. Las dos
        # cosas juntas son lo que mantiene el fichero pequeno.
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", entrada,
             "-vf", "palettegen=max_colors=64:stats_mode=diff", paleta], check=True)
        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", entrada,
             "-i", paleta, "-lavfi",
             "paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
             "-loop", "0", salida], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    kb = os.path.getsize(salida) / 1024.0
    print("%s  %dx%d (logico %dx%d)  %d fotogramas  %.1f KB"
          % (salida, ANCHO, ALTO, ANCHO // ESCALA, ALTO // ESCALA,
             len(fotogramas) + descanso, kb))
    if kb > 180:
        print("  AVISO: pesa mas de 180 KB. Bajar FPS o acortar el descanso.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Etiqueta promocional animada para correo")
    p.add_argument("--descuento", default="", help='Lo que se ve grande: "15%%", "2x1"')
    p.add_argument("--hasta", default="", help='Fecha limite: "31/10/2026"')
    p.add_argument("--salida", required=True, help="Fichero .gif de salida")
    a = p.parse_args()
    construir(a.descuento.strip(), a.hasta.strip(), a.salida)
