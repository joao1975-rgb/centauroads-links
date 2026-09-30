"""
T064 · Cada conexión a la base SQLite del acortador debe abrir con WAL y busy_timeout.

Por qué importa: con el modo de diario por defecto (DELETE) un lector y un escritor se bloquean
entre sí, y sin busy_timeout SQLite responde «database is locked» al instante en vez de esperar.
Con la copia en caliente diaria (scripts/backup_sqlite.sh) leyendo la base mientras la app
escribe, ese choque deja de ser teórico. WAL permite lectores concurrentes con un escritor y
busy_timeout hace que la conexión espere hasta 7 s antes de rendirse.

Se comprueba el valor EXACTO (7000 ms) y no un mínimo: pysqlite ya abre cada conexión con
5000 ms por su cuenta (timeout=5.0), así que una aserción «>= 5000» pasaría aunque el PRAGMA
de app/database.py no se aplicara nunca. 7000 solo puede venir de nuestro código.

Se comprueba sobre conexiones NUEVAS del pool (no solo la primera), porque los PRAGMA de
busy_timeout son por conexión: si se aplicaran una sola vez al arrancar, la segunda conexión
volvería a los valores por defecto.

foreign_keys no se comprueba a propósito: el esquema declara claves foráneas pero SQLite nunca
las ha aplicado en este proyecto, y activarlas ahora cambiaría el comportamiento de borrados con
datos de producción que podrían tener huérfanos. Queda fuera del alcance de T065.
"""

import pytest
from sqlalchemy import text

from app.database import SQLITE_BUSY_TIMEOUT_MS, SessionLocal, engine

# Distinto del valor por defecto de pysqlite (5000) para que la prueba discrimine.
BUSY_TIMEOUT_ESPERADO_MS = 7000


def _leer_pragmas(conexion) -> tuple[str, int]:
    modo = conexion.execute(text("PRAGMA journal_mode")).scalar()
    espera = conexion.execute(text("PRAGMA busy_timeout")).scalar()
    return str(modo).lower(), int(espera)


@pytest.fixture(autouse=True)
def _solo_sqlite():
    if engine.dialect.name != "sqlite":
        pytest.skip("Los PRAGMA de WAL y busy_timeout solo aplican a SQLite")


def test_la_constante_de_la_app_es_la_esperada():
    assert SQLITE_BUSY_TIMEOUT_MS == BUSY_TIMEOUT_ESPERADO_MS


def test_conexion_del_engine_abre_en_wal_con_busy_timeout():
    with engine.connect() as con:
        modo, espera = _leer_pragmas(con)

    assert modo == "wal"
    assert espera == BUSY_TIMEOUT_ESPERADO_MS


def test_cada_conexion_nueva_trae_los_pragmas():
    # Se descarta el pool para obligar a abrir conexiones DBAPI nuevas: así se prueba que los
    # PRAGMA se aplican al conectar y no solo una vez al arrancar la aplicación.
    engine.dispose()
    conexiones = [engine.connect() for _ in range(3)]
    try:
        for con in conexiones:
            modo, espera = _leer_pragmas(con)
            assert modo == "wal"
            assert espera == BUSY_TIMEOUT_ESPERADO_MS
    finally:
        for con in conexiones:
            con.close()


def test_la_sesion_de_la_app_usa_los_mismos_pragmas():
    db = SessionLocal()
    try:
        modo, espera = _leer_pragmas(db.connection())
    finally:
        db.close()

    assert modo == "wal"
    assert espera == BUSY_TIMEOUT_ESPERADO_MS
