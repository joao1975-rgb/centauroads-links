# Data Model: Espacios que acompañan, personalizados en la entrega

## Tabla nueva `entrega_espacios`

Una fila por espacio **personalizado** de una entrega. Un espacio estándar no tiene fila.

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | entero, PK | |
| `entrega_id` | entero, FK → `entregas.id`, índice | Obligatorio |
| `linea_id` | texto ≤ 60 | Id de `lineas_negocio`; tiene que existir al guardar |
| `canva_url` | texto ≤ 500, nulo | Nulo = el del catálogo. `http(s)://` con dominio (misma regla que la principal) |
| `nombre` | texto ≤ 120, nulo | Nulo = el del catálogo |
| `cobertura` | texto ≤ 200, nulo | Nulo = el del catálogo |
| `efecto` | texto ≤ 20, nulo | El del carrusel armado; uno de `carrusel.EFECTOS` |
| `paginas` | texto (JSON), nulo | `[{"orden", "ruta", "ancho", "alto", "aviso_precio"}]` de las elegidas |
| `created_at`, `updated_at` | fecha y hora UTC | |

Restricción: `UNIQUE(entrega_id, linea_id)`.

Un campo cuyo valor coincide con el del catálogo se guarda nulo (R8). Si una fila queda sin campos
propios y sin carrusel, se borra.

## Archivos en el volumen

```text
<DATA_DIR>/entregas/<id>/                     # principal (sin cambios)
<DATA_DIR>/entregas/<id>/espacios/<linea>/    # cada espacio: p0.jpg … p19.jpg, carrusel.gif
```

`<linea>` cumple `^[a-z0-9][a-z0-9-]{0,59}$` (los ids de `lineas_negocio`). Subir de nuevo las páginas
de un espacio vacía **solo** su subcarpeta.

## Salida de la entrega (`EntregaSalida`)

Campo nuevo `espacios`:

```json
[{ "linea": "mercedes", "canva_url": "https://…", "nombre": null, "cobertura": "…",
   "efecto": "barrido", "carrusel": "/media/entregas/7/espacios/mercedes/carrusel.gif?v=1a2b",
   "paginas": [{ "orden": 0, "url": "/media/…/p2.jpg?v=…", "aviso_precio": false }] }]
```

## Estado del compositor (`localStorage`)

En `bloques.entrega` (los rellena `normaliza()`; `CONTENT_VERSION` no cambia):

- `incluidos`: lista de ids de los espacios que acompañan esta entrega. Ausente → se toma de los
  servicios encendidos (lo que la H enseñaba hasta ahora).
- `espacios`: `{ "<linea>": { "canva", "nombre", "cobertura", "carrusel" } }`, solo con lo propio; el
  carrusel como dirección absoluta.

El motor aplica `espacios` e `incluidos` **solo** en la H y sobre una copia (R3).
