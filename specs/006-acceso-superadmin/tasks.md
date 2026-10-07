# Tasks: Acceso del superadministrador y Centro de control

**Input**: [spec.md](spec.md), [plan.md](plan.md). Pruebas primero (deben fallar antes de implementar).

## Phase 1: US1 — Entrar con la credencial de superadmin (P1)

- [ ] T601 [P] Pruebas: con la credencial de superadmin se entra (200, cookie), la fila queda activa, rol admin y sin hash; contraseña mala → 403 y cuenta como fallo; sin variables configuradas, ese usuario no entra; un usuario que no es correo se acepta — `tests/test_superadmin_entrada.py`
- [ ] T602 `es_superadmin()` y `usuario()` — `app/auth/superadmin.py`
- [ ] T603 Entrada del superadmin en `entrar_con_contrasena`, con registro — `app/auth/rutas.py`
- [ ] T604 Pantalla de entrada: campo de texto, sin ventana de emergencia; sustituir sus pruebas — `app/auth/rutas.py`, `tests/test_recuperar_contrasena.py`

## Phase 2: US2 — Centro de control (P1)

- [ ] T605 [P] Pruebas: sin sesión → entrada con destino; comercial → compositor; admin → 200 con las tres salidas; tras entrar sin destino, admin va a `/panel/inicio` y comercial al compositor; con destino, a ese destino — `tests/test_superadmin_entrada.py`
- [ ] T606 `GET /panel/inicio` — `app/auth/inicio.py`, registro del router en `app/main.py`
- [ ] T607 A dónde ir tras entrar (admin → inicio si no hay destino explícito) — `app/auth/rutas.py`
- [ ] T608 «Inicio» en el menú del compositor, Líneas, Textos y Equipo — `prototipos/mail/compositor.html`, `app/mails/catalogo/pantalla.py`, `app/mails/textos/pantalla.py`, `app/auth/equipo.py`

## Phase 3: US3 — La cuenta de superadmin protegida (P2)

- [ ] T609 [P] Pruebas: baja, cambio de rol, poner contraseña y «Tu contraseña» sobre el superadmin → rechazados; la lista lo marca — `tests/test_superadmin_entrada.py`
- [ ] T610 Protecciones en la API y marca en la lista — `app/auth/rutas.py`
- [ ] T611 Etiqueta «Superadmin» y sin acciones en su fila — `app/auth/equipo.py`

## Phase 4: Cierre

- [ ] T612 README: entrada del superadmin y Centro de control — `README.md`
- [ ] T613 Suite completa, build, demo en navegador (entrar como superadmin, Centro de control, las tres salidas, comercial directo al compositor), cero errores de consola
- [ ] T614 Revisión de seguridad y nota de Obsidian
