# Feature Specification: Módulo de mails de servicios

**Feature Branch**: `001-modulo-mails`

**Created**: 2026-09-19

**Status**: Draft

**Input**: User description: "arranca con Spec Kit para el módulo app/mails/"

## Contexto

Hoy Centauro ADS responde a cada solicitud de información escribiendo el correo a mano, o pegando
un HTML generado por un prototipo que vive en el portátil de una sola persona. Eso tiene tres
costes: el correo sale distinto cada vez, solo puede mandarlo quien tenga el prototipo, y cuando
el cliente abre la presentación nadie se entera.

Esta capacidad traslada el compositor al panel que el equipo ya usa (`links.centauroads.com`),
para que cualquiera del equipo comercial arme el correo correcto desde cualquier computadora, y
para que cada enlace enviado diga quién lo abrió.

**Alcance v1 (decidido, no se reabre)**: envío bajo demanda (N0), respuesta a solicitud entrante
(N1) y alerta interna de interés (N4). Queda fuera de v1: seguimiento automático por silencio
(N2) y envío por lotes programados (N3).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Armar y llevarse el correo desde el panel (Priority: P1)

Elizabeth atiende a un cliente que le escribió por WhatsApp pidiendo información sobre las
pantallas de Chacao. Entra al panel desde el computador de la oficina, elige el perfil que encaja
con ese cliente, deja activos solo los espacios que le interesan, ve cómo va a quedar el correo, y
se lleva el contenido listo para pegarlo en Gmail y enviarlo.

**Why this priority**: es el trabajo que hoy se hace a mano varias veces por semana, y es lo único
que ya entrega valor por sí solo aunque no se construya nada más. Sustituye al prototipo local por
algo que el equipo alcanza desde cualquier equipo.

**Independent Test**: se prueba entrando al panel desde una computadora que nunca ha tenido el
prototipo, armando un correo para un destinatario de prueba y comprobando que lo que llega a la
bandeja es idéntico a la vista previa.

**Acceptance Scenarios**:

1. **Given** una persona del equipo comercial autenticada en el panel, **When** elige perfil,
   formato y espacios y pide el contenido, **Then** obtiene un correo listo para enviar cuya
   apariencia coincide con la vista previa que acaba de ver.
2. **Given** un correo armado, **When** la persona lo pega en su cliente de correo y lo envía,
   **Then** el destinatario lo recibe con las imágenes visibles y los enlaces funcionando.
3. **Given** una persona sin permiso sobre una cuenta remitente, **When** intenta armar un correo
   en nombre de esa cuenta, **Then** el sistema se lo impide y explica por qué.
4. **Given** un espacio publicitario sin tarifa confirmada, **When** se activa la presentación de
   precios, **Then** ese espacio se muestra como "a cotizar" y nunca con un importe estimado.

---

### User Story 2 - Saber a quién se le mandó qué (Priority: P2)

Cada correo que sale lleva enlaces propios de ese destinatario. Cuando el cliente abre la
presentación, el sistema sabe que fue **ese** cliente, no un anónimo. El equipo puede consultar el
registro: a quién se escribió, qué se le mandó, desde qué cuenta, quién lo armó y si lo abrió.

**Why this priority**: sin esto, el equipo manda correos a ciegas y la alerta de la historia 3 es
imposible. Además evita el problema real de que dos personas respondan al mismo cliente sin
saberlo.

**Independent Test**: se envían dos correos a dos destinatarios distintos, se abre solo uno de los
enlaces, y el registro debe atribuir la apertura al destinatario correcto y solo a él.

**Acceptance Scenarios**:

1. **Given** un correo enviado a un contacto, **When** ese contacto abre un enlace de la
   presentación, **Then** el registro atribuye la apertura a ese contacto con su fecha y hora.
2. **Given** varios correos enviados, **When** alguien del equipo consulta el registro, **Then**
   ve para cada envío el contacto, el perfil y formato usados, la cuenta remitente y la persona
   que lo armó.
3. **Given** un enlace de la presentación abierto por alguien sin identificar, **When** se consulta
   el registro, **Then** la apertura consta como anónima y no se atribuye a ningún contacto.

---

### User Story 3 - Enterarse de que un cliente está interesado (Priority: P3)

Un cliente abre tres veces la misma presentación en dos días. Nadie se lo cuenta a Elizabeth y la
oportunidad se enfría. Con esta historia, el sistema la avisa: "este contacto ha vuelto tres veces
a las pantallas LED en 48 horas".

