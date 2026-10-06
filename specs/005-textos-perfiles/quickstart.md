# Quickstart: verificar los textos de los perfiles

1. **Sin cambios, nada cambia**: `node prototipos/mail/build.js` → 16 correos idénticos.
2. **Mensaje de un perfil**: como administrador, en `/panel/textos`, cambiar el título y el botón de
   *Agencias* → en otra sesión, un correo con perfil agencia los lleva; uno con perfil General no.
3. **Asuntos**: cambiar el asunto «curiosidad» del General → el compositor lo ofrece y el correo lo usa.
4. **Bloque**: cambiar el paso 2 de la ruta → el correo de *Cliente nuevo* lo muestra en ese paso.
5. **Marcadores**: un texto con `{empresa}` sale con el nombre de la empresa.
6. **Volver al de serie**: el correo vuelve a ser idéntico al de antes.
7. **Comercial**: ve la pantalla sin poder cambiar; la API de cambios responde 403.
8. **Visual**: correos A, D y E con textos cambiados a 600 y 375 px, sin desborde ni errores de consola.
