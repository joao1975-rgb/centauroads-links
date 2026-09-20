# Modelo de datos: Módulo de mails de servicios

**Fecha**: 2026-09-19 | **Plan**: [plan.md](./plan.md)

Regla que gobierna este documento: **lo que ya existe no se modifica, solo se amplía**. Ninguna
columna existente cambia de tipo, de nombre ni de obligatoriedad, y ninguna columna nueva es
`NOT NULL`. Así una base de datos escrita por el código anterior sigue abriéndose con el nuevo
(Principio I de la constitución).

## Lo que ya existe (`app/models.py`)

| Tabla | Para qué sirve hoy | Qué le pasa |
|---|---|---|
| `links` | Los enlaces cortos del acortador y su contador | **Intacta** |
| `deliveries` | Registro de por qué canal se repartió un enlace; `channel` ya contempla `'email'` | **Se amplía** con columnas nullable |
| `clicks` | Cada apertura de un enlace, con IP, user-agent y referente | **Se amplía** con una columna nullable |

## Ampliaciones sobre tablas existentes

### `clicks` — una sola columna

| Columna | Tipo | Nulo | Para qué |
|---|---|---|---|
| `contact_token` | `String(64)`, indexado | **Sí** | El distintivo que viajaba en el enlace (`/slug?c=<token>`). Es lo que convierte una apertura anónima en una apertura atribuible. |

Nulo significa apertura anónima: alguien entró por el enlace genérico. Es un caso legítimo, no un
error, y así lo debe presentar el registro.

### `deliveries` — cinco columnas, todas nullable

| Columna | Tipo | Para qué |
|---|---|---|
| `contact_id` | `Integer`, FK → `contacts.id` | A quién se le mandó |
| `perfil` | `String(30)` | Qué perfil de cliente se usó (general, agencia, nuevo, phygital) |
| `formato` | `String(2)` | Qué formato (A, B, C, D) |
| `sender_account_id` | `Integer`, FK → `sender_accounts.id` | Desde qué cuenta salió |
| `panel_user_id` | `Integer`, FK → `panel_users.id` | Quién lo armó |

Las filas que ya existan quedan con estas columnas vacías, que es la verdad: se repartieron antes
de que hubiera manera de registrar esos datos.

## Tablas nuevas

### `contacts` — a quién escribimos

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `Integer` | PK |
| `nombre` | `String(200)` | |
| `email` | `String(200)`, indexado | |
| `empresa` | `String(200)` | Opcional |
| `origen` | `String(50)` | whatsapp, instagram, correo, evento, llamada |
| `token` | `String(64)`, único, indexado | El que viaja en sus enlaces; es lo que casa con `clicks.contact_token` |
| `notas` | `Text` | |
| `created_at` | `DateTime` UTC | Mismo criterio que el resto: `datetime.now(timezone.utc)` |

### `panel_users` — quién entra al panel

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `Integer` | PK |
| `email` | `String(200)`, único, indexado | Identidad. Si acaba en `@centauroads.com` puede entrar por Google |
| `nombre` | `String(200)` | |
| `rol` | `String(30)` | `admin` o `comercial` |
| `password_hash` | `String(255)`, nullable | Solo para los usuarios de excepción (FR-001b). Vacío = entra por Google |
| `activo` | `Boolean` | Retirar el acceso es ponerlo a falso, no borrar la fila: la bitácora debe seguir señalando a alguien |
| `created_at`, `last_login_at` | `DateTime` UTC | |

### `sender_accounts` — desde qué buzones sale correo

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `Integer` | PK |
| `email` | `String(200)`, único | `equintero@` o `mercadeo@` en v1 |
| `etiqueta` | `String(100)` | Cómo se llama en el panel |
| `tipo` | `String(20)` | `personal` o `compartida` — es lo que implementa FR-004a |
| `firma_nombre`, `firma_cargo` | `String(200)` | La firma cambia con la cuenta |
| `activa` | `Boolean` | |
| `token_ref` | `String(200)`, nullable | Etapa 2: **referencia** al token cifrado en disco, nunca el token |

### `sender_permissions` — quién puede usar qué cuenta

Tabla de unión entre `panel_users` y `sender_accounts`. Una cuenta `personal` solo admite el
permiso de su titular; una `compartida` admite varios. Esa regla se valida al conceder el permiso,
no solo al enviar.

| Columna | Tipo |
|---|---|
| `id` | `Integer` PK |
| `panel_user_id` | FK → `panel_users.id` |
| `sender_account_id` | FK → `sender_accounts.id` |

### `alerts` — el aviso de interés

| Columna | Tipo | Notas |
|---|---|---|
| `id` | `Integer` | PK |
| `contact_id` | FK → `contacts.id` | |
| `link_id` | FK → `links.id` | Qué presentación miró |
| `motivo` | `String(50)` | `interes_repetido` en v1 |
| `conteo` | `Integer` | Cuántas aperturas lo dispararon |
| `ventana_inicio`, `ventana_fin` | `DateTime` UTC | El tramo que se contó |
| `created_at` | `DateTime` UTC | |
| `visto_por` | FK → `panel_users.id`, nullable | Quién lo atendió |

**La clave para no duplicar avisos** (FR-015): índice único sobre
`(contact_id, link_id, ventana_inicio)`. La ventana se calcula redondeada, de modo que las
aperturas siguientes dentro del mismo tramo caen en la misma clave y el insert se rechaza solo,
sin depender de que el código se acuerde de comprobarlo.

## Lo que NO va a la base de datos

El catálogo de espacios, los perfiles y los datos de marca viven en ficheros de datos
(`app/mails/datos/*.yaml`), no en tablas. Razón: son contenido, cambian por decisión editorial y no
por operación del sistema, y tenerlos en ficheros los hace revisables en el control de versiones —
se ve quién cambió un precio y cuándo. Esto satisface FR-011: **un único lugar editable**.

## La migración

Una función idempotente que corre al arrancar:

1. Mira qué columnas tienen realmente `clicks` y `deliveries`.
2. Añade con `ALTER TABLE ADD COLUMN` solo las que falten (todas nullable, operación segura en
   SQLite y que no reescribe la tabla).
3. Crea las tablas nuevas si no están.
4. No borra, no renombra y no cambia ningún tipo. Nunca.

**Prueba que la valida, y que es bloqueante**: se toma una base de datos creada por el código
actual con enlaces y clics dentro, se abre con el código nuevo, y se comprueba que los enlaces
siguen resolviendo, que los contadores no cambiaron y que los clics anteriores siguen ahí. Si esa
prueba no pasa, no se despliega.

**Reversión**: como todo lo añadido es opcional, el código anterior vuelve a arrancar sobre la base
de datos migrada sin tocar nada — ignora las columnas que no conoce. Eso hace la migración
reversible en la práctica, que es lo que la constitución exige.
