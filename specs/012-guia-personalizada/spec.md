# Feature Specification: Guía personalizada (plantilla I)

**Feature Branch**: `012-guia-personalizada`

**Created**: 2026-10-23

**Status**: Implementada

**Input**: Petición de la propietaria (2026-10-23): «tomar el modelo F-Guía y convertirlo en un modelo
personalizable. Consta de tres bloques: 1) Que te conozcan, 2) Que te recuerden, 3) Que te compren.
Que sean configurables: títulos, textos y los productos que le acompañan. Que todo lo demás se comporte
como la H-Personalizada, pero en vez de una presentación personalizada puedan ir hasta tres, o que se
nutran de la información de productos ya existentes».

Decisiones (preguntas, 2026-10-23):
- **Plantilla nueva aparte**: «I · Guía personalizada». La F de catálogo no cambia.
- **Un producto por bloque**.
- **Producto + su propia presentación**: cada bloque elige un producto del catálogo; si se quiere, se le
  pone enlace y PDF propios para este cliente; si no, usa la presentación estándar del producto (como
  los espacios de la H).
- **De 1 a 3 bloques**: los tres salen por defecto; cualquiera se puede apagar y se pueden reordenar.

## Contexto

Hoy la F («Guía») es una plantilla de catálogo: sus tres fases tienen títulos y textos fijos (los de la
guía, editables solo para todos a la vez) y cada fase lleva siempre el mismo producto (Tótem, LED, Rider).
No se guarda por cliente, no tiene enlace propio, ni seguimiento de aperturas.

La H sí es por cliente (entrega guardada, contacto, guardado automático, enlace `/p/<slug>`, aperturas,
WhatsApp por bloques con enlace propio por servicio, «Marcar como entregada»), pero lleva **una** sola
presentación principal más espacios acompañantes.

La I junta las dos: el diseño y la estructura de la F, con el comportamiento de la H.

## User Scenarios & Testing

### US1 — Armar una guía para un cliente (P1)

En el compositor, la pestaña **«I · Guía personalizada»**. El correo sale con el diseño de la F. En el panel:

1. **La guía**: título, entrada, saludo y párrafo, caja final («Sin fricciones técnicas»…), texto del
   llamado y botón. Vienen rellenos con los textos actuales de la F.
2. **Para quién**: contacto y guardar, igual que en la H.
3. **Las fases**: tres tarjetas (Que te conozcan / Que te recuerden / Que te compren), cada una con:
   - interruptor (sale o no sale) y flechas ↑↓ para el orden;
   - epígrafe («Fase de atracción»), título, texto, etiqueta («Recomendado para empezar») y detalle;
   - **producto**: un desplegable con las líneas activas del catálogo (por defecto Tótem, LED, Rider);
   - **su presentación**: «Enlace de su presentación (vacío = el del catálogo)» y la galería para soltar
     el PDF o imágenes, elegir de 2 a 4 páginas y el efecto; «Volver al estándar».
4. **El mensaje**: versión corta para WhatsApp y despedida.
5. **Llevártela**: copiar para Gmail, HTML, texto y WhatsApp (por bloques, con enlace propio por fase),
   y «Marcar como entregada».

**Independent Test**: crear una guía para un contacto de prueba, apagar «Que te compren», cambiar el
título de la fase 1, poner Vallas en la fase 2 con un PDF propio y 2 páginas elegidas; el correo muestra
2 fases, con el título nuevo y el carrusel propio de Vallas; reabrir la entrega y está todo igual.

**Acceptance**:
1. Todo se guarda solo (como la H, 009) y al reabrir la entrega vuelve tal cual, incluidas las páginas
   elegidas de cada fase.
2. Un mismo producto no puede estar en dos fases: el desplegable no ofrece el que ya usa otra fase.
3. Una fase apagada no sale en el correo, ni en el texto, ni en WhatsApp.
4. Sin presentación propia, una fase usa el enlace y la foto/carrusel estándar del producto.
5. Los títulos y textos aceptan los mismos realces que la F (`*texto*`) y `{destinatario}`.

### US2 — Enlaces y seguimiento como la H (P1)

- Cada fase tiene su enlace propio `/p/<slug>/<producto>` (010): tarjeta de WhatsApp con su foto y
  nombre; la persona va a la presentación de esa fase (la propia o la estándar). Las aperturas se cuentan.
- `/p/<slug>` (el enlace de la entrega) lleva a la presentación de la **primera fase encendida**.
- «Copiar para WhatsApp» manda un mensaje principal y uno por fase (010), con casillas y «Copiar el siguiente».

### US3 — Las entregas de siempre no cambian (P1)

