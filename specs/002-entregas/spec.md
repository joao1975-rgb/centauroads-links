# Feature Specification: Entrega a medida

**Feature Branch**: `002-entregas`

**Created**: 2026-09-22

**Status**: Draft

**Input**: User description: "cuando ya se le armó una presentación propia al cliente, hay que
entregársela: asignar el enlace de Canva nuevo, un texto de entrega editable, sacar imágenes de
esa presentación, elegir qué servicios la acompañan y llevarse el correo y el WhatsApp"

## Contexto

Las plantillas A–G responden a una solicitud de información: enseñan el catálogo. Pero el trabajo
de Centauro ADS no termina ahí. Cuando el cliente muestra interés, el equipo le arma **su**
presentación en Canva —con su marca puesta en las pantallas, su recorrido, su propuesta— y
entonces hay que **entregársela**.

Hoy esa entrega se escribe desde cero cada vez: se pega el enlace de Canva, se redacta el texto a
mano, se toma alguna captura de la presentación si a alguien se le ocurre, y se manda. El
resultado es desigual, no queda registrado, y cuando el cliente abre la presentación tres veces
nadie se entera, que es exactamente el momento en el que habría que llamarlo.

Esta capacidad añade un **modo Entrega** al panel: los mismos bloques y la misma marca de las
plantillas A–G, pero girados hacia una presentación concreta de un cliente concreto.

**Alcance v1 (decidido, no se reabre)**: armar la entrega, llevársela copiada para Gmail y para
WhatsApp, y saber quién la abrió. El envío sigue siendo **manual**: la persona pega y pulsa
Enviar. Queda fuera de v1 el envío automático; se coordinará después con n8n, que en v1 solo
reparte los avisos internos.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entregar una presentación propia en dos minutos (Priority: P1)

Elizabeth terminó en Canva la presentación de un cliente. Entra al panel, elige el modo Entrega,
pega el enlace de Canva, escribe a quién va, sube el PDF que Canva acaba de descargarle, elige dos
páginas para el carrusel, deja activos los dos servicios que acompañan la propuesta, retoca el
texto de entrega si quiere, y se lleva el correo listo para pegarlo en Gmail.

**Why this priority**: es el trabajo que hoy se hace a mano y sin registro. Entrega valor por sí
solo aunque no se construya nada más: el correo sale igual de bien siempre y queda constancia de a
quién se le mandó.

**Independent Test**: se arma una entrega para un contacto de prueba con una presentación real, se
pega en Gmail y se comprueba que llega con el carrusel visible, el enlace correcto y la firma de
la cuenta elegida.

**Acceptance Scenarios**:

1. **Given** una persona autenticada en el panel, **When** completa los cinco pasos del modo
   Entrega, **Then** obtiene un correo listo para pegar cuya apariencia coincide con la vista
   previa que acaba de ver.
2. **Given** una entrega armada, **When** la persona la pega en Gmail y la envía, **Then** el
   destinatario la recibe con las imágenes visibles y el enlace de la presentación funcionando.
3. **Given** una entrega sin contacto asignado, **When** la persona intenta generarla, **Then** el
   sistema se lo impide y ofrece crear el contacto en ese mismo paso.
4. **Given** un enlace de Canva que no resuelve o que no es público, **When** se guarda la entrega,
   **Then** el sistema avisa antes de generar el correo, no después de enviarlo.

---

### User Story 2 - Sacar las imágenes de la presentación sin diseñar nada (Priority: P1)

La persona que entrega no es diseñadora. Necesita dos imágenes de la presentación dentro del
correo, y no quiere recortar capturas. Descarga el PDF desde Canva, lo suelta en el panel, ve las
páginas como miniaturas, marca dos y el sistema arma el carrusel.

**Why this priority**: sin imágenes, la entrega es un enlace pelado y el cliente no abre nada.
Va junto a la historia 1 porque el paso 2 del flujo no funciona sin esto.

