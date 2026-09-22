# Tasks: Entrega a medida

**Fecha**: 2026-09-22 | **Plan**: [plan.md](./plan.md) | **Spec**: [spec.md](./spec.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]** = puede hacerse en paralelo con otras marcadas [P] (ficheros distintos, sin dependencia).
- **[US1..US5]** = a qué historia de usuario pertenece.
- Sin marca = tarea de cimientos o transversal.

## Path Conventions

Rutas relativas a la raíz del repositorio `centaurads-links`. El motor vive en
`prototipos/mail/render.js` (fuente) y se publica en `app/static/email/`. El servidor de entregas,
en `app/mails/entregas/`. Las pruebas, en `tests/`.

---

## Phase 0: Especificar *(cerrada)*

- [x] **E001** Enmendar la constitución a **1.1.0**: el principio II deja de exigir subir `CONTENT_VERSION` y pasa a exigir migrar el estado guardado en `normaliza()`. Subirlo borra el trabajo del usuario; ya ocurrió.
- [x] **E002** Escribir [spec.md](./spec.md) con las cinco historias, las decisiones cerradas y el envío manual como alcance explícito.
- [x] **E003** Escribir [plan.md](./plan.md) con las ocho decisiones y la puerta de constitución.
- [x] **E004** Escribir [data-model.md](./data-model.md): dos tablas nuevas, cero columnas tocadas.
- [x] **E005** Poner al día `specs/001-modulo-mails/tasks.md`, que marcaba 0/57 con la fase 2 ya construida.

---

## Phase 1: Bloques y recetas *(sin cambio visible)*

**Nada de las fases siguientes puede empezar hasta que A–G salgan byte a byte idénticas.**

- [x] **T101** Congelar la referencia. Resultaron **14**, no ocho: la referencia de la 001 era de antes de que existieran los formatos E, F y G, y de antes de retirar Paradas y añadir Las Mercedes. Congeladas desde `8745a4b`, con su README.
- [x] **T102** Escribir `tests/test_plantillas_identicas.py`: genera las plantillas con el motor y compara **byte a byte** con `tests/golden/`. Ahora mismo debe pasar; es la red, no el objetivo. Si falla antes de tocar nada, la referencia está mal congelada.
- [~] **T103** ~~Declarar `pytest` en las dependencias de desarrollo.~~ **La tarea no existía**: `requirements-dev.txt` ya lo declara (pytest 9.1.1, pytest-asyncio 1.3.0, httpx) desde `07dd55b`. La escribí tras mirar solo `requirements.txt`, que es el de producción y no debe llevarlo.
- [x] **T104** Extraer los bloques compartidos. **Ya estaban extraídos**: `doc`, `marca`, `firma`, `paleta`, `cabeceraAsesor`, `epigrafe`, `botonAsesor`, `fotoServicio`, `complementos`, `row`, `button`. Lo único que faltaba para reutilizarlos era que `complementos` admitiera un rótulo propio y una variante de una sola columna. Dos ampliaciones puras; A–G sin moverse.
- [ ] **T105** Convertir cada plantilla A–G en una **receta** declarativa: una lista de bloques con sus opciones. **Aplazada, y conviene decir por qué**: con T104 y T106 hechas, la Entrega ya se arma con los bloques compartidos, que era el objetivo. Reescribir las siete funciones que hoy funcionan para que declaren lo mismo de otra forma es mover 600 líneas sin que cambie nada para nadie. Se hará cuando una segunda receta lo necesite de verdad, no antes.
- [x] **T106** [P] La receta **Entrega**, registrada como formato `H`, hermana de A–G: cabecera con la marca, título de la propuesta, texto, portada enlazada, botón, los servicios que la acompañan (en una columna, que es la que sobrevive al móvil), firma y pie. Armada con los bloques de T104, no escrita a mano.
- [x] **T107** [P] `bloques.entrega` en `defaultState`: título, texto largo, texto corto, rótulo, llamada a la acción y el hueco del enlace y la portada. Con él, `renderText` sabe describir una Entrega y `renderWhatsApp` produce el mensaje corto con **un solo** enlace, al principio (FR-116, FR-118).
- [x] **T108** Estado guardado. **No hizo falta código**: `normaliza()` ya recorre `base.bloques` rellenando bloque a bloque y campo a campo lo que falte. Comprobado con un estado sin `bloques.entrega` y con textos editados a mano: aparece el bloque nuevo, sobreviven los textos, y `CONTENT_VERSION` sigue en 5 (FR-128).
- [x] **T109** Guardia byte a byte en `build.js`, con `GOLDEN_UPDATE=1` como única forma de actualizar la referencia. **Probada en los dos sentidos**: con el árbol limpio dice «16 plantillas idénticas»; al alterar un byte de una referencia sale con código 1 y nombra el fichero. De paso, su mensaje de error ya no dice «sube CONTENT_VERSION» (enmienda 1.1.0).

