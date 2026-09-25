"""
Lo que la Personalizada hace y las demás plantillas no.

La referencia byte a byte de `test_plantillas_identicas.py` renderiza H con el estado por
defecto, y ahí la empresa está vacía: la cabecera sale igual que siempre y la guardia pasa sin
enterarse de nada. Justo por eso hace falta esto — lo propio de H solo aparece cuando hay un
cliente detrás, que es como se entrega de verdad.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MOTOR = RAIZ / "prototipos" / "mail" / "render.js"

# Renderiza H dos veces —con empresa y sin ella— y una de E, F y G para comprobar que no se
# contagiaron: `cabeceraAsesor` la comparten las cuatro.
GUION = r"""
const M = require(process.argv[2]);

function conEmpresa(empresa) {
  const st = M.defaultState();
  st.plantilla = 'H';
  st.destinatario = 'Elizabeth';
  Object.assign(st.bloques.entrega, {
    titulo: 'Propuesta LED para Valmy',
    empresa: empresa,
    url: 'https://canva.link/ejemplo',
    enlace: 'https://links.centauroads.com/p/abc123',
    img: 'https://links.centauroads.com/media/entregas/1/carrusel.gif',
  });
  return M.render(st, 'H');
}

const salida = { conEmpresa: conEmpresa('Valmy'), sinEmpresa: conEmpresa('') };

// Con el efecto de la Personalizada puesto en `zoom` -que el servidor arma al vuelo pero NO
// existe como GIF pregenerado-, las plantillas A-G no pueden enterarse.
const z = M.defaultState(); z.efectoEntrega = 'zoom'; z.plantilla = 'A';
salida.A_con_zoom_en_entrega = M.render(z, 'A');

// Y el estado guardado antes de que existiera el campo tiene que heredar, no reiniciarse.
const viejo = M.defaultState(); delete viejo.efectoEntrega; viejo.efecto = 'persiana';
salida.migrado = M.normaliza(JSON.parse(JSON.stringify(viejo))).efectoEntrega;
['E', 'F', 'G'].forEach(function (k) {
  const st = M.defaultState(); st.plantilla = k;
  salida[k] = M.render(st, k);
});
// WhatsApp y texto plano: los otros dos canales por los que sale la propuesta. No tenían ni
// una prueba, y el enlace propio se vigilaba SOLO en el HTML.
const w = M.defaultState(); w.plantilla = 'H'; w.destinatario = 'Elizabeth';
Object.assign(w.bloques.entrega, {
  titulo: 'Propuesta LED para Valmy', empresa: 'Valmy',
  url: 'https://canva.link/ejemplo',
  enlace: 'https://links.centauroads.com/p/abc123',
  corto: 'La version corta que va por WhatsApp.',
  texto: 'El texto largo del correo, que aqui no pinta nada.',
});
// Los tres aspectos de la Personalizada, para comprobar que son tres de verdad y que el de la
// marca no se cuela en A-G.
['claro', 'oscuro', 'centauro'].forEach(function (tema) {
  const t = M.defaultState(); t.plantilla = 'H'; t.temaEntrega = tema;
  Object.assign(t.bloques.entrega, { titulo: 'Propuesta', empresa: 'Valmy',
    url: 'https://canva.link/x', enlace: 'https://links.centauroads.com/p/abc123' });
  salida['H_' + tema] = M.render(t, 'H');
});
// El aspecto de la marca puesto, y una plantilla del asesor -E SI responde al tema, al contrario
// que A- renderizada al lado: no puede cambiar de aspecto.
const cat = M.defaultState(); cat.plantilla = 'E'; cat.temaEntrega = 'centauro';
salida.E_con_centauro = M.render(cat, 'E');
const catClaro = M.defaultState(); catClaro.plantilla = 'E';
salida.E_intacta = M.render(catClaro, 'E');

// Renderizar la Personalizada NO puede dejar tocado el estado de quien llama: el compositor
// guarda `st` en localStorage justo despues de pintar la vista previa.
const intacto = M.defaultState();
intacto.plantilla = 'H'; intacto.tema = 'claro'; intacto.temaEntrega = 'centauro';
// Con asunto propio, `aplicaAsunto` devuelve el estado TAL CUAL en vez de una copia: es el
// unico camino por el que el render puede acabar escribiendo sobre lo que le pasaron.
intacto.asunto3 = 'propio';
M.render(intacto, 'H');
salida.temaTrasRenderizar = intacto.tema;

