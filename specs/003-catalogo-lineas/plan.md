# Implementation Plan: Catálogo de líneas de negocio

**Branch**: `003-catalogo-lineas` | **Date**: 2026-10-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-catalogo-lineas/spec.md`

## Summary

Las cinco líneas de negocio viven hoy en constantes de `render.js` (`SERVICIOS`, `GRUPOS`, `FICHA`,
`BANCO`) y `normaliza()` descarta todo lo que no esté en `SERVICIOS`. El plan convierte ese catálogo
en datos del servidor, administrados desde una pantalla nueva del panel (`/panel/lineas`), sin
duplicar el motor:

1. **Servidor**: dos tablas nuevas (`lineas_negocio`, `familias_d`), sembradas al arrancar con el
   catálogo de serie que exporta el propio `render.js` (una sola fuente). API de lectura para el
   compositor y de administración para los administradores, más subida de foto al volumen persistente.
2. **Motor**: `render.js` gana `ponCatalogo(datos)`, que sustituye en sitio el catálogo de serie por el
   del servidor; un filtro por plantilla en `render()`; filas genéricas en la tabla de agencias y en el
   inventario de la E para las líneas con ficha; familias dinámicas en la D; y fotos con dirección
   absoluta. Sin catálogo del servidor, el motor se comporta exactamente como hoy (byte a byte).
3. **Compositor**: al abrirse con servidor pide `/api/catalogo` y lo inyecta antes de pintar; marca las
   líneas que no se usan en la plantilla elegida; enlaza la pantalla nueva.

## Technical Context

**Language/Version**: Python 3.12 (FastAPI 0.115, SQLAlchemy 2.0, Pydantic 2.10) y JavaScript ES2019
en el navegador y en Node 18+ (motor `render.js`, sin dependencias)

**Primary Dependencies**: FastAPI, SQLAlchemy, Pillow 12 (ya instalado, se usa en las entregas)

**Storage**: SQLite en el volumen `links-data` → `/app/data` (tablas nuevas, creadas por
`create_all`); fotos en `/app/data/lineas/`

**Testing**: pytest (API, permisos, siembra, migración, subida) + guiones Node desde pytest (motor:
matriz plantilla × perfil, tablas, familias, migración del estado) + guardia byte a byte de `build.js`
(16 correos de referencia) + verificación visual en navegador a 600 y 375 px

**Target Platform**: contenedor Docker en EasyPanel (DigitalOcean), detrás de Traefik;
mails.centauroads.com

**Project Type**: aplicación web (API + páginas del panel generadas en el servidor + motor JS)

**Performance Goals**: el catálogo cabe en una respuesta pequeña (< 20 KB para 50 líneas); el
compositor lo pide una vez al abrirse

**Constraints**: correos HTML con tablas e inline (constitución); el acortador no se toca; migración
solo aditiva; sin cambiar ningún correo mientras el catálogo no cambie

**Scale/Scope**: decenas de líneas, un puñado de administradores

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple el plan | Estado |
|---|---|---|
| **I. El acortador no se toca** | Solo se añaden tablas, rutas (`/api/catalogo`, `/api/panel/lineas…`, `/panel/lineas`, `/media/lineas/…`) y una carpeta en el volumen. Ninguna ruta existente cambia. `create_all` crea tablas nuevas sin tocar las existentes. Prueba: el acortador redirige igual antes y después. | ✅ |
| **II. Un solo motor de contenido** | El catálogo de serie sigue definido **solo** en `render.js`; `build.js` lo exporta a JSON y el servidor se siembra de ese JSON. El HTML sigue generándose en el motor. El estado guardado se **migra** en `normaliza()` (líneas nuevas entran, retiradas salen, lo escrito a mano se conserva); `CONTENT_VERSION` no se sube. | ✅ |
| **III. Verificado renderizado** | Matriz automática 8 plantillas × 4 perfiles con una línea nueva; correos de referencia idénticos byte a byte con el catálogo de serie; revisión visual a 600 y 375 px de A, D, E y H con una línea nueva. | ✅ |
| **IV. Nada que no esté confirmado** | Una línea nueva nace sin ficha ni precio; las tablas solo le dan fila si alguien escribe su ficha; el precio solo sale con el modo de precios encendido. El sistema no inventa datos. | ✅ |
| **V. El repositorio es público** | Sin secretos nuevos. Las fotos subidas viven en el volumen, no en el repositorio. Cada push lo decide el propietario. | ✅ |
| **Puertas** | Spec → plan → tareas antes de código (este documento). Guardia de contenido y guardia byte a byte de `build.js` intactas. Nota de Obsidian actualizada al terminar. | ✅ |

Re-evaluación tras el diseño (Fase 1): sin cambios; ninguna violación que justificar.

## Project Structure

### Documentation (this feature)

```text
specs/003-catalogo-lineas/
├── plan.md              # Este archivo
├── research.md          # Fase 0: decisiones y alternativas
├── data-model.md        # Fase 1: tablas y forma del catálogo
├── quickstart.md        # Fase 1: recorrido de verificación
├── contracts/
│   └── api.md           # Fase 1: rutas nuevas
├── checklists/
│   └── requirements.md  # Calidad de la especificación
└── tasks.md             # Fase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
app/
├── models.py                      # + LineaNegocio, FamiliaD
├── main.py                        # + monta el router del catálogo; siembra al arrancar
├── mails/
│   └── catalogo/                  # NUEVO módulo
│       ├── __init__.py
│       ├── siembra.py             # siembra desde app/static/email/catalogo-serie.json
│       ├── fotos.py               # validar, reducir y guardar fotos en /app/data/lineas
│       ├── rutas.py               # /api/catalogo, /api/panel/lineas…, /media/lineas/…
│       └── pantalla.py            # /panel/lineas (HTML como equipo.py)
└── static/email/
    └── catalogo-serie.json        # GENERADO por build.js desde render.js

prototipos/mail/
├── render.js                      # + ponCatalogo, filtro por plantilla, filas genéricas, familias, fotos absolutas
├── compositor.html                # + carga /api/catalogo, marca «no se usa aquí», enlace a Líneas de negocio
└── build.js                       # + exporta catalogo-serie.json

tests/
├── test_catalogo_api.py           # permisos, validación, siembra, retirar/devolver, orden, subida
├── test_catalogo_motor.py         # matriz plantilla × perfil, tablas, familias, migración del estado
└── test_catalogo_pantalla.py      # /panel/lineas: acceso, contexto, sin innerHTML
```

**Structure Decision**: la capacidad vive en `app/mails/catalogo/`, junto a `app/mails/entregas/`,
porque es contenido del módulo de correos y comparte su almacenamiento persistente. La pantalla sigue
el patrón de `app/auth/equipo.py` (HTML en el servidor, datos por API, texto con `textContent`).

## Complexity Tracking

Sin violaciones de la constitución que justificar.
