# Implementation Plan: Textos de los perfiles, editables por el equipo

**Branch**: `005-textos-perfiles` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-textos-perfiles/spec.md`

## Summary

Los ~62 textos fijos de los perfiles pasan a ser un **catálogo de textos con clave estable**
(`agencia.titulo`, `general.asunto.curiosidad`, `nuevo.ruta.2.objetivo`…). Los de serie siguen en el
motor (`render.js`), que es la única fuente; `build.js` los exporta a `textos-perfil-serie.json`. El
servidor guarda **solo los cambios** (tabla `textos_perfil`); un administrador los edita en la pantalla
**Textos de los perfiles** (`/panel/textos`); el compositor los pide al abrirse y el motor los aplica,
igual que el catálogo de líneas de la 003 (`ponCatalogo`).

## Technical Context

**Language/Version**: Python 3.12 (FastAPI 0.115, SQLAlchemy 2.0, Pydantic 2) y JavaScript ES2019

**Primary Dependencies**: las de siempre; ninguna nueva.

**Storage**: SQLite en `/app/data`; tabla nueva `textos_perfil` (la crea `create_all`; no hay columnas
nuevas en tablas existentes, así que `migracion.py` no cambia).

**Testing**: pytest (API, permisos, validación) + guiones Node desde pytest (motor: un texto cambiado sale
en los correos de su perfil y en ningún otro; marcadores) + guardia byte a byte de `build.js` + demo en
navegador (pantalla y compositor de otra sesión, sin errores de consola).

**Target Platform**: contenedor Docker en EasyPanel; navegador del equipo; correos pegados en Gmail.

**Project Type**: aplicación web (API + pantalla del panel + motor JS compartido)

**Performance Goals**: los cambios caben en una respuesta pequeña (< 15 KB); el compositor no espera
por ellos para pintar.

**Constraints**: correos con tablas e inline; textos siempre escapados; `CONTENT_VERSION` no se sube; los
16 correos de referencia idénticos sin cambios.

**Scale/Scope**: 4 perfiles, ~62 textos, un puñado de administradores.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple el plan | Estado |
|---|---|---|
| **I. El acortador no se toca** | Solo una tabla y rutas nuevas (`/api/textos-perfil`, `/api/panel/textos…`, `/panel/textos`). | ✅ |
| **II. Un solo motor de contenido** | Los textos de serie viven solo en `render.js`; el servidor guarda diferencias. El HTML lo sigue generando el motor. | ✅ |
| **III. Verificado renderizado** | Matriz del motor (cada texto cambiado sale en su perfil y en ningún otro), guardia byte a byte, demo a 600 y 375 px. | ✅ |
| **IV. Nada que no esté confirmado** | No se inventa texto: lo que no se cambia es el de serie; un texto vacío no se guarda. | ✅ |
| **V. El repositorio es público** | Sin secretos nuevos; los textos son mensaje comercial, no datos personales. | ✅ |
| **Puertas** | Spec → plan → tareas antes de código; guardias de `build.js`; nota de Obsidian. | ✅ |

Re-evaluación tras el diseño (Fase 1): sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/005-textos-perfiles/
├── plan.md  research.md  data-model.md  quickstart.md  contracts/api.md  tasks.md
```

### Source Code (repository root)

```text
app/
├── models.py                       # + TextoPerfil
├── main.py                         # registra el router nuevo
└── mails/textos/                   # NUEVO: __init__.py, rutas.py (API) y pantalla.py (/panel/textos)
prototipos/mail/
├── render.js                       # TEXTOS de serie con clave; textosActuales(); ponTextos()
├── build.js                        # exporta app/static/email/textos-perfil-serie.json
└── compositor.html                 # pide /api/textos-perfil y llama a ponTextos; enlace en el menú
tests/
├── test_textos_motor.py            # NUEVO
├── test_textos_api.py              # NUEVO
└── test_textos_pantalla.py         # NUEVO
```

**Structure Decision**: módulo propio `app/mails/textos/`, hermano de `catalogo/`, con el mismo patrón
(API + pantalla del panel): es la misma idea, datos del negocio que el motor trae de serie y el equipo
ajusta.

## Complexity Tracking

Sin desviaciones de la constitución que justificar.
