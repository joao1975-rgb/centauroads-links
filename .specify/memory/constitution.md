<!--
SYNC IMPACT REPORT
Versión: 1.0.0 → 1.1.0
Tipo de cambio: MINOR — se redefine una regla del principio II sin retirar el principio.

Enmienda 1.1.0 (2026-09-22): el principio II exigía subir `CONTENT_VERSION` al cambiar un valor
por defecto. Esa regla resultó ser dañina: `CONTENT_VERSION` forma parte de la clave de
`localStorage`, de modo que subirla descarta el estado guardado y borra el trabajo escrito a mano
por el usuario. Ocurrió una vez, con textos ya redactados. La regla se sustituye por la práctica
que el código aplica desde entonces: **migrar el estado guardado en `normaliza()`**, que corrige
los valores retirados sin descartar lo que la persona escribió. `CONTENT_VERSION` se reserva para
cambios de forma del estado que no se puedan migrar.

Principios definidos (ninguno renombrado, ninguno eliminado):
  I.   El acortador no se toca
  II.  Un solo motor de contenido
  III. El correo se verifica renderizado, no leído
  IV.  Nada que no esté confirmado
  V.   El repositorio es público

Secciones añadidas:
  - Restricciones técnicas del correo HTML
  - Flujo de trabajo y puertas de calidad

Plantillas dependientes:
  ✅ .specify/templates/plan-template.md      — revisada; la puerta "Constitution Check" recoge los 5 principios
  ✅ .specify/templates/spec-template.md      — revisada; alineada, no exige secciones que la constitución contradiga
  ✅ .specify/templates/tasks-template.md     — revisada; las categorías de tarea admiten las puertas de verificación
  ✅ CLAUDE/proyectos/Centauro-Mails-Servicios.md (bóveda Obsidian) — es la memoria larga del proyecto

TODO diferidos: ninguno.
-->

# Centauro ADS · Mails de servicios — Constitución

Este documento gobierna el módulo `app/mails/` y todo lo que lo rodea: el motor de plantillas
(`prototipos/mail/render.js`), las imágenes servidas desde `app/static/email/` y la aplicación
FastAPI que los aloja. Las reglas de aquí están por encima de la conveniencia de cualquier
entrega concreta.

## Principios fundamentales

### I. El acortador no se toca

`centaurads-links` es, antes que nada, el acortador de enlaces que Centauro ADS ya usa en
producción. El módulo de correo **convive** con él; no lo desplaza, no lo reescribe y no lo
degrada.

- Toda migración DEBE probarse antes de desplegar: abrir una base de datos creada por el código
  anterior con el código nuevo y comprobar que los enlaces, los clics y las rutas siguen ahí.
- El volumen persistente `links-data` → `/app/data` es sagrado. Ningún cambio puede provocar que
  se recree la base de datos.
- Las rutas existentes conservan su contrato. Añadir rutas es libre; cambiar o retirar una
  existente exige justificarlo por escrito en la especificación.

**Razón**: el usuario lo pidió textualmente —*"valida que no vaya a perder la aplicacion de
links, esto del mail deberia convivir con el proyecto del link y no desplazarlo"*—. Un correo
que no sale es una molestia; un enlace roto en una valla impresa es dinero perdido.

### II. Un solo motor de contenido

El contenido de los correos vive en **un** motor, `render.js`, con dos ejes independientes que se
multiplican: el **formato** (A Cartelera, B Catálogo, C Nota, D Móvil) decide el aspecto y el
**perfil** (general, agencia, cliente nuevo, phygital) decide el mensaje.

- Un segmento de cliente nuevo es una entrada en `PERFILES`, **nunca** una plantilla duplicada.
- El HTML de un correo no se escribe a mano en ningún sitio: se genera. Los ficheros
  `plantilla-*.html` son salida del `build`, no fuente.
- Al cambiar contenido por defecto DEBE migrarse el estado guardado en `normaliza()`: los
  valores retirados se sustituyen por los vigentes y los elementos nuevos del catálogo entran en
  su sitio. Sin esa migración, el estado del navegador gana a las correcciones y reaparecen datos
  viejos; con ella, lo que la persona escribió a mano sobrevive.
- `CONTENT_VERSION` NO se sube para corregir contenido: forma parte de la clave de almacenamiento
  y subirla **descarta** el trabajo guardado del usuario. Se reserva para cambios de forma del
  estado que `normaliza()` no pueda migrar, y entonces se avisa antes.

**Razón**: la alternativa —una plantilla por segmento— multiplica el mantenimiento para cambiar
solo texto y orden. Ya ocurrió dos veces que datos de contacto retirados reaparecieran en una
copia desactualizada; la causa fue tener más de una fuente de verdad.

### III. El correo se verifica renderizado, no leído

Una plantilla no está terminada porque el código parezca correcto. Está terminada cuando se ha
**mirado** el resultado.

- Todo cambio visual DEBE revisarse renderizado, a anchura real de correo (600 px) y a anchura de
  móvil (~375 px), antes de darlo por hecho.
- Cuando se superpone contenido sobre un objeto de una foto (una pantalla, una valla), las cuatro
  esquinas se **miden** y se proyecta con homografía. Nunca un rectángulo estimado a ojo.
