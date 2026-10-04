# Feature Specification: Catálogo de líneas de negocio

**Feature Branch**: `003-catalogo-lineas`

**Created**: 2026-10-03

**Status**: Draft

**Input**: User description: "arranca el catálogo de líneas de negocio con Spec Kit, alquiler de
pantalla era una sugerencia, lo importante es que la funcionalidad de agregar nuevas líneas de
negocio quede implementada" — a partir de la auditoría del 2026-10-03, donde se pidió validar que
"si mañana aparece una nueva línea de negocio, como alquiler de pantallas, esta pueda ser
perfectamente incorporada en las plantillas y debe ser un proceso que permita su inclusión en todas
o solo en algunas".

## Contexto

Centauro ADS vende hoy cinco líneas de negocio —Vallas, Pantalla LED Chacao, Pantalla LED Las
Mercedes, Tótem digital y Publicidad móvil (Rider Clon)— y las ocho plantillas de correo (A–H) las
presentan. Esas cinco líneas están **escritas en el código**. La auditoría del 2026-10-03 lo midió:

- Una línea añadida a mano a los datos **no aparece en ninguna plantilla**: el motor descarta todo
  lo que no esté en su lista fija.
- Aunque un programador la añadiera a esa lista, **no saldría en la plantilla D** (agrupa las líneas
  en tres familias fijas), **ni en la tabla de agencias** (su ficha técnica también es fija), **ni en
  el inventario de la E** (cinco filas fijas).
- No existe forma de decir **"esta línea solo en estas plantillas"**: una línea se enciende o se apaga
  para todo el correo.

El negocio crece por líneas —el alquiler de pantallas es el ejemplo que se puso, no el único— y hoy
cada línea nueva exige programar y desplegar. Esta capacidad convierte el catálogo en un **dato del
negocio**, que administra el propio equipo desde el panel.

**Alcance v1**: dar de alta, editar, ordenar y retirar líneas de negocio desde el panel, elegir en
qué plantillas aparece cada una, y que las plantillas las presenten donde hoy presentan las cinco
actuales. Queda fuera: los textos propios de cada perfil de cliente (agencia, cliente nuevo,
phygital), que son otra capacidad, y los bloques narrativos que cuentan una historia con líneas
concretas (las tres fases de la F, la pantalla protagonista de la E y la G), que siguen igual.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Añadir una línea nueva y usarla en el siguiente correo (Priority: P1)

El equipo empieza a alquilar pantallas para eventos. Un administrador entra al panel, abre
**Líneas de negocio**, pulsa *Añadir*, escribe el nombre, una etiqueta corta, la cobertura, una nota
opcional y el enlace de su presentación, sube una foto y escribe su texto alternativo, y guarda. Sin
llamar a nadie ni esperar un despliegue, cualquier persona del equipo que abra el compositor ya ve
la línea nueva entre los servicios, y los correos que prepare la incluyen.

**Why this priority**: es exactamente lo que se pidió. Sin esto, cada línea nueva pasa por un
programador y el catálogo de los correos se queda atrás del negocio.

**Independent Test**: con un administrador, dar de alta una línea con nombre, foto y enlace; abrir
el compositor en otra sesión y comprobar que aparece y que el correo de una plantilla la muestra con
su nombre, su foto y su enlace.

**Acceptance Scenarios**:

1. **Given** un administrador en *Líneas de negocio*, **When** guarda una línea nueva con nombre,
   foto y enlace, **Then** la línea aparece en el compositor de cualquier persona del equipo la
   próxima vez que lo abra, sin despliegue.
2. **Given** una línea nueva activa, **When** alguien prepara un correo con una plantilla en la que
   esa línea está incluida, **Then** el correo la muestra con su nombre, su foto, su texto
   alternativo y su enlace, en el mismo lugar y con el mismo aspecto que las líneas existentes.
3. **Given** una línea nueva sin foto todavía, **When** se prepara un correo, **Then** la línea sale
   igual, sin un hueco de imagen rota, y el panel avisa de que le falta la foto.
4. **Given** una persona con rol comercial, **When** abre *Líneas de negocio*, **Then** puede verlas
   pero no darlas de alta, editarlas ni retirarlas.

---

### User Story 2 - Decidir en qué plantillas aparece cada línea (Priority: P1)

Al dar de alta el alquiler de pantallas, el administrador decide que encaja en el catálogo general
(A, B, C, D) y en la propuesta a medida (H), pero no en la guía para clientes nuevos (F) ni en la
de agencias (E). Marca esas plantillas y deja las otras sin marcar. A partir de ahí, la línea sale en
unas y nunca en las otras, aunque esté encendida en el correo.