**Independent Test**: se sube un PDF de seis páginas exportado de Canva, se eligen las páginas 1 y
3, y el carrusel resultante debe mostrar esas dos páginas en ese orden, con la 1 como fotograma
fijo.

**Acceptance Scenarios**:

1. **Given** un PDF exportado de Canva, **When** se sube al panel, **Then** el sistema muestra una
   miniatura por página y permite elegir de 2 a 4.
2. **Given** las páginas elegidas, **When** se genera el carrusel, **Then** la primera página
   elegida es el fotograma que se ve con las animaciones desactivadas.
3. **Given** una página que muestra un precio escrito como texto, **When** se elige esa página,
   **Then** el sistema avisa de que lleva un precio antes de incluirla.
4. **Given** una persona que no tiene el PDF a mano, **When** pulsa la opción de pedírselo a
   Claude, **Then** el sistema le entrega la instrucción ya escrita con el enlace y las páginas, y
   le abre Claude; las imágenes resultantes se sueltan en el mismo paso.
5. **Given** un fichero que no es un PDF ni una imagen, **When** se suelta en el panel, **Then** el
   sistema lo rechaza explicando qué acepta.

---

### User Story 3 - Llevarse el mismo mensaje para WhatsApp (Priority: P2)

Buena parte de las entregas van por WhatsApp, no por correo. La persona quiere el mismo mensaje
adaptado: texto corto, el enlace primero para que se vea la vista previa, y la imagen de portada
aparte para adjuntarla.

**Why this priority**: es el canal real de la mitad de las conversaciones, pero la entrega ya
funciona sin él. Depende de que la entrega exista (historia 1).

**Independent Test**: se pulsa "Copiar para WhatsApp", se pega en una conversación y debe
aparecer la vista previa de la presentación con su imagen y su título, sin enlaces de más.

**Acceptance Scenarios**:

1. **Given** una entrega armada, **When** se copia para WhatsApp, **Then** el texto copiado lleva
   **un solo** enlace y va al principio del mensaje.
2. **Given** ese enlace pegado en WhatsApp, **When** la conversación genera la vista previa,
   **Then** se muestra la imagen de portada y el título de la entrega, no una tarjeta vacía.
3. **Given** la misma entrega, **When** se compara el texto de WhatsApp con el del correo,
   **Then** dicen lo mismo con distinta extensión: no son dos mensajes distintos que mantener.

---

### User Story 4 - Enterarse de que el cliente volvió a la propuesta (Priority: P3)

El cliente abre su presentación tres veces en dos días. El sistema avisa al equipo, igual que ya
hace con las presentaciones del catálogo.

**Why this priority**: es lo que convierte el registro en una llamada a tiempo, pero depende por
completo de que la entrega lleve contacto y enlace propio. La regla y su umbral ya están
especificados en la 001 (FR-015, FR-016); aquí solo se extienden a las entregas.

**Independent Test**: se simulan tres aperturas del enlace de una entrega por el mismo contacto
dentro de 48 horas y debe generarse exactamente un aviso, visible en el panel aunque n8n esté
caído.

**Acceptance Scenarios**:

1. **Given** un contacto que abrió su entrega 3 veces en 48 horas, **When** se registra la tercera
   apertura, **Then** el sistema genera un aviso interno.
2. **Given** n8n caído o sin responder, **When** se genera un aviso, **Then** el aviso queda
   registrado y visible en el panel; no se pierde ni bloquea nada.
3. **Given** cualquier aviso generado, **When** se revisa lo que salió, **Then** se confirma que no
   se envió ningún correo al cliente.

---

### User Story 5 - Entrar desde otra computadora sin instalar nada (Priority: P2)

Una persona del equipo abre el panel desde su casa, en su propio computador, con su cuenta de
Gmail —la misma con la que entra a Canva—. No instala nada. Si mañana deja el equipo, se la saca
de la lista de autorizados y deja de entrar.

**Why this priority**: es lo que separa esta herramienta del prototipo que vivía en un solo
portátil. Sin esto la capacidad existe pero solo la usa una persona.

