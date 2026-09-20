# Implementation Plan: Módulo de mails de servicios

**Branch**: `001-modulo-mails` | **Date**: 2026-09-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-modulo-mails/spec.md`

## Summary

Llevar el compositor de correos al panel que el equipo ya usa, con identidad por persona, enlaces
por destinatario y aviso de interés. Se construye **dentro** de la aplicación FastAPI existente,
como el paquete `app/mails/`, reutilizando su base de datos y su volumen persistente.

La decisión técnica que gobierna todo lo demás: **el motor de contenido se porta de JavaScript a
Jinja2**, que ya es una dependencia declarada del proyecto. El servidor renderiza y el navegador
solo muestra, de modo que la vista previa es literalmente el correo que se enviará.

## Technical Context

**Language/Version**: Python 3.11 (el del contenedor actual)

**Primary Dependencies**: ya presentes — FastAPI 0.115.6, SQLAlchemy 2.0.36, Pydantic 2.10.4,
**Jinja2 3.1.5**, uvicorn, python-multipart. A añadir por etapa, ver "Dependencias nuevas".

**Storage**: SQLite sobre el volumen persistente `links-data` → `/app/data` (el mismo que ya usa
el acortador). Sin base de datos nueva ni servicio adicional.

**Testing**: pytest. La pieza central es una batería de **ficheros golden**: los ocho
`plantilla-*.html` que hoy genera `render.js` son la referencia contra la que se compara la
salida del motor portado.

**Target Platform**: contenedor Linux en EasyPanel, tras HTTPS, sirviendo `links.centauroads.com`.

**Project Type**: servicio web con panel administrativo servido por el propio backend.

**Performance Goals**: no es un sistema de alto volumen. Renderizar un correo debe tardar menos de
300 ms para que la vista previa se sienta inmediata al cambiar un interruptor.

**Constraints**: el correo generado debe respetar las restricciones de HTML de correo de la
constitución (tablas, CSS inline, 600 px, sin JavaScript). El módulo no puede degradar el tiempo
de respuesta del acortador, que es la ruta caliente.

**Scale/Scope**: decenas de correos por semana, ~10 usuarios de panel, 2 cuentas remitentes, 6
espacios publicitarios, 4 formatos × 4 perfiles.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Puerta | Cómo se comprueba | Estado |
|---|--------|-------------------|--------|
| I | **El acortador no se toca** | Ninguna ruta existente cambia ni se retira; solo se añaden rutas bajo `/admin/mails` y `/api/mails`. El esquema se toca **solo de forma aditiva**: una columna nullable en `clicks` y varias nullable en `deliveries`. Prueba obligatoria antes de desplegar: abrir una copia de la BD de producción con el código nuevo y verificar enlaces, clics y rutas. | **PASA con condición** — la prueba de migración es tarea bloqueante, no opcional. |
| II | **Un solo motor de contenido** | Se porta `render.js` a Jinja2 y se **retira** el motor JS del camino de producción; no quedan dos implementaciones vivas. El catálogo, los perfiles y los textos salen a ficheros de datos, un único lugar editable (FR-011). | **PASA** |
| III | **Verificado renderizado** | El plan incluye vista previa a 600 px y a ~375 px servida por el propio motor, comparación golden contra la salida actual, y revisión con imágenes bloqueadas antes de dar por buena la historia 1. | **PASA** |
| IV | **Nada sin confirmar** | Los precios viven como dato opcional por espacio; sin tarifa confirmada el motor emite "a cotizar" (FR-010). El muro de marcas cliente nace apagado. | **PASA** |
| V | **Repositorio público** | Ningún secreto en el código: credenciales de Google, clave de sesión y clave de cifrado de tokens van por entorno, validadas al arrancar. Los tokens de los buzones se guardan **cifrados** en el volumen, nunca en el repositorio. | **PASA** |

Restricciones de correo HTML que el diseño respeta: tablas anidadas, CSS inline, 600 px, sin
JavaScript, imágenes con URL pública absoluta desde `app/static/email/`, y el conector MCP de
Gmail NO se usa para enviar.

## Phase 0: Investigación y decisiones

### D1 — El motor de contenido: portar a Jinja2 *(la decisión que ordena el resto)*

El contenido vive hoy en `render.js`, JavaScript. La aplicación es Python. La constitución prohíbe
tener dos motores. Tres caminos:

| Opción | Qué implica | Veredicto |
|---|---|---|
| **A. Portar a Jinja2** | Un solo runtime. Jinja2 **ya está en `requirements.txt`**, así que no añade dependencias. La vista previa pasa a servirla el servidor. | **ELEGIDA** |
| B. Ejecutar `render.js` con Node en el contenedor | Conserva el motor tal cual, pero mete un segundo runtime en la imagen, un subproceso por render y más superficie de despliegue, para un proyecto que ya tiene Jinja2 esperando. | Rechazada |
| C. Mantener ambos, cada uno donde le toca | Dos implementaciones del mismo contenido que divergen a la primera corrección. Es exactamente lo que el Principio II prohíbe, y ya nos mordió antes con las copias desactualizadas. | Prohibida |

**Cómo se hace sin romper nada**: los ocho `plantilla-*.html` que `render.js` genera hoy son la
**referencia**. El puerto es correcto cuando produce HTML equivalente para los mismos datos de
entrada. La comparación se automatiza normalizando espacios en blanco, para que el test falle por
diferencias reales de estructura o contenido, no por formato.

**Qué pasa con el prototipo**: `prototipos/mail/` queda como herramienta de diseño y como fuente
de los ficheros golden. Deja de ser el camino de producción en cuanto la Historia 1 esté en pie.

### D2 — La vista previa la sirve el servidor

El navegador no renderiza el correo: lo pide al servidor y lo muestra en un iframe. Así la vista
previa **es** el correo, no una aproximación, que es justo lo que exige el escenario de aceptación
1 de la Historia 1. Cada cambio de interruptor es una petición; a menos de 300 ms se siente
instantáneo y evita duplicar lógica en el cliente.

### D3 — Datos: extender lo que hay, sin romperlo

`Delivery` **ya existe** en `app/models.py`, con `link_id`, `channel` (que ya contempla `'email'`)
y `delivered_at`. No se crea una tabla paralela: se le añaden columnas **nullable**. `Click` recibe
una única columna nullable, `contact_token`, que es lo que permite atribuir una apertura.

Las tablas nuevas (`contacts`, `panel_users`, `sender_accounts`, `alerts`) no tocan las
existentes. Detalle completo en [data-model.md](./data-model.md).

**Migración**: SQLite admite `ALTER TABLE ADD COLUMN` de forma segura para columnas nullable. Se
hace con una función idempotente al arrancar, que comprueba qué columnas faltan y las añade.
*Trade-off aceptado*: no se introduce Alembic todavía. Para dos `ALTER TABLE` aditivos, una
dependencia de migraciones es más maquinaria de la que el problema pide. Si el esquema crece,
se adopta Alembic y esta función se convierte en la migración inicial.

### D4 — Identidad: Google del dominio, con contraseña propia como excepción

Decidido con el cliente. El dominio `centauroads.com` está en Google Workspace (verificado por sus
registros MX), así que el camino principal es Google Sign-In restringido al dominio: sin
contraseñas que guardar, altas y bajas desde el admin de Google. La vía de usuario y contraseña
existe como excepción, con hash irreversible.

Esto **retira la clave única compartida** que hay hoy, que es el pendiente de seguridad que el
proyecto arrastra. La clave actual se conserva durante una ventana de transición como acceso de
emergencia, y se elimina al cerrar la Historia 1.

### D5 — La respuesta en hilo se aplaza a la etapa 2

La Historia 4 exige autorización sobre buzones reales y toca correo de clientes. Se construye
cuando las historias 1 a 3 estén en producción y asentadas. El modo "solo borrador" es el estado
inicial y no se discute.

### Dependencias nuevas

**Etapa 1** (historias 1 a 3):

- `itsdangerous` — cookies de sesión firmadas (lo usa el `SessionMiddleware` de Starlette).
- `google-auth` — verificar el identificador que devuelve Google Sign-In.
- `argon2-cffi` — hash de las contraseñas de los usuarios de excepción.
- `httpx` — cliente HTTP para hablar con Google.
- `pytest` + `pytest-asyncio` — pruebas (solo desarrollo).

**Etapa 2** (historia 4), no se instalan todavía:

- `google-api-python-client`, `google-auth-oauthlib` — acceso a los buzones.
- `cryptography` — cifrado de los tokens en reposo.

## Project Structure

### Documentation (this feature)

```text
specs/001-modulo-mails/
├── plan.md              # Este fichero
├── spec.md              # Especificación
├── data-model.md        # Modelo de datos (Phase 1)
├── quickstart.md        # Cómo levantarlo en local (Phase 1)
├── checklists/
│   └── requirements.md  # Validación de la especificación
└── tasks.md             # Lo genera /speckit-tasks
```

### Source Code (repository root)

```text
app/
├── main.py                    # EXISTENTE — solo se le añade el montaje del router de mails
├── models.py                  # EXISTENTE — se extiende de forma aditiva
├── database.py                # EXISTENTE — sin cambios
├── schemas.py                 # EXISTENTE — sin cambios
├── auth/                      # NUEVO — identidad del panel (sustituye la clave única)
│   ├── __init__.py
│   ├── google.py              # verificación de Google Sign-In, restringida al dominio
│   ├── local.py               # usuarios de excepción, hash argon2
│   ├── sesion.py              # cookie firmada, caducidad
│   └── dependencias.py        # dependencias FastAPI: usuario actual, permisos
├── mails/                     # NUEVO — el módulo
│   ├── __init__.py
│   ├── rutas.py               # /admin/mails (panel) y /api/mails (datos)
│   ├── motor.py               # el render: estado + perfil + formato -> HTML
│   ├── contenido.py           # carga y valida los ficheros de datos
│   ├── enlaces.py             # enlaces por destinatario (/slug?c=<token>)
│   ├── alertas.py             # regla de las 3 aperturas en 48 h
│   ├── datos/                 # EL único lugar editable del contenido
│   │   ├── catalogo.yaml      # espacios publicitarios y sus fichas
│   │   ├── perfiles.yaml      # los cuatro perfiles de cliente
│   │   └── marca.yaml         # datos de contacto, firma, slogan
│   ├── plantillas/            # Jinja2, una por formato + parciales compartidos
│   │   ├── base.html
│   │   ├── formato_a.html
│   │   ├── formato_b.html
│   │   ├── formato_c.html
│   │   ├── formato_d.html
│   │   └── bloques/           # marca, servicios, tabla, escalera, puente, firma
│   └── panel/                 # la interfaz del compositor
│       ├── compositor.html
│       └── estatico/
└── static/email/              # EXISTENTE — imágenes que ya sirve producción

