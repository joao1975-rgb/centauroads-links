/*
 * Centauro ADS — motor de plantillas de email (PROTOTIPO)
 * ---------------------------------------------------------
 * Un solo módulo que funciona en navegador (window.CentauroMail) y en Node
 * (module.exports). Contiene: catálogo de servicios, contenido por defecto
 * (bloques editables e inhibibles), tres plantillas HTML de email
 * (tablas + estilos 100 % inline) y una versión en texto plano.
 */
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.CentauroMail = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // ── Identidad (misma paleta que el panel de centaurads-links y los decks) ──
  const C = {
    black: '#0F0E13', ink: '#16141D', ink2: '#1F1C2A', line: '#2D2B3A',
    purple: '#85439A', purpleDark: '#6B3580', purpleLight: '#B98BCB',
    orange: '#F79131', orangeDark: '#E07A1A', orangeInk: '#B35E0A',
    paper: '#FFFFFF', sand: '#F6F3EF', mist: '#EFEAF2', rule: '#E2DDE8',
    text: '#1F1B24', muted: '#6E6879', textDark: '#EEEDF2', mutedDark: '#A29EB1',
  };
  const FH = "'Montserrat','Trebuchet MS',Arial,Helvetica,sans-serif";
  const FB = "'Segoe UI',Roboto,Helvetica,Arial,sans-serif";

  // ── Catálogo de servicios (decks de Canva ya validados) ──
  const SERVICIOS = [
    { id: 'vallas', nombre: 'Vallas (OOH)', eyebrow: 'Publicidad exterior', cta: 'Ver inventario general',
      cobertura: 'Disponibilidad a nivel nacional', nota: '',
      slug: 'vallas', canva: 'https://canva.link/fgsgrl8vj329ue0',
      img: 'svc_vallas.jpg', alt: 'Valla de Centauro ADS bajo el elevado de Las Mercedes, Caracas',
      cover: 'cover_vallas.jpg', altCover: 'Portada: Disponibilidad de vallas Gran Caracas' },
    { id: 'led', nombre: 'Pantallas LED (DOOH)', eyebrow: 'Digital outdoor', cta: 'Consultar disponibilidad',
      cobertura: 'Ubicación: Chacao y Las Mercedes',
      nota: 'Servicio de videos (por cotizar) · Alquiler y venta de pantallas LED',
      slug: 'pantallas-led', canva: 'https://canva.link/p69pybf8jctaq8d',
      img: 'svc_led.jpg', alt: 'Pantalla LED vertical de Chacao, Av. Francisco de Miranda con Calle Elice',
      cover: 'cover_led.jpg', altCover: 'Portada: Circuito pantallas LED Chacao y Las Mercedes' },
    { id: 'totem', nombre: 'Tótem digital', eyebrow: 'Outdoor · Indoor', cta: 'Consultar disponibilidad',
      cobertura: 'Ubicación: C.C. San Ignacio', nota: 'Alquiler y venta de tótems digitales',
      slug: 'totem-san-ignacio', canva: 'https://canva.link/p5gmvy032ba3sbm',
      img: 'svc_totem.jpg', alt: 'Tótem digital en la entrada del C.C. San Ignacio, La Castellana',
      cover: 'cover_totem.jpg', altCover: 'Portada: Tótem digital C.C. San Ignacio' },
    { id: 'rider', nombre: 'Publicidad móvil · Rider Clon', eyebrow: 'Movilidad', cta: 'Ver presentación',
      cobertura: 'A nivel nacional', nota: 'Motos con caja de luz LED · flota de 250 · tracking en tiempo real',
      slug: 'rider-clon', canva: 'https://canva.link/rider-clon',
      img: 'svc_rider.jpg', alt: 'Motorizado Rider Clon con caja de luz LED en Caracas',
      cover: 'cover_rider.jpg', altCover: 'Portada: Rider Clon publicidad móvil' },
    { id: 'paradas', nombre: 'Paradas en Caracas', eyebrow: 'Mobiliario urbano', cta: 'Consultar disponibilidad',
      cobertura: 'Paradas con pantalla LED · Las Mercedes', nota: '',
      slug: 'paradas-caracas', canva: 'https://www.canva.com/design/DAHBIjY6Bxc/InR36fbTc24tlKhdrI7tBA/view',
      img: 'svc_paradas.jpg', alt: 'Parada con pantalla LED en Av. Paseo Enrique Eraso, Las Mercedes',
      cover: 'cover_paradas.jpg', altCover: 'Portada: Parada con pantalla LED Las Mercedes' },
  ];

  // ── Grupos de la plantilla D (taxonomía del flyer "Servicios de publicidad exterior") ──
  const GRUPOS = [
    { id: 'vallas', eyebrow: 'Gran formato', titulo: 'Vallas (OOH)', servicios: ['vallas'] },
    { id: 'dooh', eyebrow: 'Digital outdoor', titulo: 'Pantallas LED y Tótems (DOOH)', servicios: ['led', 'totem', 'paradas'] },
    { id: 'movil', eyebrow: 'Movilidad', titulo: 'Publicidad móvil · Rider Clon', servicios: ['rider'] },
  ];


  // ── Ficha tecnica de cada espacio (datos reales de los decks de Canva) ──
  // Se usan en la tabla de disponibilidad del perfil de agencias y en los precios "desde".
  const FICHA = {
    led:     { ubic: 'Chacao · Av. F. de Miranda',   medida: '4 × 8 m',        trafico: '120.000 impactos/día', desde: '1.500' },
    vallas:  { ubic: 'Caracas y nivel nacional',      medida: 'Gran formato',   trafico: 'Alta rotación vial',   desde: '' },
    totem:   { ubic: 'C.C. San Ignacio',              medida: '1440 × 2560 px', trafico: '240 salidas/día',      desde: '300' },
    paradas: { ubic: 'Las Mercedes · Av. Libertador', medida: '2 × 2,4 m',      trafico: '34.000 spots/mes',     desde: '360' },
    rider:   { ubic: 'Caracas · San Antonio · Valencia', medida: '42 × 59 cm',  trafico: '250 motos · 8 h/día',  desde: '1.500' },
  };

  // ── Perfiles de cliente ──
  // Un correo no dice lo mismo a una agencia que compra medios cada semana que a una marca que nunca
  // ha anunciado en la calle. El perfil cambia asunto, texto de entrada, ORDEN de los servicios, el
  // bloque propio de cada audiencia y la llamada a la accion. El formato (A/B/C/D) es independiente.
  const PERFILES = {
    general: {
      nombre: 'General', desc: 'Catálogo completo, sin segmentar. El de siempre.',
      bloque: '', orden: null,
    },
    agencia: {
      nombre: 'Agencias y grandes cuentas',
      desc: 'Ficha de disponibilidad: medidas, tráfico y estado. Datos primero, sin rodeos.',
      asunto: 'Disponibilidad OOH/DOOH · Caracas',
      preheader: 'Medidas, tráfico y estado de cada espacio: pantallas LED, vallas, tótems, paradas y 250 riders.',
      titulo: 'Inventario disponible', sub: 'Centauro ADS · Phygital + DOOH + Digital',
      intro: 'Te comparto el estado del inventario con las medidas y el tráfico de cada espacio, para que puedas cerrar el plan de medios sin pedir las fichas por separado.',
      cierre: 'Si necesitas un espacio que no aparezca aquí, dímelo y lo busco.',
      cta: 'Pedir tarifas y disponibilidad',
      orden: ['led', 'vallas', 'rider', 'totem', 'paradas'],
      bloque: 'disponibilidad',
    },
    nuevo: {
      nombre: 'Cliente nuevo',
      desc: 'La ruta de tres pasos: que te conozcan, que te recuerden, que te encuentren.',
      asunto: 'Tu marca en la calle, paso a paso',
      preheader: 'Una ruta de tres pasos para empezar en publicidad exterior sin experiencia previa.',
      titulo: 'Cómo empezar', sub: 'Publicidad exterior para marcas que empiezan',
      intro: 'Dar el salto a la publicidad exterior no es cuestión de presupuesto, es cuestión de orden. Esta es la ruta que seguimos con las marcas que empiezan de cero.',
      cierre: 'No hace falta ser experto para empezar. Cuéntame qué vendes y te preparo una propuesta a la medida.',
      cta: 'Cuéntame tu negocio',
      orden: ['totem', 'paradas', 'led', 'vallas', 'rider'],
      bloque: 'ruta',
    },
    phygital: {
      nombre: 'Phygital · DOOH + Digital',
      desc: 'El puente: la pantalla capta, el móvil cierra. Para quien busca algo distinto.',
      asunto: 'De la calle al móvil',
      preheader: 'Tu pantalla capta la atención. Tu campaña digital cierra la venta. Así conectamos las dos.',
      titulo: 'De la calle al móvil', sub: 'Phygital · DOOH + Digital',
      intro: 'El problema ya no es que no te vean. Es que te ven y siguen caminando. Phygital convierte ese impacto en una acción que puedes medir en el teléfono.',
      cierre: '¿Armamos algo que rompa el molde este mes? Con quince minutos basta para plantearlo.',
      cta: 'Agendar 15 minutos',
      orden: ['led', 'totem', 'rider', 'paradas', 'vallas'],
      bloque: 'puente',
    },
  };

  // ── Contenido por defecto: cada bloque tiene `on` (inhibir) y campos editables ──
  // CONTENT_VERSION: SUBIR este número cada vez que cambie un valor por defecto (contacto, lema, servicios…).
  // El compositor guarda el contenido en el navegador con esta versión en la clave; al subirla, lo guardado con
  // datos viejos deja de usarse y se cargan los valores nuevos.
  const CONTENT_VERSION = 6;

  function defaultState() {
    return {
      plantilla: 'A', seed: 1, imgSet: 'fotos', heroAnim: true, cardAnim: true,
      // Eje de perfil: cambia el mensaje sin cambiar el formato. 'general' = comportamiento de siempre.
      perfil: 'general',
      // Precios: 'no' = ninguno (el precio va en la cotización formal) · 'desde' = precio de entrada.
      precios: 'no',
      asunto: 'Centauro ADS · Disponibilidad de espacios publicitarios Phygital + DOOH + Digital',
      preheader: 'Vallas, pantallas LED, tótems y publicidad móvil disponibles hoy, con presentación en línea de cada uno.',
      destinatario: 'Sr. Cesar Garcia',
      assetBase: 'img',
      assetBaseProd: 'https://links.centauroads.com/static/email',
      linkBase: '',
      token: '',
      bloques: {
        hero: { on: true, img: 'svc_led_hero.jpg', imgPortada: 'cover_led.jpg', anim: 'hero.gif', alt: 'Pantalla LED de Chacao (Edificio Valmy) con piezas en rotación' },
        saludo: { on: true, texto: 'Hola, buenas noches, {destinatario}:' },
        intro: { on: true, texto: 'Gracias por tu interés en Centauro ADS. Te comparto las soluciones de publicidad exterior que tenemos disponibles hoy; cada una lleva su presentación en línea.' },
        titulo: { on: true, texto: 'Soluciones disponibles', sub: 'Centauro ADS · Phygital + DOOH + Digital' },
        servicios: { on: true },
        suministro: { on: true, titulo: 'Suministro e instalación',
          texto: 'Pantallas, tótems digitales o tradicionales, vallas, chupetas, corpóreos, impresión e instalación. Para cotizar necesitamos:',
          requisitos: ['Foto del sitio', 'Medidas', 'Especificaciones técnicas', 'Materiales'] },
        branding: { on: true, titulo: 'Branding y esculturas',
          texto: 'Corpóreos, letras 3D, cajas de luz, tótems tradicionales, impresión e instalación a medida para tu marca.',
          cta: 'Ver catálogo especial', url: 'mailto:equintero@centauroads.com?subject=Cat%C3%A1logo%20de%20branding%20y%20esculturas' },
        // Muro de clientes: prueba social para el perfil de cliente nuevo. APAGADO hasta que Elizabeth
        // confirme que podemos nombrar a estas marcas en un correo.
        // Etiquetas promocionales sobre las fotos. Cada una se enciende por separado: se puede
        // llevar solo el descuento, solo la fecha límite, o las dos.
        etiquetas: {
          on: false,
          descuento: '15%', descuentoOn: true,
          hasta: '31/10/2026', hastaOn: true,
          // Con animación la etiqueta es un GIF (brillo + rebote del número). Sin ella, la
          // versión de tablas, que pesa cero. Ver etiqueta_gif.py.
          animada: true,
        },
        clientes: { on: false, titulo: 'Marcas que ya están en la calle con nosotros',
          lista: 'Pepsi · Nestlé · Yango · Cashea · EPA · Arturo’s · Ridery · Cinepic · Tío Rico' },
        pasos: { on: true, titulo: 'Próximos pasos',
          texto: 'Una vez seleccionados los espacios, envíanos la información y los documentos para preparar la cotización.' },
        presupuesto: { on: true, titulo: 'Para un presupuesto formal necesitamos',
          items: ['RIF digital de la empresa', 'Fecha de inicio y duración de la campaña', 'Formato o alcance (pantalla, tótem u otro)'] },
        cta: { on: true, texto: 'Enviar información para cotizar', url: 'mailto:equintero@centauroads.com?subject=Solicitud%20de%20cotizaci%C3%B3n' },
        cierre: { on: true, texto: 'Quedo atenta a tu respuesta.' },
        firma: { on: true, nombre: 'Elizabeth Quintero', cargo: 'Alianzas Comerciales · Centauro ADS',
          slogan: 'Visibilidad que conecta', linea: 'PHYGITAL DOOH + Digital',
          email: 'equintero@centauroads.com', telefono: '+58 412 100 3559', ig: '@centauroads',
          web: 'linktr.ee/centauroadss', contacto: 'mercadeo@centauroads.com', direccion: 'Caracas, Venezuela' },
        pie: { on: true, texto: 'Recibes este correo porque solicitaste información sobre espacios publicitarios de Centauro ADS.' },
      },
      servicios: SERVICIOS.map(s => Object.assign({ on: true }, s)),
    };
  }

  // ── Utilidades ──
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const nl2br = s => esc(s).replace(/\n/g, '<br>');
  const fill = (s, st) => String(s || '').replace(/\{destinatario\}/g, st.destinatario || '');
  const linkFor = (st, s) => {
    if (!st.linkBase) return s.canva;
    const b = st.linkBase.replace(/\/$/, '');
    return b + '/' + s.slug + (st.token ? '?c=' + encodeURIComponent(st.token) : '');
  };
  const webHref = (w) => /^https?:\/\//.test(w || '') ? w : 'https://' + (w || '');
  const imgFor = (st, name) => (st.assetBase || 'img').replace(/\/$/, '') + '/' + name;
  // Juego de imágenes por servicio: fotos reales del inventario o portadas de los decks de Canva
  const IMG_SETS = { fotos: 'Fotos reales del inventario', portadas: 'Portadas de las presentaciones (Canva)' };
  const usaPortadas = st => st.imgSet === 'portadas';
  const svcImg = (st, s) => imgFor(st, usaPortadas(st) && s.cover ? s.cover : s.img);
  const svcAlt = (st, s) => (usaPortadas(st) && s.altCover ? s.altCover : s.alt);
  const activos = st => st.bloques.servicios.on ? st.servicios.filter(s => s.on) : [];
  const on = (st, k) => !!(st.bloques[k] && st.bloques[k].on);
  const B = (st, k) => st.bloques[k];
  const lines = v => Array.isArray(v) ? v : String(v || '').split('\n').map(x => x.trim()).filter(Boolean);

  function doc(st, bodyBg, inner) {
    return '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<meta name="x-apple-disable-message-reformatting"><title>' + esc(st.asunto) + '</title></head>' +
      '<body style="margin:0;padding:0;background:' + bodyBg + ';-webkit-text-size-adjust:100%;">' +
      '<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">' + esc(st.preheader) + '</div>' +
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:' + bodyBg + ';">' +
      '<tr><td align="center" style="padding:24px 12px;">' +
      '<!--[if mso]><table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" align="center"><tr><td><![endif]-->' +
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:600px;">' +
      inner + '</table>' +
      '<!--[if mso]></td></tr></table><![endif]-->' +
      '</td></tr></table></body></html>';
  }
  const row = (inner, style) => '<tr><td style="' + (style || '') + '">' + inner + '</td></tr>';
  const button = (text, url, bg, color) =>
    '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td bgcolor="' + bg + '" style="background:' + bg + ';border-radius:6px;">' +
    '<a href="' + esc(url) + '" style="display:inline-block;padding:13px 26px;font-family:' + FH + ';font-size:14px;font-weight:700;letter-spacing:.02em;color:' + color + ';text-decoration:none;">' + esc(text) + '</a></td></tr></table>';
  const numbered = (items, numBg, numColor, textColor) => items.map((t, i) =>
    '<table role="presentation" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 8px 0;"><tr>' +
    '<td width="26" valign="top"><table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td bgcolor="' + numBg + '" align="center" style="background:' + numBg + ';width:22px;height:22px;border-radius:11px;font-family:' + FH + ';font-size:12px;font-weight:800;color:' + numColor + ';line-height:22px;">' + (i + 1) + '</td></tr></table></td>' +
    '<td valign="top" style="padding:2px 0 0 10px;font-family:' + FB + ';font-size:14px;line-height:20px;color:' + textColor + ';">' + esc(t) + '</td></tr></table>').join('');
  const bullets = (items, dotColor, textColor) => items.map(t =>
    '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + textColor + ';padding:0 0 4px 0;"><span style="color:' + dotColor + ';">&#9656;</span>&nbsp; ' + esc(t) + '</div>').join('');

  // ── Bloque de marca: logo horizontal + slogan + linea de servicios ──
  // Jerarquia descendente: el logo manda (200 px), el slogan es la voz (13 px, lila o morado) y la linea de
  // servicios cierra (11 px, naranja, con espaciado amplio). Sin degradados ni adornos: el logo ya tiene color.
  // El logo va en PNG sobre fondo plano (Outlook no compone transparencias con fiabilidad) y a doble resolucion
  // mostrado a la mitad, para que no se vea blando en pantallas densas.
  function marca(st, dark, ancho) {
    const w = ancho || 200;
    const f = B(st, 'firma');
    const slogan = f.slogan || 'Visibilidad que conecta';
    const linea = f.linea || 'PHYGITAL DOOH + Digital';
    const sloganColor = dark ? C.purpleLight : C.purple;
    return '<img src="' + esc(imgFor(st, dark ? 'logo_h_dark_2x.png' : 'logo_h_light_2x.png')) + '" width="' + w + '" alt="Centauro ADS" style="display:block;width:' + w + 'px;max-width:100%;height:auto;border:0;font-family:' + FH + ';font-size:22px;font-weight:800;letter-spacing:-.01em;color:' + (dark ? '#FFFFFF' : C.text) + ';">' +
      '<div style="font-family:' + FH + ';font-size:13px;font-weight:700;letter-spacing:.02em;color:' + sloganColor + ';padding:6px 0 0 2px;">' + esc(slogan) + '</div>' +
      '<div style="font-family:' + FH + ';font-size:11px;font-weight:700;letter-spacing:.10em;color:' + (dark ? C.orange : C.orangeInk) + ';text-transform:uppercase;padding:3px 0 0 2px;white-space:nowrap;">' + esc(linea) + '</div>';
  }

  function firma(st, dark) {
    const f = B(st, 'firma');
    const t = dark ? C.textDark : C.text, m = dark ? C.mutedDark : C.muted, a = dark ? C.orange : C.purple;
    return '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td valign="top" style="padding:0 0 12px 0;">' + marca(st, dark, 168) + '</td></tr><tr>' +
      '<td valign="top" style="font-family:' + FB + ';font-size:13px;line-height:19px;color:' + m + ';">' +
      '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + t + ';">' + esc(f.nombre) + '</div>' +
      '<div>' + esc(f.cargo) + '</div>' +
      '<div><a href="mailto:' + esc(f.email) + '" style="color:' + a + ';text-decoration:none;">' + esc(f.email) + '</a> &nbsp;·&nbsp; <a href="tel:' + esc(String(f.telefono).replace(/[^+0-9]/g, '')) + '" style="color:' + m + ';text-decoration:none;">' + esc(f.telefono) + '</a></div>' +
      (f.contacto ? '<div><a href="mailto:' + esc(f.contacto) + '" style="color:' + a + ';text-decoration:none;">' + esc(f.contacto) + '</a></div>' : '') +
      '<div>' + esc(f.ig) + ' &nbsp;·&nbsp; <a href="' + webHref(f.web) + '" style="color:' + a + ';text-decoration:none;">' + esc(f.web) + '</a> &nbsp;·&nbsp; ' + esc(f.direccion) + '</div>' +
      '</td></tr></table>';
  }

  // ── Aplica el perfil sobre el estado: asunto, textos, orden de servicios y llamada a la accion ──
  function aplicaPerfil(st) {
    const pf = PERFILES[st.perfil];
    if (!pf || !pf.bloque) return st;
    const p = JSON.parse(JSON.stringify(st));
    if (pf.asunto) p.asunto = pf.asunto;
    if (pf.preheader) p.preheader = pf.preheader;
    if (pf.titulo) { p.bloques.titulo.texto = pf.titulo; p.bloques.titulo.sub = pf.sub; }
    if (pf.intro) p.bloques.intro.texto = pf.intro;
    if (pf.cierre) p.bloques.cierre.texto = pf.cierre;
    if (pf.cta) p.bloques.cta.texto = pf.cta;
    if (pf.orden) {
      const pos = {}; pf.orden.forEach(function (id, i) { pos[id] = i; });
      p.servicios = p.servicios.slice().sort(function (a, b) {
        return (pos[a.id] == null ? 99 : pos[a.id]) - (pos[b.id] == null ? 99 : pos[b.id]);
      });
    }
    return p;
  }

  // Precio de entrada: solo cuando el usuario lo activa (st.precios === 'desde').
  const desdeDe = function (st, id) {
    return (st.precios === 'desde' && FICHA[id] && FICHA[id].desde) ? 'desde ' + FICHA[id].desde + ' $/mes' : '';
  };

  // ── Perfil AGENCIAS: parte de disponibilidad ──
  // Una agencia no compra inspiracion, compra disponibilidad y especificaciones. Tabla densa y escaneable,
  // con el dato alineado a la derecha para poder compararlo de un vistazo.
  function tablaDisponibilidad(st, dark) {
    const t = dark ? C.textDark : C.text, m = dark ? C.mutedDark : C.muted;
    const linea = dark ? C.line : C.rule, zebra = dark ? C.ink2 : C.sand;
    const acento = dark ? C.orange : C.orangeInk;
    const cab = 'font-family:' + FH + ';font-size:10px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:' + m + ';padding:12px 10px 8px 0;';
    // La columna de precio solo existe cuando el usuario enciende el modo "desde": sin ella la tabla
    // no insinua tarifas, y con ella el importe tiene cabecera propia en vez de colarse bajo "Trafico".
    const conPrecio = st.precios === 'desde';
    let filas = '';
    activos(st).forEach(function (s, i) {
      const f = FICHA[s.id]; if (!f) return;
      const bg = i % 2 ? 'background:' + zebra + ';' : '';
      const celda = bg + 'padding:11px 10px;border-top:1px solid ' + linea + ';font-family:' + FB + ';font-size:13px;color:' + t + ';';
      filas +=
        '<tr>' +
        '<td style="' + bg + 'padding:11px 10px 11px 12px;border-top:1px solid ' + linea + ';">' +
          '<div style="font-family:' + FH + ';font-size:14px;font-weight:800;color:' + t + ';line-height:18px;">' + esc(s.nombre) + '</div>' +
          '<div style="font-family:' + FB + ';font-size:12px;color:' + m + ';line-height:17px;">' + esc(f.ubic) + '</div>' +
        '</td>' +
        '<td align="right" style="' + celda + 'white-space:nowrap;">' + esc(f.medida) + '</td>' +
        '<td align="right" style="' + celda + (conPrecio ? '' : 'padding-right:12px;') + '">' + esc(f.trafico) + '</td>' +
        (conPrecio
          ? '<td align="right" style="' + celda + 'padding-right:12px;white-space:nowrap;' + (f.desde ? 'color:' + acento + ';font-weight:700;' : 'color:' + m + ';') + '">' +
              (f.desde ? esc(f.desde) + ' $/mes' : 'a cotizar') + '</td>'
          : '') +
        '</tr>';
    });
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid ' + linea + ';border-radius:8px;">' +
      '<tr><td style="' + cab + 'padding-left:12px;">Espacio</td>' +
      '<td align="right" style="' + cab + '">Medidas</td>' +
      '<td align="right" style="' + cab + (conPrecio ? '' : 'padding-right:12px;') + '">Tr\u00e1fico</td>' +
      (conPrecio ? '<td align="right" style="' + cab + 'padding-right:12px;">Desde</td>' : '') +
      '</tr>' +
      filas + '</table>';
  }

  // ── Perfil CLIENTE NUEVO: la ruta de tres pasos ──
  // La idea del propio cliente (pantalla, valla, digital) deja de ser un parrafo y pasa a ser la columna
  // vertebral visual: tres peldanos numerados, cada uno con su objetivo y el problema que resuelve.
  function rutaPasos(st, dark) {
    const t = dark ? C.textDark : C.text, m = dark ? C.mutedDark : C.muted;
    const caja = dark ? C.ink2 : C.sand, linea = dark ? C.line : C.rule;
    const acento = dark ? C.orange : C.orangeInk;
    const pasos = [
      { n: '1', tit: 'Que te conozcan', med: 'Pantallas LED y t\u00f3tems',
        obj: 'El movimiento y el brillo detienen la mirada. Explicas qu\u00e9 vendes a quien pasa por la zona.',
        res: 'Atracci\u00f3n y ventas a corto plazo', id: 'totem' },
      { n: '2', tit: 'Que te recuerden', med: 'Vallas de gran formato',
        obj: 'Quien la ve cada d\u00eda camino al trabajo piensa en ti cuando necesita lo que vendes.',
        res: 'Confianza y posicionamiento', id: 'vallas' },
      { n: '3', tit: 'Que te encuentren', med: 'Campa\u00f1a digital + c\u00f3digo QR',
        obj: 'La calle capta la atenci\u00f3n; el m\u00f3vil recoge al interesado y cierra la venta.',
        res: 'Conversi\u00f3n medible', id: '' },
    ];
    return pasos.map(function (p) {
      const precio = p.id ? desdeDe(st, p.id) : '';
      return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 10px 0;"><tr>' +
        '<td bgcolor="' + caja + '" style="background:' + caja + ';border:1px solid ' + linea + ';border-radius:8px;padding:14px 16px;">' +
          '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
          '<td width="40" valign="top"><table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>' +
            '<td bgcolor="' + acento + '" align="center" style="background:' + acento + ';width:28px;height:28px;border-radius:14px;font-family:' + FH + ';font-size:14px;font-weight:800;color:#FFFFFF;line-height:28px;">' + p.n + '</td>' +
          '</tr></table></td>' +
          '<td valign="top">' +
            '<div style="font-family:' + FH + ';font-size:17px;font-weight:800;color:' + t + ';line-height:22px;">' + esc(p.tit) + '</div>' +
            '<div style="font-family:' + FH + ';font-size:11px;font-weight:700;letter-spacing:.12em;text-transform:uppercase;color:' + acento + ';padding:2px 0 6px 0;">' + esc(p.med) + (precio ? ' \u00b7 ' + esc(precio) : '') + '</div>' +
            '<div style="font-family:' + FB + ';font-size:14px;line-height:21px;color:' + m + ';">' + esc(p.obj) + '</div>' +
            '<div style="font-family:' + FB + ';font-size:13px;line-height:19px;color:' + t + ';padding:6px 0 0 0;"><b>Resuelve:</b> ' + esc(p.res) + '</div>' +
          '</td></tr></table>' +
        '</td></tr></table>';
    }).join('');
  }

  // ── Perfil PHYGITAL: el puente ──
  // El concepto hay que mostrarlo, no contarlo: calle, escaneo, movil. Tres celdas y dos flechas,
  // construido con tablas para que aguante en Outlook.
  function puentePhygital(st, dark) {
    const t = dark ? C.textDark : C.text, m = dark ? C.mutedDark : C.muted;
    const caja = dark ? C.ink2 : C.sand, linea = dark ? C.line : C.rule;
    const acento = dark ? C.orange : C.orangeInk;
    const paso = function (tit, txt, color) {
      return '<td width="31%" valign="top" style="padding:0;">' +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
        '<td bgcolor="' + caja + '" align="center" style="background:' + caja + ';border:1px solid ' + linea + ';border-radius:8px;padding:14px 10px;">' +
          '<div style="font-family:' + FH + ';font-size:13px;font-weight:800;color:' + color + ';letter-spacing:.04em;text-transform:uppercase;">' + esc(tit) + '</div>' +
          '<div style="font-family:' + FB + ';font-size:13px;line-height:19px;color:' + m + ';padding:5px 0 0 0;">' + esc(txt) + '</div>' +
        '</td></tr></table></td>';
    };
    const flecha = '<td width="3.5%" align="center" valign="middle" style="font-family:' + FH + ';font-size:20px;font-weight:800;color:' + acento + ';">&rarr;</td>';
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      paso('En la calle', 'La pantalla o la valla detiene la mirada de quien pasa.', t) + flecha +
      paso('El puente', 'Un c\u00f3digo en pantalla lleva ese impacto al tel\u00e9fono.', acento) + flecha +
      paso('En el m\u00f3vil', 'La campa\u00f1a digital recoge al interesado y cierra.', t) +
      '</tr></table>' +
      '<div style="font-family:' + FB + ';font-size:14px;line-height:21px;color:' + m + ';padding:12px 2px 0 2px;">' +
      'Ya no hay que elegir entre hacer marca en la calle o vender en digital. El exterior capta la atenci\u00f3n que lo digital no consigue, y lo digital mide lo que la calle no puede.</div>';
  }

  // ── Muro de clientes (prueba social, APAGADO hasta que Elizabeth lo confirme) ──
  function muroClientes(st, dark) {
    const b = B(st, 'clientes');
    const t = dark ? C.textDark : C.text, m = dark ? C.mutedDark : C.muted;
    const linea = dark ? C.line : C.rule;
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:10px 0 0 0;"><tr>' +
      '<td align="center" style="border-top:1px solid ' + linea + ';border-bottom:1px solid ' + linea + ';padding:14px 12px;">' +
      '<div style="font-family:' + FH + ';font-size:11px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:' + m + ';padding:0 0 8px 0;">' + esc(b.titulo) + '</div>' +
      '<div style="font-family:' + FH + ';font-size:14px;font-weight:800;line-height:24px;color:' + t + ';">' + esc(b.lista) + '</div>' +
      '</td></tr></table>';
  }

  // Bloque que corresponde al perfil activo (vacio en 'general')
  function bloquePerfil(st, dark) {
    const pf = PERFILES[st.perfil];
    if (!pf || !pf.bloque) return '';
    if (pf.bloque === 'disponibilidad') return tablaDisponibilidad(st, dark);
    if (pf.bloque === 'ruta') return rutaPasos(st, dark) + (on(st, 'clientes') ? muroClientes(st, dark) : '');
    if (pf.bloque === 'puente') return puentePhygital(st, dark);
    return '';
  }

  // ── Etiquetas promocionales ──
  // Van pegadas al borde de la foto, sin separación, para que se lean como una cinta puesta
  // encima y no como otro renglón de texto. Se hace con una fila de tabla, no con posicionamiento
  // absoluto ni imagen de fondo: es lo único que aguanta en Outlook, y una promoción que no se ve
  // en la mitad de los clientes de correo no es una promoción.
  //
  // Cuando van las dos, el naranja (el premio) tira a la izquierda y la tinta oscura (la prisa)
  // cierra a la derecha. Esa tensión es el efecto buscado.
  function cintaEtiquetas(st, arriba, ancho) {
    if (!on(st, 'etiquetas')) return '';
    const e = B(st, 'etiquetas');
    const dto = e.descuentoOn && String(e.descuento || '').trim();
    const fecha = e.hastaOn && String(e.hasta || '').trim();
    if (!dto && !fecha) return '';

    const radio = arriba ? 'border-radius:8px 8px 0 0;' : 'border-radius:0 0 8px 8px;';
    const base = 'font-family:' + FH + ';font-weight:800;text-transform:uppercase;line-height:1;';

    // ── Versión animada ──
    // El correo no ejecuta JavaScript y las animaciones CSS no llegan a Gmail ni a Outlook: lo
    // único que se mueve de verdad en todos los clientes es un GIF. El fichero lo genera
    // etiqueta_gif.py, que dibuja el fotograma 0 en reposo (es lo que ve Outlook) y luego el
    // barrido de brillo y el rebote del número.
    //
    // El precio de esto: el GIF está pre-renderizado, así que los valores viven dentro de la
    // imagen. Cambiar el descuento o la fecha exige regenerarlo. El `alt` lleva el texto
    // completo para quien tenga las imágenes bloqueadas, que en Outlook es lo habitual.
    if (e.animada) {
      const archivo = (dto && fecha) ? 'etq_promo.gif' : (dto ? 'etq_dto.gif' : 'etq_fecha.gif');
      const w = ancho || 264;
      const leyenda = [dto ? dto + ' de descuento' : '', fecha ? 'solo hasta el ' + fecha : '']
        .filter(Boolean).join(' · ');
      return '<img src="' + esc(imgFor(st, archivo)) + '" width="' + w + '" alt="' + esc(leyenda) + '"' +
        ' style="display:block;width:' + w + 'px;max-width:100%;height:auto;' + radio +
        'border:0;font-family:' + FH + ';font-size:13px;font-weight:800;color:' + C.orangeInk + ';">';
    }

    // Cada celda apila etiqueta y valor en dos líneas fijas, en vez de dejar que el texto se
    // parta por donde quiera: en una tarjeta de 264 px "15% de descuento" no cabe de una línea y
    // el corte caía en mitad de la frase. Apilado a propósito se lee como un sello.
    const dosLineas = (arriba_, abajo_) =>
      '<div style="' + base + arriba_.estilo + 'white-space:nowrap;">' + arriba_.txt + '</div>' +
      '<div style="' + base + abajo_.estilo + 'white-space:nowrap;padding-top:3px;">' + abajo_.txt + '</div>';

    // Celda del descuento: el número manda, la palabra lo acompaña.
    const celdaDto = '<td align="center" bgcolor="' + C.orange + '" valign="middle" style="background:' + C.orange + ';padding:8px 8px;' +
      (fecha ? '' : radio) + '">' +
      dosLineas(
        { txt: esc(dto), estilo: 'font-size:20px;letter-spacing:-.01em;color:#141016;' },
        { txt: 'de descuento', estilo: 'font-size:9px;letter-spacing:.16em;color:#141016;' }
      ) + '</td>';

    // Celda de la fecha: más pequeña, deliberadamente. Es el contrapunto, no el titular.
    //
    // Va en morado corporativo y no en tinta casi negra: sobre las plantillas oscuras el negro se
    // fundía con el fondo y la etiqueta parecía texto suelto en vez de un sello. El morado se lee
    // como bloque en claro y en oscuro, y junto al naranja deja el par de la marca. El lila del
    // rótulo da 5,5:1 sobre el morado; el naranja que había antes daba 2,6:1 y no pasaba.
    const celdaFecha = '<td align="center" bgcolor="' + C.purple + '" valign="middle" style="background:' + C.purple + ';padding:8px 8px;' +
      (dto ? '' : radio) + '">' +
      dosLineas(
        { txt: 'solo hasta el', estilo: 'font-size:9px;letter-spacing:.16em;color:#E8D5EF;' },
        { txt: esc(fecha), estilo: 'font-size:14px;letter-spacing:.01em;color:#FFFFFF;' }
      ) + '</td>';

    // Con las dos etiquetas lado a lado hacen falta unos 250 px de hueco. Por debajo de eso el
    // texto no cabe, la tabla se ensancha por su cuenta y la cinta sobresale de la foto: parecía
    // un error de montaje. Cuando el sitio es estrecho se apilan, y así la tipografía puede
    // seguir siendo grande, que es de lo que va una etiqueta promocional.
    const apilar = !!(ancho && ancho <= 250 && dto && fecha);

    let filas;
    if (apilar) {
      filas = '<tr>' + celdaDto.replace('<td ', '<td width="100%" ') + '</tr>' +
              '<tr>' + celdaFecha.replace('<td ', '<td width="100%" ') + '</tr>';
    } else if (dto && fecha) {
      filas = '<tr>' + celdaDto.replace('<td ', '<td width="52%" ') +
                       celdaFecha.replace('<td ', '<td width="48%" ') + '</tr>';
    } else {
      filas = '<tr>' + (dto ? celdaDto : celdaFecha) + '</tr>';
    }

    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"' +
      ' style="' + (ancho ? 'width:' + ancho + 'px;max-width:100%;' : '') + radio + '">' +
      filas + '</table>';
  }

  // Versión para fondo oscuro: la cinta es la misma, pero la fecha usa el gris de las plantillas
  // oscuras en vez del negro, para no abrir un agujero en la composición.
  function cintaTexto(st) {
    if (!on(st, 'etiquetas')) return '';
    const e = B(st, 'etiquetas');
    const dto = e.descuentoOn && String(e.descuento || '').trim();
    const fecha = e.hastaOn && String(e.hasta || '').trim();
    const partes = [];
    if (dto) partes.push(dto + ' de descuento');
    if (fecha) partes.push('solo hasta el ' + fecha);
    return partes.join(' · ');
  }

  // ── Plantilla A · "Cartelera" (oscura, como los decks) ──
  function plantillaA(st) {
    const P = [];
    const T = C.textDark, M = C.mutedDark;
    P.push(row(
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td valign="top">' + marca(st, true, 210) + '</td>' +
      '</tr></table>', 'padding:22px 28px 18px 28px;background:' + C.ink + ';border-bottom:1px solid ' + C.line + ';'));
    if (on(st, 'titulo')) {
      const b = B(st, 'titulo');
      P.push(row(
        '<div style="font-family:' + FH + ';font-size:11px;font-weight:700;letter-spacing:.16em;color:' + M + ';text-transform:uppercase;">' + esc(b.sub) + '</div>' +
        '<div style="font-family:' + FH + ';font-size:32px;line-height:36px;font-weight:800;color:#FFFFFF;padding:8px 0 14px 0;">' + esc(b.texto) + '</div>' +
        '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr><td width="56" height="4" bgcolor="' + C.orange + '" style="background:' + C.orange + ';font-size:0;line-height:0;">&nbsp;</td><td width="28" height="4" bgcolor="' + C.purple + '" style="background:' + C.purple + ';font-size:0;line-height:0;">&nbsp;</td></tr></table>',
        'padding:30px 28px 10px 28px;background:' + C.ink + ';'));
    }
    let body = '';
    if (on(st, 'saludo')) body += '<div style="font-family:' + FB + ';font-size:15px;line-height:22px;color:' + T + ';padding:0 0 10px 0;">' + nl2br(fill(B(st, 'saludo').texto, st)) + '</div>';
    if (on(st, 'intro')) body += '<div style="font-family:' + FB + ';font-size:15px;line-height:23px;color:' + M + ';">' + nl2br(fill(B(st, 'intro').texto, st)) + '</div>';
    if (body) P.push(row(body, 'padding:18px 28px 8px 28px;background:' + C.ink + ';'));
    const bqA = bloquePerfil(st, true);
    if (bqA) P.push(row(bqA, 'padding:6px 28px 16px 28px;background:' + C.ink + ';'));
    activos(st).forEach(s => {
      P.push(row(
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
        '<td width="200" valign="top" style="padding:0 18px 0 0;"><a href="' + esc(linkFor(st, s)) + '"><img src="' + esc(st.cardAnim && !usaPortadas(st) ? imgFor(st, 'carousel_' + s.id + '.gif') : svcImg(st, s)) + '" width="200" alt="' + esc(svcAlt(st, s)) + '" style="display:block;width:200px;height:auto;border-radius:6px;border:1px solid ' + C.line + ';color:#EEEDF2;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:13px;line-height:18px;"></a></td>' +
        '<td valign="top">' +
        '<div style="font-family:' + FH + ';font-size:10px;font-weight:700;letter-spacing:.16em;color:' + C.orange + ';text-transform:uppercase;">' + esc(s.eyebrow) + '</div>' +
        '<div style="font-family:' + FH + ';font-size:17px;line-height:22px;font-weight:800;color:#FFFFFF;padding:4px 0 4px 0;">' + esc(s.nombre) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + T + ';">' + esc(s.cobertura) + '</div>' +
        (s.nota ? '<div style="font-family:' + FB + ';font-size:12px;line-height:18px;color:' + M + ';padding:4px 0 0 0;">' + esc(s.nota) + '</div>' : '') +
        '<div style="padding:10px 0 0 0;"><a href="' + esc(linkFor(st, s)) + '" style="font-family:' + FH + ';font-size:13px;font-weight:700;color:' + C.purpleLight + ';text-decoration:none;">Ver presentación &rarr;</a></div>' +
        '</td></tr></table>',
        'padding:18px 28px;background:' + C.ink + ';border-top:1px solid ' + C.line + ';'));
    });
    if (on(st, 'suministro')) {
      const b = B(st, 'suministro');
      P.push(row(
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td width="4" bgcolor="' + C.orange + '" style="background:' + C.orange + ';font-size:0;">&nbsp;</td>' +
        '<td style="padding:14px 18px;background:' + C.ink2 + ';">' +
        '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:#FFFFFF;padding:0 0 6px 0;">' + esc(b.titulo) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + M + ';padding:0 0 8px 0;">' + nl2br(b.texto) + '</div>' +
        bullets(lines(b.requisitos), C.orange, T) + '</td></tr></table>',
        'padding:18px 28px 6px 28px;background:' + C.ink + ';'));
    }
    let steps = '';
    if (on(st, 'pasos')) {
      const b = B(st, 'pasos');
      steps += '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:#FFFFFF;padding:0 0 6px 0;">' + esc(b.titulo) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + M + ';padding:0 0 12px 0;">' + nl2br(b.texto) + '</div>';
    }
    if (on(st, 'presupuesto')) {
      const b = B(st, 'presupuesto');
      steps += '<div style="font-family:' + FB + ';font-size:14px;font-weight:700;color:' + T + ';padding:0 0 8px 0;">' + esc(b.titulo) + '</div>' + numbered(lines(b.items), C.orange, C.black, T);
    }
    if (steps) P.push(row(steps, 'padding:18px 28px 6px 28px;background:' + C.ink + ';'));
    if (on(st, 'cta')) P.push(row(button(B(st, 'cta').texto, B(st, 'cta').url, C.orange, C.black), 'padding:12px 28px 22px 28px;background:' + C.ink + ';'));
    let foot = '';
    if (on(st, 'cierre')) foot += '<div style="font-family:' + FB + ';font-size:15px;line-height:22px;color:' + T + ';padding:0 0 16px 0;">' + nl2br(B(st, 'cierre').texto) + '</div>';
    if (on(st, 'firma')) foot += firma(st, true);
    if (foot) P.push(row(foot, 'padding:20px 28px 26px 28px;background:' + C.ink + ';border-top:1px solid ' + C.line + ';'));
    if (on(st, 'pie')) P.push(row('<div style="font-family:' + FB + ';font-size:11px;line-height:16px;color:' + M + ';">' + nl2br(B(st, 'pie').texto) + '</div>', 'padding:14px 28px 0 28px;'));
    return doc(st, C.black, P.join(''));
  }

  // ── Plantilla B · "Catálogo" (clara, tarjetas en dos columnas) ──
  function plantillaB(st) {
    const P = [];
    P.push('<tr><td style="font-size:0;line-height:0;"><table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td width="60%" height="6" bgcolor="' + C.purple + '" style="background:' + C.purple + ';">&nbsp;</td><td height="6" bgcolor="' + C.orange + '" style="background:' + C.orange + ';">&nbsp;</td></tr></table></td></tr>');
    P.push(row(
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td valign="top">' + marca(st, false, 210) + '</td>' +
      '</tr></table>', 'padding:20px 28px;background:' + C.paper + ';border-bottom:1px solid ' + C.rule + ';'));
    let body = '';
    if (on(st, 'saludo')) body += '<div style="font-family:' + FB + ';font-size:15px;line-height:22px;color:' + C.text + ';padding:0 0 10px 0;">' + nl2br(fill(B(st, 'saludo').texto, st)) + '</div>';
    if (on(st, 'intro')) body += '<div style="font-family:' + FB + ';font-size:15px;line-height:23px;color:' + C.muted + ';">' + nl2br(fill(B(st, 'intro').texto, st)) + '</div>';
    if (body) P.push(row(body, 'padding:24px 28px 6px 28px;background:' + C.paper + ';'));
    if (on(st, 'titulo')) {
      const b = B(st, 'titulo');
      P.push(row('<div style="font-family:' + FH + ';font-size:24px;line-height:28px;font-weight:800;color:' + C.text + ';">' + esc(b.texto) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:13px;color:' + C.muted + ';padding:4px 0 0 0;">' + esc(b.sub) + '</div>', 'padding:18px 28px 6px 28px;background:' + C.paper + ';'));
    }
    const bqB = bloquePerfil(st, false);
    if (bqB) P.push(row(bqB, 'padding:6px 28px 16px 28px;background:' + C.paper + ';'));
    const act = activos(st);
    if (act.length) {
      // Las dos tarjetas de una fila tienen que acabar a la misma altura. Antes no lo hacían:
      // "Vallas" lleva una línea de texto y "Pantallas LED" tres, así que una terminaba antes y
      // dejaba un hueco blanco con el borde inferior desalineado.
      //
      // La solución que aguanta en correo es fijar la altura del bloque de texto con `height` en
      // el <td>, que Outlook y Gmail respetan. ALTO_TEXTO es el peor caso real del catálogo
      // (epígrafe + nombre en dos líneas + descripción en tres + enlace).
      const ALTO_TEXTO = 116;
      const foto = (s, w) => '<a href="' + esc(linkFor(st, s)) + '"><img src="' + esc(st.cardAnim && !usaPortadas(st) ? imgFor(st, 'carousel_' + s.id + '.gif') : svcImg(st, s)) + '" width="' + w + '" height="' + Math.round(w / 1.5) + '" alt="' + esc(svcAlt(st, s)) + '" style="display:block;width:100%;height:auto;color:#1F1B24;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:13px;line-height:18px;"></a>';
      const textos = (s) =>
        '<div style="font-family:' + FH + ';font-size:10px;font-weight:700;letter-spacing:.14em;color:' + C.orangeDark + ';text-transform:uppercase;">' + esc(s.eyebrow) + '</div>' +
        '<div style="font-family:' + FH + ';font-size:15px;line-height:20px;font-weight:800;color:' + C.text + ';padding:3px 0 3px 0;">' + esc(s.nombre) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:13px;line-height:19px;color:' + C.muted + ';">' + esc(s.cobertura) + (s.nota ? '<br>' + esc(s.nota) : '') + '</div>' +
        '<div style="padding:8px 0 0 0;"><a href="' + esc(linkFor(st, s)) + '" style="font-family:' + FH + ';font-size:12px;font-weight:700;color:' + C.purple + ';text-decoration:none;">Ver presentación &rarr;</a></div>';

      const card = (s, w) => '<table role="presentation" width="' + w + '" cellpadding="0" cellspacing="0" border="0" style="width:' + w + 'px;max-width:100%;">' +
        '<tr><td style="border:1px solid ' + C.rule + ';border-top:0;border-radius:8px;overflow:hidden;background:' + C.paper + ';">' +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">' +
        (on(st, 'etiquetas') ? '<tr><td style="font-size:0;line-height:0;">' + cintaEtiquetas(st, true, w) + '</td></tr>' : '') +
        '<tr><td style="font-size:0;line-height:0;">' + foto(s, w) + '</td></tr>' +
        '<tr><td height="' + ALTO_TEXTO + '" valign="top" style="height:' + ALTO_TEXTO + 'px;padding:12px 14px 14px 14px;">' + textos(s) + '</td></tr>' +
        '</table></td></tr></table>';

      // La tarjeta impar sobrante ya no se estira a ancho completo con una foto enorme: pasa a
      // ser un destacado horizontal, foto a la izquierda y texto a la derecha. Ocupa la fila
      // entera porque así estaba pensado, no porque sobrara.
      const destacado = (s) => '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:100%;">' +
        '<tr><td style="border:1px solid ' + C.rule + ';border-radius:8px;overflow:hidden;background:' + C.sand + ';">' +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
        '<td width="240" valign="top" style="font-size:0;line-height:0;width:240px;">' +
          (on(st, 'etiquetas') ? cintaEtiquetas(st, true, 240) : '') + foto(s, 240) + '</td>' +
        '<td valign="top" style="padding:16px 18px;">' + textos(s) +
          (cintaTexto(st) ? '<div style="font-family:' + FH + ';font-size:11px;font-weight:800;letter-spacing:.10em;text-transform:uppercase;color:' + C.orangeInk + ';padding:10px 0 0 0;">' + esc(cintaTexto(st)) + '</div>' : '') +
        '</td>' +
        '</tr></table></td></tr></table>';

      // Pares en filas de verdad: dos celdas de la misma <tr> comparten altura por definición,
      // que es lo que evita el borde desalineado. El 16 del medio es el aire entre columnas.
      let grid = '';
      const pares = [];
      for (let i = 0; i < act.length; i += 2) pares.push(act.slice(i, i + 2));
      pares.forEach(par => {
        if (par.length === 2) {
          grid += '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 16px 0;"><tr>' +
            '<td width="264" valign="top">' + card(par[0], 264) + '</td>' +
            '<td width="16" style="font-size:0;line-height:0;">&nbsp;</td>' +
            '<td width="264" valign="top">' + card(par[1], 264) + '</td>' +
            '</tr></table>';
        } else {
          grid += '<div style="padding:0 0 16px 0;">' + destacado(par[0]) + '</div>';
        }
      });
      P.push(row(grid, 'padding:12px 28px 0 28px;background:' + C.paper + ';'));
    }
    if (on(st, 'suministro')) {
      const b = B(st, 'suministro');
      P.push(row('<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + C.text + ';padding:0 0 6px 0;">' + esc(b.titulo) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + C.muted + ';padding:0 0 8px 0;">' + nl2br(b.texto) + '</div>' + bullets(lines(b.requisitos), C.orange, C.text),
        'padding:16px 20px;background:' + C.sand + ';border-radius:8px;'));
    }
    let steps = '';
    if (on(st, 'pasos')) {
      const b = B(st, 'pasos');
      steps += '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + C.text + ';padding:0 0 6px 0;">' + esc(b.titulo) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + C.muted + ';padding:0 0 12px 0;">' + nl2br(b.texto) + '</div>';
    }
    if (on(st, 'presupuesto')) {
      const b = B(st, 'presupuesto');
      steps += '<div style="font-family:' + FB + ';font-size:14px;font-weight:700;color:' + C.text + ';padding:0 0 8px 0;">' + esc(b.titulo) + '</div>' + numbered(lines(b.items), C.purple, '#FFFFFF', C.text);
    }
    if (steps) P.push(row(steps, 'padding:20px 28px 4px 28px;background:' + C.paper + ';'));
    if (on(st, 'cta')) P.push(row(button(B(st, 'cta').texto, B(st, 'cta').url, C.purple, '#FFFFFF'), 'padding:12px 28px 22px 28px;background:' + C.paper + ';'));
    let foot = '';
    if (on(st, 'cierre')) foot += '<div style="font-family:' + FB + ';font-size:15px;line-height:22px;color:' + C.text + ';padding:0 0 16px 0;">' + nl2br(B(st, 'cierre').texto) + '</div>';
    if (on(st, 'firma')) foot += firma(st, false);
    if (foot) P.push(row(foot, 'padding:20px 28px 26px 28px;background:' + C.paper + ';border-top:1px solid ' + C.rule + ';'));
    if (on(st, 'pie')) P.push(row('<div style="font-family:' + FB + ';font-size:11px;line-height:16px;color:' + C.muted + ';">' + nl2br(B(st, 'pie').texto) + '</div>', 'padding:14px 28px 0 28px;'));
    return doc(st, C.sand, P.join(''));
  }

  // ── Plantilla C · "Nota" (compacta, parece un correo personal; para responder en hilo) ──
  function plantillaC(st) {
    const P = [];
    let body = '';
    if (on(st, 'saludo')) body += '<p style="margin:0 0 12px 0;font-family:' + FB + ';font-size:15px;line-height:23px;color:' + C.text + ';">' + nl2br(fill(B(st, 'saludo').texto, st)) + '</p>';
    if (on(st, 'intro')) body += '<p style="margin:0 0 18px 0;font-family:' + FB + ';font-size:15px;line-height:23px;color:' + C.text + ';">' + nl2br(fill(B(st, 'intro').texto, st)) + '</p>';
    if (on(st, 'titulo')) body += '<p style="margin:0 0 10px 0;font-family:' + FH + ';font-size:13px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:' + C.purple + ';">' + esc(B(st, 'titulo').texto) + '</p>';
    const bqC = bloquePerfil(st, false);
    if (bqC) body += '<div style="padding:2px 0 14px 0;">' + bqC + '</div>';
    activos(st).forEach(s => {
      body += '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 10px 0;"><tr>' +
        '<td width="84" valign="top"><a href="' + esc(linkFor(st, s)) + '"><img src="' + esc(svcImg(st, s)) + '" width="72" alt="' + esc(svcAlt(st, s)) + '" style="display:block;width:72px;height:auto;border-radius:4px;color:#1F1B24;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:13px;line-height:18px;"></a></td>' +
        '<td valign="top" style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + C.text + ';">' +
        '<b>' + esc(s.nombre) + '</b> &mdash; ' + esc(s.cobertura) + ' &mdash; <a href="' + esc(linkFor(st, s)) + '" style="color:' + C.purple + ';">Ver presentación</a>' +
        (s.nota ? '<br><span style="font-size:12px;color:' + C.muted + ';">' + esc(s.nota) + '</span>' : '') +
        '</td></tr></table>';
    });
    if (on(st, 'suministro')) {
      const b = B(st, 'suministro');
      body += '<p style="margin:14px 0 4px 0;font-family:' + FB + ';font-size:14px;line-height:20px;color:' + C.text + ';"><b>' + esc(b.titulo) + '.</b> ' + esc(b.texto) + ' ' + lines(b.requisitos).map(esc).join(' · ') + '.</p>';
    }
    if (on(st, 'pasos')) {
      const b = B(st, 'pasos');
      body += '<p style="margin:14px 0 4px 0;font-family:' + FB + ';font-size:14px;line-height:20px;color:' + C.text + ';"><b>' + esc(b.titulo) + '.</b> ' + esc(b.texto) + '</p>';
    }
    if (on(st, 'presupuesto')) {
      const b = B(st, 'presupuesto');
      body += '<p style="margin:10px 0 4px 0;font-family:' + FB + ';font-size:14px;line-height:20px;color:' + C.text + ';">' + esc(b.titulo) + ':</p>' +
        '<ol style="margin:0 0 14px 0;padding:0 0 0 22px;font-family:' + FB + ';font-size:14px;line-height:21px;color:' + C.text + ';">' + lines(b.items).map(t => '<li>' + esc(t) + '</li>').join('') + '</ol>';
    }
    if (on(st, 'cta')) body += '<div style="padding:4px 0 18px 0;">' + button(B(st, 'cta').texto, B(st, 'cta').url, C.orange, C.black) + '</div>';
    if (on(st, 'cierre')) body += '<p style="margin:0 0 18px 0;font-family:' + FB + ';font-size:15px;line-height:23px;color:' + C.text + ';">' + nl2br(B(st, 'cierre').texto) + '</p>';
    if (on(st, 'firma')) body += firma(st, false);
    if (on(st, 'pie')) body += '<p style="margin:18px 0 0 0;font-family:' + FB + ';font-size:11px;line-height:16px;color:' + C.muted + ';">' + nl2br(B(st, 'pie').texto) + '</p>';
    P.push(row(body, 'padding:8px 4px;background:' + C.paper + ';'));
    return doc(st, C.paper, P.join(''));
  }

  // ── Plantilla D · "Cartelera móvil" (una columna, foto arriba, tipografía grande, un solo botón principal) ──
  function plantillaD(st) {
    const P = [];
    const T = C.textDark, M = C.mutedDark;
    const txt = (s, size, color, extra) => '<div style="font-family:' + FB + ';font-size:' + size + 'px;line-height:' + Math.round(size * 1.5) + 'px;color:' + color + ';' + (extra || '') + '">' + s + '</div>';
    const eyebrow = s => '<div style="font-family:' + FH + ';font-size:12px;font-weight:700;letter-spacing:.12em;color:' + C.orange + ';text-transform:uppercase;">' + esc(s) + '</div>';
    const pill = (text, url, solid) => '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td align="center" bgcolor="' + (solid ? C.orange : C.ink2) + '" style="background:' + (solid ? C.orange : C.ink2) + ';border:2px solid ' + C.orange + ';border-radius:30px;">' +
      '<a href="' + esc(url) + '" style="display:block;padding:15px 20px;font-family:' + FH + ';font-size:16px;font-weight:800;color:' + (solid ? C.black : C.orange) + ';text-decoration:none;">' + esc(text) + '</a></td></tr></table>';
    const foto = (src, alt, url) => '<a href="' + esc(url) + '"><img src="' + esc(src) + '" width="544" alt="' + esc(alt) + '" style="display:block;width:100%;max-width:100%;height:auto;border-radius:10px 10px 0 0;color:#EEEDF2;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:13px;line-height:18px;"></a>';
    const dark = 'background:' + C.ink + ';';

    // Cabecera de marca
    P.push(row('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td valign="top">' + marca(st, true, 168) + '</td>' +
      '<td align="right" valign="top" style="font-family:' + FH + ';font-size:11px;font-weight:700;letter-spacing:.14em;color:' + C.orange + ';padding:4px 0 0 0;">DISPONIBILIDAD</td>' +
      '</tr></table>', 'padding:18px 24px;' + dark));
    // Foto de cabecera + titular
    if (on(st, 'hero')) {
      const h = B(st, 'hero');
      // Cabecera animada (GIF de HyperFrames) si heroAnim está activo; si no, la foto fija.
      const src = imgFor(st, st.heroAnim && h.anim ? h.anim : (usaPortadas(st) && h.imgPortada ? h.imgPortada : h.img));
      P.push(row('<img src="' + esc(src) + '" width="600" alt="' + esc(h.alt) + '" style="display:block;width:100%;max-width:100%;height:auto;color:#EEEDF2;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:13px;line-height:18px;">', 'font-size:0;line-height:0;' + dark));
    }
    if (on(st, 'titulo')) {
      const b = B(st, 'titulo');
      P.push(row(eyebrow(b.sub) +
        '<div style="font-family:' + FH + ';font-size:30px;line-height:36px;font-weight:800;color:#FFFFFF;padding:8px 0 0 0;">' + esc(b.texto) + '</div>',
        'padding:24px 24px 8px 24px;' + dark));
    }
    let intro = '';
    if (on(st, 'saludo')) intro += txt(nl2br(fill(B(st, 'saludo').texto, st)), 17, T, 'padding:0 0 10px 0;');
    if (on(st, 'intro')) intro += txt(nl2br(fill(B(st, 'intro').texto, st)), 16, M);
    if (intro) P.push(row(intro, 'padding:12px 24px 10px 24px;' + dark));

    // Bloques de servicio agrupados (foto arriba, texto debajo, un botón por grupo)
    const bqD = bloquePerfil(st, true);
    if (bqD) P.push(row(bqD, 'padding:6px 24px 14px 24px;' + dark));
    const act = activos(st);
    GRUPOS.forEach(g => {
      const items = g.servicios.map(id => act.find(s => s.id === id)).filter(Boolean);
      if (!items.length) return;
      const lead = items[0];
      let card = foto(svcImg(st, lead), svcAlt(st, lead), linkFor(st, lead)) +
        '<div style="padding:18px 20px 20px 20px;">' + eyebrow(g.eyebrow) +
        '<div style="font-family:' + FH + ';font-size:22px;line-height:28px;font-weight:800;color:#FFFFFF;padding:6px 0 8px 0;">' + esc(items.length === 1 ? lead.nombre : g.titulo) + '</div>';
      if (items.length === 1) {
        card += txt(esc(lead.cobertura), 16, T) + (lead.nota ? txt(esc(lead.nota), 14, M, 'padding:4px 0 0 0;') : '');
      } else {
        card += items.map(s => '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 8px 0;"><tr>' +
          '<td valign="top" style="font-family:' + FB + ';font-size:16px;line-height:24px;color:' + T + ';"><b>' + esc(s.nombre) + '</b><br><span style="color:' + M + ';font-size:14px;">' + esc(s.cobertura) + '</span></td>' +
          '<td width="70" align="right" valign="top" style="padding:2px 0 0 10px;"><a href="' + esc(linkFor(st, s)) + '" style="font-family:' + FH + ';font-size:13px;font-weight:700;color:' + C.orange + ';text-decoration:none;white-space:nowrap;">Ver &rarr;</a></td>' +
          '</tr></table>').join('');
      }
      card += '<div style="padding:14px 0 0 0;">' + pill(lead.cta || 'Ver presentación', linkFor(st, lead), false) + '</div></div>';
      P.push(row('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td bgcolor="' + C.ink2 + '" style="background:' + C.ink2 + ';border-radius:10px;">' + card + '</td></tr></table>', 'padding:10px 28px;' + dark));
    });
    if (on(st, 'branding')) {
      const b = B(st, 'branding');
      P.push(row('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr><td bgcolor="' + C.ink2 + '" style="background:' + C.ink2 + ';border-radius:10px;padding:18px 20px 20px 20px;">' +
        eyebrow('Branding') + '<div style="font-family:' + FH + ';font-size:22px;line-height:28px;font-weight:800;color:#FFFFFF;padding:6px 0 8px 0;">' + esc(b.titulo) + '</div>' +
        txt(nl2br(b.texto), 16, T) + '<div style="padding:14px 0 0 0;">' + pill(b.cta, b.url, false) + '</div></td></tr></table>', 'padding:10px 28px;' + dark));
    }

    // Bloque final: qué enviar para cotizar + botón principal
    let fin = '';
    if (on(st, 'pasos')) { const b = B(st, 'pasos'); fin += '<div style="font-family:' + FH + ';font-size:22px;font-weight:800;color:#FFFFFF;padding:0 0 8px 0;">' + esc(b.titulo) + '</div>' + txt(nl2br(b.texto), 16, M, 'padding:0 0 14px 0;'); }
    if (on(st, 'presupuesto')) { const b = B(st, 'presupuesto'); fin += txt('<b>' + esc(b.titulo) + '</b>', 16, T, 'padding:0 0 8px 0;') + numbered(lines(b.items), C.orange, C.black, T); }
    if (on(st, 'suministro')) { const b = B(st, 'suministro'); fin += txt('Para proyectos de branding e instalación: ' + lines(b.requisitos).map(esc).join(' · ') + '.', 14, M, 'padding:6px 0 0 0;'); }
    if (on(st, 'cta')) fin += '<div style="padding:20px 0 4px 0;">' + pill(B(st, 'cta').texto, B(st, 'cta').url, true) + '</div>';
    if (fin) P.push(row(fin, 'padding:22px 28px 16px 28px;' + dark));

    let foot = '';
    if (on(st, 'cierre')) foot += txt(nl2br(B(st, 'cierre').texto), 16, T, 'padding:0 0 16px 0;');
    if (on(st, 'firma')) {
      const f = B(st, 'firma');
      foot += firma(st, true);
    }
    if (foot) P.push(row(foot, 'padding:20px 28px 26px 28px;border-top:1px solid ' + C.line + ';' + dark));
    if (on(st, 'pie')) P.push(row(txt(nl2br(B(st, 'pie').texto), 12, M), 'padding:14px 28px 0 28px;'));
    return doc(st, C.black, P.join(''));
  }

  // ── Texto plano (fallback y para clientes sin HTML) ──
  function renderText(st0) {
    const st = aplicaPerfil(st0);
    const L = [];
    if (on(st, 'saludo')) L.push(fill(B(st, 'saludo').texto, st), '');
    if (on(st, 'intro')) L.push(fill(B(st, 'intro').texto, st), '');
    if (on(st, 'titulo')) L.push(B(st, 'titulo').texto.toUpperCase(), '');
    activos(st).forEach(s => { L.push('• ' + s.nombre + ' — ' + s.cobertura + ' — ' + linkFor(st, s)); if (s.nota) L.push('  ' + s.nota); });
    if (activos(st).length) L.push('');
    if (on(st, 'suministro')) { const b = B(st, 'suministro'); L.push(b.titulo + ': ' + b.texto + ' ' + lines(b.requisitos).join(' / '), ''); }
    if (on(st, 'pasos')) { const b = B(st, 'pasos'); L.push(b.titulo, b.texto, ''); }
    if (on(st, 'presupuesto')) { const b = B(st, 'presupuesto'); L.push(b.titulo + ':'); lines(b.items).forEach((t, i) => L.push((i + 1) + ') ' + t)); L.push(''); }
    if (on(st, 'cierre')) L.push(B(st, 'cierre').texto, '');
    if (on(st, 'firma')) { const f = B(st, 'firma'); L.push(f.nombre, f.cargo, f.email + ' · ' + f.telefono); if (f.contacto) L.push(f.contacto); L.push(f.ig + ' · ' + webHref(f.web) + ' · ' + f.direccion); }
    return L.join('\n');
  }

  // ── Plantilla E · "Marquesina" ──────────────────────────────────────────────────────
  // Propuesta propia, distinta de las otras cuatro a propósito.
  //
  // La idea: un correo de publicidad exterior no debería parecer una tienda en línea. A, B y D
  // son variaciones de lo mismo —una rejilla de fichas de producto— y eso ya lo hace todo el
  // mundo. Aquí se invierte la jerarquía: **manda el dato, no el nombre**. Quien compra exterior
  // no compara títulos bonitos, compara impactos por día y medidas; así que el número va grande y
  // el nombre del espacio debajo, pequeño.
  //
  // La composición imita el propio medio: bandas anchas que se alternan izquierda y derecha, como
  // vallas que van pasando, separadas por un filete morado→naranja que hace de eje. Sin tarjetas,
  // sin cajas iguales, sin rejilla.
  function plantillaE(st) {
    const P = [];
    const dark = 'background:' + C.ink + ';';
    const filete = '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td width="38%" height="3" bgcolor="' + C.purple + '" style="background:' + C.purple + ';font-size:0;line-height:0;">&nbsp;</td>' +
      '<td height="3" bgcolor="' + C.orange + '" style="background:' + C.orange + ';font-size:0;line-height:0;">&nbsp;</td>' +
      '</tr></table>';

    P.push(row(filete, 'font-size:0;line-height:0;'));
    P.push(row(marca(st, true, 210), 'padding:24px 30px 18px 30px;' + dark));

    // Titular a escala de cartel: el mayor contraste tipográfico de todas las plantillas.
    if (on(st, 'titulo')) {
      const b = B(st, 'titulo');
      P.push(row(
        '<div style="font-family:' + FH + ';font-size:11px;font-weight:800;letter-spacing:.20em;text-transform:uppercase;color:' + C.orange + ';padding:0 0 10px 0;">' + esc(b.sub) + '</div>' +
        '<div style="font-family:' + FH + ';font-size:38px;line-height:40px;font-weight:800;letter-spacing:-.03em;color:#FFFFFF;">' + esc(b.texto) + '</div>',
        'padding:6px 30px 18px 30px;' + dark));
    }

    let entrada = '';
    if (on(st, 'saludo')) entrada += '<div style="font-family:' + FB + ';font-size:15px;line-height:23px;color:' + C.textDark + ';padding:0 0 10px 0;">' + nl2br(fill(B(st, 'saludo').texto, st)) + '</div>';
    if (on(st, 'intro')) entrada += '<div style="font-family:' + FB + ';font-size:15px;line-height:24px;color:' + C.mutedDark + ';">' + nl2br(fill(B(st, 'intro').texto, st)) + '</div>';
    if (entrada) P.push(row(entrada, 'padding:0 30px 20px 30px;' + dark));

    const bqE = bloquePerfil(st, true);
    if (bqE) P.push(row(bqE, 'padding:0 30px 18px 30px;' + dark));

    // Las bandas. El lado de la foto alterna para romper la lectura en columna.
    const act = activos(st);
    act.forEach((s, i) => {
      const f = FICHA[s.id] || {};
      const izquierda = i % 2 === 0;
      const precio = desdeDe(st, s.id);

      const foto = '<td width="228" valign="top" style="width:228px;font-size:0;line-height:0;padding:0;">' +
        '<table role="presentation" width="228" cellpadding="0" cellspacing="0" border="0" style="width:228px;">' +
        (on(st, 'etiquetas') ? '<tr><td style="font-size:0;line-height:0;">' + cintaEtiquetas(st, true, 228) + '</td></tr>' : '') +
        '<tr><td style="font-size:0;line-height:0;">' +
        '<a href="' + esc(linkFor(st, s)) + '"><img src="' + esc(st.cardAnim && !usaPortadas(st) ? imgFor(st, 'carousel_' + s.id + '.gif') : svcImg(st, s)) + '" width="228" height="152" alt="' + esc(svcAlt(st, s)) + '" style="display:block;width:228px;max-width:100%;height:auto;border-radius:6px;color:' + C.textDark + ';font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:13px;line-height:18px;"></a>' +
        '</td></tr></table></td>';

      // El dato primero, a tamaño de titular. Si el espacio no tiene ficha, el nombre ocupa su
      // sitio: la banda no se queda coja, simplemente cambia de protagonista.
      const datos = '<td valign="middle" style="padding:' + (izquierda ? '2px 0 2px 20px' : '2px 20px 2px 0') + ';">' +
        (f.trafico
          ? '<div style="font-family:' + FH + ';font-size:26px;line-height:28px;font-weight:800;letter-spacing:-.02em;color:' + C.orange + ';">' + esc(f.trafico) + '</div>'
          : '') +
        '<div style="font-family:' + FH + ';font-size:17px;line-height:22px;font-weight:800;color:#FFFFFF;padding:' + (f.trafico ? '6px' : '0') + ' 0 0 0;">' + esc(s.nombre) + '</div>' +
        '<div style="font-family:' + FH + ';font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:' + C.purpleLight + ';padding:5px 0 0 0;">' + esc(s.eyebrow) + (f.medida ? ' &middot; ' + esc(f.medida) : '') + '</div>' +
        '<div style="font-family:' + FB + ';font-size:13px;line-height:19px;color:' + C.mutedDark + ';padding:7px 0 0 0;">' + esc(s.cobertura) + (s.nota ? '<br>' + esc(s.nota) : '') + '</div>' +
        (precio ? '<div style="font-family:' + FH + ';font-size:12px;font-weight:800;letter-spacing:.06em;text-transform:uppercase;color:' + C.orange + ';padding:7px 0 0 0;">' + esc(precio) + '</div>' : '') +
        '<div style="padding:10px 0 0 0;"><a href="' + esc(linkFor(st, s)) + '" style="font-family:' + FH + ';font-size:12px;font-weight:800;letter-spacing:.04em;color:' + C.orange + ';text-decoration:none;">Ver presentación &rarr;</a></div>' +
        '</td>';

      P.push(row('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
        (izquierda ? foto + datos : datos + foto) +
        '</tr></table>', 'padding:18px 30px;' + dark));

      if (i < act.length - 1) P.push(row(filete, 'padding:0 30px;font-size:0;line-height:0;' + dark));
    });

    // Cierre operativo, en tono menor para que no compita con las bandas.
    let ficha = '';
    if (on(st, 'suministro')) {
      const b = B(st, 'suministro');
      ficha += '<div style="font-family:' + FH + ';font-size:14px;font-weight:800;color:#FFFFFF;padding:0 0 6px 0;">' + esc(b.titulo) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:13px;line-height:19px;color:' + C.mutedDark + ';padding:0 0 8px 0;">' + nl2br(b.texto) + '</div>' +
        bullets(lines(b.requisitos), C.orange, C.textDark);
    }
    if (on(st, 'presupuesto')) {
      const b = B(st, 'presupuesto');
      ficha += '<div style="font-family:' + FH + ';font-size:14px;font-weight:800;color:#FFFFFF;padding:14px 0 8px 0;">' + esc(b.titulo) + '</div>' +
        numbered(lines(b.items), C.orange, '#141016', C.textDark);
    }
    if (ficha) P.push(row(ficha, 'padding:16px 30px 20px 30px;background:' + C.ink2 + ';'));

    // Llamada a la acción a sangre: una barra naranja de lado a lado. Es el único naranja grande
    // del correo, así que el ojo va ahí sin discusión.
    if (on(st, 'cta')) {
      const b = B(st, 'cta');
      P.push(row(
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
        '<td align="center" bgcolor="' + C.orange + '" style="background:' + C.orange + ';padding:20px 24px;">' +
        (cintaTexto(st) ? '<div style="font-family:' + FH + ';font-size:11px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:#141016;padding:0 0 8px 0;">' + esc(cintaTexto(st)) + '</div>' : '') +
        '<a href="' + esc(b.url) + '" style="font-family:' + FH + ';font-size:19px;line-height:24px;font-weight:800;letter-spacing:-.01em;color:#141016;text-decoration:none;">' + esc(b.texto) + ' &rarr;</a>' +
        '</td></tr></table>', 'font-size:0;line-height:0;'));
    }

    let pie = '';
    if (on(st, 'cierre')) pie += '<div style="font-family:' + FB + ';font-size:15px;line-height:23px;color:' + C.textDark + ';padding:0 0 16px 0;">' + nl2br(B(st, 'cierre').texto) + '</div>';
    if (on(st, 'firma')) pie += firma(st, true);
    if (pie) P.push(row(pie, 'padding:22px 30px 24px 30px;' + dark));
    if (on(st, 'pie')) P.push(row('<div style="font-family:' + FB + ';font-size:11px;line-height:16px;color:' + C.mutedDark + ';">' + nl2br(B(st, 'pie').texto) + '</div>', 'padding:14px 30px 0 30px;'));

    return doc(st, C.black, P.join(''));
  }

  const TEMPLATES = {
    A: { nombre: 'Cartelera', desc: 'Oscura, misma identidad que los decks. Para primer envío.', fn: plantillaA },
    B: { nombre: 'Catálogo', desc: 'Clara, tarjetas en dos columnas. Para lectura rápida.', fn: plantillaB },
    C: { nombre: 'Nota', desc: 'Compacta, parece un correo personal. Para responder en hilo.', fn: plantillaC },
    D: { nombre: 'Cartelera móvil', desc: 'Una columna, foto arriba, tipografía grande y un solo botón principal. Pensada para Gmail en el teléfono.', fn: plantillaD },
    E: { nombre: 'Marquesina', desc: 'Propuesta nueva: bandas alternadas, sin rejilla de tarjetas. Manda el dato (impactos/día) y el nombre va debajo. Para cuando hay que impresionar.', fn: plantillaE },
  };
  function pick(st) {
    if (st.plantilla && TEMPLATES[st.plantilla]) return st.plantilla;
    const keys = Object.keys(TEMPLATES);
    return keys[Math.abs(Number(st.seed) || 0) % keys.length];
  }
  const render = (st, key) => TEMPLATES[key || pick(st)].fn(aplicaPerfil(st));

  return { C, SERVICIOS, GRUPOS, TEMPLATES, IMG_SETS, PERFILES, FICHA, CONTENT_VERSION, defaultState, render, renderText, pick, aplicaPerfil };
});
