# Feature Specification: Acceso del superadministrador y Centro de control

**Feature Branch**: `006-acceso-superadmin`

**Created**: 2026-10-07

**Status**: Draft

**Input**: Petición de la propietaria (2026-10-07): «al entrar por el link del superadministrador me obliga
a ingresar un mail para modificar, esto no puede ser; deberían ser opciones: entrar al menú que controla
el superadministrador, entrar al compositor, y modificar/crear un acceso». Decisiones tomadas en la
conversación: opción A (el superadmin es una cuenta especial de la lista), entra por la misma pantalla
que todos, y el Centro de control lo ven el superadmin y los administradores.

## Contexto

La credencial de superadmin (`SUPERADMIN_USER` / `SUPERADMIN_PASS`, en EasyPanel) hoy no abre sesión:
solo pone contraseña a una cuenta que ya está en la lista, desde un formulario de emergencia que obliga a
escribir un correo. Quien tiene esa credencial —la responsable del panel— no puede entrar con ella, y si
ninguna cuenta tiene contraseña, queda fuera de su propia herramienta.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Entrar con la credencial de superadmin (Priority: P1)

La responsable abre el panel y escribe en «Entrar al panel» el usuario y la contraseña de superadmin de
EasyPanel. Entra, sin tener que poner contraseña antes a ninguna cuenta.

**Independent Test**: con la base sin ninguna contraseña puesta, entrar con la credencial de superadmin
lleva al Centro de control.

**Acceptance Scenarios**:

1. **Given** la pantalla de entrada, **When** se escriben el usuario y la contraseña de superadmin,
   **Then** se entra con rol de administrador y se llega al Centro de control.
2. **Given** el usuario de superadmin con una contraseña equivocada, **When** se pulsa Entrar, **Then** no
   entra, sale el mensaje de siempre y cuenta como intento fallido.
3. **Given** que el usuario de superadmin no tiene forma de correo, **When** se escribe en «Correo»,
   **Then** el formulario lo acepta.

---

### User Story 2 - El Centro de control (Priority: P1)

Al entrar, el superadmin y los administradores llegan a una pantalla con tres salidas: **Compositor**,
**Administración** (Líneas de negocio y Textos de los perfiles) y **Accesos** (Equipo: crear cuentas,
roles y contraseñas). Un comercial entra directo al compositor.

**Independent Test**: un administrador entra y ve las tres salidas; un comercial entra y llega al compositor.

**Acceptance Scenarios**:

1. **Given** un administrador o el superadmin, **When** entra sin un destino concreto, **Then** llega al
   Centro de control.
2. **Given** un comercial, **When** entra, **Then** llega al compositor; si abre el Centro de control, lo
   lleva al compositor.
3. **Given** alguien que iba a una pantalla concreta (p. ej. Textos) y tuvo que entrar, **When** entra,
   **Then** vuelve a esa pantalla.
4. **Given** cualquier pantalla del panel, **When** la ve un administrador, **Then** el menú de arriba
   ofrece «Inicio» para volver al Centro de control.

---

### User Story 3 - La cuenta de superadmin está protegida (Priority: P2)

En Equipo, la cuenta de superadmin aparece con la etiqueta «Superadmin» y no se puede dar de baja, cambiar
de rol ni ponerle contraseña: su contraseña es la de EasyPanel.

**Acceptance Scenarios**:

1. **Given** la lista de Equipo, **When** se ve la fila del superadmin, **Then** dice «Superadmin» y no
   ofrece dar de baja, cambiar rol ni poner contraseña.
2. **Given** una llamada directa a la API para dar de baja, cambiar de rol o poner contraseña al
   superadmin, **Then** responde que esa cuenta se gestiona en EasyPanel.

---

### Edge Cases

- **Credencial sin configurar** (faltan las variables): la entrada funciona como hasta ahora para las
  cuentas normales; nadie entra como superadmin.
- **Cambia `SUPERADMIN_USER`**: la cuenta vieja queda como administrador sin contraseña (no puede entrar);
  la nueva se crea al primer acceso.
- **La fila del superadmin estaba dada de baja o como comercial**: al entrar con la credencial vuelve a
  quedar activa y como administradora.
- **El superadmin intenta cambiar «Tu contraseña»**: se le dice que se cambia en EasyPanel.

## Requirements *(mandatory)*

- **FR-601**: La pantalla de entrada MUST aceptar la credencial de superadmin en sus campos normales y
  abrir sesión con rol de administrador.
- **FR-602**: La contraseña del superadmin MUST comprobarse siempre contra `SUPERADMIN_PASS`; nunca se
  guarda en la base.
- **FR-603**: Los intentos fallidos con el usuario de superadmin MUST contar para el mismo límite de la
  entrada.
- **FR-604**: Cada entrada del superadmin MUST quedar registrada.
- **FR-605**: Tras entrar sin destino concreto, el superadmin y los administradores MUST llegar al Centro
  de control; los comerciales, al compositor.
- **FR-606**: El Centro de control MUST ofrecer Compositor, Administración (Líneas de negocio, Textos de
  los perfiles) y Accesos (Equipo); solo para administradores.
- **FR-607**: Las pantallas del panel MUST ofrecer «Inicio» en su menú.
- **FR-608**: La cuenta de superadmin MUST NOT poder darse de baja, cambiar de rol ni recibir contraseña
  desde el panel.
- **FR-609**: El formulario de emergencia y su enlace MUST desaparecer de la pantalla de entrada (la ruta
  de recuperación por API se conserva para quien la use desde la consola).
- **FR-610**: La clave del acortador MUST seguir funcionando con la misma credencial, sin cambios.

## Success Criteria *(mandatory)*

- **SC-601**: La responsable entra con la credencial de EasyPanel en un solo paso, sin escribir otro correo.
- **SC-602**: Desde el Centro de control se llega a cada una de las tres salidas en un clic.
- **SC-603**: Ninguna acción del panel deja al superadmin sin acceso.

## Assumptions

- `SUPERADMIN_USER` puede ser un correo (hoy lo es) o un nombre; se guarda tal cual, en minúsculas, como
  identificador de la cuenta.
- No se crea un rol nuevo: el superadmin es un administrador cuya contraseña manda EasyPanel.
