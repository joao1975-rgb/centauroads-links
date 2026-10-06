"""
Revisión de seguridad de las entregas (2026-10-06): cuatro huecos que ya estaban en producción.

1. **De quién es una entrega.** Cualquier persona con sesión leía, editaba y marcaba como
   entregada la propuesta de otra. Decisión del propietario: «Quien la creó y los
   administradores». A los demás se les responde lo mismo que si no existiera.
2. **Las imágenes se podían enumerar.** `/media/entregas/1/p0.jpg`, `/2/`, `/3/`… sin sesión: el
   material de cada cliente, a un bucle de distancia. Las nuevas van por una clave que no se
   adivina; las viejas siguen por su ruta, porque sus correos ya están enviados.
3. **Una subida podía tumbar el servidor**: una imagen pequeña que declara 48 megapíxeles, o
   cientos de ficheros en una sola petición, se leían enteros antes de mirar nada.
4. **CSRF desde un subdominio hermano.** La cookie del panel viaja en cualquier petición del
   mismo sitio; un `Origin` ajeno en un POST/PUT/DELETE de `/api/` se rechaza.
"""

import io
import re
import secrets

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import sesion
from app.database import SessionLocal
from app.mails.entregas import galeria, paginas
from tests.test_entregas_api import _pdf

CANVA = "https://www.canva.com/design/SEGURIDAD/view"
CLAVE = re.compile(r"^/media/e/[0-9a-f]{32}/")


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


def _persona(db, rol):
    usuario = models.PanelUser(email="seg-%s@ejemplo.test" % secrets.token_hex(4),
                               nombre="Seg " + rol, rol=rol, activo=True)
    db.add(usuario)
    db.commit()
    c = TestClient(app_main.app)
    c.cookies.set(sesion.COOKIE, sesion.crear(usuario.id, usuario.email))
    return c


@pytest.fixture(scope="module")
def autora(db):
    return _persona(db, "comercial")


@pytest.fixture(scope="module")
def otra(db):
    return _persona(db, "comercial")


@pytest.fixture(scope="module")
def admin(db):
    return _persona(db, "admin")


@pytest.fixture(scope="module")
def linea(db):
    fila = models.LineaNegocio(id="seg-%s" % secrets.token_hex(4), nombre="Pantalla seg",
                               cobertura="Cobertura", canva="https://www.canva.com/design/S/view")
    db.add(fila)
    db.commit()
    return fila.id


@pytest.fixture
def entrega(autora, db):
    contacto = models.Contact(nombre="Cliente Seg", email="seg@ejemplo.test",
                              empresa="Seg C.A.", token=secrets.token_urlsafe(24))
    db.add(contacto)
    db.commit()
    r = autora.post("/api/entregas", json={
        "titulo": "Propuesta de la autora", "canva_url": CANVA, "contact_id": contacto.id})
    assert r.status_code == 200, r.text
    return r.json()


def _sube(cliente, ruta, datos=None, nombre="deck.pdf"):
    return cliente.post(ruta + "/paginas", files={
        "fichero": (nombre, io.BytesIO(datos or _pdf(3)), "application/pdf")})


def _con_carrusel(cliente, entrega_id, linea=None):
    ruta = "/api/entregas/%d" % entrega_id + ("/espacios/%s" % linea if linea else "")
    assert _sube(cliente, ruta).status_code == 200
    r = cliente.put(ruta + "/paginas", json={"indices": [0, 1]})
    assert r.status_code == 200, r.text
    return r.json()


# --- 1. De quién es una entrega --------------------------------------------------------

def test_otra_persona_no_alcanza_la_entrega_por_ninguna_ruta(otra, entrega, linea):
    base = "/api/entregas/%d" % entrega["id"]
    cuerpo = {"titulo": "Robada", "canva_url": CANVA, "contact_id": entrega["contact_id"]}
    intentos = [
        otra.get(base),
        otra.put(base, json=cuerpo),
        _sube(otra, base),
        otra.put(base + "/paginas", json={"indices": [0, 1]}),
        otra.post(base + "/entregada"),
        _sube(otra, base + "/espacios/%s" % linea),
        otra.put(base + "/espacios/%s/paginas" % linea, json={"indices": [0, 1]}),
        otra.put(base + "/espacios/%s" % linea, json={"nombre": "Robado"}),
        otra.delete(base + "/espacios/%s" % linea),
    ]
    for r in intentos:
        # El mismo 404 que una que no existe: ni siquiera se le confirma que existe.
        assert r.status_code == 404, (r.request.method, r.request.url, r.text)
        assert r.json()["detail"] == "Entrega no encontrada"
    assert entrega["id"] not in [e["id"] for e in otra.get("/api/entregas").json()]


def test_la_autora_sigue_pudiendo_con_la_suya(autora, entrega):
    assert autora.get("/api/entregas/%d" % entrega["id"]).status_code == 200
    assert entrega["id"] in [e["id"] for e in autora.get("/api/entregas").json()]