- El texto alternativo importa: con las imágenes bloqueadas el correo DEBE seguir leyéndose y
  manteniendo la marca.
- Contraste mínimo WCAG: 4.5:1 en texto normal, 3:1 en texto grande. El naranja corporativo
  `#F79131` NO cumple sobre fondo claro; para fondos claros se usa `#B35E0A`.

**Razón**: cada defecto que llegó al usuario —el logo con recuadro blanco, el overlay descuadrado,
las transiciones a saltos— pasó la revisión del código y falló al verse.

### IV. Nada que no esté confirmado

El correo habla en nombre de Centauro ADS ante sus clientes. Lo que no esté confirmado por la
empresa no sale.

- Precios, tarifas de entrada y datos de tráfico REQUIEREN confirmación explícita antes de usarse
  con un cliente real. Un espacio sin tarifa confirmada dice **"a cotizar"**; no se insinúa un
  precio ni se estima.
- Nombrar a marcas cliente REQUIERE permiso. El bloque existe apagado hasta que llegue.
- El material de terceros (fotos, vídeo) no se publica sin permiso de uso comercial.
- Un dato de contacto retirado no puede reaparecer. El `build` DEBE fallar si lo detecta.

**Razón**: un precio inventado en un correo comercial es una oferta. Una marca nombrada sin
permiso es un problema legal. Ambos cuestan más de lo que ahorra la prisa.

### V. El repositorio es público

`centaurads-links` está publicado en GitHub y su historia es pública e irreversible.

- Ningún secreto en el código: claves, tokens y credenciales viven en variables de entorno.
- El arranque valida que los secretos que necesita existan, y falla si faltan.
- Cada `push` es una decisión deliberada del propietario, no un efecto secundario de confirmar.
- Antes de publicar se revisa lo que sube buscando claves, tokens y cadenas hexadecimales largas.

**Razón**: el propietario decidió mantener la clave actual asumiendo que quedaba en la historia
pública. Esa decisión obliga a que todo lo demás sea escrupuloso.

## Restricciones técnicas del correo HTML

El correo no es la web. Estas restricciones no son estilo, son compatibilidad:

- **Maquetación con tablas anidadas** y CSS **100 % inline**. Nada de flexbox, grid ni hojas de
  estilo externas.
- **Anchura máxima 600 px**, con tablas fantasma (`mso`) para Outlook.
- **Sin JavaScript.** Ningún cliente de correo lo ejecuta.
- **GIF**: el fotograma 0 es lo que ve Outlook, así que debe bastarse solo. Optimización con
  paleta por diferencias; presupuesto ~1 MB por pieza.
- **Imágenes servidas desde `app/static/email/`**, con URL absoluta pública, porque el proxy de
  Gmail las descarga. Nada de `@` ni caracteres raros en los nombres de fichero.
- **El conector MCP de Gmail sanea el HTML** (elimina `<img>`, `background`, `role`): no sirve
  para estas plantillas. El envío real usa la API de Gmail directamente.

## Flujo de trabajo y puertas de calidad

- **Spec Kit primero.** Antes de escribir código para una capacidad nueva: especificación, plan y
  tareas. No se vibecodea sobre producción.
- **La bóveda Obsidian es la memoria larga.** `CLAUDE/proyectos/Centauro-Mails-Servicios.md`
  guarda decisiones y porqués; el código guarda el qué. Al terminar un trabajo relevante, la nota
  queda actualizada.
- **Puerta de despliegue**: no se despliega sin haber comprobado que el acortador sigue vivo
  (`/health` responde 200) y que las rutas existentes conservan su comportamiento.
- **Puerta de contenido**: el `build` falla si aparece un dato de contacto retirado o falta uno
  vigente. Esta puerta no se desactiva; se corrige el contenido.
- **Reversibilidad**: toda migración de datos debe poder deshacerse, o no se ejecuta.

## Gobernanza

Esta constitución está por encima de cualquier otra práctica del proyecto. Cuando una decisión de
implementación la contradiga, gana la constitución; si la constitución está equivocada, se
enmienda antes de actuar, no después.

- **Enmiendas**: cualquier cambio de principio se documenta en el Sync Impact Report de la
  cabecera de este fichero, con versión nueva y razón del cambio.
- **Versionado semántico**: MAJOR si se retira o redefine un principio de forma incompatible;
  MINOR si se añade un principio o se amplía materialmente su alcance; PATCH para aclaraciones y
  correcciones que no cambian el significado.
- **Revisión de cumplimiento**: cada plan de implementación pasa por la puerta "Constitution
  Check" antes de generar tareas, y otra vez antes de dar el trabajo por terminado. La
  complejidad que viole un principio debe justificarse explícitamente o eliminarse.
- **Guía en tiempo de ejecución**: `CLAUDE.md` y las reglas de `~/.claude/rules/` complementan
  esta constitución; donde entren en conflicto sobre este proyecto, manda la constitución.

**Versión**: 1.1.0 | **Ratificada**: 2026-09-19 | **Última enmienda**: 2026-09-22
