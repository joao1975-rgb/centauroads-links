# Research: Textos de los perfiles, editables por el equipo

## R1 — Una sola fuente para los textos de serie

**Decisión**: los textos de serie siguen en `render.js`; `build.js` los exporta a
`app/static/email/textos-perfil-serie.json`. El servidor valida las claves y muestra el de serie desde
ese JSON.

**Por qué**: es el patrón de la 003 (`catalogo-serie.json`), que ya funciona; una copia de los textos en
Python acabaría distinta de la del motor.

## R2 — Guardar solo los cambios

**Decisión**: la tabla `textos_perfil` tiene una fila por texto **cambiado**. Volver al de serie es
borrar la fila; guardar un texto igual al de serie, también.

**Por qué**: un texto de serie mejorado en el motor llega solo a quien no lo había cambiado, y
«cambiado / de serie» sale de un único criterio (FR-506).

## R3 — Claves estables

| Grupo | Clave | Cuántos |
|---|---|---|
| Mensaje del perfil | `<perfil>.<campo>` — asunto, preheader, titulo, sub, intro, cierre, cta | 4 × 7 |
| Asuntos | `<perfil>.asunto.<directo\|beneficio\|curiosidad>` | 4 × 3 |
| Ruta (cliente nuevo) | `nuevo.ruta.<1-3>.<titulo\|formato\|objetivo\|resuelve>` | 12 |
| Puente (phygital) | `phygital.puente.<1-3>.<titulo\|texto>` y `phygital.puente.nota` | 7 |
| Tabla (agencias) | `agencia.tabla.<espacio\|medidas\|trafico>` | 3 |

La clave no cambia aunque cambie el texto. La etiqueta de cada asunto (Directo, Beneficio, Curiosidad) no
se edita (FR-502).

## R4 — Cómo los aplica el motor

**Decisión**: los textos de la ruta, el puente y la tabla salen de las funciones y pasan a constantes
(`RUTA`, `PUENTE`, `TABLA_CAB`) con el mismo contenido. `ponTextos(cambios)` guarda los cambios y los
aplica sobre una copia de los de serie: `PERFILES`, `ASUNTOS` y esas constantes. Sin llamarla, el motor
queda exactamente igual (guardia byte a byte).

**Por qué**: todos los sitios que ya leen esas constantes (render, texto plano, WhatsApp, el selector de
asuntos del compositor) reciben los textos nuevos sin tocarlos uno a uno. Se guarda la copia de serie
para que `ponTextos({})` devuelva el motor a su estado original (volver al de serie sin recargar).

**Lo que no hace falta migrar**: los textos del perfil no viven en el estado guardado del compositor;
`aplicaPerfil` los toma de `PERFILES` en cada render. FR-512 se cumple sin tocar `normaliza`.

## R5 — Marcadores

Hoy la entrada del perfil pasa por `fill()` (`{destinatario}`, `{empresa}`). Se comprueba campo a campo
cuáles lo hacen y se extiende a los que falten de asunto, texto previo, título, subtítulo, entrada,
cierre y botón, con prueba (FR-509). Los textos de bloque (ruta, puente, tabla) no llevan marcadores.

## R6 — Límites

Asunto 150, texto previo 200, título y subtítulo 120, entrada y cierre 600, botón 60, textos de bloque
200 (cabeceras de tabla 30). Vacío no se guarda (FR-505). Los límites viajan en el JSON de serie.

## R7 — Si el servidor no responde

El compositor sigue con los de serie y muestra un aviso discreto (FR-513), como ya hace con el catálogo.
