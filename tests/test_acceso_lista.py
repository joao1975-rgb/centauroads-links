"""
La puerta del panel: la lista de autorizados (T125, FR-119 y FR-120).

Hasta la 002 la puerta era el dominio del correo. Ahora es una lista explícita, porque el equipo
entra con su propia cuenta de Gmail. Este fichero comprueba lo que eso implica, y lo que implica
no es cómodo:

- Una cuenta de Google **auténtica** que no esté en la lista **no entra**. Que Google diga quién
  eres no dice que puedas pasar.
- Dar de baja a alguien le corta el acceso **aunque su cuenta de Gmail siga existiendo**. Es el
  caso real: la persona se va de la empresa y su correo personal sigue ahí para siempre.
- El rechazo **no revela** si ese correo está en la lista. Si lo revelara, la pantalla de entrada
  sería una forma de averiguar quién trabaja aquí.
"""

import pytest
from fastapi.testclient import TestClient

from app import main as app_main
from app import models
from app.auth import google, rutas, sesion
from app.database import SessionLocal


@pytest.fixture(scope="module")
def db():
    s = SessionLocal()
    yield s
    s.close()


@pytest.fixture()
def cliente():
    return TestClient(app_main.app)


def _con_google(monkeypatch, email, nombre="Quien Sea"):
    """Simula que Google validó el identificador y devuelve esa cuenta."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cliente-de-prueba")
    monkeypatch.setattr(
        google.google_id_token, "verify_oauth2_token",
        lambda *a, **k: {"iss": "https://accounts.google.com", "email_verified": True,
                         "email": email, "name": nombre},
    )


def _alta(db, email, rol="comercial", activo=True):
    usuario = db.query(models.PanelUser).filter(models.PanelUser.email == email).first()
    if usuario:
        usuario.activo = activo
        usuario.rol = rol
    else:
        usuario = models.PanelUser(email=email, nombre=email.split("@")[0], rol=rol,
                                   activo=activo)
        db.add(usuario)
    db.commit()
    db.refresh(usuario)
    return usuario


# --- Quién pasa y quién no ------------------------------------------------------------

def test_un_gmail_de_la_lista_entra(cliente, db, monkeypatch):
    """El caso que motivó todo: cuenta personal de Gmail, la misma que usa en Canva."""
    _alta(db, "persona.equipo@gmail.com")
    _con_google(monkeypatch, "persona.equipo@gmail.com", "Persona Equipo")
    r = cliente.post("/api/auth/google", json={"credential": "identificador-valido"})
    assert r.status_code == 200, r.text
    assert r.json()["email"] == "persona.equipo@gmail.com"
    assert sesion.COOKIE in r.cookies


def test_un_gmail_que_no_esta_en_la_lista_no_entra(cliente, monkeypatch):
    """Identidad auténtica, autorización ninguna. Son cosas distintas."""
    _con_google(monkeypatch, "desconocido@gmail.com")
    r = cliente.post("/api/auth/google", json={"credential": "identificador-valido"})
    assert r.status_code == 403
    assert sesion.COOKIE not in r.cookies


def test_una_cuenta_del_dominio_tampoco_entra_sola(cliente, monkeypatch):
    """
    Ser de `@centauroads.com` ya no concede nada por sí mismo. Si esto dejara de cumplirse,
    cualquier cuenta del dominio entraría sin que nadie la hubiera autorizado.
    """
    _con_google(monkeypatch, "quien.sea@centauroads.com")
    r = cliente.post("/api/auth/google", json={"credential": "identificador-valido"})
    assert r.status_code == 403


def test_dar_de_baja_corta_el_acceso_aunque_el_gmail_siga_existiendo(cliente, db, monkeypatch):
    """
    El motivo por el que sacar a alguien de la lista es un paso obligatorio de su baja (FR-120).
    """
    _alta(db, "seva@gmail.com")
    _con_google(monkeypatch, "seva@gmail.com")
    assert cliente.post("/api/auth/google", json={"credential": "x"}).status_code == 200

    _alta(db, "seva@gmail.com", activo=False)
    assert cliente.post("/api/auth/google", json={"credential": "x"}).status_code == 403


# --- El rechazo no cuenta de más ------------------------------------------------------

def test_el_rechazo_no_revela_si_la_cuenta_esta_en_la_lista(cliente, db, monkeypatch):
    """
    Dos situaciones distintas —no existe, y existe pero está desactivada— tienen que dar
    exactamente la misma respuesta. Cualquier diferencia convierte la pantalla de entrada en un
    directorio del personal.
    """
    _alta(db, "desactivada@gmail.com", activo=False)

    _con_google(monkeypatch, "desactivada@gmail.com")
    a = cliente.post("/api/auth/google", json={"credential": "x"})
    _con_google(monkeypatch, "jamas.existio@gmail.com")
    b = cliente.post("/api/auth/google", json={"credential": "x"})

    assert a.status_code == b.status_code
    assert a.json()["detail"] == b.json()["detail"]

    # Compararlos entre sí no basta, y esto lo descubrió una mutación: al cambiar el mensaje por
    # «esa cuenta existe pero está desactivada», los dos seguían siendo iguales —pasan por la
    # misma rama— y la prueba no se enteraba. Lo que hay que exigir es que el texto **no hable**
    # del estado de la cuenta.
    texto = a.json()["detail"].lower()
    for revelador in ("desactiv", "existe", "no está", "no esta", "inactiv", "baja"):
        assert revelador not in texto, (
            "el rechazo revela el estado de la cuenta: %r" % a.json()["detail"])


def test_un_identificador_invalido_se_distingue_de_una_cuenta_sin_permiso(cliente, monkeypatch):
    """
    Aquí sí conviene distinguir: un identificador roto es un problema técnico de quien entra, no
    una cuestión de permisos, y decírselo le ahorra buscar donde no es.
    """
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cliente-de-prueba")
    monkeypatch.setattr(google.google_id_token, "verify_oauth2_token",
                        lambda *a, **k: (_ for _ in ()).throw(ValueError("firma mala")))
    r = cliente.post("/api/auth/google", json={"credential": "roto"})
    assert r.status_code == 401


def test_una_cuenta_sin_el_correo_verificado_no_entra(cliente, db, monkeypatch):
    _alta(db, "sinverificar@gmail.com")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cliente-de-prueba")
    monkeypatch.setattr(
        google.google_id_token, "verify_oauth2_token",
        lambda *a, **k: {"iss": "https://accounts.google.com", "email_verified": False,
                         "email": "sinverificar@gmail.com"},
    )
    assert cliente.post("/api/auth/google", json={"credential": "x"}).status_code == 401


# --- El arranque en frío --------------------------------------------------------------

def test_el_arranque_en_frio_da_de_alta_a_quien_diga_la_variable(db, monkeypatch):
    """Con la lista vacía no entraría nadie, ni siquiera para añadir al primero."""
    monkeypatch.setenv("PANEL_BOOTSTRAP", "primera@gmail.com, segunda@gmail.com")
    creados = rutas.asegura_bootstrap(db)
    assert creados == 2
    primera = db.query(models.PanelUser).filter(
        models.PanelUser.email == "primera@gmail.com").first()
    assert primera.rol == "admin" and primera.activo


def test_el_arranque_en_frio_no_resucita_a_quien_se_dio_de_baja(db, monkeypatch):
    """
    Si alguien sale de la empresa y además sigue en la variable, manda la baja. Lo contrario
    haría que cada reinicio deshiciera una decisión deliberada.
    """
    _alta(db, "yasalio@gmail.com", activo=False)
    monkeypatch.setenv("PANEL_BOOTSTRAP", "yasalio@gmail.com")
    rutas.asegura_bootstrap(db)
    usuario = db.query(models.PanelUser).filter(
        models.PanelUser.email == "yasalio@gmail.com").first()
    assert not usuario.activo, "un reinicio no puede devolverle el acceso a quien se dio de baja"


def test_la_aplicacion_arranca_con_panel_bootstrap_puesto(tmp_path):
    """
    Importar `app.main` **entera**, en un proceso aparte, con la variable puesta.

    Esta prueba existe por un fallo concreto: el arranque en frío usaba un logger que en ese
    punto del fichero todavía no existía, así que con `PANEL_BOOTSTRAP` puesto la aplicación no
    arrancaba. Ninguna prueba se enteró —ninguna pone esa variable— y lo descubrió levantar el
    servidor a mano.

    La lección no es «acordarse del logger», es que **el arranque es código** y hay que
    ejecutarlo con las variables que tendrá en producción.
    """
    import os
    import subprocess
    import sys

    entorno = dict(
        os.environ,
        PANEL_BOOTSTRAP="arranque@ejemplo.test",
        DATABASE_URL="sqlite:///" + (tmp_path / "arranque.db").as_posix(),
        DATA_DIR=str(tmp_path / "datos"),
        SESSION_SECRET="solo-para-esta-prueba",
    )
    r = subprocess.run([sys.executable, "-c", "import app.main"],
                       env=entorno, capture_output=True, text=True, timeout=120,
                       cwd=str(__import__("pathlib").Path(__file__).resolve().parent.parent))
    assert r.returncode == 0, (
        "la aplicación no arranca:" + chr(10) + r.stderr[-1500:])


# --- Administrar la lista -------------------------------------------------------------

@pytest.fixture()
def admin(db, cliente):
    usuario = _alta(db, "jefa@gmail.com", rol="admin")
    cliente.cookies.set(sesion.COOKIE, sesion.crear(usuario.id, usuario.email))
    return usuario


def test_solo_un_administrador_ve_la_lista(cliente, db):
    comercial = _alta(db, "comercial@gmail.com", rol="comercial")
    cliente.cookies.set(sesion.COOKIE, sesion.crear(comercial.id, comercial.email))
    assert cliente.get("/api/panel/usuarios").status_code == 403


def test_un_administrador_da_de_alta_y_de_baja(cliente, db, admin):
    r = cliente.post("/api/panel/usuarios",
                     json={"email": "Nueva@Gmail.com", "nombre": "Nueva"})
    assert r.status_code == 200, r.text
    nueva_id = r.json()["id"]
    # El correo se guarda en minúsculas: si no, «Nueva@» y «nueva@» serían dos personas.
    assert r.json()["email"] == "nueva@gmail.com"

    assert cliente.delete("/api/panel/usuarios/%d" % nueva_id).status_code == 200
    fila = db.query(models.PanelUser).filter(models.PanelUser.id == nueva_id).first()
    assert fila is not None, "la fila no se borra: la bitácora sigue señalando a alguien"
    assert not fila.activo


def test_dar_de_alta_a_quien_ya_estuvo_reactiva_su_fila(cliente, db, admin):
    antigua = _alta(db, "vuelve@gmail.com", activo=False)
    r = cliente.post("/api/panel/usuarios", json={"email": "vuelve@gmail.com"})
    assert r.status_code == 200
    assert r.json()["reactivado"] is True
    assert r.json()["id"] == antigua.id, "debería ser la misma fila, no una nueva"


def test_nadie_puede_retirarse_el_acceso_a_si_mismo(cliente, admin):
    r = cliente.delete("/api/panel/usuarios/%d" % admin.id)
    assert r.status_code == 400


# --- La pantalla de entrada -----------------------------------------------------------

def test_la_pantalla_de_entrada_responde(cliente):
    r = cliente.get("/panel/entrar")
    assert r.status_code == 200
    assert "Entrar al panel" in r.text


def test_sin_client_id_no_se_ofrece_el_boton_de_google(cliente, monkeypatch):
    """Enseñar un botón que fallaría al pulsarlo es peor que no enseñarlo."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "")
    r = cliente.get("/panel/entrar")
    assert "accounts.google.com/gsi/client" not in r.text


