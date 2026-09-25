# -*- coding: utf-8 -*-
"""
El logo sobre el morado de la marca, sin el recuadro negro.

Los logos del correo van en PNG **sobre fondo plano**, no transparentes: Outlook no compone
transparencias con fiabilidad. Por eso hay dos, uno aplanado sobre blanco y otro sobre el casi
negro del tema oscuro, y cada uno desaparece contra el panel de su tema.

Al añadir el tema de la marca —el morado `#33103F`— apareció el problema: el logo del tema oscuro
lleva pintado su propio fondo `#16141D`, así que sobre morado se ve un recuadro negro alrededor.
Arriba y en la firma.

Un reemplazo de color a lo bruto no vale: 17 174 píxeles del logo son de borde suavizado, mezclados
contra el fondo viejo, y quedarían con halo. Pero no hace falta inventar nada — el mismo dibujo
está aplanado sobre DOS fondos conocidos, y con eso el original se despeja:

    claro  = A·F + (1−A)·W
    oscuro = A·F + (1−A)·D        restando:  claro − oscuro = (1−A)·(W − D)

De ahí salen la opacidad y el color de cada píxel, exactos. Comprobado: recomponer sobre blanco
devuelve el fichero claro con **error 0**.

Se corre a mano cuando cambie el logo o el color del panel:

    .venv/Scripts/python.exe prototipos/mail/logo_centauro.py
"""

import os

from PIL import Image

AQUI = os.path.dirname(os.path.abspath(__file__))
# Se lee y se escribe en `app/static/email/`, que es la carpeta VERSIONADA: `prototipos/mail/img/`
# está en .gitignore, así que desde un clon limpio este script no encontraría de dónde partir.
# Si existe la del prototipo, se escribe también ahí para que las dos no se separen.
SERVIDO = os.path.join(AQUI, '..', '..', 'app', 'static', 'email')
IMG = os.path.join(AQUI, 'img')
DESTINOS = [SERVIDO] + ([IMG] if os.path.isdir(IMG) else [])

# Los fondos sobre los que están aplanados los dos ficheros de partida.
FONDO_CLARO = (255, 255, 255)
FONDO_OSCURO = (22, 20, 29)

# El panel del tema de la marca, tal como lo define `paleta('centauro')` en render.js. Si allí
# cambia, aquí también: son el mismo color por definición, y un desajuste vuelve a dibujar el
# recuadro.
PANEL_CENTAURO = (0x33, 0x10, 0x3F)

# Solo el 2x: es el unico que pide el motor (se muestra a la mitad para que no se vea blando en
# pantallas densas). Generar tambien el 1x seria dejar un fichero que nadie abre.
PAREJAS = [
    ('logo_h_light_2x.png', 'logo_h_dark_2x.png', 'logo_h_centauro_2x.png'),
]


def despeja(claro, oscuro):
    """
    Devuelve (transparencia, color premultiplicado) por píxel a partir de las dos versiones.

    Se usa el canal donde más se separan los dos fondos: es el que menos redondeo arrastra.
    """
    canal = max(range(3), key=lambda i: abs(FONDO_CLARO[i] - FONDO_OSCURO[i]))
    den = float(FONDO_CLARO[canal] - FONDO_OSCURO[canal])
    fuera = []
    for ca, cb in zip(claro.getdata(), oscuro.getdata()):
        transparencia = min(1.0, max(0.0, (ca[canal] - cb[canal]) / den))
        # A·F: el color ya multiplicado por su opacidad, que es lo que hace falta para recomponer.
        af = tuple(ca[i] - transparencia * FONDO_CLARO[i] for i in range(3))
        fuera.append((transparencia, af))
    return fuera


def recompone(piezas, fondo, tamano):
    im = Image.new('RGB', tamano)
    im.putdata([tuple(min(255, max(0, int(round(af[i] + t * fondo[i])))) for i in range(3))
                for t, af in piezas])
    return im


def main():
    for nombre_claro, nombre_oscuro, salida in PAREJAS:
        claro = Image.open(os.path.join(SERVIDO, nombre_claro)).convert('RGB')
        oscuro = Image.open(os.path.join(SERVIDO, nombre_oscuro)).convert('RGB')
        if claro.size != oscuro.size:
            raise SystemExit('%s y %s no miden lo mismo' % (nombre_claro, nombre_oscuro))

        piezas = despeja(claro, oscuro)

        # La comprobación va ANTES de escribir: si recomponer sobre blanco no devuelve el fichero
        # de partida, el despeje está mal y lo que se escriba tendrá halos que nadie va a mirar.
        prueba = recompone(piezas, FONDO_CLARO, claro.size)
        if list(prueba.getdata()) != list(claro.getdata()):
            raise SystemExit('el despeje no reproduce %s: no se escribe nada' % nombre_claro)

        nuevo = recompone(piezas, PANEL_CENTAURO, claro.size)
        for carpeta in DESTINOS:
            nuevo.save(os.path.join(carpeta, salida), optimize=True)
        bordes = sum(1 for t, _ in piezas if 0.01 < t < 0.99)
        print('OK %-26s %dx%d · %d pixeles de borde recompuestos'
              % (salida, nuevo.width, nuevo.height, bordes))


if __name__ == '__main__':
    main()