**Punto de control**: alcanzado. El motor tiene una octava receta armada con sus propias piezas, y las catorce plantillas que el equipo ya usa no han cambiado ni un byte — verificado por la guardia, no supuesto.

**Lo que se vio al mirarlo renderizado** (principio III), y que no es culpa del refactor:

- Las imágenes de **Las Mercedes** dan 404 en producción (`svc_mercedes.jpg`, `cover_mercedes.jpg`). Están en el repositorio y en `app/static/email/`, pero el despliegue del commit `8745a4b` sigue sin aplicarse en EasyPanel. Afecta a **todas** las plantillas, no solo a la Entrega.
- **Las dos pantallas comparten el enlace de Canva** (`p69pybf8jctaq8d`). Puede ser correcto —el deck se titula «Circuito pantallas LED Chacao y Las Mercedes»— pero conviene confirmarlo antes de entregárselo a un cliente.

---

## Phase 2: La entrega en el servidor

- [ ] **T110** Añadir `pypdfium2` y `Pillow` a `requirements.txt`, con el comentario de por qué pypdfium2 y no PyMuPDF (licencia AGPL, repositorio público).
- [ ] **T111** Añadir a `app/models.py` las clases `Entrega` y `EntregaPagina` de [data-model.md](./data-model.md), con `contact_id` **no nulo**, el índice único `(entrega_id, orden)` y el borrado en cascada. No tocar ninguna clase existente.
- [ ] **T112** Escribir `tests/test_entregas_api.py` **antes** que las rutas: crear una entrega sin contacto debe ser rechazado; con contacto, debe devolver su enlace. Debe fallar ahora.
- [ ] **T113** [US1] `app/mails/entregas/almacen.py`: escribir y leer ficheros bajo `/app/data/entregas/<id>/`, con rutas relativas en la base de datos. Comprobar que `.gitignore` cubre `data/`.
- [ ] **T114** [US2] `app/mails/entregas/paginas.py`: rasterizar el PDF con pypdfium2, una imagen por página, y extraer su texto. Medir el tiempo con un PDF real de 6 páginas.
- [ ] **T115** [US2] Detección de precio en el texto de cada página, y el `rotulo` a partir de su primer titular. La advertencia de que **un precio en imagen no se detecta** va escrita en la interfaz, no solo en el plan (puerta IV de la constitución).
- [ ] **T116** [US2] Validación de la subida: solo PDF o imagen, tope de 25 MB y de 20 páginas, con un mensaje que explique el límite (FR-114). Prueba con un fichero que no es ninguna de las dos cosas.
- [ ] **T117** [US2] `app/mails/entregas/carrusel.py`: de 2 a 4 páginas a GIF con Pillow, barrido, **fotograma 0 = primera página elegida** (FR-111).
- [ ] **T118** [US2] **Medición, no fe**: pesar el GIF resultante con un PDF real y mirarlo a 600 px. Si pasa de ~1 MB o se ve bandeado, añadir `ffmpeg` al `Dockerfile` y reutilizar la tubería de `carrusel_gif.py`. Anotar el resultado medido en el plan.
- [ ] **T119** [US1] `app/mails/entregas/rutas.py`: `POST/GET/PUT /api/entregas`, con creación del `Link` asociado y del contacto si no existe. Sin contacto no se crea la entrega.
- [ ] **T120** [US1] `GET /media/entregas/<id>/<fichero>`: sirve desde el **volumen**, no desde `app/static/`. Cabeceras de caché largas; los ficheros no cambian una vez escritos.
- [ ] **T121** [US3] `GET /p/{slug}`: página de vista previa con `og:title`, `og:description` y `og:image` apuntando a `og.jpg`, botón hacia la presentación, y registro del clic igual que el acortador (FR-117).
- [ ] **T122** [US3] Generar `og.jpg` a 1200×630 a partir de la página 0 al guardar el carrusel.
- [ ] **T123** Verificar que `tests/test_acortador.py` y `tests/test_migracion.py` siguen en verde: dos tablas nuevas no pueden alterar el comportamiento del acortador (principio I).

