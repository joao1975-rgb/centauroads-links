# Contrato: rutas nuevas de los espacios de una entrega

Todas con sesión del panel (como el resto de `/api/entregas`), JSON salvo donde se indica. Ninguna
ruta existente cambia de forma; `EntregaSalida` gana el campo `espacios`.

| Método y ruta | Qué hace | Respuestas |
|---|---|---|
| `PUT /api/entregas/{id}/espacios/{linea}` | Guarda lo propio del espacio: cuerpo `{canva_url?, nombre?, cobertura?}`. Cada campo igual al del catálogo queda estándar. Devuelve la entrega | 200 · 400 (enlace o texto no válido) · 401 · 404 (entrega o línea inexistente) |
| `DELETE /api/entregas/{id}/espacios/{linea}` | Vuelve al estándar: borra la fila. Las imágenes se conservan (un correo enviado puede apuntar a ellas) | 200 · 401 · 404 |
| `POST /api/entregas/{id}/espacios/{linea}/paginas` | `multipart/form-data`, campo `fichero` (uno o varios). Igual que la principal: rasteriza y guarda en la subcarpeta del espacio, sin tocar la principal ni otros espacios | 200 `{paginas, minimo, maximo, aviso}` · 400 · 401 · 404 |
| `PUT /api/entregas/{id}/espacios/{linea}/paginas` | `{indices: [2..4], efecto}`. Arma el carrusel del espacio. Devuelve la entrega | 200 · 400 · 401 · 404 |
| `GET /media/entregas/{id}/espacios/{linea}/{fichero}` | Público. Sirve la imagen con la misma lista blanca y comprobación de destino que `/media/entregas/{id}/{fichero}` | 200 · 404 |

Límites y mensajes: los de la principal (002), sin redactar de nuevo. Errores en español, sin detalles
internos.
