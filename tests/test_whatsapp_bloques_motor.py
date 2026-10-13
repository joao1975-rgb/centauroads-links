"""
WhatsApp por bloques en el motor (especificación 010, T1002).

- El mensaje principal de la H ya no lista los enlaces de los espacios (deroga FR-906 de la 009); si va
  al menos un bloque, dice «Te envío aparte los espacios que la acompañan.».
- `bloquesWhatsApp(st)`: un bloque por espacio incluido y no excluido (`bloques.entrega.waFuera`), en
  el orden de la entrega, con su nombre y su enlace propio `<enlace de la entrega>/<espacio>`. Sin
  enlace guardado, ninguno.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

MOTOR = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "render.js"
ENLACE = "https://mails.centauroads.com/p/abc123"
LINEA = "Te envío aparte los espacios que la acompañan."

GUION = r"""
const M = require(process.argv[2]);
const ENLACE = process.argv[3];
const base = (extra) => {
  const st = M.defaultState(); st.plantilla = 'H'; st.perfil = 'general';
  Object.assign(st.bloques.entrega, { enlace: ENLACE, incluidos: ['vallas', 'led', 'totem'],
    orden: ['totem', 'medida--aaaa00000001', 'vallas'],
    aMedida: [{ id: 'medida--aaaa00000001', nombre: 'PRODUCTO PROPIO', cobertura: '', canva: '', carrusel: '' }],
    espacios: { led: { nombre: 'LED PROPIA' } } }, extra || {});
  return st;
};
const out = {};
out.nombres = {}; M.defaultState().servicios.forEach(s => { out.nombres[s.id] = s.nombre; out['canva_' + s.id] = s.canva; });
const st = base(), antes = JSON.stringify(st);
out.wa = M.renderWhatsApp(st);
out.bloques = M.bloquesWhatsApp(st);
out.intacto = JSON.stringify(st) === antes;
out.fuera = M.bloquesWhatsApp(base({ waFuera: ['vallas', 'medida--aaaa00000001'] }));
out.todosFuera = { wa: M.renderWhatsApp(base({ waFuera: ['vallas', 'led', 'totem', 'medida--aaaa00000001'] })),
  bloques: M.bloquesWhatsApp(base({ waFuera: ['vallas', 'led', 'totem', 'medida--aaaa00000001'] })) };
out.sinEspacios = M.renderWhatsApp(base({ incluidos: [], aMedida: [] }));
out.sinEnlace = M.bloquesWhatsApp(base({ enlace: '' }));
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def r(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible")
    guion = tmp_path_factory.mktemp("bloques") / "_b.js"
    guion.write_text(GUION, encoding="utf-8")
    p = subprocess.run(["node", str(guion), str(MOTOR), ENLACE], capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    assert p.returncode == 0, "el motor falló:\n" + p.stderr
    return json.loads(p.stdout)


def test_el_mensaje_principal_no_lista_los_enlaces(r):
    for s in ("vallas", "led", "totem"):
        assert r["canva_" + s] not in r["wa"], s
    assert "/p/abc123/" not in r["wa"]
    assert r["wa"].split("\n")[0] == ENLACE


def test_dice_que_los_espacios_van_aparte_solo_si_hay_bloques(r):
    assert LINEA in r["wa"]
    assert LINEA not in r["todosFuera"]["wa"] and r["todosFuera"]["bloques"] == []
    assert LINEA not in r["sinEspacios"]


def test_un_bloque_por_espacio_en_su_orden_con_su_enlace_propio(r):
    assert [b["id"] for b in r["bloques"]] == ["totem", "medida--aaaa00000001", "vallas", "led"]
    totem = r["bloques"][0]
    assert totem["texto"] == "%s\n%s/totem" % (r["nombres"]["totem"], ENLACE)
    assert r["bloques"][1]["texto"] == "PRODUCTO PROPIO\n%s/medida--aaaa00000001" % ENLACE
    assert r["bloques"][3]["nombre"] == "LED PROPIA"   # lo propio de la entrega


def test_los_excluidos_no_tienen_bloque(r):
    assert [b["id"] for b in r["fuera"]] == ["totem", "led"]


def test_sin_enlace_guardado_no_hay_bloques(r):
    assert r["sinEnlace"] == []


def test_el_estado_no_se_toca(r):
    assert r["intacto"]