**Independent Test**: se entra desde una computadora que nunca ha abierto el panel, con una cuenta
de la lista, y se arma una entrega completa. Después se retira esa cuenta de la lista y se
comprueba que ya no entra.

**Acceptance Scenarios**:

1. **Given** una cuenta de Gmail en la lista de autorizados, **When** entra por Google desde
   cualquier navegador, **Then** accede al panel sin instalar nada.
2. **Given** una cuenta de Gmail que no está en la lista, **When** intenta entrar, **Then** el
   sistema la rechaza y no revela qué cuentas sí están.
3. **Given** una persona retirada de la lista, **When** vuelve a intentar entrar, **Then** no
   accede, aunque su cuenta de Gmail siga existiendo y siga teniendo acceso a Canva.

---

### Edge Cases

- **El enlace de Canva deja de ser público** (alguien cambia el permiso de la presentación): las
  entregas ya enviadas apuntan a un enlace que el cliente no puede abrir. El sistema debe poder
  comprobar el enlace y avisar, sin poder arreglarlo por su cuenta.
- **El PDF de Canva lleva marca de agua** (según el plan de la cuenta que lo descargue): el
  carrusel saldría con la marca. Hay que verlo antes de entregarlo, no después.
- **Un precio convertido en imagen**: el aviso de precios lee texto. Un precio que en la
  presentación es parte de una imagen no se detecta. Es una limitación conocida; la revisión
  visual de las miniaturas es la red que la cubre.
- **El PDF pesa más que el límite de subida** o tiene cincuenta páginas: el sistema debe rechazarlo
  con un mensaje claro en vez de agotarse intentándolo.
- **El cliente reenvía la entrega a un colega**: las aperturas se atribuirán al contacto original.
  Limitación conocida, igual que en la 001; no se presenta como certeza.
- **Dos personas entregan al mismo cliente**: el registro debe dejar ver que ya hay una entrega
  para ese contacto antes de crear la segunda.
- **El disco del servidor falla**: no hay copia de seguridad (decisión tomada, ver Assumptions). Se
  pierden entregas, imágenes, historial de clics y **el destino de los enlaces cortos ya impresos
  en vallas**. Riesgo asumido y escrito.
- **n8n sigue caído** cuando llegue el momento: los avisos se ven en el panel. La capacidad no
  depende de n8n para funcionar.

## Requirements *(mandatory)*

### Functional Requirements

**La entrega**

- **FR-101**: El sistema MUST permitir crear una entrega asociada a un enlace de presentación
  propio del cliente, distinto de los enlaces del catálogo.
- **FR-102**: Cada entrega MUST tener un contacto asignado; el sistema MUST impedir generar el
  correo sin él, y MUST permitir crear el contacto sin salir del flujo.
- **FR-103**: El sistema MUST ofrecer un texto de entrega por defecto, editable antes de generar el
  correo, y ese texto por defecto MUST vivir en el mismo motor de contenido que el resto.
- **FR-104**: El sistema MUST permitir elegir qué servicios del catálogo acompañan la entrega,
  incluido ninguno.
- **FR-105**: El sistema MUST permitir elegir la cuenta remitente y el cargo de la firma, con las
  mismas reglas de permiso que la 001 (FR-004, FR-004a).
- **FR-106**: El sistema MUST generar un enlace propio de esa entrega, atribuible a su contacto.
- **FR-107**: El sistema MUST conservar la entrega para volver a copiarla más tarde sin rehacerla.

**Las imágenes de la presentación**

- **FR-108**: El sistema MUST aceptar un PDF exportado de la presentación y MUST mostrar sus
  páginas como miniaturas elegibles.
- **FR-109**: El sistema MUST aceptar también imágenes sueltas, para quien no tenga el PDF.
- **FR-110**: El sistema MUST permitir elegir entre 2 y 4 páginas para el carrusel, en un orden que
  la persona decide.
- **FR-111**: El carrusel MUST tener como primer fotograma la primera página elegida, de modo que
  el correo se entienda con las animaciones desactivadas.
