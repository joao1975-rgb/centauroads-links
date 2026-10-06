# Tasks: Espacios que acompañan, personalizados en la entrega

**Input**: Design documents from `/specs/004-espacios-acompanantes/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md, quickstart.md

**Tests**: incluidas. Las reglas del proyecto exigen pruebas primero (RED → GREEN): cada historia
empieza por sus pruebas, que deben fallar antes de implementar.

**Organization**: por historia de usuario, para poder entregar y probar cada una por separado.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia a la que pertenece (US1…US4)

---

## Phase 1: Setup

- [x] T401 Modelo `EntregaEspacio` en `app/models.py` según `data-model.md` (tabla nueva `entrega_espacios`, creada por `create_all`; `UNIQUE(entrega_id, linea_id)`); prueba en `tests/test_entregas_espacios.py` de que la tabla existe y `migrar()` no cambia
- [x] T402 [P] `app/mails/entregas/almacen.py`: carpeta y resolución de un espacio (`entregas/<id>/espacios/<linea>/`) con lista blanca para `<linea>` y comprobación de destino, como la principal

---

## Phase 2: Foundational (bloquea todas las historias)

- [x] T403 Punto de control: `tests/test_entregas_api.py` en verde **antes** de tocar nada (la principal es la referencia de comportamiento)
- [x] T404 Extraer a `app/mails/entregas/galeria.py` la subida de páginas y el armado del carrusel, parametrizados por carpeta; `rutas.py` los usa para la principal y `tests/test_entregas_api.py` sigue en verde sin cambiarlo
- [x] T405 [P] Ruta pública `GET /media/entregas/{id}/espacios/{linea}/{fichero}` en `publicas.py`, con pruebas de lista blanca (traversal en `linea` y en `fichero`, mayúsculas, extensiones) → 404
- [x] T406 `EntregaSalida` gana `espacios` (lista vacía si no hay); prueba en `tests/test_entregas_espacios.py`
- [x] T407 Motor (`prototipos/mail/render.js`): `bloques.entrega.espacios = {}` e `incluidos` en `defaultState`; `normaliza()` inicializa `incluidos` con los servicios encendidos si falta; prueba en `tests/test_espacios_motor.py` de que un estado viejo sobrevive y los 16 correos siguen idénticos

**Checkpoint**: la principal se comporta igual con el código compartido; el motor acepta los campos nuevos sin cambiar nada de lo que ya sale.

---

## Phase 3: User Story 1 - El carrusel de un espacio sigue a su presentación (P1) 🎯 MVP

**Goal**: cada espacio acompañante puede armar su propio carrusel con el mismo flujo que la principal.

**Independent Test**: entrega guardada → en un espacio, subir un PDF de 3 páginas, elegir 2 → la H muestra ese carrusel en ese espacio; los demás, estándar.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [x] T408 [P] [US1] API en `tests/test_entregas_espacios.py`: subir PDF/imágenes a un espacio y elegir 2–4 páginas con efecto → carrusel en su subcarpeta; aviso de precio; límites y mensajes de la principal; sin sesión 401; línea o entrega inexistente 404; **independencia**: rehacer la principal no toca el espacio, rehacer un espacio no toca la principal ni otro espacio
- [x] T409 [P] [US1] Motor en `tests/test_espacios_motor.py`: con `espacios[id].carrusel`, la H usa ese carrusel en ese espacio y el estándar en los demás; con el mismo estado, A–G salen estándar

### Implementation for User Story 1

- [x] T410 [US1] `app/mails/entregas/espacios.py`: `POST` y `PUT /api/entregas/{id}/espacios/{linea}/paginas` sobre `galeria.py`; la fila `EntregaEspacio` guarda `efecto` y `paginas` (JSON); montaje en `app/mails/entregas/__init__.py`
- [x] T411 [US1] Motor: `carruselPropio` en `carruselSrc`/`fotoServicio`; `plantillaH` arma una copia del estado con el carrusel propio de cada espacio
- [x] T412 [US1] Compositor (`prototipos/mail/compositor.html`): la subida, las miniaturas y el armado de la principal pasan a un componente `galeria({...})` con estado por instancia; la principal se comporta igual
- [x] T413 [US1] Compositor: en cada espacio de «Espacios que la acompañan», «Imágenes de su presentación» con `galeria()` contra las rutas del espacio; el carrusel queda en `bloques.entrega.espacios[id].carrusel`; sin entrega guardada, el aviso de la principal

**Checkpoint**: un espacio arma su carrusel y la H lo muestra; la principal intacta.

---

## Phase 4: User Story 2 - Lo que se cambia se queda en esta entrega (P1)

**Goal**: enlace, nombre, cobertura y selección de cada espacio valen solo para la entrega.

**Independent Test**: personalizar un espacio → la plantilla A y otra entrega lo muestran estándar; desmarcarlo en la H no lo apaga en A.

### Tests for User Story 2 ⚠️

- [x] T414 [P] [US2] API en `tests/test_entregas_espacios.py`: `PUT …/espacios/{linea}` guarda textos y enlace; un valor igual al del catálogo queda estándar; enlace sin `https://` 400 con el mensaje de la principal; `DELETE` vuelve al estándar y conserva las imágenes; 401/404
- [x] T415 [P] [US2] Motor en `tests/test_espacios_motor.py`: enlace/nombre/cobertura propios solo en la H; con `incluidos`, la H lleva exactamente esos espacios y A–G siguen con el `on` global; el estado de la persona no se modifica

