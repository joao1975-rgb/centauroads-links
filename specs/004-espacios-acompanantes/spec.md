# Feature Specification: Espacios que acompañan, personalizados en la entrega

**Feature Branch**: `004-espacios-acompanantes`

**Created**: 2026-10-06

**Status**: Draft

**Input**: User description: "falta que las opciones contenidas en el frame «Espacios que la
acompañan» permiten colocar el link de la presentación, pero no generan las imágenes de dicha
presentación para seleccionar las imágenes y conformar el carrusel. Esto debe comportarse igual que
la opción de conformar la presentación personalizada principal. Valida que en cada una de las
opciones que se modifiquen, se aparten de las opciones estándar, se personalice cada una de estas
opciones dentro de este frame." Decisiones del propietario (2026-10-06): el cambio vale **solo para
esa entrega**, y se personaliza **enlace, carrusel y textos** de cada espacio.

## Contexto

La plantilla H (Personalizada) entrega la presentación propia de un cliente. Su presentación
principal ya se arma de punta a punta: se sube el PDF que exporta Canva (o imágenes sueltas), se
eligen de 2 a 4 páginas, se arma el carrusel y todo queda guardado con la entrega (002).

Debajo, en **«Espacios que la acompañan»**, van los espacios del catálogo que acompañan la propuesta.
Hoy cada uno sale con su foto o su carrusel **estándar** del catálogo. Se puede cambiar su enlace,
pero:

- **Las imágenes no siguen al enlace.** Si a un cliente se le arma también una presentación propia
  de la Pantalla LED de Las Mercedes, el enlace apunta a ella pero la imagen sigue siendo la del
  catálogo: el correo enseña una cosa y lleva a otra.
- **El cambio no se queda en la entrega.** Cambiar el enlace de un espacio en la H lo cambia en todo
  el compositor: alcanza también a las plantillas A–G y a la siguiente entrega que se arme.
- **No se guarda en el servidor.** La entrega solo recuerda *qué* espacios lleva, no cómo se
  cambiaron. Al reabrirla desde otra computadora, los cambios no están.

Esta capacidad hace que cada espacio acompañante pueda **personalizarse dentro de la entrega** con
el mismo flujo que la presentación principal, sin tocar nada fuera de ella.

**Alcance v1**: personalizar enlace, carrusel, nombre y cobertura de cada espacio acompañante dentro
de una entrega; guardarlo con la entrega; volver al estándar. Queda fuera: personalizar espacios en
las plantillas A–G (siguen con el catálogo), y cambiar el catálogo desde la entrega (eso es de
*Líneas de negocio*, 003).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - El carrusel de un espacio sigue a su presentación (Priority: P1)

Elizabeth arma la entrega de un cliente. Además de su propuesta principal, al cliente se le preparó
una presentación propia de la Pantalla LED Las Mercedes. En «Espacios que la acompañan» abre ese
espacio, pega el enlace nuevo y, como con la principal, sube el PDF de esa presentación, elige dos o
tres páginas, elige el efecto y arma el carrusel. El correo muestra ese espacio con **sus** imágenes
y lleva a **su** presentación.

**Why this priority**: es exactamente lo que falta. Sin esto, un espacio con presentación propia sale
con imágenes que no corresponden a su enlace.

**Independent Test**: con una entrega guardada, en un espacio acompañante subir un PDF de 3 páginas,
elegir 2 y armar el carrusel; el correo H muestra ese carrusel en ese espacio y su enlace nuevo, y
los demás espacios siguen con el estándar.

**Acceptance Scenarios**:

1. **Given** una entrega guardada y un espacio acompañante, **When** se sube el PDF de su
   presentación, **Then** se ven sus páginas como miniaturas elegibles, igual que en la principal.
2. **Given** las miniaturas de un espacio, **When** se eligen entre 2 y 4 en un orden y un efecto,
   **Then** se arma el carrusel de ese espacio y el correo H lo muestra en su lugar, con la primera
   página elegida como imagen fija para quien no ve animaciones.
3. **Given** un espacio sin PDF, **When** se suben imágenes sueltas, **Then** sirven igual que las
   páginas de un PDF.
4. **Given** una página elegida que contiene un precio escrito como texto, **When** se arma el
   carrusel, **Then** se avisa, como en la principal.
5. **Given** un espacio con carrusel propio, **When** se arma o se rehace el de la principal,
   **Then** el del espacio no cambia (y al revés).

---

### User Story 2 - Lo que se cambia se queda en esta entrega (Priority: P1)

Elizabeth cambia el enlace, el nombre o la cobertura de un espacio dentro de la entrega. Ese cambio
vale para el correo de **esta** entrega y nada más: las plantillas A–G siguen mostrando el espacio
del catálogo, y la siguiente entrega empieza con el espacio estándar.

