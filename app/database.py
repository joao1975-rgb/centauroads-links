"""
Configuración de base de datos — SQLAlchemy
Soporta SQLite (dev) y PostgreSQL (producción)
"""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./data/centaurads_links.db"
)

# Ajuste para SQLite
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # Asegurar que el directorio data/ exista
    os.makedirs("data", exist_ok=True)

# Espera máxima (ms) ante un bloqueo antes de responder «database is locked». Distinto del
# valor que pysqlite pone por su cuenta (5000) para que las pruebas distingan si se aplica.
SQLITE_BUSY_TIMEOUT_MS = 7000

engine = create_engine(DATABASE_URL, connect_args=connect_args)


if engine.dialect.name == "sqlite":

    @event.listens_for(engine, "connect")
    def _configurar_sqlite(conexion_dbapi, _registro):
        """Aplica WAL y busy_timeout a CADA conexión nueva del pool.

        - journal_mode=WAL: lectores y un escritor no se bloquean entre sí; permite la copia en
          caliente diaria (scripts/backup_sqlite.sh) sin frenar la app. Queda persistido en el
          fichero, pero se repite por si la base se recrea.
        - busy_timeout: es por conexión, por eso va aquí y no una sola vez al arrancar.
        """
        cursor = conexion_dbapi.cursor()
        try:
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute(f"PRAGMA busy_timeout={SQLITE_BUSY_TIMEOUT_MS}")
        finally:
            cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