### Implementation for User Story 2

- [x] T416 [US2] `PUT` y `DELETE /api/entregas/{id}/espacios/{linea}` en `espacios.py` (estándar = igual al catálogo de `lineas_negocio`; fila vacía se borra)
- [x] T417 [US2] Motor: la copia de la H aplica `canva`, `nombre`, `cobertura` de `espacios` y `on` según `incluidos`
- [x] T418 [US2] Compositor: en la H los espacios editan `bloques.entrega.espacios` e `incluidos` (no `st.servicios`); se sincronizan con el servidor; `guardaEntrega` manda `servicios` desde `incluidos`

**Checkpoint**: US1 + US2 = MVP entregable.

---

## Phase 5: User Story 3 - Se ve qué está personalizado y se puede volver al estándar (P2)

- [ ] T419 [P] [US3] Prueba del compositor (estática + demo): cada espacio dice «Estándar» o «Personalizado para esta entrega» y qué tiene propio
- [ ] T420 [US3] Compositor: la marca, la lista de lo propio y «Volver al estándar» (`DELETE` + limpiar `espacios[id]`)

---

## Phase 6: User Story 4 - Al reabrir la entrega, todo sigue ahí (P2)

- [ ] T421 [P] [US4] API: `GET /api/entregas/{id}` devuelve los espacios con su carrusel versionado (`?v=`) y sus páginas
- [ ] T422 [US4] Compositor: «Abrir una entrega guardada» en el paso 01 (lista de `GET /api/entregas`); carga enlace, título, texto, contacto, `incluidos`, carrusel principal y espacios
- [ ] T423 [US4] Demo: abrir en otra sesión una entrega con espacios personalizados → panel y correo iguales

---

## Phase 7: Polish & Cross-Cutting

- [ ] T424 `node prototipos/mail/build.js`: guardia byte a byte (16 correos idénticos) y guardia de contenido; suite completa en verde
- [ ] T425 Verificación visual con Playwright de la H con dos espacios personalizados a 600 y 375 px, sin desborde y con cero errores de página (principio III)
- [x] T426 [P] Revisión de seguridad (agente `security-reviewer`): subidas por espacio, ruta pública con `linea`, permisos
- [ ] T427 Recorrido de `quickstart.md` en local con datos de prueba; `/health` y `/p/{slug}` intactos
- [ ] T428 [P] Nota de Obsidian `Centauro-Mails-Servicios.md` y memoria del proyecto

---

## Dependencies & Execution Order

- **Setup (T401–T402)** → **Foundational (T403–T407)** → historias.
- **US1 (P1)** y **US2 (P1)** forman el MVP; US2 reutiliza las rutas y la vista de espacios de US1.
- **US3** depende de US2 (necesita lo propio guardado); **US4** depende de US1 y US2.
- **Polish** al final.

```text
Setup → Foundational → US1 → US2 ─┬─ US3
                                  └─ US4 → Polish
```

## Parallel Example: User Story 1

```text
T408 pruebas de API    ┐ en paralelo (archivos distintos)
T409 pruebas del motor ┘
→ después T410 → T411 → T412 → T413
```

## Implementation Strategy

1. **MVP = US1 + US2**: con eso se cumple lo pedido (el carrusel de cada espacio sigue a su
   presentación, y lo que se cambia se queda en la entrega). Se verifica, se enseña y se sube con
   «súbelo».
2. **Incremento 2 = US3 + US4**: la marca y el retorno al estándar, y reabrir la entrega.
3. Cada incremento pasa la guardia byte a byte y la verificación visual antes de subirse.
