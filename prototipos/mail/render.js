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
          respuesta: 'Respuesta en menos de 24 horas hábiles.',
        },
        clientes: { on: false, titulo: 'Marcas que ya están en la calle con nosotros',
          lista: 'Pepsi · Nestlé · Yango · Cashea · EPA · Arturo’s · Ridery · Cinepic · Tío Rico' },
        pasos: { on: true, titulo: 'Próximos pasos',
          texto: 'Una vez seleccionados los espacios, envíanos la información y los documentos para preparar la cotización.' },
        presupuesto: { on: true, titulo: 'Para un presupuesto formal necesitamos',
          items: ['RIF digital de la empresa', 'Fecha de inicio y duración de la campaña', 'Formato o alcance (pantalla, tótem u otro)'] },
        cta: { on: true, texto: 'Enviar información para cotizar', url: 'mailto:equintero@centauroads.com?subject=Solicitud%20de%20cotizaci%C3%B3n' },
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
          url: '',
          img: 'cover_led.jpg',
          alt: 'Portada de la propuesta preparada para el cliente',
          texto: 'Preparamos esta propuesta para {empresa}: los espacios que le convienen, d\u00f3nde se ve y qu\u00e9 pasa cuando la gente pasa por delante.\n\n\u00c1brela con calma y me dices qu\u00e9 te parece. Si hay algo que ajustar, lo ajustamos.',
          corto: 'Te dejo la propuesta que preparamos para {empresa}. \u00c1brela con calma y me dices qu\u00e9 te parece.',
          cta: 'Ver la propuesta',
          // Pie propio, y corto a proposito. El de A-G explica por que recibes el correo
          // -"solicitaste informacion sobre espacios publicitarios"-, que en una entrega
          // sobra: el cuerpo ya dice exactamente de que va y a quien.
          // El primer intento fue el nombre y la ciudad, y visto renderizado repetia la
          // ultima linea de la firma, justo encima. Una invitacion a responder no repite
          // nada y ademas sirve: es lo que se espera despues de una propuesta.
          pie: 'Cualquier duda, resp\u00f3ndeme a este mismo correo.',
          acompanan: 'Lo que la acompa\u00f1a',
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
  // La portada de una entrega puede venir de tres sitios: del servidor que la guarda
  // (/media/entregas/7/og.jpg), de una direccion completa, o del juego de imagenes local
  // cuando es el marcador de posicion. Se distingue por la forma, no por una bandera mas.
  const entregaImg = (st, v) => (/^(https?:)?\/\//.test(v) || String(v).charAt(0) === '/') ? v : imgFor(st, v);
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

  function paleta(oscuro) {
    return oscuro ? {
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
  const esOscuro = st => st.tema === 'oscuro';

  // Cabecera comun: logo a la izquierda, metadato a la derecha.
  function cabeceraAsesor(st, P, meta) {
    const k = paleta(esOscuro(st));
    return '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td valign="middle">' + marca(st, esOscuro(st), 150) + '</td>' +
      '<td valign="middle" align="right" style="font-family:' + FH + ';font-size:10px;font-weight:800;' +
        'letter-spacing:.24em;text-transform:uppercase;color:' + k.apagado + ';">' + esc(meta) + '</td>' +
      '</tr></table>';
  }

  // Epigrafe pequeno en mayusculas. Es el recurso tipografico que ordena sus tres disenos.
  function epigrafe(st, txt, color) {
    const k = paleta(esOscuro(st));
    return '<div style="font-family:' + FH + ';font-size:11px;font-weight:800;letter-spacing:.26em;' +
      'text-transform:uppercase;color:' + (color || k.vivo) + ';padding:0 0 12px 0;">' + esc(txt) + '</div>';
  }

  // Boton solido construido con tabla, no con <button>: es lo unico que Outlook dibuja bien.
  function botonAsesor(st, texto, url) {
    const k = paleta(esOscuro(st));
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
    const k = paleta(esOscuro(st));
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
    const k = paleta(esOscuro(st));
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

  // Rellena lo que falte en un estado guardado antes de que exista un campo nuevo.
  //
  // La alternativa era subir CONTENT_VERSION, que cambia la clave del almacenamiento y
  // hace desaparecer lo que el usuario llevara escrito a mano. Ya paso una vez y se
  // vivio como una perdida de trabajo. Completar en silencio lo que falta cuesta veinte
  // lineas y no le quita nada a nadie.
  function normaliza(st) {
    const base = defaultState();
    if (st.tema === undefined) st.tema = base.tema;
    if (st.asunto3 === undefined) st.asunto3 = base.asunto3;
    if (st.efecto === undefined) st.efecto = base.efecto;
    if (!st.efectosPorServicio) st.efectosPorServicio = {};
    if (!st.banco) st.banco = {};
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
        '<td width="200" valign="top" style="padding:0 18px 0 0;"><a href="' + esc(linkFor(st, s)) + '"><img src="' + esc(st.cardAnim && !usaPortadas(st) ? carruselSrc(st, s) : svcImg(st, s)) + '" width="200" alt="' + esc(svcAlt(st, s)) + '" style="display:block;width:200px;height:auto;border-radius:6px;border:1px solid ' + C.line + ';color:#EEEDF2;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:13px;line-height:18px;"></a></td>' +
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
      const card = (s, w) => '<table role="presentation" width="' + w + '" align="left" cellpadding="0" cellspacing="0" border="0" style="width:' + w + 'px;max-width:100%;margin:0 0 16px 0;"><tr><td style="border:1px solid ' + C.rule + ';border-radius:8px;overflow:hidden;background:' + C.paper + ';">' +
        '<a href="' + esc(linkFor(st, s)) + '"><img src="' + esc(st.cardAnim && !usaPortadas(st) ? carruselSrc(st, s) : svcImg(st, s)) + '" width="' + w + '" alt="' + esc(svcAlt(st, s)) + '" style="display:block;width:100%;height:auto;border-radius:8px 8px 0 0;color:#1F1B24;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:13px;line-height:18px;"></a>' +
        '<div style="padding:12px 14px 14px 14px;">' +
        '<div style="font-family:' + FH + ';font-size:10px;font-weight:700;letter-spacing:.14em;color:' + C.orangeDark + ';text-transform:uppercase;">' + esc(s.eyebrow) + '</div>' +
        '<div style="font-family:' + FH + ';font-size:15px;line-height:20px;font-weight:800;color:' + C.text + ';padding:3px 0 3px 0;">' + esc(s.nombre) + '</div>' +
        '<div style="font-family:' + FB + ';font-size:13px;line-height:19px;color:' + C.muted + ';">' + esc(s.cobertura) + (s.nota ? '<br>' + esc(s.nota) : '') + '</div>' +
        '<div style="padding:8px 0 0 0;"><a href="' + esc(linkFor(st, s)) + '" style="font-family:' + FH + ';font-size:12px;font-weight:700;color:' + C.purple + ';text-decoration:none;">Ver presentación &rarr;</a></div>' +
        '</div></td></tr></table>';
      let grid = '';
      act.forEach((s, i) => {
        const last = i === act.length - 1 && act.length % 2 === 1;
        grid += last ? card(s, 544) : card(s, 264) + (i % 2 === 0 ? '<table role="presentation" width="16" align="left" cellpadding="0" cellspacing="0" border="0"><tr><td style="font-size:0;line-height:0;">&nbsp;</td></tr></table>' : '');
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
      if (e.url) L.push(e.cta + ': ' + e.url, '');
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
    if (e.url) L.push(e.url, '');
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
    const o = esOscuro(st), k = paleta(o), P = [];
    const a = B(st, 'asesor');
    const pad = 'padding-left:32px;padding-right:32px;background:' + k.panel + ';';

    P.push(row(cabeceraAsesor(st, P, a.etiquetaMeta),
      'padding:26px 32px 22px 32px;background:' + k.panel + ';'));

    // Hero. El acento va en "Share of Voice" porque es el termino que la agencia busca.
    P.push(row(
      epigrafe(st, 'Inventario \u00b7 ' + a.periodo) +
      '<div style="font-family:' + FH + ';font-size:40px;line-height:1.02;font-weight:800;letter-spacing:-.035em;color:' + k.texto + ';">' +
        'Tu pr\u00f3ximo <span style="color:' + k.acento + ';">Share of Voice</span>, en una sola tabla.</div>' +
      '<div style="font-family:' + FB + ';font-size:15px;line-height:1.6;color:' + k.apagado + ';padding:16px 0 0 0;">' +
        'Sin brief educativo. Sin rodeos. Los ' + cuantos(activos(st).length) + ' frentes que operamos en Caracas, con m\u00e9tricas comparables, ' +
        'para que tu equipo de medios calcule el mix sin llamar a nadie.</div>',
      pad + 'padding-bottom:26px;'));

    if (on(st, 'saludo')) {
      P.push(row(
        epigrafe(st, 'Para el equipo de ' + (st.destinatario || '[Nombre de la Agencia]'), k.acento) +
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.texto + ';">' +
          'Sabemos c\u00f3mo trabajan: brief, medios, tabla de disponibilidad, decisi\u00f3n. Vamos directo a la \u00faltima parte.</div>' +
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.apagado + ';padding:12px 0 0 0;">' +
          'Este es el inventario que operamos hoy en Caracas, listo para integrarse a tu mix del pr\u00f3ximo trimestre, ' +
          'sin brief educativo de por medio.</div>',
        pad + 'padding-bottom:24px;'));
    }

    // Tira de cifras: tres datos que la agencia reconoce de un vistazo.
    const cifra = function (n, l) {
      return '<td width="33%" valign="top" style="padding:14px 10px;border-top:1px solid ' + k.linea + ';border-bottom:1px solid ' + k.linea + ';">' +
        '<div style="font-family:' + FH + ';font-size:17px;font-weight:800;color:' + k.vivo + ';">' + esc(n) + '</div>' +
        '<div style="font-family:' + FH + ';font-size:10px;font-weight:700;letter-spacing:.16em;text-transform:uppercase;color:' + k.apagado + ';padding:4px 0 0 0;">' + esc(l) + '</div></td>';
    };
    P.push(row('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      cifra('120K impactos / d\u00eda', 'LED') + cifra('250 motos LED', 'Rider') + cifra(activos(st).length + ' frentes', 'activos') +
      '</tr></table>', pad + 'padding-bottom:26px;'));

    // La tabla de inventario: el corazon de su diseno.
    P.push(row(epigrafe(st, '01 \u00b7 Inventario', k.acento) +
      '<div style="font-family:' + FH + ';font-size:24px;font-weight:800;letter-spacing:-.02em;color:' + k.texto + ';">Espacios disponibles</div>' +
      '<div style="font-family:' + FB + ';font-size:13px;color:' + k.apagado + ';padding:5px 0 0 0;">orden por rotaci\u00f3n de audiencia</div>',
      pad + 'padding-bottom:16px;'));

    const INVENTARIO = [
      { n: '01', id: 'led', t: 'Pantalla LED Chacao \u00b7 DOOH', badge: a.slotsLed,
        d: 'Chacao, Av. Francisco de Miranda \u00b7 ' + FICHA.led.medida + ' \u00b7 rotaci\u00f3n por franjas horarias',
        m: [['Impactos', '120.000/d\u00eda'], ['Formato', 'Video / MP4']] },
      { n: '02', id: 'mercedes', t: 'Pantalla LED Las Mercedes \u00b7 DOOH', badge: '',
        d: 'Av. Paseo Enrique Erazo \u00b7 ' + FICHA.mercedes.medida + ' \u00b7 horizontal, 24 horas',
        m: [['Tr\u00e1fico', '95.000 veh\u00edculos/d\u00eda'], ['Formato', 'Video / MP4 \u00b7 30 s']] },
      { n: '03', id: 'vallas', t: 'Vallas \u00b7 OOH nacional', badge: '',
        d: 'Caracas y arterias viales \u00b7 gran formato \u00b7 brand recall de largo plazo',
        m: [['Rotaci\u00f3n', 'Alta vial'], ['Cobertura', 'Nacional']] },
      { n: '04', id: 'rider', t: 'Rider Clon \u00b7 movilidad LED', badge: 'TRACKING',
        d: 'Caracas \u00b7 San Antonio \u00b7 Valencia \u00b7 caja LED ' + FICHA.rider.medida + ' \u00b7 GPS en vivo',
        m: [['Flota', '250 motos'], ['Turno', '8 h / d\u00eda']] },
      { n: '05', id: 'totem', t: 'T\u00f3tem digital \u00b7 indoor', badge: '',
        d: 'C.C. San Ignacio \u00b7 ' + FICHA.totem.medida + ' \u00b7 audiencia cautiva premium',
        m: [['Salidas', '240/d\u00eda'], ['Ambiente', 'Indoor A+']] },
    ];
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
        '&uarr; LED Chacao, el frente con mayor rotaci\u00f3n en Caracas Este.</div>',
        pad + 'padding-bottom:22px;'));
    }

    // Disponibilidad: los datos que caducan salen del estado, no del codigo.
    P.push(row('<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td bgcolor="' + k.panel2 + '" style="background:' + k.panel2 + ';border-left:3px solid ' + k.vivo + ';padding:14px 16px;">' +
      '<div style="font-family:' + FH + ';font-size:10px;font-weight:800;letter-spacing:.16em;text-transform:uppercase;color:' + k.vivo + ';">' +
        '\u25cf Disponibilidad al ' + esc(a.dispoFecha) + '</div>' +
      '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + k.texto + ';padding:6px 0 0 0;">' +
        esc(a.dispoTexto) + ' ' + esc(a.cierreTexto) + '</div>' +
      '</td></tr></table>', pad + 'padding-bottom:24px;'));

    if (on(st, 'cta')) {
      P.push(row(botonAsesor(st, 'Solicitar disponibilidad Q1', B(st, 'cta').url) +
        '<div style="font-family:' + FB + ';font-size:12px;color:' + k.apagado + ';padding:12px 0 0 0;">' + esc(a.pieCta) + '</div>',
        pad + 'padding-bottom:28px;'));
    }

    // Complementos: los servicios sin foto propia en su diseno original.
    const comp = complementos(st, ['led']);
    if (comp) P.push(row(comp, pad + 'padding-bottom:26px;'));

    // Mi firma, por decision del cliente: la suya no lleva el correo de mercadeo.
    if (on(st, 'firma')) {
      P.push(row(firma(st, o),
        'padding:24px 32px 26px 32px;background:' + k.panel + ';border-top:1px solid ' + k.linea + ';'));
    }
    if (on(st, 'pie')) {
      P.push(row('<div style="font-family:' + FB + ';font-size:11px;line-height:16px;color:' + k.apagado + ';">' +
        nl2br(B(st, 'pie').texto) + '</div>', 'padding:14px 32px 0 32px;'));
    }
    return doc(st, k.fondo, P.join(''));
  }

  // -- Formato F - "Guia" (asesor, para cliente nuevo) --------------------------
  // Su idea: quien nunca ha comprado exterior no necesita un catalogo, necesita que le
  // quiten el miedo. Tres fases en orden, cada una con el servicio que le corresponde.
  function plantillaF(st) {
    const o = esOscuro(st), k = paleta(o), P = [];
    const a = B(st, 'asesor');
    const pad = 'padding-left:32px;padding-right:32px;background:' + k.panel + ';';

    P.push(row(cabeceraAsesor(st, P, 'Gu\u00eda para empezar'),
      'padding:26px 32px 22px 32px;background:' + k.panel + ';'));

    P.push(row(
      '<div style="font-family:' + FH + ';font-size:36px;line-height:1.06;font-weight:800;letter-spacing:-.03em;color:' + k.texto + ';">' +
        'Que te conozcan. <span style="color:' + k.acento + ';">Que te recuerden.</span> Que te compren.</div>' +
      '<div style="font-family:' + FB + ';font-size:15px;line-height:1.6;color:' + k.apagado + ';padding:16px 0 0 0;">' +
        'Esa es la secuencia. Tres fases, en ese orden, es c\u00f3mo crecen las marcas que aparecen en las calles. ' +
        'Te la explicamos sin tecnicismos y sin comprometerte a nada.</div>',
      // El aire de arriba lo daba el epigrafe que habia aqui. Al quitarlo, el titular de
      // 36 px se quedaba a 22 px de la cabecera; esto le devuelve el respiro.
      pad + 'padding-top:12px;padding-bottom:26px;'));

    if (on(st, 'saludo')) {
      P.push(row(
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.texto + ';">' +
          'Hola ' + esc(st.destinatario || '[Nombre]') + ',</div>' +
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.apagado + ';padding:10px 0 0 0;">' +
          'Gracias por interesarte en dar el paso a la <b style="color:' + k.texto + ';">publicidad exterior</b>. ' +
          'Sabemos que es una decisi\u00f3n importante: hay muchos formatos, muchos precios y poca informaci\u00f3n clara ' +
          'sobre por d\u00f3nde empezar. Este correo no es una cotizaci\u00f3n: es la gu\u00eda que les contamos a puerta ' +
          'cerrada a las marcas que arrancan con nosotros. L\u00e9ela en 2 minutos y hablamos.</div>',
        pad + 'padding-bottom:26px;'));
    }

    // Las tres fases. Cada una lleva su servicio con mi carrusel animado.
    const FASES = [
      { n: '01', fase: 'Fase de atracci\u00f3n', tit: 'Que te conozcan', id: 'totem',
        txt: 'Empezamos con <b>formatos digitales de alto tr\u00e1fico</b>. El brillo y el movimiento captan miradas ' +
             'nuevas, explican qu\u00e9 haces y qu\u00e9 ofreces. Es la manera m\u00e1s r\u00e1pida de dejar de ser un desconocido.',
        tag: 'Recomendado para empezar', svcTit: 'T\u00f3tem digital \u00b7 San Ignacio',
        svcTxt: '240 salidas/d\u00eda en un centro comercial premium. Audiencia atenta, presupuesto de entrada.' },
      { n: '02', fase: 'Fase de memoria', tit: 'Que te recuerden', id: 'led',
        txt: 'Cuando ya te conocen, tu marca se instala en <b>las calles que tu cliente recorre todos los d\u00edas</b>. ' +
             'Vallas y pantallas LED trabajando juntas: y cuando piensen en lo que vendes, aparecer\u00e1s t\u00fa.',
        tag: 'Combinamos con la fase 1', svcTit: 'Pantalla LED \u00b7 Chacao',
        svcTxt: '120.000 impactos/d\u00eda en la arteria de mayor rotaci\u00f3n de Caracas Este.' },
      { n: '03', fase: 'Fase de decisi\u00f3n', tit: 'Que te compren', id: 'rider',
        txt: 'La calle empuja, el m\u00f3vil cierra. En esta fase activamos promociones t\u00e1cticas y motos con LED que ' +
             'aparecen justo donde y cuando decides. Es la parte donde la campa\u00f1a se convierte en ventas.',
        tag: 'T\u00e1ctico y medible', svcTit: 'Rider Clon \u00b7 movilidad LED',
        svcTxt: '250 motos con GPS. Elegimos las zonas y horas donde vive tu cliente.' },
    ];
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
      '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + k.texto + ';">Sin fricciones t\u00e9cnicas</div>' +
      '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + k.apagado + ';padding:6px 0 0 0;">' +
        'Nosotros nos encargamos de todo lo t\u00e9cnico. T\u00fa apruebas el dise\u00f1o.</div>' +
      '</td></tr></table>', pad + 'padding-bottom:26px;'));

    if (on(st, 'cta')) {
      P.push(row(
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.6;color:' + k.texto + ';padding:0 0 14px 0;">' +
          'Cu\u00e9ntame de tu marca y te preparo una propuesta <b>a la medida de tu presupuesto</b>. Sin compromiso.</div>' +
        botonAsesor(st, 'Cu\u00e9ntame de tu marca', B(st, 'cta').url) +
        '<div style="font-family:' + FB + ';font-size:12px;color:' + k.apagado + ';padding:12px 0 0 0;">' + esc(a.respuesta) + '</div>',
        pad + 'padding-bottom:28px;'));
    }

    const compF = complementos(st, ['totem', 'led', 'rider'], { titulo: false });
    if (compF) P.push(row(compF, pad + 'padding-bottom:26px;'));

    if (on(st, 'firma')) {
      P.push(row(firma(st, o),
        'padding:24px 32px 26px 32px;background:' + k.panel + ';border-top:1px solid ' + k.linea + ';'));
    }
    if (on(st, 'pie')) {
      P.push(row('<div style="font-family:' + FB + ';font-size:11px;line-height:16px;color:' + k.apagado + ';">' +
        nl2br(B(st, 'pie').texto) + '</div>', 'padding:14px 32px 0 32px;'));
    }
    return doc(st, k.fondo, P.join(''));
  }

  // -- Formato G - "Phygital" (asesor) ------------------------------------------
  // Su idea: no explicar el concepto, contarlo como escena. Dos momentos con hora, la
  // calle y el movil, y el puente entre los dos.
  function plantillaG(st) {
    const o = esOscuro(st), k = paleta(o), P = [];
    const pad = 'padding-left:32px;padding-right:32px;background:' + k.panel + ';';

    P.push(row(cabeceraAsesor(st, P, 'PHYGITAL \u00b7 Serie 2026'),
      'padding:26px 32px 22px 32px;background:' + k.panel + ';'));

    P.push(row(
      epigrafe(st, 'Physical + Digital') +
      '<div style="font-family:' + FH + ';font-size:40px;line-height:1.02;font-weight:800;letter-spacing:-.035em;color:' + k.texto + ';">' +
        'La pantalla capta.<br><span style="color:' + k.vivo + ';">El m\u00f3vil cierra.</span></div>',
      pad + 'padding-bottom:24px;'));

    if (on(st, 'saludo')) {
      P.push(row(
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.texto + ';">' +
          'Hola ' + esc(st.destinatario || '[Nombre]') + ',</div>' +
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.65;color:' + k.apagado + ';padding:10px 0 0 0;">' +
          'La gente ya no mira los anuncios. Los graba, los sube y los convierte en contenido, o los ignora. ' +
          'Sabemos que necesitan algo que rompa el molde. Antes de mostrarte precios o formatos, mira c\u00f3mo se ve ' +
          'una campa\u00f1a Phygital en <b style="color:' + k.texto + ';">tres minutos reales</b>. Despu\u00e9s conversamos.</div>',
        pad + 'padding-bottom:26px;'));
    }

    // Escena 01: la calle.
    const led = st.servicios.filter(function (x) { return x.id === 'led' && x.on; })[0];
    P.push(row(
      '<div style="font-family:' + FH + ';font-size:11px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:' + k.vivo + ';padding:0 0 10px 0;">' +
        '\u25cf 09:00 AM \u00b7 Chacao</div>' +
      (led ? fotoServicio(st, led, 536) : '') +
      '<div style="font-family:' + FH + ';font-size:10px;font-weight:800;letter-spacing:.18em;text-transform:uppercase;color:' + k.apagado + ';padding:12px 0 4px 0;">Escena 01</div>' +
      '<div style="font-family:' + FB + ';font-size:15px;line-height:1.6;color:' + k.texto + ';">' +
        'Una persona mira arriba. Ve un QR gigante en la pantalla LED. Curiosidad. Levanta el tel\u00e9fono.</div>' +
      '<div style="font-family:' + FH + ';font-size:11px;font-weight:800;letter-spacing:.2em;color:' + k.vivo + ';padding:14px 0 0 0;">3 SEGUNDOS &darr;</div>',
      pad + 'padding-bottom:26px;'));

    // Escena 02: el movil. Maqueta de la publicacion, construida con tablas.
    P.push(row(
      '<div style="font-family:' + FH + ';font-size:11px;font-weight:800;letter-spacing:.2em;text-transform:uppercase;color:' + k.acento + ';padding:0 0 10px 0;">' +
        '\u25cf 09:03 AM \u00b7 Instagram</div>' +
      '<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"><tr>' +
      '<td bgcolor="' + k.panel2 + '" style="background:' + k.panel2 + ';border:1px solid ' + k.linea + ';border-radius:12px;padding:14px 16px;">' +
        '<div style="font-family:' + FH + ';font-size:13px;font-weight:800;color:' + k.texto + ';">@tu_marca_aqui</div>' +
        '<div style="font-family:' + FB + ';font-size:11px;color:' + k.apagado + ';padding:2px 0 10px 0;">Caracas \u00b7 Venezuela</div>' +
        '<div style="font-family:' + FH + ';font-size:10px;font-weight:800;letter-spacing:.14em;text-transform:uppercase;color:' + k.vivo + ';">Filtro AR activo</div>' +
        '<div style="font-family:' + FB + ';font-size:15px;line-height:1.5;color:' + k.texto + ';padding:8px 0 10px 0;">' +
          'Encontr\u00e9 la valla \u26a1 <span style="color:' + k.acento + ';">#TuMarcaChacao</span></div>' +
        '<div style="font-family:' + FH + ';font-size:12px;font-weight:800;color:' + k.texto + ';">2.847 me gusta</div>' +
        '<div style="font-family:' + FB + ';font-size:13px;line-height:19px;color:' + k.apagado + ';padding:8px 0 0 0;">' +
          'Vieron mi campa\u00f1a. Se pararon. La grabaron. La subieron.</div>' +
      '</td></tr></table>', pad + 'padding-bottom:26px;'));

    P.push(row(
      '<div style="font-family:' + FH + ';font-size:26px;line-height:1.15;font-weight:800;letter-spacing:-.025em;color:' + k.texto + ';">' +
        'La calle tambi\u00e9n es feed.</div>' +
      '<div style="font-family:' + FB + ';font-size:15px;line-height:1.6;color:' + k.apagado + ';padding:10px 0 0 0;">' +
        'Eso es Phygital. Una pantalla que no termina cuando el sem\u00e1foro cambia.</div>',
      pad + 'padding-bottom:26px;'));

    // Como se arma: tres piezas.
    P.push(row(epigrafe(st, 'C\u00f3mo se arma', k.acento) +
      '<div style="font-family:' + FB + ';font-size:14px;color:' + k.apagado + ';padding:0 0 4px 0;">' +
      'Tres piezas. Una campa\u00f1a que se comparte.</div>', pad + 'padding-bottom:12px;'));

    const PIEZAS = [
      { n: '01', t: 'Pantalla LED \u00b7 el gancho f\u00edsico',
        d: 'QR gigante en Chacao o Las Mercedes. Lleva a un filtro AR, un cup\u00f3n o tu e-commerce directo.' },
      { n: '02', t: 'Rider Clon \u00b7 la campa\u00f1a que se mueve',
        d: '250 motos con caja LED se convierten en caza-recompensas: los usuarios las fotograf\u00edan y suben, etiquet\u00e1ndote.' },
      { n: '03', t: 'Capa digital \u00b7 el cierre en el m\u00f3vil',
        d: 'Retargeting a quien escane\u00f3, filtros AR de tu marca, hashtag propio. El impacto f\u00edsico deja huella medible en redes.' },
    ];
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
      '<div style="font-family:' + FH + ';font-size:15px;font-weight:800;color:' + k.texto + ';">Lo que resolvemos</div>' +
      '<div style="font-family:' + FB + ';font-size:14px;line-height:20px;color:' + k.apagado + ';padding:6px 0 0 0;">' +
        'Ya no eliges entre branding masivo o conversi\u00f3n digital. La calle capta. El m\u00f3vil cierra.</div>' +
      '</td></tr></table>', pad + 'padding-bottom:26px;'));

    if (on(st, 'cta')) {
      P.push(row(botonAsesor(st, 'Dise\u00f1emos una campa\u00f1a que se comparta', B(st, 'cta').url) +
        '<div style="font-family:' + FB + ';font-size:12px;color:' + k.apagado + ';padding:12px 0 0 0;">' +
        'Llamada creativa de 15 minutos, sin brief formal.</div>',
        pad + 'padding-bottom:28px;'));
    }

    const compG = complementos(st, ['led']);
    if (compG) P.push(row(compG, pad + 'padding-bottom:26px;'));

    if (on(st, 'firma')) {
      P.push(row(firma(st, o),
        'padding:24px 32px 26px 32px;background:' + k.panel + ';border-top:1px solid ' + k.linea + ';'));
    }
    if (on(st, 'pie')) {
      P.push(row('<div style="font-family:' + FB + ';font-size:11px;line-height:16px;color:' + k.apagado + ';">' +
        nl2br(B(st, 'pie').texto) + '</div>', 'padding:14px 32px 0 32px;'));
    }
    return doc(st, k.fondo, P.join(''));
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
  function plantillaH(st) {
    const o = esOscuro(st), k = paleta(o), P = [];
    const e = B(st, 'entrega');
    const pad = 'padding-left:32px;padding-right:32px;background:' + k.panel + ';';
    // Sin enlace todavia -la plantilla en seco- el boton no debe llevar a ninguna parte.
    const url = e.url || '#';

    P.push(row(cabeceraAsesor(st, P, e.meta),
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

    if (on(st, 'firma')) {
      P.push(row(firma(st, o),
        'padding:24px 32px 26px 32px;background:' + k.panel + ';border-top:1px solid ' + k.linea + ';'));
    }
    if (on(st, 'pie')) {
      P.push(row('<div style="font-family:' + FB + ';font-size:11px;line-height:16px;color:' + k.apagado + ';">' +
        nl2br(e.pie) + '</div>', 'padding:14px 32px 0 32px;'));
    }
    return doc(st, k.fondo, P.join(''));
  }

  const TEMPLATES = {
    A: { nombre: 'Cartelera', desc: 'Oscura, misma identidad que los decks. Para primer envío.', fn: plantillaA },
    B: { nombre: 'Catálogo', desc: 'Clara, tarjetas en dos columnas. Para lectura rápida.', fn: plantillaB },
    C: { nombre: 'Nota', desc: 'Compacta, parece un correo personal. Para responder en hilo.', fn: plantillaC },
    D: { nombre: 'Cartelera móvil', desc: 'Una columna, foto arriba, tipografía grande y un solo botón principal. Pensada para Gmail en el teléfono.', fn: plantillaD },
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
  const render = (st, key) => TEMPLATES[key || pick(st)].fn(aplicaAsunto(aplicaPerfil(normaliza(st))));

  return { C, SERVICIOS, GRUPOS, TEMPLATES, IMG_SETS, PERFILES, ASUNTOS, asuntosDe, EFECTOS, efectoDe, pesoDe, rangoPeso, ROLES, CORREOS, cargoDe, correosDe, BANCO, bancoDe, fotosDe, comandoCarrusel, FICHA, CONTENT_VERSION, defaultState, render, renderText, renderWhatsApp, pick, aplicaPerfil, aplicaAsunto, normaliza };
});
