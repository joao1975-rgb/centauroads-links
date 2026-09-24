"""
Pruebas de las entregas a medida (002, fase 2).

Lo que más importa de este fichero son dos cosas, y ninguna es un detalle técnico:

1. **Sin contacto no hay entrega.** Es la decisión que tomó el propietario con el riesgo delante:
   sin contacto no hay seguimiento ni aviso, y entonces la capacidad no sirve para lo que se
   construyó. Si esa regla se cae, se cae en silencio.

2. **`/media` no sirve lo que no debe.** Esa ruta recibe un nombre de fichero desde fuera. Aquí se
   le pasan los intentos de siempre —`../`, rutas absolutas, nombres con barra— y todos tienen que
   acabar en 404.

`conftest.py` ya apuntó DATABASE_URL y las claves a un directorio temporal antes de que esto se
importe, así que la aplicación se importa tal cual.
"""

import io
import os
import secrets

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import sesion
from app.database import SessionLocal
from app.mails.entregas import almacen

CANVA = "https://www.canva.com/design/EJEMPLO/view"


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture(scope="module")
def persona(db):
    """Alguien del equipo, con sesión. Sin esto la API entera responde 401, que es lo correcto."""
    usuario = models.PanelUser(email="ana@ejemplo.test", nombre="Ana", rol="comercial",
                               activo=True)
    db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


@pytest.fixture(scope="module")
def cliente(persona):
    c = TestClient(app_main.app)
    c.cookies.set(sesion.COOKIE, sesion.crear(persona.id, persona.email))
    return c


@pytest.fixture(scope="module")
def contacto(db):
    c = models.Contact(nombre="Cliente de Prueba", email="cliente@ejemplo.test",
                       empresa="Ejemplo C.A.", origen="whatsapp",
                       token=secrets.token_urlsafe(24))
    db.add(c)
    db.commit()
    db.refresh(c)
    return c