**Why this priority**: es la pieza que convierte el registro en ventas, pero depende por completo
de la historia 2. Sin enlaces por destinatario no hay a quién avisar.

**Independent Test**: se simulan tres aperturas del mismo enlace por el mismo contacto dentro de la
ventana de tiempo y se comprueba que se genera exactamente un aviso, no tres.

**Acceptance Scenarios**:

1. **Given** un contacto que ha abierto la misma presentación 3 veces en 48 horas, **When** se
   registra la tercera apertura, **Then** el sistema genera un aviso interno dirigido al equipo
   comercial.
2. **Given** un aviso ya generado para ese contacto y esa presentación, **When** el contacto vuelve
   a abrirla dentro de la misma ventana, **Then** no se genera un aviso duplicado.
3. **Given** cualquier aviso generado, **When** se revisa lo que salió, **Then** se confirma que
   **no** se envió ningún correo al cliente: el aviso es solo interno.

---

### User Story 4 - Responder en el hilo, desde el buzón que recibió (Priority: P4)

Llega una solicitud a `mercadeo@centauroads.com`. El sistema la reconoce, detecta qué espacios
menciona el cliente, arma la respuesta con esos espacios y la deja **como borrador dentro del
mismo hilo**, en el buzón que recibió el correo. Una persona lo abre, lo retoca si quiere, y pulsa
Enviar.

**Why this priority**: es la mayor ganancia de tiempo, pero también lo más delicado: exige
autorización sobre los buzones y toca correo real de clientes. Se construye cuando las tres
historias anteriores estén asentadas.

**Independent Test**: se envía un correo de prueba al buzón conectado mencionando "vallas", y debe
aparecer un borrador de respuesta en ese mismo hilo con el bloque de vallas activo y los demás
espacios inactivos.

**Acceptance Scenarios**:

1. **Given** una solicitud entrante en un buzón conectado, **When** el sistema la procesa, **Then**
   deja un borrador de respuesta dentro del mismo hilo del buzón que la recibió, nunca desde otra
   cuenta.
2. **Given** una solicitud que menciona espacios concretos, **When** se arma la respuesta, **Then**
   solo esos espacios van activos; si no menciona ninguno, va el catálogo completo.
3. **Given** el modo "solo borrador" activo, **When** el sistema procesa una solicitud, **Then**
   **nunca** envía el correo por su cuenta: siempre espera a que una persona pulse Enviar.
4. **Given** un borrador ya creado por el sistema para un hilo, **When** llega otro mensaje del
   mismo hilo, **Then** no se crea un segundo borrador que compita con el primero.

---

### Edge Cases

- **El cliente de correo bloquea las imágenes** (comportamiento por defecto en Outlook y en muchas
  configuraciones de Gmail): el correo debe seguir leyéndose y siendo reconocible como de Centauro
  ADS, con el texto alternativo haciendo de marca.
- **Dos personas responden al mismo cliente**: el buzón `mercadeo@` lo ven varias personas. El
  sistema debe dejar rastro visible de que alguien ya tomó ese hilo.
- **El contacto reenvía el correo a un colega**: las aperturas del colega se atribuirán al contacto
  original. Es una limitación conocida, no un defecto; el registro no debe presentarlas como
  certeza de que fue esa persona.
- **La autorización sobre un buzón caduca o se revoca**: el sistema debe avisar al equipo en vez de
  fallar en silencio, y las historias 1 a 3 deben seguir funcionando sin ella.
- **Un espacio publicitario deja de ofrecerse** (por ejemplo, si Rider Clon se retira del
  catálogo): debe poder desactivarse sin tocar los correos ya enviados ni romper sus enlaces.
- **El equipo pierde una computadora**: debe poder cortarse el acceso de esa persona de forma
  central, sin cambiar credenciales para todos los demás.
- **Un dato de contacto cambia** (teléfono, correo, slogan): debe cambiarse en un solo sitio y
  quedar reflejado en todos los correos que se armen a partir de ese momento.

## Requirements *(mandatory)*

### Functional Requirements

**Acceso e identidad**

- **FR-001**: El sistema MUST identificar a cada persona que entra al panel de forma individual;
  una clave única compartida por todo el equipo NO es suficiente.
- **FR-001a**: El sistema MUST permitir entrar con la cuenta de Google del dominio
  `centauroads.com`, y MUST rechazar cuentas de Google ajenas al dominio.
