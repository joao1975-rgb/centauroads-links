"""
El catálogo de líneas de negocio en el servidor (especificación 003).

Lo que se fija aquí:

- **Siembra.** Con la base vacía, el catálogo nace igual que `catalogo-serie.json`, que a su vez
  sale de `render.js`: una sola fuente. Y nunca pisa un catálogo que ya existe.
- **Alta (US1).** Solo un administrador da de alta; el nombre no se repite; el enlace es http(s);
  el identificador sale del nombre y no choca con otro.
- **Plantillas (US2).** Por defecto todas; solo letras A–H sin repetir; sin ninguna, hay que
  confirmarlo.
- **Fotos.** Se reducen, se sirven en `/media/lineas/…` y esa ruta pública no sirve nada que no
  sea una foto de línea, por mucho que se le pruebe.
"""

import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import main as app_main
from app import models
from app.auth import sesion
from app.database import Base, SessionLocal
from app.mails.catalogo import fotos, siembra
from app.mails.catalogo.rutas import catalogo_activo

SERIE = json.loads((Path(__file__).resolve().parents[1] / "app" / "static" / "email"
                    / "catalogo-serie.json").read_text(encoding="utf-8"))
NUEVA = {"nombre": "Alquiler de pantallas", "eyebrow": "Renta de equipos",
         "cobertura": "Eventos en todo el país", "canva": "https://canva.link/alquiler-prueba",
         "alt": "Pantalla de alquiler en un evento"}


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


def _persona(db, email, rol):
    u = db.query(models.PanelUser).filter(models.PanelUser.email == email).first()
    if not u:
        u = models.PanelUser(email=email, nombre=email.split("@")[0], rol=rol, activo=True)
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


def _cliente(usuario=None):
    c = TestClient(app_main.app)
    if usuario is not None:
        c.cookies.set(sesion.COOKIE, sesion.crear(usuario.id, usuario.email))
    return c


@pytest.fixture(scope="module")
def admin(db):
    return _cliente(_persona(db, "admin-cat@ejemplo.test", "admin"))


@pytest.fixture(scope="module")
def comercial(db):
    return _cliente(_persona(db, "comercial-cat@ejemplo.test", "comercial"))


@pytest.fixture(scope="module")
def anonimo():
    return _cliente()


@pytest.fixture()
def base_vacia():
    motor = create_engine("sqlite://")
    Base.metadata.create_all(bind=motor)
    s = sessionmaker(bind=motor)()
    yield s
    s.close()


def _png(ancho=2000, alto=1000, modo="RGB"):
    buf = io.BytesIO()
    Image.new(modo, (ancho, alto), (200, 60, 30, 128) if modo == "RGBA" else (200, 60, 30)).save(buf, "PNG")
    return buf.getvalue()


def _alta(cliente, **cambios):
    cuerpo = dict(NUEVA)
    cuerpo.update(cambios)
    return cliente.post("/api/panel/lineas", json=cuerpo)


# --- Siembra -------------------------------------------------------------------------------------

def test_con_base_vacia_nace_el_catalogo_de_serie(base_vacia):
    assert siembra.siembra(base_vacia) is True
    assert catalogo_activo(base_vacia) == SERIE


def test_la_siembra_es_idempotente(base_vacia):
    siembra.siembra(base_vacia)
    assert siembra.siembra(base_vacia) is False
    assert base_vacia.query(models.LineaNegocio).count() == 5
    assert base_vacia.query(models.FamiliaD).count() == 3


def test_la_siembra_no_pisa_un_catalogo_que_ya_existe(base_vacia):
    siembra.siembra(base_vacia)
    led = base_vacia.get(models.LineaNegocio, "led")
    led.cobertura = "CAMBIADO EN EL PANEL"
    base_vacia.commit()
    siembra.siembra(base_vacia)
    assert base_vacia.get(models.LineaNegocio, "led").cobertura == "CAMBIADO EN EL PANEL"


def test_la_aplicacion_arranca_sembrada(db):
    ids = [l.id for l in db.query(models.LineaNegocio).order_by(models.LineaNegocio.orden)]
    assert ids[:5] == [l["id"] for l in SERIE["lineas"]]


# --- GET /api/catalogo ---------------------------------------------------------------------------

def test_el_catalogo_pide_sesion(anonimo):
    assert anonimo.get("/api/catalogo").status_code == 401


def test_cualquier_sesion_lee_el_catalogo(comercial):
    r = comercial.get("/api/catalogo")
    assert r.status_code == 200
    d = r.json()
    assert d["familias"] == SERIE["familias"]
    assert d["lineas"][:5] == SERIE["lineas"]


