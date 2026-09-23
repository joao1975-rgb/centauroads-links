# Modelo de datos: Entrega a medida

**Fecha**: 2026-09-22 | **Plan**: [plan.md](./plan.md)

Misma regla que en la 001: **lo que ya existe no se modifica, solo se amplía**. Esta etapa no
añade ni una columna a las tablas existentes. Solo crea dos tablas nuevas y usa las que ya están.

## Lo que ya existe y se usa tal cual

| Tabla | Qué aporta a las entregas | Qué le pasa |
|---|---|---|
| `links` | Cada entrega crea una fila aquí, con destino el enlace de Canva del cliente. Así el acortador, sus clics y sus estadísticas sirven a la entrega sin cambiar nada. | **Intacta** |
| `clicks` | Las aperturas de la entrega, con `contact_token` para atribuirlas | **Intacta** |
| `contacts` | A quién va la entrega. Aquí es **obligatorio** | **Intacta** |
| `panel_users` | Quién la armó, y la lista de cuentas autorizadas a entrar | **Intacta** |
| `sender_accounts` | La cuenta remitente y su firma | **Intacta** |
| `sender_permissions` | Quién puede usar qué cuenta | **Intacta** |
| `alerts` | El aviso de interés repetido, ya con su clave única antiduplicados | **Intacta** |
| `deliveries` | Registro de reparto por canal; una entrega copiada para WhatsApp o para correo puede anotarse aquí | **Intacta** |

Nada de esto exige `ALTER TABLE`. `app/migracion.py` sigue como está; las dos tablas nuevas las
crea `Base.metadata.create_all`, que es aditivo por definición.

## Tablas nuevas

### `entregas` — una presentación propia entregada a un cliente

| Columna | Tipo | Nulo | Para qué |
|---|---|---|---|
| `id` | `Integer` | No | PK |
| `link_id` | `Integer`, FK → `links.id`, indexado | **No** | El enlace del acortador que lleva a la presentación. Es lo que hace que clics, estadísticas y avisos funcionen sin código nuevo |
| `contact_id` | `Integer`, FK → `contacts.id`, indexado | **No** | A quién se le entrega. **Obligatorio por decisión del propietario**: sin contacto no hay seguimiento ni aviso (FR-102) |
| `titulo` | `String(200)` | No | Lo que se ve en la tarjeta de WhatsApp y en el asunto sugerido |
| `canva_url` | `String(500)` | No | El enlace de la presentación del cliente. Duplicado con `links.target_url` a propósito: el acortador puede cambiar su destino y la entrega debe conservar el original |
| `texto` | `Text` | No | El texto de entrega, ya editado por la persona. Nace del texto por defecto del motor |
| `servicios` | `Text` | No | Qué servicios del catálogo la acompañan, como lista de identificadores separados por comas (`"led,mercedes"`). Vacío es legítimo: ninguno |
| `sender_account_id` | `Integer`, FK → `sender_accounts.id` | Sí | Desde qué cuenta se va a enviar. Nulo mientras la entrega es borrador |
| `firma_cargo` | `String(200)` | Sí | Alianzas Comerciales / Directora, según elija quien firme |
| `panel_user_id` | `Integer`, FK → `panel_users.id`, indexado | **No** | Quién la armó |
| `estado` | `String(20)` | No | `borrador` o `entregada`. Por defecto `borrador` |
| `entregada_en` | `DateTime` UTC | Sí | Cuándo se marcó como entregada. Nulo mientras sea borrador |
| `created_at` | `DateTime` UTC | No | `datetime.now(timezone.utc)`, igual que el resto |
| `updated_at` | `DateTime` UTC | No | Se toca en cada guardado |

Ejemplo, con valores sintéticos:

```text
id=7  link_id=142  contact_id=31  titulo="Propuesta Cafetería Ejemplo · Q4"
canva_url="https://www.canva.com/design/DAExxxxxxx/view"
texto="Ana, aquí tienes la propuesta que armamos para ustedes…"
servicios="led,mercedes"  sender_account_id=2  firma_cargo="Alianzas Comerciales"
panel_user_id=3  estado="entregada"  entregada_en=2026-09-22T14:05:00Z
```

**Por qué `estado` y no borrar**: una entrega a medio armar es trabajo de alguien. Se guarda como
borrador y se recupera; no se pierde porque se cerró la pestaña.

