"""
La prueba que protege los datos del acortador.

Escrita ANTES que la migración, a propósito: si pasara ahora, no estaría protegiendo nada.

Lo que afirma es lo único que de verdad importa del Principio I de la constitución: una base de
datos escrita por el código ANTERIOR se abre con el código NUEVO y sigue teniendo todo dentro.
Para que eso sea cierto de verdad, el esquema "viejo" se construye aquí con SQL literal, tal y
como está hoy en producción, y no importando los modelos actuales: si importáramos los modelos,
la prueba se movería con ellos y dejaría de detectar la rotura.
"""

import sqlite3
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect, text

# Esquema tal y como lo creó el código anterior. Congelado a propósito: NO importar models.
ESQUEMA_ANTERIOR = """
CREATE TABLE links (
    id INTEGER NOT NULL PRIMARY KEY,
    slug VARCHAR(100) NOT NULL,
    target_url TEXT NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    is_active BOOLEAN,
    click_count INTEGER,
    created_at DATETIME,
    last_clicked_at DATETIME
);
CREATE UNIQUE INDEX ix_links_slug ON links (slug);

CREATE TABLE deliveries (
    id INTEGER NOT NULL PRIMARY KEY,
    link_id INTEGER NOT NULL REFERENCES links (id),
    channel VARCHAR(50),
    delivered_at DATETIME
);

CREATE TABLE clicks (
    id INTEGER NOT NULL PRIMARY KEY,
    link_id INTEGER NOT NULL REFERENCES links (id),
    ip VARCHAR(50),
    user_agent TEXT,
    referer TEXT,
    clicked_at DATETIME
);
"""

# Datos representativos de lo que hay hoy en producción, con valores inventados.
ENLACES = [
    (1, "pantallas-led", "https://www.canva.com/design/EJEMPLO-led/view", "Pantallas LED", "DOOH", 1, 17),
    (2, "vallas", "https://www.canva.com/design/EJEMPLO-vallas/view", "Vallas OOH", "OOH", 1, 4),
    (3, "totem", "https://www.canva.com/design/EJEMPLO-totem/view", "Tótem digital", "DOOH", 0, 0),
]


@pytest.fixture()
def bd_anterior(tmp_path):
    """Una base de datos escrita por el código anterior, con enlaces, clics y entregas dentro."""
    ruta = tmp_path / "centaurads_links.db"
    con = sqlite3.connect(ruta)
    con.executescript(ESQUEMA_ANTERIOR)
    ahora = datetime.now(timezone.utc).isoformat(sep=" ", timespec="seconds")

    for id_, slug, url, nombre, cat, activo, clics in ENLACES:
        con.execute(
            "INSERT INTO links (id, slug, target_url, name, description, category,"
            " is_active, click_count, created_at) VALUES (?,?,?,?,'',?,?,?,?)",
            (id_, slug, url, nombre, cat, activo, clics, ahora),
        )
        for n in range(clics):
            con.execute(
                "INSERT INTO clicks (link_id, ip, user_agent, referer, clicked_at)"
                " VALUES (?,?,?,?,?)",
                (id_, f"190.0.0.{n % 250}", "Mozilla/5.0", "", ahora),
            )
        con.execute(
            "INSERT INTO deliveries (link_id, channel, delivered_at) VALUES (?,?,?)",
            (id_, "whatsapp", ahora),
        )
    con.commit()
    con.close()
    return ruta


def _migrar(ruta):
    """Aplica la migración del código nuevo sobre esa base de datos."""
    from app.migracion import migrar

    motor = create_engine(f"sqlite:///{ruta}", connect_args={"check_same_thread": False})
    migrar(motor)
    return motor


def test_los_enlaces_sobreviven(bd_anterior):
    """Ningún enlace desaparece ni cambia de destino: son los que están impresos en vallas."""
    motor = _migrar(bd_anterior)
    with motor.connect() as con:
        filas = con.execute(text("SELECT slug, target_url, click_count FROM links ORDER BY id")).all()

    assert len(filas) == len(ENLACES), "La migración perdió enlaces"
    for fila, esperado in zip(filas, ENLACES):
        assert fila[0] == esperado[1]
        assert fila[1] == esperado[2], f"Cambió el destino de /{fila[0]}"
        assert fila[2] == esperado[6], f"Cambió el contador de /{fila[0]}"