# --- Alta (US1) ----------------------------------------------------------------------------------

def test_un_administrador_da_de_alta_una_linea(admin):
    r = _alta(admin)
    assert r.status_code == 201, r.text
    d = r.json()
    assert d["id"] == "alquiler-de-pantallas"
    assert d["plantillas"] == "ABCDEFGH"
    assert d["activa"] is True
    nuevas = [l for l in admin.get("/api/catalogo").json()["lineas"] if l["id"] == d["id"]]
    assert len(nuevas) == 1 and nuevas[0]["nombre"] == "Alquiler de pantallas"
    assert nuevas[0]["canva"] == NUEVA["canva"] and nuevas[0]["ficha"] is None


def test_la_nueva_va_detras_de_las_que_ya_estaban(admin):
    ids = [l["id"] for l in admin.get("/api/catalogo").json()["lineas"]]
    assert ids.index("alquiler-de-pantallas") > ids.index("rider")


def test_un_comercial_no_da_de_alta(comercial):
    assert _alta(comercial, nombre="Otra cosa").status_code == 403


def test_sin_sesion_no_se_da_de_alta(anonimo):
    assert _alta(anonimo, nombre="Otra cosa").status_code == 401


def test_el_nombre_no_se_repite_aunque_cambien_las_mayusculas(admin):
    r = _alta(admin, nombre="ALQUILER DE PANTALLAS")
    assert r.status_code == 409
    assert "ya existe" in r.json()["detail"].lower()


def test_el_identificador_no_choca_con_otro(admin):
    r = _alta(admin, nombre="Alquiler de pantallas!")
    assert r.status_code == 201, r.text
    assert r.json()["id"] == "alquiler-de-pantallas-2"


def test_el_identificador_sale_sin_acentos(admin):
    r = _alta(admin, nombre="Producción audiovisual")
    assert r.status_code == 201, r.text
    assert r.json()["id"] == "produccion-audiovisual"


def test_un_nombre_no_da_un_identificador_reservado_del_navegador(admin):
    """`constructor` es una propiedad de todo objeto de JavaScript: como identificador de linea,
    el motor la encontraria en BANCO y FICHA sin estar ahi (revision de seguridad, 2026-10-03)."""
    r = _alta(admin, nombre="Constructor")
    assert r.status_code == 201, r.text
    assert r.json()["id"] == "linea-constructor"


@pytest.mark.parametrize("enlace", ["ftp://x.test/a", "canva.link/sin-protocolo", "javascript:alert(1)"])
def test_el_enlace_tiene_que_ser_http(admin, enlace):
    r = _alta(admin, nombre="Con enlace raro " + enlace[:3], canva=enlace)
    assert r.status_code == 400
    assert "http" in r.json()["detail"]


@pytest.mark.parametrize("nombre", ["", "   ", "x" * 121])
def test_el_nombre_es_obligatorio_y_con_limite(admin, nombre):
    assert _alta(admin, nombre=nombre).status_code == 400


def test_un_texto_demasiado_largo_se_rechaza(admin):
    assert _alta(admin, nombre="Cobertura larga", cobertura="x" * 201).status_code == 400


def test_la_familia_tiene_que_existir(admin):
    assert _alta(admin, nombre="Sin familia real", familia="no-existe").status_code == 400
    r = _alta(admin, nombre="En la familia DOOH", familia="dooh")
    assert r.status_code == 201 and r.json()["familia"] == "dooh"


# --- Plantillas (US2) ----------------------------------------------------------------------------

def test_las_plantillas_se_guardan_en_orden(admin):
    r = _alta(admin, nombre="Solo A y H", plantillas="HA")
    assert r.status_code == 201 and r.json()["plantillas"] == "AH"


@pytest.mark.parametrize("plantillas", ["AX", "AA", "abc", "ABCDEFGHI"])
def test_letras_invalidas_o_repetidas_se_rechazan(admin, plantillas):
    assert _alta(admin, nombre="Mal " + plantillas, plantillas=plantillas).status_code == 400


def test_sin_plantillas_hay_que_confirmarlo(admin):
    r = _alta(admin, nombre="En ninguna", plantillas="")
    assert r.status_code == 400
    assert "ninguna plantilla" in r.json()["detail"]
    r = _alta(admin, nombre="En ninguna", plantillas="", confirmarSinPlantillas=True)
    assert r.status_code == 201 and r.json()["plantillas"] == ""


# --- Lista de administración ---------------------------------------------------------------------

def test_la_lista_completa_es_de_administradores(admin, comercial, anonimo):
    assert anonimo.get("/api/panel/lineas").status_code == 401
    assert comercial.get("/api/panel/lineas").status_code == 403
    d = admin.get("/api/panel/lineas").json()
    assert {"lineas", "familias"} <= set(d)
    led = next(l for l in d["lineas"] if l["id"] == "led")
    assert led["activa"] is True and "orden" in led


