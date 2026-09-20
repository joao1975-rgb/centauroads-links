"""
Configuración común de las pruebas.

Este fichero lo carga pytest ANTES de importar ningún módulo de prueba, y ese detalle es justo el
motivo de que exista: `app.database` lee DATABASE_URL en tiempo de importación y `app.main` crea
tablas y migra también al importarse. Si dejáramos que eso ocurriera con la configuración por
defecto, las pruebas escribirían en `data/centaurads_links.db`, que es la base de datos real de
desarrollo.

Aquí se apunta todo a un directorio temporal antes de que nada de `app` se importe.

Se intentó antes la vía de recargar módulos dentro de una fixture y no funciona de forma fiable:
sacar `app.models` de `sys.modules` no borra el atributo `models` del paquete `app`, así que
`from . import models` sigue devolviendo el módulo viejo, atado a un `Base` cuyo metadata ya no
es el que se acaba de crear. El resultado era un `create_all` que no creaba nada y un
desconcertante "no such table: links". Configurar el entorno antes de importar evita el problema
de raíz en vez de pelearse con él.
"""

import os
import tempfile

# Un directorio propio para toda la sesión de pruebas. No se borra al terminar: es temporal del
# sistema y ocupa unos kilobytes, y tenerlo a mano ayuda cuando algo falla y hay que mirar la BD.
_TMP = tempfile.mkdtemp(prefix="centaurads-tests-")

os.environ.setdefault(
    "DATABASE_URL",
    "sqlite:///" + os.path.join(_TMP, "pruebas.db").replace("\\", "/"),
)
os.environ.setdefault("ADMIN_KEY_FILE", os.path.join(_TMP, "admin.key"))
os.environ.setdefault("ADMIN_KEY", "clave-de-prueba")
os.environ.setdefault("SESSION_SECRET", "clave-de-firma-solo-para-pruebas")
os.environ.setdefault("SUPERADMIN_USER", "super@ejemplo.test")
os.environ.setdefault("SUPERADMIN_PASS", "contrasena-de-prueba")
# Sin HTTPS en las pruebas, así TestClient conserva la cookie de sesión.
os.environ.setdefault("COOKIE_INSEGURA", "1")

DIRECTORIO_TEMPORAL = _TMP