tests/
├── golden/                    # los plantilla-*.html de referencia
├── test_motor.py              # el puerto produce HTML equivalente al de referencia
├── test_migracion.py          # una BD del código viejo se abre intacta con el nuevo
├── test_acortador.py          # las rutas existentes siguen respondiendo igual
├── test_enlaces.py            # atribución de aperturas por contacto
└── test_alertas.py            # 3 en 48 h genera un aviso, no tres
```

**Structure Decision**: un solo proyecto, el que ya existe. El módulo entra como paquete
`app/mails/` dentro de la aplicación FastAPI actual, y la identidad sale a `app/auth/` porque la
necesita todo el panel, no solo los correos. No se crea ni frontend separado ni servicio nuevo:
la constitución exige convivir con el acortador, y levantar otra pieza sería contradecirlo.

## Orden de construcción

1. **Cimientos** — identidad del panel (`app/auth/`), migración aditiva y su prueba, andamiaje de
   pruebas con los ficheros golden. Bloquea todo lo demás.
2. **Historia 1 (P1)** — motor portado, contenido a datos, compositor en el panel, copiar correo.
   Es el MVP: en cuanto esto esté, el equipo ya no depende del portátil de nadie.
3. **Historia 2 (P2)** — enlaces por destinatario, `Click.contact_token`, registro consultable.
4. **Historia 3 (P3)** — regla de las tres aperturas y aviso interno.
5. **Historia 4 (P4)** — etapa 2: autorización de buzones y borrador en el hilo.

Cada historia se despliega por su cuenta y deja el sistema utilizable.

## Complexity Tracking

> Solo lo que se aparta del camino simple y por qué.

| Desviación | Por qué hace falta | Alternativa más simple, y por qué se rechaza |
|-----------|--------------------|-----------------------------------------------|
| Portar el motor de JS a Python en vez de reutilizar el que ya funciona | El Principio II prohíbe dos motores, y meter Node en la imagen para conservar el de JS cuesta más a largo plazo que portarlo una vez | Dejar `render.js` y llamarlo por subproceso: dos runtimes en el contenedor, imagen más pesada y un punto de fallo nuevo en cada render |
| Dos vías de autenticación (Google y contraseña propia) | Decisión explícita del cliente: no todo el mundo tendrá cuenta del dominio | Solo Google: más simple, pero deja fuera a quien no tenga cuenta `@centauroads.com` |
| Migración idempotente escrita a mano en vez de Alembic | Son dos `ALTER TABLE` aditivos sobre SQLite; una herramienta de migraciones es más maquinaria de la que el problema pide hoy | Alembic desde el principio: correcto a medio plazo, pero añade dependencia y ceremonia para un cambio que cabe en veinte líneas verificables |
