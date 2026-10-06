"""
Pruebas de los espacios que acompañan a una entrega (004, servidor).

Lo que vigila este fichero, por orden de lo caro que sería romperlo:

1. **Independencia.** Rehacer las páginas de la principal no puede borrar las de un espacio, ni al
   revés, ni un espacio las de otro. Con las imágenes en la misma carpeta, `borra_entrega()` se
   llevaba por delante todo lo que tuviera nombre válido (research R1).
2. **`/media/.../espacios/{linea}/{fichero}` no sirve lo que no debe.** Ahora entran DOS trozos de
   ruta desde fuera, y los dos son entrada no confiable.
3. **«Estándar» lo decide el servidor** contra el catálogo (R8): un campo igual al de la línea se
   guarda vacío, y una fila sin nada propio desaparece.

La base de pruebas es de toda la sesión: aquí se crean una persona y unas líneas propias, con
nombres únicos, en vez de suponer qué hay sembrado.
"""

import io
import os
import secrets

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app import main as app_main
from app import models
from app.auth import sesion
from app.database import SessionLocal, engine
from app.mails.entregas import almacen
from app.migracion import migrar
from tests.test_entregas_api import _pdf

CANVA = "https://www.canva.com/design/PRINCIPAL/view"
CANVA_SERIE = "https://www.canva.com/design/SERIE/view"


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture(scope="module")
def cliente(db):
    usuario = models.PanelUser(email="esp-%s@ejemplo.test" % secrets.token_hex(4),
                               nombre="Eva", rol="comercial", activo=True)
    db.add(usuario)
    db.commit()
    c = TestClient(app_main.app)
    c.cookies.set(sesion.COOKIE, sesion.crear(usuario.id, usuario.email))
    return c


def _linea(db, nombre):
    linea = models.LineaNegocio(
        id="esp-%s" % secrets.token_hex(4), nombre=nombre,
        cobertura="Cobertura de serie", canva=CANVA_SERIE)
    db.add(linea)
    db.commit()
    return linea.id


@pytest.fixture(scope="module")
def linea(db):
    return _linea(db, "Pantalla de prueba")


@pytest.fixture(scope="module")
def otra_linea(db):
    return _linea(db, "Valla de prueba")


@pytest.fixture
def entrega(cliente, db):
    """Una entrega nueva por prueba: el estado de los espacios no se arrastra entre pruebas."""
    contacto = models.Contact(nombre="Cliente Espacios", email="c@ejemplo.test",
                              empresa="Espacios C.A.", token=secrets.token_urlsafe(24))
    db.add(contacto)
    db.commit()
    r = cliente.post("/api/entregas", json={
        "titulo": "Propuesta con espacios", "canva_url": CANVA, "contact_id": contacto.id})
    assert r.status_code == 200, r.text
    return r.json()


def _sube(cliente, entrega_id, linea=None, paginas=3, con_precio=False):
    ruta = "/api/entregas/%d" % entrega_id
    if linea:
        ruta += "/espacios/%s" % linea
    return cliente.post(ruta + "/paginas", files={
        "fichero": ("deck.pdf", io.BytesIO(_pdf(paginas, con_precio)), "application/pdf")})


def _elige(cliente, entrega_id, linea=None, indices=(0, 1), efecto="barrido"):
    ruta = "/api/entregas/%d" % entrega_id
    if linea:
        ruta += "/espacios/%s" % linea
    return cliente.put(ruta + "/paginas", json={"indices": list(indices), "efecto": efecto})


def _espacio(salida, linea):
    return next((e for e in salida["espacios"] if e["linea"] == linea), None)


def _media(db, entrega_id):
    """La raíz pública de sus ficheros: por su clave, no por su número (revisión de seguridad)."""
    return "/media/e/%s" % db.get(models.Entrega, entrega_id).clave


def _fichero(entrega_id, nombre, linea=None):
    return os.path.join(almacen.carpeta(entrega_id, crear=False, linea=linea), nombre)


# --- La tabla --------------------------------------------------------------------------

def test_la_tabla_existe_y_migrar_no_cambia_nada():
    assert "entrega_espacios" in inspect(engine).get_table_names()
    hecho = migrar(engine)
    assert hecho == {"columnas": [], "tablas": [], "indices": []}


