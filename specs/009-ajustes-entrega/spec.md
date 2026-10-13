# Feature Specification: Ajustes de la entrega H (enlace, cargo, orden, WhatsApp)

**Feature Branch**: `009-ajustes-entrega`

**Created**: 2026-10-12

**Status**: Draft

**Input**: Petición de la propietaria (2026-10-12), con capturas de la entrega #5 (Clínica El Ávila).

Decisiones tomadas (preguntas, 2026-10-12): el paso 1 se **guarda solo**; el orden de los espacios es
**de cada entrega**; en WhatsApp, **todo en un mensaje**.

## Contexto y diagnóstico

**El enlace equivocado (lo más grave).** En la entrega #5 se pegó `canva.link/0ziureqkfvl5mp7`, pero
«Ver la propuesta» llevó a otra presentación. Comprobado:

- `canva.link/0ziureqkfvl5mp7` → diseño `DAHQ-e8eEOM` (el que se quería).
- `/p/ea4w44v3` (enlace de la entrega #5 en el servidor) → `canva.link/idstrncm0v4ll5q` → `DAHW4XcxvYo`.
- La tarjeta de `/p/ea4w44v3` tiene el título y el texto de Clínica El Ávila, pero la portada de la
  presentación anterior («Solución DOOH Phygital & Sports Analytics»).

El correo y WhatsApp llevan al cliente a `/p/<slug>`, que redirige a lo que está **guardado**. El
compositor muestra lo que hay **en pantalla**. El enlace nuevo se pegó después de guardar y nada avisó de
que el servidor seguía con el anterior. La portada vieja tiene la misma raíz: el enlace cambió y las
imágenes de la presentación no.

## User Scenarios & Testing

### US1 — Lo que se ve es lo que recibe el cliente (P1)

Con la entrega ya guardada, cada cambio del paso 1 (enlace, título, textos, rótulo, texto corto, estilo
del título, orden e inclusión de los espacios) se guarda solo, un segundo después. Junto al paso 1 se
lee «Guardado», «Guardando…» o «Sin guardar: <motivo>». Al copiar (Gmail, HTML, texto, WhatsApp) con
algo sin guardar, no se copia: se guarda y se pide volver a copiar.

Si el enlace de Canva cambia y la entrega ya tiene imágenes, se avisa: «Las imágenes (portada y
carrusel) siguen siendo las de la presentación anterior: sube el PDF de la nueva».

**Acceptance**: cambiar el enlace de una entrega guardada y esperar → `/p/<slug>` lleva al nuevo, sin
pulsar Guardar. Un enlace inválido o un título vacío no se guardan y se dice por qué. Un contacto nuevo
sin guardar sigue necesitando «Guardar».

### US2 — Cargo de la firma (P1)

«Cargo (debajo del nombre)» ofrece solo: **Asesor Comercial**, **Alianzas Comerciales**, **Directora**.
El de por defecto no cambia (Alianzas Comerciales): los correos de siempre salen idénticos.

### US3 — Ordenar los espacios que la acompañan (P2)

Cada espacio (del catálogo o a medida) lleva **↑** y **↓** a su lado. El orden es de esa entrega: se
guarda con ella y el correo, el texto plano y WhatsApp lo siguen. Sin orden guardado, el de hoy.

### US4 — Los servicios en el mensaje de WhatsApp (P2)

El mensaje de WhatsApp de la H, además de lo de hoy, lista los espacios que la acompañan con su enlace.
El enlace de la propuesta sigue siendo el primero, para que la vista previa sea la de la propuesta
(WhatsApp solo enseña la del primer enlace).

## Requirements

- **FR-901**: Con entrega guardada y contacto ya elegido, los cambios del paso 1 y de los espacios MUST
  guardarse solos (espera de 1 s); el estado MUST verse junto al paso 1.
- **FR-902**: Copiar MUST NOT copiar con cambios sin guardar; MUST guardar y pedir repetir.
- **FR-903**: Cambiar el enlace con imágenes ya subidas MUST avisar de que las imágenes son las anteriores.
- **FR-904**: El cargo MUST ofrecer exactamente Asesor Comercial, Alianzas Comerciales y Directora.
- **FR-905**: Los espacios MUST poder subirse y bajarse; el orden MUST guardarse con la entrega
  (`orden_espacios`) y aplicarse en el correo, el texto plano y WhatsApp de la H.
- **FR-906**: El WhatsApp de la H MUST listar los espacios incluidos con su enlace, después del texto.
- **FR-907**: Sin orden ni cambios, los 16 correos de referencia MUST salir idénticos.

## Plan técnico

- **Compositor**: `cuerpoEntrega()` sale de `guardaEntrega`; `touch()` compara el cuerpo con el último
  guardado y programa `autoguarda()` (PUT, sin rehacer el panel para no quitar el foco). Indicador en el
  paso 1. Los botones de copiar pasan por `listoParaCopiar()`. Flechas en `espacioEl`/`aMedidaEl` que
  mueven la fila en el DOM y reescriben `E.orden`.
- **Servidor**: columna `entregas.orden_espacios` (VARCHAR(2000), migración); validada como lista de ids
  con la forma de `almacen.linea_valida`, como mucho 60.
- **Motor**: `espaciosDeLaEntrega` ordena por `e.orden` (orden estable; lo que no está, al final);
  `ROLES` con `asesor`; `renderWhatsApp` de la H añade la lista de espacios.

## Tasks

- [x] T901 Pruebas del motor: orden aplicado en H (correo, texto, WhatsApp) y no en A–G; WhatsApp lista los espacios con enlace y el de la propuesta sigue primero; `ROLES` = asesor/alianzas/directora y por defecto Alianzas — `tests/test_ajustes_entrega_motor.py`
- [x] T902 Pruebas de API: `orden_espacios` se guarda y se devuelve; un id con forma inválida → 422; un PUT sin él no lo borra — `tests/test_entregas_orden.py`
- [x] T903 Motor: orden, cargo y WhatsApp — `prototipos/mail/render.js`
- [x] T904 Servidor: columna, migración, validación y salida — `app/models.py`, `app/migracion.py`, `app/mails/entregas/rutas.py`
- [x] T905 Compositor: guardado automático, indicador, guarda de copiado y aviso de imágenes viejas — `prototipos/mail/compositor.html`
- [x] T906 Compositor: flechas de orden — `prototipos/mail/compositor.html`
- [x] T907 Demo en navegador (cambiar enlace → `/p/` lleva al nuevo sin pulsar Guardar; ordenar; WhatsApp), suite, build (16 idénticas), README y Obsidian
