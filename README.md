# ⚡ CentauroADS Links

**Acortador de URLs, compositor de correos y entregas a medida de Centauro ADS.**
En producción en `https://links.centauroads.com`.

Tres piezas en un mismo servicio:

| Pieza | Para qué | Dónde |
|---|---|---|
| **Compositor de correos** | Arma los correos de servicios (plantillas A–H) para pegarlos en Gmail | `/panel` → entrar → compositor |
| **Entregas a medida** | La plantilla H: sube el PDF de Canva, genera el carrusel y un enlace propio con tarjeta de WhatsApp | Dentro del compositor |
| **Acortador** | Enlaces cortos con registro de clics | `/admin` y `/{slug}` |

El enlace para el equipo es **`https://links.centauroads.com/panel`**: pide el correo y después abre
el compositor. El compositor no se abre sin haber entrado.

---

## Requisitos

| Qué | Versión | Para qué |
|---|---|---|
| Git | cualquiera | bajar el repositorio |
| **Python** | **3.12** (sirve de 3.10 a 3.13) | la aplicación |
| Node.js | 18 o superior | solo para construir las plantillas y para parte de las pruebas |
| Docker | — | solo para desplegar |

> **No uses Python 3.14.** `pydantic==2.10.4` no tiene versión para 3.14 y la instalación falla al
> compilar. En Windows, si 3.14 es tu Python por defecto, usa `py -3.12` como en los pasos de abajo.
> El fichero `.python-version` fija 3.12 para las herramientas que lo leen.

No hace falta nada más: ni base de datos aparte (usa SQLite), ni ffmpeg, ni cuentas externas.

---

## Instalar y arrancar en un equipo nuevo

### 1. Bajar e instalar

```bash
git clone https://github.com/joao1975-rgb/centauroads-links.git
cd centauroads-links

# Windows (PowerShell o Git Bash)
py -3.12 -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt -r requirements-dev.txt

# macOS / Linux
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -r requirements-dev.txt
```

### 2. Configurar

Copia `.env.example` a `.env` y rellénalo. **`.env` no se sube nunca al repositorio.** Para
empezar en local bastan tres líneas:

```ini
PANEL_BOOTSTRAP=tu.correo@centauroads.com
SUPERADMIN_USER=arranque
SUPERADMIN_PASS=una-clave-larga-inventada-para-este-equipo
```

