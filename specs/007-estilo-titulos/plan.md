# Implementation Plan: Estilo de los títulos (tipografía y tamaño)

**Branch**: `007-estilo-titulos` | **Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)

## Summary

Dos elecciones nuevas en el estado del compositor —`tipografia` (centauro · impacto · editorial ·
moderna) y `tamTitulo` (base · grande · maximo)— que el motor aplica al renderizar. Sin ellas, el motor
hace exactamente lo de hoy. En la H se guardan también con la entrega.

## Technical Context

**Language/Version**: JavaScript ES2019 (motor `render.js`, compositor) y Python 3.12 (FastAPI) para
guardar la elección con la entrega.

**Storage**: dos columnas opcionales en `entregas` (`tipografia`, `tam_titulo`), por `COLUMNAS_NUEVAS`.

**Testing**: guiones Node desde pytest (motor), pytest (API de entregas), guardia byte a byte de
`build.js`, demo en navegador midiendo desbordes a 600 y 375 px.

**Constraints**: correos con tablas y estilos en línea, sin fuentes web ni media queries; `CONTENT_VERSION`
no se sube; los 16 correos de referencia, idénticos sin elección.

## Constitution Check

| Principio | Cómo lo cumple | Estado |
|---|---|---|
| I. El acortador no se toca | Solo motor, compositor y dos columnas de `entregas`. | ✅ |
| II. Un solo motor de contenido | Las parejas y el ajuste viven en `render.js`; el compositor solo elige. | ✅ |
| III. Verificado renderizado | Matriz plantilla × pareja × tamaño a 600 y 375 px en navegador real. | ✅ |
| IV. Nada inventado | No hay textos nuevos de negocio. | ✅ |
| V. Repositorio público | Sin secretos. | ✅ |

## Diseño por pieza

### Motor (`prototipos/mail/render.js`)

- **`PAREJAS`**: por pareja, la pila de título, la de texto y si el título va en mayúsculas o itálica.
  `centauro` no define nada: se quedan las tipografías de hoy.

  | Pareja | Título | Texto | Título principal |
  |---|---|---|---|
  | impacto | `Impact, Haettenschweiler, 'Arial Narrow Bold', sans-serif` | `Georgia, 'Times New Roman', serif` | mayúsculas |
  | editorial | `Georgia, 'Times New Roman', serif` | `Arial, Helvetica, sans-serif` | negrita itálica |
  | moderna | `'Arial Black', 'Arial Bold', Gadget, sans-serif` | `Verdana, Geneva, sans-serif` | — |

- **Cómo se aplica la pareja**: las tres pilas de hoy (`FH` títulos, `FS` rótulos condensados, `FB`
  texto) pasan de `const` a `let`. `render()` las cambia según la pareja al empezar y las devuelve al
  terminar (`try/finally`); el motor es síncrono, así que no hay mezcla entre correos. Todo lo que hoy usa
  esas pilas cambia a la vez, sin tocar cada plantilla.
- **`tamanoTitulo(st, base, texto)`** → `{ px, base, ajustado }`. Base ×1 / ×1,25 / ×1,5. Con Grande o
  Máximo: la palabra más larga × ancho medio de carácter de esa tipografía (en em, con margen) no puede
  pasar de 327 px; si pasa, se baja hasta que quepa, nunca por debajo del base. Se exporta para que el
  compositor pueda avisar.
- **Dónde se usa**: los títulos principales de A (54), B (48), D (46), E (40), F (36), G (40) y H (34)
  piden su tamaño a `tamanoTitulo` y su estilo (mayúsculas o itálica) a la pareja. La C no tiene título
  grande.
- **Texto plano y WhatsApp**: no pasan por aquí; no cambian.

### Compositor (`prototipos/mail/compositor.html`)

- Grupo **«Estilo del título»** con dos selectores (Tipografía, Tamaño): en A–G, justo antes de los
  bloques del mensaje; en la H, en el paso 01, debajo del título de la propuesta.
- Si `tamanoTitulo` dice `ajustado`, un aviso junto al selector: «Máximo se ajustó a 62 px para que quepa
  en el móvil».

### Servidor (H)

- `app/models.py`: `Entrega.tipografia` (String 20) y `Entrega.tam_titulo` (String 10), opcionales.
- `app/migracion.py`: las dos columnas en `COLUMNAS_NUEVAS["entregas"]`.
- `app/mails/entregas/rutas.py`: los campos en la entrada y la salida, validados contra los valores
  permitidos (400 si no); un PUT sin ellos no los borra.
- Compositor: `guardaEntrega` los envía; `abreEntrega` los restaura.

## Riesgos

- **Anchos de carácter estimados**: si el cálculo se queda corto, una palabra podría desbordar en el
  móvil. Se calibra midiendo en navegador real la palabra más larga de prueba en cada pareja, con margen
  de seguridad, y la demo comprueba 0 px de desborde.
- **Fuentes que faltan** (Impact no está en algunos Android): la pila cae en su respaldo
  (Haettenschweiler, Arial Narrow Bold); el ajuste usa el ancho de la más ancha de la pila.
