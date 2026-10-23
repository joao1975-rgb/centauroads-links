# Feature Specification: Usar las imágenes de Vallas en la propuesta (H)

**Feature Branch**: `011-imagenes-vallas`

**Created**: 2026-10-23

**Status**: Draft

**Input**: Petición de la propietaria (2026-10-23): «quiero crear una opción que me permita utilizar las
mismas imágenes insertas en la opción vallas, para una presentación en específico».

Decisiones (preguntas, 2026-10-23): las imágenes van **como imágenes de la propuesta** (el carrusel
principal de la entrega H, paso 03), y la opción es **solo para Vallas**.

## Contexto

Hoy las imágenes de la propuesta salen solo de un PDF o de imágenes que se suben desde el ordenador. Si la
propuesta es de vallas y no hay un PDF propio, no hay forma de usar las fotos que la app ya tiene de Vallas.

Las fotos de Vallas que la app ya conoce (comprobadas en producción, 110–155 KB cada una):
- la foto del catálogo (`img` de la línea `vallas`: `svc_vallas.jpg` o la que se haya subido en Líneas de
  negocio);
- las del banco de fotos (`svc_vallas.jpg`, `svc_vallas_alt.jpg`, `svc_vallas_alt2.jpg`) y las que se hayan
  añadido como extra en el banco;
- la portada de su presentación de Canva (`cover_vallas.jpg`).

## User Scenarios & Testing

### US1 — Las fotos de Vallas como imágenes de la propuesta (P1)

En el paso 03 de la entrega H, junto a «Suelta aquí el PDF», un botón **«Usar las imágenes de Vallas»**.
Al pulsarlo, las fotos de Vallas aparecen como miniaturas elegibles, exactamente como si se hubieran
subido a mano; se eligen de 2 a 4, en el orden deseado, y se arma el carrusel de la propuesta (y su
portada de WhatsApp) con el efecto elegido.

**Independent Test**: en una entrega guardada sin imágenes, pulsar el botón → aparecen 4 miniaturas (foto
del catálogo, dos alternativas y portada, sin repetidas) → elegir 2 → «Carrusel listo» y el correo H muestra
el carrusel.

**Acceptance**:
1. Sin entrega guardada, el botón dice que hay que guardarla antes (como la subida de un PDF).
2. Si la propuesta ya tiene imágenes, pide confirmación antes de reemplazarlas; si se cancela, no cambia nada.
3. Una foto repetida en varias fuentes sale una sola vez.
4. Si la línea Vallas no está en el catálogo o una foto no se puede descargar, se dice cuál falló y se usan
   las demás; si no queda ninguna, no se toca nada.
5. Las plantillas A–G y los espacios que acompañan no cambian.

## Requirements

- **FR-1101**: En el paso 03 de la H MUST existir «Usar las imágenes de Vallas».
- **FR-1102**: El botón MUST subir las fotos de Vallas por la misma vía que una subida manual
  (`POST /api/entregas/{id}/paginas`), en este orden: foto del catálogo, banco, extras, portada; sin repetidas.
- **FR-1103**: MUST pedir confirmación si ya hay imágenes en la propuesta.
- **FR-1104**: El servidor y los 16 correos de referencia MUST NOT cambiar.

## Plan técnico

- **Solo compositor** (`prototipos/mail/compositor.html`):
  - `fotosDeVallas()`: arma la lista con `M.SERVICIOS` (`vallas`: `img`, `cover`) y `M.bancoDe(st, sv)`
    (`fotos`, `extra`); resuelve cada nombre con la base de imágenes (`st.assetBase`, en producción `.`) o
    la deja tal cual si ya es una dirección (`/media/...`, `https://...`); quita repetidas.
  - La galería (`galeria(op)`) acepta un botón opcional `op.desde = { texto, ficheros }`: al pulsarlo,
    confirma si `op.hayCarrusel()`, descarga las fotos como `File` y llama a su `sube(ficheros)` interno, el
    mismo del arrastre. Solo la galería de la propuesta principal (paso 03) lo pasa.
- Las fotos son del mismo dominio: no hay problema de CORS ni de tamaño (4 × ~150 KB, lejos del límite).

## Tasks

- [x] T1101 Prueba del compositor: el paso 03 de la H ofrece «Usar las imágenes de Vallas» solo en la galería principal; `fotosDeVallas()` sin repetidas y en orden — `tests/test_imagenes_vallas.py`
- [x] T1102 `fotosDeVallas()` y el botón `op.desde` de la galería — `prototipos/mail/compositor.html`
- [x] T1103 Demo en navegador: entrega guardada → botón → 4 miniaturas → elegir 2 → carrusel en el correo; confirmación al reemplazar; 0 errores de consola; capturas
- [x] T1104 Suite, build (16 idénticas), README y Obsidian

## Ajuste tras probarla en producción (2026-10-23)

La propietaria vio dos fallos:
1. El botón traía siempre las fotos estándar, no las páginas subidas al espacio Vallas de **esa** entrega.
2. «No toma los efectos»: al abrir una entrega guardada las galerías empezaban vacías (sin páginas
   elegidas), así que cambiar el efecto solo decía «Efecto guardado» y no rehacía el carrusel; y tras
   el botón, las miniaturas quedaban sin elegir.

- **FR-1105**: si el espacio Vallas de la entrega tiene páginas, el botón usa esas; si no, las estándar.
- **FR-1106**: al abrir una entrega vuelven a su galería las páginas elegidas (propuesta, espacios y
  productos a medida), en su orden y con su efecto: cambiar el efecto rehace el carrusel.
- **FR-1107**: el botón deja el carrusel armado con todas las imágenes (hasta 4); se pueden quitar o reordenar.

- [x] T1105 Pruebas — `tests/test_imagenes_vallas.py`
- [x] T1106 `fotosDeVallas()` primero el espacio; `restaura()` al abrir; el botón elige y arma; «Volver al estándar» vacía la galería del espacio — `prototipos/mail/compositor.html`
- [x] T1107 Demo: subir 3 a Vallas, elegir 2, reabrir → 2 elegidas, «persiana» rehace; botón → 2 miniaturas y carrusel armado; «fundido» lo cambia; 0 errores
