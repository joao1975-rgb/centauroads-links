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

- ~~Las imágenes de **Las Mercedes** dan 404 en producción.~~ **Resuelto el 2026-09-23**: no era del código sino del despliegue, y hubo que desplegar el servicio correcto (`centauro-links`, no `mundial`). Verificado: las cuatro imágenes dan 200 y el `render.js` publicado es byte a byte el del repositorio.
- ~~Las dos pantallas comparten el enlace de Canva (`p69pybf8jctaq8d`).~~ **Confirmado correcto por el propietario el 2026-09-23**: es un solo deck que cubre las dos pantallas, «Circuito pantallas LED Chacao y Las Mercedes».

---

## Phase 2: La entrega en el servidor

- [x] **T110** `pypdfium2==5.9.0` y `Pillow==12.2.0` en `requirements.txt`, con el porqué de pypdfium2 frente a PyMuPDF (AGPL, repositorio público). Se fijan las versiones **probadas aquí**, no las que supuse al escribir el plan.
- [x] **T111** `Entrega` y `EntregaPagina` en `app/models.py`, con `contact_id` no nulo, `UNIQUE(entrega_id, orden)` y borrado en cascada. Ninguna clase existente tocada. De paso: la columna destino de `links` se llama `target_url`, no `destination` — corregido en el modelo de datos, que decía lo segundo.
- [x] **T112** `tests/test_entregas_api.py`: **24 pruebas, en verde**, con el contacto obligatorio y los intentos de salirse de `/media` como piezas centrales. Añadido `tests/test_carrusel.py` (10 más) porque el orden de los fotogramas no estaba cubierto.
- [x] **T113** [US1] `almacen.py`. Doble comprobación en `resuelve()`: por forma (lista de caracteres permitidos) y por destino (`realpath` dentro de la carpeta de la entrega). `.gitignore` ya cubría `data/`.
- [x] **T114** [US2] `paginas.py`. **Medido**: 6 páginas en 365 ms, a 1200 px de ancho, con su texto leído.
- [x] **T115** [US2] Detección de precio y rótulo. **Probada con 9 casos, 9 aciertos**: detecta «USD 1500», «desde 1.500 $/mes», «Precio: 300»; y NO se dispara con «1024 × 2048 px», «+95.000 vehículos/día» ni «7,68 × 4,80 m». La advertencia de que un precio en imagen no se detecta viaja en la respuesta de la subida, para que la interfaz la enseñe.
- [x] **T116** [US2] Validación **por los primeros bytes, no por la extensión**: la extensión la escribe quien sube. Topes de 25 MB y 20 páginas, con mensajes que dicen qué hacer. Comprobado: texto plano y fichero vacío se rechazan.
- [x] **T117** [US2] `carrusel.py`. **Fotograma 0 comprobado**: coincide con la primera página elegida, diferencia 0.
- [x] **T118** [US2] **Medido con páginas fotográficas reales**: 2 → 791 KB, 3 → 971 KB, 4 → 842 KB, todas a 128 colores, de 4,5 a 8,3 s. **Pillow basta; FFmpeg no entra en la imagen.** La primera medición salió a 12,1 s y 64 colores: se reordenaron los intentos (recortar transición antes que color) y se añadió una estimación para no codificar seis veces. Margen estrecho: 3 páginas se quedan a 29 KB del techo.
- [x] **T119** [US1] `rutas.py`: alta, listado, lectura, actualización, subida, selección y «marcar entregada». Sin contacto no se crea, comprobado.
- [x] **T120** [US1] `GET /media/entregas/<id>/<fichero>` desde el volumen, con caché inmutable, y sus dos capas de guardia probadas por separado.
- [x] **T121** [US3] `GET /p/{slug}` con sus etiquetas Open Graph, **un solo enlace saliente** y registro del clic que no deja sin página al cliente si falla. Las tres cosas, comprobadas.
- [x] **T122** [US3] `og.jpg` a **1200×630, 11 KB** comprobados, recortando desde el centro en vez de deformar.
- [x] **T123** La puerta del principio I, **en verde**: `test_acortador.py` 21/21 y `test_migracion.py` 8/8, sobre un esquema con las dos tablas nuevas. Batería completa: **93 pruebas, 0 fallos**. Y el motor sigue dando «16 plantillas idénticas a la referencia».

**Punto de control**: alcanzado. Una entrega existe, tiene imágenes, tiene enlace propio y su
tarjeta se ve al pegarla. **93 pruebas en verde**, incluida la puerta del acortador.

**Lo que hizo falta para creérselo.** Las 82 primeras pruebas pasaron a la primera, lo cual es
motivo de sospecha, no de alivio. Se rompió el código a propósito en cinco sitios para ver si
alguna prueba se enteraba, y **dos no se enteraban**:

- El orden de los fotogramas del carrusel: la prueba miraba el orden de las filas en la base de
  datos, que es otra cosa. De ahí nació `tests/test_carrusel.py`.
- La segunda capa de la guardia de `/media`: el filtro de nombres ya rechazaba todo lo que llegaba
  por HTTP, así que la guardia de destino se podía borrar sin que nada fallara. Y la primera
  corrección tampoco servía —apuntaba a ficheros inexistentes, así que fallaba en el `isfile`—:
  hubo que dejar un fichero real justo fuera de la carpeta.

Esas pruebas encontraron además **un defecto de verdad**: `dentro_de_presupuesto` comparaba contra
la constante del módulo en vez de contra el presupuesto que se le había pasado, de modo que decía
«entra» cuando se le pedía un techo más bajo. Corregido.