def _pdf(paginas=3, con_precio=False) -> bytes:
    """Un PDF mínimo pero real, escrito a mano: sin dependencias de generación."""
    textos = []
    for i in range(paginas):
        t = "Pagina %d de la propuesta" % (i + 1)
        if con_precio and i == 1:
            t = "Tarifa mensual USD 1500"
        textos.append(t)

    contenidos = []
    for t in textos:
        contenidos.append(
            b"BT /F1 24 Tf 40 500 Td (" + t.encode("latin-1", "replace") + b") Tj ET")

    cuerpo = b"%PDF-1.4\n"
    desplazamientos = []

    def agrega(n, datos):
        nonlocal cuerpo
        desplazamientos.append(len(cuerpo))
        cuerpo += b"%d 0 obj\n" % n + datos + b"\nendobj\n"

    hijos = " ".join("%d 0 R" % (4 + i * 2) for i in range(paginas)).encode()
    agrega(1, b"<< /Type /Catalog /Pages 2 0 R >>")
    agrega(2, b"<< /Type /Pages /Kids [" + hijos + b"] /Count %d >>" % paginas)
    agrega(3, b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for i in range(paginas):
        agrega(4 + i * 2,
               b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
               b"/Resources << /Font << /F1 3 0 R >> >> /Contents %d 0 R >>" % (5 + i * 2))
        flujo = contenidos[i]
        agrega(5 + i * 2, b"<< /Length %d >>\nstream\n" % len(flujo) + flujo + b"\nendstream")

    inicio = len(cuerpo)
    total = 3 + paginas * 2
    cuerpo += b"xref\n0 %d\n0000000000 65535 f \n" % (total + 1)
    for d in desplazamientos:
        cuerpo += b"%010d 00000 n \n" % d
    cuerpo += (b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n"
               % (total + 1, inicio))
    return cuerpo


# --- Sin sesión, nada -----------------------------------------------------------------

def test_sin_sesion_la_api_no_responde():
    anonimo = TestClient(app_main.app)
    r = anonimo.post("/api/entregas", json={"titulo": "X", "canva_url": CANVA})
    assert r.status_code == 401


# --- El contacto es obligatorio -------------------------------------------------------

def test_sin_contacto_no_se_crea_la_entrega(cliente):
    r = cliente.post("/api/entregas", json={"titulo": "Propuesta", "canva_url": CANVA})
    assert r.status_code == 400
    assert "contacto" in r.json()["detail"].lower()


def test_con_un_contacto_que_no_existe_tampoco(cliente):
    r = cliente.post("/api/entregas",
                     json={"titulo": "Propuesta", "canva_url": CANVA, "contact_id": 999999})
    assert r.status_code == 404


def test_el_contacto_puede_crearse_en_el_mismo_paso(cliente):
    r = cliente.post("/api/entregas", json={
        "titulo": "Propuesta con contacto nuevo", "canva_url": CANVA,
        "contacto": {"nombre": "Nuevo Cliente", "email": "nuevo@ejemplo.test",
                     "empresa": "Nueva Empresa C.A."},
    })
    assert r.status_code == 200, r.text
    assert r.json()["contacto_nombre"] == "Nuevo Cliente"


def test_sin_empresa_no_se_crea_la_entrega(cliente):
    """
    El correo saluda por el nombre y el texto habla de la empresa. Una propuesta
    «personalizada» que no nombra a quién va dirigida no lo es (decisión del propietario,
    2026-09-24).
    """
    r = cliente.post("/api/entregas", json={
        "titulo": "Sin empresa", "canva_url": CANVA,
        "contacto": {"nombre": "Alguien", "email": "alguien@ejemplo.test"},
    })
    assert r.status_code == 400
    assert "empresa" in r.json()["detail"].lower()


def test_un_contacto_antiguo_sin_empresa_se_rechaza_con_su_nombre(cliente, db):
    """
    Los contactos de antes de esta regla pueden no tener empresa. No se inventa: se para y se
    dice de quién falta, que es lo único que permite arreglarlo.
    """
    viejo = models.Contact(nombre="Contacto Antiguo", email="antiguo@ejemplo.test",
                           empresa="", token=secrets.token_urlsafe(24))
    db.add(viejo)
    db.commit()
    db.refresh(viejo)
    r = cliente.post("/api/entregas", json={
        "titulo": "Con contacto antiguo", "canva_url": CANVA, "contact_id": viejo.id})
    assert r.status_code == 400
    assert "Contacto Antiguo" in r.json()["detail"]


# --- Crear una entrega ----------------------------------------------------------------

@pytest.fixture(scope="module")
def entrega(cliente, contacto):
    r = cliente.post("/api/entregas", json={
        "titulo": "Propuesta Cafetería Ejemplo", "canva_url": CANVA,
        "texto": "Preparamos esto para ustedes.", "servicios": "led,mercedes",
        "contact_id": contacto.id,
    })
    assert r.status_code == 200, r.text
    return r.json()


def test_la_entrega_nace_con_su_enlace_propio(entrega):
    assert entrega["slug"].startswith("e")
    assert entrega["enlace"] == "/p/" + entrega["slug"]
    assert entrega["estado"] == "borrador"


def test_el_enlace_corto_del_acortador_lleva_a_la_presentacion(cliente, entrega):
    """La fila en `links` es normal: el acortador la resuelve sin saber que es una entrega."""
    r = cliente.get("/" + entrega["slug"], follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == CANVA


# --- Las páginas ----------------------------------------------------------------------

def test_un_fichero_que_no_es_pdf_ni_imagen_se_rechaza(cliente, entrega):
    r = cliente.post("/api/entregas/%d/paginas" % entrega["id"],
                     files={"fichero": ("notas.txt", io.BytesIO(b"hola"), "text/plain")})
    assert r.status_code == 400
    assert "PDF" in r.json()["detail"]


def test_el_pdf_se_convierte_en_paginas_elegibles(cliente, entrega):
    r = cliente.post("/api/entregas/%d/paginas" % entrega["id"],
                     files={"fichero": ("deck.pdf", io.BytesIO(_pdf(3)), "application/pdf")})
    assert r.status_code == 200, r.text
    datos = r.json()
    assert len(datos["paginas"]) == 3
    assert datos["minimo"] == 2 and datos["maximo"] == 4
    # La advertencia del principio IV tiene que llegar a la interfaz, no quedarse en el plan.
    assert "imagen" in datos["aviso"]


def test_avisa_de_un_precio_escrito_como_texto(cliente, entrega):
    r = cliente.post("/api/entregas/%d/paginas" % entrega["id"],
                     files={"fichero": ("deck.pdf", io.BytesIO(_pdf(3, con_precio=True)),
                                        "application/pdf")})
    assert r.status_code == 200, r.text
    avisos = [p["aviso_precio"] for p in r.json()["paginas"]]
    assert avisos[1] is True, "la página con «USD 1500» debería avisar"
    assert avisos[0] is False, "una página sin precio no debe avisar"


def test_menos_de_dos_paginas_no_es_un_carrusel(cliente, entrega):
    cliente.post("/api/entregas/%d/paginas" % entrega["id"],
                 files={"fichero": ("deck.pdf", io.BytesIO(_pdf(3)), "application/pdf")})
    r = cliente.put("/api/entregas/%d/paginas" % entrega["id"], json={"indices": [0]})
    assert r.status_code == 422


def test_elegir_paginas_arma_el_carrusel_y_la_portada(cliente, entrega):
    cliente.post("/api/entregas/%d/paginas" % entrega["id"],
                 files={"fichero": ("deck.pdf", io.BytesIO(_pdf(3)), "application/pdf")})
    r = cliente.put("/api/entregas/%d/paginas" % entrega["id"], json={"indices": [2, 0]})
    assert r.status_code == 200, r.text
    datos = r.json()
    assert datos["carrusel"] and datos["portada"]
    assert [p["orden"] for p in datos["paginas"]] == [0, 1]
    # El orden es el que eligió la persona, no el del PDF. Se compara solo la ruta: la dirección
    # lleva además una marca de versión (?v=...) para que al rehacer el carrusel no se sirva el
    # de la caché.
    assert datos["paginas"][0]["url"].split("?")[0].endswith("p2.jpg")


def test_un_enlace_sin_https_no_se_guarda(cliente):
    """
    Canva enseña sus enlaces cortos SIN esquema —«canva.link/xyz»— y así se copian. Guardado tal
    cual, la redirección de /p/{slug} lo resuelve **relativo**: el cliente acaba en
    /p/canva.link/xyz y un 404, con la propuesta ya enviada y el enlace ya repartido.
    """
    r = cliente.post("/api/entregas", json={
        "titulo": "Sin esquema", "canva_url": "canva.link/jmkzpcozb78dd35",
        "contacto": {"nombre": "Quien Sea", "empresa": "Empresa C.A."}})
    assert r.status_code == 422
    assert "https" in r.text


def test_un_enlace_con_https_si_se_guarda(cliente):
    """Cerrar la puerta no puede cerrarla a quien tiene que pasar."""
    r = cliente.post("/api/entregas", json={
        "titulo": "Con esquema", "canva_url": CANVA,
        "contacto": {"nombre": "Quien Sea", "empresa": "Empresa C.A."}})
    assert r.status_code == 200, r.text


def test_el_efecto_elegido_llega_al_carrusel(cliente, entrega):
    """
    Que `arma()` sepa hacer siete efectos no sirve de nada si la ruta no le pasa el que se pidio.
    Ese hueco existio: se elegia uno en el panel y siempre salia barrido, y ninguna prueba se
    enteraba porque todas miraban `arma()` por su cuenta.
    """
    cliente.post("/api/entregas/%d/paginas" % entrega["id"],
                 files={"fichero": ("deck.pdf", io.BytesIO(_pdf(3)), "application/pdf")})
    gifs = {}
    for efecto in ("corte", "fundido", "zoom"):
        cliente.put("/api/entregas/%d/paginas" % entrega["id"],
                    json={"indices": [0, 1, 2], "efecto": efecto})
        with open(almacen.resuelve(entrega["id"], "carrusel.gif"), "rb") as f:
            gifs[efecto] = f.read()
    assert len(set(gifs.values())) == 3, (
        "dos efectos distintos dieron el mismo GIF: el elegido no esta llegando al carrusel")


def test_al_rehacer_el_carrusel_cambia_su_direccion(cliente, entrega):
    """
    El fichero se reescribe con el MISMO nombre y se sirve como `immutable` a un año. Si la
    dirección no cambiara, el navegador —y el proxy de imágenes de Gmail— no volverían a pedirlo
    nunca: se eligen otras páginas, el servidor arma el carrusel nuevo, y el correo sigue
    enseñando el anterior. Pasó, y se vio porque en la vista previa salía una página que ni
    siquiera estaba elegida.
    """
    cliente.post("/api/entregas/%d/paginas" % entrega["id"],
                 files={"fichero": ("deck.pdf", io.BytesIO(_pdf(3)), "application/pdf")})
    primera = cliente.put("/api/entregas/%d/paginas" % entrega["id"],
                          json={"indices": [0, 1], "efecto": "corte"}).json()["carrusel"]
    segunda = cliente.put("/api/entregas/%d/paginas" % entrega["id"],
                          json={"indices": [0, 1, 2], "efecto": "fundido"}).json()["carrusel"]
    assert primera != segunda, (
        "la dirección del carrusel no cambió al rehacerlo: se servirá el viejo desde la caché")


def test_la_direccion_del_carrusel_sigue_sirviendo_el_fichero(cliente, entrega):
    """La marca de versión no puede romper la descarga: es una query, no parte del nombre."""
    cliente.post("/api/entregas/%d/paginas" % entrega["id"],
                 files={"fichero": ("deck.pdf", io.BytesIO(_pdf(3)), "application/pdf")})
    url = cliente.put("/api/entregas/%d/paginas" % entrega["id"],
                      json={"indices": [0, 1]}).json()["carrusel"]
    assert "?v=" in url
    r = cliente.get(url)
    assert r.status_code == 200
    assert r.content[:3] == b"GIF"


def test_un_efecto_que_no_existe_no_deja_sin_carrusel(cliente, entrega):
    """
    Mejor una transicion distinta de la pedida que una entrega sin propuesta que mandar.
    """
    cliente.post("/api/entregas/%d/paginas" % entrega["id"],
                 files={"fichero": ("deck.pdf", io.BytesIO(_pdf(3)), "application/pdf")})
    r = cliente.put("/api/entregas/%d/paginas" % entrega["id"],
                    json={"indices": [0, 1], "efecto": "remolino"})
    assert r.status_code == 200, r.text
    assert r.json()["carrusel"]


def test_el_carrusel_entra_en_presupuesto(cliente, entrega):
    """~1 MB por pieza. Un correo que tarda en cargar no lo lee nadie."""
    cliente.post("/api/entregas/%d/paginas" % entrega["id"],
                 files={"fichero": ("deck.pdf", io.BytesIO(_pdf(4)), "application/pdf")})
    cliente.put("/api/entregas/%d/paginas" % entrega["id"], json={"indices": [0, 1, 2, 3]})
    destino = almacen.resuelve(entrega["id"], "carrusel.gif")
    assert destino, "no se escribió el carrusel"
    assert os.path.getsize(destino) <= 1_000_000


# --- /media no sirve lo que no debe ---------------------------------------------------

@pytest.mark.parametrize("nombre", [
    "../../../etc/passwd",
    "..%2f..%2fdatabase.db",
    "/etc/passwd",
    "carrusel.gif/../../../secreto.txt",
    "CARRUSEL.GIF",
    "carrusel.exe",
])
def test_media_rechaza_los_nombres_que_no_son_suyos(cliente, entrega, nombre):
    r = cliente.get("/media/entregas/%d/%s" % (entrega["id"], nombre))
    assert r.status_code in (404, 405), "debería haber rechazado %r" % nombre


def test_la_guardia_de_destino_sirve_aunque_el_nombre_pase_el_filtro(entrega, monkeypatch):
    """
    La segunda capa de `resuelve()`, probada sola y **con un fichero que existe de verdad**.

    Esta prueba nació de dos errores seguidos. Primero, al quitar la comprobación de destino
    ninguna prueba se enteraba: el filtro de nombres ya rechazaba todo lo que llegaba por HTTP.
    Y la primera versión de esta prueba tampoco servía, porque apuntaba a ficheros inexistentes:
    pasaba por el `isfile` final, no por la guardia. Una defensa solo está probada cuando la
    prueba falla al quitarla.

    Aquí se desactiva el filtro de nombres **y** se deja un fichero real justo fuera de la
    carpeta de la entrega, que es lo único que un escape podría alcanzar.
    """
    fuera = os.path.join(almacen.raiz(), "secreto.txt")
    with open(fuera, "w", encoding="utf-8") as f:
        f.write("esto no se sirve")
    try:
        monkeypatch.setattr(almacen, "nombre_valido", lambda nombre: True)
        assert os.path.isfile(fuera), "el fichero señuelo tiene que existir o no se prueba nada"
        for nombre in ("../secreto.txt", "./../secreto.txt", "sub/../../secreto.txt"):
            assert almacen.resuelve(entrega["id"], nombre) is None,                 "se salió de la carpeta con %r" % nombre
        # Y lo que sí es suyo sigue sirviéndose.
        assert almacen.resuelve(entrega["id"], "p0.jpg") is not None
    finally:
        os.remove(fuera)


def test_media_sirve_una_pagina_de_verdad(cliente, entrega):
    r = cliente.get("/media/entregas/%d/p0.jpg" % entrega["id"])
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/")


# --- La página pública ----------------------------------------------------------------
#
# Existe por la tarjeta de WhatsApp. Quien la pide con un navegador no la ve: va derecho a su
# propuesta. Por eso aquí hay que decir con qué se pide.

ROBOT = {"user-agent": "WhatsApp/2.23.20.0 A"}
PERSONA = {"user-agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) Safari/605.1"}


def test_la_previa_lleva_las_etiquetas_que_lee_whatsapp(cliente, entrega):
    r = cliente.get("/p/" + entrega["slug"], headers=ROBOT)
    assert r.status_code == 200
    html = r.text
    assert 'property="og:title"' in html
    assert 'property="og:image"' in html
    assert CANVA in html
    # Un solo enlace saliente: el de la presentación. Cada enlace de más es una tarjeta menos.
    assert html.count('href="https://') == 1


def test_la_tarjeta_no_ensena_los_marcadores(cliente, entrega):
    """
    El texto se guarda con {empresa} dentro y lo rellena el compositor al pintar el correo. La
    página lo imprimía en crudo: la tarjeta que ve el cliente al recibir el enlace por WhatsApp
    decía "Preparamos esta propuesta para {empresa}", con las llaves.
    """
    cliente.put("/api/entregas/%d" % entrega["id"], json={
        "titulo": entrega["titulo"], "canva_url": CANVA,
        "texto": "Preparamos esta propuesta para {empresa}, {destinatario}.",
        "servicios": entrega["servicios"], "contact_id": entrega["contact_id"]})
    html = cliente.get("/p/" + entrega["slug"], headers=ROBOT).text
    assert "{empresa}" not in html and "{destinatario}" not in html


def test_la_previa_registra_la_apertura(cliente, entrega, db):
    enlace = db.query(models.Link).filter(models.Link.slug == entrega["slug"]).first()
    antes = db.query(models.Click).filter(models.Click.link_id == enlace.id).count()
    cliente.get("/p/" + entrega["slug"] + "?c=token-de-prueba", headers=PERSONA,
                follow_redirects=False)
    db.expire_all()
    clics = db.query(models.Click).filter(models.Click.link_id == enlace.id).all()
    assert len(clics) == antes + 1
    assert clics[-1].contact_token == "token-de-prueba"


def test_una_persona_va_derecha_a_su_propuesta(cliente, entrega):
    """
    La página intermedia era un peaje: un clic de más para leer un resumen de lo que el correo ya
    decía. Quien pulsa quiere la propuesta.
    """
    r = cliente.get("/p/" + entrega["slug"], headers=PERSONA, follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == CANVA


def test_el_robot_no_cuenta_como_apertura(cliente, entrega, db):
    """
    Que WhatsApp mire el enlace al pegarlo lo hace QUIEN ENVÍA, no el cliente. Contarlo dispara un
    aviso de interés por algo que no pasó, y el aviso deja de significar nada.
    """
    enlace = db.query(models.Link).filter(models.Link.slug == entrega["slug"]).first()
    antes = db.query(models.Click).filter(models.Click.link_id == enlace.id).count()
    cliente.get("/p/" + entrega["slug"], headers=ROBOT)
    db.expire_all()
    assert db.query(models.Click).filter(
        models.Click.link_id == enlace.id).count() == antes


def test_una_previa_que_no_existe_da_404(cliente):
    assert cliente.get("/p/no-existe-este-slug").status_code == 404


# --- Marcar como entregada NO envía nada ----------------------------------------------

def test_marcar_entregada_deja_constancia_y_no_envia(cliente, entrega, db):
    r = cliente.post("/api/entregas/%d/entregada" % entrega["id"])
    assert r.status_code == 200
    assert r.json()["estado"] == "entregada"
    fila = db.query(models.Entrega).filter(models.Entrega.id == entrega["id"]).first()
    reparto = db.query(models.Delivery).filter(
        models.Delivery.link_id == fila.link_id).all()
    assert reparto, "debería haber quedado constancia del reparto"
    assert reparto[-1].formato == "H"