def test_a_donde_lleva_entrar_existe_de_verdad(cliente, admin):
    """
    Entrar y aterrizar en un 404 es entrar mal.

    Esta prueba nació de eso exactamente: el destino por defecto era `/admin/entregas`, una ruta
    que nunca se creó. La sesión quedaba puesta y la persona veía `{"detail":"Not Found"}`. No lo
    cogió ninguna prueba porque todas comprobaban el **login**, y ninguna a dónde te deja.

    Comprobar que una dirección responde es barato; descubrirlo con alguien entrando, no. Se
    comprueba CON sesión y sin seguir redirecciones: sin sesión el compositor manda a entrar, y
    siguiéndola se acabaría en la pantalla de entrada, que también da 200 y no prueba nada.
    """
    r = cliente.get(rutas.COMPOSITOR, follow_redirects=False)
    assert r.status_code == 200, "el compositor no responde en " + rutas.COMPOSITOR
    cliente.cookies.clear()

    r = cliente.get("/panel/entrar")
    assert rutas.COMPOSITOR in r.text, "la pantalla de entrada no apunta al compositor"

    # Y el nombre corto lleva al mismo sitio.
    corto = cliente.get("/admin/entregas", follow_redirects=False)
    assert corto.status_code in (302, 303, 307)
    assert corto.headers["location"] == rutas.COMPOSITOR


