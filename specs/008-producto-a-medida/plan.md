# Implementation Plan: Producto a medida en la entrega (H)

**Branch**: `008-producto-a-medida` | **Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)

## Summary

Un producto a medida es **una fila más de `entrega_espacios`** (la tabla de la 004) con un identificador
que el catálogo no puede producir. El servidor lo crea, lo edita, le arma el carrusel con la galería de
siempre y lo borra; un administrador lo puede pasar al catálogo. El motor lo añade al final de los
espacios de la H, con la misma tarjeta. Sin productos a medida, nada cambia.

## Technical Context

**Language/Version**: Python 3.12 (FastAPI, SQLAlchemy) y JavaScript ES2019 (motor `render.js`, compositor).

**Storage**: sin tabla ni columna nuevas. Imágenes en `<DATA_DIR>/entregas/<id>/espacios/<id-producto>/`,
como las de cualquier espacio.

**Testing**: pytest (API), guiones Node desde pytest (motor), guardia byte a byte de `build.js`, demo en
navegador a 600 y 375 px.

**Constraints**: `CONTENT_VERSION` no se sube; los 16 correos de referencia, idénticos; mismas reglas de
dueño que la entrega.

## Constitution Check

| Principio | Cómo lo cumple | Estado |
|---|---|---|
| I. El acortador no se toca | Solo entregas, catálogo (alta desde la entrega), motor y compositor. | ✅ |
| II. Un solo motor de contenido | El producto se pinta con la tarjeta de espacio que ya existe en `render.js`. | ✅ |
| III. Verificado renderizado | Demo en navegador: H con productos, A–G sin ellos, 600 y 375 px. | ✅ |
| IV. Nada inventado | El producto lleva solo lo que escribe quien redacta; el alt de la foto del catálogo es su nombre. | ✅ |
| V. Repositorio público | Sin secretos. | ✅ |

## Diseño por pieza

### Identificador

`medida--` + 12 hexadecimales al azar (`secrets.token_hex(6)`). El doble guion no lo puede producir
`_id_desde` del catálogo (colapsa los guiones) ni está en la siembra, así que nunca choca con una línea.
Cumple la forma de `almacen.linea_valida`, así que carpetas, rutas de `/media` y la galería lo aceptan sin
cambios. Al azar y no correlativo: un producto quitado deja sus imágenes en disco para los correos ya
enviados (FR-414 de la 004), y otro nuevo no puede pisarlas reusando el número.

`es_a_medida(linea)` en `espacios.py` lo reconoce por el prefijo.

### API (`app/mails/entregas/espacios.py`)

- **`POST /api/entregas/{id}/espacios`** — alta. Cuerpo `{nombre, cobertura?, canva_url?}`. Nombre
  obligatorio (1–120), cobertura ≤ 200, enlace con `valida_enlace`. Con 5 ya en la entrega → 409 «Como
  mucho 5 productos a medida por entrega». Responde 201 con la entrega (`EntregaSalida`).
  `# ponytail:` dos altas simultáneas pueden dejar 6; un tope estricto pediría bloquear la entrega.
- **`_espacio(db, entrega, linea)`** sustituye a `_catalogo` en subir, elegir, guardar y borrar: si es a
  medida, la fila tiene que existir **en esa entrega** (404 si no); si no, el catálogo, como hoy.
- **`PUT .../espacios/{linea}`** con un producto a medida: escribe los campos tal cual (no hay catálogo
  con el que comparar, R8 no aplica); nombre vacío → 400; la fila no se borra nunca por quedar «sin nada
  propio».
- **`DELETE .../espacios/{linea}`** con un producto a medida = quitarlo: borra la fila. Las imágenes se
  quedan en disco, como las de cualquier espacio.
