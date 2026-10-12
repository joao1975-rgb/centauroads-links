# Tasks: Producto a medida en la entrega (H)

**Input**: [spec.md](spec.md), [plan.md](plan.md). Pruebas primero (deben fallar antes de implementar).

## Phase 1: US1 — Añadir un producto que no está en el catálogo (P1)

- [ ] T801 [P] Pruebas de API: alta con nombre (201, sale en `espacios` con `a_medida`), sin nombre → 400, enlace inválido → 400, el sexto → 409; subir y armar su carrusel; un id a medida de otra entrega → 404; un comercial que no es dueño → 404 — `tests/test_entregas_a_medida.py`
- [ ] T802 [P] Pruebas del motor: la H lo pinta después de los del catálogo con su carrusel, su texto y «Ver presentación»; sin enlace no hay enlace vacío; sin nombre no sale; A–G y un estado sin `aMedida` salen idénticos; texto plano de la H sin « — » sueltos — `tests/test_a_medida_motor.py`
- [ ] T803 `es_a_medida`, `_espacio()` en lugar de `_catalogo()` en subir/elegir, alta `POST /api/entregas/{id}/espacios` con tope de 5, `a_medida` en la salida — `app/mails/entregas/espacios.py`, `app/mails/entregas/rutas.py`
- [ ] T804 Motor: `aMedida` al final de los espacios de la H; foto y «Ver presentación» solo con enlace; texto plano sin partes vacías — `prototipos/mail/render.js`
- [ ] T805 Compositor: fichas de los productos a medida tras los del catálogo (nombre, texto, enlace, galería) y «+ Añadir otro producto» (sin entrega guardada, avisa; con 5, se desactiva y dice por qué) — `prototipos/mail/compositor.html`

## Phase 2: US2 — Editarlo, quitarlo y recuperarlo (P1)

- [ ] T806 [P] Pruebas de API: editar nombre/texto/enlace; nombre vacío → 400 y la fila sigue; quitar borra la fila y deja las imágenes en disco; abrir la entrega los devuelve con su carrusel — `tests/test_entregas_a_medida.py`
- [ ] T807 `PUT` y `DELETE` de un producto a medida (sin R8; nunca se borra la fila por quedar vacía) — `app/mails/entregas/espacios.py`
- [ ] T808 Compositor: «Quitar» con confirmación; `abreEntrega` reparte los espacios entre `aMedida` y `espacios` — `prototipos/mail/compositor.html`

## Phase 3: US3 — Pasar al catálogo (P2)

- [ ] T809 [P] Pruebas de API: un administrador lo pasa → línea con su nombre, texto, enlace, todas las plantillas y la primera imagen como foto; carpeta copiada (la vieja sigue); la fila pasa a la línea con su carrusel; incluido en `servicios`; nombre ya existente → 409 sin crear nada; comercial → 403; un espacio del catálogo → 400 — `tests/test_entregas_a_medida.py`
- [ ] T810 `POST /api/entregas/{id}/espacios/{linea}/catalogo` (validación y alta con las funciones del catálogo, foto por `fotos.prepara`/`guarda`, copia de carpeta, un solo commit) — `app/mails/entregas/espacios.py`
- [ ] T811 Compositor: «Pasar al catálogo» solo para administradores (`/api/auth/yo`); al terminar, catálogo recargado y el producto convertido en ese espacio — `prototipos/mail/compositor.html`

## Phase 4: Cierre

- [ ] T812 Demo en navegador: añadir, subir PDF, editar, quitar y pasar al catálogo; H a 600 y 375 px sin desborde; cero errores de consola; capturas para la propietaria
- [ ] T813 Revisión de seguridad (entrada no confiable en rutas y nombres de carpeta, dueño de la entrega, alta en el catálogo)
- [ ] T814 Suite completa, build (16 idénticas), README y nota de Obsidian
