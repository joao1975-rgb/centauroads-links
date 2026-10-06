# Quickstart: verificar el catálogo de líneas de negocio

1. **Siembra**: arrancar la app con una base vacía → `GET /api/panel/lineas` devuelve las cinco líneas
   de serie y las tres familias, con los mismos datos que `render.js`.
2. **Sin cambios, nada cambia**: `node prototipos/mail/build.js` → la guardia byte a byte pasa (16
   correos idénticos). Con el compositor servido, los correos A–H salen iguales que antes.
3. **Alta**: como administrador, en `/panel/lineas` añadir «Alquiler de pantallas» (etiqueta, cobertura,
   enlace, foto subida, texto alternativo), incluida solo en A, D y H, familia nueva «Renta de equipos».
4. **Compositor**: abrir el compositor en otra sesión → la línea está entre los servicios; en B aparece
   marcada «no se usa en esta plantilla»; en A, D y H sale con su foto y su enlace; en D, dentro de
   «Renta de equipos».
5. **Ficha**: añadirle ubicación, medidas y tráfico → aparece en la tabla de agencias (perfil agencia)
   y, si se incluye la E, en su inventario. Sin ficha, no aparece en esas tablas.
6. **Retirar**: retirarla → desaparece del compositor y de los correos nuevos; devolverla → vuelve.
7. **Estado guardado**: con un compositor que tenía texto escrito a mano en la cobertura de una línea
   de serie, recargar tras el alta → el texto a mano sigue; la línea nueva entra.
8. **Comercial**: con una cuenta comercial, `/panel/lineas` se ve en solo lectura y la API de
   administración responde 403.
9. **Acortador**: `/health` 200 y un enlace corto existente redirige igual.
10. **Visual**: A, D, E y H con la línea nueva a 600 y 375 px, sin desborde.
