# Contrato: rutas nuevas del catálogo

Todas JSON salvo donde se indica. Sesión del panel por cookie, como el resto. Ninguna ruta existente cambia.

| Método y ruta | Quién | Qué hace | Respuestas |
|---|---|---|---|
| `GET /api/catalogo` | Cualquier sesión | Catálogo activo en la forma de `ponCatalogo` | 200 · 401 |
| `GET /api/panel/lineas` | Administrador | Todas las líneas (activas y retiradas) y las familias | 200 · 401 · 403 |
| `POST /api/panel/lineas` | Administrador | Alta. Cuerpo: campos de la línea; `plantillas` por defecto todas. Exige `confirmarSinPlantillas: true` si `plantillas` va vacío | 201 · 400 (validación) · 409 (nombre repetido) |
| `PATCH /api/panel/lineas/{id}` | Administrador | Edita solo lo que se manda; `activa: false/true` retira o devuelve | 200 · 400 · 404 · 409 |
| `POST /api/panel/lineas/orden` | Administrador | Cuerpo `{"ids": [...]}`: nuevo orden | 200 · 400 |
| `POST /api/panel/lineas/{id}/foto` | Administrador | `multipart/form-data`, campo `fichero`. Valida, reduce y guarda; devuelve la dirección pública | 200 · 400 (no es imagen) · 413 (> 8 MB) · 404 |
| `POST /api/panel/familias` | Administrador | Alta de familia `{titulo, eyebrow}` | 201 · 400 · 409 |
| `GET /media/lineas/{archivo}` | Público | Sirve la foto (la usan los correos). Nombre validado por lista blanca, como `/media/entregas` | 200 · 404 |
| `GET /panel/lineas` | Cualquier sesión (sin sesión → entrada) | Pantalla «Líneas de negocio»; los comerciales la ven en solo lectura | 200 · 307 |

Validación común: nombre obligatorio, único y ≤ 120; `canva` vacío o `http(s)://`; `plantillas` solo
letras A–H sin repetir; textos con los límites de `data-model.md`. Mensajes de error en español, sin
detalles internos.