def test_sin_espacios_la_salida_trae_una_lista_vacia(cliente, entrega):
    assert entrega["espacios"] == []
    assert cliente.get("/api/entregas/%d" % entrega["id"]).json()["espacios"] == []


# --- US1: el carrusel de un espacio ----------------------------------------------------

def test_subir_a_un_espacio_da_paginas_en_su_subcarpeta(cliente, entrega, linea, db):
    r = _sube(cliente, entrega["id"], linea)
    assert r.status_code == 200, r.text
    datos = r.json()
    assert len(datos["paginas"]) == 3
    assert datos["minimo"] == 2 and datos["maximo"] == 4
    assert "imagen" in datos["aviso"]
    url = datos["paginas"][0]["url"]
    assert url.startswith("%s/espacios/%s/p0.jpg?v=" % (_media(db, entrega["id"]), linea))
    assert cliente.get(url).status_code == 200


def test_elegir_arma_el_carrusel_del_espacio(cliente, entrega, linea, db):
    _sube(cliente, entrega["id"], linea)
    r = _elige(cliente, entrega["id"], linea, indices=[2, 0], efecto="fundido")
    assert r.status_code == 200, r.text
    salida = r.json()
    esp = _espacio(salida, linea)
    assert esp["efecto"] == "fundido"
    assert esp["carrusel"].startswith(
        "%s/espacios/%s/carrusel.gif?v=" % (_media(db, entrega["id"]), linea))
    assert [p["orden"] for p in esp["paginas"]] == [0, 1]
    assert esp["paginas"][0]["url"].split("?")[0].endswith("/espacios/%s/p2.jpg" % linea)
    assert esp["paginas"][0]["ancho"] > 0 and esp["paginas"][0]["alto"] > 0
    # Sin campos propios: todo lo demás sale del catálogo.
    assert esp["canva_url"] is None and esp["nombre"] is None and esp["cobertura"] is None
    # La principal no tiene carrusel: armar el del espacio no se lo inventa.
    assert salida["carrusel"] is None
    gif = cliente.get(esp["carrusel"])
    assert gif.status_code == 200 and gif.content[:3] == b"GIF"


def test_el_efecto_desconocido_se_guarda_como_el_que_salio(cliente, entrega, linea):
    _sube(cliente, entrega["id"], linea)
    esp = _espacio(_elige(cliente, entrega["id"], linea, efecto="remolino").json(), linea)
    assert esp["carrusel"] and esp["efecto"] == "barrido"


def test_el_aviso_de_precio_llega_a_las_paginas_elegidas(cliente, entrega, linea):
    r = _sube(cliente, entrega["id"], linea, con_precio=True)
    assert [p["aviso_precio"] for p in r.json()["paginas"]] == [False, True, False]
    esp = _espacio(_elige(cliente, entrega["id"], linea, indices=[1, 0]).json(), linea)
    assert [p["aviso_precio"] for p in esp["paginas"]] == [True, False]


def test_los_limites_son_los_de_la_principal(cliente, entrega, linea):
    _sube(cliente, entrega["id"], linea)
    # Los mismos códigos que la principal: el mínimo lo valida el esquema (422)…
    assert _elige(cliente, entrega["id"], linea, indices=[0]).status_code == 422
    assert _elige(cliente, entrega["id"], linea, indices=[0, 1, 2, 0, 1]).status_code == 422
    # …y lo demás, la ruta (400) con su mensaje.
    r = _elige(cliente, entrega["id"], linea, indices=[0, 0])
    assert r.status_code == 400 and "repetida" in r.json()["detail"]
    r = _elige(cliente, entrega["id"], linea, indices=[0, 9])
    assert r.status_code == 400 and "vuelve a subir" in r.json()["detail"]
    r = cliente.post("/api/entregas/%d/espacios/%s/paginas" % (entrega["id"], linea),
                     files={"fichero": ("notas.txt", io.BytesIO(b"hola"), "text/plain")})
    assert r.status_code == 400 and "PDF" in r.json()["detail"]


