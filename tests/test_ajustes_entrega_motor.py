"""
Ajustes de la entrega H en el motor (especificación 009, T901).

- El orden de los espacios (`bloques.entrega.orden`) manda en el correo, el texto plano y WhatsApp de
  la H; A–G no lo ven. Lo que no está en el orden va al final, en el orden de siempre.
- El WhatsApp de la H lista los espacios incluidos con su enlace; el de la propuesta sigue primero.
- El cargo: Asesor Comercial, Alianzas Comerciales y Directora; por defecto, Alianzas Comerciales.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

MOTOR = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "render.js"
ENLACE = "https://mails.centauroads.com/p/abc123"

GUION = r"""
const M = require(process.argv[2]);
const base = () => {
  const st = M.defaultState(); st.plantilla = 'H'; st.perfil = 'general';
  st.bloques.entrega.enlace = 'ENLACE';
  st.bloques.entrega.incluidos = ['vallas', 'led', 'totem'];
  st.bloques.entrega.aMedida = [{ id: 'medida--aaaa00000001', nombre: 'PRODUCTO PROPIO', cobertura: '',
    canva: '', carrusel: '' }];
  return st;
};
const ordenado = () => { const st = base();
  st.bloques.entrega.orden = ['medida--aaaa00000001', 'totem', 'no-existe', 'vallas']; return st; };
const out = {};
out.nombres = {}; M.defaultState().servicios.forEach(s => { out.nombres[s.id] = s.nombre; out['canva_' + s.id] = s.canva; });
const st = ordenado(), antes = JSON.stringify(st);
out.h = M.render(st, 'H'); out.texto = M.renderText(st); out.wa = M.renderWhatsApp(st);
out.hSin = M.render(base(), 'H'); out.waSin = M.renderWhatsApp(base());
out.intacto = JSON.stringify(st) === antes;
out.otras = {};
'ABCDEFG'.split('').forEach(k => { const a = ordenado(); a.plantilla = k; const b = base(); b.plantilla = k;
  out.otras[k] = [M.render(a, k), M.render(b, k)]; });
out.espaciosH = M.espaciosDeH(st);
out.imgs = {}; M.defaultState().servicios.forEach(s => { out.imgs[s.id] = s.img; });
const conCarrusel = ordenado(); conCarrusel.bloques.entrega.espacios = { totem: { carrusel: 'https://x.test/totem.gif', nombre: 'TOTEM PROPIO' } };
out.espaciosPropios = M.espaciosDeH(conCarrusel);
out.roles = Object.keys(M.ROLES).map(k => [k, M.ROLES[k]]);
out.cargoDefecto = M.cargoDe(M.defaultState().bloques.firma);
out.cargoAsesor = M.cargoDe(Object.assign({}, M.defaultState().bloques.firma, { rol: 'asesor' }));
process.stdout.write(JSON.stringify(out).split('ENLACE').join(process.argv[3]));
"""


@pytest.fixture(scope="module")
def r(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible")
    guion = tmp_path_factory.mktemp("ajustes") / "_a.js"
    guion.write_text(GUION, encoding="utf-8")
    p = subprocess.run(["node", str(guion), str(MOTOR), ENLACE], capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    assert p.returncode == 0, "el motor falló:\n" + p.stderr
    return json.loads(p.stdout)


def _orden(texto, nombres):
    return sorted(nombres, key=texto.index)


# --- El orden ------------------------------------------------------------------------------------

def test_el_orden_manda_en_el_correo_de_la_h(r):
    n = r["nombres"]
    assert _orden(r["h"], ["PRODUCTO PROPIO", n["totem"], n["vallas"], n["led"]]) == \
        ["PRODUCTO PROPIO", n["totem"], n["vallas"], n["led"]]


def test_sin_orden_sale_el_de_siempre(r):
    n = r["nombres"]
    assert _orden(r["hSin"], [n["vallas"], n["led"], n["totem"], "PRODUCTO PROPIO"]) == \
        [n["vallas"], n["led"], n["totem"], "PRODUCTO PROPIO"]


def test_el_orden_manda_en_el_texto_plano_y_whatsapp(r):
    n = r["nombres"]
    esperado = ["PRODUCTO PROPIO", n["totem"], n["vallas"], n["led"]]
    # WhatsApp ya no lista los espacios (010): van en bloques aparte, que siguen el mismo orden.
    assert _orden(r["texto"], esperado) == esperado


def test_a_g_no_cambian(r):
    for k, (con, sin) in r["otras"].items():
        assert con == sin, k


def test_el_estado_no_se_toca(r):
    assert r["intacto"]


# --- WhatsApp ------------------------------------------------------------------------------------

def test_whatsapp_ya_no_lista_los_espacios(r):
    # La lista de la 009 (FR-906) la deroga la 010: cada espacio va en su propio mensaje.
    for s in ("vallas", "led", "totem"):
        assert r["canva_" + s] not in r["wa"], s


def test_whatsapp_el_enlace_de_la_propuesta_sigue_primero(r):
    assert r["wa"].split("\n")[0] == ENLACE
    assert r["wa"].index("https://") == 0


# --- El cargo ------------------------------------------------------------------------------------

def test_el_cargo_tiene_exactamente_tres_opciones(r):
    assert r["roles"] == [["asesor", "Asesor Comercial"], ["alianzas", "Alianzas Comerciales"],
                          ["directora", "Directora"]]


def test_el_cargo_por_defecto_no_cambia(r):
    assert r["cargoDefecto"] == "Alianzas Comerciales · Centauro ADS"
    assert r["cargoAsesor"] == "Asesor Comercial · Centauro ADS"


# --- La imagen de WhatsApp (los espacios ya resueltos) ---------------------------------------------

def test_espacios_de_h_en_su_orden_con_foto_y_enlace(r):
    e = r["espaciosH"]
    assert [x["id"] for x in e] == ["medida--aaaa00000001", "totem", "vallas", "led"]
    propio, totem = e[0], e[1]
    assert propio["nombre"] == "PRODUCTO PROPIO" and propio["foto"] == "" and propio["enlace"] == ""
    assert totem["foto"].endswith(r["imgs"]["totem"]) and totem["enlace"] == r["canva_totem"]


def test_espacios_de_h_usan_lo_propio_de_la_entrega(r):
    totem = [x for x in r["espaciosPropios"] if x["id"] == "totem"][0]
    assert totem["nombre"] == "TOTEM PROPIO" and totem["foto"] == "https://x.test/totem.gif"


# --- La publicación enlaza el motor con su huella (2026-10-13) --------------------------------------

def test_el_compositor_publicado_enlaza_el_motor_con_su_huella():
    """
    Sin la huella, un navegador con el render.js anterior y el compositor nuevo dejaba el botón de la
    imagen de servicios sin hacer nada: el servidor no dice cuánto guardar el motor.
    """
    import hashlib
    publicado = MOTOR.parents[2] / "app" / "static" / "email"
    huella = hashlib.sha256((publicado / "render.js").read_bytes()).hexdigest()[:12]
    assert '<script src="render.js?v=%s"></script>' % huella in (publicado / "compositor.html").read_text(encoding="utf-8")
    assert (publicado / "render.js").read_bytes() == MOTOR.read_bytes()