- **FR-001b**: El sistema MUST admitir, como excepción, personas con usuario y contraseña propios
  para quien no tenga cuenta del dominio; esas contraseñas MUST guardarse de forma irreversible,
  nunca en claro.
- **FR-002**: El sistema MUST registrar, para cada correo armado o enviado, qué persona lo hizo.
- **FR-003**: El sistema MUST permitir retirar el acceso de una persona concreta sin afectar al de
  las demás.
- **FR-004**: El sistema MUST limitar qué cuentas remitentes puede usar cada persona.
- **FR-004a**: El sistema MUST impedir que una persona envíe desde la cuenta personal de otra. Una
  cuenta personal (por ejemplo `equintero@`) solo la usa su titular; `mercadeo@` es compartida
  entre quienes tengan ese permiso.

**Armado del correo**

- **FR-005**: El sistema MUST permitir elegir el perfil de cliente y el formato del correo de
  forma independiente entre sí.
- **FR-006**: El sistema MUST permitir activar o desactivar cada espacio publicitario y cada
  bloque del mensaje antes de generar el correo.
- **FR-007**: El sistema MUST mostrar una vista previa fiel de lo que va a recibir el destinatario,
  incluyendo cómo se ve en pantalla de móvil.
- **FR-008**: El sistema MUST producir un correo que se vea correctamente en Gmail (web y móvil) y
  en Outlook de escritorio.
- **FR-009**: El sistema MUST ajustar la firma a la cuenta remitente elegida, manteniendo siempre
  el contacto general en el pie.
- **FR-010**: El sistema MUST impedir que se muestre un importe para un espacio cuyo precio no esté
  confirmado; en su lugar MUST indicar que se cotiza.
- **FR-011**: El contenido por defecto (textos, datos de contacto, catálogo de espacios) MUST vivir
  en un único lugar editable, no duplicado por formato ni por perfil.

**Seguimiento**

- **FR-012**: El sistema MUST generar enlaces propios para cada destinatario, de modo que una
  apertura pueda atribuirse a un contacto.
- **FR-013**: El sistema MUST conservar el registro de envíos y aperturas de forma que sobreviva a
  los despliegues de la aplicación.
- **FR-014**: El sistema MUST permitir consultar, por contacto, qué se le envió y qué abrió.
- **FR-015**: El sistema MUST avisar al equipo cuando un contacto abra la misma presentación 3
  veces en 48 horas, y MUST evitar avisos duplicados por el mismo motivo.
- **FR-016**: El aviso de interés MUST ser interno; el sistema NUNCA MUST enviar correo al cliente
  a raíz de sus aperturas.

**Respuesta en hilo**

- **FR-017**: El sistema MUST responder siempre desde el buzón que recibió la solicitud, dentro del
  mismo hilo.
- **FR-018**: El sistema MUST detectar qué espacios menciona la solicitud entrante y activar solo
  esos; si no menciona ninguno, MUST incluir el catálogo completo.
- **FR-019**: El sistema MUST disponer de un modo "solo borrador" que impida cualquier envío
  automático, y ese MUST ser el estado inicial.
- **FR-020**: El sistema MUST marcar los borradores que crea, de forma que en un buzón compartido
  se distingan de los escritos a mano.
- **FR-021**: El sistema MUST autorizar el acceso a cada buzón una sola vez, sin conocer ni
  almacenar la contraseña de esa cuenta de correo.

**Convivencia con el acortador**

- **FR-022**: El acortador de enlaces existente MUST seguir funcionando con su comportamiento
  actual; sus enlaces ya publicados MUST seguir resolviendo.
- **FR-023**: Los datos existentes del acortador MUST conservarse íntegros al desplegar esta
  capacidad.

### Key Entities *(include if feature involves data)*

- **Contacto**: la persona o empresa a la que se escribe. Nombre, correo, empresa, y cómo llegó
  (WhatsApp, Instagram, correo entrante, evento). Es a quien se atribuyen las aperturas.
- **Envío**: un correo concreto que salió. A qué contacto, qué perfil y formato se usó, qué
  espacios llevaba, desde qué cuenta remitente, quién lo armó y cuándo.
- **Espacio publicitario**: cada producto del catálogo (pantallas LED, vallas, tótem, paradas,
  rider, branding). Nombre, cobertura, ficha técnica, presentación asociada y si está disponible.
- **Perfil de cliente**: el ángulo desde el que se habla (general, agencia, cliente nuevo,
  phygital). Determina el mensaje, el orden de los espacios y el bloque propio que se incluye.