- Las plantillas A–H y los 16 correos de referencia salen idénticos byte a byte.
- Las entregas H existentes se abren y se comportan igual.
- En la lista de entregas del compositor se distingue cuál es H y cuál I; abrir una I lleva a la I.

## Requirements

- **FR-1201**: Nueva plantilla «I · Guía personalizada» en el compositor (solo con servidor y sesión).
- **FR-1202**: La entrega guarda su formato (`H` por defecto, `I`) y, en la I, los textos de la guía y
  de cada fase (epígrafe, título, texto, etiqueta, detalle, producto, encendida) y su orden.
- **FR-1203**: La presentación propia de cada fase reutiliza los espacios de la entrega (004): enlace,
  páginas, carrusel y efecto por producto, con «Volver al estándar».
- **FR-1204**: Guardado automático, aviso de «sin guardar» al copiar, enlaces propios, aperturas,
  WhatsApp por bloques y «Marcar como entregada», como en la H.
- **FR-1205**: Valores por defecto = los textos actuales de la F y sus productos (Tótem, LED, Rider).
- **FR-1206**: Las plantillas A–H, sus correos de referencia y las entregas H MUST NOT cambiar.

## Fuera de alcance (v1)

- Productos a medida (008) dentro de una fase: solo líneas del catálogo. Se puede añadir después.
- Más de un producto por fase, o más de tres fases.
- La lista de servicios complementarios del final de la F («también tenemos…»): la I no la lleva; la
  propuesta son sus fases.
- Cambiar la F de catálogo.

## Plan técnico

**Servidor** (`app/`):
- `models.Entrega`: columnas nuevas `formato` (`VARCHAR(2)`, por defecto `H`) y `guia` (`TEXT`, JSON):
  `{entrada, saludo, parrafo, caja_titulo, caja_texto, cta_texto, boton, fases: [{clave, on, fase,
  titulo, texto, etiqueta, detalle, linea}]}`. Migración en `app/migracion.py` como las de 009.
- Esquemas de entrada/salida de entregas: `formato` y `guia` (validados: 3 fases como máximo, claves
  conocidas, longitudes acotadas, líneas existentes y sin repetir).
- `servicios` y `orden_espacios` = las líneas de las fases encendidas, en su orden: así los enlaces
  propios `/p/<slug>/<linea>`, las aperturas y los espacios (004) funcionan sin cambios.
- `canva_url` de una I = la presentación de la primera fase encendida (la propia o la del catálogo); se
  recalcula al guardar.

**Compositor** (`prototipos/mail/compositor.html`, `render.js`):
- `render.js`: `plantillaI(st)`, a partir de `plantillaF`: lee las fases de la entrega en vez de las fijas;
  la foto de cada fase es el carrusel propio del espacio si lo tiene (`carruselPropio`) o la del
  catálogo; su enlace, el de la fase. `plantillaF` no se toca.
- `compositor.html`: panel de la I con los pasos 01–05; la tarjeta de fase reutiliza `galeria()` con la
  ruta del espacio de su producto; cambiar el producto de una fase con presentación propia pide
  confirmación (la propia es de ese producto). Abrir una entrega la lleva a H o I según `formato`.
- WhatsApp (010) y el texto plano: las fases encendidas, en su orden.

**Pruebas**: servidor (crear/guardar/reabrir una I, validación de fases, `canva_url` derivado, H
intacta); compositor (estático: pestaña I, F intacta); guardia de build (16 idénticas); demo en
navegador del Independent Test con 0 errores de consola y capturas.

## Tasks

- [x] T1201 Pruebas de servidor (RED): formato y guía, validación, derivados, H sin cambios — `tests/test_guia_personalizada.py`
- [x] T1202 Modelo, migración y esquemas — `app/models.py`, `app/migracion.py`, `app/mails/entregas/rutas.py`
- [x] T1203 `plantillaI` en `render.js` + registro de la plantilla; guardia de build intacta
- [x] T1204 Panel de la I en el compositor (pasos 01–05, tarjetas de fase con producto, textos, orden, galería)
- [x] T1205 Abrir/guardar/autoguardado de la I; lista de entregas con su formato
- [x] T1206 WhatsApp por bloques y texto plano para la I
- [x] T1207 Demo en navegador (Independent Test), capturas, 0 errores
- [x] T1208 Suite completa, build, README y Obsidian

## Notas de la implementación

- Cambiar el producto de una fase no pide confirmación (difiere del plan): la presentación propia del
  producto anterior no se borra, sigue en su espacio y vuelve si se elige otra vez.
- En epígrafe, título, etiqueta y detalle de una fase los `*` se quitan (van sin realce, como en la F);
  el título de la guía y los textos sí admiten `*realce*`.
- Referencias de la I: `tests/golden/plantilla-I-guiapropia*.html` (las 16 de A–H, intactas).