**Why this priority**: sin esto, un enlace o un texto pensado para un cliente se cuela en los correos
de catálogo y en las entregas de otros clientes.

**Independent Test**: personalizar un espacio en una entrega; abrir la plantilla A y otra entrega:
ambas muestran el espacio estándar.

**Acceptance Scenarios**:

1. **Given** un espacio personalizado en una entrega, **When** se arma un correo A–G, **Then** ese
   espacio sale con los datos del catálogo.
2. **Given** un espacio personalizado en la entrega X, **When** se arma la entrega Y, **Then** Y lo
   muestra estándar.
3. **Given** un espacio en el que solo se tocó la cobertura, **When** se genera el correo H,
   **Then** cambia la cobertura y todo lo demás sigue siendo el estándar (incluido el carrusel).

---

### User Story 3 - Se ve qué está personalizado y se puede volver al estándar (Priority: P2)

En «Espacios que la acompañan» cada espacio dice si sale **estándar** o **personalizado para esta
entrega**, y qué tiene de propio (enlace, imágenes, textos). Un espacio personalizado puede volver al
estándar en un paso.

**Why this priority**: con varios espacios, sin esa marca nadie sabe cuál lleva qué antes de
copiar el correo al cliente.

**Independent Test**: personalizar dos de cuatro espacios; la lista marca exactamente esos dos;
devolver uno al estándar lo deja igual que el catálogo, carrusel incluido.

**Acceptance Scenarios**:

1. **Given** espacios estándar y personalizados, **When** se mira la lista, **Then** cada uno indica
   su estado y qué tiene de propio.
2. **Given** un espacio personalizado, **When** se vuelve al estándar, **Then** recupera enlace,
   textos e imágenes del catálogo y deja de marcarse como personalizado.
3. **Given** un campo cuyo valor nuevo es igual al del catálogo, **When** se guarda, **Then** no
   cuenta como personalización.

---

### User Story 4 - Al reabrir la entrega, todo sigue ahí (Priority: P2)

Elizabeth deja una entrega a medias y la termina al día siguiente desde otra computadora. Al reabrirla,
cada espacio acompañante conserva su enlace, sus textos, sus páginas elegidas y su carrusel.

**Why this priority**: la entrega ya se guarda y se recupera (002); un espacio personalizado que se
perdiera al reabrir obligaría a rehacer el trabajo.

**Independent Test**: personalizar un espacio, cerrar, abrir la entrega en otra sesión y comprobar
que el espacio sale igual en el panel y en el correo.

**Acceptance Scenarios**:

1. **Given** una entrega con espacios personalizados, **When** se reabre en otra sesión, **Then** los
   espacios conservan enlace, textos, páginas y carrusel.
2. **Given** una entrega reabierta, **When** se rehace el carrusel de un espacio, **Then** el correo
   usa el nuevo y no una copia vieja guardada por el navegador o por Gmail.

---

### Edge Cases

- **Espacio quitado de la entrega**: si se desmarca un espacio personalizado, su personalización se
  conserva con la entrega; si se vuelve a marcar, vuelve como estaba.
- **Espacio retirado del catálogo** después de personalizarlo: ya no se ofrece al armar correos nuevos
  de esa entrega; lo ya enviado no cambia.
- **Catálogo editado** después de personalizar: lo personalizado se queda como se dejó; lo no
  personalizado sigue al catálogo.
- **Entrega sin guardar**: no hay dónde guardar las páginas de un espacio; se pide guardar la entrega
  primero, como ya pasa con la principal.