### `entrega_paginas` — cada imagen sacada de la presentación

| Columna | Tipo | Nulo | Para qué |
|---|---|---|---|
| `id` | `Integer` | No | PK |
| `entrega_id` | `Integer`, FK → `entregas.id`, indexado | **No** | A qué entrega pertenece. Con borrado en cascada: sin la entrega, sus imágenes no significan nada |
| `orden` | `Integer` | No | Posición dentro del carrusel, desde 0. El 0 es el fotograma que ve Outlook |
| `ruta` | `String(300)` | No | Ruta **relativa** dentro del volumen: `entregas/7/p0.jpg`. Relativa a propósito: mover el volumen no debe invalidar las filas |
| `ancho` | `Integer` | No | Píxeles |
| `alto` | `Integer` | No | Píxeles |
| `origen` | `String(20)` | No | `pdf`, `imagen` o `claude`. Sirve para saber de dónde salió cuando algo se ve raro |
| `pagina_pdf` | `Integer` | Sí | Número de página en el PDF original, si vino de ahí. Nulo para imágenes sueltas |
| `rotulo` | `String(200)` | Sí | El nombre leído del texto de la página ("Ficha técnica – Pantalla Chacao"), para la miniatura |
| `aviso_precio` | `Boolean` | No | Verdadero si el texto de la página contiene algo que parece un precio. Por defecto falso |
| `created_at` | `DateTime` UTC | No | |

Ejemplo, con valores sintéticos:

```text
id=19  entrega_id=7  orden=0  ruta="entregas/7/p0.jpg"  ancho=1200  alto=675
origen="pdf"  pagina_pdf=1  rotulo="Portada – Propuesta"  aviso_precio=false
```

**Restricción**: `UNIQUE(entrega_id, orden)`. Dos imágenes no pueden ocupar el mismo sitio del
carrusel; que lo rechace la base de datos, no la memoria de quien programa.

**Límite**: entre 2 y 4 filas por entrega (FR-110). Lo valida la aplicación, porque SQLite no
sabe expresar "entre 2 y 4 hijos" sin un disparador que complicaría la migración.

## Ficheros, que no son base de datos

| Qué | Dónde | Por qué ahí |
|---|---|---|
| Páginas de la entrega | `/app/data/entregas/<id>/p<n>.jpg` | En el **volumen**: son datos de cliente, tienen que sobrevivir a los despliegues y no pueden entrar al repositorio público |
| Carrusel | `/app/data/entregas/<id>/carrusel.gif` | Igual |
| Portada para la tarjeta de WhatsApp | `/app/data/entregas/<id>/og.jpg` | Igual. Es la página 0 recortada a 1200×630 |
| PDF original | **No se guarda** | Se rasteriza y se descarta. Guardarlo sería conservar el material completo del cliente sin que nadie lo haya pedido |

Se sirven por la ruta `/media/entregas/<id>/<fichero>`, que lee del volumen. `app/static/` no
vale: lo que hay ahí va al repositorio y se reemplaza en cada despliegue.

`.gitignore` debe cubrir `data/` para que ninguna imagen de cliente acabe en un repositorio
público por descuido.

## Lo que NO va a la base de datos

- **El PDF original.** Se rasteriza y se descarta.
- **Credenciales de Claude.** La vía de "Pedírselo a Claude" es de cada persona, en su navegador;
  el servidor solo prepara el texto de la instrucción.
- **Credenciales de envío.** No hay envío en esta versión, y los avisos los reparte n8n con las
  suyas.
- **La URL del webhook de n8n.** Va por variable de entorno, no en tabla ni en código.

## La migración

No hay migración, en el sentido de `ALTER TABLE`: las dos tablas son nuevas y `create_all` las
crea si faltan. Aun así, la puerta de despliegue del principio I sigue siendo obligatoria:

1. Copiar la base de datos de producción.
2. Abrirla con el código nuevo.
3. Comprobar que los enlaces existentes siguen resolviendo, que los clics siguen ahí y que
   `/health` responde 200.
4. Comprobar que el código **anterior** también puede abrir la base de datos ya tocada: ignora las
   tablas que no conoce, de modo que volver atrás sigue siendo posible.

Ese cuarto punto es lo que hace la operación reversible, que es lo que la constitución exige.
