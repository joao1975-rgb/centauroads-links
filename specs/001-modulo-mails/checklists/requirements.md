# Specification Quality Checklist: Módulo de mails de servicios

**Purpose**: Validar que la especificación está completa y es de calidad antes de pasar a la planificación
**Created**: 2026-09-19
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] Sin detalles de implementación (lenguajes, frameworks, APIs)
- [x] Centrada en el valor para el usuario y la necesidad de negocio
- [x] Escrita para interlocutores no técnicos
- [x] Todas las secciones obligatorias completadas

## Requirement Completeness

- [x] No quedan marcadores [NEEDS CLARIFICATION]
- [x] Los requisitos son verificables y no ambiguos
- [x] Los criterios de éxito son medibles
- [x] Los criterios de éxito son agnósticos de la tecnología
- [x] Todos los escenarios de aceptación están definidos
- [x] Los casos límite están identificados
- [x] El alcance está delimitado
- [x] Dependencias y supuestos identificados

## Feature Readiness

- [x] Todos los requisitos funcionales tienen criterios de aceptación claros
- [x] Las historias de usuario cubren los flujos principales
- [x] La capacidad cumple los resultados medibles de Success Criteria
- [x] No se filtran detalles de implementación en la especificación

## Notes

**Lista completa: no quedan marcadores abiertos.** Los tres puntos que el borrador dejaba en el
aire se cerraron así:

1. **¿`centauroads.com` está en Google Workspace?** Resuelto **por verificación, no por pregunta**:
   los registros MX públicos del dominio apuntan a `aspmx.l.google.com`, luego es Workspace. No
   tenía sentido gastar una pregunta del cliente en un dato comprobable.
2. **¿Cómo entra cada persona al panel?** Decidido por el cliente: **las dos vías** — Google del
   dominio como camino principal y usuario con contraseña propia como excepción (FR-001a, FR-001b).
3. **¿Quién envía desde cada cuenta?** Decidido por el cliente: **cada quien su cuenta,
   `mercadeo@` compartido** (FR-004a). Nadie usa la cuenta personal de otra persona.

La lista nominal de personas del equipo sigue sin estar, pero es configuración de puesta en
marcha, no diseño: no bloquea planificar ni construir.

**Decisiones heredadas que esta especificación respeta y no reabre** (de la bóveda Obsidian,
sección 12 de `Centauro-Mails-Servicios.md`):

- Alcance v1 = N0 + N1 + N4. N2 y N3 quedan fuera.
- Enfoque A en dos etapas: etapa 1 = armar + copiar + enlaces por destinatario + alerta;
  etapa 2 = respuesta en hilo por API de correo.
- Regla de remitente: la respuesta a un entrante sale del buzón que lo recibió; el envío bajo
  demanda lo elige la persona entre las cuentas que tenga permitidas.
- Modo "solo borrador" como estado inicial de la etapa 2.
- Nada sale por servicios de envío masivo de terceros en v1.

**Tensión conocida a resolver en el plan, no aquí**: el motor de contenido actual (`render.js`) es
JavaScript y la aplicación es Python. El plan debe decidir entre portarlo o ejecutarlo, y esa
decisión tiene que pasar la puerta del Principio II de la constitución: **un solo motor de
contenido**. Duplicar la lógica de plantillas en dos lenguajes viola ese principio y sería la
opción a rechazar.