def test_rehacer_la_principal_no_toca_el_espacio(cliente, entrega, linea):
    _sube(cliente, entrega["id"], linea)
    antes = _espacio(_elige(cliente, entrega["id"], linea).json(), linea)
    _sube(cliente, entrega["id"])
    _elige(cliente, entrega["id"])
    _sube(cliente, entrega["id"], paginas=2)   # la principal vuelve a vaciar su carpeta
    for nombre in ("p0.jpg", "p1.jpg", "p2.jpg", "carrusel.gif"):
        assert os.path.isfile(_fichero(entrega["id"], nombre, linea)), nombre
    despues = _espacio(cliente.get("/api/entregas/%d" % entrega["id"]).json(), linea)
    assert despues["carrusel"] == antes["carrusel"]


def test_rehacer_un_espacio_no_toca_la_principal_ni_otro_espacio(
        cliente, entrega, linea, otra_linea):
    _sube(cliente, entrega["id"])
    principal = _elige(cliente, entrega["id"]).json()
    _sube(cliente, entrega["id"], otra_linea)
    otro = _espacio(_elige(cliente, entrega["id"], otra_linea).json(), otra_linea)
    marcas = {n: os.stat(_fichero(entrega["id"], n)).st_mtime_ns
              for n in ("p0.jpg", "carrusel.gif", "og.jpg")}

    _sube(cliente, entrega["id"], linea, paginas=4)
    salida = _elige(cliente, entrega["id"], linea, indices=[3, 2, 1]).json()

    assert {n: os.stat(_fichero(entrega["id"], n)).st_mtime_ns for n in marcas} == marcas
    assert salida["carrusel"] == principal["carrusel"]
    assert salida["portada"] == principal["portada"]
    assert [p["url"] for p in salida["paginas"]] == [p["url"] for p in principal["paginas"]]
    assert _espacio(salida, otra_linea)["carrusel"] == otro["carrusel"]
    assert os.path.isfile(_fichero(entrega["id"], "p2.jpg", otra_linea))
    # Un espacio no tiene portada: la tarjeta de WhatsApp es de la principal.
    assert not os.path.exists(_fichero(entrega["id"], "og.jpg", linea))


def test_resubir_un_espacio_vacia_solo_su_subcarpeta(cliente, entrega, linea):
    _sube(cliente, entrega["id"], linea, paginas=4)
    _sube(cliente, entrega["id"], linea, paginas=2)
    assert os.path.isfile(_fichero(entrega["id"], "p1.jpg", linea))
    assert not os.path.exists(_fichero(entrega["id"], "p3.jpg", linea))


# --- Acceso -----------------------------------------------------------------------------

def test_sin_sesion_nada(entrega, linea):
    anonimo = TestClient(app_main.app)
    base = "/api/entregas/%d/espacios/%s" % (entrega["id"], linea)
    assert anonimo.post(base + "/paginas", files={
        "fichero": ("deck.pdf", io.BytesIO(_pdf(2)), "application/pdf")}).status_code == 401
    assert anonimo.put(base + "/paginas", json={"indices": [0, 1]}).status_code == 401
    assert anonimo.put(base, json={"nombre": "X"}).status_code == 401
    assert anonimo.delete(base).status_code == 401


@pytest.mark.parametrize("linea_mala", ["no-existe-en-el-catalogo", "MAYUSCULAS", "a_b"])
def test_una_linea_que_no_existe_da_404(cliente, entrega, linea_mala):
    base = "/api/entregas/%d/espacios/%s" % (entrega["id"], linea_mala)
    assert _sube(cliente, entrega["id"], linea_mala).status_code == 404
    assert cliente.put(base + "/paginas", json={"indices": [0, 1]}).status_code == 404
    assert cliente.put(base, json={"nombre": "X"}).status_code == 404
    assert cliente.delete(base).status_code == 404


def test_una_entrega_que_no_existe_da_404(cliente, linea):
    base = "/api/entregas/999999/espacios/%s" % linea
    assert _sube(cliente, 999999, linea).status_code == 404
    assert cliente.put(base + "/paginas", json={"indices": [0, 1]}).status_code == 404
    assert cliente.put(base, json={"nombre": "X"}).status_code == 404
    assert cliente.delete(base).status_code == 404


# --- US2: lo propio de cada espacio ------------------------------------------------------

def _guarda(cliente, entrega_id, linea, **campos):
    return cliente.put("/api/entregas/%d/espacios/%s" % (entrega_id, linea), json=campos)


