# ⚡ CentauroADS Links

**Acortador de URLs corporativo para Centauro ADS**

Servicio standalone que convierte URLs largos (Canva, YouTube, etc.) en enlaces
cortos y personalizados bajo el dominio `centaurads`, con panel de administración
y tracking de clics.

---

## Ejemplo de uso

| Antes (URL original) | Después (URL corto) |
|---|---|
| `https://www.canva.com/design/DAHFJ8q9h9E/_6WxpJ7-9juUUmeHATZkjg/view?utm_content=...` | `https://centaurads.XXXX.easypanel.host/propuesta-fifa-2026` |

---

## Stack técnico

| Componente | Tecnología |
|---|---|
| Backend | Python 3.12 + FastAPI |
| Base de datos | SQLite (incluido) — opción PostgreSQL |
| Frontend admin | HTML/CSS/JS vanilla (sin dependencias) |
| Deploy | Docker → Easypanel → DigitalOcean |

---

## Estructura del proyecto

```
centaurads-links/
├── app/
│   ├── __init__.py
│   ├── main.py          # App FastAPI (rutas, API, redirect)
│   ├── models.py         # Modelos SQLAlchemy (Link, Click)
│   ├── schemas.py        # Schemas Pydantic (validación)
│   ├── database.py       # Config de base de datos
│   ├── templates/
│   │   └── admin.html    # Panel de administración
│   └── static/           # Assets estáticos (vacío por ahora)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Despliegue en Easypanel

### 1. Crear proyecto nuevo en Easypanel

1. En el dashboard de Easypanel, crear un **nuevo proyecto**: `centaurads-links`
2. Dentro del proyecto, añadir un **servicio tipo "App"**
3. Fuente: **GitHub** (subir este repo) o **Docker Image** (build manual)

### 2. Configuración del servicio

| Parámetro | Valor |
|---|---|
| **Build** | Dockerfile (ya incluido) |
| **Puerto expuesto** | `8000` |
| **Dominio** | `centaurads.XXXXX.easypanel.host` |
| **Variables de entorno** | Ver sección siguiente |

### 3. Variables de entorno (configurar en Easypanel)

```
ADMIN_KEY=<clave_segura_para_admin>
DATABASE_URL=sqlite:///./data/centaurads_links.db
```

> ⚠️ **IMPORTANTE**: Cambiar `ADMIN_KEY` a una clave segura en producción.

### 4. Volumen persistente

Para que la base de datos SQLite sobreviva reinicios del contenedor:

- Crear un **volumen** en Easypanel
- Mount path: `/app/data`

### 5. Dominio personalizado

Para obtener el subdominio `centaurads`:

- En Easypanel → Servicio → **Domains**
- El dominio automático será: `centaurads-links-centaurads-links.XXXXX.easypanel.host`
- Se puede configurar un **dominio custom** si se dispone de uno (ej: `links.centaurads.com`)

---

## Desarrollo local

```bash
# Clonar
git clone <repo-url>
cd centaurads-links

# Con Docker
docker compose up --build

# Sin Docker
pip install -r requirements.txt
ADMIN_KEY=centauro2026 uvicorn app.main:app --reload --port 8000
```

Abrir: `http://localhost:8000/admin`

---

## API Reference

Todos los endpoints de API requieren `?admin_key=<clave>` como query parameter.

### Endpoints públicos

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/{slug}` | Redirige al URL destino (302) |
| `GET` | `/health` | Health check |
| `GET` | `/admin` | Panel de administración |

### Endpoints API (protegidos)

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/links` | Listar todos los enlaces |
| `POST` | `/api/links` | Crear enlace nuevo |
| `PUT` | `/api/links/{id}` | Actualizar enlace |
| `DELETE` | `/api/links/{id}` | Eliminar enlace |
| `GET` | `/api/links/{id}/stats` | Estadísticas de clics |

### Ejemplo: Crear enlace

```bash
curl -X POST "http://localhost:8000/api/links?admin_key=centauro2026" \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "propuesta-fifa-2026",
    "target_url": "https://www.canva.com/design/DAHFJ8q9h9E/...",
    "name": "Propuesta FIFA World Cup 2026",
    "description": "Deck de venta para agencias - campaña abril-julio",
    "category": "propuesta"
  }'
```

### Categorías disponibles

| Valor | Uso |
|---|---|
| `propuesta` | Propuestas comerciales |
| `presentacion` | Presentaciones / decks |
| `video` | Videos / reels |
| `portafolio` | Portafolio / showcase |
| `campaña` | Campañas activas |
| `general` | Otros enlaces |

---

## Datos que se capturan por clic

Cada vez que alguien accede a un enlace corto, se registra:

- IP del visitante
- User-Agent (navegador/dispositivo)
- Referer (de dónde viene)
- Timestamp exacto

Estos datos se pueden consultar desde el endpoint `/api/links/{id}/stats`.

---

## Seguridad

- El panel admin está protegido por `ADMIN_KEY` (variable de entorno)
- No se usa sesión ni cookies — la clave se envía en cada request
- Para mayor seguridad en producción, considerar:
  - Usar HTTPS (Easypanel lo configura automáticamente con Let's Encrypt)
  - Cambiar la clave admin regularmente
  - Restringir acceso al `/admin` por IP si es necesario

---

## Próximas mejoras sugeridas

- [ ] Autenticación con JWT en lugar de clave simple
- [ ] Dashboard de analytics con gráficos
- [ ] Expiración automática de enlaces
- [ ] QR code generado automáticamente para cada enlace
- [ ] Integración con el sistema QR Tracking existente
- [ ] Dominio personalizado corto (ej: `cads.link`)

---

**Desarrollado para Centauro ADS** | Proyecto Antigravity
