#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generador de carruseles animados por servicio, con efecto elegible.

Por que GIF: el correo no ejecuta JavaScript y las animaciones CSS no llegan a Gmail ni
a Outlook. El GIF es lo unico que se mueve en todos los clientes.

REGLA QUE MANDA (constitucion del proyecto, principio III):
    el fotograma 0 es lo que ve Outlook.
Outlook muestra el primer fotograma y descarta el resto. Asi que el fotograma 0 es
SIEMPRE la primera foto completa y quieta, nunca un estado intermedio de la transicion.
Quien no vea la animacion ve una foto acabada.

SIETE EFECTOS (el encargo pedia no menos de seis):

  corte      Cambio seco, sin transicion. El mas ligero de todos y el que mejor
             aguanta en conexiones lentas. Util cuando las fotos ya son fuertes.
  fundido    Una foto se disuelve en la siguiente. El mas neutro; no compite con
             el contenido.
  barrido    Una linea vertical descubre la foto siguiente. Recuerda al cambio de
             cara de una valla rotativa, que es literalmente el medio.
  deslizar   La foto nueva empuja a la anterior. Sensacion de recorrido, como pasar
             por delante de varios soportes.
  zoom       Acercamiento lento sobre cada foto. Da vida a imagenes quietas, pero
             PESA: cada fotograma cambia entero y la compresion no puede reutilizar
             nada.
  destello   Un brillo diagonal cruza la foto antes de cambiar. Lee como metalico,
             va bien con las promociones.
  persiana   La foto siguiente aparece en franjas horizontales. El mas llamativo.

Uso:
    python carrusel_gif.py --servicio led --efecto barrido
    python carrusel_gif.py --servicio totem --efecto zoom --imagenes svc_totem.jpg svc_totem_alt.jpg
    python carrusel_gif.py --todos --efecto fundido
    python carrusel_gif.py --listar