**Punto de control**: una entrega existe, tiene imágenes, tiene enlace propio y su tarjeta se ve al pegarla.

---

## Phase 3: El modo Entrega en el panel 🎯 *aquí ya se entregan propuestas de verdad*

- [ ] **T124** [US5] Ampliar `app/auth/google.py`: entra quien tenga fila **activa** en `panel_users`, sea del dominio o un Gmail personal (FR-119). El rechazo no revela si la cuenta está en la lista.
- [ ] **T125** [US5] `tests/test_acceso_lista.py`: un Gmail de la lista entra; uno que no está, no; uno desactivado, tampoco, aunque su sesión anterior siguiera viva.
- [ ] **T126** [US5] Administración de la lista de autorizados en el panel, con el aviso escrito de que **retirar a alguien es un paso obligatorio de su baja**, porque su Gmail sigue existiendo fuera de la empresa (FR-120).
- [ ] **T127** [US1] Modo Entrega en `compositor.html`, paso 1: enlace de Canva y título, con comprobación de que el enlace resuelve antes de seguir (FR-101, escenario 4 de US1).
- [ ] **T128** [US2] Paso 2: soltar el PDF o las imágenes, miniaturas con su rótulo, elegir de 2 a 4 y ordenarlas. Aviso visible en las que llevan precio.
- [ ] **T129** [US2] Botón **"Pedírselo a Claude"**: escribe la instrucción con el enlace y las páginas, la copia y abre Claude en otra pestaña. La herramienta no guarda credenciales de Claude ni depende de él (FR-113).
- [ ] **T130** [US1] Paso 3: contacto **obligatorio**, con creación rápida sin salir del flujo (FR-102). Avisar si ese contacto ya tiene una entrega.
- [ ] **T131** [US1] Paso 4: texto de entrega editable, servicios que la acompañan, cuenta remitente limitada a las permitidas y cargo de la firma (FR-103, FR-104, FR-105).
- [ ] **T132** [US1] Paso 5: vista previa a 600 px y a ~375 px y **"Copiar para Gmail"**. El envío no existe en esta versión: lo dice la interfaz, no solo la especificación (FR-115).
- [ ] **T133** [US3] **"Copiar para WhatsApp"**: texto corto con **un solo** enlace, al principio del mensaje, y la portada aparte para adjuntarla (FR-116).
- [ ] **T134** [US1] Listado de entregas: recuperar un borrador, volver a copiar una entregada sin rehacerla (FR-107).
- [ ] **T135** [US1] **Verificación visual obligatoria**: la entrega renderizada a 600 px, a 375 px y **con las imágenes bloqueadas**, en Gmail y en Outlook. No se cierra la fase sin esto (principio III).
- [ ] **T136** [US3] Prueba real de pegado: pegar el enlace en una conversación de WhatsApp y comprobar que sale la tarjeta con imagen a la primera (SC-104).