def test_el_destino_no_puede_llevar_fuera_del_sitio(cliente):
    """Un enlace preparado no puede hacer que alguien entre y acabe en otra parte."""
    for malo in ("https://otro-sitio.example/robar", "//otro-sitio.example"):
        r = cliente.get("/panel/entrar", params={"destino": malo})
        assert "otro-sitio.example" not in r.text


# --- Primero se entra, luego se usa la herramienta ------------------------------------
# El enlace que circulaba abría el compositor sin preguntar quién eras, y solo al pulsar algo
# que hablaba con el servidor salía «Hay que entrar al panel». Era el orden al revés.

def test_sin_sesion_el_compositor_lleva_a_la_entrada(cliente):
    cliente.cookies.clear()
    r = cliente.get(rutas.COMPOSITOR, follow_redirects=False)
    assert r.status_code == 307
    assert r.headers["location"] == "/panel/entrar?destino=%2Fstatic%2Femail%2Fcompositor.html"


def test_una_cookie_inventada_no_abre_el_compositor(cliente):
    cliente.cookies.set(sesion.COOKIE, "inventada.sin.firma")
    r = cliente.get(rutas.COMPOSITOR, follow_redirects=False)
    assert r.status_code == 307
    cliente.cookies.clear()


def test_con_sesion_la_entrada_pasa_directo_a_la_herramienta(cliente, admin):
    """Quien ya entró no tiene que volver a escribir su correo."""
    r = cliente.get("/panel/entrar", follow_redirects=False)
    assert r.status_code == 303 and r.headers["location"] == rutas.COMPOSITOR
    # Y respeta a dónde iba, si es una ruta de la casa.
    r = cliente.get("/panel/entrar", params={"destino": "/admin"}, follow_redirects=False)
    assert r.headers["location"] == "/admin"
    cliente.cookies.clear()


