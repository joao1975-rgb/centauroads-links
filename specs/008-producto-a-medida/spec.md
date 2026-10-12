# Feature Specification: Producto a medida en la entrega (H)

**Feature Branch**: `008-producto-a-medida`

**Created**: 2026-10-12

**Status**: Draft

**Input**: Petición de la propietaria (2026-10-12): «en la opción donde aparecen las opciones para insertar
otros productos, permite la incorporación de otros».

Decisiones tomadas (brainstorming, 2026-10-12):
- Es un producto **a medida dentro de la H**, en «Espacios que la acompañan», **solo para esa entrega**.
- Lleva **lo mismo que un espacio**: nombre, una línea de texto, enlace a su presentación y su carrusel.
- Un administrador puede **«Pasar al catálogo»**: lo convierte en línea de negocio para todo el equipo.

Se apoya en la especificación 004 (espacios que acompañan la entrega), que ya permite personalizar, solo
para una entrega, los espacios del catálogo.

## Contexto

Hoy la H solo ofrece los espacios del catálogo de líneas de negocio. Cuando una propuesta incluye algo
que no está en el catálogo (una pantalla en un evento, una activación, un formato puntual), no hay dónde
ponerlo: o se da de alta una línea para todo el equipo por un solo cliente, o se queda fuera del correo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Añadir un producto que no está en el catálogo (Priority: P1)

En la H, al final de «Espacios que la acompañan», **«+ Añadir otro producto»** abre una ficha con nombre,
una línea de texto (qué es o dónde), el enlace a su presentación y su carrusel —subiendo el PDF o las
imágenes, con la misma galería que los demás espacios—. El correo lo muestra con el mismo diseño que los
demás espacios.

**Independent Test**: añadir «Pantalla en evento» con su texto, su enlace y un PDF de tres páginas; el
correo H lo muestra con su carrusel, su texto y «Ver presentación»; las plantillas A–G no lo muestran.

**Acceptance Scenarios**:

1. **Given** una entrega guardada, **When** se añade un producto con nombre, **Then** aparece en la lista
   de espacios de esa entrega y en el correo, después de los del catálogo.
2. **Given** un producto a medida, **When** se sube su PDF o sus imágenes y se eligen páginas, **Then**
   su carrusel se arma igual que el de un espacio del catálogo.
3. **Given** un producto a medida, **When** se arma el correo de cualquier plantilla A–G u otra entrega,
   **Then** no aparece.
4. **Given** 5 productos a medida en una entrega, **When** se intenta añadir otro, **Then** no se permite
   y se dice por qué.

---

### User Story 2 - Editarlo, quitarlo y recuperarlo (Priority: P1)

El producto a medida se edita y se quita como un espacio más, y se guarda con la entrega.

**Acceptance Scenarios**:

1. **Given** un producto a medida, **When** se cambia su nombre, texto o enlace, **Then** el correo lo
   refleja.
2. **Given** un producto a medida, **When** se quita, **Then** deja de salir en la entrega y en el correo.
3. **Given** una entrega con productos a medida, **When** se abre desde otra computadora, **Then** salen
   con sus datos y su carrusel.
4. **Given** un comercial que no es dueño de la entrega, **Then** no ve ni toca sus productos (mismas
   reglas de dueño que la entrega).

---

### User Story 3 - Pasar al catálogo (Priority: P2)

Si el producto sirve para otros clientes, un administrador pulsa **«Pasar al catálogo»**: se crea una
línea de negocio con sus datos y, desde ahí, sale para todo el equipo.

**Acceptance Scenarios**:

1. **Given** un administrador y un producto a medida, **When** pulsa «Pasar al catálogo», **Then** se crea
   una línea de negocio con su nombre, su texto como cobertura, su enlace como presentación y la primera
   imagen de su carrusel como foto, en todas las plantillas.
2. **Given** ese paso, **Then** en esa entrega el producto pasa a ser ese espacio del catálogo,
   personalizado con lo que ya tenía (su carrusel incluido).
3. **Given** que ya hay una línea con ese nombre, **Then** no se duplica: se avisa y no se crea nada.
4. **Given** un comercial, **Then** no ve «Pasar al catálogo».

---

### Edge Cases

- **Entrega sin guardar**: para añadir productos hay que guardarla antes (como para subir el carrusel).
- **Producto sin carrusel ni foto**: sale sin imagen, sin dejar una imagen rota (como una línea sin foto).
- **Nombre vacío**: no se guarda; el nombre es obligatorio. Texto y enlace, opcionales.
- **Enlace**: solo `http://` o `https://`, con la misma comprobación que el resto de enlaces.
- **Quitar un producto ya pasado al catálogo**: se quita de la entrega como cualquier espacio; la línea de
  negocio sigue en el catálogo.

## Requirements *(mandatory)*

- **FR-801**: La H MUST permitir añadir, solo a esa entrega, productos que no están en el catálogo, con
  nombre (obligatorio), una línea de texto, enlace a su presentación y carrusel.
- **FR-802**: El carrusel de un producto a medida MUST armarse con la misma galería que los demás espacios.
- **FR-803**: El correo H MUST mostrarlos con el mismo diseño que los demás espacios, después de los del
  catálogo; A–G y las demás entregas MUST NOT mostrarlos.
- **FR-804**: Como máximo 5 por entrega.
- **FR-805**: Se MUST guardar con la entrega y recuperarse al abrirla; las reglas de dueño de la entrega
  MUST aplicarse.
- **FR-806**: Se MUST poder editar y quitar.
- **FR-807**: Un administrador MUST poder pasarlo al catálogo, sin duplicar líneas por nombre; en esa
  entrega pasa a ser el espacio del catálogo, personalizado con lo que tenía.
- **FR-808**: Sin productos a medida, los correos MUST salir idénticos a los de hoy.

## Success Criteria *(mandatory)*

- **SC-801**: Un producto que no está en el catálogo llega al correo de la propuesta sin pedir a nadie que
  lo dé de alta.
- **SC-802**: Ninguna otra plantilla ni entrega lo muestra.
- **SC-803**: Pasar al catálogo deja la línea lista para todo el equipo en un clic.

## Assumptions

- Un producto a medida se guarda como un espacio más de la entrega (la tabla de espacios de la 004), con
  un identificador propio que no choca con los del catálogo.
- Sus imágenes van a su propia carpeta dentro de la entrega, como las de los espacios.