**Punto de control**: el equipo entrega propuestas desde cualquier computadora, sin instalar nada.

---

## Phase 4: Saber quién la abrió

- [ ] **T137** [US4] `tests/test_avisos.py`: tres aperturas del mismo contacto sobre la misma entrega en 48 h generan **un** aviso; la cuarta no genera otro. Debe fallar ahora.
- [ ] **T138** [US4] Enlace por destinatario en la entrega: `?c=<token>` del contacto, y atribución de la apertura en `clicks.contact_token`.
- [ ] **T139** [US4] Aplicar la regla de las tres aperturas a las entregas, apoyada en el índice único de `alerts` para que el duplicado lo impida la base de datos.
- [ ] **T140** [US4] Evaluar la regla **sin bloquear** la redirección ni la página de vista previa: el cliente no espera por nuestra contabilidad.
- [ ] **T141** [US4] Ver los avisos en el panel y marcarlos como atendidos. **Desde el primer día se ven aquí**, con o sin n8n.
- [ ] **T142** [US4] Prueba explícita de que **no sale ningún correo al cliente** a raíz de sus aperturas (FR-016 de la 001, SC-106).

**Punto de control**: el equipo se entera de que un cliente volvió a su propuesta.

---

## Phase 5: n8n reparte los avisos *(depende de repararlo)*

> **No empezar** hasta que n8n responda y sus credenciales expuestas estén cambiadas. Es trabajo de infraestructura, no de código.

- [ ] **T143** Reparar n8n (hoy responde 502) y **cambiar sus credenciales expuestas**. Sin esto, lo demás de esta fase no se toca.
- [ ] **T144** `app/mails/entregas/avisos.py`: registrar el aviso en `alerts` y **después** llamar al webhook. La URL del webhook por variable de entorno, validada al arrancar si está definida.
- [ ] **T145** Reintento y tolerancia: si el webhook falla, el aviso queda marcado como no repartido y sigue visible en el panel. Prueba con el webhook apagado (FR-124, FR-125).
- [ ] **T146** Flujo en n8n que recibe el aviso y lo reparte por el canal que el equipo elija.

**Punto de control**: el aviso llega fuera del panel, y si n8n cae no se pierde nada.

---

## Fuera de alcance de esta especificación

- **El envío automático del correo.** Decisión del propietario: *"deja que el proceso se siga haciendo manual el copiar y pegar en el mail y por ultimo coordinamos el envio automatico por N8N"*. Se coordinará después, y exigirá el puerto del motor a Jinja2 que la 001 dejó pendiente (T022–T037 de la 001).
- **Copias de seguridad.** Decisión tomada con el riesgo a la vista; no se replantea aquí.
- **Respuesta en el hilo del buzón** (historia 4 de la 001). Sigue siendo etapa 2 de aquella.

---

## Dependencias

- **Phase 1 bloquea todo.** Sin bloques, la entrega sería una plantilla escrita a mano.
- **T101 antes que T102**, y **T102 en verde antes de cada extracción** de T104 y T105.
- **T110–T111 antes que T113–T122**: sin modelos ni dependencias no hay servidor de entregas.
- **Phase 2 antes que Phase 3**: el panel consume la API, no al revés.
- **T143 bloquea toda la Phase 5**, y nada más depende de ella.
- **US4 depende de US1**: sin entrega con contacto no hay a quién atribuir la apertura.

## Notas

- Las pruebas que dicen "debe fallar ahora" son deliberadas: si pasan antes de implementar, la
  prueba está mal escrita y no protege nada. **T102 es la excepción**: debe pasar desde el
  principio, porque su trabajo es detectar que el refactor rompió algo.
- **Puerta de despliegue de cada fase**: `tests/test_acortador.py` y `tests/test_migracion.py` en
  verde, y `/health` respondiendo 200 tras desplegar. La constitución no permite saltársela.
- Cada `push` al repositorio público es una decisión del propietario, no un efecto secundario.
