/* ============================================================================
   Simplif'IA · Pack 23 · Petits détails délicieux
   Subtil, jamais voyant, à découvrir progressivement.
   Chargé sur TOUTES les pages (user + admin).
   ============================================================================ */
(function () {

  /* ========================================================================
     1) MESSAGE CONSOLE POUR DEVS (recrutement masqué · désactivé)
     ====================================================================== */
  // Message console désactivé (était commenté incorrectement, causait une SyntaxError)

  /* ========================================================================
     2) GREETING DYNAMIQUE selon l'heure
     ====================================================================== */
  function updateDynamicGreeting() {
    const h = new Date().getHours();
    let g, e;
    if (h >= 5 && h < 12)       { g = 'Bonjour';        e = '☕'; }
    else if (h >= 12 && h < 14) { g = 'Bon appétit';    e = '🥐'; }
    else if (h >= 14 && h < 18) { g = 'Bon après-midi'; e = '🌤'; }
    else if (h >= 18 && h < 22) { g = 'Bonsoir';        e = '🌙'; }
    else                          { g = 'Bonne nuit';   e = '🌜'; }

    /* On remplace dans la greeting-card si elle existe */
    const card = document.querySelector('.greeting-card .greeting-title');
    if (card && /Bonsoir|Bonjour|Bon ([aA])près-midi|Bonne nuit|Bon appétit/.test(card.textContent)) {
      card.innerHTML = card.innerHTML.replace(/Bonsoir|Bonjour|Bon ([aA])près-midi|Bonne nuit|Bon appétit/, g);
    }
  }
  updateDynamicGreeting();
  /* Refresh chaque minute (au cas où on passe minuit) */
  setInterval(updateDynamicGreeting, 60000);

  /* ========================================================================
     3) SAINT DU JOUR + JOUR ANNIVERSAIRE FAMEUX
     ====================================================================== */
  const SAINTS = {
    '01-01': 'Jour de l\'An', '01-06': 'Sainte Mélaine',
    '02-14': 'Saint Valentin', '02-29': 'Saint Auguste',
    '03-08': 'Journée internationale des droits des femmes',
    '04-01': 'Poisson d\'avril 🐟', '04-23': 'Saint Georges',
    '05-01': 'Fête du Travail', '05-08': 'Victoire 1945',
    '05-12': 'Saint Achille', '05-15': 'Saint Honoré (boulanger)',
    '06-21': 'Fête de la Musique 🎶', '07-14': 'Fête nationale 🇫🇷',
    '08-15': 'Assomption', '10-31': 'Halloween 🎃',
    '11-01': 'Toussaint', '11-11': 'Armistice 1918',
    '12-24': 'Saint Adèle · réveillon', '12-25': 'Noël 🎄', '12-31': 'Saint Sylvestre'
  };

  function saintDuJour() {
    const d = new Date();
    const key = String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    return SAINTS[key] || null;
  }

  /* ========================================================================
     4) CITATIONS ADMINISTRATIVES (tournantes, footer)
     ====================================================================== */
  const QUOTES = [
    'Personne ne se baigne deux fois dans le même CERFA. — Héraclite, peut-être',
    'L\'administration est l\'art de rendre simple ce qui est compliqué… ou l\'inverse.',
    'Un papier perdu, c\'est trois mois de procédure.',
    'Le silence de l\'administration vaut rejet. Sauf quand il vaut acceptation.',
    'Donnez-moi un timbre, et je vous remuerai le monde.',
    'Les délais administratifs sont comme les promesses : faits pour être prolongés.',
    'Le mieux est l\'ennemi du formulaire 14323*02.',
    'Patience et longueur de temps font plus que force ni rage. — Et la CAF.',
    'Article L142-2 du Code de la Sécu Sociale : votre meilleur ami pour un RAPO.',
    'En matière de paperasse, l\'optimisme est un acte de résistance.'
  ];

  function injectFooterQuote() {
    const footer = document.querySelector('.site-footer-bottom');
    if (!footer || footer.querySelector('.sia-quote')) return;
    const quote = QUOTES[Math.floor(Math.random() * QUOTES.length)];
    const saint = saintDuJour();
    const span = document.createElement('div');
    span.className = 'sia-quote';
    span.style.cssText = 'flex-basis:100%;font-size:12px;color:var(--text-mute,#A0A0AC);font-style:italic;text-align:center;margin-top:14px;padding-top:14px;border-top:1px solid var(--border,#EBEBF1);';
    span.innerHTML = (saint ? `<span style="color:var(--bleu,#000091);font-weight:600;font-style:normal;">${saint}</span> · ` : '') + '« ' + quote + ' »';
    footer.appendChild(span);
  }
  setTimeout(injectFooterQuote, 300);

  /* ========================================================================
     5) LOGO CLICK COUNTER · 7 clics = surprise
     ====================================================================== */
  let logoClicks = 0;
  let logoTimer = null;
  document.addEventListener('click', e => {
    const logo = e.target.closest('.site-nav-mark, .side-mark');
    if (!logo) return;
    logoClicks++;
    clearTimeout(logoTimer);
    logoTimer = setTimeout(() => { logoClicks = 0; }, 3000);

    if (logoClicks === 3) {
      logo.style.transition = 'transform 0.3s';
      logo.style.transform = 'rotate(360deg)';
      setTimeout(() => logo.style.transform = '', 400);
    }
    if (logoClicks === 7) {
      logoClicks = 0;
      triggerEasterEgg('🇫🇷 Merci d\'aimer le drapeau autant que nous.');
    }
  });

  /* ========================================================================
     6) KONAMI CODE → confetti tricolore
     ====================================================================== */
  const KONAMI = ['ArrowUp','ArrowUp','ArrowDown','ArrowDown','ArrowLeft','ArrowRight','ArrowLeft','ArrowRight','b','a'];
  let konamiPos = 0;
  document.addEventListener('keydown', e => {
    if (e.key === KONAMI[konamiPos]) {
      konamiPos++;
      if (konamiPos === KONAMI.length) {
        konamiPos = 0;
        triggerConfetti();
        triggerEasterEgg('🎉 Code Konami activé · vous êtes officiellement un power user');
      }
    } else {
      konamiPos = e.key === KONAMI[0] ? 1 : 0;
    }
  });

  function triggerConfetti() {
    const colors = ['#000091', '#FFFFFF', '#E1000F'];
    const c = document.createElement('div');
    c.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:99999;overflow:hidden;';
    for (let i = 0; i < 80; i++) {
      const piece = document.createElement('div');
      const color = colors[Math.floor(Math.random() * colors.length)];
      const left = Math.random() * 100;
      const delay = Math.random() * 0.8;
      const duration = 2 + Math.random() * 2;
      piece.style.cssText = `position:absolute;width:8px;height:14px;background:${color};left:${left}%;top:-20px;border-radius:1px;animation:siaConfettiFall ${duration}s ease-in ${delay}s forwards;transform:rotate(${Math.random()*360}deg);`;
      c.appendChild(piece);
    }
    document.body.appendChild(c);
    setTimeout(() => c.remove(), 5000);
  }

  /* ========================================================================
     7) EASTER EGG · message toast subtil
     ====================================================================== */
  function triggerEasterEgg(/* msg */) {
    /* Popups DÉSACTIVÉES définitivement · demande utilisateur · no-op global */
    return;
  }

  /* ========================================================================
     8) PERFORMANCE BADGE · "page chargée en X ms" sur F12
     ====================================================================== */
  if (window.performance && performance.timing) {
    window.addEventListener('load', () => {
      setTimeout(() => {
        const t = performance.timing;
        const ms = t.loadEventEnd - t.navigationStart;
        if (ms > 0) {
          // console.log(`%c⚡ Page chargée en ${ms} ms`, 'color:#18753C;font-weight:bold;');
        }
      }, 100);
    });
  }

  /* ========================================================================
     9) SAVIEZ-VOUS · tooltips sur sigles admin (RAPO, CERFA, RFR, LRE…)
     ====================================================================== */
  const SIGLES = {
    'RAPO': 'Recours Administratif Préalable Obligatoire · gratuit, à faire avant tout contentieux',
    'CERFA': 'Centre d\'Enregistrement et de Révision des Formulaires Administratifs',
    'RFR': 'Revenu Fiscal de Référence · base de calcul des aides sociales',
    'LRE': 'Lettre Recommandée Électronique · valeur eIDAS qualifiée comme un recommandé papier',
    'APL': 'Aide Personnalisée au Logement · versée par la CAF aux locataires',
    'CSS': 'Complémentaire Santé Solidaire · ex CMU-C, gratuite ou 1€/jour',
    'DALO': 'Droit Au Logement Opposable · recours pour les demandeurs prioritaires',
    'URSSAF': 'Union de Recouvrement des cotisations · gère la sécu',
    'ANTS': 'Agence Nationale des Titres Sécurisés · CNI, passeport, permis, carte grise',
    'FALC': 'Facile À Lire et Comprendre · standard accessibilité cognitive',
    'eIDAS': 'Règlement européen · cadre légal LRE et signature électronique',
    'RGPD': 'Règlement Général sur la Protection des Données · UE 2016/679',
    'CAF': 'Caisse d\'Allocations Familiales',
    'AME': 'Aide Médicale d\'État',
    'BOFiP': 'Bulletin Officiel des Finances Publiques · doctrine fiscale'
  };

  function injectTooltips() {
    if (window.__siaTooltipsInjected) return;
    window.__siaTooltipsInjected = true;

    /* Style tooltip */
    const style = document.createElement('style');
    style.textContent = `
      .sia-sigle {
        border-bottom: 1px dotted var(--bleu, #000091);
        cursor: help;
        position: relative;
      }
      .sia-sigle:hover::after {
        content: attr(data-def);
        position: absolute;
        bottom: 100%;
        left: 50%;
        transform: translateX(-50%) translateY(-4px);
        background: #18181B;
        color: white;
        padding: 8px 12px;
        border-radius: 8px;
        font-size: 12px;
        font-weight: 400;
        font-style: normal;
        white-space: normal;
        max-width: 280px;
        line-height: 1.4;
        z-index: 99999;
        box-shadow: 0 8px 24px rgba(0,0,0,0.25);
        pointer-events: none;
      }
    `;
    document.head.appendChild(style);

    /* Walker dans les nœuds texte */
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT, {
      acceptNode: n => {
        const p = n.parentElement;
        if (!p) return NodeFilter.FILTER_REJECT;
        if (['SCRIPT','STYLE','INPUT','TEXTAREA','SELECT','BUTTON','A','CODE','PRE'].includes(p.tagName)) return NodeFilter.FILTER_REJECT;
        if (p.closest('.sia-sigle, .modal-bg, .ad-modal-bg, .upg-modal-bg')) return NodeFilter.FILTER_REJECT;
        if (n.textContent.length < 3) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    const nodes = [];
    let n;
    while ((n = walker.nextNode())) nodes.push(n);

    const pattern = new RegExp('\\b(' + Object.keys(SIGLES).join('|') + ')\\b', 'g');
    nodes.forEach(node => {
      const txt = node.textContent;
      if (!pattern.test(txt)) return;
      pattern.lastIndex = 0;
      const frag = document.createDocumentFragment();
      let last = 0, m;
      while ((m = pattern.exec(txt))) {
        if (m.index > last) frag.appendChild(document.createTextNode(txt.slice(last, m.index)));
        const span = document.createElement('span');
        span.className = 'sia-sigle';
        span.dataset.def = SIGLES[m[0]];
        span.textContent = m[0];
        frag.appendChild(span);
        last = m.index + m[0].length;
      }
      if (last < txt.length) frag.appendChild(document.createTextNode(txt.slice(last)));
      node.parentNode.replaceChild(frag, node);
    });
  }
  setTimeout(injectTooltips, 800);

  /* ========================================================================
     10) ANIMATIONS CSS GLOBALES (insérées une fois)
     ====================================================================== */
  if (!document.getElementById('siaPolishAnimations')) {
    const s = document.createElement('style');
    s.id = 'siaPolishAnimations';
    s.textContent = `
      @keyframes siaConfettiFall {
        0% { transform: translateY(0) rotate(0deg); opacity: 1; }
        100% { transform: translateY(110vh) rotate(720deg); opacity: 0.6; }
      }
      @keyframes siaPop {
        0% { opacity: 0; transform: translateX(-50%) translateY(20px) scale(0.9); }
        100% { opacity: 1; transform: translateX(-50%) translateY(0) scale(1); }
      }
      @keyframes siaSparkle {
        0%, 100% { opacity: 0; transform: scale(0.5) rotate(0deg); }
        50% { opacity: 1; transform: scale(1) rotate(180deg); }
      }
      .site-nav-mark { transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
      .site-nav-mark:hover { transform: rotate(-3deg) scale(1.06); }

      /* Bouton primaire : micro-bounce au mousedown */
      .btn-primary:active, .btn-marianne:active { transform: scale(0.97); }

      /* Lien hover sparkle subtle */
      a:not(.btn):not(.site-nav-brand) { position: relative; }

      /* Selection text aux couleurs Marianne */
      ::selection { background: #000091; color: white; }
    `;
    document.head.appendChild(s);
  }

  /* ========================================================================
     11) PROMPT URL · taper "simplif" dans la barre d'URL → easter egg
        (Le ?simplif=1 active une animation)
     ====================================================================== */
  if (window.location.search.includes('simplif=1') || window.location.hash.includes('simplif')) {
    setTimeout(() => {
      triggerConfetti();
      triggerEasterEgg('🎩 Vous avez trouvé l\'easter egg URL. Bravo.');
    }, 1500);
  }

  /* ========================================================================
     12) ASTUCES TOURNANTES (1 toast / 5 min, max 2 par session)
     ====================================================================== */
  const TIPS = [
    { icon: '⌨', msg: 'Astuce · <kbd>Cmd+K</kbd> ouvre la recherche universelle' },
    { icon: '🎨', msg: 'Astuce · le bouton 🎨 dans la nav change le thème du site' },
    { icon: '👩‍⚖️', msg: 'Astuce · Maître Léa cite ses sources (Légifrance, BOFiP)' },
    { icon: '🔒', msg: 'Astuce · vos données sont chiffrées AES-256, OVH France' },
    { icon: '✉️', msg: 'Astuce · les LRE eIDAS ont la même valeur qu\'un recommandé papier' },
    { icon: '⭐', msg: 'Astuce · les achievements se débloquent en utilisant le produit' }
  ];

  let tipsShown = parseInt(sessionStorage.getItem('sia.tips') || '0', 10);
  function maybeShowTip() {
    if (tipsShown >= 2) return;
    if (!window.toast || document.hidden) return;
    const tip = TIPS[Math.floor(Math.random() * TIPS.length)];
    window.toast({ type: 'info', icon: tip.icon, msg: tip.msg, duration: 6000 });
    tipsShown++;
    sessionStorage.setItem('sia.tips', String(tipsShown));
  }
  /* Astuces automatiques DÉSACTIVÉES (l'utilisateur ne veut aucun popup d'arrivée) */
  // setTimeout(maybeShowTip, 30000);
  // setTimeout(maybeShowTip, 5 * 60 * 1000);

  /* ========================================================================
     13) "FRANCE EN DIRECT" · petite donnée fun en bas de footer
     ====================================================================== */
  const FRANCE_FACTS = [
    'En France, 67 millions d\'habitants utilisent 250 000 CERFAs différents par an.',
    'L\'administration française compte 5,5 millions d\'agents publics.',
    'Le mot "paperasse" a été créé en 1727.',
    'Service-Public.fr existe depuis 2000 · 47 millions de visiteurs uniques par mois.',
    'La CAF traite 6,5 millions de dossiers par mois.',
    'Le CERFA le plus rempli en France : le 14000*04 (RIB) avec 12 millions/an.',
    'La France a plus de 6 000 communes de moins de 200 habitants.',
    'Le 3939 (Allô Service Public) reçoit 2 millions d\'appels/an.'
  ];
  function injectFranceFact() {
    if (Math.random() > 0.3) return; /* 30% de chance seulement */
    const footer = document.querySelector('.site-footer');
    if (!footer || footer.querySelector('.sia-france-fact')) return;
    const fact = FRANCE_FACTS[Math.floor(Math.random() * FRANCE_FACTS.length)];
    const div = document.createElement('div');
    div.className = 'sia-france-fact';
    div.style.cssText = 'text-align:center;font-size:11px;color:var(--text-mute,#A0A0AC);padding:10px;background:transparent;font-style:italic;';
    div.innerHTML = '🇫🇷 ' + fact;
    footer.appendChild(div);
  }
  setTimeout(injectFranceFact, 500);

  /* ========================================================================
     14) PAGE TITLE · indicateur visite (perte de focus)
     ====================================================================== */
  const originalTitle = document.title;
  let titleInterval = null;
  document.addEventListener('visibilitychange', () => {
    if (document.hidden && !titleInterval) {
      let n = 0;
      const messages = ['👋 Revenez !', '😢 Vous nous manquez', '☕ On vous attend', originalTitle];
      titleInterval = setInterval(() => {
        document.title = messages[n % messages.length];
        n++;
      }, 2000);
    } else if (!document.hidden && titleInterval) {
      clearInterval(titleInterval);
      titleInterval = null;
      document.title = originalTitle;
    }
  });

  /* ========================================================================
     15) RIGHT-CLICK custom sur le logo → easter egg copyright
     ====================================================================== */
  document.addEventListener('contextmenu', e => {
    const logo = e.target.closest('.site-nav-mark');
    if (!logo) return;
    e.preventDefault();
    triggerEasterEgg('© 2026 · Avec ❤️ depuis Paris 11e · Liberté, Égalité, Simplicité');
  });

  // console.log('[Simplif\'IA] Pack 23 loaded · petits détails · 7 easter eggs · 16 sigles tooltips · greeting dynamique');
})();
