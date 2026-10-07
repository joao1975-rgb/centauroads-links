# Tasks: Textos de los perfiles, editables por el equipo

**Input**: Design documents from `/specs/005-textos-perfiles/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: se escriben primero (TDD) y deben fallar antes de implementar.

**MVP**: Fases 1–4 (US1 + US2). Tras el MVP se para, se enseña y se espera «súbelo».

## Format: `[ID] [P?] [Story] Description`

- **[P]**: puede ir en paralelo (archivos distintos, sin dependencias)

## Phase 1: Setup

- [x] T501 Crear `app/mails/textos/__init__.py` y registrar su router en `app/main.py` (sin rutas aún)

## Phase 2: Foundational (bloquea todas las historias)

- [x] T502 [P] Prueba: `textosActuales()` del motor devuelve las ~62 claves de research R3, cada una con perfil, grupo, etiqueta, valor y límite, y el valor coincide con el texto que hoy pinta el motor — `tests/test_textos_motor.py`
- [x] T503 [P] Prueba: `build.js` deja `app/static/email/textos-perfil-serie.json` igual a `textosActuales()` y la guardia byte a byte sigue en 16 idénticas — `tests/test_textos_motor.py`
- [x] T504 Motor: pasar los textos de `rutaPasos`, `puentePhygital` y las cabeceras de `tablaDisponibilidad` a constantes (`RUTA`, `PUENTE`, `TABLA_CAB`) sin cambiar el HTML; añadir `textosActuales()` — `prototipos/mail/render.js`
- [x] T505 `build.js` exporta `textos-perfil-serie.json` y copia el motor a `app/static/email/` — `prototipos/mail/build.js`
- [x] T506 Modelo `TextoPerfil` (clave PK, valor, actualizado_por, actualizado_en) — `app/models.py`

**Checkpoint**: motor con catálogo de textos, sin ningún cambio visible; 16 correos idénticos.

## Phase 3: User Story 1 — Ajustar el mensaje de un perfil (P1) 🎯 MVP

- [x] T507 [P] [US1] Prueba del motor: `ponTextos({'agencia.titulo': X, 'agencia.cta': Y})` → los correos con perfil agencia llevan X e Y; los de los otros perfiles salen idénticos; `ponTextos({})` devuelve los 16 de referencia — `tests/test_textos_motor.py`
- [x] T508 [P] [US1] Prueba del motor: `{empresa}` y `{destinatario}` se sustituyen en asunto, texto previo, título, subtítulo, entrada, cierre y botón; `<b>` en un texto sale escapado — `tests/test_textos_motor.py`
- [x] T509 [P] [US1] Pruebas de API: GET de cambios (cualquier sesión), PUT/DELETE solo administrador (403 comercial, 401 sin sesión, 403 sin origen propio), 404 clave desconocida, 400 vacío, 422 largo, igual al de serie = borra la fila, quién y cuándo — `tests/test_textos_api.py`
- [x] T510 [US1] Motor: `ponTextos(cambios)` sobre copia de serie de `PERFILES` (mensaje); extender `fill()` a los campos que falten (research R5) — `prototipos/mail/render.js`
- [x] T511 [US1] API: `GET /api/textos-perfil`, `GET /api/panel/textos`, `PUT` y `DELETE /api/panel/textos/{clave}` con validación contra el JSON de serie — `app/mails/textos/rutas.py`
- [x] T512 [US1] Compositor: pide `/api/textos-perfil` al abrir (junto a `/api/catalogo`), llama a `ponTextos` y avisa si falla (FR-513) — `prototipos/mail/compositor.html`
- [x] T513 [P] [US1] Prueba de la pantalla: sin sesión → entrada; comercial ve sin editar; administrador edita — `tests/test_textos_pantalla.py`
- [x] T514 [US1] Pantalla `/panel/textos` modelada en `/panel/lineas`: perfiles como pestañas, grupo «Mensaje», campo por texto con su límite, guardar; solo lectura para comerciales; enlace en el menú del panel — `app/mails/textos/pantalla.py`

**Checkpoint**: un administrador cambia el título de agencias y otra sesión lo ve en su correo.

## Phase 4: User Story 2 — Los tres asuntos de cada perfil (P1) 🎯 MVP

- [x] T515 [P] [US2] Prueba del motor: `ponTextos({'general.asunto.curiosidad': X})` → `asuntosDe` ofrece X con clave y etiqueta iguales; un emoji se conserva — `tests/test_textos_motor.py`
- [x] T516 [US2] Motor: `ponTextos` aplica también a `ASUNTOS` — `prototipos/mail/render.js`
- [x] T517 [US2] Pantalla: grupo «Asuntos» en cada perfil (etiqueta fija, texto editable) — `app/mails/textos/pantalla.py`
- [x] T518 [US2] Demo en navegador (scratchpad): administrador cambia título, botón y un asunto; otra sesión arma el correo y los ve; consola sin errores; capturas a 600 y 375 px

**Checkpoint MVP**: suite completa en verde, guardia de 16, demo; revisión de seguridad; parar y enseñar.

## Phase 5: User Story 3 — El bloque propio de cada perfil (P2)

- [x] T519 [P] [US3] Prueba del motor: cambiar `nuevo.ruta.2.objetivo`, `phygital.puente.2.texto` y `agencia.tabla.trafico` → salen en su sitio en todas las plantillas que pintan ese bloque y en ningún otro perfil — `tests/test_textos_motor.py`
- [x] T520 [US3] Motor: `ponTextos` aplica a `RUTA`, `PUENTE` y `TABLA_CAB` — `prototipos/mail/render.js`
- [x] T521 [US3] Pantalla: grupos «Ruta de tres pasos», «Puente» y «Tabla de disponibilidad» en su perfil — `app/mails/textos/pantalla.py`

## Phase 6: User Story 4 — Volver al texto de serie (P3)

- [x] T522 [P] [US4] Prueba de la pantalla: marca de «cambiado» con quién y cuándo; botón «Volver al de serie» llama a DELETE — `tests/test_textos_pantalla.py`
- [x] T523 [US4] Pantalla: marcas de cambiado, contador por perfil y «Volver al de serie» — `app/mails/textos/pantalla.py`

## Phase 7: Polish

- [x] T524 README: sección «Textos de los perfiles» — `README.md`
- [ ] T525 Revisión de seguridad (permisos, escape, origen) y suite completa
- [ ] T526 Nota de Obsidian del proyecto actualizada

## Notas de la implementación (MVP, 2026-10-06)

- **30 textos en el MVP**, no ~33: el `asunto` propio de cada perfil no se ofrece. En el correo siempre
  manda uno de los tres asuntos o el escrito a mano, así que editarlo no cambiaría nada. Al revisarlo
  apareció un fallo previo: con un perfil distinto del General, el perfil pisaba el asunto escrito a
  mano («El mío»). Arreglado en `aplicaPerfil`, con prueba.
- El General no tiene mensaje propio (sus textos son los del compositor): en la pantalla solo salen sus
  tres asuntos.
- T504 (pasar ruta, puente y tabla a constantes) se hizo con la US3, que es quien los necesitaba.
- US3 (2026-10-06): 22 textos de bloque (ruta 12, puente 7, tabla 3); 52 en total. La nota del puente
  y las cabeceras de la tabla, que eran literales, ahora pasan por esc(). El bloque sale en A-D (E-G son
  los formatos del asesor, sin bloque de perfil). La etiqueta «Resuelve:» de la ruta sigue fija.
- US4 adelantada: «Volver al de serie», la marca de cambiado con quién y cuándo y el contador por perfil
  salieron casi gratis con la pantalla del MVP (T522/T523).

## Dependencies & Execution Order

- Fase 2 bloquea todo. US1 antes que US2 (comparten `ponTextos` y la pantalla). US3 y US4 dependen de US1.
- Dentro de cada historia: pruebas [P] primero (fallan), luego motor → API → compositor → pantalla.
