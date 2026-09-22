# Tasks: Módulo de mails de servicios

**Fecha**: 2026-09-19 | **Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

**Estado a 2026-09-22**: 14 de 57 hechas, todas de la fase 2. Verificado contra el código, no
contra la memoria.

| Bloque | Estado |
|---|---|
| Fase 1 · Setup (T001-T004) | Hecha salvo **T003**: hay pruebas en `tests/` pero `pytest` no está declarado, así que una máquina limpia no puede ejecutarlas |
| Fase 2 · Migración e identidad (T005-T014, T017) | **Hecha**. `app/auth/` completo, modelos ampliados de forma aditiva, `app/migracion.py` llamado al arrancar, pruebas de acortador, migración y acceso en verde |
| Fase 2 · Panel (T015-T016) | **Abiertas**. No hay pantalla de entrada y `app/main.py` sigue autenticando con la clave compartida (`require_admin`) |
| Fase 2 · Contenido a datos (T018-T021) | **Aplazadas**: dependen del puerto a Jinja2 |
| Fase 3 · El motor en Python (T022-T037) | **Aplazadas a propósito**. La [002](../002-entregas/plan.md), decisión D1, mantiene `render.js` como motor único y deja el puerto para cuando el servidor tenga que renderizar por su cuenta, es decir, para el envío automático |
| Fases 4-6 (T038-T057) | Sin empezar. La 002 cubre el seguimiento y los avisos **de las entregas**; estas siguen siendo las del catálogo |

Lo que hoy usa el equipo no es este módulo: es el compositor estático de `app/static/email/`,
publicado por `prototipos/mail/build.js`. Eso no es un descuido, es el estado real, y la 002 lo
toma como punto de partida en vez de fingir que la fase 3 está hecha.

## Format: `[ID] [P?] [Story] Description`

- **[P]** = puede hacerse en paralelo con otras marcadas [P] (ficheros distintos, sin dependencia).
- **[US1..US4]** = a qué historia de usuario pertenece.
- Sin marca = tarea de cimientos o transversal.

## Path Conventions

Rutas relativas a la raíz del repositorio `centaurads-links`. El módulo vive en `app/mails/`, la
identidad en `app/auth/`, las pruebas en `tests/`.

---

## Phase 1: Setup

- [x] **T001** Crear el esqueleto de paquetes: `app/mails/__init__.py`, `app/auth/__init__.py` y el árbol de carpetas del plan (`datos/`, `plantillas/bloques/`, `panel/`).
- [x] **T002** Añadir a `requirements.txt` las dependencias de etapa 1: `itsdangerous`, `google-auth`, `argon2-cffi`, `httpx`. **No** añadir las de etapa 2 todavía.
- [ ] **T003** [P] Añadir `pytest` y `pytest-asyncio` como dependencias de desarrollo, con su configuración mínima.
- [x] **T004** [P] Copiar los ocho `prototipos/mail/plantilla-*.html` actuales a `tests/golden/` como ficheros de referencia, y dejar anotado en un README de esa carpeta de qué versión del motor JS salieron.

---

## Phase 2: Cimientos (bloquean todo lo demás)

**Nada de las historias puede empezar hasta que esta fase esté cerrada.**

### Migración de datos — la tarea de mayor riesgo del proyecto

- [x] **T005** Escribir `tests/test_migracion.py` **antes** que la migración: crea una base de datos con el esquema actual, mete enlaces y clics, y afirma que tras migrar siguen ahí con los mismos contadores. Debe fallar ahora mismo.
- [x] **T006** Ampliar `app/models.py` de forma aditiva: `Click.contact_token` y las cinco columnas nullable de `Delivery` descritas en [data-model.md](./data-model.md). No tocar ninguna columna existente.
- [x] **T007** Añadir los modelos nuevos: `Contact`, `PanelUser`, `SenderAccount`, `SenderPermission`, `Alert`, con el índice único `(contact_id, link_id, ventana_inicio)` en `alerts`.
- [x] **T008** Implementar la migración idempotente en `app/migracion.py`: inspecciona columnas reales, añade solo las que faltan, crea las tablas nuevas. Sin borrados, sin renombrados, sin cambios de tipo.
- [x] **T009** Llamar a la migración al arrancar en `app/main.py`, antes de servir tráfico. Verificar que T005 ahora pasa.
- [x] **T010** Escribir `tests/test_acortador.py`: las 13 rutas existentes responden lo mismo que antes del cambio. Es la red que protege el Principio I.

### Identidad del panel

