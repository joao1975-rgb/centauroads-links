# Implementation Plan: Entrega a medida

**Branch**: `002-entregas` | **Date**: 2026-09-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-entregas/spec.md`

## Summary

Añadir al panel un **modo Entrega**: la presentación propia que el equipo ya le armó al cliente en
Canva se entrega con un correo y un WhatsApp consistentes, con su carrusel de 2 a 4 páginas
sacadas de esa misma presentación, con contacto obligatorio y enlace propio, y con aviso cuando el
cliente vuelva a abrirla.

Dos decisiones gobiernan el resto:

1. **El motor sigue siendo `render.js` en el navegador.** No se porta a Jinja2 ahora. Se
   **refactoriza en bloques y recetas**, y la entrega pasa a ser una receta más, hermana de A–G.
   Eso hace trivial la exigencia de que A–G salgan byte a byte idénticas.
2. **La entrega vive en el servidor, pero el envío no.** El servidor guarda la entrega, rasteriza
   el PDF, arma el carrusel y sirve la página de vista previa. Copiar y pegar en el correo lo sigue
   haciendo una persona: *"deja que el proceso se siga haciendo manual el copiar y pegar en el
   mail y por ultimo coordinamos el envio automatico por N8N"*.

## Technical Context

**Language/Version**: Python 3.12 (el del contenedor actual) + JavaScript ES5 en el motor de
contenido (compatible con el UMD de `render.js`, que corre en navegador y en Node).

**Primary Dependencies**: ya presentes — FastAPI 0.115.6, SQLAlchemy 2.0.36, Pydantic 2.10.4,
Jinja2 3.1.5, itsdangerous, argon2-cffi, `google-auth[requests]` 2.58.0. A añadir: **pypdfium2**
(rasterizar el PDF) y **Pillow** (recortar, redimensionar y escribir el GIF). Ver D4 sobre por qué
no se añade FFmpeg a la imagen.

**Storage**: la misma SQLite sobre el volumen `links-data` → `/app/data`. Dos tablas nuevas y
ninguna columna retirada. Las imágenes de cada entrega van a `/app/data/entregas/<id>/`, en el
**volumen**, no en la imagen del contenedor ni en `app/static/`, porque son datos de cliente y
tienen que sobrevivir a los despliegues.

**Testing**: pytest. La pieza central de esta etapa es la **comparación byte a byte** de las ocho
plantillas A–G antes y después de la refactorización del motor (FR-126, SC-105).

**Target Platform**: contenedor Linux en EasyPanel, tras HTTPS, sirviendo `links.centauroads.com`.

**Project Type**: servicio web con panel administrativo servido por el propio backend.

**Performance Goals**: rasterizar un PDF de 6 páginas y mostrar las miniaturas en menos de 3
segundos (medido: pypdfium2 tarda 0,44 s en esas 6 páginas). Armar el carrusel en menos de 10 s.
Ninguna de las dos operaciones puede bloquear la ruta caliente del acortador.

**Constraints**: restricciones de HTML de correo de la constitución (tablas anidadas, CSS inline,
600 px, sin JavaScript, imágenes con URL pública absoluta). Presupuesto de ~1 MB por carrusel. El
repositorio es público: ninguna credencial en el código, y ninguna dependencia con licencia que
obligue a abrir más de lo que ya está abierto (por eso pypdfium2 y no PyMuPDF, ver D3).

**Scale/Scope**: unas pocas entregas por semana, ~10 personas de panel, 5 espacios publicitarios,
PDF de hasta 20 páginas y 25 MB.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| # | Puerta | Cómo se comprueba | Estado |
|---|--------|-------------------|--------|
| I | **El acortador no se toca** | Ninguna ruta existente cambia. Se añaden `/admin/entregas`, `/api/entregas`, `/media/...` y `/p/{slug}`. El esquema solo **crece**: dos tablas nuevas, cero columnas retiradas. Cada entrega crea una fila normal en `links`, que es uso del acortador, no modificación suya. Prueba bloqueante antes de desplegar: abrir una copia de la base de datos de producción con el código nuevo y verificar enlaces, clics y rutas. | **PASA con condición** |
| II | **Un solo motor de contenido** | Sigue habiendo **un** motor, `render.js`. La entrega es una receta dentro de él, no una plantilla nueva escrita a mano. El texto de entrega por defecto vive en el catálogo del motor (FR-103), no incrustado en la interfaz. El estado guardado se migra en `normaliza()`, no se descarta (FR-128, y enmienda 1.1.0 de la constitución). | **PASA** |
| III | **Verificado renderizado** | El plan incluye ver la entrega renderizada a 600 px y a ~375 px, con las imágenes bloqueadas, y mirar las miniaturas del PDF antes de entregar. La comparación byte a byte de A–G es una puerta, no un deseo. | **PASA** |
| IV | **Nada sin confirmar** | El sistema avisa si una página elegida lleva un precio escrito como texto (FR-112) y advierte de que un precio incrustado en imagen no lo detecta. Los precios del catálogo siguen apagados. La marca de agua de Canva se comprueba mirando, antes de entregar. | **PASA con condición** — la advertencia sobre precios en imagen debe estar escrita en la interfaz, no solo aquí. |
| V | **Repositorio público** | Cliente de Google, clave de sesión y URL del webhook de n8n van por entorno y se validan al arrancar. Las imágenes de cliente viven en el volumen, nunca en el repositorio. `.gitignore` debe cubrir `data/entregas/`. | **PASA con condición** |

Restricciones de correo HTML que el diseño respeta: tablas anidadas, CSS inline, 600 px, sin
JavaScript, imágenes con URL pública absoluta, fotograma 0 del GIF autosuficiente. El conector MCP
de Gmail NO se usa: sanea el HTML y rompe estas plantillas.

## Phase 0: Investigación y decisiones

### D1 — El motor no se porta ahora: se parte en bloques y recetas *(la decisión que ordena el resto)*

La 001 decidió portar `render.js` a Jinja2 (su D1). No ha ocurrido: `app/mails/` existe vacío y lo
que sirve producción es el compositor estático de `app/static/email/`. Esta etapa **no** hace ese
puerto, y conviene decir por qué en vez de dejarlo como deuda muda.

- El puerto obliga a reproducir ocho plantillas con fidelidad byte a byte **y** a construir el modo
  Entrega encima. Son dos riesgos a la vez, y el segundo es el que el usuario pidió.
- El motor de hoy ya cumple el principio II: es uno solo, y corre igual en el navegador y en Node
  (UMD). El `build` de las plantillas lo consume desde Node; el compositor, desde el navegador.
- Lo que sí hace falta para la entrega es que el motor deje de ser siete plantillas paralelas y
  pase a ser **bloques** (marca, servicios, ficha, puente, firma, pie) combinados por **recetas**.
  A–G se convierten en siete recetas sobre los mismos bloques; la entrega es la octava.

**Decisión**: refactorizar `render.js` en bloques + recetas, con la comparación byte a byte de las
ocho plantillas como red. El puerto a Jinja2 sigue vivo como tarea de la 001 y se hará cuando el
servidor necesite renderizar el correo por su cuenta — es decir, cuando se aborde el envío
automático con n8n. No antes.

**Alternativa rechazada**: escribir la entrega como una plantilla nueva a mano. La constitución lo
prohíbe (principio II) y ya se pagó dos veces el precio de tener más de una fuente de verdad.

### D2 — La entrega se guarda en el servidor; el correo se arma en el navegador

El servidor guarda la entrega (enlace, texto, servicios, contacto, páginas) y sirve las imágenes.
El navegador pide ese estado y llama a `render.js` para pintar la vista previa y producir el HTML
que la persona copia. El servidor no genera HTML de correo en esta etapa.

**Consecuencia buena**: la entrega se puede volver a copiar más tarde (FR-107) sin rehacerla, y
la vista previa es exactamente lo que se copia, porque es el mismo código que lo produce.

**Consecuencia asumida**: mientras el correo lo arme el navegador, el envío no puede ser
automático. Es justamente lo que se pidió para esta versión.

### D3 — Del PDF a las imágenes: pypdfium2, no PyMuPDF

Medido sobre un deck real de Canva: **pypdfium2 rasteriza 6 páginas en 0,44 s** con calidad
idéntica a la exportación directa, y además permite leer el texto de cada página, que es lo que
hace posible ponerle nombre a la miniatura ("Ficha técnica – Pantalla Chacao") y avisar de que una
página muestra un precio.

**PyMuPDF queda descartado por licencia**: es AGPL, y este repositorio es público pero no está
licenciado como AGPL. pypdfium2 es BSD/Apache y no impone nada. Principio V.

**Límite de la detección de precios**: lee texto. Un precio convertido en imagen —en el deck de
pantallas hay uno así— no se detecta. La interfaz debe decirlo con todas las letras (puerta IV).

### D4 — El carrusel: Pillow primero, FFmpeg solo si hace falta

El carrusel de las plantillas A–G se arma hoy con FFmpeg (`carrusel_gif.py`), en el portátil, con
paleta por diferencias. Para la entrega hay que armarlo **en el servidor**, y añadir FFmpeg a la
imagen del contenedor son unos 70 MB y una dependencia de sistema nueva en la máquina que sirve el
acortador.

**Decisión**: intentarlo primero con Pillow, que ya hace falta de todos modos para recortar y
redimensionar, y que sabe escribir GIF animado con paleta adaptativa. Con 2 a 4 páginas y una
transición de barrido, el número de fotogramas es pequeño.

**Puerta de medición, no de fe**: se mide con un PDF real. Si el GIF se pasa del presupuesto de
~1 MB, o si el bandeado se ve a 600 px, se añade `ffmpeg` al `Dockerfile` y se reutiliza la
tubería ya probada. La medición es una tarea, no una suposición.

**Medido el 2026-09-23**, con páginas fotográficas reales a 600 px: 2 páginas → 791 KB, 3 → 971 KB,
4 → 842 KB, todas a 128 colores, entre 4,5 s y 8,3 s. **Pillow basta: FFmpeg no entra en la
imagen.** El precio es la transición —con cuatro páginas fotográficas el barrido baja a dos
pasos—, y el margen es estrecho: tres páginas se quedan a 29 KB del techo. Si un deck más pesado
se pasara, la salida sigue siendo la de arriba.

### D5 — Cada entrega es un enlace del acortador, y eso no es tocarlo

Cada entrega crea una fila normal en `links`, con destino el enlace de Canva del cliente. Con eso:

- `/{slug}` sigue siendo el acortador de siempre y redirige a la presentación. Cero cambios.
- Los clics se registran donde ya se registran, con la columna `contact_token` que la 001 añadió.
- La regla de las 3 aperturas en 48 horas y la tabla `alerts` funcionan sin tocarse.

Y se añade **`/p/{slug}`**: una página de vista previa mínima, con `og:title`, `og:description` y
`og:image` apuntando a la portada de la entrega, para que WhatsApp muestre la tarjeta al pegar el
enlace (FR-117). Esa página registra el clic igual y ofrece el botón hacia la presentación. Es una
página web, no un correo: el principio II no la alcanza.

**Alternativa rechazada**: un identificador propio de entregas desconectado de `links`. Obligaría a
duplicar clics, estadísticas y avisos, y a mantener dos historias de aperturas.

### D6 — Entrar con el Gmail de cada persona, contra la lista que ya existe

`panel_users` ya es la lista de autorizados: tiene `email`, `activo` y `rol`. Hoy
`app/auth/google.py` restringe la entrada al dominio `centauroads.com`. Para esta capacidad se
amplía: **entra quien tenga una fila activa en `panel_users`**, sea del dominio o un Gmail
personal. No hace falta tabla nueva.

- Retirar a alguien es poner `activo` en falso, no borrar la fila: la bitácora tiene que seguir
  señalando a alguien.
- El rechazo no revela si la cuenta existe en la lista (FR-119, escenario 2).
- **Es un paso obligatorio de la baja de una persona**, porque su Gmail sigue existiendo fuera de
  la empresa. Queda escrito aquí y en la interfaz de administración.

### D7 — Los avisos: primero se registran, después se reparten

El aviso se escribe en `alerts` y **solo después** se intenta el webhook a n8n. Si n8n no responde
—hoy da 502— el aviso sigue visible en el panel y se reintenta más tarde. La aplicación no guarda
ninguna credencial de envío: solo la URL del webhook, por entorno.

**Antes de darle el reparto a n8n hay que repararlo y cambiar sus credenciales expuestas.** Esa
tarea es de infraestructura, no de código, y está al final del orden de construcción por eso.

### D8 — Sin copias de seguridad, por decisión del propietario

Decisión tomada con el riesgo delante, y se escribe aquí para que sea recuperable: entregas,
imágenes de cliente, historial de clics y **el destino de los enlaces cortos ya impresos en
vallas** viven en un solo disco. Si ese disco falla, se pierden, y los enlaces impresos dejan de
funcionar.

No se vuelve a plantear en cada etapa. Activarlo después es barato (copias de DigitalOcean, o
copia nocturna a Spaces); cuanto más tarde, más hay que perder.

### Dependencias nuevas

| Paquete | Para qué | Licencia | Por qué esta y no otra |
|---------|----------|----------|------------------------|
| `pypdfium2` | PDF → imagen y texto por página | BSD-3 / Apache-2.0 | PyMuPDF es AGPL y el repositorio es público (principio V) |
| `Pillow` | recortar, redimensionar, escribir el GIF | HPND (tipo MIT) | Ya es la biblioteca de imagen estándar de Python; evita añadir FFmpeg a la imagen |

`ffmpeg` (paquete de sistema) queda **condicionado** a la medición de D4.

## Project Structure

### Documentation (this feature)

```text
specs/002-entregas/
├── plan.md              # Este fichero
├── spec.md              # Especificación
├── data-model.md        # Modelo de datos
└── tasks.md             # Tareas
```

### Source Code (repository root)

```text
app/
├── main.py                       # EXISTENTE — solo se le añade el montaje del router de entregas
├── models.py                     # EXISTENTE — se le añaden dos clases, no se toca ninguna
├── migracion.py                  # EXISTENTE — las tablas nuevas las crea `create_all`
├── auth/
│   └── google.py                 # EXISTENTE — se amplía: vale cualquier Gmail de panel_users
├── mails/
│   └── entregas/                 # NUEVO
│       ├── __init__.py
│       ├── rutas.py              # /admin/entregas, /api/entregas, /media/..., /p/{slug}
│       ├── paginas.py            # PDF -> imágenes + texto (pypdfium2); aviso de precio
│       ├── carrusel.py           # imágenes -> GIF (Pillow); fotograma 0 = primera página
│       ├── almacen.py            # ficheros bajo /app/data/entregas/<id>/
│       └── avisos.py             # registra en `alerts` y después llama al webhook de n8n
└── static/email/
    ├── render.js                 # EXISTENTE — refactor: bloques + recetas, + receta "entrega"
    └── compositor.html           # EXISTENTE — + modo Entrega (cinco pasos)

