# Data Model: Textos de los perfiles

## Tabla nueva `textos_perfil`

Una fila por texto **cambiado**. Lo que no tiene fila es el de serie.

| Campo | Tipo | Reglas |
|---|---|---|
| `clave` | texto ≤ 80, PK | Una de las claves de `textos-perfil-serie.json` |
| `valor` | texto | No vacío tras quitar espacios; límite según la clave (research R6) |
| `actualizado_por` | texto | Correo de quien lo cambió |
| `actualizado_en` | fecha y hora UTC | |

## Textos de serie (`app/static/email/textos-perfil-serie.json`, generado por `build.js`)

```json
{ "textos": [
    { "clave": "agencia.titulo", "perfil": "agencia", "grupo": "Mensaje", "etiqueta": "Título",
      "valor": "Inventario disponible", "limite": 120 },
    { "clave": "general.asunto.curiosidad", "perfil": "general", "grupo": "Asuntos", "etiqueta": "Curiosidad",
      "valor": "👀 120.000 personas al día pasan por esta pantalla", "limite": 150 },
    { "clave": "nuevo.ruta.2.titulo", "perfil": "nuevo", "grupo": "Ruta de tres pasos", "etiqueta": "Paso 2 · título",
      "valor": "Que te recuerden", "limite": 200 } ] }
```

## Lo que recibe el motor (`ponTextos`)

`{ "<clave>": "<valor cambiado>" }`: solo los cambiados. Una clave que el motor no conoce se ignora.