- [x] **T011** [P] `app/auth/sesion.py`: cookie de sesión firmada con caducidad, clave leída del entorno y **validada al arrancar** (falla si no está).
- [x] **T012** [P] `app/auth/google.py`: verificar el identificador de Google Sign-In y **rechazar** toda cuenta que no sea del dominio `centauroads.com` (FR-001a).
- [x] **T013** [P] `app/auth/local.py`: alta y verificación de usuarios de excepción con hash argon2 (FR-001b). Nunca guardar ni registrar la contraseña en claro.
- [x] **T014** `app/auth/dependencias.py`: dependencias de FastAPI para usuario actual, rol y permiso sobre cuenta remitente. Aquí vive la regla de FR-004a: **una cuenta `personal` solo la usa su titular**.
- [ ] **T015** Pantalla de entrada al panel con los dos caminos, y cierre de sesión.
- [ ] **T016** Sustituir la clave única compartida de las rutas de administración por la dependencia de usuario. Mantenerla temporalmente como acceso de emergencia, con un aviso explícito en el registro cada vez que se use.
- [x] **T017** Pruebas de acceso: sin sesión no se entra; una cuenta de Google ajena al dominio se rechaza; una persona sin permiso sobre `equintero@` no puede usarla.

### Contenido a datos

- [ ] **T018** [P] Extraer el catálogo de espacios de `render.js` a `app/mails/datos/catalogo.yaml`, con su ficha técnica y el precio **opcional** por espacio.
- [ ] **T019** [P] Extraer los cuatro perfiles a `app/mails/datos/perfiles.yaml` (asunto, preheader, título, subtítulo, intro, cierre, botón, orden de espacios, bloque propio).
- [ ] **T020** [P] Extraer marca, firma y datos de contacto a `app/mails/datos/marca.yaml`. **Un solo lugar**, que es lo que exige FR-011 y lo que evita que reaparezcan datos retirados.
- [ ] **T021** `app/mails/contenido.py`: cargar y **validar** esos ficheros con Pydantic al arrancar. Un dato de contacto retirado o un fichero mal formado deben impedir el arranque, no descubrirse en un correo enviado.

---

## Phase 3: Historia 1 — Armar y llevarse el correo (P1) 🎯 MVP

**Se puede desplegar sola y ya quita la dependencia del portátil de una persona.**

- [ ] **T022** Escribir `tests/test_motor.py` contra los ficheros golden: para los mismos datos, el motor Python debe producir HTML equivalente al de referencia (comparación normalizando espacios). Debe fallar ahora.
- [ ] **T023** [US1] `app/mails/plantillas/base.html` y los parciales de `bloques/`: marca, servicios, firma y pie, con tablas anidadas y CSS inline.
- [ ] **T024** [P] [US1] Portar el formato **A** (Cartelera) a `formato_a.html` hasta que su golden pase.
- [ ] **T025** [P] [US1] Portar el formato **B** (Catálogo) hasta que su golden pase.
- [ ] **T026** [P] [US1] Portar el formato **C** (Nota) hasta que su golden pase.
- [ ] **T027** [P] [US1] Portar el formato **D** (Móvil) hasta que su golden pase.
- [ ] **T028** [P] [US1] Portar los bloques de perfil: tabla de disponibilidad, escalera de tres pasos y puente phygital.
- [ ] **T029** [US1] `app/mails/motor.py`: aplicar el perfil **sobre una copia** del estado, como hace hoy `aplicaPerfil`, para no pisar lo que la persona haya escrito a mano.
- [ ] **T030** [US1] Implementar la regla de precios: sin tarifa confirmada, "a cotizar" (FR-010). Prueba que lo fija: con precios activos y un espacio sin tarifa, el HTML **no** contiene ningún importe para ese espacio.
- [ ] **T031** [US1] `app/mails/rutas.py`: `GET /admin/mails` (panel) y `POST /api/mails/render` (devuelve el HTML del estado recibido).
- [ ] **T032** [US1] Compositor en `app/mails/panel/compositor.html`: selector de perfil, de formato, interruptores de espacios y bloques, y vista previa en iframe servida por el propio motor.
- [ ] **T033** [US1] Conmutador de vista previa escritorio (600 px) / móvil (~375 px), que es lo que pide el Principio III.
- [ ] **T034** [US1] Acción "copiar correo" con las imágenes apuntando a la URL pública absoluta de `app/static/email/`.
- [ ] **T035** [US1] Selector de cuenta remitente limitado a las que la persona tiene permitidas, con la firma cambiando en consecuencia (FR-009).
- [ ] **T036** [US1] **Verificación visual obligatoria**: revisar los cuatro formatos × cuatro perfiles renderizados, a 600 px y a 375 px, y con imágenes bloqueadas. No se cierra la historia sin esto.
- [ ] **T037** [US1] Retirar `prototipos/mail/` del camino de producción: pasa a ser herramienta de diseño y fuente de ficheros golden. Dejarlo anotado en su README para que nadie lo confunda con el motor vivo.