- **Enlace no válido** (sin https://, o que no abre): se avisa igual que con el enlace principal.
- **Carrusel rehecho**: se reemplaza el anterior de ese espacio; el correo debe enseñar el nuevo.
- **Un correo ya enviado** sigue apuntando a sus imágenes: no se borran mientras exista la entrega.
- **Espacio sin foto en el catálogo** (línea nueva de la 003 sin foto): puede personalizarse igual.

## Requirements *(mandatory)*

### Functional Requirements

**Personalizar un espacio dentro de la entrega**

- **FR-401**: El sistema MUST permitir, para cada espacio acompañante de una entrega, cambiar su
  enlace de presentación, su nombre y su cobertura, y armar su propio carrusel.
- **FR-402**: Esos cambios MUST valer solo para esa entrega: las plantillas A–G y las demás entregas
  MUST seguir mostrando el espacio del catálogo.
- **FR-403**: Un campo MUST contar como personalizado solo si su valor difiere del catálogo; volver a
  escribir el valor del catálogo lo deja estándar.
- **FR-404**: El enlace de un espacio MUST validarse igual que el enlace principal de la entrega.

**Carrusel de un espacio (igual que el de la principal)**

- **FR-405**: El sistema MUST aceptar para cada espacio el PDF exportado de su presentación o
  imágenes sueltas, con los mismos formatos y límites que la presentación principal (002, FR-108,
  FR-109, FR-114).
- **FR-406**: El sistema MUST mostrar sus páginas como miniaturas y permitir elegir entre 2 y 4, en
  orden, y el efecto, igual que en la principal (002, FR-110).
- **FR-407**: El carrusel de un espacio MUST tener como primer fotograma la primera página elegida
  (002, FR-111) y MUST avisar de precios escritos en las páginas elegidas (002, FR-112).
- **FR-408**: Las páginas y el carrusel de cada espacio MUST ser independientes de los de la
  principal y de los de los otros espacios: rehacer uno no toca los demás.
- **FR-409**: El correo H MUST mostrar el carrusel propio de un espacio en lugar de su foto o
  carrusel estándar; un espacio sin carrusel propio MUST seguir con el estándar.
- **FR-410**: Al rehacer el carrusel de un espacio, el correo MUST enseñar el nuevo (sin quedarse con
  una copia anterior en caché).

**Estado y retorno al estándar**

- **FR-411**: Cada espacio MUST indicar si sale estándar o personalizado para la entrega, y qué tiene
  de propio (enlace, imágenes, textos).
- **FR-412**: El sistema MUST permitir devolver un espacio al estándar en un paso, recuperando
  enlace, textos e imágenes del catálogo.

**Persistencia**

- **FR-413**: Las personalizaciones de cada espacio MUST guardarse con la entrega en el servidor y
  recuperarse al reabrirla desde cualquier sesión.
- **FR-414**: Las imágenes de un espacio MUST conservarse mientras exista la entrega: un correo ya
  enviado sigue apuntando a ellas.
- **FR-415**: Desmarcar un espacio personalizado MUST conservar su personalización con la entrega.

**Sin cambios fuera de la entrega**

- **FR-416**: Las plantillas A–H generadas sin personalizaciones MUST seguir saliendo idénticas byte a
  byte a las de referencia.
- **FR-417**: El estado guardado en el navegador de quien ya usa el compositor MUST sobrevivir al
  cambio, sin perder lo escrito a mano (constitución: nunca subir CONTENT_VERSION).
- **FR-418**: Las reglas de acceso de la entrega (002) MUST aplicarse a sus espacios: solo con sesión
  del panel; las imágenes públicas se sirven con las mismas comprobaciones que las de la principal.

### Key Entities *(include if feature involves data)*

- **Espacio de una entrega**: un espacio acompañante dentro de una entrega concreta. Recuerda qué
  línea del catálogo es y, solo si se cambiaron, su enlace, nombre y cobertura propios.
- **Páginas de un espacio**: las imágenes sacadas de la presentación de ese espacio, con su orden en
  el carrusel; como las páginas de la principal, pero de un espacio.
- **Carrusel de un espacio**: la animación armada con esas páginas, con su efecto.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-401**: Personalizar el carrusel de un espacio (subir, elegir, armar) lleva lo mismo que el de la
  principal: menos de 2 minutos con el PDF a mano.
- **SC-402**: Con un espacio personalizado en una entrega, el 100 % de los correos A–G y de las otras
  entregas lo muestran estándar.
- **SC-403**: Al reabrir una entrega en otra sesión, el 100 % de sus espacios personalizados conservan
  enlace, textos y carrusel.
- **SC-404**: En la lista de espacios, cualquier persona del equipo distingue en un vistazo cuáles van
  personalizados (verificado con la propietaria).
- **SC-405**: Los 16 correos de referencia salen idénticos y el estado guardado de quien ya usa la
  herramienta no pierde nada.

## Assumptions

- Personalizar espacios es parte de armar la entrega: lo hace quien arma la entrega (cualquier persona
  con sesión del panel), como el resto de la entrega. No hace falta rol de administrador.
- El enlace propio de un espacio se usa tal cual, como hoy el de los espacios; el seguimiento de
  aperturas atribuible sigue siendo el del enlace principal de la entrega (002).
- Las formas de sacar imágenes son las mismas que en la principal: PDF, imágenes sueltas y la
  alternativa sin subir que ya ofrece el compositor.
- Las imágenes viven donde viven las de la entrega (volumen persistente), nunca en el repositorio, que
  es público.
- La foto estándar y el carrusel estándar del catálogo no cambian; solo se sustituyen dentro del
  correo de esa entrega.