def test_un_administrador_la_ve_y_la_edita(admin, entrega):
    base = "/api/entregas/%d" % entrega["id"]
    assert admin.get(base).status_code == 200
    r = admin.put(base, json={"titulo": "Corregida por admin", "canva_url": CANVA,
                              "contact_id": entrega["contact_id"]})
    assert r.status_code == 200 and r.json()["titulo"] == "Corregida por admin"
    assert entrega["id"] in [e["id"] for e in admin.get("/api/entregas").json()]


def test_la_entrega_queda_a_nombre_de_quien_la_creo(entrega, db, autora):
    fila = db.get(models.Entrega, entrega["id"])
    yo = autora.get("/api/auth/yo").json()
    creador = db.get(models.PanelUser, fila.panel_user_id)
    assert creador.email == yo["email"]


# --- 2. Las imágenes no se enumeran -----------------------------------------------------

def test_una_entrega_nueva_sirve_sus_imagenes_por_su_clave(autora, entrega):
    salida = _con_carrusel(autora, entrega["id"])
    urls = [salida["carrusel"], salida["portada"]] + [p["url"] for p in salida["paginas"]]
    for url in urls:
        assert CLAVE.match(url), url
        r = autora.get(url)
        assert r.status_code == 200 and "immutable" in r.headers["cache-control"]
    # Y por su número, ya no: eso es lo que se podía recorrer en bucle.
    for nombre in ("p0.jpg", "carrusel.gif", "og.jpg"):
        assert autora.get("/media/entregas/%d/%s" % (entrega["id"], nombre)).status_code == 404


def test_la_tarjeta_de_whatsapp_usa_la_clave(autora, entrega):
    _con_carrusel(autora, entrega["id"])
    html = autora.get("/p/" + entrega["slug"], headers={"user-agent": "WhatsApp/2"}).text
    imagen = html.split('property="og:image" content="')[1].split('"')[0]
    assert re.search(r"/media/e/[0-9a-f]{32}/og\.jpg\?v=", imagen), imagen


def test_un_espacio_nuevo_tambien_va_por_la_clave(autora, entrega, linea):
    salida = _con_carrusel(autora, entrega["id"], linea)
    esp = next(e for e in salida["espacios"] if e["linea"] == linea)
    for url in [esp["carrusel"]] + [p["url"] for p in esp["paginas"]]:
        assert CLAVE.match(url) and "/espacios/%s/" % linea in url, url
        assert autora.get(url).status_code == 200
    legado = "/media/entregas/%d/espacios/%s/p0.jpg" % (entrega["id"], linea)
    assert autora.get(legado).status_code == 404


def test_una_entrega_antigua_sin_clave_sigue_por_su_ruta(autora, entrega, linea, db):
    """Sus correos ya se enviaron con `/media/entregas/<id>/…`: no se pueden romper."""
    _con_carrusel(autora, entrega["id"])
    _con_carrusel(autora, entrega["id"], linea)
    fila = db.get(models.Entrega, entrega["id"])
    clave = fila.clave
    fila.clave = None
    db.commit()

    salida = autora.get("/api/entregas/%d" % entrega["id"]).json()
    assert salida["carrusel"].startswith("/media/entregas/%d/carrusel.gif?v=" % entrega["id"])
    assert salida["paginas"][0]["url"].startswith("/media/entregas/%d/" % entrega["id"])
    esp = next(e for e in salida["espacios"] if e["linea"] == linea)
    assert esp["carrusel"].startswith(
        "/media/entregas/%d/espacios/%s/carrusel.gif?v=" % (entrega["id"], linea))
    assert autora.get(salida["carrusel"]).status_code == 200
    assert autora.get(esp["carrusel"]).status_code == 200
    # La clave que tuvo ya no abre nada: no es de ninguna entrega.
    assert autora.get("/media/e/%s/p0.jpg" % clave).status_code == 404


@pytest.mark.parametrize("ruta", [
    "/media/e/%s/p0.jpg" % ("A" * 32),
    "/media/e/%s/p0.jpg" % ("a" * 31),
    "/media/e/%s/p0.jpg" % ("a" * 33),
    "/media/e/%s/p0.jpg" % ("0" * 32),
    "/media/e/../p0.jpg",
    "/media/e/%2e%2e/p0.jpg",
    "/media/e/{clave}/../../secreto.jpg",
    "/media/e/{clave}/..%2f..%2fdatabase.db",
    "/media/e/{clave}/CARRUSEL.GIF",
    "/media/e/{clave}/espacios/%2e%2e/p0.jpg",
    "/media/e/{clave}/espacios/{linea}/subida.json",
])
def test_la_ruta_por_clave_rechaza_lo_que_no_es_suyo(autora, entrega, linea, db, ruta):
    _con_carrusel(autora, entrega["id"])
    _con_carrusel(autora, entrega["id"], linea)
    clave = db.get(models.Entrega, entrega["id"]).clave
    r = autora.get(ruta.format(clave=clave, linea=linea))
    assert r.status_code in (404, 405), ruta