Las cinco mutaciones se detectan ahora.

---

## Phase 3: El modo Entrega en el panel 🎯 *aquí ya se entregan propuestas de verdad*

- [x] **T124** [US5] `google.py` pasa a decir solo **quién eres**; la puerta es la lista. Y faltaba lo más básico, que no estaba en esta lista de tareas: **no había ninguna ruta que abriera sesión**, así que la API de entregas era inalcanzable. Añadidas pantalla de entrada, Google, contraseña, salida y `PANEL_BOOTSTRAP` para el arranque en frío.
- [x] **T125** [US5] `tests/test_acceso_lista.py`, 17 pruebas. Una mutación coló al principio: la prueba del rechazo comparaba los dos mensajes **entre sí**, así que uno que revelara el estado pasaba si lo revelaba en ambos casos. Ahora exige además que el texto no hable de la cuenta.
- [x] **T126** [US5] API de la lista: alta, baja y listado, solo para rol admin. La baja es `activo = False`, nunca borrar la fila. Nadie puede retirarse el acceso a sí mismo. Queda por poner **la pantalla** de administración; hoy se administra por API.
- [x] **T127** [US1] Paso 01, con «Comprobar el enlace» contra `POST /api/entregas/comprobar-enlace`. El servidor solo llama a canva.com y canva.link: comprobar una dirección que escribe otra persona significa que el servidor hace la petición, y sin esa lista cerrada sería una puerta a la red interna.
- [x] **T128** [US2] Paso 03 (ver la nota de orden abajo): soltar el PDF **o varias imágenes**, miniaturas con rótulo y distintivo de precio, elegir de 2 a 4 en orden. Al usarlo apareció un defecto: cada subida reemplaza a la anterior, así que aceptando un fichero por subida la vía de imágenes sueltas **nunca** podía llegar al mínimo de dos páginas.
- [x] **T129** [US2] «¿Sin el PDF? Pedírselo a Claude»: copia la instrucción con el enlace y abre Claude. El servidor no guarda credenciales de Claude ni habla con él.
- [x] **T130** [US1] Contacto obligatorio, con creación rápida en el mismo paso y `GET /api/contactos` para elegir uno existente. **Queda pendiente** avisar de que ese contacto ya tiene otra entrega.
- [x] **T131** [US1] Paso 04: texto largo, texto corto de WhatsApp y texto del botón, editables; los servicios que la acompañan, con sus interruptores; y la firma con su cargo y su correo.
- [x] **T132** [US1] Paso 05 con «Copiar para Gmail» y el aviso escrito de que **el envío es manual**: la herramienta no manda correos, y lo dice la interfaz.
- [x] **T133** [US3] «Copiar para WhatsApp», en la barra y en el paso 05, visible solo en modo Entrega.
- [ ] **T134** [US1] Listado de entregas para recuperar un borrador (FR-107). **Sin hacer.** La API existe (`GET /api/entregas`); falta la pantalla. Hoy el compositor recuerda la última entrega en el navegador, que sirve para seguir donde lo dejaste pero no para retomar la de otra persona.
- [x] **T135** [US1] Verificación visual hecha sobre la aplicación levantada de verdad. Y de paso apareció algo peor que un fallo de la entrega: el conmutador **«Sin imágenes» del compositor no servía**. Las ocultaba con `display:none`, que esconde también el texto alternativo, de modo que daba por buena una plantilla que con las imágenes bloqueadas se quedaba muda. Ahora quita el `src`, que es lo que hace Outlook. Comprobado: la entrega sigue leyéndose y sigue siendo de Centauro ADS.
- [ ] **T136** [US3] Prueba real de pegado en WhatsApp. **Te toca a ti**: hay que pegarlo en una conversación real. Verificado hasta donde se puede sin eso: la página del cliente sirve `og:title`, `og:description` y `og:image` a 1200×630, y lleva **un solo** enlace saliente.

**Cambio de orden, y por qué.** El contacto pasa del paso 3 al 2. Es obligatorio para crear la
entrega en el servidor (FR-102), y sin entrega creada no hay dónde subir el PDF; pedirlo después
obligaría a interrumpir a mitad del paso de las páginas. FR-102 exige que sea obligatorio y que se
pueda crear sin salir del flujo, no que vaya en un sitio concreto.

**Punto de control**: alcanzado para el camino principal. Probado de extremo a extremo sobre la
aplicación levantada: entrar, crear la entrega, subir tres imágenes, elegirlas, armar el carrusel
y ver la página del cliente con su tarjeta. Quedan **T134** (listado de entregas) y **T136** (el
pegado real en WhatsApp, que solo puedes hacer tú).

**Tres defectos que solo aparecieron al usarlo**, y que ninguna prueba había cogido:

- La aplicación **no arrancaba** con `PANEL_BOOTSTRAP` puesto: usaba un logger que en ese punto
  del fichero aún no existía. Habría reventado en producción, no aquí. Ahora hay una prueba que
  importa la aplicación entera en otro proceso con esa variable.
- El panel **no se reconstruía** al cambiar de plantilla, así que el modo Entrega no aparecía.
  Hasta ahora todas las plantillas compartían panel y nadie lo había necesitado.
- Sin sesión, el panel **se quedaba callado**: lista de contactos vacía y un error críptico al
  guardar. Ahora lo dice y ofrece el enlace para entrar.

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