def test_guardar_textos_y_enlace_propios(cliente, entrega, linea):
    r = _guarda(cliente, entrega["id"], linea, canva_url="https://canva.link/propio",
                nombre="Pantalla a medida", cobertura="Solo Chacao")
    assert r.status_code == 200, r.text
    esp = _espacio(r.json(), linea)
    assert esp == {"linea": linea, "canva_url": "https://canva.link/propio",
                   "nombre": "Pantalla a medida", "cobertura": "Solo Chacao",
                   "efecto": None, "carrusel": None, "paginas": []}
    # Solo cambia lo que llega: la cobertura y el enlace se quedan.
    esp = _espacio(_guarda(cliente, entrega["id"], linea, nombre="Otro nombre").json(), linea)
    assert esp["nombre"] == "Otro nombre"
    assert esp["cobertura"] == "Solo Chacao" and esp["canva_url"] == "https://canva.link/propio"


def test_un_valor_igual_al_del_catalogo_queda_estandar(cliente, entrega, linea):
    r = _guarda(cliente, entrega["id"], linea, nombre="Pantalla de prueba",
                cobertura="Solo Chacao", canva_url=CANVA_SERIE)
    esp = _espacio(r.json(), linea)
    assert esp["nombre"] is None and esp["canva_url"] is None
    assert esp["cobertura"] == "Solo Chacao"


def test_vaciar_el_ultimo_campo_propio_borra_la_fila(cliente, entrega, linea, db):
    _guarda(cliente, entrega["id"], linea, cobertura="Solo Chacao")
    r = _guarda(cliente, entrega["id"], linea, cobertura="")
    assert r.status_code == 200
    assert r.json()["espacios"] == []
    assert db.query(models.EntregaEspacio).filter_by(
        entrega_id=entrega["id"], linea_id=linea).count() == 0


def test_con_carrusel_la_fila_sobrevive_sin_textos(cliente, entrega, linea):
    _sube(cliente, entrega["id"], linea)
    _elige(cliente, entrega["id"], linea)
    _guarda(cliente, entrega["id"], linea, nombre="Propio")
    esp = _espacio(_guarda(cliente, entrega["id"], linea, nombre="").json(), linea)
    assert esp["nombre"] is None and esp["carrusel"]


def test_un_enlace_sin_https_se_rechaza_con_el_mensaje_de_la_principal(cliente, entrega, linea):
    r = _guarda(cliente, entrega["id"], linea, canva_url="canva.link/abc123")
    assert r.status_code == 400
    assert r.json()["detail"] == "Falta el https:// al principio — prueba con https://canva.link/abc123"
    r = _guarda(cliente, entrega["id"], linea, canva_url="ftp://canva.link/abc123")
    assert r.status_code == 400
    assert r.json()["detail"] == "El enlace tiene que empezar por https://"


def test_los_textos_tienen_su_limite(cliente, entrega, linea):
    assert _guarda(cliente, entrega["id"], linea, nombre="x" * 121).status_code == 422
    assert _guarda(cliente, entrega["id"], linea, cobertura="x" * 201).status_code == 422
    assert _guarda(cliente, entrega["id"], linea,
                   canva_url="https://canva.link/" + "x" * 500).status_code == 422


def test_volver_al_estandar_borra_la_fila_y_conserva_las_imagenes(cliente, entrega, linea):
    _sube(cliente, entrega["id"], linea)
    esp = _espacio(_elige(cliente, entrega["id"], linea).json(), linea)
    _guarda(cliente, entrega["id"], linea, nombre="Propio")
    r = cliente.delete("/api/entregas/%d/espacios/%s" % (entrega["id"], linea))
    assert r.status_code == 200
    assert r.json()["espacios"] == []
    # Un correo ya enviado puede apuntar a ellas (FR-414).
    assert cliente.get(esp["carrusel"]).status_code == 200
    assert cliente.get(esp["paginas"][0]["url"]).status_code == 200


def test_volver_al_estandar_sin_fila_tambien_responde(cliente, entrega, linea):
    r = cliente.delete("/api/entregas/%d/espacios/%s" % (entrega["id"], linea))
    assert r.status_code == 200 and r.json()["espacios"] == []


