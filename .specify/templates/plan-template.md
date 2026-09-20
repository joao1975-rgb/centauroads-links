# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: [e.g., Python 3.11, Swift 5.9, Rust 1.75 or NEEDS CLARIFICATION]

**Primary Dependencies**: [e.g., FastAPI, UIKit, LLVM or NEEDS CLARIFICATION]

**Storage**: [if applicable, e.g., PostgreSQL, CoreData, files or N/A]

**Testing**: [e.g., pytest, XCTest, cargo test or NEEDS CLARIFICATION]

**Target Platform**: [e.g., Linux server, iOS 15+, WASM or NEEDS CLARIFICATION]

**Project Type**: [e.g., library/cli/web-service/mobile-app/compiler/desktop-app or NEEDS CLARIFICATION]

**Performance Goals**: [domain-specific, e.g., 1000 req/s, 10k lines/sec, 60 fps or NEEDS CLARIFICATION]

**Constraints**: [domain-specific, e.g., <200ms p95, <100MB memory, offline-capable or NEEDS CLARIFICATION]

**Scale/Scope**: [domain-specific, e.g., 10k users, 1M LOC, 50 screens or NEEDS CLARIFICATION]

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Puertas derivadas de `.specify/memory/constitution.md` v1.0.0. Marca cada una PASA / FALLA /
N/A y, si falla, justifícala en "Complexity Tracking" o cambia el diseño.

| # | Puerta | Cómo se comprueba | Estado |
|---|--------|-------------------|--------|
| I | **El acortador no se toca** | ¿El diseño cambia o retira alguna ruta existente? ¿Toca el esquema de la BD o el volumen `links-data`? Si toca datos, ¿hay prueba de apertura de una BD creada por el código anterior? | [ ] |
| II | **Un solo motor de contenido** | ¿El HTML de correo sale de `render.js` y no se escribe a mano en ningún sitio? ¿Un segmento nuevo es una entrada en `PERFILES` y no una plantilla duplicada? ¿Sube `CONTENT_VERSION` si cambia contenido por defecto? | [ ] |
| III | **Verificado renderizado** | ¿El plan incluye revisar el resultado a 600 px y a ~375 px? ¿Contraste ≥ 4.5:1 en texto normal? ¿El correo se lee con las imágenes bloqueadas? | [ ] |
| IV | **Nada sin confirmar** | ¿Aparece algún precio, dato de tráfico o marca cliente sin confirmación explícita? ¿Se respeta "a cotizar" donde no hay tarifa? | [ ] |
| V | **Repositorio público** | ¿Hay algún secreto en el código en vez de en variables de entorno? ¿El arranque valida que existan? | [ ] |

Restricciones de correo HTML que el diseño debe respetar (constitución, sección "Restricciones
técnicas"): tablas anidadas, CSS inline, 600 px, sin JavaScript, imágenes con URL pública
absoluta desde `app/static/email/`, y el conector MCP de Gmail NO sirve para enviar estas
plantillas.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
