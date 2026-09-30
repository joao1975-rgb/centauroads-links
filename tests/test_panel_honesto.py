"""
El panel dice qué campos no cambian el correo, y avisa de las fechas que ya pasaron.

El panel es uno para las ocho plantillas y cada una usa una parte. Sin decirlo, mentía: en E, F y
G se escribía el saludo, la introducción o el texto del botón y no pasaba nada, y el interruptor
del asesor no cambiaba ninguna plantilla. La decisión la toma el motor (`cambiaElCorreo`)
renderizando una copia; aquí se prueba que no se equivoca en ninguna de las dos direcciones,
porque marcar como inútil un campo que sí se usa sería otra forma de mentir.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
MOTOR = RAIZ / "prototipos" / "mail" / "render.js"
ESTATICO = RAIZ / "app" / "static" / "email"

GUION = r"""
const M = require(process.argv[2]);
const fuera = { casos: {}, falsos: [], asesorOn: {}, apagado: null, fechas: {}, botonE: '' };

// Casos conocidos, comprobados a mano en la auditoria.
['A', 'E'].forEach(function (k) {
  const st = M.defaultState(); st.plantilla = k;
  fuera.casos[k] = {};
  ['bloques.saludo.texto', 'bloques.intro.texto', 'bloques.cta.texto'].forEach(function (r) {
    fuera.casos[k][r] = M.cambiaElCorreo(st, k, r);
  });
});

// El interruptor del asesor: en ninguna plantilla cambiaba nada. Por eso se quito del panel.
Object.keys(M.TEMPLATES).forEach(function (k) {
  const st = M.defaultState(); st.plantilla = k;
  fuera.asesorOn[k] = M.cambiaElCorreo(st, k, 'bloques.asesor.on');
});

// Un campo de un bloque APAGADO no es inutil: el bloque puede encenderse.
const ap = M.defaultState(); ap.plantilla = 'A'; ap.bloques.saludo.on = false;
fuera.apagado = M.cambiaElCorreo(ap, 'A', 'bloques.saludo.texto');

// La prueba de verdad contra falsos positivos: si el texto de un campo APARECE en el correo, el
// motor no puede decir que ese campo no lo cambia.
Object.keys(M.TEMPLATES).forEach(function (k) {
  const base = M.defaultState(); base.plantilla = k;
  Object.keys(base.bloques).forEach(function (b) {
    Object.keys(base.bloques[b]).forEach(function (c) {
      if (typeof base.bloques[b][c] !== 'string') return;
      const st = JSON.parse(JSON.stringify(base));
      Object.keys(st.bloques).forEach(function (x) { if (st.bloques[x]) st.bloques[x].on = true; });
      const marca = 'MRC' + b + c + 'ZQ';
      st.bloques[b][c] = marca;
      if (M.render(st, k).indexOf(marca) >= 0 && !M.cambiaElCorreo(st, k, 'bloques.' + b + '.' + c)) {
        fuera.falsos.push(k + ':' + b + '.' + c);
      }
    });
  });
});

// Fechas, contra un "hoy" fijo: 29 de septiembre de 2026.
const hoy = new Date(2026, 8, 29);
['Q1 2026', 'Q4 2026', 'Octubre – Diciembre 2026', 'Diciembre 2025', 'Julio de 2026',
 'Cerramos programación de Q1 el 15 de noviembre'].forEach(function (t) {
  fuera.fechas[t] = M.fechasPasadas({ x: t }, hoy).length > 0;
});

// El boton de E sale del campo, no de un literal.
const e = M.defaultState(); e.plantilla = 'E'; e.bloques.asesor.botonTexto = 'BOTON-DE-PRUEBA';
fuera.botonE = M.render(e, 'E');