# --- /media de los espacios no sirve lo que no debe -----------------------------------

@pytest.mark.parametrize("linea_mala, fichero", [
    ("..", "p0.jpg"),
    ("..%2f..", "p0.jpg"),
    ("%2e%2e", "p0.jpg"),
    ("MAYUSCULAS", "p0.jpg"),
    ("{linea}", "../p0.jpg"),
    ("{linea}", "..%2f..%2f..%2fdatabase.db"),
    ("{linea}", "CARRUSEL.GIF"),
    ("{linea}", "carrusel.exe"),
    ("{linea}", "subida.json"),
])
def test_media_del_espacio_rechaza_lo_que_no_es_suyo(cliente, entrega, linea, db, linea_mala,
                                                    fichero):
    _sube(cliente, entrega["id"], linea)
    r = cliente.get("%s/espacios/%s/%s"
                    % (_media(db, entrega["id"]), linea_mala.format(linea=linea), fichero))
    assert r.status_code in (404, 405), "debería haber rechazado %r/%r" % (linea_mala, fichero)


def test_una_linea_con_puntos_no_sale_de_la_carpeta_del_espacio(cliente, entrega, linea):
    """Con la principal subida, `..` como línea apuntaría a SUS páginas. La forma lo para."""
    _sube(cliente, entrega["id"])
    _sube(cliente, entrega["id"], linea)
    assert almacen.resuelve(entrega["id"], "p0.jpg") is not None
    for mala in ("..", ".", "../..", "../../%d" % entrega["id"]):
        assert almacen.resuelve(entrega["id"], "p0.jpg", linea=mala) is None, mala
    for mala in ("..", "MAYUS", "a_b", "a/b", "-guion", "x" * 61, ""):
        assert not almacen.linea_valida(mala), mala
    assert almacen.linea_valida(linea) and almacen.linea_valida("led-chacao-2")


def test_la_guardia_de_destino_del_espacio(cliente, entrega, linea, monkeypatch):
    """
    Como en la principal: sin los filtros de forma —del fichero **y** de la línea—, la guardia de
    destino sigue cerrando. Con ficheros reales justo fuera, o no se prueba nada.
    """
    _sube(cliente, entrega["id"])
    _sube(cliente, entrega["id"], linea)
    fuera = _fichero(entrega["id"], "secreto.jpg")
    with open(fuera, "wb") as f:
        f.write(b"no se sirve")
    try:
        monkeypatch.setattr(almacen, "nombre_valido", lambda nombre: True)
        monkeypatch.setattr(almacen, "linea_valida", lambda linea: True)
        assert almacen.resuelve(entrega["id"], "../../secreto.jpg", linea=linea) is None
        for mala in ("..", "../..", "x/../.."):
            assert almacen.resuelve(entrega["id"], "p0.jpg", linea=mala) is None, mala
        assert almacen.resuelve(entrega["id"], "p0.jpg", linea=linea) is not None
    finally:
        os.remove(fuera)


def test_media_del_espacio_sirve_una_pagina_de_verdad(cliente, entrega, linea, db):
    _sube(cliente, entrega["id"], linea)
    r = cliente.get("%s/espacios/%s/p0.jpg" % (_media(db, entrega["id"]), linea))
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")
    assert "immutable" in r.headers["cache-control"]


# --- Revision de seguridad (2026-10-06) ----------------------------------------------------------

def test_dos_guardados_a_la_vez_del_mismo_espacio_no_dan_500(cliente, entrega, linea, monkeypatch):
    """
    El compositor guarda cada campo por su lado: el nombre y la cobertura de un espacio nuevo
    pueden llegar a la vez, los dos ven que no hay fila y los dos la crean. El segundo chocaba con
    UNIQUE(entrega_id, linea_id) -un 500- y su valor se perdia. Se simula haciendo que la primera
    busqueda de la fila no vea la que ya creo el otro guardado.
    """
    from app.mails.entregas import espacios
    ruta = "/api/entregas/%d/espacios/%s" % (entrega["id"], linea)
    assert cliente.put(ruta, json={"nombre": "Nombre propio (prueba)"}).status_code == 200
    real, vistas = espacios._fila, []

    def _fila_sin_ver_la_primera_vez(db, entrega_id, linea_id):
        vistas.append(1)
        return None if len(vistas) == 1 else real(db, entrega_id, linea_id)

    monkeypatch.setattr(espacios, "_fila", _fila_sin_ver_la_primera_vez)
    r = cliente.put(ruta, json={"cobertura": "Cobertura propia (prueba)"})
    assert r.status_code == 200, r.text
    propio = _espacio(r.json(), linea)
    assert propio["nombre"] == "Nombre propio (prueba)"
    assert propio["cobertura"] == "Cobertura propia (prueba)"


