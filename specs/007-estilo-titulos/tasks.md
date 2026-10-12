# Tasks: Estilo de los títulos (tipografía y tamaño)

**Input**: [spec.md](spec.md), [plan.md](plan.md). Pruebas primero (deben fallar antes de implementar).

## Phase 1: US1 — La pareja de tipografías (P1)

- [ ] T701 [P] Pruebas del motor: sin elección y con `centauro` los 16 correos son idénticos; con cada pareja, en A–H, el título y el texto usan sus pilas; el título principal va en mayúsculas (impacto) o itálica (editorial); el texto plano y WhatsApp no cambian; después de renderizar con una pareja, el siguiente correo sin pareja sale como hoy — `tests/test_estilo_titulos_motor.py`
- [ ] T702 `PAREJAS`; `FH`/`FS`/`FB` como `let`, cambiadas y devueltas en `render()` — `prototipos/mail/render.js`
- [ ] T703 Estilo del título principal (mayúsculas, itálica) en A, B, D, E, F, G y H — `prototipos/mail/render.js`

## Phase 2: US2 — El tamaño del título (P1)

- [ ] T704 [P] Pruebas del motor: Base/Grande/Máximo = ×1/×1,25/×1,5 en cada plantilla; una palabra larga en Máximo se ajusta y no baja del base; `tamanoTitulo` dice `ajustado` — `tests/test_estilo_titulos_motor.py`
- [ ] T705 Calibrar los anchos medios de carácter de cada pila midiendo en navegador (Playwright) — guion en el scratchpad, valores en `render.js`
- [ ] T706 `tamanoTitulo()` y su uso en los títulos principales — `prototipos/mail/render.js`
- [ ] T707 Compositor: grupo «Estilo del título» (A–G antes de los bloques; H en el paso 01) y aviso de ajuste — `prototipos/mail/compositor.html`

## Phase 3: US3 — Que se conserve (P2)

- [ ] T708 [P] Pruebas de API: la entrega guarda y devuelve `tipografia` y `tam_titulo`; valores no permitidos → 400; un PUT sin ellos no los borra — `tests/test_entregas_estilo.py`
- [ ] T709 Columnas, migración y API — `app/models.py`, `app/migracion.py`, `app/mails/entregas/rutas.py`
- [ ] T710 Compositor: `guardaEntrega` los envía y `abreEntrega` los restaura — `prototipos/mail/compositor.html`

## Phase 4: Cierre

- [ ] T711 Demo en navegador: plantillas A, B, D, E, F, G, H × 4 parejas × Máximo a 600 y 375 px, 0 px de desborde y 0 errores de consola; capturas para la propietaria
- [ ] T712 Suite completa, build (16 idénticas), README y nota de Obsidian
