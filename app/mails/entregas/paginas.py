"""
Del PDF que exporta Canva a las imágenes que van en el correo.

Por qué pypdfium2 y no PyMuPDF: PyMuPDF es AGPL y este repositorio es público sin esa licencia
(constitución, principio V). pypdfium2 es BSD-3/Apache-2.0, va igual de rápido —medido: 0,44 s
para las seis páginas de un deck real— y además **lee el texto** de cada página, que es lo que
permite dos cosas que importan: ponerle nombre a la miniatura y avisar de que lleva un precio.

## El límite del aviso de precios, dicho sin rodeos

`parece_precio()` lee TEXTO. Un precio que en la presentación es parte de una imagen —y en el
deck de pantallas hay uno así— **no se detecta**. Esto no es un defecto que se pueda arreglar
leyendo mejor: haría falta reconocimiento óptico, y aun así fallaría. La red que cubre este hueco
es humana: quien entrega mira las miniaturas antes de mandarlas, y la interfaz se lo dice con
todas las letras (constitución, principio IV).

## Qué se acepta

Se valida por los primeros bytes del fichero, no por su extensión: la extensión la escribe quien
sube, y quien sube puede equivocarse o mentir.
"""

import io
import re
from typing import List, Optional

MEGA = 1024 * 1024
LIMITE_BYTES = 25 * MEGA
LIMITE_PAGINAS = 20
# Ancho al que se rasteriza cada página. 1200 px da margen para el carrusel de 600 px en
# pantallas densas y para la portada de WhatsApp, que es 1200 × 630.
ANCHO_PAGINA = 1200

_FIRMAS = (
    (b"%PDF-", "pdf"),
    (b"\xff\xd8\xff", "imagen"),          # JPEG
    (b"\x89PNG\r\n\x1a\n", "imagen"),     # PNG
    (b"GIF87a", "imagen"),
    (b"GIF89a", "imagen"),
)

# Un precio es una cifra **junto a** una marca de moneda, o una palabra que anuncia precio. Las
# medidas y los datos de tráfico del catálogo son cifras sin moneda —"1024 × 2048 px",
# "7,68 x 4,80 m", "+95.000 vehículos/día"— y no deben disparar el aviso: un aviso que salta
# siempre es un aviso que nadie lee.
_PATRONES_PRECIO = (
    re.compile(r"(?:US\$|\$|€|USD|BS\.?|BsS?)\s*\d", re.IGNORECASE),
    re.compile(r"\d[\d.,]*\s*(?:US\$|\$|€|USD|BS\.?|BsS?)\b", re.IGNORECASE),
    re.compile(r"\b(?:precio|tarifa|costo|inversi[oó]n|desde)\b[^\n]{0,40}\d", re.IGNORECASE),
)


class FicheroNoValido(ValueError):
    """Lo que subieron no se puede usar, con un mensaje que explica el límite."""


class Pagina:
    """Una página rasterizada, con lo que se leyó de ella."""

    def __init__(self, numero: Optional[int], imagen, texto: str = "", origen: str = "pdf"):
        self.numero = numero              # 1 para la primera página del PDF; None si es suelta
        self.imagen = imagen              # PIL.Image
        self.texto = texto or ""
        self.origen = origen              # pdf | imagen | claude
        self.rotulo = rotulo_de(self.texto)
        self.aviso_precio = parece_precio(self.texto)

    @property
    def ancho(self) -> int:
        return self.imagen.width

    @property
    def alto(self) -> int:
        return self.imagen.height

    def __repr__(self):
        return "<Pagina %s %dx%d%s>" % (
            self.numero, self.ancho, self.alto, " precio" if self.aviso_precio else "")


def tipo_de(datos: bytes) -> Optional[str]:
    """`'pdf'`, `'imagen'` o `None`, según los primeros bytes."""
    for firma, tipo in _FIRMAS:
        if datos.startswith(firma):
            return tipo
    return None


