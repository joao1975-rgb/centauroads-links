"""
La guía personalizada (plantilla I) en el motor del correo (especificación 012, T1203 y T1206).

- Sin guía guardada, la I es la F: sus textos y sus tres productos (Tótem, LED, Rider).
- Con guía: solo las fases encendidas, en su orden y numeradas por su sitio; cada una con su producto,
  su presentación propia en la entrega si la tiene (carrusel y enlace) y, sin detalle, la ubicación.
- Texto plano y WhatsApp siguen a las fases; cada bloque de WhatsApp lleva el título de su fase.
- La F de catálogo no cambia (la guardia byte a byte de build.js lo cubre).
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

MOTOR = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "render.js"
ENLACE = "https://mails.centauroads.com/p/eguia123"
CARRUSEL = "https://mails.centauroads.com/media/e/x/espacios/vallas/carrusel.gif?v=1"

GUION = r"""
const M = require(process.argv[2]);
const ENLACE = process.argv[3], CARRUSEL = process.argv[4];
const fase = (clave, linea, extra) => Object.assign({ clave, on: true, fase: 'Epígrafe ' + clave,
  titulo: 'Título *' + clave + '*', texto: 'Texto de ' + clave + ' para {empresa}', etiqueta: 'Etiqueta ' + clave,
  detalle: 'Detalle ' + clave, linea }, extra || {});
const base = guia => {
  const st = M.defaultState(); st.plantilla = 'I'; st.perfil = 'general';
  Object.assign(st.bloques.entrega, { enlace: ENLACE, titulo: 'Tu *guía* para crecer', empresa: 'ACME (prueba)',
    meta: 'GUÍA PARA EMPEZAR', espacios: { vallas: { carrusel: CARRUSEL } } });
  if (guia) st.bloques.entrega.guia = guia;
  return st;
};
const GUIA = { entrada: 'Entrada propia', saludo: 'Hola {destinatario},', parrafo: 'Párrafo propio',
  caja_titulo: 'Caja propia', caja_texto: 'Texto de caja', cta_texto: 'Llamado propio', boton: 'Botón propio',
  fases: [fase('recuerden', 'vallas', { detalle: '' }), fase('conozcan', 'totem'), fase('compren', 'rider', { on: false })] };
const out = { nombres: {}, cobertura: {} };
M.defaultState().servicios.forEach(s => { out.nombres[s.id] = s.nombre; out.cobertura[s.id] = s.cobertura; });
const sinGuia = base();
out.defecto = { html: M.render(sinGuia), lineas: M.lineasDeGuia(sinGuia), fases: M.guiaDe(sinGuia).fases };
out.guiaF = M.defaultState().bloques.guia;
const st = base(GUIA), antes = JSON.stringify(st);
out.html = M.render(st);
out.texto = M.renderText(st);
out.wa = M.renderWhatsApp(st);
out.bloques = M.bloquesWhatsApp(st);
out.lineas = M.lineasDeGuia(st);
out.intacto = JSON.stringify(st) === antes;
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def r(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible")
    guion = tmp_path_factory.mktemp("guia") / "_g.js"
    guion.write_text(GUION, encoding="utf-8")
    p = subprocess.run(["node", str(guion), str(MOTOR), ENLACE, CARRUSEL], capture_output=True,
                       text=True, encoding="utf-8", timeout=120)
    assert p.returncode == 0, "el motor falló:\n" + p.stderr
    return json.loads(p.stdout)


def test_sin_guia_es_la_f_con_sus_tres_productos(r):
    assert r["defecto"]["lineas"] == ["totem", "led", "rider"]
    g = r["guiaF"]
    for n in (1, 2, 3):
        assert g["fase%dTitulo" % n] in r["defecto"]["html"]
    assert [f["clave"] for f in r["defecto"]["fases"]] == ["conozcan", "recuerden", "compren"]


def test_solo_las_fases_encendidas_en_su_orden_y_numeradas_por_su_sitio(r):
    h = r["html"]
    assert r["lineas"] == ["vallas", "totem"]
    assert h.index("Epígrafe recuerden") < h.index("Epígrafe conozcan")
    assert "Epígrafe compren" not in h and r["nombres"]["rider"] not in h
    assert ">01</td>" in h and ">02</td>" in h and ">03</td>" not in h


def test_cada_fase_con_su_producto_su_carrusel_y_sin_detalle_la_ubicacion(r):
    h = r["html"]
    assert r["nombres"]["vallas"] in h and r["nombres"]["totem"] in h
    assert CARRUSEL.replace("&", "&amp;") in h                 # la presentación propia de la entrega
    assert r["cobertura"]["vallas"] in h                       # detalle vacío → su ubicación
    assert "Detalle conozcan" in h


def test_los_textos_de_la_guia_y_sus_huecos(r):
    h = r["html"]
    for t in ("Entrada propia", "Párrafo propio", "Caja propia", "Llamado propio", "Botón propio",
              "Texto de recuerden para ACME (prueba)"):
        assert t in h, t
    assert "<title>Tu guía para crecer</title>" in h            # el asunto, sin los asteriscos


def test_texto_plano_y_whatsapp_siguen_a_las_fases(r):
    t = r["texto"]
    assert "01 · TÍTULO RECUERDEN" in t and "02 · TÍTULO CONOZCAN" in t and "COMPREN" not in t
    assert "Te envío aparte cada fase con su presentación." in r["wa"]
    assert [b["id"] for b in r["bloques"]] == ["vallas", "totem"]
    assert r["bloques"][0]["texto"] == "Título recuerden · %s\n%s/vallas" % (r["nombres"]["vallas"], ENLACE)


def test_no_toca_el_estado(r):
    assert r["intacto"]