def test_una_imagen_ilegible_es_un_400_y_no_un_500(cliente, entrega, linea):
    # Cabecera de PNG (pasa el filtro de tipo) y basura detras: Pillow no la puede abrir.
    rota = bytes([0x89]) + b"PNG" + bytes([13, 10, 26, 10]) + b"esto no es una imagen" * 20
    r = cliente.post("/api/entregas/%d/espacios/%s/paginas" % (entrega["id"], linea),
                     files={"fichero": ("rota.png", io.BytesIO(rota), "image/png")})
    assert r.status_code == 400
    r = cliente.post("/api/entregas/%d/paginas" % entrega["id"],
                     files={"fichero": ("rota.png", io.BytesIO(rota), "image/png")})
    assert r.status_code == 400, "la principal usa la misma lectura"


@pytest.mark.parametrize("nombre", ["p0.jpg" + chr(10), "carrusel.gif" + chr(10)])
def test_un_salto_de_linea_al_final_no_es_un_nombre_valido(nombre):
    assert not almacen.nombre_valido(nombre)


def test_un_salto_de_linea_al_final_no_es_una_linea_valida():
    assert not almacen.linea_valida("mercedes" + chr(10))


def test_leer_la_entrega_trae_sus_espacios_con_el_carrusel_versionado(cliente, entrega, linea):
    """Lo que necesita el compositor para reabrir una entrega en otra sesion (US4)."""
    _sube(cliente, entrega["id"], linea)
    _elige(cliente, entrega["id"], linea)
    cliente.put("/api/entregas/%d/espacios/%s" % (entrega["id"], linea), json={"cobertura": "Cobertura (prueba US4)"})
    leida = _espacio(cliente.get("/api/entregas/%d" % entrega["id"]).json(), linea)
    assert leida["cobertura"] == "Cobertura (prueba US4)"
    assert "/espacios/%s/carrusel.gif?v=" % linea in leida["carrusel"]
    assert len(leida["paginas"]) == 2


# --- El rotulo de la esquina y el texto corto de WhatsApp viajan con la entrega ------------------

def test_el_rotulo_y_el_texto_corto_se_guardan_con_la_entrega(cliente, entrega):
    ruta = "/api/entregas/%d" % entrega["id"]
    base = {"titulo": entrega["titulo"], "canva_url": entrega["canva_url"]}
    r = cliente.put(ruta, json=dict(base, rotulo="ROTULO DE PRUEBA", texto_corto="Corto de WhatsApp (prueba)"))
    assert r.status_code == 200, r.text
    leida = cliente.get(ruta).json()
    assert leida["rotulo"] == "ROTULO DE PRUEBA" and leida["texto_corto"] == "Corto de WhatsApp (prueba)"


def test_un_compositor_que_no_los_manda_no_los_borra(cliente, entrega):
    ruta = "/api/entregas/%d" % entrega["id"]
    base = {"titulo": entrega["titulo"], "canva_url": entrega["canva_url"]}
    cliente.put(ruta, json=dict(base, rotulo="ROTULO", texto_corto="Corto"))
    cliente.put(ruta, json=base)
    leida = cliente.get(ruta).json()
    assert leida["rotulo"] == "ROTULO" and leida["texto_corto"] == "Corto"
    cliente.put(ruta, json=dict(base, rotulo="", texto_corto=""))
    leida = cliente.get(ruta).json()
    assert leida["rotulo"] is None and leida["texto_corto"] is None


def test_el_rotulo_tiene_limite(cliente, entrega):
    base = {"titulo": entrega["titulo"], "canva_url": entrega["canva_url"]}
    r = cliente.put("/api/entregas/%d" % entrega["id"], json=dict(base, rotulo="x" * 121))
    assert r.status_code == 422