Todas las variables, con lo que hace cada una, están en [Variables de entorno](#variables-de-entorno).

### 3. Arrancar

```bash
# Windows
.venv\Scripts\python -m uvicorn app.main:app --env-file .env --port 8005
# macOS / Linux
.venv/bin/python -m uvicorn app.main:app --env-file .env --port 8005
```

`--env-file` carga el `.env` (viene con `uvicorn[standard]`, no hay que instalar nada más).
Comprueba que responde: `http://localhost:8005/health` → `{"status":"ok",...}`.

### 4. Primer acceso

`PANEL_BOOTSTRAP` da de alta tu correo como administrador, pero **sin contraseña**. La primera se la
pone la credencial de arranque (`SUPERADMIN_*`), una sola vez:

```bash
curl -X POST http://localhost:8005/api/panel/arranque/contrasena \
  -H "Content-Type: application/json" \
  -d '{"user":"arranque","password":"<SUPERADMIN_PASS>","email":"tu.correo@centauroads.com","nueva":"<tu contraseña, 12+ caracteres>"}'
```

```powershell
# Lo mismo en PowerShell
Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/panel/arranque/contrasena `
  -ContentType "application/json" `
  -Body '{"user":"arranque","password":"<SUPERADMIN_PASS>","email":"tu.correo@centauroads.com","nueva":"<tu contraseña>"}'
```

Responde `{"ok":true,...}`. Abre **`http://localhost:8005/panel`**, entra con tu correo y esa
contraseña, y llegas al compositor.

Para dar de alta al resto del equipo **todavía no hay pantalla**: lo hace un administrador con el API,
usando su propia sesión (o añadiendo correos a `PANEL_BOOTSTRAP` y repitiendo este paso):

```text
POST /api/panel/usuarios                    {"email": "nuevo@centauroads.com", "nombre": "Nombre"}
POST /api/panel/usuarios/{id}/contrasena    {"password": "<12+ caracteres>"}
```

Quien tenga Google no necesita contraseña si está configurado `GOOGLE_CLIENT_ID`.

> Si vas a entrar desde otro equipo de la red local por `http://192.168…` (sin HTTPS), añade
> `COOKIE_INSEGURA=1`: sin HTTPS el navegador no guarda la sesión. En `localhost` no hace falta.

### 5. Pruebas y plantillas

```bash
.venv\Scripts\python -m pytest            # Windows   (macOS/Linux: .venv/bin/python -m pytest)
node prototipos/mail/build.js             # construye las 16 plantillas y el compositor publicable
```

`build.js` tiene dos guardias: el contacto vigente en todos los correos, y que las plantillas no
cambien ni un byte sin querer. Si un cambio en una plantilla es deliberado:
`GOLDEN_UPDATE=1 node prototipos/mail/build.js`.

> En Windows, después de construir, git puede marcar `app/static/email/compositor.html` como
> modificado aunque el contenido sea idéntico: son los finales de línea. `.gitattributes` lo evita.

---

## Variables de entorno

Se definen en `.env` (local) o en EasyPanel (producción). Ninguna es un dato del código.

| Variable | Obligatoria | Qué hace |
|---|---|---|
| `SESSION_SECRET` | **En producción, sí** | Firma las sesiones del panel. Si falta, se genera una y se guarda en `data/session.key`: funciona mientras esa carpeta no se pierda. Defínela para no depender del disco |
| `PANEL_BOOTSTRAP` | Para el primer acceso | Correos separados por comas que entran como administradores. Sin nadie en la lista, **no entra nadie**. Es idempotente y no reactiva bajas |
| `SUPERADMIN_USER` / `SUPERADMIN_PASS` | Para el primer acceso | Credencial de arranque: pone la primera contraseña a alguien de la lista y cambia la clave del acortador. Sin ellas esas rutas responden 503. No es un usuario del panel |
| `ADMIN_KEY` | No | Clave del acortador (cabecera `X-Admin-Key`). Si falta, se genera una y se guarda en `data/admin.key` (nunca se escribe en el log) |
| `GOOGLE_CLIENT_ID` | No | Activa «Entrar con Google». Sin ella solo se entra con contraseña y el botón no se muestra |
| `CORS_ORIGINS` | No | Orígenes propios que pueden llamar a la API desde otro dominio, separados por comas. Vacío = ninguno (el panel se sirve desde el mismo dominio). Nunca `*` |
| `DATABASE_URL` | No | Por defecto `sqlite:///./data/centaurads_links.db`. Acepta PostgreSQL |
| `DATA_DIR` | No | Carpeta de datos de las entregas (PDF convertidos, carruseles). Por defecto `data` |
| `COOKIE_INSEGURA` | No | `1` permite la sesión sin HTTPS. Solo para probar en la red local; **nunca en producción** |
| `ADMIN_KEY_FILE` / `SESSION_SECRET_FILE` | No | Dónde se guardan las claves generadas. Por defecto `data/admin.key` y `data/session.key` |

Todo lo que genera la aplicación vive en **`data/`**: la base de datos, las dos claves generadas y
las entregas. En producción esa carpeta es un volumen persistente; perderla es perder todo.

---

## Direcciones

| Dirección | Qué es | Acceso |
|---|---|---|
| `/panel` | Pantalla de entrada (la que se comparte) | público |
| `/static/email/compositor.html` | El compositor | **con sesión**; sin ella lleva a `/panel/entrar` y vuelve |
| `/static/email/*.png`, `*.gif`, `*.jpg` | Imágenes de los correos | público (las cargan los clientes) |
| `/p/{slug}` | Enlace propio de una entrega: tarjeta para WhatsApp y robots, redirección a Canva para personas | público |
| `/admin` | Panel del acortador | clave `X-Admin-Key` |
| `/{slug}` | Enlace corto → destino | público |
| `/health` | Estado del servicio | público |

---

## Despliegue en EasyPanel (producción)

Servicio **`centauro-links`** en EasyPanel (DigitalOcean), dominio `links.centauroads.com`.

| Parámetro | Valor |
|---|---|
| Fuente | GitHub, rama `main` de este repositorio |
| Build | `Dockerfile` (Python 3.12) |
| Puerto | **8005**. La aplicación escucha también en el 8000, que usaba la configuración antigua del dominio |
| Volumen | montado en **`/app/data`** |
| Variables | las de la tabla de arriba; como mínimo `SESSION_SECRET`, `PANEL_BOOTSTRAP` y `SUPERADMIN_*` |

- **El repositorio es público.** Si se hace privado, EasyPanel falla con «Repository not found»
  hasta que se le da un token de GitHub de solo lectura en la configuración de la fuente del servicio.
- **Para verificar un despliegue**, no basta con `/health`: compara el fichero servido con el del
  commit (`git hash-object`), por ejemplo `/static/email/render.js?cb=<n>`.
- Con Docker en local: `docker compose up --build` y abre `http://localhost:8005/panel`.

## Copias de seguridad

`scripts/backup_sqlite.sh` hace copias en caliente de la base, cifradas y verificadas, a
DigitalOcean Spaces. Cómo configurarlo, restaurar y programarlo: [`scripts/BACKUP.md`](scripts/BACKUP.md).

---

## API del acortador

Los endpoints de `/api/links` requieren la clave en la cabecera `X-Admin-Key: <clave>` (solo la
cabecera: `?admin_key=` ya no se acepta porque quedaba en los logs y en el historial).

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/links` | Listar todos los enlaces |
| `POST` | `/api/links` | Crear enlace nuevo |
| `PUT` | `/api/links/{id}` | Actualizar enlace |
| `DELETE` | `/api/links/{id}` | Eliminar enlace |
| `GET` | `/api/links/{id}/stats` | Estadísticas de clics |

```bash
curl -X POST "http://localhost:8005/api/links" -H "X-Admin-Key: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "propuesta-fifa-2026",
    "target_url": "https://www.canva.com/design/DAHFJ8q9h9E/...",
    "name": "Propuesta FIFA World Cup 2026",
    "category": "propuesta"
  }'
```

Categorías: `propuesta`, `presentacion`, `video`, `portafolio`, `campaña`, `general`.

Por cada clic se registran IP, navegador, procedencia y fecha; se consultan en `/api/links/{id}/stats`.

---

## Seguridad

- **Panel de correos:** entrada con contraseña (argon2) o con Google, limitada a una lista de
  autorizados. Sesión en cookie firmada, solo HTTPS, 8 horas. Una baja corta el acceso al momento.
- **Acortador:** clave `X-Admin-Key`.
- Ningún secreto en el código ni en el repositorio: todo por variables de entorno. `gitleaks`
  revisa cada commit (`.gitleaks.toml`). En un clon nuevo el gancho no se activa solo:
  `git config core.hooksPath .githooks` (necesita [gitleaks](https://github.com/gitleaks/gitleaks) instalado).
- HTTPS lo pone EasyPanel (Let's Encrypt).

---

**Desarrollado para Centauro ADS**