- **FR-112**: El sistema MUST avisar cuando una página elegida contenga un precio escrito como
  texto, y MUST advertir de que un precio incrustado en una imagen no se detecta.
- **FR-113**: El sistema MUST ofrecer, como alternativa gratuita a la subida, preparar la
  instrucción para pedirle las páginas a Claude con su conector de Canva; esa vía MUST ser
  opcional y el sistema NUNCA MUST guardar credenciales de Claude ni depender de él para funcionar.
- **FR-114**: El sistema MUST rechazar ficheros que no sean PDF o imagen, y MUST limitar tamaño y
  número de páginas con un mensaje que explique el límite.

**Lo que se lleva la persona**

- **FR-115**: El sistema MUST entregar el contenido para pegar en Gmail, y el envío MUST seguir
  siendo manual: el sistema NO envía correo al cliente en esta versión.
- **FR-116**: El sistema MUST entregar una versión para WhatsApp con un solo enlace, colocado al
  principio del mensaje.
- **FR-117**: El enlace de la entrega MUST exponer una vista previa propia (imagen de portada y
  título) para que WhatsApp la muestre al pegarlo.
- **FR-118**: Las dos versiones MUST salir del mismo texto: no se mantienen dos redacciones
  separadas.

**Acceso desde cualquier equipo**

- **FR-119**: El sistema MUST permitir entrar con la cuenta de Google personal de cada persona,
  limitada a una lista de cuentas autorizadas.
- **FR-120**: El sistema MUST permitir retirar una cuenta de esa lista de forma inmediata, y esa
  retirada MUST ser un paso obligatorio del procedimiento de baja de una persona, porque su cuenta
  de Gmail sigue existiendo fuera de la empresa.
- **FR-121**: El uso desde otra computadora NO MUST exigir instalación alguna: navegador y sesión.

**Seguimiento y avisos**

- **FR-122**: El sistema MUST registrar las aperturas de cada entrega y atribuirlas a su contacto.
- **FR-123**: El sistema MUST aplicar a las entregas la misma regla de aviso por interés repetido
  de la 001 (3 aperturas en 48 horas, sin duplicados).
- **FR-124**: El sistema MUST registrar cada aviso en su propio almacenamiento **antes** de
  intentar repartirlo, de modo que un fallo del repartidor no pierda el aviso.
- **FR-125**: El reparto de avisos MUST hacerse mediante un aviso saliente a n8n, sin que el
  sistema guarde credenciales de envío; si n8n no responde, el aviso MUST seguir visible en el
  panel.

**Convivencia**

- **FR-126**: Las plantillas A–G MUST seguir generándose idénticas byte a byte tras la
  refactorización en bloques; cualquier diferencia es un defecto, no una mejora.
- **FR-127**: El acortador de enlaces y el módulo de la 001 MUST seguir funcionando sin cambios de
  comportamiento (constitución, principio I).
- **FR-128**: El estado guardado en el navegador de quien ya usa el compositor MUST sobrevivir al
  despliegue: se migra en `normaliza()`, no se descarta.

### Key Entities *(include if feature involves data)*

- **Entrega**: una presentación propia entregada a un cliente. Su enlace de Canva, su título, su
  texto, qué servicios la acompañan, qué páginas lleva el carrusel, a qué contacto va, quién la
  armó y cuándo. Tiene enlace propio y, por tanto, aperturas propias.
- **Página de la entrega**: cada imagen extraída de la presentación, con su orden dentro del
  carrusel y de dónde salió (PDF subido, imagen suelta, exportación de Claude).
- **Contacto**: el mismo de la 001. Aquí es obligatorio.
- **Cuenta autorizada**: una cuenta de Google personal con permiso de entrada al panel, con el
  momento en que se autorizó y quién la autorizó.
- **Aviso**: la señal interna de interés repetido. Nace en el sistema, se reparte fuera.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-101**: Una persona arma y se lleva una entrega completa en **menos de 4 minutos** desde que
  tiene el enlace de Canva y el PDF, sin ayuda.