def valida(datos: bytes) -> str:
    """Comprueba tamaño y tipo. Devuelve el tipo, o levanta `FicheroNoValido` explicando por qué."""
    if not datos:
        raise FicheroNoValido("El fichero llegó vacío.")
    if len(datos) > LIMITE_BYTES:
        raise FicheroNoValido(
            "El fichero pesa %.1f MB y el límite son %d MB. En Canva, al descargar el PDF, "
            "elige «PDF estándar» en vez de «PDF para imprimir»."
            % (len(datos) / MEGA, LIMITE_BYTES // MEGA))
    tipo = tipo_de(datos)
    if tipo is None:
        raise FicheroNoValido(
            "Solo se aceptan PDF e imágenes (JPG, PNG o GIF). Si lo que tienes es un enlace de "
            "Canva, usa «Pedírselo a Claude».")
    return tipo


def parece_precio(texto: str) -> bool:
    """
    Verdadero si el texto contiene algo que parece un precio.

    Recuerda el límite: solo ve texto. Un precio incrustado en una imagen pasa sin avisar.
    """
    t = texto or ""
    return any(p.search(t) for p in _PATRONES_PRECIO)


def rotulo_de(texto: str) -> str:
    """
    Un nombre corto para la miniatura, sacado del texto de la página.

    Se queda con la primera línea que parezca un titular: ni una palabra suelta ni un párrafo. Si
    no hay ninguna, devuelve cadena vacía y la interfaz enseña «Página N», que es honesto.
    """
    for linea in (texto or "").splitlines():
        limpia = " ".join(linea.split())
        if 4 <= len(limpia) <= 120:
            return limpia[:200]
    return ""


def _texto_de(pagina) -> str:
    """El texto de una página de pypdfium2, o vacío si no se pudo leer."""
    try:
        tp = pagina.get_textpage()
        try:
            return tp.get_text_range() or ""
        finally:
            tp.close()
    except Exception:
        # Una página sin capa de texto —toda imagen— es un caso normal, no un error: significa
        # que no habrá rótulo ni aviso de precio para ella, y eso ya está dicho arriba.
        return ""


def paginas_de_pdf(datos: bytes, ancho: int = ANCHO_PAGINA) -> List[Pagina]:
    """Rasteriza el PDF entero, una `Pagina` por página, en orden."""
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(datos)
    try:
        total = len(pdf)
        if total == 0:
            raise FicheroNoValido("El PDF no tiene páginas.")
        if total > LIMITE_PAGINAS:
            raise FicheroNoValido(
                "El PDF tiene %d páginas y el límite son %d. Exporta desde Canva solo las "
                "páginas que vayas a usar." % (total, LIMITE_PAGINAS))

        salida = []
        for i in range(total):
            pagina = pdf[i]
            # El ancho de una página va en puntos (1/72"); la escala es cuántos píxeles queremos
            # por punto para llegar al ancho pedido.
            puntos = pagina.get_width() or 1
            escala = float(ancho) / float(puntos)
            mapa = pagina.render(scale=escala)
            imagen = mapa.to_pil().convert("RGB")
            salida.append(Pagina(numero=i + 1, imagen=imagen, texto=_texto_de(pagina),
                                 origen="pdf"))
        return salida
    finally:
        pdf.close()


def pagina_de_imagen(datos: bytes, ancho: int = ANCHO_PAGINA, origen: str = "imagen") -> Pagina:
    """
    Una imagen suelta como página. Para quien no tiene el PDF, o para lo que exportó Claude.

    No se lee texto: una imagen no lo tiene. Eso significa que **no habrá aviso de precio**, y es
    otra razón para mirar las miniaturas antes de entregar.
    """
    from PIL import Image

    imagen = Image.open(io.BytesIO(datos)).convert("RGB")
    if imagen.width > ancho:
        alto = max(1, round(imagen.height * ancho / imagen.width))
        imagen = imagen.resize((ancho, alto), Image.LANCZOS)
    return Pagina(numero=None, imagen=imagen, texto="", origen=origen)


def lee(datos: bytes, origen: str = "imagen") -> List[Pagina]:
    """Valida lo que subieron y devuelve sus páginas, venga de un PDF o de una imagen."""
    tipo = valida(datos)
    if tipo == "pdf":
        return paginas_de_pdf(datos)
    return [pagina_de_imagen(datos, origen=origen)]
