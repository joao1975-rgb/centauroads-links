# Implementation Plan: Acceso del superadministrador y Centro de control

**Branch**: `006-acceso-superadmin` | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)

## Summary

La credencial de superadmin pasa a abrir sesión desde la pantalla de entrada normal. El superadmin es una
fila más de `panel_users` (rol `admin`) que se crea o se reactiva al entrar, **sin contraseña guardada**:
se reconoce porque su correo coincide con `SUPERADMIN_USER` y su contraseña se comprueba contra
`SUPERADMIN_PASS`. Tras entrar, superadmin y administradores llegan a un **Centro de control**
(`/panel/inicio`) con tres salidas; los comerciales, al compositor.

## Technical Context

**Language/Version**: Python 3.12 (FastAPI 0.115) y JavaScript ES2019 en páginas servidas por Python.

**Storage**: SQLite. **Sin columnas nuevas**: «es superadmin» se deduce del entorno, no se guarda.

**Testing**: pytest (entrada, permisos, protecciones) + demo en navegador.

**Constraints**: la credencial no se escribe en el código ni en la base; mismo límite de intentos; la clave
del acortador sigue igual.

## Constitution Check

| Principio | Cómo lo cumple | Estado |
|---|---|---|
| I. El acortador no se toca | `app/main.py` sigue usando `superadmin.verifica` para la clave del acortador. | ✅ |
| II. Un solo motor de contenido | No toca el motor ni las plantillas. | ✅ |
| III. Verificado | Pruebas de entrada y permisos, demo en navegador sin errores. | ✅ |
| IV. Nada inventado | Sin textos de negocio nuevos. | ✅ |
| V. Repositorio público | Ningún secreto en el código; la contraseña vive solo en EasyPanel. | ✅ |

## Diseño por pieza

| Pieza | Archivo | Cambio |
|---|---|---|
| Reconocer al superadmin | `app/auth/superadmin.py` | `es_superadmin(email)` y `usuario()`: comparan con `SUPERADMIN_USER` en minúsculas. |
| Entrar | `app/auth/rutas.py` · `entrar_con_contrasena` | Si el correo es el de superadmin: comprueba la contraseña con `compare_digest` contra `SUPERADMIN_PASS`; si falla, mismo rechazo y cuenta como fallo; si acierta, crea o reactiva la fila (activo, rol admin, sin hash) y abre sesión. Registro en el log. |
| Pantalla de entrada | `app/auth/rutas.py` · `_ENTRADA` | Campo «Correo» de tipo texto (acepta un usuario que no sea correo). Fuera la ventana de emergencia y su enlace. Tras entrar sin destino explícito: admin → `/panel/inicio`; comercial → compositor. |
| Centro de control | `app/auth/inicio.py` (nuevo) | `GET /panel/inicio`: sin sesión → entrada; comercial → compositor; admin → página con Compositor, Administración (Líneas, Textos) y Accesos (Equipo). Mismo estilo que las pantallas del panel. |
| «Inicio» en el menú | compositor, `/panel/lineas`, `/panel/textos`, `/panel/equipo` | Enlace «Inicio» a `/panel/inicio`. |
| Protecciones | `app/auth/rutas.py` | `baja_usuario`, `edita_usuario` (rol/activo), `contrasena_de_otro`: 403 «Esa cuenta se gestiona en EasyPanel» si es el superadmin. `cambia_mi_contrasena`: 400 con el mismo motivo. `listar_usuarios` devuelve `superadmin: true` en su fila. |
| Equipo | `app/auth/equipo.py` | La fila del superadmin lleva la etiqueta «Superadmin» y no ofrece baja, rol ni contraseña. |
| Documentación | `README.md` | Entrada del superadmin y Centro de control. |

La ruta `POST /api/panel/arranque/contrasena` se conserva (recuperación desde la consola), sin interfaz.

## Riesgos

- **Un administrador normal con el mismo correo que `SUPERADMIN_USER`**: pasa a ser la cuenta de superadmin
  y su contraseña guardada deja de valer (manda EasyPanel). Hoy no existe esa fila; se documenta.
- **Pruebas que fijan la ventana de emergencia** (`test_recuperar_contrasena.py`): se sustituyen; las de la
  ruta por API se quedan.
