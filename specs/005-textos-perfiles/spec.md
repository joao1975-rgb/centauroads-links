# Feature Specification: Textos de los perfiles, editables por el equipo

**Feature Branch**: `005-textos-perfiles`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "sigue con los textos de los perfiles editables" — a partir de la
auditoría del 2026-10-03, que midió que unos 55 textos de los perfiles de cliente (agencia, cliente
nuevo, phygital) estaban fijos en el código, sin campo en el compositor. Decisión de la propietaria
(2026-10-06): los textos son **del equipo**; los edita **un administrador** en el panel y llegan a
todos los compositores, como el catálogo de líneas de negocio (003).

## Contexto

El compositor arma cada correo con un formato (A–H) y un **perfil de cliente**: General, Agencias y
grandes cuentas, Cliente nuevo, y Phygital. El perfil cambia el mensaje sin cambiar el formato: el
asunto, el texto que se ve antes de abrir, el título, la entrada, el cierre, el botón y un bloque
propio de cada audiencia (la tabla de disponibilidad para agencias, la ruta de tres pasos para el
cliente nuevo, el puente calle–móvil para phygital). Además, cada perfil ofrece **tres asuntos** para
elegir (directo, beneficio, curiosidad).

Todos esos textos están **escritos en el código**. Cambiar una coma de la ruta del cliente nuevo, o
ajustar el asunto de agencias a la temporada, exige un programador y un despliegue. El mensaje es del
negocio y lo tiene que poder ajustar el propio equipo.

**Alcance v1**: editar desde el panel, por un administrador, los textos de cada perfil, sus tres
asuntos y los textos de su bloque propio; que lleguen a todos los compositores; y poder volver al
texto de serie. Queda fuera: crear perfiles nuevos, cambiar el orden de los servicios de cada perfil,
el nombre y la descripción con que el compositor presenta cada perfil, y los textos de las plantillas
que no dependen del perfil.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ajustar el mensaje de un perfil sin programar (Priority: P1)

Elizabeth quiere que el correo para agencias diga «Inventario de diciembre» en vez de «Inventario
disponible» y que el botón pida «tarifas de temporada». Entra al panel, abre **Textos de los perfiles**,
elige *Agencias y grandes cuentas*, cambia el título y el botón y guarda. Desde ese momento, cualquier
persona del equipo que arme un correo con el perfil de agencias lo ve con los textos nuevos.

**Why this priority**: es exactamente lo que falta; sin esto cada ajuste de mensaje pasa por un
programador.

**Independent Test**: un administrador cambia el título y el botón de un perfil; en otra sesión, un
correo con ese perfil los muestra; un correo con otro perfil no cambia.

**Acceptance Scenarios**:

1. **Given** un administrador en *Textos de los perfiles*, **When** cambia el asunto, el texto previo,
   el título, el subtítulo, la entrada, el cierre o el botón de un perfil y guarda, **Then** los correos
   de ese perfil los usan en todos los compositores del equipo.
2. **Given** un texto con los marcadores del compositor (`{destinatario}`, `{empresa}`), **When** se usa
   en un correo, **Then** se sustituyen igual que en el resto del correo.
3. **Given** una persona con rol comercial, **When** abre *Textos de los perfiles*, **Then** los ve pero
   no puede cambiarlos.

---

### User Story 2 - Los tres asuntos de cada perfil (Priority: P1)

Los tres asuntos que ofrece cada perfil (directo, beneficio, curiosidad), también los del perfil
General, se editan en el mismo sitio. El compositor ofrece los nuevos al elegir asunto.

**Why this priority**: el asunto es lo único que se ve antes de abrir; es el texto que más se quiere
ajustar.

**Independent Test**: cambiar el asunto «curiosidad» del perfil General; el compositor lo ofrece y el
correo lo lleva al elegirlo.

**Acceptance Scenarios**:

1. **Given** un administrador, **When** cambia uno de los tres asuntos de un perfil, **Then** el
   compositor ofrece el nuevo en su lugar, con su misma etiqueta.
2. **Given** un asunto con emoji, **When** se guarda, **Then** se conserva tal cual.

---

### User Story 3 - El bloque propio de cada perfil (Priority: P2)

Los textos del bloque de cada perfil también se editan: los tres pasos de la ruta del cliente nuevo
(título, qué formato, para qué sirve y qué se consigue en cada uno), los textos del puente de phygital
y las cabeceras de la tabla de agencias.

**Why this priority**: son la parte más larga y más propia de cada mensaje, pero cambian menos que el
asunto o el botón.

**Independent Test**: cambiar el texto del paso 2 de la ruta; el correo del perfil cliente nuevo lo
muestra en ese paso.

**Acceptance Scenarios**:

1. **Given** un administrador, **When** cambia un texto del bloque de un perfil, **Then** el correo de
   ese perfil lo muestra en su sitio, en todas las plantillas que lo pintan.