El fichero de salida se llama carousel_<servicio>_<efecto>.gif, que es exactamente el
nombre que el motor de plantillas pide cuando se elige ese efecto.
"""

import argparse
import glob
import io
import os
import shutil
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw

AQUI = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(AQUI, 'img')

ANCHO, ALTO = 600, 400          # 3:2, la proporcion de todas las fotos del inventario
FPS = 15                        # por debajo de 12 la transicion se percibe a saltos
HOLD = 2.0                      # quieto en cada foto
TRANS = 0.85                    # duracion de la transicion

EFECTOS = ['corte', 'fundido', 'barrido', 'deslizar', 'zoom', 'destello', 'persiana']

# Ajuste por efecto, medido y no adivinado.
#
# El GIF comprime reutilizando lo que NO cambia entre fotogramas. Los efectos que mueven
# solo una parte de la imagen -barrido, persiana- dejan quieto el resto y pesan poco. Los
# que cambian todos los pixeles a la vez -fundido, deslizar, zoom, destello- no pueden
# reutilizar nada.
#
# Lo medido, con 3 fotos de 600x400: CADA fotograma de transicion cuesta unos 70 KB, y la
# relacion es lineal. 18 fotogramas de transicion = 1267 KB; 9 = 667 KB; 3 = 231 KB. Por
# eso los efectos de pantalla completa se quedan en 0,20 s (3 fotogramas por transicion):
# 200 ms es una duracion de transicion perfectamente normal y es lo que los deja por
# debajo del aviso.
#
# Lo que NO funciono: pense que los dos segundos de reposo, al ser 30 fotogramas
# identicos, pesaban. Al pasarlos a un solo fotograma con retardo largo el fichero bajo
# 2 KB de 1269. El GIF ya los colapsaba solo. El reposo con retardo se ha mantenido
# igualmente porque deja el fichero en 21 fotogramas en vez de 108, pero no es un ahorro.
#
# El zoom es la excepcion que no tiene arreglo: el acercamiento cambia la imagen entera
# en cada paso, asi que no hay ajuste que lo baje al rango de los demas. Se ofrece con su
# peso real a la vista. El zoom que se pidio para las ETIQUETAS es otra cosa y sí es
# ligero: esa animacion vive en etiqueta_gif.py y pesa 25 KB.
AJUSTE = {
    'corte':    {'trans': 0.00, 'col': 128, 'peso': 'muy ligero'},
    'barrido':  {'trans': 0.85, 'col': 128, 'peso': 'ligero'},
    'persiana': {'trans': 0.85, 'col': 128, 'peso': 'ligero'},
    'fundido':  {'trans': 0.20, 'col':  64, 'peso': 'medio'},
    'destello': {'trans': 0.20, 'col':  64, 'peso': 'medio'},
    'deslizar': {'trans': 0.20, 'col':  64, 'peso': 'medio'},
    'zoom':     {'trans': 0.20, 'col':  48, 'peso': 'pesado'},
}
SERVICIOS = ['led', 'mercedes', 'vallas', 'totem', 'rider']

# Peso maximo razonable. Gmail corta el HTML a 102 KB, pero las imagenes van aparte;
# aun asi, un carrusel de mas de 700 KB castiga a quien abre el correo con datos moviles.
AVISO_KB = 700


def fotos_de(servicio, explicitas=None):
    """Las fotos de un servicio, en orden. Sin 'hero' ni 'vid', que son de otro uso."""
    if explicitas:
        return [f if os.path.isabs(f) else os.path.join(IMG, f) for f in explicitas]
    todas = sorted(glob.glob(os.path.join(IMG, 'svc_%s*.jpg' % servicio)))
    return [f for f in todas if '_hero' not in f and '_vid' not in f]


def encuadra(ruta):
    """Recorta al centro y escala. Todas las fotos deben salir del mismo tamano."""
    im = Image.open(ruta).convert('RGB')
    objetivo = ANCHO / float(ALTO)
    w, h = im.size
    if w / float(h) > objetivo:
        nuevo = int(h * objetivo)
        im = im.crop(((w - nuevo) // 2, 0, (w + nuevo) // 2, h))
    else:
        nuevo = int(w / objetivo)
        im = im.crop((0, (h - nuevo) // 2, w, (h + nuevo) // 2))
    return im.resize((ANCHO, ALTO), Image.LANCZOS)


def suave(t):
    """Aceleracion y frenada. Una transicion lineal se nota mecanica."""
    return t * t * (3 - 2 * t)


# -- Los efectos --------------------------------------------------------------------

def _fundido(a, b, t):
    return Image.blend(a, b, suave(t))


def _barrido(a, b, t):
    """Linea vertical que descubre la foto nueva, con un filo claro que la acompana."""
    out = a.copy()
    x = int(ANCHO * suave(t))
    if x > 0:
        out.paste(b.crop((0, 0, x, ALTO)), (0, 0))
    if 3 < x < ANCHO:
        filo = Image.new('RGB', (3, ALTO), (255, 255, 255))
        out.paste(Image.blend(out.crop((x - 3, 0, x, ALTO)), filo, 0.55), (x - 3, 0))
    return out


def _deslizar(a, b, t):
    """La nueva empuja a la anterior. Sensacion de recorrido."""
    out = Image.new('RGB', (ANCHO, ALTO))
    d = int(ANCHO * suave(t))
    out.paste(a, (-d, 0))
    out.paste(b, (ANCHO - d, 0))
    return out


def _persiana(a, b, t):
    """Franjas horizontales que se abren a la vez. El mas llamativo de los siete."""
    out = a.copy()
    franjas = 9
    alto_f = ALTO // franjas + 1
    visible = int(alto_f * suave(t))
    if visible <= 0:
        return out
    for i in range(franjas):
        y = i * alto_f
        fin = min(y + visible, ALTO)
        if fin > y:
            out.paste(b.crop((0, y, ANCHO, fin)), (0, y))
    return out


def _destello(a, b, t):
    """Brillo diagonal que cruza y, al pasar, deja la foto nueva detras."""
    base = _fundido(a, b, t)
    capa = Image.new('RGBA', (ANCHO, ALTO), (255, 255, 255, 0))
    d = ImageDraw.Draw(capa)
    banda, inclin = 130, 70
    x = -banda * 2 + t * (ANCHO + banda * 4)
    for desp, alfa in ((0, 78), (banda * 0.5, 34), (-banda * 0.5, 34)):
        d.polygon([(x + desp, ALTO), (x + desp + inclin, 0),
                   (x + desp + inclin + banda * 0.45, 0),
                   (x + desp + banda * 0.45, ALTO)],
                  fill=(255, 255, 255, alfa))
    return Image.alpha_composite(base.convert('RGBA'), capa).convert('RGB')


TRANSICIONES = {
    'fundido': _fundido, 'barrido': _barrido, 'deslizar': _deslizar,
    'persiana': _persiana, 'destello': _destello,
}


def _zoom_frames(im, n, desde=1.0, hasta=1.10):
    """Acercamiento lento sobre una foto quieta."""
    salida = []
    for i in range(n):
        f = desde + (hasta - desde) * suave(i / float(max(n - 1, 1)))
        w, h = int(ANCHO / f), int(ALTO / f)
        x, y = (ANCHO - w) // 2, (ALTO - h) // 2
        salida.append(im.crop((x, y, x + w, y + h)).resize((ANCHO, ALTO), Image.LANCZOS))
    return salida


def construir(servicio, efecto, imagenes=None, salida=None, fps=FPS):
    if efecto not in EFECTOS:
        sys.exit('Efecto desconocido: %s\nDisponibles: %s' % (efecto, ', '.join(EFECTOS)))

    rutas = fotos_de(servicio, imagenes)
    if not rutas:
        sys.exit('Sin fotos para el servicio "%s" en %s' % (servicio, IMG))
    faltan = [r for r in rutas if not os.path.exists(r)]
    if faltan:
        sys.exit('No existen: %s' % ', '.join(faltan))

    salida = salida or os.path.join(IMG, 'carousel_%s_%s.gif' % (servicio, efecto))
    aj = AJUSTE[efecto]
    fotos = [encuadra(r) for r in rutas]
    if len(fotos) == 1:
        fotos = fotos * 2       # con una sola foto no hay carrusel, pero no falla

    paso = 1.0 / fps                # lo que dura un fotograma de transicion
    n_trans = max(int(aj['trans'] * fps), 1)

    # Secuencia de pares (imagen, segundos). Un reposo de dos segundos es UN fotograma
    # con dos segundos de retardo, no treinta copias identicas: el GIF lo permite y el
    # ojo no distingue la diferencia. Es la unica optimizacion de este fichero que no
    # cuesta nada de calidad.
    seq = []

    for i, foto in enumerate(fotos):
        siguiente = fotos[(i + 1) % len(fotos)]
        if efecto == 'zoom':
            # Quieta, empujon breve, y a la siguiente.
            #
            # El primer intento hacia zoom continuo durante todo el reposo y daba 5,5 MB:
            # con la camara siempre en marcha NINGUN fotograma se repite y el GIF no puede
            # reutilizar nada. Ademas, visto en bucle, un zoom que nunca para marea.
            empujon = _zoom_frames(foto, 8, 1.0, 1.07)
            seq.append((foto, HOLD * 0.6))
            seq.extend((f, paso) for f in empujon)
            seq.extend((_fundido(empujon[-1], siguiente, j / float(n_trans)), paso)
                       for j in range(1, n_trans + 1))
        else:
            seq.append((foto, HOLD))
            if efecto != 'corte':
                fn = TRANSICIONES[efecto]
                seq.extend((fn(foto, siguiente, j / float(n_trans)), paso)
                           for j in range(1, n_trans + 1))

    # El fotograma 0 tiene que ser la primera foto limpia: es lo unico que ve Outlook.
    seq[0] = (fotos[0], seq[0][1])

    tmp = tempfile.mkdtemp(prefix='carr-')
    try:
        # El demuxer concat es lo que deja dar un retardo distinto a cada fotograma.
        # Con -framerate fijo no habria manera: todos durarian lo mismo.
        lista = os.path.join(tmp, 'lista.txt')
        with io.open(lista, 'w', encoding='utf-8', newline='\n') as fh:
            for i, (f, seg) in enumerate(seq):
                ruta = os.path.join(tmp, 'f%04d.png' % i)
                f.save(ruta)
                fh.write(u"file '%s'\nduration %.4f\n"
                         % (os.path.basename(ruta), seg))
            # concat ignora la duracion del ultimo: se repite para que se respete.
            fh.write(u"file '%s'\n" % os.path.basename(ruta))

        paleta = os.path.join(tmp, 'paleta.png')
        entrada = ['-f', 'concat', '-safe', '0', '-i', lista]
        # stats_mode=diff concentra la paleta en lo que cambia entre fotogramas;
        # diff_mode=rectangle solo reescribe el rectangulo que se mueve. Las dos juntas
        # son lo que mantiene el fichero manejable.
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error'] + entrada +
                       ['-vf', 'palettegen=max_colors=%d:stats_mode=diff' % aj['col'],
                        paleta], check=True)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error'] + entrada +
                       ['-i', paleta, '-lavfi',
                        'paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle',
                        '-fps_mode', 'vfr', '-loop', '0', salida], check=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    kb = os.path.getsize(salida) / 1024.0
    print('%-40s %d fotos  %3d fotogramas  %6.1f KB%s'
          % (os.path.basename(salida), len(rutas), len(seq), kb,
             '   <-- PESA MUCHO' if kb > AVISO_KB else ''))
    return kb


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description='Carrusel animado por servicio, con efecto elegible')
    ap.add_argument('--servicio', help=', '.join(SERVICIOS))
    ap.add_argument('--efecto', default='fundido', help='uno de: ' + ', '.join(EFECTOS))
    ap.add_argument('--imagenes', nargs='*', help='fotos concretas; por defecto, todas las del servicio')
    ap.add_argument('--salida', help='fichero .gif; por defecto img/carousel_<servicio>_<efecto>.gif')
    ap.add_argument('--todos', action='store_true', help='los cinco servicios con el mismo efecto')
    ap.add_argument('--listar', action='store_true', help='efectos y fotos disponibles')
    a = ap.parse_args()

    if a.listar:
        print('Efectos (%d):' % len(EFECTOS))
        for e in EFECTOS:
            print('   ' + e)
        print('\nFotos por servicio:')
        for sv in SERVICIOS:
            fs = [os.path.basename(x) for x in fotos_de(sv)]
            print('  %-9s %d  %s' % (sv, len(fs), ', '.join(fs)))
        sys.exit(0)

    servicios = SERVICIOS if a.todos else [a.servicio]
    if not servicios[0]:
        ap.error('Hace falta --servicio o --todos')

    total = 0
    for sv in servicios:
        total += construir(sv, a.efecto, a.imagenes, a.salida)
    if len(servicios) > 1:
        print('%-40s %40.1f KB' % ('TOTAL', total))
