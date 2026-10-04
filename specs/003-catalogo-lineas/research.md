# Research: Catálogo de líneas de negocio

## 1. Dónde vive el catálogo

- **Decision**: tablas en la misma SQLite del volumen (`lineas_negocio`, `familias_d`), servidas por API.
- **Rationale**: tiene que ser compartido por todo el equipo y cambiar sin despliegue (FR-301); la base
  persistente ya existe y sobrevive a los despliegues; `create_all` añade tablas sin tocar las del
  acortador (principio I).
- **Alternatives considered**: un JSON en el volumen (sin transacciones ni historial de quién cambió);
  `localStorage` del navegador (no se comparte); seguir en `render.js` (exige programar y desplegar,
  que es justo lo que se quiere evitar).

## 2. Una sola fuente para el catálogo de serie

- **Decision**: `render.js` sigue siendo la fuente de las cinco líneas de serie. `build.js` exporta
  `app/static/email/catalogo-serie.json` (líneas, familias, ficha, plantillas = todas) y el servidor
  siembra sus tablas desde ese archivo **solo si están vacías**.
- **Rationale**: principio II (un solo motor). Si la siembra copiara los datos a mano en Python,
  habría dos fuentes que acabarían separándose, como ya pasó con los datos de contacto.
- **Alternatives considered**: sembrar con datos escritos en Python (dos fuentes); que el compositor
  mande al servidor su catálogo la primera vez (depende de quién entre primero).

## 3. Cómo recibe el motor el catálogo del servidor

- **Decision**: `ponCatalogo({lineas, familias})` reemplaza **en sitio** el contenido de `SERVICIOS`,
  `GRUPOS`, `FICHA` y `BANCO` (son las mismas referencias que usa todo el motor) antes de pintar. Sin
  llamarla, el motor queda exactamente como hoy.
- **Rationale**: no hay que tocar cada uso de esas constantes; `normaliza()` ya incorpora las líneas
  nuevas del catálogo y quita las que no están, conservando lo escrito a mano (principio II); la guardia
  byte a byte sigue midiendo el comportamiento de serie.
- **Alternatives considered**: pasar el catálogo dentro del estado `st` (lo guardaría `localStorage` y
  envejecería en cada navegador); reescribir el motor para leer siempre del estado (cambio grande sin
  beneficio para el usuario).

## 4. Inclusión por plantilla

- **Decision**: cada línea lleva `plantillas` (cadena con las letras A–H). `render()` trabaja sobre una
  copia en la que las líneas no incluidas en la plantilla de ese correo quedan apagadas (`on = false`).
- **Rationale**: un único punto cubre las ocho plantillas, las listas, las tablas, los bloques que
  buscan una línea por su id y el texto plano y WhatsApp; el estado de la persona no se modifica.
- **Alternatives considered**: filtrar en cada plantilla (ocho sitios que mantener); quitar la línea
  del estado (perdería lo escrito a mano al cambiar de plantilla).

## 5. Tablas y familias

- **Decision**: las cinco filas actuales del inventario de la E y sus textos se mantienen; detrás se
  añade una fila genérica por cada línea activa con ficha (nombre, cobertura, medidas y tráfico de su
  ficha). La tabla de agencias ya recorre `FICHA` por id, así que una línea con ficha entra sola. En la
  D, `GRUPOS` se construye desde `familias_d`; una línea sin familia va a «Otros servicios».
- **Rationale**: los correos de serie no cambian (SC-303) y una línea nueva no aparece con datos que
  nadie escribió (principio IV).
- **Alternatives considered**: rehacer el inventario de la E como tabla 100 % genérica (cambiaría los
  correos de referencia y perdería los textos curados de las cinco filas).

## 6. Fotos

- **Decision**: subida al panel (`POST /api/panel/lineas/{id}/foto`), validada con Pillow (solo
  imagen, máx. 8 MB), reducida a 1072 px de ancho (2× de 536, la columna más ancha) en JPEG calidad 82,
  guardada en `/app/data/lineas/<id>-<huella>.jpg` y servida en `/media/lineas/<archivo>`. La línea
  guarda la **dirección absoluta**; `imgFor()` del motor respeta las direcciones absolutas.
- **Rationale**: el proxy de imágenes de Gmail necesita una dirección pública y estable; la huella en
  el nombre evita que una foto cambiada se quede en caché; el volumen sobrevive a los despliegues.
- **Alternatives considered**: guardar la foto en `app/static/email/` (se reemplaza en cada
  despliegue); pegar una URL externa (frágil, y el equipo no tiene dónde alojarla).

## 7. Retirar

- **Decision**: `activa = false`; el catálogo de lectura solo entrega las activas; la pantalla
  muestra las retiradas aparte con «Devolver».
- **Rationale**: FR-319 (no borrar) y coherencia con la baja de usuarios de la 002.
