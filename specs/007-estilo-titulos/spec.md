# Feature Specification: Estilo de los títulos (tipografía y tamaño)

**Feature Branch**: `007-estilo-titulos`

**Created**: 2026-10-12

**Status**: Draft

**Input**: Petición de la propietaria (2026-10-12): «realiza una adecuación de opciones estéticas en las
ventanas de inserción de títulos de diferentes tamaños, siendo el actual el base y permitiendo agrandar
hasta un máximo nivel de espacio, así como también permitir cambiar la tipografía, que solo debe hacerse
en función de las mejores combinaciones de estrategias de comunicación, como las empleadas en Instagram».

Decisiones tomadas con maquetas (brainstorming, 2026-10-12):
- **Solo tipografías seguras**: Gmail no carga fuentes de internet; las parejas usan fuentes que ya tienen
  los equipos y móviles, para que se vean igual en Gmail, Outlook y el teléfono.
- **Parejas elegidas**: Centauro (la actual, por defecto), **Impacto**, **Editorial** y **Moderna**.
- **Tamaños**: Base (el de hoy), Grande (×1,25) y Máximo (×1,5).

La otra petición del mismo mensaje —incorporar un producto a medida en la H— va en su propia
especificación (008).

## Contexto

Cada plantilla pinta su título principal a un tamaño fijo (A 54 px, B 48 px, D 46 px…) con la pareja de
siempre: Montserrat → Trebuchet para títulos y Segoe UI para el texto. Quien redacta no puede darle más
presencia al título ni cambiar el tono visual del correo según el cliente.

Un correo no puede adaptar el tamaño a cada pantalla: las reglas que lo harían (media queries) se pierden
al pegar en Gmail, y por eso las plantillas no las usan. **Hay un solo tamaño para escritorio y móvil.**

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Elegir la pareja de tipografías (Priority: P1)

Al armar un correo, quien redacta elige junto al título una de cuatro parejas. La pareja cambia el título
y el texto de todo ese correo.

| Pareja | Título | Texto |
|---|---|---|
| **Centauro** (por defecto) | La de hoy en cada plantilla (condensada DIN/Bahnschrift en A, B y D; Montserrat → Trebuchet en E–H) | La de hoy (Segoe UI → Roboto → Arial) |
| **Impacto** | Impact, en mayúsculas | Georgia |
| **Editorial** | Georgia, negrita itálica | Arial |
| **Moderna** | Arial Black | Verdana |

Cada pila lleva sus fuentes de respaldo, por si el equipo de quien lee no tuviera la primera.

**Independent Test**: elegir «Impacto» en la plantilla A; el título sale en Impact y en mayúsculas, y el
texto en Georgia. Volver a «Centauro» deja el correo idéntico al de antes.

**Acceptance Scenarios**:

1. **Given** un correo nuevo, **When** no se toca nada, **Then** sale con la pareja Centauro, idéntico al
   de hoy.
2. **Given** la pareja Impacto, Editorial o Moderna, **When** se arma el correo en cualquiera de las
   plantillas A–H, **Then** el título y el texto usan esa pareja.

---

### User Story 2 - Elegir el tamaño del título (Priority: P1)

Junto al título, tres tamaños: **Base** (el de hoy en esa plantilla), **Grande** (×1,25) y **Máximo**
(×1,5). Solo cambia el título principal.

**Independent Test**: en la plantilla A, Grande da un título de 68 px y Máximo de 81 px, si el título
cabe.

**Acceptance Scenarios**:

1. **Given** un correo nuevo, **When** no se toca nada, **Then** el título sale en Base, idéntico al de hoy.
2. **Given** Grande o Máximo, **When** la palabra más larga del título no cabría a lo ancho de un teléfono
   (327 px de texto), **Then** el motor baja el tamaño lo justo para que quepa —en escritorio y en móvil,
   porque es un solo tamaño— y el compositor lo dice: «Máximo se ajustó a 62 px para que quepa en el
   móvil».
3. **Given** Base, **Then** el tamaño no se ajusta nunca (es el de hoy).

---

### User Story 3 - Que la elección se conserve (Priority: P2)

La pareja y el tamaño quedan con el correo que se está armando. En la H, se guardan también con la
entrega, para que al abrirla en otra computadora salga igual.

**Acceptance Scenarios**:

1. **Given** una pareja y un tamaño elegidos, **When** se recarga el compositor, **Then** siguen elegidos.
2. **Given** una entrega guardada con Editorial y Grande, **When** se abre desde otra computadora,
   **Then** sale con Editorial y Grande.

---

### Edge Cases

- **Estado guardado de antes** (sin pareja ni tamaño): sale como hoy (Centauro, Base). No se sube
  `CONTENT_VERSION`.
- **Título muy largo o de una sola palabra larga** en Máximo: se ajusta hasta que quepa; nunca por
  debajo del tamaño Base. Si ni el Base cupiera, queda en Base: el mismo resultado que hoy.
- **Texto plano y WhatsApp**: no cambian (no tienen tipografía).
- **Bloques con su propio rótulo grande** (fases de la G, cifras de la E…): siguen con su tamaño; solo
  cambia su tipografía según la pareja.

## Requirements *(mandatory)*

- **FR-701**: El compositor MUST ofrecer, junto al título principal, la pareja (Centauro, Impacto,
  Editorial, Moderna) y el tamaño (Base, Grande, Máximo).
- **FR-702**: La pareja MUST aplicarse al título y al texto de todo el correo, en las plantillas A–H.
- **FR-703**: El tamaño MUST aplicarse solo al título principal: ×1 / ×1,25 / ×1,5 sobre el tamaño de
  esa plantilla.
- **FR-704**: Con Grande o Máximo, si la palabra más larga no cabe en 327 px, el tamaño MUST bajar lo
  justo para que quepa, sin bajar del Base, y el compositor MUST decirlo.
- **FR-705**: Las tipografías MUST ser solo fuentes de sistema, con sus respaldos; ninguna fuente de
  internet.
- **FR-706**: Sin elección (o con Centauro y Base), los 16 correos de referencia MUST salir idénticos
  byte a byte.
- **FR-707**: La elección MUST conservarse en el estado del compositor y, en la H, con la entrega.
- **FR-708**: El texto plano y el de WhatsApp MUST NOT cambiar.

## Success Criteria *(mandatory)*

- **SC-701**: Con cualquier pareja y tamaño, ningún correo desborda a 600 ni a 375 px.
- **SC-702**: Sin elegir nada, los correos son idénticos a los de hoy.
- **SC-703**: Elegir pareja y tamaño son dos clics junto al título.

## Assumptions

- «Título principal» es el del bloque Título en A–G y el título de la propuesta en la H.
- El ancho de referencia del móvil es 375 px con 24 px de margen a cada lado (327 px de texto), el mismo
  con el que se comprueban las plantillas.
- El ajuste se calcula con anchos medios de carácter por tipografía, con margen de seguridad; se
  comprueba en navegador real.
