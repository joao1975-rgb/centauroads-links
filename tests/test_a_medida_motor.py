"""
El motor con productos a medida en la H (especificación 008, T802).

- `bloques.entrega.aMedida` sale en la H **después** de los espacios del catálogo, con la misma
  tarjeta: su carrusel, su nombre, su texto y «Ver presentación».
- Sin enlace no hay enlace vacío: ni «Ver presentación» ni la foto envuelta en `href=""`.
- Uno sin nombre no sale.
- A–G, con el mismo estado, salen idénticas; el estado de la persona no se toca.
- El texto plano de la H no deja « — » colgando cuando faltan partes.
"""

import json
import shutil
import subprocess
from pathlib import Path

import pytest

MOTOR = Path(__file__).resolve().parents[1] / "prototipos" / "mail" / "render.js"

GUION = r"""
const M = require(process.argv[2]);
const copia = o => JSON.parse(JSON.stringify(o));
const base = () => { const st = M.defaultState(); st.plantilla = 'H'; st.perfil = 'general'; return st; };
const conMedida = () => {
  const st = base();
  st.bloques.entrega.aMedida = [
    { id: 'medida--aaaa0001', nombre: 'PRODUCTO UNO', cobertura: 'COBERTURA UNO',
      canva: 'https://x.test/uno', carrusel: 'https://x.test/uno.gif' },
    { id: 'medida--aaaa0002', nombre: 'PRODUCTO DOS', cobertura: '', canva: '', carrusel: '' },
    { id: 'medida--aaaa0003', nombre: '  ', cobertura: 'COBERTURA SIN NOMBRE', canva: '', carrusel: '' },
  ];
  return st;
};
const out = {};
const st = conMedida();
const antes = JSON.stringify(st);
out.h = M.render(st, 'H');
out.hSin = M.render(base(), 'H');
out.textoH = M.renderText(st);
out.waH = M.renderWhatsApp(st);
out.waSin = M.renderWhatsApp(base());
out.estadoIntacto = JSON.stringify(st) === antes;
out.nombres = st.servicios.filter(s => st.bloques.entrega.incluidos.indexOf(s.id) >= 0).map(s => s.nombre);
out.otras = {};
'ABCDEFG'.split('').forEach(k => {
  const a = conMedida(); a.plantilla = k; const b = base(); b.plantilla = k;
  out.otras[k] = [M.render(a, k), M.render(b, k), M.renderText(a), M.renderText(b)];
});
process.stdout.write(JSON.stringify(out));
"""


@pytest.fixture(scope="module")
def r(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible")
    guion = tmp_path_factory.mktemp("medida") / "_m.js"
    guion.write_text(GUION, encoding="utf-8")
    p = subprocess.run(["node", str(guion), str(MOTOR)], capture_output=True, text=True,
                       encoding="utf-8", timeout=120)
    assert p.returncode == 0, "el motor falló:\n" + p.stderr
    return json.loads(p.stdout)


def test_salen_despues_de_los_del_catalogo(r):
    h = r["h"]
    ultimo = max(h.index(n) for n in r["nombres"])
    assert ultimo < h.index("PRODUCTO UNO") < h.index("PRODUCTO DOS")


def test_con_su_carrusel_texto_y_enlace(r):
    h = r["h"]
    assert 'src="https://x.test/uno.gif"' in h and 'alt="PRODUCTO UNO"' in h
    assert "COBERTURA UNO" in h and 'href="https://x.test/uno"' in h


def test_sin_enlace_no_hay_enlace_vacio(r):
    assert 'href=""' not in r["h"]
    # Solo el de UNO añade un «Ver presentación»; DOS no tiene adónde llevar.
    assert r["h"].count("Ver presentaci") == r["hSin"].count("Ver presentaci") + 1


def test_sin_nombre_no_sale(r):
    assert "COBERTURA SIN NOMBRE" not in r["h"]
    assert "COBERTURA SIN NOMBRE" not in r["textoH"]


def test_a_g_no_los_ven(r):
    for k, (con, sin, texto_con, texto_sin) in r["otras"].items():
        assert con == sin, k
        assert texto_con == texto_sin, k


def test_el_estado_no_se_toca(r):
    assert r["estadoIntacto"]


def test_texto_plano_sin_partes_vacias(r):
    lineas = r["textoH"].split("\n")
    assert "• PRODUCTO UNO — COBERTURA UNO — https://x.test/uno" in lineas
    assert "• PRODUCTO DOS" in lineas
    assert not any(l.endswith("— ") or "—  —" in l for l in lineas)


def test_whatsapp_los_lista_tras_los_del_catalogo(r):
    # Desde la 009 WhatsApp lista los espacios: el de enlace con él; el que no, solo su nombre.
    assert "• PRODUCTO UNO: https://x.test/uno" in r["waH"]
    assert "• PRODUCTO DOS\n" in r["waH"]
    assert "COBERTURA SIN NOMBRE" not in r["waH"]