**Why this priority**: se pidió de forma explícita —"en todas o solo en algunas"— y sin esto una
línea pensada para un público aparece en correos dirigidos a otro.

**Independent Test**: con una línea incluida solo en A y H, preparar un correo con cada una de las
ocho plantillas y comprobar que aparece en A y H y en ninguna otra.

**Acceptance Scenarios**:

1. **Given** una línea nueva, **When** el administrador la guarda sin tocar la selección de
   plantillas, **Then** queda incluida en las ocho.
2. **Given** una línea incluida solo en A y H, **When** se prepara un correo con B, **Then** la línea
   no aparece, ni siquiera si está encendida en ese correo, y el compositor indica que en esa
   plantilla no se usa.
3. **Given** una línea sin ninguna plantilla marcada, **When** el administrador intenta guardar,
   **Then** el panel avisa de que no saldría en ningún correo y le pide confirmarlo o marcar alguna.
4. **Given** que se cambia la selección de plantillas de una línea, **When** alguien prepara un correo
   después, **Then** el cambio se aplica sin que esa persona tenga que hacer nada.

---

### User Story 3 - Editar, ordenar y retirar las líneas existentes (Priority: P2)

Las cinco líneas actuales pasan a ser del catálogo como cualquier otra: el administrador puede
corregir la cobertura de una pantalla, cambiar el enlace de su presentación, cambiar la foto,
mover una línea más arriba en el orden en que salen en los correos, o retirar una línea que el
negocio deja de vender. Retirar no borra: la línea deja de ofrecerse y de salir en los correos
nuevos, y se puede devolver.

**Why this priority**: añadir sin poder corregir ni retirar deja el catálogo envejeciendo. Va
después de P1 porque las cinco líneas actuales ya funcionan.

**Independent Test**: retirar una línea existente y comprobar que no sale en ningún correo nuevo;
devolverla y comprobar que vuelve con sus datos; cambiar el orden y comprobar que los correos lo
siguen.

**Acceptance Scenarios**:

1. **Given** las cinco líneas actuales, **When** la capacidad entra en producción, **Then** el
   catálogo las contiene con los mismos datos que hoy y los correos de las ocho plantillas salen
   idénticos a como salían antes del cambio.
2. **Given** una línea activa, **When** el administrador la retira, **Then** deja de aparecer en el
   compositor y en los correos nuevos, y la línea se conserva para poder devolverla.
3. **Given** una línea retirada, **When** el administrador la devuelve, **Then** vuelve con todos sus
   datos y su selección de plantillas.
4. **Given** el administrador cambia el orden de las líneas, **When** se prepara un correo, **Then**
   las líneas salen en ese orden (salvo donde un perfil de cliente impone el suyo, que sigue
   mandando para las líneas que ese perfil nombra; las demás van detrás, en el orden del catálogo).
5. **Given** una persona que ya había editado a mano, en su compositor, la cobertura o el enlace de
   una línea, **When** el administrador cambia otros datos de esa línea, **Then** lo que esa persona
   escribió a mano en su correo no se pierde.

---

### User Story 4 - Ficha técnica opcional: la línea entra también en las tablas (Priority: P2)

Para las agencias, una línea muestra su ficha: ubicación, medidas y tráfico. El administrador puede
rellenarla al dar de alta la línea. Si la rellena, la línea aparece también en la tabla de
disponibilidad del perfil de agencias y en el inventario de la plantilla E. Si no, esas tablas no la
muestran y nada se inventa.

**Why this priority**: sin ficha la línea ya sale en las listas de servicios (P1); la ficha la
completa para el público que compara datos.

**Independent Test**: dar de alta una línea con ficha y otra sin ficha; preparar un correo E y uno
con perfil de agencias; comprobar que la primera aparece en ambas tablas con sus datos y la segunda
en ninguna.

**Acceptance Scenarios**:

1. **Given** una línea con ubicación, medidas y tráfico, **When** se prepara un correo E o uno con el
   perfil de agencias, **Then** la línea tiene su fila en la tabla con esos datos.
2. **Given** una línea sin ficha, **When** se prepara ese mismo correo, **Then** la tabla no le dedica
   fila y no aparece ningún dato que nadie haya escrito.
3. **Given** el modo de precios apagado (como está hoy), **When** una línea tiene un precio "desde",
   **Then** el precio no sale; solo sale con el modo de precios encendido.

---

### User Story 5 - La línea en la plantilla D, en su familia (Priority: P3)

La plantilla D agrupa las líneas en familias (Gran formato, Digital outdoor, Movilidad). Al dar de
alta una línea, el administrador elige su familia de entre las existentes o crea una nueva con su
título y su etiqueta. La D la presenta dentro de su familia.