salida.whatsapp = M.renderWhatsApp(w);
salida.texto = M.renderText(w);

process.stdout.write(JSON.stringify(salida));
"""


@pytest.fixture(scope="module")
def html(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible")
    guion = tmp_path_factory.mktemp("h") / "_h.js"
    guion.write_text(GUION, encoding="utf-8")
    # `encoding` explícito: el HTML lleva acentos y comillas tipográficas, y sin decirlo Python
    # descodifica con el códec del sistema —cp1252 en este Windows— y se rompe sin avisar: deja
    # `stdout` en None con `returncode` 0, que parece un acierto.
    salida = subprocess.run(["node", str(guion), str(MOTOR)],
                            capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert salida.returncode == 0, "el motor no pudo renderizar:\n" + salida.stderr
    return json.loads(salida.stdout)


def test_la_empresa_sale_en_la_cabecera(html):
    """
    Quien recibe la propuesta tiene que ver su nombre arriba, junto al rótulo. Sin esto, la
    cabecera de una propuesta a medida es idéntica a la de cualquier otro correo.
    """
    assert "Valmy" in html["conEmpresa"]
    # El rótulo y la empresa van en la MISMA celda de la cabecera, una debajo de la otra. Si la
    # empresa apareciera solo en el cuerpo, esta comprobación no la vería.
    cabecera = html["conEmpresa"].split("A MEDIDA")[1][:300]
    assert "Valmy" in cabecera, "la empresa debería ir bajo el rótulo, no perdida en el cuerpo"


def test_sin_empresa_la_cabecera_no_cambia(html):
    """
    Con el campo vacío no se deja un hueco ni una línea en blanco: simplemente no hay nada. Es lo
    que ve quien todavía no ha elegido contacto.
    """
    assert "padding-top:6px" not in html["sinEmpresa"]


@pytest.mark.parametrize("k", ["E", "F", "G"])
def test_las_demas_no_heredan_la_linea(html, k):
    """
    `cabeceraAsesor` es de las cuatro. El argumento nuevo es opcional justo para que E, F y G
    sigan saliendo byte a byte como su referencia; esto lo dice en voz alta.
    """
    assert "padding-top:6px" not in html[k]


def test_el_enlace_del_correo_es_el_propio_no_el_de_canva(html):
    """
    Lo que se manda registra la apertura; el de Canva es solo el destino al otro lado. Si el
    correo enlazara a Canva, no habría ni estadística ni aviso de interés.
    """
    assert "/p/abc123" in html["conEmpresa"]
    assert "canva.link/ejemplo" not in html["conEmpresa"]


def test_el_efecto_de_la_personalizada_no_rompe_las_demas(html):
    """
    En A-G cada efecto es un GIF **pregenerado** que hay que subir (`carousel_led_zoom.gif` no
    está); en una Personalizada el servidor lo arma al vuelo con las páginas del cliente. Cuando
    compartían campo, elegir `zoom` aquí dejaba las cinco imágenes de A-G rotas en Gmail, sin un
    solo aviso, en el correo siguiente.
    """
    assert "_zoom.gif" not in html["A_con_zoom_en_entrega"], (
        "el efecto de la entrega se coló en las imágenes de A")


def test_el_estado_guardado_hereda_el_efecto(html):
    """
    Principio II: el estado guardado se MIGRA, no se tira. Quien ya tenía `persiana` elegido no
    puede encontrarse el campo nuevo en su valor de fábrica.
    """
    assert html["migrado"] == "persiana"


# --- WhatsApp y texto plano: los otros dos canales -------------------------------------

@pytest.mark.parametrize("canal", ["whatsapp", "texto"])
def test_los_otros_canales_mandan_el_enlace_propio(html, canal):
    """
    El enlace propio se vigilaba solo en el HTML, y WhatsApp es un canal de entrega de primera en
    este proyecto. Mandar el de Canva se salta las tres cosas a la vez: registro de la apertura,
    aviso de interés y tarjeta con la portada.
    """
    assert "/p/abc123" in html[canal]
    assert "canva.link/ejemplo" not in html[canal]


def test_whatsapp_lleva_la_version_corta_y_un_solo_enlace():
    """
    FR-118: por WhatsApp va la versión corta, no el texto del correo. Y un solo enlace: cada
    enlace de más es una tarjeta menos, porque WhatsApp dibuja la del primero y nada más.
    """
    import json as _json
    import shutil as _shutil
    import subprocess as _subprocess
    import tempfile as _tempfile
    from pathlib import Path as _Path
    if _shutil.which("node") is None:
        pytest.skip("node no está disponible")
    guion = _Path(_tempfile.mkdtemp()) / "_w.js"
    guion.write_text(GUION, encoding="utf-8")
    salida = _subprocess.run(["node", str(guion), str(MOTOR)],
                             capture_output=True, text=True, encoding="utf-8", timeout=120)
    wa = _json.loads(salida.stdout)["whatsapp"]
    assert "version corta" in wa
    assert "no pinta nada" not in wa, "por WhatsApp se está mandando el texto largo del correo"
    assert wa.count("https://") == 1, "más de un enlace: WhatsApp solo dibuja la tarjeta del primero"


# --- Los tres aspectos ------------------------------------------------------------------

def test_los_tres_aspectos_son_tres_correos_distintos(html):
    """
    Claro, oscuro y el de la marca. Si dos salieran iguales, el selector prometería una elección
    que no existe.
    """
    tres = {html["H_claro"], html["H_oscuro"], html["H_centauro"]}
    assert len(tres) == 3


def test_el_aspecto_de_la_marca_usa_el_morado_como_superficie(html):
    """
    No es "otro oscuro": el morado ES el fondo, y el naranja manda en lo que hay que pulsar. Se
    comprueba en el botón, que es lo que distingue este tema de los otros dos de un vistazo.
    """
    cuerpo = html["H_centauro"]
    assert "#33103F" in cuerpo, "falta el morado de la superficie"
    assert "background:#F79131" in cuerpo, "el botón debería ser naranja"
    # Y el oscuro sigue con su botón morado: no se contagiaron.
    assert "background:#F79131" not in html["H_oscuro"]


def test_la_firma_sigue_al_tema(html):
    """
    La firma tomaba sus grises de constantes sueltas, así que sobre el morado ponía el gris del
    tema oscuro —otro distinto del que usa el resto del correo—. Ahora sale de la paleta.
    """
    assert "#CBAFD8" in html["H_centauro"], "la firma no usa el apagado del tema"
    assert "#A29EB1" not in html["H_centauro"], "quedó el gris del tema oscuro"


def test_el_aspecto_de_la_marca_no_toca_el_catalogo(html):
    """
    `tema` lo comparte el catálogo, y su panel es un interruptor de DOS posiciones que no sabe
    decir "centauro". Compartir el campo haría que ese interruptor mintiera —apagado, y el correo
    en morado— y que el aspecto elegido para un cliente reapareciera en el siguiente catálogo.

    Se comprueba con E, que sí responde al tema; A lleva el suyo fijo y pasaría sin enterarse.
    """
    assert html["E_con_centauro"] == html["E_intacta"]


def test_renderizar_no_deja_tocado_el_estado(html):
    """
    El compositor guarda `st` en localStorage justo después de pintar la vista previa. Si el
    render estampara el aspecto sobre el estado en vez de sobre una copia, elegir el morado en
    una Personalizada dejaría `tema` en 'centauro' guardado, y el catálogo cambiaría de aspecto
    solo, sin que nadie lo hubiera pedido.
    """
    assert html["temaTrasRenderizar"] == "claro"


def test_la_personalizada_no_lleva_pie(html):
    """
    Había una línea al final —"Cualquier duda, respóndeme a este mismo correo"— que no se podía
    tocar desde ningún sitio: la plantilla pintaba `bloques.entrega.pie` y el panel editaba
    `bloques.pie`, que es otro campo. Un texto fijo que nadie puede cambiar es peor que no estar.

    El pie de A-G explica POR QUÉ recibes el correo, porque es un envío de catálogo. Una propuesta
    que llega con tu nombre y tu empresa en la cabecera no tiene nada que explicar, y la firma ya
    lleva el correo y el teléfono.
    """
    for tema in ("claro", "oscuro", "centauro"):
        cuerpo = html["H_" + tema]
        assert "respóndeme a este mismo correo" not in cuerpo
        assert "solicitaste informaci" not in cuerpo, "se coló el pie del catálogo"