---

### User Story 4 - Volver al texto de serie (Priority: P3)

Cada texto editado se puede devolver al de serie en un paso, y la pantalla dice qué textos de cada
perfil están cambiados.

**Why this priority**: da seguridad para probar cambios sin miedo a perder el texto original.

**Independent Test**: cambiar un texto, devolverlo al de serie; el correo vuelve a ser idéntico al de
antes y la pantalla deja de marcarlo como cambiado.

**Acceptance Scenarios**:

1. **Given** un texto cambiado, **When** se devuelve al de serie, **Then** el correo vuelve a llevar el
   texto original y la pantalla lo muestra como de serie.

---

### Edge Cases

- **Texto vacío**: no se guarda; para quitar un cambio está «volver al de serie». Un asunto o un botón
  vacíos dejarían un correo roto.
- **Texto muy largo**: hay un límite por campo; se avisa al pasar de él.
- **Dos administradores a la vez**: gana el último que guarda; la pantalla muestra quién cambió cada
  perfil por última vez.
- **Un compositor abierto** mientras se cambia un texto: recibe el nuevo la próxima vez que se abra.
- **Lo escrito a mano en un correo**: el equipo puede seguir retocando el correo antes de copiarlo,
  como hoy; los textos de los perfiles son el punto de partida.
- **Texto con HTML o código**: se trata como texto; nunca se interpreta.

## Requirements *(mandatory)*

### Functional Requirements

**Edición**

- **FR-501**: El sistema MUST permitir a un administrador editar, para cada perfil, su asunto, texto
  previo, título, subtítulo, entrada, cierre y texto del botón.
- **FR-502**: El sistema MUST permitir editar los tres asuntos de cada perfil, incluido el General,
  conservando su clave y su etiqueta (directo, beneficio, curiosidad).
- **FR-503**: El sistema MUST permitir editar los textos del bloque propio de cada perfil: los tres
  pasos de la ruta del cliente nuevo, los textos del puente de phygital y las cabeceras de la tabla de
  agencias.
- **FR-504**: Solo un administrador MUST poder cambiar textos; un comercial MUST poder verlos.
- **FR-505**: Ningún texto MUST quedar vacío; cada campo MUST tener un límite de longitud.
- **FR-506**: El sistema MUST permitir devolver cualquier texto al de serie y MUST indicar qué textos
  están cambiados.
- **FR-507**: El sistema MUST registrar quién cambió cada perfil por última vez y cuándo.

**Uso en los correos**

- **FR-508**: Los textos guardados MUST llegar a todos los compositores del equipo sin desplegar nada.
- **FR-509**: Los marcadores `{destinatario}` y `{empresa}` MUST seguir funcionando en los textos
  editados.
- **FR-510**: Los textos MUST tratarse siempre como texto, nunca como HTML.
- **FR-511**: Sin textos cambiados, los correos MUST salir idénticos byte a byte a los de referencia.
- **FR-512**: El estado guardado en el navegador de quien ya usa el compositor MUST sobrevivir al
  cambio, sin perder lo escrito a mano (constitución: nunca subir CONTENT_VERSION).
- **FR-513**: Si el servidor no responde, el compositor MUST seguir con los textos de serie y decirlo.

### Key Entities *(include if feature involves data)*

- **Texto de perfil**: un texto concreto de un perfil (por ejemplo, «agencia · botón» o «nuevo · paso 2 ·
  para qué sirve»), con su valor cambiado, quién lo cambió y cuándo. Lo que no está cambiado es el de
  serie.
- **Texto de serie**: el que trae el motor; es la referencia y el valor al que se vuelve.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-501**: Un administrador cambia el texto de un perfil y lo ve en un correo de otra sesión en menos
  de 1 minuto, sin pedir nada a nadie.
- **SC-502**: El 100 % de los textos fijos de los perfiles que midió la auditoría se pueden editar desde
  el panel.
- **SC-503**: Sin cambios, los 16 correos de referencia salen idénticos; con un cambio, solo cambia el
  texto tocado en los correos de su perfil.
- **SC-504**: Devolver un texto al de serie deja el correo idéntico al de antes del cambio.
- **SC-505**: Ningún comercial puede cambiar un texto (comprobado).

## Assumptions

- Los textos de serie siguen viviendo en el motor (`render.js`) y son la única fuente: el servidor
  guarda solo los cambios, igual que el catálogo de la 003 se siembra del motor.
- Los perfiles son los cuatro de hoy; crear perfiles nuevos es otra capacidad.
- El orden de los servicios de cada perfil, y el nombre y la descripción con que el compositor presenta
  cada perfil, quedan como están.
- La edición se hace en una pantalla del panel parecida a *Líneas de negocio*, no dentro del compositor.