**Why this priority**: la D es una de las ocho; sin esto, una línea nueva incluida en la D no
saldría. Va la última porque las otras siete ya la muestran sin familias.

**Independent Test**: dar de alta una línea en una familia nueva "Renta de equipos" incluida en D y
comprobar que la D muestra esa familia con la línea dentro.

**Acceptance Scenarios**:

1. **Given** una línea asignada a una familia existente e incluida en D, **When** se prepara un
   correo D, **Then** la línea sale dentro de esa familia.
2. **Given** una línea asignada a una familia nueva, **When** se prepara un correo D, **Then** la
   familia aparece con su título y su etiqueta, con la línea dentro.
3. **Given** una línea incluida en D pero sin familia elegida, **When** se prepara un correo D,
   **Then** sale en una familia por defecto ("Otros servicios") en lugar de desaparecer.

---

### Edge Cases

- **Nombre repetido**: dos líneas con el mismo nombre confunden en el panel y en el correo. El alta
  avisa y no lo permite.
- **Estado guardado viejo**: cada persona tiene en su navegador una copia de las líneas del último
  correo que preparó. Una línea nueva debe entrar en esa copia, una retirada debe salir, y lo que la
  persona escribió a mano sobre una línea que sigue existiendo debe sobrevivir.
- **Correos ya preparados o guardados**: retirar o editar una línea no cambia los correos ya
  enviados ni las entregas ya guardadas.
- **Compositor sin servidor** (la copia autónoma o el artefacto de prueba): sin conexión al panel no
  hay catálogo compartido; el compositor usa el catálogo incluido de serie (las cinco líneas
  actuales) y lo dice.
- **Foto pesada o de formato raro**: el alta acepta las fotos habituales, las reduce al tamaño que
  usan los correos y rechaza lo que no sea una imagen, con un mensaje claro.
- **Plantilla H (entrega a medida)**: las líneas que acompañan la propuesta salen de este mismo
  catálogo y respetan la misma selección de plantillas.
- **Bloques narrativos**: la F (tres fases con tótem, pantalla LED y Rider), la pantalla protagonista
  de la E y la G nombran líneas concretas. No se rehacen; si una de esas líneas se retira, su bloque
  narrativo deja de mostrarla igual que hoy cuando se apaga.
- **Enlace roto**: un enlace de presentación mal escrito se avisa al guardar, como ya avisa el
  compositor con los enlaces de Canva.

## Requirements *(mandatory)*

### Functional Requirements

**Catálogo y permisos**

- **FR-301**: El sistema DEBE guardar las líneas de negocio en un catálogo compartido por todo el
  equipo, de modo que un cambio hecho por un administrador lo vean todas las personas sin despliegue.
- **FR-302**: Solo un administrador DEBE poder dar de alta, editar, reordenar, retirar y devolver
  líneas; cualquier persona con acceso al panel DEBE poder verlas.
- **FR-303**: Al entrar en producción, el catálogo DEBE contener las cinco líneas actuales con sus
  datos actuales, y los correos de las ocho plantillas DEBEN salir idénticos a los de antes mientras
  nadie cambie el catálogo.

**Datos de una línea**

- **FR-304**: Una línea DEBE tener nombre (obligatorio y único), etiqueta corta, cobertura o
  ubicación, nota opcional, texto del botón propio (opcional), enlace de su presentación, foto, texto
  alternativo de la foto y, opcionalmente, una portada alternativa con su texto alternativo para el
  juego de imágenes de portadas.
- **FR-305**: Una línea DEBE poder llevar una ficha técnica opcional —ubicación, medidas, tráfico— y
  un precio "desde" opcional, sometido al modo de precios existente.
- **FR-306**: Una línea DEBE poder asignarse a una familia de la plantilla D, existente o nueva (con
  título y etiqueta propios).
- **FR-307**: El sistema DEBE asignar a cada línea un identificador estable que no cambie al editar su
  nombre, para que los correos y el estado guardado sigan reconociéndola.

**Inclusión por plantilla**

- **FR-308**: Cada línea DEBE tener la lista de plantillas (A–H) en las que puede aparecer. Por
  defecto, todas.
- **FR-309**: Una línea DEBE aparecer en un correo solo si está activa en el catálogo, incluida en la
  plantilla de ese correo y encendida en ese correo.
- **FR-310**: El compositor DEBE indicar, junto a una línea, cuándo no se usa en la plantilla elegida,
  en vez de ofrecer un interruptor que no cambia nada.
- **FR-311**: Guardar una línea sin ninguna plantilla marcada DEBE pedir confirmación.

**Presentación en las plantillas**

- **FR-312**: Una línea incluida DEBE aparecer en las plantillas allí donde hoy aparecen las líneas
  existentes —listas, tarjetas, rejillas y la sección "También disponible"—, con el mismo aspecto.