- **Cuenta remitente**: un buzón desde el que puede salir correo, con su autorización y su firma.
- **Usuario del panel**: la persona del equipo, con su rol y las cuentas remitentes que puede usar.
- **Apertura**: el hecho de que alguien abrió un enlace, con su momento y el contacto al que se
  atribuye (o anónima si no se puede atribuir).
- **Aviso**: la señal interna de que un contacto ha mostrado interés repetido.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una persona del equipo comercial arma y se lleva un correo completo en **menos de 3
  minutos** desde que entra al panel, sin ayuda y sin consultar documentación.
- **SC-002**: **Cualquier** computadora o teléfono con navegador del equipo puede armar un correo;
  hoy solo puede una.
- **SC-003**: El **100 %** de los correos enviados queda registrado con contacto, contenido, cuenta
  remitente y responsable.
- **SC-004**: El **100 %** de las aperturas de enlaces enviados a un contacto identificado se
  atribuyen a ese contacto.
- **SC-005**: Un aviso de interés llega al equipo en **menos de 15 minutos** desde la tercera
  apertura.
- **SC-006**: **Cero** correos enviados al cliente de forma automática mientras el modo "solo
  borrador" esté activo.
- **SC-007**: **Cero** interrupciones del acortador de enlaces durante y después del despliegue:
  los enlaces publicados siguen resolviendo y los datos anteriores siguen presentes.
- **SC-008**: Un cambio en un dato de contacto se refleja en **todos** los formatos y perfiles
  editándolo **una sola vez**.
- **SC-009**: Los correos generados se leen correctamente con las imágenes bloqueadas en Gmail y en
  Outlook de escritorio.

## Assumptions

- **Usuarios**: el equipo comercial de Centauro ADS, personas no técnicas, trabajando desde
  navegadores en computadoras y teléfonos con conexión estable.
- **Volumen**: decenas de correos por semana, no miles. No se diseña para envío masivo.
- **Cuentas remitentes v1**: dos, `equintero@centauroads.com` y `mercadeo@centauroads.com`. El
  diseño admite añadir más sin rehacerlo.
- **Canal del aviso de interés**: se asume que basta con verlo en el panel más un correo interno al
  equipo comercial. Si se quisiera WhatsApp, sería una ampliación posterior.
- **Presentaciones**: siguen alojadas en Canva y se alcanzan por enlace; esta capacidad no las
  reemplaza ni las copia.
- **Infraestructura**: se reutiliza la aplicación y el alojamiento del acortador existente,
  incluido su almacenamiento persistente. No se levanta un servicio nuevo.
- **Idioma**: los correos y el panel van en español de Venezuela.
- **Datos de los contactos**: son datos de negocio de Centauro ADS; no se comparten con terceros ni
  se usan para nada distinto de responder a su solicitud.
- **Detección de solicitudes entrantes**: se asume que las solicitudes llegan a los buzones
  conectados y pueden reconocerse por su contenido o por una etiqueta puesta previamente.
- **Correo corporativo**: `centauroads.com` está en Google Workspace (verificado, ver
  Clarifications), de modo que existe un administrador de dominio capaz de conceder y revocar
  accesos de forma central.

## Clarifications

### Resueltas

- **`centauroads.com` está en Google Workspace** (verificado 2026-09-19 consultando sus registros
  MX públicos: apuntan a `aspmx.l.google.com` y sus alternativos). Consecuencias: la autorización
  sobre los buzones puede concederse de forma centralizada por el administrador del dominio, y
  `mercadeo@` puede ser un buzón compartido real. También se observa en el SPF del dominio una
  ruta de correo adicional (`mx:correo.servidor365.com` y varias IP), indicio de un proveedor
  anterior que convive con Workspace; el plan debe confirmarlo antes de tocar nada de entrega.

- **Forma de entrar al panel: las dos** (decidido 2026-09-19). Google del dominio
  `@centauroads.com` como camino principal, y usuario con contraseña propia como excepción para
  quien no tenga cuenta del dominio. Recogido en FR-001a y FR-001b.

- **Permisos de envío: cada quien su cuenta, `mercadeo@` compartido** (decidido 2026-09-19).
  Elizabeth envía desde `equintero@`; el equipo de mercadeo desde `mercadeo@`. Nadie usa la cuenta
  personal de otra persona. Recogido en FR-004a.

### Pendientes

Ninguna. La lista nominal de personas del equipo y a qué grupo pertenece cada una es un dato de
configuración que se carga al poner el módulo en marcha; no condiciona el diseño.