# --- 3. Límites de subida ---------------------------------------------------------------

def _png_enorme() -> bytes:
    """Pocos KB en disco que declaran 48 megapíxeles: lo que hay que parar ANTES de decodificar."""
    from PIL import Image
    salida = io.BytesIO()
    Image.new("1", (8000, 6000)).save(salida, "PNG")
    return salida.getvalue()


def test_una_imagen_de_demasiados_pixeles_se_rechaza(autora, entrega):
    datos = _png_enorme()
    assert len(datos) < paginas.LIMITE_BYTES
    r = autora.post("/api/entregas/%d/paginas" % entrega["id"],
                    files={"fichero": ("bomba.png", io.BytesIO(datos), "image/png")})
    assert r.status_code == 400
    assert "píxeles" in r.json()["detail"]


def test_una_pagina_de_pdf_desmesurada_se_rasteriza_acotada():
    # 99 × 1500 puntos: a 1200 px de ancho saldría de 1200 × 18 182. Mismo largo que el MediaBox
    # original, para que la tabla xref del PDF siga cuadrando.
    pdf = _pdf(1).replace(b"/MediaBox [0 0 612 792]", b"/MediaBox [0 0 99 1500]")
    pagina = paginas.paginas_de_pdf(pdf)[0]
    assert max(pagina.ancho, pagina.alto) <= paginas.LADO_MAXIMO
    assert pagina.ancho * pagina.alto <= paginas.LIMITE_PIXELES


def test_demasiados_ficheros_se_rechazan_sin_leerlos(autora, entrega, monkeypatch):
    leidos = []
    monkeypatch.setattr(galeria.mod_paginas, "lee",
                        lambda datos, *a, **k: leidos.append(1) or [])
    ficheros = [("fichero", ("p%d.pdf" % i, io.BytesIO(b"%PDF-"), "application/pdf"))
                for i in range(paginas.LIMITE_PAGINAS + 1)]
    r = autora.post("/api/entregas/%d/paginas" % entrega["id"], files=ficheros)
    assert r.status_code == 400
    assert leidos == [], "leyó los ficheros antes de contar cuántos eran"


def test_una_subida_normal_de_imagenes_sigue_funcionando(autora, entrega):
    from PIL import Image
    ficheros = []
    for i in range(2):
        b = io.BytesIO()
        Image.new("RGB", (1600, 900), (i * 90, 40, 80)).save(b, "PNG")
        ficheros.append(("fichero", ("img%d.png" % i, io.BytesIO(b.getvalue()), "image/png")))
    r = autora.post("/api/entregas/%d/paginas" % entrega["id"], files=ficheros)
    assert r.status_code == 200, r.text
    assert [p["ancho"] for p in r.json()["paginas"]] == [paginas.ANCHO_PAGINA] * 2


# --- 4. CSRF desde otro origen ----------------------------------------------------------

NUEVA = {"titulo": "X", "canva_url": CANVA}   # sin contacto: si pasa la guardia, da 400


def test_un_post_desde_un_origen_ajeno_se_rechaza(autora):
    r = autora.post("/api/entregas", json=NUEVA, headers={"Origin": "https://evil.example"})
    assert r.status_code == 403 and r.json()["detail"] == "Origen no permitido"


def test_un_subdominio_hermano_tampoco_pasa(autora):
    r = autora.put("/api/entregas/1", json=NUEVA,
                   headers={"Origin": "https://otro.ejemplo.test"})
    assert r.status_code == 403


@pytest.mark.parametrize("cabeceras", [
    {"Origin": "http://testserver"},          # el propio: el panel servido desde aquí
    {"Origin": "http://TESTSERVER"},
    {"Origin": "https://panel.ejemplo.test"},  # CORS_ORIGINS de conftest
    {},                                        # curl, scripts con X-Admin-Key
    {"Sec-Fetch-Site": "same-origin"},
])
def test_el_mismo_origen_los_permitidos_y_sin_origen_pasan(autora, cabeceras):
    r = autora.post("/api/entregas", json=NUEVA, headers=cabeceras)
    assert r.status_code == 400, r.text   # llegó a la validación de siempre


def test_sin_origin_pero_marcado_como_de_otro_sitio_se_rechaza(autora):
    for sitio in ("cross-site", "same-site"):
        r = autora.post("/api/entregas", json=NUEVA, headers={"Sec-Fetch-Site": sitio})
        assert r.status_code == 403, sitio


def test_leer_desde_otro_origen_no_cambia(autora):
    r = autora.get("/api/entregas", headers={"Origin": "https://evil.example"})
    assert r.status_code == 200
