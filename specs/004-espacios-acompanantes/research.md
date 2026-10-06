# Research: Espacios que acompañan, personalizados en la entrega

Decisiones tomadas leyendo el código de la 002 (entregas) y la 003 (catálogo), 2026-10-06.

## R1 — Dónde viven las imágenes de cada espacio

**Decisión**: subcarpeta `entregas/<id>/espacios/<linea>/` con los mismos nombres que la principal
(`p0.jpg…`, `carrusel.gif`).

**Por qué**: `almacen.borra_entrega()` borra **todo** archivo de nombre válido de la carpeta de la
entrega cuando se vuelve a subir la principal. Con archivos de espacio en la misma carpeta, rehacer la
principal los borraría (incumple FR-408). Una subcarpeta no es un «nombre válido» para ese borrado,
así que queda intacta sin tocar `borra_entrega`.

**Alternativas**: prefijos de nombre en la misma carpeta (`e-led-p0.jpg`) — obliga a cambiar el
borrado de la principal y a repartir reglas de nombre; descartada.

## R2 — Cómo se guardan las páginas elegidas de un espacio

**Decisión**: columna JSON `paginas` en la fila del espacio (`[{orden, ruta, ancho, alto, aviso_precio}]`).

**Por qué**: `entrega_paginas` tiene `UNIQUE(entrega_id, orden)`; añadirle páginas de espacios exigiría
cambiar esa restricción, y SQLite no altera restricciones sin rehacer la tabla. El JSON basta: las
páginas de un espacio solo se leen con su espacio.

## R3 — Dónde aplica el motor lo propio de cada espacio

**Decisión**: `plantillaH` arma una **copia** del estado: `servicios` con lo propio de cada espacio
aplicado (`canva`, `nombre`, `cobertura`, y `carruselPropio` = dirección absoluta de su carrusel) y con
`on` según `incluidos`. `carruselSrc`/`fotoServicio` usan `s.carruselPropio` si existe.

**Por qué**: `complementos()` lo comparten A–G; tocarlo solo por la H obligaría a pasar opciones por
varias capas. Un campo que solo la H pone deja A–G y los 16 correos de referencia como están, y la copia
no muta el estado de la persona (patrón ya usado por `soloSuyas` y `aplicaPerfil`).

## R4 — Qué espacios acompañan *esta* entrega

**Decisión**: `bloques.entrega.incluidos` (lista de ids). Si no existe (sesión anterior a la 004), se
inicializa con los servicios encendidos en ese momento, que es lo que la H enseñaba hasta ahora.

**Por qué**: hoy la H usa el `on` global de `st.servicios`; marcar un espacio en la H lo enciende en
A–G. El servidor ya guarda la selección por entrega (`entregas.servicios`), solo faltaba que el
compositor la usara.

## R5 — Reabrir una entrega

**Hallazgo**: el compositor **no carga** entregas guardadas; `GET /api/entregas/{id}` existe pero nadie
lo llama. Todo vive en `localStorage` de quien la armó.

**Decisión**: «Abrir una entrega guardada» en el paso 01: lista de `GET /api/entregas` y, al elegir,
se cargan en el estado su enlace, título, texto, contacto, `incluidos`, carrusel principal y espacios.
Las miniaturas de una subida anterior no se recuperan (se pueden volver a subir); el carrusel ya armado
sí.

## R6 — Un solo flujo de páginas

**Decisión**: extraer de `rutas.py` la subida (`lee` + guardar `p{i}.jpg`) y el armado
(`arma` + `carrusel.gif` + portada) a `galeria.py`, parametrizados por carpeta. Principal y espacios
llaman a lo mismo. En el compositor, `sube`/`pintaMinis`/`armaCarrusel` (hoy atados a ids fijos y
variables globales) pasan a un componente `galeria({...})` con estado propio por instancia.

**Por qué**: la especificación pide que el espacio se comporte **igual** que la principal; dos copias
del flujo acabarían divergiendo. `test_entregas_api.py` vigila que la principal no cambie.

## R7 — Que el correo enseñe el carrusel nuevo

**Decisión**: la misma marca de versión que la principal (`?v=` de `_url_media`, sacada de la fecha y
el tamaño del archivo).

## R8 — «Estándar» lo decide el servidor contra el catálogo

**Decisión**: al guardar lo propio de un espacio, cada campo igual al de su línea en `lineas_negocio`
se guarda vacío (= estándar). Una fila sin campos propios ni carrusel se borra.

**Por qué**: FR-403; y así la marca «personalizado» del compositor sale de un único criterio.