- **FR-313**: En la tabla de agencias y en el inventario de la E, una línea DEBE tener fila solo si
  tiene ficha técnica.
- **FR-314**: En la D, una línea DEBE salir dentro de su familia; sin familia, en "Otros servicios".
- **FR-315**: Una línea sin foto DEBE salir sin hueco de imagen rota.
- **FR-316**: Cuando un perfil de cliente impone un orden propio, las líneas que el perfil nombra
  DEBEN seguir ese orden y las demás DEBEN ir detrás, en el orden del catálogo.

**Fotos**

- **FR-317**: El administrador DEBE poder subir la foto de una línea desde el panel; el sistema DEBE
  guardarla de forma persistente, servirla con una dirección pública estable (la que usan los
  correos) y reducirla al tamaño que usan las plantillas.
- **FR-318**: El sistema DEBE rechazar con un mensaje claro un archivo que no sea una imagen o que
  supere el tamaño máximo.

**Retirar y conservar**

- **FR-319**: Retirar una línea NO DEBE borrarla: deja de ofrecerse y de salir en correos nuevos, y
  DEBE poder devolverse con todos sus datos.
- **FR-320**: Editar o retirar una línea NO DEBE alterar correos ya enviados ni entregas guardadas.

**Estado guardado**

- **FR-321**: El estado guardado de cada persona DEBE incorporar las líneas nuevas, quitar las
  retiradas y conservar lo que la persona escribió a mano en las que siguen, sin descartar su
  trabajo (constitución, principio II).

**Convivencia**

- **FR-322**: El acortador y sus rutas existentes NO DEBEN verse afectados (constitución, principio I):
  la capacidad añade datos y rutas; no cambia ni retira ninguna.
- **FR-323**: Sin conexión al panel, el compositor DEBE seguir funcionando con el catálogo de serie y
  decirlo.

### Key Entities *(include if feature involves data)*

- **Línea de negocio**: algo que Centauro ADS vende y que los correos presentan. Identificador
  estable, nombre, etiqueta corta, cobertura, nota, texto del botón, enlace de presentación, foto y
  su texto alternativo, portada opcional y su texto alternativo, ficha técnica opcional (ubicación,
  medidas, tráfico), precio "desde" opcional, familia de la D, plantillas en las que puede aparecer,
  posición en el orden, estado (activa o retirada), quién y cuándo la cambió por última vez.
- **Familia (plantilla D)**: agrupación visual de líneas en la D. Título, etiqueta corta, posición.
  Las tres actuales (Gran formato, Digital outdoor, Movilidad) se conservan.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-301**: Un administrador da de alta una línea nueva, con foto y enlace, en menos de 3 minutos,
  sin programar ni desplegar.
- **SC-302**: Una línea nueva aparece en el 100 % de las plantillas marcadas y en el 0 % de las no
  marcadas, comprobado en las 8 plantillas y los 4 perfiles.
- **SC-303**: Tras la puesta en producción, y sin tocar el catálogo, los 16 correos de referencia
  salen idénticos byte a byte a los anteriores.
- **SC-304**: Ninguna persona pierde texto escrito a mano en su compositor por la migración ni por
  cambios posteriores del catálogo (0 casos en las pruebas de migración).
- **SC-305**: Una línea retirada desaparece de los correos nuevos de todas las personas la próxima vez
  que abren el compositor, y se devuelve con todos sus datos.
- **SC-306**: El acortador sigue respondiendo y sus enlaces existentes siguen redirigiendo igual
  antes y después del despliegue.

## Assumptions

- La gestión del catálogo es de **administradores**, igual que la del equipo; los comerciales usan las
  líneas pero no las cambian.
- El catálogo vive en el **servidor** y se comparte; el compositor lo pide al abrirse. La copia
  autónoma sin servidor usa las cinco líneas de serie.
- Las **fotos** se suben desde el panel y se guardan en el almacenamiento persistente del servidor,
  igual que las páginas de las entregas; también se puede elegir una foto que ya exista.
- **Textos de los perfiles** (agencia, cliente nuevo, phygital) y las etiquetas fijas detectadas en la
  auditoría quedan para otra capacidad.
- Los **bloques narrativos** que cuentan una historia con líneas concretas (fases de la F,
  protagonista de la E y de la G) no cambian.
- El **banco de imágenes** por línea (fotos alternativas y fotogramas de vídeo) se mantiene para las
  cinco actuales; una línea nueva empieza con su foto principal y puede ampliarlo después.
- Los datos que el equipo introduce (cobertura, ficha, precios) son responsabilidad de quien los
  escribe: el sistema no los valida contra ninguna fuente externa (constitución, principio IV).