prototipos/mail/
├── render.js                     # la fuente; `build.js` la copia a app/static/email/
└── build.js                      # EXISTENTE — + la comparación byte a byte contra las golden

tests/
├── golden/                       # las ocho plantilla-*.html de referencia, antes del refactor
├── test_plantillas_identicas.py  # A–G byte a byte (FR-126, SC-105)
├── test_paginas_pdf.py           # 6 páginas, orden, aviso de precio, ficheros rechazados
├── test_carrusel.py              # 2–4 páginas, fotograma 0, peso bajo presupuesto
├── test_entregas_api.py          # contacto obligatorio, enlace propio, vista previa /p/{slug}
├── test_acceso_lista.py          # Gmail en la lista entra, fuera de la lista no
└── test_avisos.py                # el aviso se registra aunque n8n esté caído
```

**Structure Decision**: el mismo proyecto de siempre. Las entregas entran como subpaquete de
`app/mails/`, que la 001 ya reservó. Los ficheros de cliente van al volumen, separados del código.
No se levanta servicio nuevo: la constitución exige convivir con el acortador y añadir una pieza
más sería contradecirlo.

## Orden de construcción

| Fase | Qué deja funcionando | Tamaño | Depende de |
|------|----------------------|--------|-----------|
| **0 · Especificar** | Esta especificación, el plan, el modelo de datos y las tareas. La constitución enmendada a 1.1.0. | pequeña | — |
| **1 · Bloques y recetas** | Nada visible. El motor partido en bloques, A–G byte a byte idénticas. | mediana | 0 |
| **2 · La entrega en el servidor** | Se puede crear una entrega por API, subir su PDF, elegir páginas y ver `/p/{slug}` con su tarjeta de WhatsApp. | mediana | 1 |
| **3 · El modo Entrega en el panel** | **Aquí ya se entregan propuestas de verdad.** Los cinco pasos, entrada con Google contra la lista, "Pedírselo a Claude", "Copiar para Gmail" y "Copiar para WhatsApp". | mediana | 2 |
| **4 · Saber quién la abrió** | Aperturas por contacto y aviso de interés repetido, visible en el panel. | pequeña | 2 |
| **5 · n8n reparte los avisos** | El aviso llega fuera del panel. | pequeña | 4 · **y reparar n8n** |

Cada fase se despliega sola y deja algo utilizable. La 3 es el punto en el que la capacidad
empieza a devolver trabajo; de la 4 en adelante es ganancia.

## Complexity Tracking

> Solo lo que se aparta del camino simple y por qué.

| Desviación | Por qué hace falta | Alternativa más simple, y por qué se rechaza |
|-----------|--------------------|-----------------------------------------------|
| Refactorizar el motor antes de añadir la entrega | Sin bloques, la entrega sería una octava plantilla escrita a mano: exactamente lo que prohíbe el principio II y lo que ya salió caro dos veces | Añadir la entrega como plantilla nueva: más rápido esta semana, dos fuentes de verdad para siempre |
| Aplazar el puerto a Jinja2 que decidió la 001 | Hacer el puerto y la entrega a la vez son dos riesgos simultáneos, y solo uno es lo que se pidió | Portar ahora: retrasa la entrega y pone en riesgo ocho plantillas que hoy funcionan |
| Rasterizar PDF dentro del servidor del acortador | Es la única forma de que funcione desde cualquier computadora sin instalar nada (SC-108), que es el motivo de toda la capacidad | Hacerlo en local como hoy: vuelve a atar la herramienta a un portátil |
| Guardar imágenes de cliente en el volumen | Son datos, no código: tienen que sobrevivir a los despliegues y no pueden entrar al repositorio público | Servirlas desde `app/static/`: irían al repositorio público y se perderían en cada despliegue |

## Riesgos abiertos

- **Sin copias de seguridad** (D8). Riesgo aceptado, no mitigado. Es el mayor del plan.
- **n8n caído con credenciales expuestas.** Bloquea solo la fase 5; nada más depende de él.
- **Marca de agua de Canva** según el plan de la cuenta que descargue el PDF. Se comprueba mirando
  las miniaturas, antes de entregar. Pendiente de verificar en la práctica.
- **Permiso de uso comercial de los vídeos de @nanopopcast** sigue pendiente; no afecta a esta
  capacidad, pero sigue afectando a las plantillas que los usan.