def test_los_clics_sobreviven(bd_anterior):
    """El historial de clics es la única métrica que el acortador acumula: no puede perderse."""
    motor = _migrar(bd_anterior)
    esperados = sum(e[6] for e in ENLACES)
    with motor.connect() as con:
        total = con.execute(text("SELECT COUNT(*) FROM clicks")).scalar_one()
        con_ip = con.execute(text("SELECT COUNT(*) FROM clicks WHERE ip != ''")).scalar_one()

    assert total == esperados, f"Se esperaban {esperados} clics y quedaron {total}"
    assert con_ip == esperados, "Algún clic perdió su IP"


def test_las_entregas_sobreviven(bd_anterior):
    motor = _migrar(bd_anterior)
    with motor.connect() as con:
        total = con.execute(text("SELECT COUNT(*) FROM deliveries")).scalar_one()
        canales = con.execute(text("SELECT DISTINCT channel FROM deliveries")).scalars().all()

    assert total == len(ENLACES)
    assert canales == ["whatsapp"], "La migración alteró el canal de entregas anteriores"


def test_las_columnas_anteriores_siguen_intactas(bd_anterior):
    """Nada se renombra, nada cambia de tipo, nada se borra."""
    motor = _migrar(bd_anterior)
    inspector = inspect(motor)

    esperado = {
        "links": {"id", "slug", "target_url", "name", "description", "category",
                  "is_active", "click_count", "created_at", "last_clicked_at"},
        "deliveries": {"id", "link_id", "channel", "delivered_at"},
        "clicks": {"id", "link_id", "ip", "user_agent", "referer", "clicked_at"},
    }
    for tabla, columnas in esperado.items():
        actuales = {c["name"] for c in inspector.get_columns(tabla)}
        faltan = columnas - actuales
        assert not faltan, f"La migración se llevó por delante {faltan} de {tabla}"


def test_las_columnas_nuevas_aparecen_y_son_opcionales(bd_anterior):
    """
    Lo añadido tiene que ser opcional. Si alguna columna nueva fuera NOT NULL, las filas que ya
    existen no cabrían y la migración fallaría sobre datos reales en vez de sobre una prueba.
    """
    motor = _migrar(bd_anterior)
    inspector = inspect(motor)

    clicks = {c["name"]: c for c in inspector.get_columns("clicks")}
    assert "contact_token" in clicks, "Falta clicks.contact_token: sin ella no hay atribución"
    assert clicks["contact_token"]["nullable"], "contact_token debe admitir nulo (apertura anónima)"

    deliveries = {c["name"]: c for c in inspector.get_columns("deliveries")}
    for nueva in ("contact_id", "perfil", "formato", "sender_account_id", "panel_user_id"):
        assert nueva in deliveries, f"Falta deliveries.{nueva}"
        assert deliveries[nueva]["nullable"], (
            f"deliveries.{nueva} debe admitir nulo: las entregas anteriores no tienen ese dato"
        )


def test_las_tablas_nuevas_se_crean(bd_anterior):
    motor = _migrar(bd_anterior)
    tablas = set(inspect(motor).get_table_names())
    for nueva in ("contacts", "panel_users", "sender_accounts", "sender_permissions", "alerts"):
        assert nueva in tablas, f"Falta la tabla {nueva}"


def test_migrar_dos_veces_no_rompe(bd_anterior):
    """
    Se ejecuta en cada arranque del contenedor. Si no fuera idempotente, el segundo despliegue
    tumbaría la aplicación entera, acortador incluido.
    """
    _migrar(bd_anterior)
    motor = _migrar(bd_anterior)  # otra vez, como en el siguiente arranque

    with motor.connect() as con:
        assert con.execute(text("SELECT COUNT(*) FROM links")).scalar_one() == len(ENLACES)


def test_el_codigo_anterior_seguiria_funcionando(bd_anterior):
    """
    La reversión que promete el plan: como todo lo añadido es opcional, el código de antes puede
    volver a escribir en esta base de datos sin saber nada de las columnas nuevas.
    """
    motor = _migrar(bd_anterior)
    ahora = datetime.now(timezone.utc).isoformat(sep=" ", timespec="seconds")

    with motor.begin() as con:
        # Exactamente el INSERT que hace el código anterior, sin mencionar las columnas nuevas.
        con.execute(
            text("INSERT INTO clicks (link_id, ip, user_agent, referer, clicked_at)"
                 " VALUES (1, '190.0.0.9', 'Mozilla/5.0', '', :t)"),
            {"t": ahora},
        )
        con.execute(
            text("INSERT INTO deliveries (link_id, channel, delivered_at)"
                 " VALUES (1, 'instagram', :t)"),
            {"t": ahora},
        )

    with motor.connect() as con:
        token = con.execute(
            text("SELECT contact_token FROM clicks ORDER BY id DESC LIMIT 1")
        ).scalar_one()
        assert token is None, "Un clic del código anterior debe quedar como apertura anónima"
