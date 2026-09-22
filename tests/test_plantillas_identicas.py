"""
La red de la fase 1 de la 002: las plantillas A-G no pueden cambiar ni un byte.

El motor `prototipos/mail/render.js` se está partiendo en bloques y recetas. Un refactor que
cambie una coma de la salida no es un refactor: es un cambio de contenido disfrazado, y el correo
que el equipo manda a sus clientes no puede moverse por un cambio interno (FR-126, SC-105).

Esta prueba es la segunda red. La primera vive en `prototipos/mail/build.js`, que hace la misma
comprobación al construir. Se mantienen las dos a propósito: el `build` protege al que genera los
entregables, la prueba protege al que solo ejecuta `pytest`.

A diferencia del `build`, esta prueba **no escribe nada en el repositorio**: renderiza en un
directorio temporal. Así se puede ejecutar con el árbol sucio sin ensuciarlo más.

Si esta prueba falla y el cambio era querido, se actualiza la referencia con
`GOLDEN_UPDATE=1 node prototipos/mail/build.js`, mirando antes qué cambió. Nunca al revés.
"""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
MOTOR = RAIZ / "prototipos" / "mail" / "render.js"
GOLDEN = RAIZ / "tests" / "golden"

# Renderiza cada formato x cada juego de imágenes con el contenido por defecto, exactamente como
# lo hace build.js, y escribe el resultado en el directorio que se le pase. Las plantillas
# entregables apuntan a producción (`assetBaseProd`), que es lo que ve Gmail.
GUION = r"""
const fs = require('fs'), path = require('path');
const M = require(process.argv[2]);
const destino = process.argv[3];
const hechas = [];
for (const key of Object.keys(M.TEMPLATES)) {
  for (const set of Object.keys(M.IMG_SETS)) {
    const st = M.defaultState();
    st.plantilla = key; st.imgSet = set; st.assetBase = st.assetBaseProd;
    const nombre = key + '__' + set + '.html';
    fs.writeFileSync(path.join(destino, nombre), M.render(st), 'utf8');
    hechas.push({ key: key, set: set, fichero: nombre });
  }
}
process.stdout.write(JSON.stringify(hechas));
"""


def _hay_node():
    return shutil.which("node") is not None


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    """Renderiza las plantillas con el motor actual. Sin node, la prueba se salta."""
    if not _hay_node():
        pytest.skip("node no está disponible; la guardia de build.js cubre este caso")
    destino = tmp_path_factory.mktemp("plantillas")
    guion = destino / "_render.js"
    guion.write_text(GUION, encoding="utf-8")
    salida = subprocess.run(
        ["node", str(guion), str(MOTOR), str(destino)],
        capture_output=True, text=True, timeout=120,
    )
    assert salida.returncode == 0, "el motor no pudo renderizar:\n" + salida.stderr
    return destino, json.loads(salida.stdout)


def _referencia(key, conjunto):
    """
    El nombre del fichero de referencia, deducido de la propia carpeta.

    Deliberadamente NO se replica aquí el diccionario de nombres bonitos de build.js
    ('A' -> 'cartelera', ...). Duplicarlo sería una segunda fuente de verdad, y este proyecto ya
    pagó dos veces el precio de tener más de una.
    """
    sufijo = "" if conjunto == "fotos" else "-" + conjunto
    patron = re.compile(r"^plantilla-%s-[a-z]+%s\.html$" % (re.escape(key), re.escape(sufijo)))
    candidatos = sorted(f for f in GOLDEN.iterdir() if patron.match(f.name))
    assert len(candidatos) == 1, (
        "esperaba una sola referencia para %s/%s y hay %d: %s"
        % (key, conjunto, len(candidatos), [c.name for c in candidatos])
    )
    return candidatos[0]


def test_la_referencia_existe():
    """Sin referencia no hay red, y una carpeta vacía pasaría todas las demás pruebas."""
    plantillas = [f for f in GOLDEN.iterdir() if f.name.startswith("plantilla-")]
    assert plantillas, "tests/golden/ no tiene ninguna plantilla de referencia"
    assert (GOLDEN / "README.md").exists(), "falta el README que dice de qué commit salieron"


def test_se_renderizan_todas(rendered):
    _, hechas = rendered
    plantillas = [f for f in GOLDEN.iterdir() if f.name.startswith("plantilla-")]
    assert len(hechas) == len(plantillas), (
        "el motor genera %d plantillas y la referencia tiene %d: alguien añadió o quitó un "
        "formato sin actualizar la referencia" % (len(hechas), len(plantillas))
    )


def test_cada_plantilla_es_identica_byte_a_byte(rendered):
    destino, hechas = rendered
    distintas = []
    for h in hechas:
        actual = (destino / h["fichero"]).read_bytes()
        referencia = _referencia(h["key"], h["set"]).read_bytes()
        if actual != referencia:
            distintas.append("%s/%s (%d bytes ahora, %d antes)"
                             % (h["key"], h["set"], len(actual), len(referencia)))
    assert not distintas, (
        "estas plantillas cambiaron:\n  " + "\n  ".join(distintas)
        + "\n\nEl refactor del motor no puede mover ni un byte de A-G (FR-126). Si el cambio era "
          "querido, mira qué cambió y actualiza la referencia:\n"
          "  GOLDEN_UPDATE=1 node prototipos/mail/build.js"
    )