- **`POST .../espacios/{linea}/catalogo`** — pasar al catálogo, `solo_admin`.
  1. 400 si no es a medida. Valida con `_valida` del catálogo (409 si ya hay una línea con ese nombre:
     no se crea nada).
  2. Crea la línea: nombre, cobertura, enlace, todas las plantillas, al final del orden, con
     `_id_desde`. Foto: la primera página elegida del carrusel, por `fotos.prepara` y `fotos.guarda`, con
     el nombre como texto alternativo; sin carrusel, sin foto.
  3. Copia la carpeta del producto a la del espacio nuevo (`shutil.copytree`); la vieja se queda para los
     correos ya enviados.
  4. La fila pasa a la línea nueva: textos nulos (= los del catálogo, R8), carrusel y efecto
     conservados, `paginas` con las rutas nuevas. El id se añade a `entrega.servicios`, para que el
     espacio siga incluido.
  5. Un solo `commit` al final; si la copia o la foto fallan, no queda ni la línea ni el cambio.
  Responde `{"linea": <id>, "entrega": EntregaSalida}`.
- **Salida**: `_espacio_a_salida` añade `"a_medida": true|false`. El orden ya es por `id` de fila, así
  que los productos salen en el orden en que se añadieron.

### Motor (`prototipos/mail/render.js`)

- Estado: `bloques.entrega.aMedida = [{ id, nombre, cobertura, canva, carrusel }]`, en orden.
- `espaciosDeLaEntrega` (solo H, sobre una copia) los añade **al final** de `servicios`, encendidos, con
  `carruselPropio` = su carrusel, `alt` = su nombre y sin foto de serie. Uno sin nombre no sale.
- Un espacio **sin enlace** no pinta «Ver presentación» ni envuelve la foto en un enlace vacío
  (`fotoServicio`, `textoComplemento`). Todas las líneas de referencia tienen enlace: los 16 correos no
  cambian.
- Texto plano de la H: las partes vacías no dejan « — » colgando. WhatsApp no lista espacios: sin cambio.
- A–G no llaman a `espaciosDeLaEntrega`: no pueden verlos.

### Compositor (`prototipos/mail/compositor.html`)

- En «Espacios que la acompañan», tras los del catálogo, cada producto a medida con su ficha: nombre,
  línea de texto, enlace (guardado con espera, como los espacios), su galería (la misma, con su ruta),
  **«Quitar»** (pide confirmación) y **«Pasar al catálogo»** solo si `/api/auth/yo` dice `rol: admin`.
- **«+ Añadir otro producto»**: pide el nombre y lo crea en el servidor. Sin entrega guardada, dice que
  hay que guardarla antes; con 5, se desactiva y dice por qué.
- `abreEntrega` rellena `aMedida` con los espacios `a_medida` de la entrega; los demás siguen yendo a
  `espacios`, como hoy.
- Tras «Pasar al catálogo»: vuelve a pedir `/api/catalogo` (`ponCatalogo`), quita el producto de
  `aMedida`, añade la línea a `incluidos` y su carrusel a `espacios`, y rehace el panel.

## Pruebas

- **API** (`tests/test_entregas_a_medida.py`): alta y nombre obligatorio; tope de 5; enlace inválido;
  editar; quitar (fila fuera, imágenes en disco); subir y armar su carrusel; un id a medida de **otra**
  entrega da 404; un comercial que no es dueño no lo toca; pasar al catálogo (línea creada con sus datos y
  foto, carpeta copiada, fila convertida, incluido en `servicios`); nombre duplicado → 409 sin crear
  nada; un comercial → 403; pasar un espacio del catálogo → 400.
- **Motor** (`tests/test_a_medida_motor.py`): la H lo pinta después de los del catálogo, con su carrusel,
  texto y enlace; sin enlace, sin «Ver presentación»; sin nombre, no sale; A–G y el estado sin
  `aMedida`, idénticos; texto plano sin « — » sueltos.
- **Guardia**: `build.js` sigue dando 16 idénticas.
- **Demo en navegador**: añadir, subir PDF, quitar y pasar al catálogo; H a 600 y 375 px sin desborde;
  cero errores de consola.
