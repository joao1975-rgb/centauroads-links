# Tasks: Catálogo de líneas de negocio

**Input**: Design documents from `/specs/003-catalogo-lineas/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: incluidas. Las reglas del proyecto exigen pruebas primero (RED → GREEN): cada historia
empieza por sus pruebas, que deben fallar antes de implementar.

**Organization**: por historia de usuario, para poder entregar y probar cada una por separado.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia a la que pertenece (US1…US5)

---

## Phase 1: Setup

- [x] T301 Crear el módulo `app/mails/catalogo/__init__.py` (router vacío) y montarlo en `app/main.py` junto a los de auth y entregas
- [x] T302 [P] Hacer que `prototipos/mail/build.js` exporte `app/static/email/catalogo-serie.json` (líneas con ficha y familia, familias, plantillas = `ABCDEFGH`) a partir de `SERVICIOS`, `GRUPOS` y `FICHA` de `render.js`

---

## Phase 2: Foundational (bloquea todas las historias)

- [x] T303 Pruebas de siembra en `tests/test_catalogo_api.py`: con base vacía se crean las 5 líneas y las 3 familias exactamente como en `catalogo-serie.json`; la siembra es idempotente; no pisa una base que ya tiene catálogo
- [x] T304 Pruebas del motor en `tests/test_catalogo_motor.py`: sin `ponCatalogo` los 16 correos de referencia no cambian; con `ponCatalogo(catálogo de serie)` tampoco; con una línea nueva, `normaliza()` la incorpora
- [x] T305 Modelos `LineaNegocio` y `FamiliaD` en `app/models.py` según `data-model.md`
- [x] T306 Siembra en `app/mails/catalogo/siembra.py` y llamada al arrancar en `app/main.py`, después de `create_all` y `migrar`
- [x] T307 `ponCatalogo({lineas, familias})` en `prototipos/mail/render.js`: reemplaza en sitio `SERVICIOS`, `GRUPOS`, `FICHA` y `BANCO` (una línea nueva entra con su foto principal en el banco); exportarlo; `imgFor()` respeta direcciones absolutas
- [x] T308 `GET /api/catalogo` en `app/mails/catalogo/rutas.py` (solo activas, en orden, forma de `ponCatalogo`) con pruebas de 401 sin sesión y 200 con sesión
- [x] T309 Compositor (`prototipos/mail/compositor.html`): con servidor, pedir `/api/catalogo` y llamar a `ponCatalogo` antes de construir el panel y pintar; si falla, seguir con el catálogo de serie y avisarlo (FR-323)

**Checkpoint**: el motor acepta un catálogo externo sin cambiar nada de lo que ya sale.

---

## Phase 3: User Story 1 - Añadir una línea nueva y usarla en el siguiente correo (P1) 🎯 MVP

**Goal**: un administrador da de alta una línea con foto y enlace y todo el equipo la ve en el compositor sin desplegar.

**Independent Test**: alta de una línea por la API o la pantalla → aparece en el compositor de otra sesión y en el correo de una plantilla, con su nombre, foto y enlace.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [x] T310 [P] [US1] Pruebas de alta en `tests/test_catalogo_api.py`: administrador 201; comercial 403; sin sesión 401; nombre repetido 409 (sin distinguir mayúsculas); enlace que no es `http(s)` 400; id derivado del nombre y estable al renombrar
- [x] T311 [P] [US1] Pruebas de fotos en `tests/test_catalogo_api.py`: imagen válida se reduce a 1072 px y se sirve en `/media/lineas/…`; archivo que no es imagen 400; más de 8 MB 413; nombre fuera de la lista blanca 404
- [x] T312 [P] [US1] Pruebas de la pantalla en `tests/test_catalogo_pantalla.py`: sin sesión 307 a la entrada; comercial la ve en solo lectura; la página no usa `innerHTML`; el compositor la enlaza
- [x] T313 [P] [US1] Pruebas del motor en `tests/test_catalogo_motor.py`: una línea nueva activa sale en las 8 plantillas × 4 perfiles con su nombre, foto, alt y enlace; sin foto no deja imagen rota

### Implementation for User Story 1

- [x] T314 [US1] `POST /api/panel/lineas` y `GET /api/panel/lineas` en `app/mails/catalogo/rutas.py` con la validación de `contracts/api.md` (solo administradores)
- [x] T315 [US1] Fotos en `app/mails/catalogo/fotos.py` (validar con Pillow, reducir, JPEG 82, nombre con huella, carpeta `/app/data/lineas`) y rutas `POST /api/panel/lineas/{id}/foto` y `GET /media/lineas/{archivo}`
- [x] T316 [US1] Pantalla `/panel/lineas` en `app/mails/catalogo/pantalla.py` (patrón de `app/auth/equipo.py`): lista de líneas y formulario de alta con foto y texto alternativo; enlace «Líneas de negocio» en el menú del compositor
- [x] T317 [US1] Motor: una línea sin foto sale sin imagen rota en todas las plantillas (`prototipos/mail/render.js`)

**Checkpoint**: alta completa y visible en los correos; US1 probada sola.

---

## Phase 4: User Story 2 - Decidir en qué plantillas aparece (P1)

**Goal**: cada línea sale solo en las plantillas marcadas.

**Independent Test**: línea incluida solo en A y H → aparece en A y H y en ninguna otra (8 × 4).

### Tests for User Story 2 ⚠️

- [x] T318 [P] [US2] Pruebas del motor en `tests/test_catalogo_motor.py`: matriz 8 plantillas × 4 perfiles con una línea en `AH` → 100 % en A y H, 0 % en el resto, también en texto plano y WhatsApp; el estado de la persona no se modifica
- [x] T319 [P] [US2] Pruebas de API en `tests/test_catalogo_api.py`: `plantillas` por defecto `ABCDEFGH`; letras inválidas o repetidas 400; vacío sin `confirmarSinPlantillas` 400 y con él 201

### Implementation for User Story 2

- [x] T320 [US2] `render()` en `prototipos/mail/render.js`: trabajar sobre una copia con `on = false` en las líneas no incluidas en la plantilla del correo
- [x] T321 [US2] Compositor: junto a cada línea, «no se usa en esta plantilla» cuando corresponda (FR-310), usando la misma marca `nousa` que los bloques
- [x] T322 [US2] Pantalla y API: casillas A–H (todas marcadas por defecto) y confirmación al guardar sin ninguna

**Checkpoint**: US1 + US2 = MVP entregable.

---

## Phase 5: User Story 3 - Editar, ordenar y retirar (P2)

**Goal**: las cinco líneas actuales y las nuevas se editan, reordenan, retiran y devuelven.

**Independent Test**: retirar una línea → no sale en correos nuevos; devolverla → vuelve igual; cambiar el orden → los correos lo siguen.

### Tests for User Story 3 ⚠️

- [x] T323 [P] [US3] Pruebas de API: `PATCH` edita solo lo enviado; retirar y devolver; `POST /api/panel/lineas/orden`; `/api/catalogo` no entrega retiradas; comercial 403
- [x] T324 [P] [US3] Pruebas de migración del estado en `tests/test_catalogo_motor.py`: con un estado guardado viejo, la línea nueva entra, la retirada sale y el texto escrito a mano en una línea que sigue se conserva; un perfil con orden propio deja las líneas no nombradas detrás (FR-316)

### Implementation for User Story 3

- [x] T325 [US3] `PATCH /api/panel/lineas/{id}` y `POST /api/panel/lineas/orden` en `app/mails/catalogo/rutas.py`
- [x] T326 [US3] Pantalla: editar en la fila, retirar/devolver (retiradas aparte) y subir/bajar en el orden
- [x] T327 [US3] Ajustar `normaliza()` solo si las pruebas de T324 lo exigen (sin subir `CONTENT_VERSION`)

---

## Phase 6: User Story 4 - Ficha técnica opcional (P2)

**Goal**: una línea con ficha entra en la tabla de agencias y en el inventario de la E; sin ficha, no.

**Independent Test**: una línea con ficha y otra sin ella → la primera tiene fila en ambas tablas; la segunda en ninguna.

### Tests for User Story 4 ⚠️

- [x] T328 [P] [US4] Pruebas del motor: fila en la tabla de agencias y en el inventario de la E solo con ficha; las cinco filas de serie de la E no cambian; el precio "desde" solo sale con el modo de precios encendido

### Implementation for User Story 4

- [x] T329 [US4] Inventario de la E en `prototipos/mail/render.js`: filas genéricas, detrás de las cinco de serie, para las líneas activas con ficha
- [x] T330 [US4] Campos de ficha (ubicación, medidas, tráfico, precio "desde") en la pantalla y en la API

---

## Phase 7: User Story 5 - Familias de la plantilla D (P3)

**Goal**: la D presenta cada línea dentro de su familia.

**Independent Test**: línea en una familia nueva incluida en D → la D muestra esa familia con la línea.

### Tests for User Story 5 ⚠️

- [ ] T331 [P] [US5] Pruebas del motor: familia existente, familia nueva y sin familia («Otros servicios»); la D de serie no cambia
- [ ] T332 [P] [US5] Pruebas de API: `POST /api/panel/familias` (administrador 201, comercial 403, título repetido 409)

### Implementation for User Story 5

- [ ] T333 [US5] `GRUPOS` desde las familias del catálogo y grupo «Otros servicios» en `prototipos/mail/render.js`
- [ ] T334 [US5] `POST /api/panel/familias` y selector de familia (existente o nueva) en la pantalla

---

## Phase 8: Polish & Cross-Cutting

- [ ] T335 `node prototipos/mail/build.js`: guardia byte a byte (16 correos idénticos) y guardia de contenido; suite completa en verde
- [ ] T336 Verificación visual con Playwright de A, D, E y H con una línea nueva, a 600 y 375 px, sin desborde (principio III)
- [x] T337 [P] Revisión de seguridad (agente `security-reviewer`) de las rutas nuevas y la subida de fotos
- [ ] T338 Recorrido de `quickstart.md` en local con datos de prueba; `/health` y un enlace corto del acortador intactos
- [ ] T339 [P] README (sección «Líneas de negocio») y nota de Obsidian `Centauro-Mails-Servicios.md`

---

## Dependencies & Execution Order

- **Setup (T301–T302)** → **Foundational (T303–T309)** → historias.
- **US1 (P1)** es el MVP y la base de la pantalla; **US2 (P1)** depende de US1 (pantalla y API).
- **US3, US4 y US5** dependen de US1 y son independientes entre sí.
- **Polish** al final.

```text
Setup → Foundational → US1 → US2 ─┬─ US3
                                  ├─ US4
                                  └─ US5 → Polish
```

## Parallel Example: User Story 1

```text
T310 pruebas de alta      ┐
T311 pruebas de fotos     │ en paralelo (archivos o partes distintas)
T312 pruebas de pantalla  │
T313 pruebas del motor    ┘
→ después T314 → T315 → T316 → T317
```

## Implementation Strategy

1. **MVP = US1 + US2**: con eso se cumple lo que se pidió (añadir líneas y elegir en qué plantillas
   aparecen). Se verifica, se enseña y se sube con «súbelo».
2. **Incremento 2 = US3 + US4**: editar/retirar y fichas.
3. **Incremento 3 = US5**: familias de la D.
4. Cada incremento pasa la guardia byte a byte y la verificación visual antes de subirse.
