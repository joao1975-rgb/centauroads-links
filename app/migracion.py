"""
Migración aditiva del esquema.

Corre en cada arranque del contenedor, así que tiene que ser idempotente: la segunda vez no puede
hacer nada. Y como comparte base de datos con el acortador, que es lo que de verdad está en
producción, aquí solo se AÑADE.

Reglas que este módulo no rompe nunca (Principio I de la constitución):

  * No borra tablas ni columnas.
  * No renombra nada.
  * No cambia tipos.
  * Toda columna que añade es opcional (nullable), porque las filas que ya existen no tienen ese
    dato y su ausencia es la verdad, no un hueco que rellenar.

Consecuencia deliberada: el código anterior sigue pudiendo escribir en la base de datos migrada,
porque ignora sin más las columnas que no conoce. Eso hace la migración reversible en la práctica.
"""

import logging

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from .database import Base
from . import models  # noqa: F401  — registra los modelos en Base.metadata

log = logging.getLogger("centaurads.migracion")

# Columnas a añadir, por tabla. El tipo va en SQL porque ALTER TABLE lo necesita literal.
# TODAS sin NOT NULL y sin DEFAULT: en SQLite eso convierte el ALTER en una operación de
# metadatos, sin reescribir la tabla, que es lo que la hace segura sobre datos reales.
COLUMNAS_NUEVAS = {
    "clicks": [
        ("contact_token", "VARCHAR(64)"),
    ],
    "deliveries": [
        ("contact_id", "INTEGER"),
        ("perfil", "VARCHAR(30)"),
        ("formato", "VARCHAR(2)"),
        ("sender_account_id", "INTEGER"),
        ("panel_user_id", "INTEGER"),
    ],
}

# Índices que conviene tener, creados aparte porque ALTER TABLE ADD COLUMN no los admite.
INDICES = [
    ("ix_clicks_contact_token", "clicks", "contact_token"),
    ("ix_deliveries_contact_id", "deliveries", "contact_id"),
]


def columnas_de(inspector, tabla):
    return {c["name"] for c in inspector.get_columns(tabla)}


def migrar(engine: Engine) -> dict:
    """
    Pone el esquema al día. Devuelve lo que hizo, para poder registrarlo.

    Es seguro llamarla tantas veces como haga falta: mira el estado real antes de tocar nada.
    """
    inspector = inspect(engine)
    tablas = set(inspector.get_table_names())
    hecho = {"columnas": [], "tablas": [], "indices": []}

    # 1) Ampliar las tablas que ya existen. Si no existen todavía (instalación nueva), no hay nada
    #    que ampliar: las creará create_all con las columnas ya incluidas.
    with engine.begin() as con:
        for tabla, columnas in COLUMNAS_NUEVAS.items():
            if tabla not in tablas:
                continue
            existentes = columnas_de(inspector, tabla)
            for nombre, tipo in columnas:
                if nombre in existentes:
                    continue
                con.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {tipo}"))
                hecho["columnas"].append(f"{tabla}.{nombre}")

    # 2) Crear las tablas nuevas. create_all solo toca las que faltan; las existentes ni las mira.
    antes = set(inspect(engine).get_table_names())
    Base.metadata.create_all(bind=engine)
    hecho["tablas"] = sorted(set(inspect(engine).get_table_names()) - antes)

    # 3) Índices sobre las columnas recién añadidas.
    inspector = inspect(engine)
    with engine.begin() as con:
        for nombre, tabla, columna in INDICES:
            if tabla not in inspector.get_table_names():
                continue
            if columna not in columnas_de(inspector, tabla):
                continue
            if nombre in {i["name"] for i in inspector.get_indexes(tabla)}:
                continue
            con.execute(text(f"CREATE INDEX {nombre} ON {tabla} ({columna})"))
            hecho["indices"].append(nombre)

    if hecho["columnas"] or hecho["tablas"] or hecho["indices"]:
        log.info(
            "Migración aplicada — columnas: %s | tablas: %s | índices: %s",
            hecho["columnas"] or "ninguna",
            hecho["tablas"] or "ninguna",
            hecho["indices"] or "ninguno",
        )
    return hecho
