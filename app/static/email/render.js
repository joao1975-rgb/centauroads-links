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
    { id: 'led', nombre: 'Pantalla LED Chacao', eyebrow: 'Digital outdoor', cta: 'Consultar disponibilidad',
      cobertura: 'Ubicación: Chacao · Av. Francisco de Miranda',
      nota: 'Servicio de videos (por cotizar) · Alquiler y venta de pantallas LED',
      slug: 'pantallas-led', canva: 'https://canva.link/p69pybf8jctaq8d',
      img: 'svc_led.jpg', alt: 'Pantalla LED vertical de Chacao, Av. Francisco de Miranda con Calle Elice',
      cover: 'cover_led.jpg', altCover: 'Portada: Circuito pantallas LED Chacao y Las Mercedes' },
    { id: 'mercedes', nombre: 'Pantalla LED Las Mercedes', eyebrow: 'Digital outdoor', cta: 'Consultar disponibilidad',
      cobertura: 'Ubicación: Las Mercedes · Av. Paseo Enrique Erazo',
      nota: 'Formato horizontal · transmisión 24 horas',
      slug: 'pantalla-las-mercedes', canva: 'https://canva.link/p69pybf8jctaq8d',
      img: 'svc_mercedes.jpg', alt: 'Pantalla LED horizontal bajo el elevado de la Av. Paseo Enrique Erazo, Las Mercedes',
      cover: 'cover_mercedes.jpg', altCover: 'Ficha técnica: Pantalla LED Las Mercedes' },
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
  ];

  // ── Grupos de la plantilla D (taxonomía del flyer "Servicios de publicidad exterior") ──
  const GRUPOS = [
    { id: 'vallas', eyebrow: 'Gran formato', titulo: 'Vallas (OOH)', servicios: ['vallas'] },
    { id: 'dooh', eyebrow: 'Digital outdoor', titulo: 'Pantallas LED y Tótem (DOOH)', servicios: ['led', 'mercedes', 'totem'] },
    { id: 'movil', eyebrow: 'Movilidad', titulo: 'Publicidad móvil · Rider Clon', servicios: ['rider'] },
  ];


  // ── Ficha tecnica de cada espacio (datos reales de los decks de Canva) ──
  // Se usan en la tabla de disponibilidad del perfil de agencias y en los precios "desde".
  // El cargo que va DEBAJO del nombre en la firma. Dos opciones, a peticion.
  const ROLES = {
    alianzas:  'Alianzas Comerciales',
    directora: 'Directora',
  };

  // Que correo se ensena en la firma. Por defecto el de mercadeo, que es la cuenta de la
  // casa: si alguien cambia de puesto el correo sigue funcionando. El personal y los dos
  // juntos quedan como opcion.
  const CORREOS = {
    mercadeo: 'Solo el de mercadeo',
    personal: 'Solo el personal',
    ambos:    'Los dos',
  };

  // El texto del cargo, compuesto. La empresa se anade aqui y no se escribe a mano.
  function cargoDe(f) {
    return (ROLES[f.rol] || ROLES.alianzas) + ' \u00b7 Centauro ADS';
  }

  // Los correos que toca ensenar, en orden. Nunca devuelve vacio: una firma sin correo
  // no sirve de nada.
  function correosDe(f) {
    const casa = f.contacto || 'mercadeo@centauroads.com';
    const propio = f.email || '';
    if (f.correo === 'personal' && propio) return [propio];
    if (f.correo === 'ambos') return propio ? [casa, propio] : [casa];
    return [casa];
  }

  const FICHA = {
    led:     { ubic: 'Chacao · Av. F. de Miranda',   medida: '1024 × 2048 px',        trafico: '120.000 impactos/día', desde: '1.500' },
    mercedes: { ubic: 'Las Mercedes · Av. P. Enrique Erazo', medida: '1920 × 1200 px', trafico: '95.000 vehículos/día', desde: '' },
    vallas:  { ubic: 'Caracas y nivel nacional',      medida: 'Según ubicación',   trafico: 'Alta rotación vial',   desde: '' },
    totem:   { ubic: 'C.C. San Ignacio',              medida: '1440 × 2560 px', trafico: '240 salidas/día',      desde: '300' },
    rider:   { ubic: 'Caracas · San Antonio · Valencia', medida: '0,42 × 0,59 m',  trafico: '250 motos · 8 h/día',  desde: '1.500' },
  };

  // ── Perfiles de cliente ──
  // Un correo no dice lo mismo a una agencia que compra medios cada semana que a una marca que nunca
  // ha anunciado en la calle. El perfil cambia asunto, texto de entrada, ORDEN de los servicios, el
  // bloque propio de cada audiencia y la llamada a la accion. El formato (A/B/C/D) es independiente.
  // Tres asuntos por perfil, con angulos distintos a proposito: el asunto es lo unico
  // que se ve antes de abrir, y el que funciona depende de a quien se escribe.
  //   directo    - dice que hay dentro, sin adornos. El que menos falla.
  //   beneficio  - nombra lo que el lector gana.
  //   curiosidad - abre un hueco que solo se cierra abriendo. El que mas arriesga.
  // Banco de imagenes por servicio.
  //
  // Va escrito porque el motor corre en el navegador y no puede mirar el disco. Es el
  // inventario real: comprobado contra img/ y contra lo que sirve produccion en
  // app/static/email/. Si se anade una foto al disco hay que anadirla tambien aqui.
  //
  // Los VIDEOS no se incrustan: ningun cliente de correo reproduce video de forma
  // fiable. Lo que se manda es un fotograma que enlaza al video completo, que es lo
  // unico que funciona en Gmail y en Outlook a la vez.
  const BANCO = {
    vallas:  { fotos: ['svc_vallas.jpg', 'svc_vallas_alt.jpg', 'svc_vallas_alt2.jpg'], videos: [] },
    led:     { fotos: ['svc_led.jpg', 'svc_led_alt.jpg', 'svc_led_alt2.jpg'],
               videos: [
                 { poster: 'svc_led_vid1.jpg', etiqueta: 'Pantalla LED Chacao \u00b7 fotograma 1' },
                 { poster: 'svc_led_vid2.jpg', etiqueta: 'Pantalla LED Chacao \u00b7 fotograma 2' },
               ],
               // Pendiente y sin resolver: estos dos fotogramas son de @nanopopcast, llevan
               // su marca de agua y el permiso de uso comercial NO esta concedido. Por eso
               // el video viene apagado de serie y el panel lo avisa.
               aviso: 'Fotogramas de @nanopopcast: llevan marca de agua y el permiso de uso comercial sigue pendiente.' },
    mercedes: { fotos: ['svc_mercedes.jpg', 'svc_mercedes_alt.jpg'], videos: [] },
    totem:   { fotos: ['svc_totem.jpg', 'svc_totem_alt.jpg', 'svc_totem_alt2.jpg'], videos: [] },
    rider:   { fotos: ['svc_rider.jpg', 'svc_rider_alt.jpg', 'svc_rider_alt2.jpg'], videos: [] },
  };

  // Lo que hay disponible para un servicio, con los tres huecos libres ya unidos.
  function bancoDe(st, s) {
    const fijo = BANCO[s.id] || { fotos: [s.img], videos: [] };
    const mio = (st.banco && st.banco[s.id]) || {};
    const extra = (mio.extra || []).filter(x => x && x.trim());
    return {
      fotos: fijo.fotos,
      videos: fijo.videos || [],
      aviso: fijo.aviso || '',
      extra: extra,
      video: mio.video || { poster: '', enlace: '' },
    };
  }

  // Las fotos que entran de verdad en el carrusel: las marcadas mas los huecos usados.
  // Sin marcar ninguna entran todas, que es como se comportaba antes de existir el banco.
  function fotosDe(st, s) {
    const b = bancoDe(st, s);
    const mio = (st.banco && st.banco[s.id]) || {};
    const marcadas = (mio.usar && mio.usar.length)
      ? b.fotos.filter(f => mio.usar.indexOf(f) >= 0)
      : b.fotos.slice();
    return marcadas.concat(b.extra);
  }

  // El comando exacto que regenera el carrusel de un servicio con lo que se ha marcado.
  // El GIF esta hecho de antemano: marcar fotos aqui no cambia el fichero hasta que se
  // vuelve a generar, y el panel ensena el comando en vez de fingir que ya esta hecho.
  function comandoCarrusel(st, s) {
    return 'python carrusel_gif.py --servicio ' + s.id + ' --efecto ' + efectoDe(st, s) +
           ' --imagenes ' + fotosDe(st, s).join(' ');
  }

  // Banco de efectos de animacion para el carrusel de cada servicio.
  //
  // El correo no ejecuta JavaScript y las animaciones CSS no llegan a Gmail ni a Outlook:
  // el GIF es lo unico que se mueve en todos los clientes. Cada efecto se genera con
  // carrusel_gif.py y se guarda como carousel_<servicio>_<efecto>.gif.
  //
  // El campo "kb" es el peso MEDIDO fichero a fichero, no una estimacion, y va POR
  // SERVICIO porque depende de las fotos y de cuantas hay: el mismo efecto pesa 667 KB
  // en LED y 888 KB en Vallas. Esta aqui a proposito: quien elige tiene que ver lo
  // que le cuesta a quien abre el correo con datos moviles.
  //
  // "servido" dice si el GIF esta subido a app/static/email/. Seis lo estan. El zoom
  // no: sus cuatro ficheros pesan 8 MB, mas de la mitad que los otros seis juntos, y
  // meter eso en la historia de un repositorio publico es permanente. Se sigue
  // ofreciendo porque la eleccion informada es justamente para esto, pero hay que
  // generarlo y subirlo antes de usarlo, y el panel lo dice.
  const EFECTOS = [
    { clave: 'corte', servido: true, etiqueta: 'Corte',
      kb: { led: 245, mercedes: 198, vallas: 310, totem: 301, rider: 250 },
      idea: 'Cambio seco, sin transicion. El mas ligero y el que mejor aguanta conexiones lentas.' },
    { clave: 'barrido', servido: true, etiqueta: 'Barrido',
      kb: { led: 355, mercedes: 320, vallas: 426, totem: 392, rider: 342 },
      idea: 'Una linea vertical descubre la foto siguiente, como el giro de una valla rotativa.' },
    { clave: 'persiana', servido: true, etiqueta: 'Persiana',
      kb: { led: 405, mercedes: 356, vallas: 477, totem: 458, rider: 409 },
      idea: 'La foto nueva entra en franjas horizontales. El mas llamativo de los ligeros.' },
    { clave: 'fundido', servido: true, etiqueta: 'Fundido',
      kb: { led: 667, mercedes: 597, vallas: 888, totem: 789, rider: 697 },
      idea: 'Una foto se disuelve en la siguiente. El mas neutro: no compite con el texto.' },
    { clave: 'deslizar', servido: true, etiqueta: 'Deslizar',
      kb: { led: 669, mercedes: 563, vallas: 860, totem: 758, rider: 634 },
      idea: 'La foto nueva empuja a la anterior. Sensacion de recorrido entre soportes.' },
    { clave: 'destello', servido: true, etiqueta: 'Destello',
      kb: { led: 672, mercedes: 581, vallas: 890, totem: 817, rider: 699 },
      idea: 'Un brillo diagonal cruza la foto antes del cambio. Lee metalico, va con promociones.' },
    { clave: 'zoom', servido: false, etiqueta: 'Zoom',
      kb: { led: 1784, mercedes: 1590, vallas: 2511, totem: 2188, rider: 1820 },
      idea: 'Acercamiento lento sobre cada foto. PESA MUCHO y no tiene arreglo: el acercamiento ' +
            'cambia la imagen entera en cada paso y la compresion no puede reutilizar nada. En ' +
            'Vallas son 2,5 MB, que en datos moviles no se abre. El zoom de las etiquetas de ' +
            'oferta es otra animacion distinta y si es ligera (25 KB).' },
  ];

  // El peso REAL de un efecto en un servicio concreto, en KB.
  function pesoDe(clave, s) {
    const e = EFECTOS.filter(function (x) { return x.clave === clave; })[0];
    if (!e) return 0;
    return e.kb[s.id] || 0;
  }

  // Lo que pesa el mas ligero y el mas pesado de un efecto, para ensenar el rango.
  function rangoPeso(clave) {
    const e = EFECTOS.filter(function (x) { return x.clave === clave; })[0];
    if (!e) return [0, 0];
    const v = Object.keys(e.kb).map(function (k) { return e.kb[k]; });
    return [Math.min.apply(null, v), Math.max.apply(null, v)];
  }

  // El efecto que toca a un servicio: el suyo propio si se le ha puesto uno, si no el global.
  function efectoDe(st, s) {
    const propio = st.efectosPorServicio && st.efectosPorServicio[s.id];
    return propio || st.efecto || 'barrido';
  }

  // El GIF del carrusel de un servicio. Estaba escrito a mano en tres sitios; ahora el
  // nombre se arma en uno solo, que es donde hay que tocar si cambia el esquema.
  function carruselSrc(st, s) {
    return imgFor(st, 'carousel_' + s.id + '_' + efectoDe(st, s) + '.gif');
  }

  const ASUNTOS = {
    general: [
      { clave: 'directo',    etiqueta: 'Directo',    texto: '📍 Centauro ADS \u00b7 Espacios publicitarios disponibles' },
      { clave: 'beneficio',  etiqueta: 'Beneficio',  texto: '🚦 Tu marca en las calles de Caracas: esto es lo que hay libre' },
      { clave: 'curiosidad', etiqueta: 'Curiosidad', texto: '👀 120.000 personas al d\u00eda pasan por esta pantalla' },
    ],
    agencia: [
      { clave: 'directo',    etiqueta: 'Directo',    texto: '📊 Inventario OOH/DOOH Caracas \u00b7 disponibilidad actualizada' },
      { clave: 'beneficio',  etiqueta: 'Beneficio',  texto: '🎯 Cinco frentes con m\u00e9tricas comparables para tu pr\u00f3ximo mix' },
      { clave: 'curiosidad', etiqueta: 'Curiosidad', texto: '📈 Tu pr\u00f3ximo Share of Voice, en una sola tabla' },
    ],
    nuevo: [
      { clave: 'directo',    etiqueta: 'Directo',    texto: '🪧 C\u00f3mo empezar a anunciar en la calle, paso a paso' },
      { clave: 'beneficio',  etiqueta: 'Beneficio',  texto: '✨ Publicidad exterior sin ser experto ni gastar de m\u00e1s' },
      { clave: 'curiosidad', etiqueta: 'Curiosidad', texto: '🤔 \u00bfPor d\u00f3nde se empieza a anunciar en la calle?' },
    ],
    phygital: [
      { clave: 'directo',    etiqueta: 'Directo',    texto: '📲 Phygital \u00b7 c\u00f3mo conectar la calle con el m\u00f3vil' },
      { clave: 'beneficio',  etiqueta: 'Beneficio',  texto: '🔗 La calle capta la atenci\u00f3n. El m\u00f3vil cierra la venta.' },
      { clave: 'curiosidad', etiqueta: 'Curiosidad', texto: '⏱️ 9:00 AM en Chacao. 9:03 AM en Instagram.' },
    ],
  };

  // Los tres asuntos que corresponden al perfil activo.
  function asuntosDe(st) { return ASUNTOS[st.perfil] || ASUNTOS.general; }

  const PERFILES = {
    general: {
      nombre: 'General', desc: 'Catálogo completo, sin segmentar. El de siempre.',
      bloque: '', orden: null,
    },
    agencia: {
      nombre: 'Agencias y grandes cuentas',
      desc: 'Ficha de disponibilidad: medidas, tráfico y estado. Datos primero, sin rodeos.',
      asunto: 'Disponibilidad OOH/DOOH · Caracas',
      preheader: 'Medidas, tráfico y estado de cada espacio: dos pantallas LED, vallas, tótem y 250 riders.',
      titulo: 'Inventario disponible', sub: 'Centauro ADS · Phygital + DOOH + Digital',
      intro: 'Te comparto la disponibilidad, con las medidas y el tráfico de cada espacio, para que puedas cerrar el plan de medios sin pedir las fichas por separado.',
      cierre: 'Si necesitas un espacio que no aparezca aquí, dímelo y lo busco.',
      cta: 'Pedir tarifas y disponibilidad',
      orden: ['led', 'mercedes', 'vallas', 'rider', 'totem'],
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
      orden: ['totem', 'led', 'mercedes', 'vallas', 'rider'],
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
      orden: ['led', 'mercedes', 'totem', 'rider', 'vallas'],
      bloque: 'puente',
    },
  };

  // ── Contenido por defecto: cada bloque tiene `on` (inhibir) y campos editables ──
  // CONTENT_VERSION: SUBIR este número cada vez que cambie un valor por defecto (contacto, lema, servicios…).
  // El compositor guarda el contenido en el navegador con esta versión en la clave; al subirla, lo guardado con
  // datos viejos deja de usarse y se cargan los valores nuevos.
  const CONTENT_VERSION = 5;

  function defaultState() {
    return {
      plantilla: 'A', seed: 1, imgSet: 'fotos', heroAnim: true, cardAnim: true,
      // Eje de perfil: cambia el mensaje sin cambiar el formato. 'general' = comportamiento de siempre.
      perfil: 'general',
      // Claro u oscuro. Los formatos del asesor (E, F, G) existen en los dos; los mios
      // (A-D) llevan su tema fijo por diseno y este campo no les afecta.
      tema: 'claro',
      // Cual de los tres asuntos se usa. 'propio' respeta el que se escriba a mano en el
      // campo Asunto: la ultima palabra la tiene quien redacta, no el catalogo.
      asunto3: 'directo',
      // Efecto de animacion del carrusel. Por defecto uno de los ligeros: un correo que
      // tarda en cargar no lo lee nadie, por muy bonita que sea la transicion.
      efecto: 'barrido',
      // El de la Personalizada va aparte del de A-G a proposito. En A-G cada efecto es un
      // GIF pregenerado que hay que subir; en una Personalizada el servidor lo arma al
      // vuelo con las paginas del cliente. Compartir campo hacia que elegir aqui un efecto
      // sin subir dejara las imagenes de A-G rotas, sin que nadie se enterara.
      efectoEntrega: 'barrido',
      // El aspecto de la Personalizada, aparte del de A-G por la misma razon que el efecto:
      // su panel es un interruptor de dos posiciones y aqui hay tres.
      temaEntrega: 'claro',
      // Excepciones por servicio: { led: 'persiana' }. Vacio = todos usan el global.
      efectosPorServicio: {},
      // Banco de imagenes por servicio: que fotos entran, tres huecos libres y el video.
      // Vacio = cada servicio usa todas sus fotos, que es el comportamiento de siempre.
      banco: {},


      // Precios: 'no' = ninguno (el precio va en la cotización formal) · 'desde' = precio de entrada.
      precios: 'no',
      asunto: 'Centauro ADS · Disponibilidad de espacios publicitarios Phygital + DOOH + Digital',
      preheader: 'Vallas, pantallas LED, tótems y publicidad móvil disponibles hoy, con presentación en línea de cada uno.',
      destinatario: 'Sr. Cesar Garcia',
      // De donde salen las imagenes. 'img' es la carpeta de trabajo local; la copia
      // publicada en /static/email/ inyecta window.ASSET_BASE='.' para que resuelvan
      // al lado del propio fichero. En Node no hay window y se queda en 'img'.
      assetBase: (typeof window !== 'undefined' && window.ASSET_BASE) || 'img',
      assetBaseProd: 'https://links.centauroads.com/static/email',
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
          cta: 'Ver catálogo especial', url: 'mailto:mercadeo@centauroads.com?subject=Cat%C3%A1logo%20de%20branding%20y%20esculturas' },
        // Muro de clientes: prueba social para el perfil de cliente nuevo. APAGADO hasta que Elizabeth
        // confirme que podemos nombrar a estas marcas en un correo.
        // Datos operativos de los formatos del asesor. Van aparte porque CADUCAN: una
        // disponibilidad y una fecha de cierre dejan de ser ciertas solas. El texto de
        // partida es el que entrego el asesor, sin tocar; aqui solo se puede actualizar.
        asesor: {
          on: true,
          periodo: 'Octubre – Diciembre 2026',
          etiquetaMeta: 'Q1 2026 · AGENCIAS',
          dispoFecha: '19-sep',
          dispoTexto: 'LED Chacao: 3 slots libres en octubre.',
          cierreTexto: 'Cerramos programación de Q1 el 15 de noviembre.',
          slotsLed: '3 SLOTS',
          pieCta: 'Instalación llave en mano · reporte de campaña incluido',
          // El texto del boton de E. Era un literal, y se quedaba diciendo "Q1" aunque el
          // periodo cambiara. Por defecto el de siempre: cambiarlo es cosa del negocio.
          botonTexto: 'Solicitar disponibilidad Q1',
          respuesta: 'Respuesta en menos de 24 horas hábiles.',
        },
        // Textos de E, F y G. Eran literales en el codigo y no se podian tocar desde el panel.
        // *asi* marca el realce que tenia el diseno (color de acento o negrita) y una linea nueva
        // es un salto. Los huecos entre llaves los rellena el motor: {destinatario}, y en E
        // {periodo}, {frentes} (en letras), {n} (en cifra) y, en la tabla, {medida}, que sale de
        // la ficha oficial de cada espacio y no se copia aqui.
        inventario: {
          epigrafe: 'Inventario · {periodo}',
          titulo: 'Tu próximo *Share of Voice*, en una sola tabla.',
          entrada: 'Sin brief educativo. Sin rodeos. Los {frentes} frentes que operamos en Caracas, con métricas comparables, para que tu equipo de medios calcule el mix sin llamar a nadie.',
          saludoEpigrafe: 'Para el equipo de {destinatario}',
          saludo1: 'Sabemos cómo trabajan: brief, medios, tabla de disponibilidad, decisión. Vamos directo a la última parte.',
          saludo2: 'Este es el inventario que operamos hoy en Caracas, listo para integrarse a tu mix del próximo trimestre, sin brief educativo de por medio.',
          cifra1: '120K impactos / día', etiqueta1: 'LED',
          cifra2: '250 motos LED', etiqueta2: 'Rider',
          cifra3: '{n} frentes', etiqueta3: 'activos',
          seccion: '01 · Inventario',
          seccionTitulo: 'Espacios disponibles',
          seccionSub: 'orden por rotación de audiencia',
          pieFoto: 'LED Chacao, el frente con mayor rotación en Caracas Este.',
          dispoEtiqueta: 'Disponibilidad al',
        },
        tablaInventario: {
          led_titulo: 'Pantalla LED Chacao · DOOH',
          led_detalle: 'Chacao, Av. Francisco de Miranda · {medida} · rotación por franjas horarias',
          led_dato1: 'Impactos', led_valor1: '120.000/día', led_dato2: 'Formato', led_valor2: 'Video / MP4',
          mercedes_titulo: 'Pantalla LED Las Mercedes · DOOH',
          mercedes_detalle: 'Av. Paseo Enrique Erazo · {medida} · horizontal, 24 horas',
          mercedes_dato1: 'Tráfico', mercedes_valor1: '95.000 vehículos/día', mercedes_dato2: 'Formato', mercedes_valor2: 'Video / MP4 · 30 s',
          vallas_titulo: 'Vallas · OOH nacional',
          vallas_detalle: 'Caracas y arterias viales · gran formato · brand recall de largo plazo',
          vallas_dato1: 'Rotación', vallas_valor1: 'Alta vial', vallas_dato2: 'Cobertura', vallas_valor2: 'Nacional',
          rider_titulo: 'Rider Clon · movilidad LED', rider_distintivo: 'TRACKING',
          rider_detalle: 'Caracas · San Antonio · Valencia · caja LED {medida} · GPS en vivo',
          rider_dato1: 'Flota', rider_valor1: '250 motos', rider_dato2: 'Turno', rider_valor2: '8 h / día',
          totem_titulo: 'Tótem digital · indoor',
          totem_detalle: 'C.C. San Ignacio · {medida} · audiencia cautiva premium',
          totem_dato1: 'Salidas', totem_valor1: '240/día', totem_dato2: 'Ambiente', totem_valor2: 'Indoor A+',
        },
        guia: {
          meta: 'Guía para empezar',
          titulo: 'Que te conozcan. *Que te recuerden.* Que te compren.',
          entrada: 'Esa es la secuencia. Tres fases, en ese orden, es cómo crecen las marcas que aparecen en las calles. Te la explicamos sin tecnicismos y sin comprometerte a nada.',
          saludo: 'Hola {destinatario},',
          parrafo: 'Gracias por interesarte en dar el paso a la *publicidad exterior*. Sabemos que es una decisión importante: hay muchos formatos, muchos precios y poca información clara sobre por dónde empezar. Este correo no es una cotización: es la guía que les contamos a puerta cerrada a las marcas que arrancan con nosotros. Léela en 2 minutos y hablamos.',
          fase1: 'Fase de atracción', fase1Titulo: 'Que te conozcan',
          fase1Texto: 'Empezamos con *formatos digitales de alto tráfico*. El brillo y el movimiento captan miradas nuevas, explican qué haces y qué ofreces. Es la manera más rápida de dejar de ser un desconocido.',
          fase1Etiqueta: 'Recomendado para empezar', fase1Servicio: 'Tótem digital · San Ignacio',
          fase1Detalle: '240 salidas/día en un centro comercial premium. Audiencia atenta, presupuesto de entrada.',
          fase2: 'Fase de memoria', fase2Titulo: 'Que te recuerden',
          fase2Texto: 'Cuando ya te conocen, tu marca se instala en *las calles que tu cliente recorre todos los días*. Vallas y pantallas LED trabajando juntas: y cuando piensen en lo que vendes, aparecerás tú.',
          fase2Etiqueta: 'Combinamos con la fase 1', fase2Servicio: 'Pantalla LED · Chacao',
          fase2Detalle: '120.000 impactos/día en la arteria de mayor rotación de Caracas Este.',
          fase3: 'Fase de decisión', fase3Titulo: 'Que te compren',
          fase3Texto: 'La calle empuja, el móvil cierra. En esta fase activamos promociones tácticas y motos con LED que aparecen justo donde y cuando decides. Es la parte donde la campaña se convierte en ventas.',
          fase3Etiqueta: 'Táctico y medible', fase3Servicio: 'Rider Clon · movilidad LED',
          fase3Detalle: '250 motos con GPS. Elegimos las zonas y horas donde vive tu cliente.',
          cajaTitulo: 'Sin fricciones técnicas',
          cajaTexto: 'Nosotros nos encargamos de todo lo técnico. Tú apruebas el diseño.',
          ctaTexto: 'Cuéntame de tu marca y te preparo una propuesta *a la medida de tu presupuesto*. Sin compromiso.',
          boton: 'Cuéntame de tu marca',
        },
        phygital: {
          meta: 'PHYGITAL · Serie 2026',
          epigrafe: 'Physical + Digital',
          titulo: 'La pantalla capta.\n*El móvil cierra.*',
          saludo: 'Hola {destinatario},',
          parrafo: 'La gente ya no mira los anuncios. Los graba, los sube y los convierte en contenido, o los ignora. Sabemos que necesitan algo que rompa el molde. Antes de mostrarte precios o formatos, mira cómo se ve una campaña Phygital en *tres minutos reales*. Después conversamos.',
          hora1: '09:00 AM · Chacao',
          escena1: 'Escena 01',
          escena1Texto: 'Una persona mira arriba. Ve un QR gigante en la pantalla LED. Curiosidad. Levanta el teléfono.',
          puente: '3 SEGUNDOS',
          hora2: '09:03 AM · Instagram',
          cuenta: '@tu_marca_aqui', lugar: 'Caracas · Venezuela', filtro: 'Filtro AR activo',
          publicacion: 'Encontré la valla ⚡ *#TuMarcaChacao*',
          meGusta: '2.847 me gusta',
          comentario: 'Vieron mi campaña. Se pararon. La grabaron. La subieron.',
          remate: 'La calle también es feed.',
          remateTexto: 'Eso es Phygital. Una pantalla que no termina cuando el semáforo cambia.',
          comoEpigrafe: 'Cómo se arma',
          comoTexto: 'Tres piezas. Una campaña que se comparte.',
          pieza1: 'Pantalla LED · el gancho físico',
          pieza1Texto: 'QR gigante en Chacao o Las Mercedes. Lleva a un filtro AR, un cupón o tu e-commerce directo.',
          pieza2: 'Rider Clon · la campaña que se mueve',
          pieza2Texto: '250 motos con caja LED se convierten en caza-recompensas: los usuarios las fotografían y suben, etiquetándote.',
          pieza3: 'Capa digital · el cierre en el móvil',
          pieza3Texto: 'Retargeting a quien escaneó, filtros AR de tu marca, hashtag propio. El impacto físico deja huella medible en redes.',
          cajaTitulo: 'Lo que resolvemos',
          cajaTexto: 'Ya no eliges entre branding masivo o conversión digital. La calle capta. El móvil cierra.',
          boton: 'Diseñemos una campaña que se comparta',
          pieBoton: 'Llamada creativa de 15 minutos, sin brief formal.',
        },
        clientes: { on: false, titulo: 'Marcas que ya están en la calle con nosotros',
          lista: 'Pepsi · Nestlé · Yango · Cashea · EPA · Arturo’s · Ridery · Cinepic · Tío Rico' },
        pasos: { on: true, titulo: 'Próximos pasos',
          texto: 'Una vez seleccionados los espacios, envíanos la información y los documentos para preparar la cotización.' },
        presupuesto: { on: true, titulo: 'Para un presupuesto formal necesitamos',
          items: ['RIF digital de la empresa', 'Fecha de inicio y duración de la campaña', 'Formato o alcance (pantalla, tótem u otro)'] },
        // `responder`: el boton abre un mensaje a la cuenta desde la que se envia, con "Re:" y el
        // asunto del correo (ver ctaHref). Apagado, manda `url`, escrita a mano.
        cta: { on: true, texto: 'Enviar información para cotizar', url: 'mailto:mercadeo@centauroads.com?subject=Solicitud%20de%20cotizaci%C3%B3n',
          responder: true, cuerpo: 'Hola, quiero pedir una cotización. Me interesan estos espacios:\n\n',
          alternativa: 'O, si lo prefieres, responde directamente a este correo.' },
        cierre: { on: true, texto: 'Quedo atenta a tu respuesta.' },
        firma: { on: true, nombre: 'Elizabeth Quintero',
          // Cargo elegible: 'alianzas' o 'directora'. El texto lo compone cargoDe().
          rol: 'alianzas',
          // Que correo se ensena: 'mercadeo' (por defecto), 'personal' o 'ambos'.
          correo: 'mercadeo',
          slogan: 'Visibilidad que conecta', linea: 'PHYGITAL DOOH + Digital',
          email: 'equintero@centauroads.com', telefono: '+58 412 100 3559', ig: '@centauroads',
          web: 'linktr.ee/centauroadss', contacto: 'mercadeo@centauroads.com', direccion: 'Caracas, Venezuela' },
        // Entrega a medida (formato H).
        // Esto NO es el catalogo: es la presentacion propia que ya se le armo a un cliente.
        // `url` e `img` los rellena el panel con los datos de esa entrega; los valores de
        // aqui son el marcador de posicion con el que se ve la plantilla en seco.
        //
        // `texto` y `corto` son el MISMO mensaje en dos longitudes, no dos redacciones que
        // mantener (FR-118): el largo va al correo, el corto a WhatsApp.
        entrega: {
          on: true,
          titulo: 'Propuesta para tu marca',
          // El rotulo de la esquina. Editable: no toda entrega es una propuesta -puede ser una
          // revision, una renovacion o un cierre de campana- y el correo tiene que poder decirlo.
          meta: 'PROPUESTA \u00b7 A MEDIDA',
          // La empresa del cliente. La rellena el panel con el contacto elegido; sin ella el
          // texto queda hablando de nadie.
          empresa: '',
          // `url` es el enlace de Canva -el destino-; `enlace` es el propio de la entrega, que
          // es el que se manda. Son distintos a proposito: mandar el de Canva se salta el
          // registro de aperturas, el aviso de interes y la tarjeta de WhatsApp.
          url: '',
          enlace: '',
          // Sin imagen elegida NO hay imagen. Antes habia aqui una foto del catalogo, y en una
          // propuesta personalizada eso es ensenarle al cliente algo que no es suyo.
          img: '',
          alt: 'Portada de la propuesta preparada para el cliente',
          texto: 'Preparamos esta propuesta para {empresa}: los espacios que le convienen, d\u00f3nde se ve y qu\u00e9 pasa cuando la gente pasa por delante.\n\n\u00c1brela con calma y me dices qu\u00e9 te parece. Si hay algo que ajustar, lo ajustamos.',
          corto: 'Te dejo la propuesta que preparamos para {empresa}. \u00c1brela con calma y me dices qu\u00e9 te parece.',
          cta: 'Ver la propuesta',
          acompanan: 'Lo que la acompa\u00f1a',
          // Interruptores PROPIOS. El contenido se comparte con A-G, pero alli estos bloques
          // van siempre encendidos; aqui se anaden cuando hacen falta, y compartir el
          // interruptor significaria que apagarlos en una propuesta los apaga en el catalogo.
          conSuministro: false,
          conPasos: false,
          // La despedida, justo antes de la firma. Propia de la entrega: es lo ultimo que se
          // lee y cambia segun a quien va dirigida.
          cierre: '\u00a1Si necesitas un espacio que no aparezca aqu\u00ed, d\u00edmelo y lo busco!',
        },
        pie: { on: true, texto: 'Recibes este correo porque solicitaste información sobre espacios publicitarios de Centauro ADS.' },
      },
      servicios: SERVICIOS.map(s => Object.assign({ on: true }, s)),
    };
  }

  // ── Utilidades ──
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const nl2br = s => esc(s).replace(/\n/g, '<br>');
  // {destinatario} es a quien se escribe; {empresa}, de donde es. La segunda solo la usan los
  // textos de la Entrega, pero se resuelve aqui para que haya UN sitio donde se rellenan los
  // huecos y no dos que se separen con el tiempo.
  const fill = (s, st) => String(s || '')
    .replace(/\{destinatario\}/g, st.destinatario || '')
    // Sin empresa elegida el hueco NO se queda vacio: 'para : los espacios' es una frase rota,
    // y se ve en la vista previa antes de elegir contacto. Con el respaldo, la plantilla en
    // seco se lee igual que antes de que el campo existiera.
    .replace(/\{empresa\}/g, (st.bloques && st.bloques.entrega && st.bloques.entrega.empresa) || 'tu marca');
  // El enlace de cada presentacion base es SUYO y editable en el panel: otro de Canva, o uno corto
  // del acortador propio. Antes habia una base global que componia <base>/<slug> con slugs fijos
  // que no existian en el acortador -los cinco daban 404, comprobado- y el enlace de cada
  // servicio no se podia tocar.
  //
  // El token por destinatario (?c=) solo va en los del acortador: es el que registra quien pulso.
  // A uno de Canva no le sirve, y ponerle parametros a un corto de canva.link es arriesgar que
  // deje de resolver.
  const ACORTADOR = /^https?:\/\/links\.centauroads\.com\//i;
  const linkFor = (st, s) => {
    const url = String(s.canva || '').trim();
    if (st.token && ACORTADOR.test(url)) {
      return url + (url.indexOf('?') >= 0 ? '&' : '?') + 'c=' + encodeURIComponent(st.token);
    }
    return url;
  };
  // El boton de cotizar, como una respuesta al correo.
  //
  // Un enlace no puede pulsar el "Responder" del programa del cliente: ninguno lo permite, y el hilo
  // de una respuesta lo marcan cabeceras que un mailto: no puede fijar. Lo mas cercano: un mensaje a
  // la cuenta DESDE LA QUE SE ENVIA (mercadeo@, siempre: decision del 2026-09-30), con el asunto
  // "Re: <el del correo>". La peticion llega al mismo buzon y, con el mismo asunto, se lee como la
  // respuesta que es. Antes abria un correo nuevo a otra direccion, con un asunto que no casaba con nada.
  // Con `responder` apagado manda el enlace escrito a mano (un formulario, otra direccion).
  const CUENTA_DE_ENVIO = 'mercadeo@centauroads.com';
  function ctaHref(st) {
    const c = B(st, 'cta');
    if (c.responder === false) return c.url;
    const asunto = String(st.asunto || '').trim();
    const re = /^re:/i.test(asunto) ? asunto : 'Re: ' + asunto;
    return 'mailto:' + ((B(st, 'firma') || {}).contacto || CUENTA_DE_ENVIO) +
      '?subject=' + encodeURIComponent(re) + (c.cuerpo ? '&body=' + encodeURIComponent(c.cuerpo) : '');
  }
  const webHref = (w) => /^https?:\/\//.test(w || '') ? w : 'https://' + (w || '');
  const imgFor = (st, name) => (st.assetBase || 'img').replace(/\/$/, '') + '/' + name;
  // Juego de imágenes por servicio: fotos reales del inventario o portadas de los decks de Canva
  const IMG_SETS = { fotos: 'Fotos reales del inventario', portadas: 'Portadas de las presentaciones (Canva)' };
  const usaPortadas = st => st.imgSet === 'portadas';
  const svcImg = (st, s) => imgFor(st, usaPortadas(st) && s.cover ? s.cover : s.img);
  const svcAlt = (st, s) => (usaPortadas(st) && s.altCover ? s.altCover : s.alt);
  // La portada de una entrega puede venir de tres sitios: del servidor que la guarda
  // (/media/entregas/7/og.jpg), de una direccion completa, o del juego de imagenes local
  // cuando es el marcador de posicion. Se distingue por la forma, no por una bandera mas.
  const entregaImg = (st, v) => (/^(https?:)?\/\//.test(v) || String(v).charAt(0) === '/') ? v : imgFor(st, v);
  const activos = st => st.bloques.servicios.on ? st.servicios.filter(s => s.on) : [];
  const on = (st, k) => !!(st.bloques[k] && st.bloques[k].on);
  const B = (st, k) => st.bloques[k];
  const lines = v => Array.isArray(v) ? v : String(v || '').split('\n').map(x => x.trim()).filter(Boolean);

  // Solo se pinta el marco de 600 px. Por fuera no va color: el correo se apoya en el fondo del
  // cliente, como una carta sobre la mesa. Antes el fondo del tema llenaba toda la ventana de
  // Gmail en el ordenador, y con el tema oscuro o el de la marca el correo dejaba de tener borde.
  function doc(st, inner) {
    return '<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">' +
      '<meta name="viewport" content="width=device-width,initial-scale=1">' +
      '<meta name="x-apple-disable-message-reformatting"><title>' + esc(st.asunto) + '</title></head>' +
      '<body style="margin:0;padding:0;-webkit-text-size-adjust:100%;">' +
      '<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">' + esc(st.preheader) + '</div>' +
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">' +
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
  // Un logo por tema, y no por casualidad: van aplanados sobre fondo plano porque Outlook no
  // compone transparencias con fiabilidad, asi que cada uno trae pintado el fondo de SU panel.
  // Sin el de la marca, el del tema oscuro dejaba un recuadro casi negro sobre el morado.
  // Se generan con .
  const LOGOS = {
    claro: 'logo_h_light_2x.png',
    oscuro: 'logo_h_dark_2x.png',
    centauro: 'logo_h_centauro_2x.png',
  };

  function marca(st, tema, ancho) {
    const dark = tema !== 'claro';
    const w = ancho || 200;
    const f = B(st, 'firma');
    const slogan = f.slogan || 'Visibilidad que conecta';
    const linea = f.linea || 'PHYGITAL DOOH + Digital';
    // Sobre morado, el morado claro del slogan se pierde contra su propio fondo: va en blanco.
    const sloganColor = tema === 'centauro' ? '#F8F4FA' : (dark ? C.purpleLight : C.purple);
    return '<img src="' + esc(imgFor(st, LOGOS[tema] || LOGOS.claro)) + '" width="' + w + '" alt="Centauro ADS" style="display:block;width:' + w + 'px;max-width:100%;height:auto;border:0;font-family:' + FH + ';font-size:22px;font-weight:800;letter-spacing:-.01em;color:' + (dark ? '#FFFFFF' : C.text) + ';">' +
      '<div style="font-family:' + FH + ';font-size:13px;font-weight:700;letter-spacing:.02em;color:' + sloganColor + ';padding:6px 0 0 2px;">' + esc(slogan) + '</div>' +
      '<div style="font-family:' + FH + ';font-size:11px;font-weight:700;letter-spacing:.10em;color:' + (dark ? C.orange : C.orangeInk) + ';text-transform:uppercase;padding:3px 0 0 2px;white-space:nowrap;">' + esc(linea) + '</div>';
  }

  function firma(st, tema) {
    const dark = tema !== 'claro';
    const f = B(st, 'firma');
    // Los colores salen de la paleta, no de constantes sueltas. Para claro y oscuro son los
    // mismos de siempre -el guardia byte a byte lo comprueba-, pero la firma dejaba de seguir al
    // tema en cuanto habia un tercero: sobre el morado ponia el gris del tema oscuro, otro gris
    // distinto del que usa el resto del correo.
    const k = paleta(tema);
    const t = k.texto, m = k.apagado, a = dark ? C.orange : C.purple;
    return '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td valign="top" style="padding:0 0 12px 0;">' + marca(st, tema, 168) + '</td></tr><tr>' +
      '<td valign="top" style="font-family:' + FB + ';font-size:13px;line-height:19px;color:' + m + ';">' +
      '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + t + ';">' + esc(f.nombre) + '</div>' +
      '<div>' + esc(cargoDe(f)) + '</div>' +
      // El primer correo comparte linea con el telefono; los demas van debajo.
      correosDe(f).map(function (dir, i) {
        const enlace = '<a href="mailto:' + esc(dir) + '" style="color:' + a +
          ';text-decoration:none;">' + esc(dir) + '</a>';
        if (i > 0) return '<div>' + enlace + '</div>';
        return '<div>' + enlace + ' &nbsp;·&nbsp; <a href="tel:' +
          esc(String(f.telefono).replace(/[^+0-9]/g, '')) + '" style="color:' + m +
          ';text-decoration:none;">' + esc(f.telefono) + '</a></div>';
      }).join('') +
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
      { n: '1', tit: 'Que te conozcan', med: 'Pantalla LED y t\u00f3tem digital',
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

  // ══ FORMATOS DEL ASESOR (E, F, G) ══════════════════════════════════════════════
  //
  // Tres disenos entregados por el asesor de diseno grafico, cada uno pensado para un
  // perfil: agencias, cliente nuevo y phygital. Se ANADEN a los mios (A-D), no los
  // sustituyen.
  //
  // Lo que se respeta de su entrega: el texto principal, la composicion y la escala
  // tipografica, palabra por palabra.
  // Lo que se cambia por decision del cliente: la firma del pie es la mia (lleva el
  // correo de mercadeo, que la suya no trae), las fotos son mis carruseles animados en
  // vez de imagenes sueltas, y los servicios que su diseno no ensena se anaden al final
  // como complementos.
  //
  // Sus versiones clara y oscura usan EXACTAMENTE los tokens de la marca, asi que una
  // sola funcion sirve las dos: solo cambia la paleta. Duplicar el HTML habria
  // garantizado que las dos versiones se separaran con el primer retoque.

  // Tres temas. El tercero no es "otro oscuro": en el oscuro el morado es un acento sobre negro,
  // y aqui el morado ES la superficie. Es la marca puesta en el correo, para cuando la propuesta
  // tiene que llegar como un objeto de Centauro y no como un documento.
  //
  // El naranja pasa a mandar en todo lo que hay que pulsar: sobre morado canta, y el texto del
  // boton va oscuro, que da 7,5:1. Comprobados todos los pares; el mas justo es el texto apagado
  // sobre el panel, 8,3:1, muy por encima del 4,5 que pide el minimo.
  const TEMAS = ['claro', 'oscuro', 'centauro'];
  const temaDe = st => TEMAS.indexOf(st.tema) >= 0 ? st.tema : 'claro';

  function paleta(tema) {
    if (tema === 'centauro') return {
      fondo: '#1B0722', panel: '#33103F', panel2: '#421553', linea: '#63267B',
      texto: '#F8F4FA', apagado: '#CBAFD8',
      acento: C.orange, vivo: C.orange, sobreVivo: '#2A0E35',
      botonFondo: C.orange, botonTexto: '#2A0E35',
    };
    return tema === 'oscuro' ? {
      fondo: C.black, panel: C.ink, panel2: C.ink2, linea: C.line,
      texto: C.textDark, apagado: C.mutedDark,
      acento: C.purpleLight, vivo: C.orange, sobreVivo: '#141016',
      botonFondo: C.purple, botonTexto: '#FFFFFF',
    } : {
      fondo: C.sand, panel: C.paper, panel2: C.sand, linea: C.rule,
      texto: C.text, apagado: C.muted,
      acento: C.purple, vivo: C.orangeInk, sobreVivo: '#FFFFFF',
      botonFondo: C.purple, botonTexto: '#FFFFFF',
    };
  }
  // Cierto para los dos temas de fondo oscuro: manda la version clara del logo y el texto claro.
  const esOscuro = st => temaDe(st) !== 'claro';

  // Cabecera comun: logo a la izquierda, metadato a la derecha.
  // `submeta` es opcional y solo lo usa la Personalizada: el nombre de la empresa, bajo el
  // rotulo. Sin el, el HTML sale identico al de siempre, que es lo que E, F y G necesitan para
  // seguir pasando el guardia byte a byte.
  function cabeceraAsesor(st, P, meta, submeta) {
    const k = paleta(temaDe(st));
    // Debajo y no dentro: el rotulo dice de que clase de correo se trata y la empresa dice de
    // quien es. Juntarlos en una linea de 10px en mayusculas espaciadas haria ilegible lo que
    // mas importa de los dos.
    const abajo = submeta
      ? '<div style="font-family:' + FH + ';font-size:14px;font-weight:800;letter-spacing:-.01em;' +
        'text-transform:none;color:' + k.texto + ';padding-top:6px;">' + esc(submeta) + '</div>'
      : '';
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td valign="middle">' + marca(st, temaDe(st), 150) + '</td>' +
      '<td valign="middle" align="right" style="font-family:' + FH + ';font-size:10px;font-weight:800;' +
        'letter-spacing:.24em;text-transform:uppercase;color:' + k.apagado + ';">' + esc(meta) + abajo + '</td>' +
      '</tr></table>';
  }

  // Textos editables de E, F y G. *asi* es el realce del diseno -el color de acento en un titular,
  // la negrita en un parrafo-: quien lo cambia decide que palabra se resalta. Una linea nueva es
  // un salto. Se escapa ANTES de poner las etiquetas, asi que lo escrito nunca es HTML.
  const realce = (s, abre, cierra) => esc(s).replace(/\*([^*\n]+)\*/g, abre + '$1' + cierra).replace(/\n/g, '<br>');
  // Huecos entre llaves que rellena el motor. Uno que no conoce se queda tal cual, a la vista:
  // mejor que desaparezca en silencio una palabra que alguien escribio.
  const huecos = (s, mapa) => String(s == null ? '' : s)
    .replace(/\{(\w+)\}/g, (m, k) => (mapa[k] != null ? String(mapa[k]) : m));

  // Epigrafe pequeno en mayusculas. Es el recurso tipografico que ordena sus tres disenos.
  function epigrafe(st, txt, color) {
    const k = paleta(temaDe(st));
    return '<div style="font-family:' + FH + ';font-size:11px;font-weight:800;letter-spacing:.26em;' +
      'text-transform:uppercase;color:' + (color || k.vivo) + ';padding:0 0 12px 0;">' + esc(txt) + '</div>';
  }

  // Boton solido construido con tabla, no con <button>: es lo unico que Outlook dibuja bien.
  function botonAsesor(st, texto, url) {
    const k = paleta(temaDe(st));
    return '<table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td bgcolor="' + k.botonFondo + '" style="background:' + k.botonFondo + ';border-radius:8px;">' +
      '<a href="' + esc(url) + '" style="display:inline-block;padding:15px 30px;font-family:' + FH + ';' +
      'font-size:14px;font-weight:800;letter-spacing:.01em;color:' + k.botonTexto + ';text-decoration:none;">' +
      esc(texto) + ' &rarr;</a></td></tr></table>';
  }

  // La foto de un servicio, siempre con mi carrusel animado cuando existe: el cliente
  // pidio conservar las varias imagenes por servicio con sus transiciones.
  function fotoServicio(st, s, ancho, alto) {
    const src = (st.cardAnim && !usaPortadas(st)) ? carruselSrc(st, s) : svcImg(st, s);
    const k = paleta(temaDe(st));
    return '<a href="' + esc(linkFor(st, s)) + '"><img src="' + esc(src) + '" width="' + ancho + '"' +
      (alto ? ' height="' + alto + '"' : '') + ' alt="' + esc(svcAlt(st, s)) + '"' +
      ' style="display:block;width:' + ancho + 'px;max-width:100%;height:auto;border:0;border-radius:8px;' +
      'color:' + k.texto + ';font-family:' + FB + ';font-size:13px;line-height:18px;"></a>';
  }

  // Complementos: los servicios que el diseno del asesor no ensena con imagen se anaden
  // al final, con foto mas pequena. Asi ninguno queda fuera del correo aunque su
  // composicion original solo destacara uno o tres.
  // "cuatro frentes", no "4 frentes", dentro de una frase.
  function cuantos(n) {
    return ['cero', 'un', 'dos', 'tres', 'cuatro', 'cinco', 'seis', 'siete'][n] || String(n);
  }

  // La tarjeta de un complemento: foto, nombre, cobertura y enlace.
  function textoComplemento(st, s, k) {
    return '<div style="font-family:' + FH + ';font-size:14px;font-weight:800;color:' + k.texto + ';padding:8px 0 2px 0;">' + esc(s.nombre) + '</div>' +
      '<div style="font-family:' + FB + ';font-size:12px;line-height:17px;color:' + k.apagado + ';">' + esc(s.cobertura) + '</div>' +
      '<div style="padding:6px 0 0 0;"><a href="' + esc(linkFor(st, s)) + '" style="font-family:' + FH + ';font-size:11px;font-weight:800;color:' + k.acento + ';text-decoration:none;">Ver presentaci\u00f3n &rarr;</a></div>';
  }

  // opts.titulo === false quita el "Tambien disponible" de encima (la Guia no lo lleva).
  //
  // Con cuatro productos los complementos salen en numero impar -tres en Inventario y
  // Phygital, uno en la Guia- y una tarjeta sola en una rejilla de dos columnas se queda
  // huerfana a media anchura. La que sobra va en horizontal, foto y texto lado a lado,
  // con dos tablas align="left": a 600 px caben juntas y en el movil la segunda baja
  // sola debajo de la foto. Es la misma tecnica que ya usa la rejilla del Catalogo.
  function complementos(st, yaMostrados, opts) {
    const faltan = activos(st).filter(s => yaMostrados.indexOf(s.id) < 0);
    if (!faltan.length) return '';
    const k = paleta(temaDe(st));
    let filas = '';
    // opts.columnas === 1 fuerza una tarjeta por fila. Dos columnas son <td> hermanos, y un
    // <td> no baja debajo de su hermano en el movil sin media queries, que el correo no tiene:
    // a 375 px las dos tarjetas se reparten el ancho y quedan ilegibles. La variante de una
    // columna usa dos tablas align='left' -la misma tecnica que ya usaba la tarjeta impar-,
    // que a 600 px van lado a lado y en el movil se apilan solas. La Entrega la usa porque
    // ensena los cinco servicios; A-G siguen con dos columnas y no se mueven.
    const paso = (opts && opts.columnas === 1) ? 1 : 2;
    for (let i = 0; i < faltan.length; i += paso) {
      const par = faltan.slice(i, i + paso);
      if (par.length === 1) {
        const s = par[0];
        filas += '<tr><td colspan="2" valign="top" style="padding:0 0 16px 0;">' +
          '<table role="presentation" width="266" align="left" cellpadding="0" cellspacing="0" border="0"><tr>' +
            '<td valign="top" style="padding:0 16px 8px 0;">' + fotoServicio(st, s, 250) + '</td></tr></table>' +
          '<table role="presentation" width="260" align="left" cellpadding="0" cellspacing="0" border="0"><tr>' +
            '<td valign="top">' + textoComplemento(st, s, k) + '</td></tr></table>' +
          '</td></tr>';
        continue;
      }
      filas += '<tr>' + par.map(s =>
        '<td width="50%" valign="top" style="padding:0 8px 16px 0;">' +
          fotoServicio(st, s, 250) + textoComplemento(st, s, k) +
        '</td>').join('') + '</tr>';
    }
    // opts.titulo: false lo quita, una cadena lo sustituye, ausente deja el de siempre.
    // La Entrega necesita decir "Lo que la acompana", no "Tambien disponible": alli los
    // servicios no son alternativas, son lo que va con la propuesta que ya se le armo.
    const rotulo = (opts && typeof opts.titulo === 'string') ? opts.titulo : 'Tambi\u00e9n disponible';
    const titulo = (opts && opts.titulo === false) ? '' : epigrafe(st, rotulo, k.acento);
    return titulo +
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">' + filas + '</table>';
  }

  // Valores de catalogo que cambiaron y que un estado guardado puede llevar todavia.
  const RENOMBRADOS = {
    led: [
      { campo: 'nombre', antes: ['Pantallas LED (DOOH)', 'Pantalla LED (DOOH)'] },
      { campo: 'cobertura', antes: ['Ubicaci\u00f3n: Chacao y Las Mercedes', 'Ubicaci\u00f3n: Chacao'] },
    ],
  };

  // Textos de la Entrega que cambiaron de redaccion. Mismo criterio que RENOMBRADOS: se
  // sustituyen SOLO si siguen siendo exactamente los de antes. Quien los edito se queda con
  // lo suyo; quien no, deja de tener un correo que habla de "tu marca" con el contacto puesto.
  const ENTREGA_ANTES = {
    texto: ['Preparamos esta propuesta pensando en tu marca: los espacios que le convienen, d\u00f3nde se ve y qu\u00e9 pasa cuando la gente pasa por delante.\n\n\u00c1brela con calma y me dices qu\u00e9 te parece. Si hay algo que ajustar, lo ajustamos.'],
    corto: ['Te dejo la propuesta que preparamos para tu marca. \u00c1brela con calma y me dices qu\u00e9 te parece.'],
  };

  // Rellena lo que falte en un estado guardado antes de que exista un campo nuevo.
  //
  // La alternativa era subir CONTENT_VERSION, que cambia la clave del almacenamiento y
  // hace desaparecer lo que el usuario llevara escrito a mano. Ya paso una vez y se
  // vivio como una perdida de trabajo. Completar en silencio lo que falta cuesta veinte
  // lineas y no le quita nada a nadie.
  // Enlaces que apuntaban a la cuenta personal de la asesora. Todo pasa por mercadeo@ (decision
  // del 2026-09-30). Mismo criterio que RENOMBRADOS: solo se cambian si siguen siendo exactamente los
  // de antes; un enlace escrito a mano se respeta.
  const ENLACES_ANTES = {
    branding: ['mailto:equintero@centauroads.com?subject=Cat%C3%A1logo%20de%20branding%20y%20esculturas'],
    cta: ['mailto:equintero@centauroads.com?subject=Solicitud%20de%20cotizaci%C3%B3n'],
  };

  function normaliza(st) {
    const base = defaultState();
    if (st.tema === undefined) st.tema = base.tema;
    if (st.asunto3 === undefined) st.asunto3 = base.asunto3;
    if (st.efecto === undefined) st.efecto = base.efecto;
    if (st.efectoEntrega === undefined) st.efectoEntrega = st.efecto || base.efectoEntrega;
    if (st.temaEntrega === undefined) st.temaEntrega = st.tema || base.temaEntrega;
    if (!st.efectosPorServicio) st.efectosPorServicio = {};
    if (!st.banco) st.banco = {};
    // La base global de enlaces cortos se retiro: componia <base>/<slug> con slugs que no
    // existian en el acortador. Quien la tuviera puesta mandaba cinco 404; al quitarla,
    // sus correos vuelven a llevar el enlace de cada servicio.
    delete st.linkBase;
    // Paradas salio del catalogo (2026-09-21). El estado guardado lleva una COPIA de los
    // servicios, asi que hay que quitarla tambien de ahi: si no, seguiria saliendo en los
    // correos de quien ya uso la herramienta. Vale para cualquier servicio que se retire.
    if (Array.isArray(st.servicios)) {
      const vigentes = SERVICIOS.map(function (x) { return x.id; });
      st.servicios = st.servicios.filter(function (x) { return vigentes.indexOf(x.id) >= 0; });
      // Los servicios nuevos del catalogo entran tambien, en la posicion del catalogo: sin
      // esto, quien ya uso la herramienta no veria nunca un servicio anadido despues.
      const guardados = st.servicios.map(function (x) { return x.id; });
      SERVICIOS.forEach(function (nuevo, pos) {
        if (guardados.indexOf(nuevo.id) >= 0) return;
        st.servicios.splice(Math.min(pos, st.servicios.length), 0, Object.assign({ on: true }, nuevo));
      });
      // Textos de catalogo que cambiaron: solo si siguen con el valor de antes. Si alguien
      // los edito a mano, se queda lo suyo.
      st.servicios.forEach(function (x) {
        const actual = SERVICIOS.filter(function (y) { return y.id === x.id; })[0];
        (RENOMBRADOS[x.id] || []).forEach(function (r) {
          if (r.antes.indexOf(x[r.campo]) >= 0) x[r.campo] = actual[r.campo];
        });
      });
    }
    delete st.banco.paradas;
    if (st.efectosPorServicio) delete st.efectosPorServicio.paradas;
    // La firma paso de un 'cargo' escrito a mano a un rol elegible, y gano la
    // eleccion de correo. Se rellenan aqui para no tocar CONTENT_VERSION: subirlo
    // cambia la clave de localStorage y borraria todo lo escrito a mano.
    if (st.bloques && st.bloques.firma) {
      if (st.bloques.firma.rol === undefined) st.bloques.firma.rol = base.bloques.firma.rol;
      if (st.bloques.firma.correo === undefined) st.bloques.firma.correo = base.bloques.firma.correo;
    }
    if (!st.bloques) st.bloques = base.bloques;
    Object.keys(base.bloques).forEach(function (k) {
      if (!st.bloques[k]) { st.bloques[k] = base.bloques[k]; return; }
      Object.keys(base.bloques[k]).forEach(function (campo) {
        if (st.bloques[k][campo] === undefined) st.bloques[k][campo] = base.bloques[k][campo];
      });
    });
    Object.keys(ENLACES_ANTES).forEach(function (k) {
      if (st.bloques[k] && ENLACES_ANTES[k].indexOf(st.bloques[k].url) >= 0) st.bloques[k].url = base.bloques[k].url;
    });
    if (st.bloques.entrega) {
      Object.keys(ENTREGA_ANTES).forEach(function (campo) {
        if (ENTREGA_ANTES[campo].indexOf(st.bloques.entrega[campo]) >= 0) {
          st.bloques.entrega[campo] = base.bloques.entrega[campo];
        }
      });
    }
    return st;
  }

  // Sustituye el asunto por el elegido de los tres. Se aplica DESPUES del perfil, porque
  // es una decision mas concreta: el perfil propone y esto dispone.
  function aplicaAsunto(st) {
    // En la Entrega el asunto ES el titulo de la propuesta: la misma frase dicha una vez. Dejar
    // el del catalogo en un correo que entrega algo concreto desentona en lo primero que lee el
    // cliente. La linea de vista previa -la que Gmail ensena al lado- sale del texto corto por
    // el mismo motivo: si no, la bandeja anuncia una cosa y el correo dice otra.
    //
    // `asunto3 = 'propio'` sigue mandando: quien redacta tiene la ultima palabra.
    if (st.plantilla === 'H' && st.asunto3 !== 'propio') {
      const h = JSON.parse(JSON.stringify(st));
      const e = h.bloques.entrega;
      if (e.titulo) h.asunto = e.titulo;
      const corto = fill(e.corto || '', h).replace(/[ \t\r\n]+/g, ' ').trim();
      if (corto) h.preheader = corto;
      return h;
    }
    if (!st.asunto3 || st.asunto3 === 'propio') return st;
    const elegido = asuntosDe(st).filter(function (x) { return x.clave === st.asunto3; })[0];
    if (!elegido) return st;
    const p = JSON.parse(JSON.stringify(st));
    p.asunto = elegido.texto;
    return p;
  }

  // ══ A y B · «Señal nocturna» ═══════════════════════════════════════════════
  //
  // Lo que Centauro vende es ver tu marca en la calle, de noche, con las pantallas encendidas.
  // El correo copia ese mundo: fondo de noche, la foto del espacio a sangre como si fuera la
  // valla, titulares en letra de señalética (la familia DIN de los carteles de calle,
  // condensada) y el naranja como la luz de las pantallas: se usa una sola vez, en la acción.
  //
  // Nada de web fonts (Gmail las quita al pegar): la pila tira de las condensadas que ya trae
  // cada sistema. macOS/iOS: DIN Condensed. Windows 10+: Bahnschrift. Android: la condensada
  // de Roboto. Si ninguna existe, cae en Arial Narrow y luego en Trebuchet.
  const N = {
    // La noche es la del panel de hoy (#16141D) y no otra: el logo va aplanado sobre ese
    // color para Outlook, y con cualquier otro negro vuelve el recuadro alrededor del logo.
    noche: '#16141D', noche2: '#1F1C2A', hilo: '#302A3C',
    luz: '#F79131', texto: '#F4EFF7', apagado: '#B9AFC2', lila: '#CDA8DC',
    papel: '#FFFFFF', arena: '#F5F1EC', tinta: '#15111A', gris: '#5E5767', regla: '#E6E0E9',
    naranjaTinta: '#B35E0A', morado: '#85439A',
  };
  const FS = "'DIN Condensed','Bahnschrift SemiBold Condensed','Bahnschrift Condensed',Bahnschrift," +
    "'AvenirNextCondensed-Bold','Roboto Condensed',sans-serif-condensed,'Arial Narrow','Trebuchet MS',Arial,sans-serif";

  // Titular de señal: condensado, grande, interlineado apretado.
  const rotulo = (html, size, color, extra) =>
    '<div style="font-family:' + FS + ';font-size:' + size + 'px;line-height:' + Math.round(size * 1.04) + 'px;' +
    'font-weight:700;color:' + color + ';' + (extra || '') + '">' + html + '</div>';
  const cuerpo = (html, size, color, extra) =>
    '<div style="font-family:' + FB + ';font-size:' + size + 'px;line-height:' + Math.round(size * 1.6) + 'px;' +
    'color:' + color + ';' + (extra || '') + '">' + html + '</div>';
  // Enlace secundario: texto con flecha, sin caja. Solo hay UNA acción con fondo por correo.
  const flecha = (txt, url, color) =>
    '<a href="' + esc(url) + '" style="font-family:' + FS + ';font-size:18px;line-height:22px;font-weight:700;' +
    'color:' + color + ';text-decoration:none;">' + esc(txt) + '&nbsp;&rarr;</a>';
  // La acción principal: una señal rectangular a todo el ancho, como un rótulo de calle.
  const senal = (txt, url, fondo, color) =>
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
    '<td bgcolor="' + fondo + '" style="background:' + fondo + ';border-radius:3px;">' +
    '<a href="' + esc(url) + '" style="display:block;padding:18px 22px;font-family:' + FS + ';font-size:22px;' +
    'line-height:26px;font-weight:700;color:' + color + ';text-decoration:none;">' + esc(txt) + '&nbsp;&nbsp;&rarr;</a>' +
    '</td></tr></table>';
  const fotoDe = (st, s) => (st.cardAnim && !usaPortadas(st) ? carruselSrc(st, s) : svcImg(st, s));
  const imagen = (st, s, ancho, fondoAlt) =>
    '<a href="' + esc(linkFor(st, s)) + '"><img src="' + esc(fotoDe(st, s)) + '" width="' + ancho + '" alt="' +
    esc(svcAlt(st, s)) + '" style="display:block;width:100%;max-width:100%;height:auto;border:0;' +
    'color:' + fondoAlt + ';font-family:' + FB + ';font-size:14px;line-height:20px;"></a>';
  // Lista de requisitos: filas separadas por un hilo, sin viñetas ni números en círculo.
  const lista = (items, color, hilo) =>
    '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">' +
    items.map(t => '<tr><td style="border-top:1px solid ' + hilo + ';padding:11px 0;font-family:' + FB +
      ';font-size:15px;line-height:22px;color:' + color + ';">' + esc(t) + '</td></tr>').join('') +
    '<tr><td style="border-top:1px solid ' + hilo + ';font-size:0;line-height:0;">&nbsp;</td></tr></table>';

  // El bloque de cotizar, común a A y B: qué pasa ahora, qué hace falta y la única acción.
  function cotizar(st, k) {
    let h = '';
    if (on(st, 'pasos')) {
      const b = B(st, 'pasos');
      h += rotulo(esc(b.titulo), 30, k.texto) + cuerpo(nl2br(b.texto), 16, k.apagado, 'padding:10px 0 0 0;');
    }
    if (on(st, 'presupuesto')) {
      const b = B(st, 'presupuesto');
      h += cuerpo('<b style="color:' + k.texto + ';">' + esc(b.titulo) + '</b>', 15, k.texto, 'padding:22px 0 8px 0;') +
        lista(lines(b.items), k.texto, k.hilo);
    }
    if (on(st, 'suministro')) {
      const b = B(st, 'suministro');
      h += cuerpo('<b style="color:' + k.texto + ';">' + esc(b.titulo) + '.</b> ' + esc(b.texto) + ' ' +
        lines(b.requisitos).map(esc).join(' · ') + '.', 14, k.apagado, 'padding:18px 0 0 0;');
    }
    if (on(st, 'cta')) {
      h += '<div style="padding:26px 0 0 0;">' + senal(B(st, 'cta').texto, ctaHref(st), N.luz, N.tinta) + '</div>';
      if (B(st, 'cta').alternativa) h += cuerpo(esc(B(st, 'cta').alternativa), 14, k.apagado, 'padding:12px 0 0 0;');
    }
    return h;
  }

  function despedida(st, tema, k, fondo) {
    const P = [];
    let foot = '';
    if (on(st, 'cierre')) foot += cuerpo(nl2br(B(st, 'cierre').texto), 16, k.texto, 'padding:0 0 18px 0;');
    if (on(st, 'firma')) foot += firma(st, tema);
    if (foot) P.push(row(foot, 'padding:30px 28px 30px 28px;background:' + fondo + ';'));
    if (on(st, 'pie')) P.push(row(cuerpo(nl2br(B(st, 'pie').texto), 12, k.apagado), 'padding:0 28px 26px 28px;background:' + fondo + ';'));
    return P.join('');
  }

  // ── Plantilla A · "Cartelera" (Señal nocturna: cada espacio es una valla) ──
  // Cada espacio es una valla: la foto a sangre, de borde a borde, y debajo su placa con el
  // nombre en letra de señal. Se lee como una calle: una detrás de otra, con aire entre medias.
  function plantillaA(st) {
    const P = [];
    const k = { texto: N.texto, apagado: N.apagado, hilo: N.hilo };
    const fondo = 'background:' + N.noche + ';';
    P.push(row(marca(st, 'oscuro', 150), 'padding:26px 28px 0 28px;' + fondo));
    if (on(st, 'titulo')) {
      const b = B(st, 'titulo');
      P.push(row(rotulo(esc(b.texto), 54, N.texto, 'letter-spacing:-.01em;') +
        cuerpo(esc(b.sub), 15, N.lila, 'padding:10px 0 0 0;'), 'padding:40px 28px 6px 28px;' + fondo));
    }
    let intro = '';
    if (on(st, 'saludo')) intro += cuerpo(nl2br(fill(B(st, 'saludo').texto, st)), 17, N.texto, 'padding:0 0 10px 0;');
    if (on(st, 'intro')) intro += cuerpo(nl2br(fill(B(st, 'intro').texto, st)), 16, N.apagado);
    if (intro) P.push(row(intro, 'padding:22px 28px 34px 28px;' + fondo));
    const bq = bloquePerfil(st, true);
    if (bq) P.push(row(bq, 'padding:0 28px 30px 28px;' + fondo));
    activos(st).forEach(s => {
      P.push(row(imagen(st, s, 600, N.texto), 'font-size:0;line-height:0;' + fondo));
      P.push(row(
        rotulo(esc(s.nombre), 32, N.texto) +
        cuerpo(esc(s.cobertura), 15, N.apagado, 'padding:6px 0 0 0;') +
        (s.nota ? cuerpo(esc(s.nota), 13, N.apagado, 'padding:2px 0 0 0;opacity:.85;') : '') +
        '<div style="padding:14px 0 0 0;">' + flecha('Ver presentación', linkFor(st, s), N.luz) + '</div>',
        'padding:20px 28px 44px 28px;' + fondo));
    });
    const c = cotizar(st, k);
    if (c) P.push(row(c, 'padding:36px 28px 36px 28px;background:' + N.noche2 + ';'));
    P.push(despedida(st, 'oscuro', k, N.noche));
    return doc(st, P.join(''));
  }

  // ── Plantilla B · "Catálogo" (Señal nocturna, versión de día) ──
  // La versión clara: papel blanco y la tinta de un plano. Rompe la rejilla de tarjetas iguales:
  // el primer espacio va destacado a todo el ancho y los demás de dos en dos, sin cajas ni
  // bordes, la foto con la esquina viva como un cartel. En el móvil las parejas bajan solas.
  function plantillaB(st) {
    const P = [];
    const k = { texto: N.tinta, apagado: N.gris, hilo: N.regla };
    const fondo = 'background:' + N.papel + ';';
    P.push(row(marca(st, 'claro', 150), 'padding:28px 28px 0 28px;' + fondo));
    if (on(st, 'titulo')) {
      const b = B(st, 'titulo');
      P.push(row(rotulo(esc(b.texto), 48, N.tinta, 'letter-spacing:-.01em;') +
        cuerpo(esc(b.sub), 15, N.morado, 'padding:8px 0 0 0;'), 'padding:38px 28px 4px 28px;' + fondo));
    }
    let intro = '';
    if (on(st, 'saludo')) intro += cuerpo(nl2br(fill(B(st, 'saludo').texto, st)), 17, N.tinta, 'padding:0 0 10px 0;');
    if (on(st, 'intro')) intro += cuerpo(nl2br(fill(B(st, 'intro').texto, st)), 16, N.gris);
    if (intro) P.push(row(intro, 'padding:20px 28px 30px 28px;' + fondo));
    const bq = bloquePerfil(st, false);
    if (bq) P.push(row(bq, 'padding:0 28px 30px 28px;' + fondo));
    const placa = (s, grande) =>
      rotulo(esc(s.nombre), grande ? 30 : 23, N.tinta, 'padding:' + (grande ? 16 : 12) + 'px 0 0 0;') +
      cuerpo(esc(s.cobertura), grande ? 15 : 14, N.gris, 'padding:5px 0 0 0;') +
      '<div style="padding:10px 0 0 0;">' + flecha('Ver presentación', linkFor(st, s), N.naranjaTinta) + '</div>';
    const act = activos(st);
    if (act.length) {
      // Destacado: el primero, a todo el ancho de la columna.
      P.push(row(imagen(st, act[0], 544, N.tinta) + placa(act[0], true), 'padding:0 28px 34px 28px;' + fondo));
      // El resto de dos en dos. Tablas que flotan: lado a lado en el ordenador, una debajo
      // de otra en el móvil (la misma técnica con la que A y B dejaron de encogerse en el móvil).
      const resto = act.slice(1);
      for (let i = 0; i < resto.length; i += 2) {
        const par = resto.slice(i, i + 2);
        if (par.length === 1) {
          P.push(row(imagen(st, par[0], 544, N.tinta) + placa(par[0], true), 'padding:0 28px 34px 28px;' + fondo));
          continue;
        }
        const celda = (s, lado) =>
          '<table role="presentation" width="264" align="' + lado + '" cellpadding="0" cellspacing="0" border="0" ' +
          'style="width:264px;max-width:100%;margin:0 0 30px 0;"><tr><td valign="top">' +
          imagen(st, s, 264, N.tinta) + placa(s, false) + '</td></tr></table>';
        P.push(row(celda(par[0], 'left') +
          '<table role="presentation" width="16" align="left" cellpadding="0" cellspacing="0" border="0"><tr><td style="font-size:0;line-height:0;">&nbsp;</td></tr></table>' +
          celda(par[1], 'left'), 'padding:0 28px 4px 28px;' + fondo));
      }
    }
    const c = cotizar(st, k);
    if (c) P.push(row(c, 'padding:34px 28px 34px 28px;background:' + N.arena + ';'));
    P.push(despedida(st, 'claro', k, N.papel));
    return doc(st, P.join(''));
  }

  // ── Plantilla C · "Nota" (Señal nocturna: sigue pareciendo un correo escrito a mano) ──
  // Sigue pareciendo un correo escrito a mano: sin rótulos en mayúsculas ni botón de campaña.
  // La acción es un enlace en negrita, como lo pondría una persona.
  function plantillaC(st) {
    let body = '';
    const p = (html, extra) => '<p style="margin:0 0 14px 0;font-family:' + FB + ';font-size:15px;line-height:24px;color:' + N.tinta + ';' + (extra || '') + '">' + html + '</p>';
    if (on(st, 'saludo')) body += p(nl2br(fill(B(st, 'saludo').texto, st)));
    if (on(st, 'intro')) body += p(nl2br(fill(B(st, 'intro').texto, st)), 'margin-bottom:22px;');
    const bq = bloquePerfil(st, false);
    if (bq) body += '<div style="padding:0 0 18px 0;">' + bq + '</div>';
    activos(st).forEach(s => {
      body += '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 16px 0;"><tr>' +
        '<td width="112" valign="top"><a href="' + esc(linkFor(st, s)) + '"><img src="' + esc(svcImg(st, s)) + '" width="96" alt="' + esc(svcAlt(st, s)) + '" style="display:block;width:96px;height:auto;border:0;border-radius:3px;color:' + N.tinta + ';font-family:' + FB + ';font-size:12px;"></a></td>' +
        '<td valign="top" style="font-family:' + FB + ';font-size:15px;line-height:22px;color:' + N.tinta + ';">' +
        '<b>' + esc(s.nombre) + '</b><br><span style="color:' + N.gris + ';font-size:14px;">' + esc(s.cobertura) + '</span><br>' +
        '<a href="' + esc(linkFor(st, s)) + '" style="color:' + N.morado + ';font-size:14px;">Ver presentación</a></td></tr></table>';
    });
    if (on(st, 'pasos')) { const b = B(st, 'pasos'); body += p('<b>' + esc(b.titulo) + '.</b> ' + esc(b.texto), 'margin-top:10px;'); }
    if (on(st, 'presupuesto')) {
      const b = B(st, 'presupuesto');
      body += p(esc(b.titulo) + ': ' + lines(b.items).map(esc).join(', ') + '.');
    }
    if (on(st, 'suministro')) { const b = B(st, 'suministro'); body += p('<b>' + esc(b.titulo) + '.</b> ' + esc(b.texto) + ' ' + lines(b.requisitos).map(esc).join(' · ') + '.', 'color:' + N.gris + ';font-size:14px;'); }
    if (on(st, 'cta')) body += p('<a href="' + esc(ctaHref(st)) + '" style="color:' + N.morado + ';font-weight:700;">' + esc(B(st, 'cta').texto) + ' &rarr;</a>' + (B(st, 'cta').alternativa ? '<br><span style="color:' + N.gris + ';font-size:14px;">' + esc(B(st, 'cta').alternativa) + '</span>' : ''), 'margin:4px 0 22px 0;');
    if (on(st, 'cierre')) body += p(nl2br(B(st, 'cierre').texto), 'margin-bottom:22px;');
    if (on(st, 'firma')) body += firma(st, 'claro');
    if (on(st, 'pie')) body += '<p style="margin:22px 0 0 0;font-family:' + FB + ';font-size:11px;line-height:16px;color:' + N.gris + ';">' + nl2br(B(st, 'pie').texto) + '</p>';
    return doc(st, row(body, 'padding:8px 4px;background:' + N.papel + ';'));
  }

  // ── Plantilla D · "Cartelera móvil" (Señal nocturna: una columna, fotos a sangre) ──
  // La de las referencias (Digitel, Cashea) sin cajas dentro de cajas: la foto de cada grupo
  // a sangre, el título en letra de señal y un único botón de píldora por grupo.
  function plantillaD(st) {
    const P = [];
    const fondo = 'background:' + N.noche + ';';
    const pildora = (text, url, lleno) => '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td align="center" bgcolor="' + (lleno ? N.luz : N.noche) + '" style="background:' + (lleno ? N.luz : N.noche) + ';border:2px solid ' + N.luz + ';border-radius:40px;">' +
      '<a href="' + esc(url) + '" style="display:block;padding:15px 20px;font-family:' + FS + ';font-size:20px;line-height:24px;font-weight:700;color:' + (lleno ? N.tinta : N.luz) + ';text-decoration:none;">' + esc(text) + '</a></td></tr></table>';
    P.push(row(marca(st, 'oscuro', 150), 'padding:22px 24px 20px 24px;' + fondo));
    if (on(st, 'hero')) {
      const h = B(st, 'hero');
      const src = imgFor(st, st.heroAnim && h.anim ? h.anim : (usaPortadas(st) && h.imgPortada ? h.imgPortada : h.img));
      P.push(row('<img src="' + esc(src) + '" width="600" alt="' + esc(h.alt) + '" style="display:block;width:100%;max-width:100%;height:auto;border:0;color:' + N.texto + ';font-family:' + FB + ';font-size:14px;">', 'font-size:0;line-height:0;' + fondo));
    }
    if (on(st, 'titulo')) {
      const b = B(st, 'titulo');
      P.push(row(rotulo(esc(b.texto), 46, N.texto) + cuerpo(esc(b.sub), 15, N.lila, 'padding:8px 0 0 0;'), 'padding:30px 24px 4px 24px;' + fondo));
    }
    let intro = '';
    if (on(st, 'saludo')) intro += cuerpo(nl2br(fill(B(st, 'saludo').texto, st)), 18, N.texto, 'padding:0 0 10px 0;');
    if (on(st, 'intro')) intro += cuerpo(nl2br(fill(B(st, 'intro').texto, st)), 17, N.apagado);
    if (intro) P.push(row(intro, 'padding:18px 24px 30px 24px;' + fondo));
    const bq = bloquePerfil(st, true);
    if (bq) P.push(row(bq, 'padding:0 24px 26px 24px;' + fondo));
    const act = activos(st);
    GRUPOS.forEach(g => {
      const items = g.servicios.map(id => act.find(s => s.id === id)).filter(Boolean);
      if (!items.length) return;
      const lead = items[0];
      // La cabecera ya es la pantalla de Chacao: si el grupo abre con ella, se repetiria la misma
      // foto dos veces seguidas. Con cabecera, el grupo abre con el siguiente espacio.
      const foto = (on(st, 'hero') && lead.id === 'led' && items[1]) ? items[1] : lead;
      P.push(row(imagen(st, foto, 600, N.texto), 'font-size:0;line-height:0;' + fondo));
      let t = rotulo(esc(items.length === 1 ? lead.nombre : g.titulo), 32, N.texto);
      if (items.length === 1) {
        t += cuerpo(esc(lead.cobertura), 17, N.apagado, 'padding:8px 0 0 0;');
      } else {
        t += '<div style="padding:10px 0 0 0;">' + items.map(s =>
          '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
          '<td valign="top" style="border-top:1px solid ' + N.hilo + ';padding:12px 0;font-family:' + FB + ';font-size:17px;line-height:24px;color:' + N.texto + ';">' + esc(s.nombre) +
          '<br><span style="color:' + N.apagado + ';font-size:15px;">' + esc(s.cobertura) + '</span></td>' +
          '<td width="64" align="right" valign="top" style="border-top:1px solid ' + N.hilo + ';padding:14px 0 0 8px;"><a href="' + esc(linkFor(st, s)) + '" style="font-family:' + FS + ';font-size:18px;font-weight:700;color:' + N.luz + ';text-decoration:none;white-space:nowrap;">Ver &rarr;</a></td>' +
          '</tr></table>').join('') + '</div>';
      }
      t += '<div style="padding:18px 0 0 0;">' + pildora(lead.cta || 'Ver presentación', linkFor(st, lead), false) + '</div>';
      P.push(row(t, 'padding:20px 24px 40px 24px;' + fondo));
    });
    if (on(st, 'branding')) {
      const b = B(st, 'branding');
      P.push(row(rotulo(esc(b.titulo), 32, N.texto) + cuerpo(nl2br(b.texto), 17, N.apagado, 'padding:8px 0 0 0;') +
        '<div style="padding:18px 0 0 0;">' + pildora(b.cta, b.url, false) + '</div>', 'padding:6px 24px 40px 24px;border-top:1px solid ' + N.hilo + ';' + fondo));
    }
    let fin = '';
    if (on(st, 'pasos')) { const b = B(st, 'pasos'); fin += rotulo(esc(b.titulo), 32, N.texto) + cuerpo(nl2br(b.texto), 17, N.apagado, 'padding:8px 0 0 0;'); }
    if (on(st, 'presupuesto')) { const b = B(st, 'presupuesto'); fin += cuerpo('<b style="color:' + N.texto + ';">' + esc(b.titulo) + '</b>', 16, N.texto, 'padding:20px 0 8px 0;') + lista(lines(b.items), N.texto, N.hilo); }
    if (on(st, 'suministro')) { const b = B(st, 'suministro'); fin += cuerpo('Para proyectos de branding e instalación: ' + lines(b.requisitos).map(esc).join(' · ') + '.', 15, N.apagado, 'padding:14px 0 0 0;'); }
    if (on(st, 'cta')) {
      fin += '<div style="padding:24px 0 0 0;">' + pildora(B(st, 'cta').texto, ctaHref(st), true) + '</div>';
      if (B(st, 'cta').alternativa) fin += cuerpo(esc(B(st, 'cta').alternativa), 15, N.apagado, 'padding:14px 0 0 0;text-align:center;');
    }
    if (fin) P.push(row(fin, 'padding:32px 24px 34px 24px;background:' + N.noche2 + ';'));
    P.push(despedida(st, 'oscuro', { texto: N.texto, apagado: N.apagado, hilo: N.hilo }, N.noche));
    return doc(st, P.join(''));
  }

  // ── Texto plano (fallback y para clientes sin HTML) ──
  function renderText(st0) {
    const st = aplicaAsunto(aplicaPerfil(normaliza(st0)));
    const L = [];
    // La Entrega no es el catalogo: lo que se lee en texto plano es la propuesta, no la
    // lista de espacios. Se separa aqui y no en una funcion aparte para que quien copie
    // "solo texto" obtenga siempre lo que esta viendo.
    if (st.plantilla === 'H') {
      const e = B(st, 'entrega');
      if (on(st, 'saludo')) L.push(fill(B(st, 'saludo').texto, st), '');
      L.push(e.titulo.toUpperCase(), '');
      L.push(fill(e.texto, st), '');
      if (e.enlace || e.url) L.push(e.cta + ': ' + (e.enlace || e.url), '');
      if (activos(st).length) {
        L.push(e.acompanan + ':');
        activos(st).forEach(s => L.push('\u2022 ' + s.nombre + ' \u2014 ' + s.cobertura + ' \u2014 ' + linkFor(st, s)));
        L.push('');
      }
      if (on(st, 'firma')) L.push.apply(L, pieDeFirma(st));
      return L.join('\n');
    }
    if (on(st, 'saludo')) L.push(fill(B(st, 'saludo').texto, st), '');
    if (on(st, 'intro')) L.push(fill(B(st, 'intro').texto, st), '');
    if (on(st, 'titulo')) L.push(B(st, 'titulo').texto.toUpperCase(), '');
    activos(st).forEach(s => { L.push('• ' + s.nombre + ' — ' + s.cobertura + ' — ' + linkFor(st, s)); if (s.nota) L.push('  ' + s.nota); });
    if (activos(st).length) L.push('');
    if (on(st, 'suministro')) { const b = B(st, 'suministro'); L.push(b.titulo + ': ' + b.texto + ' ' + lines(b.requisitos).join(' / '), ''); }
    if (on(st, 'pasos')) { const b = B(st, 'pasos'); L.push(b.titulo, b.texto, ''); }
    if (on(st, 'presupuesto')) { const b = B(st, 'presupuesto'); L.push(b.titulo + ':'); lines(b.items).forEach((t, i) => L.push((i + 1) + ') ' + t)); L.push(''); }
    if (on(st, 'cierre')) L.push(B(st, 'cierre').texto, '');
    if (on(st, 'firma')) L.push.apply(L, pieDeFirma(st));
    return L.join('\n');
  }

  // La firma en texto plano. La usan el texto del correo, el de la Entrega y el de WhatsApp:
  // tres sitios es uno de mas para copiarla a mano.
  function pieDeFirma(st) {
    const f = B(st, 'firma'), dirs = correosDe(f), L = [];
    L.push(f.nombre, cargoDe(f), dirs[0] + ' \u00b7 ' + f.telefono);
    dirs.slice(1).forEach(function (d) { L.push(d); });
    L.push(f.ig + ' \u00b7 ' + webHref(f.web) + ' \u00b7 ' + f.direccion);
    return L;
  }

  // El mismo mensaje, para WhatsApp (FR-116, FR-118).
  //
  // Dos reglas que no son de estilo sino de como funciona WhatsApp: solo previsualiza el
  // PRIMER enlace del mensaje, y solo si va donde lo encuentre pronto. Por eso el enlace
  // abre el mensaje y por eso no se anaden mas: cada enlace de mas es una tarjeta menos.
  function renderWhatsApp(st0) {
    const st = aplicaAsunto(aplicaPerfil(normaliza(st0)));
    const e = B(st, 'entrega');
    const L = [];
    if (e.enlace || e.url) L.push(e.enlace || e.url, '');
    if (on(st, 'saludo')) L.push(fill(B(st, 'saludo').texto, st));
    L.push(fill(e.corto, st), '');
    const f = B(st, 'firma');
    L.push(f.nombre + ' \u00b7 ' + cargoDe(f));
    L.push(correosDe(f)[0] + ' \u00b7 ' + f.telefono);
    return L.join('\n');
  }

  // -- Formato E - "Inventario" (asesor, para agencias) -------------------------
  // Su idea: una agencia no quiere que le eduquen, quiere la tabla. El correo entero es
  // una ficha de inventario con metricas comparables, sin parrafo introductorio de mas.
  function plantillaE(st) {
    const tema = temaDe(st), o = tema !== 'claro', k = paleta(tema), P = [];
    const a = B(st, 'asesor'), x = B(st, 'inventario'), tb = B(st, 'tablaInventario');
    const pad = 'padding-left:32px;padding-right:32px;background:' + k.panel + ';';
    const n = activos(st).length;
    const h = t => huecos(t, { periodo: a.periodo, frentes: cuantos(n), n: n,
      destinatario: st.destinatario || '[Nombre de la Agencia]' });
    const acento = '<span style="color:' + k.acento + ';">';

    P.push(row(cabeceraAsesor(st, P, a.etiquetaMeta),
      'padding:26px 32px 22px 32px;background:' + k.panel + ';'));

    // Hero. El acento va en "Share of Voice" porque es el termino que la agencia busca.
    P.push(row(
      epigrafe(st, h(x.epigrafe)) +
      '<div style="font-family:' + FH + ';font-size:40px;line-height:1.02;font-weight:800;letter-spacing:-.035em;color:' + k.texto + ';">' +
        realce(h(x.titulo), acento, '</span>') + '</div>' +
      '<div style="font-family:' + FB + ';font-size:15px;line-height:1.6;color:' + k.apagado + ';padding:16px 0 0 0;">' +
        realce(h(x.entrada), '<b>', '</b>') + '</div>',
      pad + 'padding-bottom:26px;'));

    if (on(st, 'saludo')) {
      P.push(row(
        epigrafe(st, h(x.saludoEpigrafe), k.acento) +
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.texto + ';">' +
          realce(h(x.saludo1), '<b>', '</b>') + '</div>' +
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.apagado + ';padding:12px 0 0 0;">' +
          realce(h(x.saludo2), '<b>', '</b>') + '</div>',
        pad + 'padding-bottom:24px;'));
    }

    // Tira de cifras: tres datos que la agencia reconoce de un vistazo.
    const cifra = function (n, l) {
      return '<td width="33%" valign="top" style="padding:14px 10px;border-top:1px solid ' + k.linea + ';border-bottom:1px solid ' + k.linea + ';">' +
        '<div style="font-family:' + FH + ';font-size:17px;font-weight:800;color:' + k.vivo + ';">' + esc(n) + '</div>' +
        '<div style="font-family:' + FH + ';font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:' + k.apagado + ';padding:4px 0 0 0;">' + esc(l) + '</div></td>';
    };
    P.push(row('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      cifra(h(x.cifra1), h(x.etiqueta1)) + cifra(h(x.cifra2), h(x.etiqueta2)) + cifra(h(x.cifra3), h(x.etiqueta3)) +
      '</tr></table>', pad + 'padding-bottom:26px;'));

    // La tabla de inventario: el corazon de su diseno.
    P.push(row(epigrafe(st, h(x.seccion), k.acento) +
      '<div style="font-family:' + FH + ';font-size:24px;font-weight:800;letter-spacing:-.02em;color:' + k.texto + ';">' + realce(h(x.seccionTitulo), acento, '</span>') + '</div>' +
      '<div style="font-family:' + FB + ';font-size:13px;color:' + k.apagado + ';padding:5px 0 0 0;">' + realce(h(x.seccionSub), '<b>', '</b>') + '</div>',
      pad + 'padding-bottom:16px;'));

    // La tabla sale de su bloque de datos. {medida} la pone la ficha oficial de cada espacio:
    // la medida de una pantalla no se escribe a mano en ningun sitio.
    const fila = (num, id, badge) => ({ n: num, id: id, badge: badge, t: h(tb[id + '_titulo']),
      d: huecos(h(tb[id + '_detalle']), { medida: (FICHA[id] || {}).medida }),
      m: [[h(tb[id + '_dato1']), h(tb[id + '_valor1'])], [h(tb[id + '_dato2']), h(tb[id + '_valor2'])]] });
    const INVENTARIO = [fila('01', 'led', a.slotsLed), fila('02', 'mercedes', ''), fila('03', 'vallas', ''),
      fila('04', 'rider', h(tb.rider_distintivo)), fila('05', 'totem', '')];
    const vivos = activos(st).map(function (x) { return x.id; });
    let tabla = '';
    INVENTARIO.filter(function (f) { return vivos.indexOf(f.id) >= 0; }).forEach(function (f, i) {
      const cebra = i % 2 ? k.panel2 : k.panel;
      const svc = st.servicios.filter(function (x) { return x.id === f.id; })[0];
      tabla += '<tr><td bgcolor="' + cebra + '" style="background:' + cebra + ';padding:16px 14px;border-bottom:1px solid ' + k.linea + ';">' +
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
        '<td width="26" valign="top" style="font-family:' + FH + ';font-size:11px;font-weight:800;color:' + k.apagado + ';padding-top:3px;">' + f.n + '</td>' +
        '<td valign="top">' +
          '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + k.texto + ';">' + esc(f.t) +
            (f.badge ? ' <span style="font-family:' + FH + ';font-size:9px;font-weight:800;letter-spacing:.14em;color:' + k.sobreVivo + ';background:' + k.vivo + ';padding:3px 7px;border-radius:100px;">' + esc(f.badge) + '</span>' : '') +
          '</div>' +
          '<div style="font-family:' + FB + ';font-size:12px;line-height:17px;color:' + k.apagado + ';padding:5px 0 0 0;">' + esc(f.d) + '</div>' +
          (svc ? '<div style="padding:7px 0 0 0;"><a href="' + esc(linkFor(st, svc)) + '" style="font-family:' + FH + ';font-size:11px;font-weight:800;color:' + k.acento + ';text-decoration:none;">Ver presentaci\u00f3n &rarr;</a></div>' : '') +
        '</td>' +
        '<td width="150" valign="top" align="right">' +
          f.m.map(function (par) {
            return '<div style="font-family:' + FH + ';font-size:9px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;color:' + k.apagado + ';">' + esc(par[0]) + '</div>' +
              '<div style="font-family:' + FH + ';font-size:13px;font-weight:800;color:' + k.texto + ';padding:1px 0 7px 0;">' + esc(par[1]) + '</div>';
          }).join('') +
        '</td></tr></table></td></tr>';
    });
    P.push(row('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border-top:1px solid ' + k.linea + ';">' + tabla + '</table>',
      pad + 'padding-bottom:24px;'));

    // La foto del frente principal, con mi carrusel animado.
    const led = st.servicios.filter(function (x) { return x.id === 'led' && x.on; })[0];
    if (led) {
      P.push(row(fotoServicio(st, led, 536) +
        '<div style="font-family:' + FB + ';font-size:12px;color:' + k.apagado + ';padding:9px 0 0 0;">' +
        '&uarr; ' + realce(h(x.pieFoto), '<b>', '</b>') + '</div>',
        pad + 'padding-bottom:22px;'));
    }

    // Disponibilidad: los datos que caducan salen del estado, no del codigo.
    P.push(row('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td bgcolor="' + k.panel2 + '" style="background:' + k.panel2 + ';border-left:3px solid ' + k.vivo + ';padding:14px 16px;">' +
      '<div style="font-family:' + FH + ';font-size:10px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:' + k.vivo + ';">' +
        '\u25cf ' + esc(h(x.dispoEtiqueta)) + ' ' + esc(a.dispoFecha) + '</div>' +
      '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + k.texto + ';padding:6px 0 0 0;">' +
        esc(a.dispoTexto) + ' ' + esc(a.cierreTexto) + '</div>' +
      '</td></tr></table>', pad + 'padding-bottom:24px;'));

    if (on(st, 'cta')) {
      P.push(row(botonAsesor(st, B(st, 'asesor').botonTexto || 'Solicitar disponibilidad Q1', ctaHref(st)) +
        '<div style="font-family:' + FB + ';font-size:12px;color:' + k.apagado + ';padding:12px 0 0 0;">' + esc(a.pieCta) + '</div>',
        pad + 'padding-bottom:28px;'));
    }

    // Complementos: los servicios sin foto propia en su diseno original.
    const comp = complementos(st, ['led']);
    if (comp) P.push(row(comp, pad + 'padding-bottom:26px;'));

    // Mi firma, por decision del cliente: la suya no lleva el correo de mercadeo.
    if (on(st, 'firma')) {
      P.push(row(firma(st, tema),
        'padding:24px 32px 26px 32px;background:' + k.panel + ';border-top:1px solid ' + k.linea + ';'));
    }
    if (on(st, 'pie')) {
      P.push(row('<div style="font-family:' + FB + ';font-size:11px;line-height:16px;color:' + k.apagado + ';">' +
        nl2br(B(st, 'pie').texto) + '</div>', 'padding:0 32px 24px 32px;background:' + k.panel + ';'));
    }
    return doc(st, P.join(''));
  }

  // -- Formato F - "Guia" (asesor, para cliente nuevo) --------------------------
  // Su idea: quien nunca ha comprado exterior no necesita un catalogo, necesita que le
  // quiten el miedo. Tres fases en orden, cada una con el servicio que le corresponde.
  function plantillaF(st) {
    const tema = temaDe(st), o = tema !== 'claro', k = paleta(tema), P = [];
    const a = B(st, 'asesor'), g = B(st, 'guia');
    const pad = 'padding-left:32px;padding-right:32px;background:' + k.panel + ';';
    const h = t => huecos(t, { destinatario: st.destinatario || '[Nombre]' });

    P.push(row(cabeceraAsesor(st, P, h(g.meta)),
      'padding:26px 32px 22px 32px;background:' + k.panel + ';'));

    P.push(row(
      '<div style="font-family:' + FH + ';font-size:36px;line-height:1.06;font-weight:800;letter-spacing:-.03em;color:' + k.texto + ';">' +
        realce(h(g.titulo), '<span style="color:' + k.acento + ';">', '</span>') + '</div>' +
      '<div style="font-family:' + FB + ';font-size:15px;line-height:1.6;color:' + k.apagado + ';padding:16px 0 0 0;">' +
        realce(h(g.entrada), '<b>', '</b>') + '</div>',
      // El aire de arriba lo daba el epigrafe que habia aqui. Al quitarlo, el titular de
      // 36 px se quedaba a 22 px de la cabecera; esto le devuelve el respiro.
      pad + 'padding-top:12px;padding-bottom:26px;'));

    if (on(st, 'saludo')) {
      P.push(row(
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.texto + ';">' +
          realce(h(g.saludo), '<b>', '</b>') + '</div>' +
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.apagado + ';padding:10px 0 0 0;">' +
          realce(h(g.parrafo), '<b style="color:' + k.texto + ';">', '</b>') + '</div>',
        pad + 'padding-bottom:26px;'));
    }

    // Las tres fases. Cada una lleva su servicio con mi carrusel animado.
    const fase = (num, id) => ({ n: String(num).padStart(2, '0'), id: id,
      fase: h(g['fase' + num]), tit: h(g['fase' + num + 'Titulo']),
      txt: realce(h(g['fase' + num + 'Texto']), '<b>', '</b>'), tag: h(g['fase' + num + 'Etiqueta']),
      svcTit: h(g['fase' + num + 'Servicio']), svcTxt: h(g['fase' + num + 'Detalle']) });
    const FASES = [fase(1, 'totem'), fase(2, 'led'), fase(3, 'rider')];
    FASES.forEach(function (f) {
      const svc = st.servicios.filter(function (x) { return x.id === f.id && x.on; })[0];
      P.push(row(
        '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
        '<td width="54" valign="top" style="font-family:' + FH + ';font-size:34px;font-weight:800;color:' + k.acento + ';letter-spacing:-.03em;">' + f.n + '</td>' +
        '<td valign="top">' +
          '<div style="font-family:' + FH + ';font-size:10px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:' + k.vivo + ';">' + esc(f.fase) + '</div>' +
          '<div style="font-family:' + FH + ';font-size:21px;font-weight:800;letter-spacing:-.02em;color:' + k.texto + ';padding:4px 0 8px 0;">' + esc(f.tit) + '</div>' +
          '<div style="font-family:' + FB + ';font-size:14px;line-height:21px;color:' + k.apagado + ';">' + f.txt + '</div>' +
        '</td></tr></table>' +
        (svc ?
          '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:14px 0 0 0;"><tr>' +
          '<td bgcolor="' + k.panel2 + '" style="background:' + k.panel2 + ';border:1px solid ' + k.linea + ';border-radius:10px;padding:14px;">' +
          '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
          '<td width="180" valign="top" style="font-size:0;line-height:0;">' + fotoServicio(st, svc, 180) + '</td>' +
          '<td valign="top" style="padding:0 0 0 14px;">' +
            '<div style="font-family:' + FH + ';font-size:9px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:' + k.vivo + ';">' + esc(f.tag) + '</div>' +
            '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + k.texto + ';padding:5px 0 4px 0;">' + esc(f.svcTit) + '</div>' +
            '<div style="font-family:' + FB + ';font-size:13px;line-height:18px;color:' + k.apagado + ';">' + esc(f.svcTxt) + '</div>' +
            '<div style="padding:7px 0 0 0;"><a href="' + esc(linkFor(st, svc)) + '" style="font-family:' + FH + ';font-size:11px;font-weight:800;color:' + k.acento + ';text-decoration:none;">Ver presentaci\u00f3n &rarr;</a></div>' +
          '</td></tr></table></td></tr></table>' : ''),
        pad + 'padding-bottom:28px;'));
    });

    P.push(row(
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td bgcolor="' + k.panel2 + '" style="background:' + k.panel2 + ';border-left:3px solid ' + k.acento + ';padding:16px 18px;">' +
      '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + k.texto + ';">' + realce(h(g.cajaTitulo), '<span style="color:' + k.acento + ';">', '</span>') + '</div>' +
      '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + k.apagado + ';padding:6px 0 0 0;">' +
        realce(h(g.cajaTexto), '<b>', '</b>') + '</div>' +
      '</td></tr></table>', pad + 'padding-bottom:26px;'));

    if (on(st, 'cta')) {
      P.push(row(
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.6;color:' + k.texto + ';padding:0 0 14px 0;">' +
          realce(h(g.ctaTexto), '<b>', '</b>') + '</div>' +
        botonAsesor(st, h(g.boton), ctaHref(st)) +
        '<div style="font-family:' + FB + ';font-size:12px;color:' + k.apagado + ';padding:12px 0 0 0;">' + esc(a.respuesta) + '</div>',
        pad + 'padding-bottom:28px;'));
    }

    const compF = complementos(st, ['totem', 'led', 'rider'], { titulo: false });
    if (compF) P.push(row(compF, pad + 'padding-bottom:26px;'));

    if (on(st, 'firma')) {
      P.push(row(firma(st, tema),
        'padding:24px 32px 26px 32px;background:' + k.panel + ';border-top:1px solid ' + k.linea + ';'));
    }
    if (on(st, 'pie')) {
      P.push(row('<div style="font-family:' + FB + ';font-size:11px;line-height:16px;color:' + k.apagado + ';">' +
        nl2br(B(st, 'pie').texto) + '</div>', 'padding:0 32px 24px 32px;background:' + k.panel + ';'));
    }
    return doc(st, P.join(''));
  }

  // -- Formato G - "Phygital" (asesor) ------------------------------------------
  // Su idea: no explicar el concepto, contarlo como escena. Dos momentos con hora, la
  // calle y el movil, y el puente entre los dos.
  function plantillaG(st) {
    const tema = temaDe(st), o = tema !== 'claro', k = paleta(tema), P = [];
    const pad = 'padding-left:32px;padding-right:32px;background:' + k.panel + ';';
    const p = B(st, 'phygital');
    const h = t => huecos(t, { destinatario: st.destinatario || '[Nombre]' });
    // En un titulo que ya va en negrita, la negrita no se nota: ahi el realce es el color.
    const b = t => realce(h(t), '<b>', '</b>');
    const c = t => realce(h(t), '<span style="color:' + k.acento + ';">', '</span>');

    P.push(row(cabeceraAsesor(st, P, h(p.meta)),
      'padding:26px 32px 22px 32px;background:' + k.panel + ';'));

    P.push(row(
      epigrafe(st, h(p.epigrafe)) +
      '<div style="font-family:' + FH + ';font-size:40px;line-height:1.02;font-weight:800;letter-spacing:-.035em;color:' + k.texto + ';">' +
        realce(h(p.titulo), '<span style="color:' + k.vivo + ';">', '</span>') + '</div>',
      pad + 'padding-bottom:24px;'));

    if (on(st, 'saludo')) {
      P.push(row(
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.texto + ';">' +
          b(p.saludo) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.apagado + ';padding:10px 0 0 0;">' +
          realce(h(p.parrafo), '<b style="color:' + k.texto + ';">', '</b>') + '</div>',
        pad + 'padding-bottom:26px;'));
    }

    // Escena 01: la calle.
    const led = st.servicios.filter(function (x) { return x.id === 'led' && x.on; })[0];
    P.push(row(
      '<div style="font-family:' + FH + ';font-size:11px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:' + k.vivo + ';padding:0 0 10px 0;">' +
        '\u25cf ' + b(p.hora1) + '</div>' +
      (led ? fotoServicio(st, led, 536) : '') +
      '<div style="font-family:' + FH + ';font-size:10px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:' + k.apagado + ';padding:12px 0 4px 0;">' + b(p.escena1) + '</div>' +
      '<div style="font-family:' + FB + ';font-size:15px;line-height:1.6;color:' + k.texto + ';">' +
        b(p.escena1Texto) + '</div>' +
      '<div style="font-family:' + FH + ';font-size:11px;font-weight:800;letter-spacing:.2em;color:' + k.vivo + ';padding:14px 0 0 0;">' + b(p.puente) + ' &darr;</div>',
      pad + 'padding-bottom:26px;'));

    // Escena 02: el movil. Maqueta de la publicacion, construida con tablas.
    P.push(row(
      '<div style="font-family:' + FH + ';font-size:11px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:' + k.acento + ';padding:0 0 10px 0;">' +
        '\u25cf ' + b(p.hora2) + '</div>' +
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td bgcolor="' + k.panel2 + '" style="background:' + k.panel2 + ';border:1px solid ' + k.linea + ';border-radius:12px;padding:14px 16px;">' +
        '<div style="font-family:' + FH + ';font-size:13px;font-weight:800;color:' + k.texto + ';">' + b(p.cuenta) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:11px;color:' + k.apagado + ';padding:2px 0 10px 0;">' + b(p.lugar) + '</div>' +
        '<div style="font-family:' + FH + ';font-size:10px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:' + k.vivo + ';">' + b(p.filtro) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.5;color:' + k.texto + ';padding:8px 0 10px 0;">' +
          realce(h(p.publicacion), '<span style="color:' + k.acento + ';">', '</span>') + '</div>' +
        '<div style="font-family:' + FH + ';font-size:12px;font-weight:800;color:' + k.texto + ';">' + b(p.meGusta) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:13px;line-height:19px;color:' + k.apagado + ';padding:8px 0 0 0;">' +
          b(p.comentario) + '</div>' +
      '</td></tr></table>', pad + 'padding-bottom:26px;'));

    P.push(row(
      '<div style="font-family:' + FH + ';font-size:26px;line-height:1.15;font-weight:800;letter-spacing:-.025em;color:' + k.texto + ';">' +
        c(p.remate) + '</div>' +
      '<div style="font-family:' + FB + ';font-size:15px;line-height:1.6;color:' + k.apagado + ';padding:10px 0 0 0;">' +
        b(p.remateTexto) + '</div>',
      pad + 'padding-bottom:26px;'));

    // Como se arma: tres piezas.
    P.push(row(epigrafe(st, h(p.comoEpigrafe), k.acento) +
      '<div style="font-family:' + FB + ';font-size:14px;color:' + k.apagado + ';padding:0 0 4px 0;">' +
      b(p.comoTexto) + '</div>', pad + 'padding-bottom:12px;'));

    const PIEZAS = [1, 2, 3].map(num => ({ n: '0' + num, t: h(p['pieza' + num]), d: h(p['pieza' + num + 'Texto']) }));
    let piezas = '';
    PIEZAS.forEach(function (z) {
      piezas += '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="margin:0 0 12px 0;"><tr>' +
        '<td width="40" valign="top" style="font-family:' + FH + ';font-size:13px;font-weight:800;color:' + k.vivo + ';padding-top:2px;">' + z.n + '</td>' +
        '<td valign="top" style="border-left:1px solid ' + k.linea + ';padding:0 0 0 14px;">' +
          '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + k.texto + ';">' + esc(z.t) + '</div>' +
          '<div style="font-family:' + FB + ';font-size:13px;line-height:19px;color:' + k.apagado + ';padding:4px 0 0 0;">' + esc(z.d) + '</div>' +
        '</td></tr></table>';
    });
    P.push(row(piezas, pad + 'padding-bottom:22px;'));

    P.push(row(
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td bgcolor="' + k.panel2 + '" style="background:' + k.panel2 + ';border-left:3px solid ' + k.vivo + ';padding:16px 18px;">' +
      '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + k.texto + ';">' + c(p.cajaTitulo) + '</div>' +
      '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + k.apagado + ';padding:6px 0 0 0;">' +
        b(p.cajaTexto) + '</div>' +
      '</td></tr></table>', pad + 'padding-bottom:26px;'));

    if (on(st, 'cta')) {
      P.push(row(botonAsesor(st, h(p.boton), ctaHref(st)) +
        '<div style="font-family:' + FB + ';font-size:12px;color:' + k.apagado + ';padding:12px 0 0 0;">' +
        b(p.pieBoton) + '</div>',
        pad + 'padding-bottom:28px;'));
    }

    const compG = complementos(st, ['led']);
    if (compG) P.push(row(compG, pad + 'padding-bottom:26px;'));

    if (on(st, 'firma')) {
      P.push(row(firma(st, tema),
        'padding:24px 32px 26px 32px;background:' + k.panel + ';border-top:1px solid ' + k.linea + ';'));
    }
    if (on(st, 'pie')) {
      P.push(row('<div style="font-family:' + FB + ';font-size:11px;line-height:16px;color:' + k.apagado + ';">' +
        nl2br(B(st, 'pie').texto) + '</div>', 'padding:0 32px 24px 32px;background:' + k.panel + ';'));
    }
    return doc(st, P.join(''));
  }

  // -- Formato H - "Entrega" (la presentacion propia del cliente) ---------------------
  //
  // Los formatos A-G responden a una solicitud: ensenan el catalogo. Este entrega lo que
  // vino despues, cuando el cliente ya mostro interes y el equipo le armo SU presentacion.
  // Por eso el orden se invierte: primero la propuesta, y los servicios del catalogo van
  // al final, como lo que la acompana.
  //
  // Se arma con los mismos bloques que el resto -cabecera, epigrafe, boton, complementos,
  // firma, pie- porque una plantilla escrita a mano seria una segunda fuente de verdad, y
  // este proyecto ya pago dos veces ese precio (constitucion, principio II).
  // Suministro e instalacion, y los proximos pasos. Se escriben aparte porque la Personalizada
  // los pinta con la paleta del tema elegido -claro, oscuro o el de la marca- mientras que A-G
  // los llevan con colores fijos. El CONTENIDO es el mismo en las dos: sale de `B(st, ...)`, que
  // es lo que evita tener dos versiones del mismo parrafo.
  function bloqueSuministro(st, k) {
    const b = B(st, 'suministro');
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td width="4" bgcolor="' + k.vivo + '" style="background:' + k.vivo + ';font-size:0;">&nbsp;</td>' +
      '<td style="padding:14px 18px;background:' + k.panel2 + ';">' +
      '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + k.texto + ';padding:0 0 6px 0;">' +
        esc(b.titulo) + '</div>' +
      '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + k.apagado + ';padding:0 0 8px 0;">' +
        nl2br(b.texto) + '</div>' +
      bullets(lines(b.requisitos), k.vivo, k.texto) + '</td></tr></table>';
  }

  function bloquePasos(st, k) {
    // Los dos van juntos y en este orden: primero que hay que hacer, luego que hay que mandar.
    // Uno sin el otro deja la frase a medias, asi que llevan un solo interruptor.
    const a = B(st, 'pasos'), b = B(st, 'presupuesto');
    return '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + k.texto + ';padding:0 0 6px 0;">' +
        esc(a.titulo) + '</div>' +
      '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + k.apagado + ';padding:0 0 12px 0;">' +
        nl2br(a.texto) + '</div>' +
      '<div style="font-family:' + FB + ';font-size:14px;font-weight:700;color:' + k.texto + ';padding:0 0 8px 0;">' +
        esc(b.titulo) + '</div>' +
      numbered(lines(b.items), k.vivo, k.sobreVivo, k.texto);
  }

  function plantillaH(st) {
    const tema = temaDe(st), o = tema !== 'claro', k = paleta(tema), P = [];
    const e = B(st, 'entrega');
    const pad = 'padding-left:32px;padding-right:32px;background:' + k.panel + ';';
    // Lo que se manda es el enlace propio de la entrega: registra la apertura y permite el
    // aviso de interes. El de Canva es solo el destino final, y queda al otro lado.
    // Mientras la entrega no este guardada se usa el de Canva, para poder ver la plantilla.
    const url = e.enlace || e.url || '#';

    P.push(row(cabeceraAsesor(st, P, e.meta, e.empresa),
      'padding:26px 32px 22px 32px;background:' + k.panel + ';'));

    // Sin epigrafe sobre el titulo: el rotulo de la cabecera ya dice de que va esto, y dos
    // etiquetas seguidas antes del titular solo retrasan la lectura.
    P.push(row(
      '<div style="font-family:' + FH + ';font-size:34px;line-height:1.08;font-weight:800;' +
        'letter-spacing:-.03em;color:' + k.texto + ';">' + esc(e.titulo) + '</div>',
      pad + 'padding-bottom:22px;'));

    let cuerpo = '';
    if (on(st, 'saludo')) {
      cuerpo += '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.texto + ';">' +
        nl2br(fill(B(st, 'saludo').texto, st)) + '</div>';
    }
    cuerpo += '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.apagado + ';' +
      'padding:10px 0 0 0;">' + nl2br(fill(e.texto, st)) + '</div>';
    P.push(row(cuerpo, pad + 'padding-bottom:24px;'));

    // La portada, enlazada a la propia presentacion. El texto alternativo tiene que bastar
    // con las imagenes bloqueadas, que es como la abre medio Outlook (principio III).
    if (e.img) {
      P.push(row(
        '<a href="' + esc(url) + '"><img src="' + esc(entregaImg(st, e.img)) + '" width="536"' +
        ' alt="' + esc(e.alt) + '" style="display:block;width:536px;max-width:100%;height:auto;' +
        'border:0;border-radius:10px;color:' + k.texto + ';font-family:' + FB + ';font-size:13px;' +
        'line-height:18px;"></a>',
        pad + 'padding-bottom:22px;'));
    }

    P.push(row(botonAsesor(st, e.cta, url), pad + 'padding-bottom:28px;'));

    // Los servicios que acompanan la propuesta. Ninguno mostrado antes, asi que entran todos
    // los que sigan activos: quitarlos es apagarlos en el panel.
    const compH = complementos(st, [], { titulo: e.acompanan, columnas: 1 });
    if (compH) P.push(row(compH, pad + 'padding-bottom:26px;'));

    if (e.conSuministro) P.push(row(bloqueSuministro(st, k), pad + 'padding-bottom:18px;'));
    if (e.conPasos) P.push(row(bloquePasos(st, k), pad + 'padding-bottom:22px;'));

    // La despedida, lo ultimo antes de la firma. Vacia, no deja hueco.
    if (e.cierre) {
      P.push(row('<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.texto + ';">' +
        nl2br(fill(e.cierre, st)) + '</div>', pad + 'padding-bottom:26px;'));
    }

    if (on(st, 'firma')) {
      P.push(row(firma(st, tema),
        'padding:24px 32px 26px 32px;background:' + k.panel + ';border-top:1px solid ' + k.linea + ';'));
    }
    // Sin pie. El de A-G explica POR QUÉ recibes el correo —es un envío de catálogo—; una
    // propuesta que llega con tu nombre y tu empresa en la cabecera no tiene nada que explicar, y
    // la firma de arriba ya lleva el correo y el teléfono. Además el que había no se podía tocar:
    // esto pintaba `bloques.entrega.pie` y el panel editaba `bloques.pie`, que es otro campo.
    return doc(st, P.join(''));
  }

  const TEMPLATES = {
    A: { nombre: 'Cartelera', desc: 'Oscura. Cada espacio es una valla: la foto a sangre y su nombre en letra de señal. Para primer envío.', fn: plantillaA },
    B: { nombre: 'Catálogo', desc: 'Clara. Un espacio destacado y los demás de dos en dos, sin cajas. Para lectura rápida.', fn: plantillaB },
    C: { nombre: 'Nota', desc: 'Parece un correo escrito a mano: sin rótulos ni botón de campaña. Para responder en hilo.', fn: plantillaC },
    D: { nombre: 'Cartelera móvil', desc: 'Una columna, fotos a sangre, letra de señal y un solo botón principal. Pensada para Gmail en el teléfono.', fn: plantillaD },
    E: { nombre: 'Inventario', desc: 'Asesor de diseño · para agencias. Tabla de inventario con métricas comparables, sin brief educativo. Claro u oscuro.', fn: plantillaE },
    F: { nombre: 'Guía', desc: 'Asesor de diseño · para cliente nuevo. Tres fases en orden: que te conozcan, que te recuerden, que te compren. Claro u oscuro.', fn: plantillaF },
    G: { nombre: 'Phygital', desc: 'Asesor de diseño · la escena de las 9:00 AM. La calle capta, el móvil cierra. Claro u oscuro.', fn: plantillaG },
    H: { nombre: 'Personalizada', desc: 'Para entregar la presentación propia de un cliente: su enlace, sus imágenes y los servicios que la acompañan. Claro u oscuro.', fn: plantillaH },
  };
  function pick(st) {
    if (st.plantilla && TEMPLATES[st.plantilla]) return st.plantilla;
    const keys = Object.keys(TEMPLATES);
    return keys[Math.abs(Number(st.seed) || 0) % keys.length];
  }
  const temaEntregaDe = st => {
    const t = st.temaEntrega || st.tema;
    return TEMAS.indexOf(t) >= 0 ? t : 'claro';
  };
  const render = (st, key) => {
    const k = key || pick(st);
    const listo = aplicaAsunto(aplicaPerfil(normaliza(st)));
    // Solo la Personalizada mira su propio aspecto, y sobre una COPIA: `tema` sigue siendo
    // el del catalogo y no se toca, que es lo que evita que el morado reaparezca alli.
    return TEMPLATES[k].fn(k === 'H'
      ? Object.assign({}, listo, { tema: temaEntregaDe(listo) })
      : listo);
  };

  // ── ¿Cambia el correo si se toca este campo? ──
  // El panel es uno para las ocho plantillas y cada una usa una parte: E, F y G ignoran el texto
  // del saludo, la introduccion y el boton; el interruptor del asesor no cambiaba nada en
  // ninguna. Sin decirlo, el panel mentia: se escribia y no pasaba nada.
  //
  // En vez de una lista a mano de que usa cada plantilla -que caducaria con el primer cambio-,
  // se pregunta al propio motor: se cambia el campo en una COPIA, se renderiza, y si el correo
  // sale identico, ese campo no pinta nada aqui. Unos 0,2 ms por prueba.
  const leeRuta = (o, p) => p.split('.').reduce((a, k) => a == null ? a : a[k], o);
  const ponRuta = (o, p, v) => { const ks = p.split('.'); const u = ks.pop(); ks.reduce((a, k) => a[k], o)[u] = v; };
  const TESTIGO = '⁣·testigo·';
  function cambiaElCorreo(st, key, ruta) {
    const copia = () => {
      const s = JSON.parse(JSON.stringify(st));
      // Un campo de un bloque apagado no sale PORQUE el bloque esta apagado, no porque la
      // plantilla no lo use: se prueba con su bloque o su servicio encendido.
      const m = /^bloques\.([^.]+)\./.exec(ruta);
      if (m && s.bloques && s.bloques[m[1]]) s.bloques[m[1]].on = true;
      const n = /^servicios\.(\d+)\./.exec(ruta);
      if (n && s.servicios && s.servicios[+n[1]]) s.servicios[+n[1]].on = true;
      return s;
    };
    try {
      const a = copia(), b = copia();
      const v = leeRuta(b, ruta);
      if (typeof v === 'boolean') ponRuta(b, ruta, !v);
      else if (Array.isArray(v)) ponRuta(b, ruta, v.concat([TESTIGO]));
      else ponRuta(b, ruta, String(v == null ? '' : v) + TESTIGO);
      return render(a, key) !== render(b, key);
    } catch (e) { return true; }   // ante la duda se dice que si: mejor callar que mentir
  }

  // ── Fechas ya pasadas en los datos que caducan ──
  // E salia por defecto anunciando "Q1 2026" en septiembre de 2026, y nada lo avisaba. No se
  // corrigen solas -que trimestre se vende es cosa del negocio-, pero se dicen.
  const MESES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto',
                 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  function fechasPasadas(datos, hoy) {
    const avisos = [];
    Object.keys(datos || {}).forEach(function (campo) {
      const v = String(datos[campo] || '');
      let m;
      const trimestre = /Q([1-4])\s*(20\d\d)/gi;
      while ((m = trimestre.exec(v))) {
        if (new Date(+m[2], +m[1] * 3, 0) < hoy) avisos.push('«' + m[0] + '» ya terminó');
      }
      const mes = new RegExp('(' + MESES.join('|') + ')\\s+(?:de\\s+)?(20\\d\\d)', 'gi');
      while ((m = mes.exec(v))) {
        if (new Date(+m[2], MESES.indexOf(m[1].toLowerCase()) + 1, 0) < hoy) avisos.push('«' + m[0] + '» ya pasó');
      }
    });
    return avisos;
  }

  return { C, SERVICIOS, GRUPOS, TEMPLATES, IMG_SETS, PERFILES, ASUNTOS, asuntosDe, EFECTOS, efectoDe, pesoDe, rangoPeso, ROLES, CORREOS, cargoDe, correosDe, BANCO, bancoDe, fotosDe, comandoCarrusel, FICHA, CONTENT_VERSION, defaultState, render, renderText, renderWhatsApp, linkFor, cambiaElCorreo, fechasPasadas, pick, aplicaPerfil, aplicaAsunto, normaliza };
});