# --- Fotos ---------------------------------------------------------------------------------------

def test_la_foto_se_reduce_y_se_sirve(admin, anonimo):
    r = admin.post("/api/panel/lineas/alquiler-de-pantallas/foto",
                   files={"fichero": ("evento.png", _png(), "image/png")})
    assert r.status_code == 200, r.text
    url = r.json()["img"]
    assert url.startswith("/media/lineas/alquiler-de-pantallas-") and url.endswith(".jpg")
    servida = anonimo.get(url)
    assert servida.status_code == 200
    assert servida.headers["content-type"] == "image/jpeg"
    assert Image.open(io.BytesIO(servida.content)).size == (1072, 536)
    linea = next(l for l in admin.get("/api/catalogo").json()["lineas"]
                 if l["id"] == "alquiler-de-pantallas")
    assert linea["img"] == url


def test_una_foto_con_transparencia_tambien_vale(admin):
    r = admin.post("/api/panel/lineas/alquiler-de-pantallas-2/foto",
                   files={"fichero": ("logo.png", _png(400, 300, "RGBA"), "image/png")})
    assert r.status_code == 200, r.text


def test_un_fichero_que_no_es_imagen_se_rechaza(admin):
    r = admin.post("/api/panel/lineas/alquiler-de-pantallas/foto",
                   files={"fichero": ("nota.png", b"esto no es una imagen", "image/png")})
    assert r.status_code == 400


@pytest.mark.parametrize("formato", ["BMP", "TIFF"])
def test_solo_jpg_png_o_webp(admin, formato):
    buf = io.BytesIO()
    Image.new("RGB", (20, 20)).save(buf, formato)
    r = admin.post("/api/panel/lineas/alquiler-de-pantallas/foto",
                   files={"fichero": ("a." + formato.lower(), buf.getvalue(), "image/" + formato.lower())})
    assert r.status_code == 400


def test_una_imagen_de_mas_de_40_megapixeles_se_rechaza_sin_cargarla(admin):
    buf = io.BytesIO()
    Image.new("1", (7000, 6000)).save(buf, "PNG")   # 42 MP que ocupan pocos KB
    r = admin.post("/api/panel/lineas/alquiler-de-pantallas/foto",
                   files={"fichero": ("grande.png", buf.getvalue(), "image/png")})
    assert r.status_code == 400 and "megapíxeles" in r.json()["detail"]


def test_mas_de_8_mb_se_rechaza(admin):
    r = admin.post("/api/panel/lineas/alquiler-de-pantallas/foto",
                   files={"fichero": ("enorme.jpg", b"0" * (fotos.MAXIMO_BYTES + 1), "image/jpeg")})
    assert r.status_code == 413


def test_la_foto_de_una_linea_que_no_existe_da_404(admin):
    r = admin.post("/api/panel/lineas/no-existe/foto",
                   files={"fichero": ("a.png", _png(10, 10), "image/png")})
    assert r.status_code == 404


def test_sin_texto_alternativo_no_hay_foto(admin):
    sin_alt = _alta(admin, nombre="Sin texto alternativo", alt="").json()
    r = admin.post("/api/panel/lineas/%s/foto" % sin_alt["id"],
                   files={"fichero": ("a.png", _png(10, 10), "image/png")})
    assert r.status_code == 400 and "alternativo" in r.json()["detail"]
    r = admin.post("/api/panel/lineas/%s/foto" % sin_alt["id"],
                   files={"fichero": ("a.png", _png(10, 10), "image/png")},
                   data={"alt": "Descripción de la foto"})
    assert r.status_code == 200 and r.json()["alt"] == "Descripción de la foto"


def test_un_comercial_no_sube_fotos(comercial):
    r = comercial.post("/api/panel/lineas/alquiler-de-pantallas/foto",
                       files={"fichero": ("a.png", _png(10, 10), "image/png")})
    assert r.status_code == 403


@pytest.mark.parametrize("pedido", [
    "/media/lineas/..%2F..%2Fpruebas.db",
    "/media/lineas/..%5Cpruebas.db",
    "/media/lineas/Mayusculas.jpg",
    "/media/lineas/foto.png",
    "/media/lineas/.jpg",
    "/media/lineas/no-existe-12345678.jpg",
    "/media/lineas/alquiler-12345678.jpg%0A",
])
def test_la_ruta_publica_solo_sirve_fotos_de_linea(anonimo, pedido):
    assert anonimo.get(pedido).status_code == 404