- **SC-102**: El **100 %** de las entregas queda registrado con contacto, enlace, contenido y
  responsable. Hoy: 0 %.
- **SC-103**: **Cero** entregas sin contacto asignado.
- **SC-104**: El enlace de una entrega pegado en WhatsApp muestra vista previa con imagen en la
  **primera** vez que se pega.
- **SC-105**: Las plantillas A–G generadas después de la refactorización son **byte a byte
  idénticas** a las generadas antes.
- **SC-106**: **Cero** correos enviados al cliente por el sistema: el envío es manual en toda la v1.
- **SC-107**: Un aviso de interés queda visible en el panel en **menos de 1 minuto** desde la
  tercera apertura, con n8n arriba o caído.
- **SC-108**: Una persona nueva del equipo entrega desde su propia computadora **sin instalar
  nada** y sin que nadie le pase un fichero.
- **SC-109**: **Cero** interrupciones del acortador durante y después del despliegue.

## Assumptions

- **Cuenta de Canva**: Centauro ADS, con `imagencreativa@gmail.com`, en el plan **Canva Equipos (2
  personas)**. No es Enterprise, de modo que la API de Canva para integraciones privadas no está
  disponible. De ahí que la vía sea el PDF exportado, no una extracción automática.
- **Entrada al panel**: cada persona con su cuenta de Gmail personal, la misma que ya usa en
  Canva, contra una lista de autorizados. No se exige Google Workspace para esta capacidad.
- **Volumen**: unas pocas entregas por semana. No se diseña para lotes.
- **Alojamiento**: el droplet de DigitalOcean que ya sirve el acortador, con su volumen persistente.
  No se levanta infraestructura nueva. No hay "nube" adicional que contratar.
- **Envío**: manual en toda la v1, por decisión explícita del propietario. El envío automático se
  coordinará después, con n8n, y no forma parte de esta especificación.
- **n8n**: hoy responde con error 502 y tiene credenciales expuestas. Hay que repararlo y
  cambiarlas antes de darle el reparto de avisos. Mientras tanto, los avisos viven en el panel.
- **Copias de seguridad**: no las hay, por decisión explícita del propietario tomada con el riesgo
  a la vista. Se puede activar cuando se quiera (copias de DigitalOcean o copia nocturna a Spaces);
  hasta entonces, un fallo de disco pierde los datos y rompe los enlaces cortos ya impresos.
- **Marca de agua**: está por comprobar si una cuenta de Canva del plan actual descarga el PDF sin
  marca de agua. Si la llevara, la revisión visual de las miniaturas lo detecta antes de entregar.
- **Idioma**: español de Venezuela, igual que el resto.

## Clarifications

### Resueltas

- **Contacto obligatorio en cada entrega** (decidido 2026-09-22). Sin contacto no hay seguimiento
  ni aviso, que es la razón de ser de la historia 4. Recogido en FR-102; en el modelo de datos,
  `contact_id` no admite vacío.
- **Los avisos los reparte n8n** (decidido 2026-09-22). La aplicación los registra primero y los
  reparte después, de modo que no guarda credenciales de envío y no se pierde nada si n8n cae.
  Recogido en FR-124 y FR-125.
- **Sin copias de seguridad, de momento** (decidido 2026-09-22, riesgo aceptado). No se vuelve a
  plantear; queda escrito en Assumptions y en el plan para que la decisión sea recuperable.
- **El envío sigue siendo manual** (decidido 2026-09-22). Copiar y pegar en el correo. Recogido en
  FR-115 y SC-106.
- **Extracción de imágenes: PDF subido, con Claude como alternativa gratuita** (decidido
  2026-09-22). La API de Canva exige Enterprise; el conector de Claude funciona en el plan gratuito
  pero es de cada persona, no del servidor. Recogido en FR-108 y FR-113.

### Pendientes

Ninguna que condicione el diseño. Queda por comprobar en la práctica, no por decidir: si el plan
actual de Canva descarga PDF sin marca de agua.