process.stdout.write(JSON.stringify(fuera));
"""


@pytest.fixture(scope="module")
def r(tmp_path_factory):
    if shutil.which("node") is None:
        pytest.skip("node no está disponible: estas pruebas necesitan Node 18+")
    guion = tmp_path_factory.mktemp("ph") / "_p.js"
    guion.write_text(GUION, encoding="utf-8")
    salida = subprocess.run(["node", str(guion), str(MOTOR)],
                            capture_output=True, text=True, encoding="utf-8", timeout=180)
    assert salida.returncode == 0, "el motor falló:\n" + salida.stderr
    return json.loads(salida.stdout)


def test_e_ignora_saludo_introduccion_y_boton_y_a_no(r):
    """Los tres casos que encontró la auditoría, en las dos direcciones."""
    for ruta in ("bloques.saludo.texto", "bloques.intro.texto", "bloques.cta.texto"):
        assert r["casos"]["A"][ruta] is True, "A sí usa %s" % ruta
        assert r["casos"]["E"][ruta] is False, "E no usa %s: el panel debe decirlo" % ruta


def test_el_interruptor_del_asesor_no_cambiaba_nada(r):
    """Por eso se quitó del panel: un interruptor que no apaga nada miente."""
    assert not any(r["asesorOn"].values()), r["asesorOn"]


def test_un_campo_de_un_bloque_apagado_no_se_da_por_inutil(r):
    """El bloque puede encenderse. Marcarlo inútil por estar apagado sería falso."""
    assert r["apagado"] is True


def test_ningun_campo_que_sale_en_el_correo_se_da_por_inutil(r):
    """
    La dirección que más importa: si el texto de un campo aparece en el correo, decir que no lo
    cambia sería otra mentira del panel, solo que al revés. Se recorren todos los campos de texto
    de todos los bloques, en las ocho plantillas.
    """
    assert r["falsos"] == [], "salen en el correo pero se dan por inútiles: %s" % r["falsos"]


def test_las_fechas_pasadas_se_detectan_y_las_futuras_no(r):
    """Contra un «hoy» fijo, 29-sep-2026, para que la prueba no caduque ella misma."""
    f = r["fechas"]
    assert f["Q1 2026"] is True
    assert f["Diciembre 2025"] is True
    assert f["Julio de 2026"] is True
    assert f["Q4 2026"] is False
    assert f["Octubre – Diciembre 2026"] is False
    # Sin año no se juzga: «Q1» a secas puede ser el próximo.
    assert f["Cerramos programación de Q1 el 15 de noviembre"] is False


def test_el_boton_de_e_sale_del_campo(r):
    """Era un literal que decía «Q1» aunque el periodo cambiara."""
    assert "BOTON-DE-PRUEBA" in r["botonE"]


def test_build_js_encuentra_todas_las_imagenes_sin_la_carpeta_local():
    """
    `prototipos/mail/img/` está en .gitignore: en un clon limpio no existe y build.js cae a
    `app/static/email/`. Esa carpeta tiene que tener TODAS las imágenes que piden las plantillas,
    o el compositor autónomo sale con fotos rotas en cualquier otro equipo.
    """
    if shutil.which("node") is None:
        pytest.skip("node no está disponible")
    guion = r'''
      const M = require(process.argv[1]); const out = new Set();
      Object.keys(M.TEMPLATES).forEach(k => Object.keys(M.IMG_SETS).forEach(set => {
        const st = M.defaultState(); st.plantilla = k; st.imgSet = set;
        (M.render(st, k).match(/src="img\/[^"]+"/g) || []).forEach(m => out.add(m.slice(9, -1)));
      }));
      process.stdout.write(JSON.stringify([...out]));
    '''
    salida = subprocess.run(["node", "-e", guion, str(MOTOR)],
                            capture_output=True, text=True, encoding="utf-8", timeout=120)
    assert salida.returncode == 0, salida.stderr
    pedidas = json.loads(salida.stdout)
    assert pedidas, "no se encontró ninguna imagen: la prueba no estaría probando nada"
    faltan = [n for n in pedidas if not (ESTATICO / n).is_file()]
    assert faltan == [], "imágenes que no están en app/static/email/: %s" % faltan


def test_build_js_no_depende_de_la_carpeta_ignorada():
    """El cambio en sí: si img/ no existe, se usa la carpeta versionada."""
    fuente = (RAIZ / "prototipos" / "mail" / "build.js").read_text(encoding="utf-8")
    assert re.search(r"fs\.existsSync\(imgLocal\)\s*\?\s*imgLocal", fuente), (
        "build.js tiene que caer a app/static/email cuando falta prototipos/mail/img")


def test_python_fijado_a_una_version_que_instala():
    """
    Con 3.14, pydantic 2.10.4 intenta compilar con Rust y falla, y en el equipo del dueño 3.14 es
    el Python por defecto. La versión tiene que estar escrita donde las herramientas la leen.
    """
    assert (RAIZ / ".python-version").read_text(encoding="utf-8").strip() == "3.12"
    assert "3.14" in (RAIZ / "requirements.txt").read_text(encoding="utf-8")
