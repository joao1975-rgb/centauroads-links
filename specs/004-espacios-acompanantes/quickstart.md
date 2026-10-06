# Quickstart: verificar los espacios personalizados

1. **Sin tocar nada, nada cambia**: `node prototipos/mail/build.js` → 16 correos idénticos; una entrega
   sin espacios propios genera la H como antes.
2. **Carrusel de un espacio**: con una entrega guardada, en «Espacios que la acompañan» abrir Pantalla
   LED Las Mercedes, subir un PDF de 3 páginas, elegir 2 y un efecto → el correo H muestra ese carrusel
   en ese espacio; los demás siguen estándar.
3. **Independencia**: volver a subir la presentación principal → el carrusel del espacio sigue igual; y
   al revés.
4. **Textos y enlace**: cambiar la cobertura y el enlace del espacio → salen en la H; la plantilla A y
   otra entrega lo muestran estándar.
5. **Marca y retorno**: la lista marca el espacio como personalizado y dice qué tiene propio; «Volver
   al estándar» lo deja como el catálogo, carrusel incluido.
6. **Selección por entrega**: desmarcar un espacio en la H no lo apaga en la plantilla A.
7. **Reabrir**: en otra sesión, «Abrir una entrega guardada» → la entrega vuelve con su carrusel
   principal y sus espacios personalizados.
8. **Visual**: H con dos espacios personalizados a 600 y 375 px, sin desborde y sin errores de página.
9. **Acortador**: `/health` 200 y el enlace de la entrega (`/p/{slug}`) redirige igual.
