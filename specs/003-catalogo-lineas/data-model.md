# Data Model: Catálogo de líneas de negocio

## Tabla `lineas_negocio`

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | texto, PK | Identificador estable (FR-307). Las cinco de serie conservan el suyo (`vallas`, `led`, `mercedes`, `totem`, `rider`). Las nuevas: derivado del nombre (minúsculas, sin acentos, guiones), único, no cambia al renombrar. |
| `nombre` | texto ≤ 120 | Obligatorio y único (sin distinguir mayúsculas). |
| `eyebrow` | texto ≤ 60 | Etiqueta corta. |
| `cta` | texto ≤ 60 | Texto del botón propio (opcional). |
| `cobertura` | texto ≤ 200 | Cobertura o ubicación. |
| `nota` | texto ≤ 300 | Opcional. |
| `canva` | texto ≤ 500 | Enlace de la presentación; `http(s)://`. |
| `slug` | texto ≤ 80 | Del acortador, para el enlace propio (como hoy). |
| `img` | texto ≤ 500 | Archivo de serie (`svc_x.jpg`) o dirección absoluta de una foto subida. |
| `alt` | texto ≤ 200 | Texto alternativo; obligatorio si hay foto. |
| `cover`, `alt_cover` | texto | Portada opcional para el juego de portadas. |
| `ficha_ubic`, `ficha_medida`, `ficha_trafico`, `ficha_desde` | texto ≤ 120 | Ficha técnica opcional (FR-305). Hay ficha si al menos ubicación, medidas o tráfico tienen valor. |
| `familia_id` | texto, FK → `familias_d.id`, nulo | Familia de la D (FR-306). |
| `plantillas` | texto ≤ 8 | Letras A–H incluidas; por defecto `ABCDEFGH` (FR-308). |
| `orden` | entero | Posición en el catálogo. |
| `activa` | booleano | `false` = retirada (FR-319). |
| `actualizado_por` | texto | Correo de quien la cambió. |
| `actualizado_en` | fecha y hora UTC | |

## Tabla `familias_d`

| Campo | Tipo | Reglas |
|---|---|---|
| `id` | texto, PK | `vallas`, `dooh`, `movil` de serie; nuevas derivadas del título. |
| `titulo` | texto ≤ 120 | Obligatorio. |
| `eyebrow` | texto ≤ 60 | |
| `orden` | entero | |

## Forma que recibe el motor (`ponCatalogo`)

```json
{
  "lineas": [
    { "id": "led", "nombre": "Pantalla LED Chacao", "eyebrow": "Digital outdoor", "cta": "Consultar disponibilidad",
      "cobertura": "…", "nota": "…", "slug": "pantallas-led", "canva": "https://canva.link/…",
      "img": "svc_led.jpg", "alt": "…", "cover": "cover_led.jpg", "altCover": "…",
      "ficha": { "ubic": "…", "medida": "1024 × 2048 px", "trafico": "…", "desde": "1.500" },
      "familia": "dooh", "plantillas": "ABCDEFGH" }
  ],
  "familias": [ { "id": "dooh", "eyebrow": "Digital outdoor", "titulo": "Pantallas LED y Tótem (DOOH)" } ]
}
```

Solo líneas activas, en su orden. Las fotos subidas llegan como dirección absoluta.

## Estado guardado del compositor (`localStorage`)

Sin cambio de forma. `normaliza()` ya hace lo necesario contra el catálogo vigente: quita las líneas
que no están, añade las nuevas en su posición y actualiza los textos de catálogo que siguen con el
valor anterior. Con `ponCatalogo` llamado antes, "el catálogo vigente" es el del servidor.

## Transiciones

`activa` → retirada (`activa=false`) → devuelta (`activa=true`). Nunca se borra una fila.
