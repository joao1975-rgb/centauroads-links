# Implementation Plan: Espacios que acompañan, personalizados en la entrega

**Branch**: `004-espacios-acompanantes` | **Date**: 2026-10-06 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-espacios-acompanantes/spec.md`

## Summary

Cada espacio acompañante de una entrega (plantilla H) podrá llevar enlace, nombre, cobertura y
**carrusel propios**, armados con el mismo flujo que la presentación principal, y guardados con la
entrega en el servidor. Nada de eso sale de la entrega: las plantillas A–G y las otras entregas siguen
con el catálogo.

Enfoque técnico, en una línea por capa:

- **Servidor**: tabla nueva `entrega_espacios` (una fila por espacio personalizado); las páginas y el
  carrusel de cada espacio en una **subcarpeta propia** de la entrega
  (`entregas/<id>/espacios/<linea>/`); rutas `…/espacios/{linea}` y `…/espacios/{linea}/paginas`
  que **reutilizan** la lógica de subida y armado de la principal, extraída a funciones comunes.
- **Motor**: `bloques.entrega.espacios` (lo propio de cada espacio) y `bloques.entrega.incluidos`
  (qué espacios acompañan *esta* entrega). La H trabaja sobre una **copia** del estado con esos datos
  aplicados; A–G no los leen. Un único punto nuevo en la foto: si un espacio trae `carruselPropio`,
  se usa ese.
- **Compositor**: en «Espacios que la acompañan», cada espacio se abre con su estado (estándar o
  personalizado), sus textos, su enlace y la **misma galería** de páginas que la principal (se
  convierte en un componente reutilizable); «Volver al estándar». Y «Abrir una entrega guardada»,
  que hoy no existe ni para la principal (ver research R5).

## Technical Context

**Language/Version**: Python 3.12 (FastAPI 0.115, SQLAlchemy 2.0, Pydantic 2) y JavaScript ES2019

**Primary Dependencies**: FastAPI, SQLAlchemy, Pillow 12 y el rasterizado de PDF que ya usan las
entregas (`app/mails/entregas/paginas.py`, `carrusel.py`). Ninguna dependencia nueva.

**Storage**: SQLite en `/app/data` (tabla nueva, creada por `create_all`; ninguna columna nueva en
tablas existentes). Imágenes en el volumen: `entregas/<id>/espacios/<linea>/`.

**Testing**: pytest (API, permisos, independencia de carpetas, media pública) + guiones Node desde
pytest (motor: la H aplica lo propio, A–G no) + guardia byte a byte de `build.js` + Playwright para
la demo a 600 y 375 px.

**Target Platform**: contenedor Docker en EasyPanel (DigitalOcean) detrás de Traefik; navegador del
equipo; correos pegados en Gmail.

**Project Type**: aplicación web (API + compositor estático + motor JS compartido)

**Performance Goals**: el carrusel de un espacio pesa lo mismo que el de la principal (presupuesto de
1 MB del armado actual); subir y armar no tarda más que en la principal.

**Constraints**: correos con tablas e inline; el acortador no se toca; `CONTENT_VERSION` no se sube;
los 16 correos de referencia idénticos; las imágenes nunca en el repositorio.

**Scale/Scope**: una entrega lleva de 0 a ~8 espacios; cada uno, de 2 a 4 páginas elegidas.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cómo lo cumple el plan | Estado |
|---|---|---|
| **I. El acortador no se toca** | Solo se añaden una tabla y rutas bajo `/api/entregas/{id}/espacios…` y `/media/entregas/{id}/espacios/…`. El enlace atribuible sigue siendo el de la entrega (`/p/{slug}`). Prueba: el acortador redirige igual. | ✅ |
| **II. Un solo motor de contenido** | El HTML de la H sigue saliendo de `render.js`. Lo propio de cada espacio se aplica en el motor sobre una **copia** del estado; `normaliza()` rellena los campos nuevos sin subir `CONTENT_VERSION`. | ✅ |
| **III. Verificado renderizado** | Matriz del motor (H con y sin espacios propios; A–G con el mismo estado salen estándar); guardia byte a byte; demo en navegador a 600 y 375 px con cero errores de página. | ✅ |
| **IV. Nada que no esté confirmado** | No se inventa nada: un espacio solo cambia lo que la persona escribe o sube; el aviso de precios de la principal se aplica también a sus páginas. | ✅ |
| **V. El repositorio es público** | Las imágenes de cada espacio viven en el volumen, junto a las de la entrega. Sin secretos nuevos. Cada push lo decide la propietaria. | ✅ |
| **Puertas** | Spec → plan → tareas antes de código. Guardias de `build.js` intactas. Nota de Obsidian al terminar. | ✅ |

Re-evaluación tras el diseño (Fase 1): sin cambios; ninguna violación que justificar.

## Project Structure

### Documentation (this feature)

```text
specs/004-espacios-acompanantes/
├── plan.md              # este archivo
├── research.md          # decisiones R1–R8
├── data-model.md        # tabla entrega_espacios y estado del compositor
├── quickstart.md        # recorrido de verificación
├── contracts/api.md     # rutas nuevas
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
app/
├── models.py                      # + EntregaEspacio
└── mails/entregas/
    ├── almacen.py                 # + carpeta/resolución por espacio (subcarpeta)
    ├── galeria.py                 # NUEVO: subir páginas y armar carrusel, comunes a principal y espacios
    ├── rutas.py                   # usa galeria.py; + espacios en la salida de la entrega
    ├── espacios.py                # NUEVO: rutas …/espacios/{linea} y …/espacios/{linea}/paginas
    └── publicas.py                # + /media/entregas/{id}/espacios/{linea}/{fichero}
prototipos/mail/
├── render.js                      # bloques.entrega.espacios / incluidos; carruselPropio
└── compositor.html                # galería reutilizable; espacios en la H; abrir entrega guardada
tests/
├── test_entregas_espacios.py      # NUEVO: API, independencia, media, permisos
├── test_espacios_motor.py         # NUEVO: la H aplica lo propio; A–G no; incluidos por entrega
└── test_entregas_api.py           # sin cambios: debe seguir en verde tras el refactor de galeria.py
```

**Structure Decision**: la capacidad vive dentro de `app/mails/entregas/`, porque un espacio
personalizado **es parte de una entrega**: comparte su sesión, su carpeta, su ciclo de vida y su flujo
de páginas. El flujo de páginas se extrae a `galeria.py` para que principal y espacios usen **el mismo
código** (la especificación pide que se comporten igual).

## Complexity Tracking

| Decisión | Por qué hace falta | Alternativa más simple descartada porque |
|---|---|---|
| Abrir una entrega guardada (nuevo también para la principal) | US4 / SC-403 piden recuperar la entrega en otra sesión; hoy el compositor no carga entregas, solo su propio `localStorage` | Dejarlo en `localStorage`: no cumple «desde otra computadora», que es el caso real del equipo |
| `incluidos` por entrega (qué espacios acompañan) | FR-402 / edge case «espacio quitado»: hoy marcar un espacio en la H lo enciende también en A–G | Seguir con el `on` global: el mismo cambio que la especificación prohíbe para enlaces y textos se colaría por la selección |
