# Contrato: rutas de los textos de los perfiles

Sesión del panel por cookie, JSON. Ninguna ruta existente cambia. Las que cambian estado pasan por el
filtro de origen (403 «Origen no permitido»).

| Método y ruta | Quién | Qué hace | Respuestas |
|---|---|---|---|
| `GET /api/textos-perfil` | Cualquier sesión | Los textos cambiados `{clave: valor}` (lo que recibe `ponTextos`) | 200 · 401 |
| `GET /api/panel/textos` | Cualquier sesión | Todos los textos: de serie, cambiado (si lo hay), quién y cuándo | 200 · 401 |
| `PUT /api/panel/textos/{clave}` | Administrador | `{valor}`: guarda el cambio. Igual al de serie = vuelve al de serie | 200 · 400 (vacío) · 401 · 403 · 404 (clave desconocida) · 422 (largo) |
| `DELETE /api/panel/textos/{clave}` | Administrador | Vuelve al de serie (si no estaba cambiado, no pasa nada) | 200 · 401 · 403 · 404 |
| `GET /panel/textos` | Cualquier sesión (sin sesión → entrada) | Pantalla «Textos de los perfiles»; los comerciales la ven en solo lectura | 200 · 307 |