def test_la_direccion_corta_del_panel_lleva_a_la_entrada(cliente):
    cliente.cookies.clear()
    r = cliente.get("/panel", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == "/panel/entrar"


def test_las_imagenes_de_los_correos_siguen_publicas(cliente):
    """Las cargan los correos de los clientes, que no tienen sesión ni la van a tener."""
    cliente.cookies.clear()
    assert cliente.get("/static/email/logo_h_dark_2x.png").status_code == 200
    assert cliente.get("/static/email/render.js").status_code == 200


def test_el_navegador_no_guarda_el_compositor(cliente, admin):
    """
    Si lo guarda, tras salir lo sigue abriendo de su caché sin preguntar al servidor, y la puerta
    no sirve de nada. Se vio probándolo en un navegador de verdad.
    """
    r = cliente.get(rutas.COMPOSITOR, follow_redirects=False)
    assert r.status_code == 200 and r.headers.get("cache-control") == "no-store"
    cliente.cookies.clear()
    r = cliente.get(rutas.COMPOSITOR, follow_redirects=False)
    assert r.status_code == 307 and r.headers.get("cache-control") == "no-store"


# --- La guía de instalación, desde la pantalla de entrada (2026-09-30, petición del usuario) ----

def test_la_entrada_enlaza_la_guia_para_verla_y_para_descargarla(cliente):
    cliente.cookies.clear()
    html = cliente.get("/panel/entrar").text
    assert 'href="/panel/guia" target="_blank"' in html
    assert 'href="/panel/guia/descargar"' in html


def test_la_guia_se_abre_sin_haber_entrado(cliente):
    """Se consulta antes de poder entrar: exigir sesión para leerla no tendría sentido."""
    cliente.cookies.clear()
    r = cliente.get(rutas.GUIA, follow_redirects=False)
    assert r.status_code == 200
    assert "<title>Instalar Centauro Links</title>" in r.text
    assert r.text.lstrip().lower().startswith("<!doctype html>")
    # y el compositor, en cambio, sigue pidiendo entrar
    assert cliente.get(rutas.COMPOSITOR, follow_redirects=False).status_code == 307


def test_la_direccion_corta_de_la_guia_funciona_con_y_sin_sesion(cliente, admin):
    """Se puede mandar a cualquiera. Con la sesión abierta, antes no había forma de llegar a la guía."""
    r = cliente.get("/panel/guia", follow_redirects=False)
    assert r.status_code == 307 and r.headers["location"] == rutas.GUIA
    cliente.cookies.clear()
    assert cliente.get("/panel/guia", follow_redirects=False).headers["location"] == rutas.GUIA


def test_con_la_sesion_abierta_la_guia_esta_en_el_compositor(cliente, admin):
    """
    Con la sesión abierta, /panel pasa directo al compositor y la pantalla de entrada no se ve: los
    enlaces de la guía tienen que estar también dentro.
    """
    assert cliente.get("/panel", follow_redirects=True).url.path == rutas.COMPOSITOR
    html = cliente.get(rutas.COMPOSITOR).text
    assert 'href="/panel/guia" target="_blank"' in html
    assert 'href="/panel/guia/descargar"' in html
    cliente.cookies.clear()


def test_la_descarga_la_entrega_el_servidor_como_archivo(cliente):
    """Content-Disposition: attachment obliga a guardar en cualquier navegador, con o sin sesión."""
    cliente.cookies.clear()
    r = cliente.get("/panel/guia/descargar")
    assert r.status_code == 200
    assert r.headers["content-disposition"].startswith("attachment")
    assert 'filename="guia-instalacion-centauro-links.html"' in r.headers["content-disposition"]
    assert "<title>Instalar Centauro Links</title>" in r.text
