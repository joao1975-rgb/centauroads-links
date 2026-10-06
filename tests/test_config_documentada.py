"""
Cada variable de entorno que lee la aplicación está en `.env.example` y en el README.

La auditoría de instalación (2026-09-30) encontró que la aplicación leía 12 variables y el ejemplo
explicaba 5. Sin `PANEL_BOOTSTRAP` un equipo nuevo arranca con el panel vacío y nadie puede entrar;
sin `SESSION_SECRET` las sesiones dependen de un fichero en disco. Esta prueba falla en cuanto
alguien añade una variable nueva y se olvida de documentarla.
"""

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
LEE = re.compile(r"""os\.(?:getenv|environ\.get)\(\s*["']([A-Z][A-Z0-9_]+)["']""")


def _variables_que_lee_la_app():
    nombres = set()
    for fichero in list((RAIZ / "app").rglob("*.py")) + [RAIZ / "run.py"]:
        nombres.update(LEE.findall(fichero.read_text(encoding="utf-8")))
    return nombres


def test_la_prueba_encuentra_variables():
    """Si el patrón dejara de encontrar nada, las pruebas de abajo pasarían sin probar nada."""
    assert {"SESSION_SECRET", "PANEL_BOOTSTRAP", "ADMIN_KEY"} <= _variables_que_lee_la_app()


def test_cada_variable_esta_en_el_ejemplo():
    ejemplo = (RAIZ / ".env.example").read_text(encoding="utf-8")
    documentadas = set(re.findall(r"^#?\s*([A-Z][A-Z0-9_]+)=", ejemplo, re.M))
    faltan = sorted(_variables_que_lee_la_app() - documentadas)
    assert faltan == [], "leídas por la aplicación pero sin explicar en .env.example: %s" % faltan


def test_cada_variable_esta_en_el_readme():
    readme = (RAIZ / "README.md").read_text(encoding="utf-8")
    faltan = sorted(v for v in _variables_que_lee_la_app() if "`%s`" % v not in readme)
    assert faltan == [], "leídas por la aplicación pero sin explicar en el README: %s" % faltan
