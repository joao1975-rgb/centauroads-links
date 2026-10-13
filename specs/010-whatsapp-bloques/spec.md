# Feature Specification: WhatsApp por bloques (entrega H)

**Feature Branch**: `010-whatsapp-bloques`

**Created**: 2026-10-13

**Status**: Draft

**Input**: Petición de la propietaria (2026-10-13): «no tiene ningún sentido que los links queden en un
bloque y las imágenes en otro… la primera generación con la información actual sin los links… construir
los bloques adicionales… elegibles… nombre, la imagen y el link». Maqueta aprobada
(`scratchpad/maqueta-wa/maqueta-whatsapp.png`). Decisiones: **enlace propio por servicio**; el botón
«Copiar imagen de servicios» (009) **se queda**.

Sustituye el FR-906 de la 009 (la lista de enlaces dentro del mensaje principal).

## Contexto

WhatsApp dibuja la tarjeta (imagen, título, descripción) solo del **primer** enlace de cada mensaje. Con
el enlace de Canva tal cual, la tarjeta la escribe Canva: el título interno del diseño (Vallas saldría
«PROYECTO - CENTRO COMERCIAL VALENCIA», de otro cliente) y «Check out this Presentation designed by
Departamento Creativo.». Comprobado el 2026-10-13 con los cuatro enlaces de los servicios.

## User Scenarios & Testing

### US1 — Un mensaje por servicio, con su tarjeta (P1)

En la H, «Enviar por WhatsApp» (paso 05) lista: **1 · Mensaje principal** y un **bloque por cada
espacio que la acompaña** (catálogo o a medida), en el orden de la entrega, cada uno con su casilla
(marcados por defecto) y su botón «Copiar». **«Copiar el siguiente · n de N»** copia el próximo
marcado a cada pulsación. Un bloque es: su nombre y su **enlace propio**
`https://mails.centauroads.com/p/<slug>/<espacio>`. Al pegarlo, WhatsApp dibuja la tarjeta con **nuestra
foto, el nombre y la ubicación** del servicio.

**Acceptance**:
1. El mensaje principal es el de hoy sin la lista de enlaces; si va al menos un bloque, termina el texto
   con «Te envío aparte los espacios que la acompañan.».
2. Un espacio desmarcado no tiene bloque ni cuenta en «n de N».
3. Sin entrega guardada no hay bloques (no hay enlace propio): se dice que hay que guardarla.

### US2 — La tarjeta y el destino del enlace propio (P1)

`/p/<slug>/<espacio>`:
- **Robot** (WhatsApp, Telegram…): página con `og:title` = nombre, `og:description` = línea (cobertura),
  `og:image` = la primera página de su carrusel propio si lo tiene; si no, la foto del catálogo.
- **Persona**: se registra la apertura (qué servicio, de qué entrega) y se la manda a la presentación de
  ese espacio (su enlace propio de la entrega o el del catálogo); sin enlace, a la de la propuesta.
- Un espacio que no es de esa entrega (no incluido, de otra entrega, inventado) → 404.

### US3 — Sigue la imagen con todos (P3)

«Copiar imagen de servicios» (009) se queda como opción para mandarlo todo en una sola foto.

## Requirements

- **FR-1001**: El mensaje principal de WhatsApp de la H MUST NOT llevar la lista de enlaces (deroga FR-906).
- **FR-1002**: El compositor MUST ofrecer un bloque por espacio incluido, elegible, con «Copiar» y
  «Copiar el siguiente · n de N».
- **FR-1003**: `/p/<slug>/<espacio>` MUST servir a los robots una tarjeta con el nombre, la línea y la foto
  del espacio, y MUST mandar a las personas a la presentación del espacio (o de la propuesta).
- **FR-1004**: Cada apertura de una persona MUST registrarse con su espacio (tabla nueva
  `aperturas_espacios`) y contar como un clic de la entrega, como hoy `/p/<slug>`. Los robots no cuentan.
- **FR-1005**: Un espacio ajeno a la entrega MUST dar 404.
- **FR-1006**: Las plantillas A–G y el correo H MUST salir idénticos (16 de referencia).

## Plan técnico

- **Servidor** (`app/mails/entregas/publicas.py`): ruta `GET /p/{slug}/{espacio}`. Resuelve el espacio con
  la entrega: incluido en `entrega.servicios` (catálogo, con lo propio de `entrega_espacios`) o fila
  `medida--` de esa entrega. Imagen: la primera elegida de su carrusel (`_url_media` de su carpeta)
  o la foto de la línea (`/static/email/<img>` o `/media/lineas/...`), siempre absoluta con el esquema del
  proxy. Página con el mismo `_PAGINA` (botón «Ver la presentación»). Tabla `aperturas_espacios`
  (`id`, `entrega_id`, `linea`, `contact_token`, `ip`, `user_agent`, `creado`) por `create_all`.
- **Motor** (`render.js`): `renderWhatsApp` sin la lista; la línea «Te envío aparte…» si hay bloques.
  `bloquesWhatsApp(st)` → `[{ id, nombre, texto }]` de los incluidos no excluidos en
  `bloques.entrega.waFuera`, con `texto = nombre + "\n" + enlace + "/" + id`; vacío sin enlace guardado.
- **Compositor**: grupo «Enviar por WhatsApp» en el paso 05 (casillas → `E.waFuera`, «Copiar» por
  bloque, «Copiar el siguiente» con contador que vuelve a empezar al cambiar la selección). Pasa por la
  guarda de cambios sin guardar de la 009.

## Tasks

- [x] T1001 Pruebas de la ruta: robot (título, línea, imagen absoluta del catálogo, del carrusel propio y de un a medida), persona (307 al destino correcto; apertura registrada con su espacio; clic de la entrega), 404 para ajeno/otra entrega/inventado/enlace inactivo — `tests/test_whatsapp_bloques.py`
- [x] T1002 Pruebas del motor: mensaje principal sin lista y con la línea solo si hay bloques; `bloquesWhatsApp` en orden, sin excluidos, con el enlace propio; vacío sin enlace — `tests/test_whatsapp_bloques_motor.py`
- [x] T1003 Ruta pública y tabla `aperturas_espacios` — `app/mails/entregas/publicas.py`, `app/models.py`
- [x] T1004 Motor — `prototipos/mail/render.js`
- [x] T1005 Compositor: grupo «Enviar por WhatsApp» — `prototipos/mail/compositor.html`
- [x] T1006 Demo: tarjeta de robot por servicio (HTML con og:*), copiar bloques en orden, 0 errores; suite, build (16 idénticas), README y Obsidian