**Punto de control**: el equipo arma correos desde el panel, desde cualquier equipo, con identidad propia.

---

## Phase 4: Historia 2 — Saber a quién se le mandó qué (P2)

- [ ] **T038** Escribir `tests/test_enlaces.py`: dos contactos, dos enlaces, se abre uno; la apertura se atribuye a un solo contacto y la del enlace genérico queda anónima. Debe fallar ahora.
- [ ] **T039** [US2] CRUD de contactos en el panel, con generación del `token` único.
- [ ] **T040** [US2] `app/mails/enlaces.py`: generar `/slug?c=<token>` por destinatario al armar el correo.
- [ ] **T041** [US2] En la ruta de redirección del acortador, **leer** `?c=` y guardarlo en `Click.contact_token`. Cambio mínimo y aditivo; la redirección debe seguir funcionando igual si el parámetro no viene.
- [ ] **T042** [US2] Registrar una fila en `deliveries` con contacto, perfil, formato, cuenta remitente y persona, al armar o enviar el correo (FR-002, y la bitácora de FR-014).
- [ ] **T043** [US2] Vista de registro en el panel: por envío y por contacto, con las aperturas.
- [ ] **T044** [US2] Verificar que T010 (las rutas del acortador) sigue en verde tras tocar la redirección.

**Punto de control**: se sabe a quién se escribió y quién abrió.

---

## Phase 5: Historia 3 — Aviso de interés (P3)

- [ ] **T045** Escribir `tests/test_alertas.py`: tres aperturas del mismo contacto y enlace en 48 h generan **un** aviso; la cuarta no genera otro. Debe fallar ahora.
- [ ] **T046** [US3] `app/mails/alertas.py`: regla de las tres aperturas en 48 h, apoyada en el índice único para que el duplicado lo impida la base de datos, no la memoria del programador.
- [ ] **T047** [US3] Evaluar la regla al registrar cada clic atribuido, sin bloquear la redirección: el cliente no debe esperar por nuestra contabilidad.
- [ ] **T048** [US3] Mostrar los avisos en el panel, con marcarlos como atendidos.
- [ ] **T049** [US3] Aviso por correo **interno** al equipo comercial. Prueba explícita de que no sale nada hacia el cliente (FR-016).

**Punto de control**: el equipo se entera de que un cliente volvió, y el cliente no recibe nada.

---

## Phase 6: Historia 4 — Responder en el hilo (P4) · etapa 2

> **No empezar** hasta que las historias 1 a 3 estén en producción y asentadas.

- [ ] **T050** [US4] Añadir las dependencias de etapa 2 y el cifrado de tokens en reposo, con la clave por entorno.
- [ ] **T051** [US4] Flujo de autorización por buzón, una sola vez por cuenta, sin conocer contraseñas (FR-021).
- [ ] **T052** [US4] Lectura de solicitudes entrantes en los buzones conectados.
- [ ] **T053** [US4] Detección de espacios mencionados; si no menciona ninguno, catálogo completo (FR-018).
- [ ] **T054** [US4] Crear el borrador **en el hilo** y **en el buzón que recibió** el mensaje (FR-017), marcado con etiqueta propia (FR-020).
- [ ] **T055** [US4] Interruptor global "solo borrador", **encendido de fábrica**, con prueba de que impide cualquier envío automático (FR-019).
- [ ] **T056** [US4] Evitar el segundo borrador para un hilo que ya tiene uno.
- [ ] **T057** [US4] Aviso al equipo cuando una autorización caduca o se revoca, en vez de fallar en silencio.

---

## Dependencias

- **Phase 2 bloquea todo.** Sin migración probada e identidad, nada más debe tocarse.
- **T005 antes que T006–T009**: la prueba de migración se escribe primero, porque es la que protege los datos del acortador.
- **T022 antes que T023–T029**: los golden se ponen en verde, no se ajustan a lo que salga.
- **US2 → US3**: sin enlaces por destinatario no hay a quién avisar.
- **US4** depende de US1 (el motor) y de US2 (los enlaces).

## Notas

- Las tareas marcadas [P] tocan ficheros distintos y pueden repartirse.
- Las pruebas que dicen "debe fallar ahora" son deliberadas: si pasan antes de implementar, la
  prueba está mal escrita y no protege nada.
- **Puerta de despliegue de cada fase**: `tests/test_acortador.py` y `tests/test_migracion.py` en
  verde, y `/health` respondiendo 200 tras desplegar. La constitución no permite saltársela.
