/* ============================================================================
   SIMPLIF'IA · Recherche universelle (search.js)
   Inclus sur toutes les pages du site. Bouton 🔍 dans la nav + overlay + index.
   Raccourci Cmd+K / Ctrl+K.
   ============================================================================ */
(function () {
  /* === Index complet de tout le site === */
  const INDEX = [
    /* Pages principales */
    { t: 'Accueil', d: 'Page d\'accueil de Simplif\'IA France', i: '🏠', u: 'index.html', cat: 'Page' },
    { t: 'Fonctionnalités', d: 'Toutes les fonctionnalités du produit', i: '⚙️', u: 'fonctionnalites.html', cat: 'Page' },
    { t: 'Tarifs', d: 'Plans Découverte, Premium 9,99€, Pro 49€, Solidaire gratuit', i: '💳', u: 'tarifs.html', cat: 'Page' },
    { t: 'Contact', d: 'Nous contacter par email, téléphone ou formulaire', i: '📧', u: 'contact.html', cat: 'Page' },
    { t: 'À propos', d: 'L\'équipe et la mission Simplif\'IA France', i: '🌟', u: 'apropos.html', cat: 'Page' },
    { t: 'Aide', d: 'Centre d\'aide, FAQ, guides', i: '❓', u: 'aide.html', cat: 'Page' },
    { t: 'Blog', d: 'Articles juridiques et administratifs', i: '📰', u: 'blog.html', cat: 'Page' },
    { t: 'API & Développeurs', d: 'Documentation REST, webhooks, SDK', i: '🔌', u: 'api.html', cat: 'Page' },

    /* Modules produit */
    { t: 'Suite Pro · Factures & Devis', d: 'Factures, devis, URSSAF, TVA, bilan, trésorerie pour auto-entrepreneurs', i: '💼', u: 'factures.html', cat: 'Module', kw: 'facture devis urssaf tva bilan tresorerie auto-entrepreneur autoentrepreneur' },
    { t: 'Pense-Maison Premium', d: 'Mémoire du foyer · abonnements, garanties, prêts, véhicules, entretien', i: '🏠', u: 'pense-maison.html', cat: 'Module', kw: 'maison foyer abonnement garantie pret vehicule entretien' },
    { t: 'Maître Léa · IA juridique', d: 'Conseillère IA sourcée Légifrance', i: '🎙️', u: 'app.html#avatar', cat: 'Module', kw: 'lea ia juridique avocat conseil legifrance' },
    { t: 'Anti-jargon', d: 'Traducteur de courriers admin en français simple', i: '📖', u: 'app.html#trans', cat: 'Module', kw: 'traducteur courrier jargon falc' },
    { t: 'CERFA · 17 formulaires', d: 'Pré-remplissage automatique des CERFAs officiels', i: '📝', u: 'app.html#cerfa', cat: 'Module' },
    { t: 'Coffre-fort chiffré', d: '74 documents AES-256 hébergés en France', i: '🔒', u: 'app.html#coffre', cat: 'Module', kw: 'coffre vault document chiffre aes' },
    { t: 'LRE AR24 · eIDAS', d: 'Lettre Recommandée Électronique 4,68€ pleine valeur juridique', i: '✉️', u: 'app.html#lre', cat: 'Module', kw: 'lre lettre recommandee eidas ar24' },
    { t: 'Clic-par-clic · Auto-pilote', d: 'L\'IA pilote les démarches sur les sites publics', i: '🖱️', u: 'app.html#agent', cat: 'Module', kw: 'agent autopilot pilotage clic' },

    /* Pages ressources */
    { t: 'Centre de guides', d: '12 guides pas-à-pas pour les démarches courantes', i: '📚', u: 'guides.html', cat: 'Ressource' },
    { t: 'Webinaires', d: 'Sessions live de 45 min avec juristes', i: '🎥', u: 'webinaires.html', cat: 'Ressource' },
    { t: 'Témoignages', d: '8 247 avis clients vérifiés', i: '⭐', u: 'temoignages.html', cat: 'Ressource' },
    { t: 'Comparatif', d: 'Comparaison vs Service-Public, Doctolib, autres', i: '🆚', u: 'comparatif.html', cat: 'Ressource' },
    { t: 'Glossaire admin', d: 'Sigles français traduits : RAPO, CERFA, RFR…', i: '📖', u: 'glossaire.html', cat: 'Ressource' },
    { t: 'Sécurité & RGPD', d: 'Chiffrement AES-256, audits, conformités', i: '🔐', u: 'securite.html', cat: 'Ressource' },
    { t: 'Ressources', d: 'Hub central : guides, webinaires, glossaire', i: '📚', u: 'ressources.html', cat: 'Ressource' },

    /* Société */
    { t: 'Carrières · 12 postes', d: 'Postes ouverts CDI/Stage Backend, Frontend, AI, Design…', i: '💼', u: 'carrieres.html', cat: 'Société' },
    { t: 'Presse', d: 'Communiqués, kit média, contacts journalistes', i: '📰', u: 'presse.html', cat: 'Société' },
    { t: 'Partenaires', d: 'data.gouv, FranceConnect, AR24, MAIF, Stripe…', i: '🤝', u: 'partenaires.html', cat: 'Société' },
    { t: 'Programme d\'affiliation', d: 'Recommandez et touchez 30% à vie', i: '💰', u: 'affiliation.html', cat: 'Société' },
    { t: 'Changelog', d: 'Toutes les versions et nouveautés', i: '📝', u: 'changelog.html', cat: 'Société' },
    { t: 'Status page', d: 'Disponibilité temps réel des services', i: '🟢', u: 'status.html', cat: 'Société' },

    /* Compte / espace utilisateur */
    { t: 'Connexion', d: 'Se connecter à votre compte', i: '🔐', u: 'connexion.html', cat: 'Compte' },
    { t: 'Inscription', d: 'Créer un compte gratuit', i: '📝', u: 'inscription.html', cat: 'Compte' },
    { t: 'Mot de passe oublié', d: 'Réinitialiser votre mot de passe', i: '🔑', u: 'mot-de-passe-oublie.html', cat: 'Compte' },
    { t: 'Tableau de bord', d: 'Votre espace utilisateur', i: '📊', u: 'app.html', cat: 'Compte' },
    { t: 'Paramètres', d: 'Profil, sécurité, 2FA, notifications', i: '⚙', u: 'parametres.html', cat: 'Compte' },
    { t: 'Facturation', d: 'Plan, moyen de paiement, factures', i: '💳', u: 'facturation.html', cat: 'Compte' },
    { t: 'Back-office Admin', d: 'Gestion utilisateurs, démarches, CMS', i: '🛠', u: 'admin.html', cat: 'Compte' },

    /* Légal */
    { t: 'CGU', d: 'Conditions Générales d\'Utilisation', i: '📜', u: 'cgu.html', cat: 'Légal' },
    { t: 'Politique de confidentialité', d: 'RGPD, données, droits', i: '🔒', u: 'confidentialite.html', cat: 'Légal' },
    { t: 'Mentions légales', d: 'Éditeur, hébergeur, contact', i: '⚖', u: 'mentions-legales.html', cat: 'Légal' },
    { t: 'Cookies', d: 'Politique de cookies', i: '🍪', u: 'cookies.html', cat: 'Légal' },

    /* CERFAs (top 12) */
    { t: 'CERFA 15473*02 · Remise gracieuse CAF', d: 'Demande de remise gracieuse de dette CAF', i: '📝', u: 'app.html#cerfa', cat: 'CERFA', kw: 'caf indu rapo remise' },
    { t: 'CERFA 14004*04 · Logement social', d: 'Demande de logement social numéro unique', i: '🏠', u: 'app.html#cerfa', cat: 'CERFA', kw: 'logement hlm' },
    { t: 'CERFA 12100*02 · Aide juridictionnelle', d: 'Demande d\'aide juridictionnelle', i: '⚖', u: 'app.html#cerfa', cat: 'CERFA' },
    { t: 'CERFA 14952*01 · CNI majeur', d: 'Carte nationale d\'identité majeur', i: '🆔', u: 'app.html#cerfa', cat: 'CERFA', kw: 'carte identite cni' },
    { t: 'CERFA 12434*05 · MDPH', d: 'Reconnaissance handicap MDPH', i: '🩺', u: 'app.html#cerfa', cat: 'CERFA', kw: 'mdph handicap' },
    { t: 'CERFA 10072*02 · Auto-entrepreneur', d: 'Création auto-entrepreneur INPI', i: '💼', u: 'app.html#cerfa', cat: 'CERFA', kw: 'autoentrepreneur creation' },
    { t: 'CERFA 13750*07 · Passeport', d: 'Demande passeport', i: '🛂', u: 'app.html#cerfa', cat: 'CERFA' },
    { t: 'CERFA 13971*05 · PACS', d: 'Pacte civil de solidarité', i: '💕', u: 'app.html#cerfa', cat: 'CERFA' },
    { t: 'CERFA 14076*02 · Bourse étudiante', d: 'DSE bourse CROUS', i: '🎓', u: 'app.html#cerfa', cat: 'CERFA' },
    { t: 'CERFA 11580*04 · Naturalisation', d: 'Demande de naturalisation française', i: '🇫🇷', u: 'app.html#cerfa', cat: 'CERFA' },
    { t: 'CERFA 14523*02 · Surendettement', d: 'Recours surendettement Banque de France', i: '💸', u: 'app.html#cerfa', cat: 'CERFA' },
    { t: 'CERFA 13651*05 · AEEH', d: 'Allocation enfant handicapé', i: '👶', u: 'app.html#cerfa', cat: 'CERFA' },

    /* Glossaire */
    { t: 'AME · Aide Médicale d\'État', d: 'Couverture santé situations irrégulières', i: '📖', u: 'glossaire.html#ame', cat: 'Glossaire' },
    { t: 'APL · Aide Personnalisée Logement', d: 'Aide CAF pour le loyer', i: '📖', u: 'glossaire.html#apl', cat: 'Glossaire' },
    { t: 'CSS · Complémentaire Santé Solidaire', d: 'Ex CMU-C, mutuelle gratuite ou 1€/jour', i: '📖', u: 'glossaire.html#css', cat: 'Glossaire' },
    { t: 'DALO · Droit au Logement Opposable', d: 'Recours pour demandeurs prioritaires', i: '📖', u: 'glossaire.html#dalo', cat: 'Glossaire' },
    { t: 'RAPO · Recours Administratif', d: 'Recours préalable obligatoire avant contentieux', i: '📖', u: 'glossaire.html#rapo', cat: 'Glossaire' },
    { t: 'RFR · Revenu Fiscal de Référence', d: 'Base de calcul des aides sociales', i: '📖', u: 'glossaire.html#rfr', cat: 'Glossaire' },
    { t: 'eIDAS', d: 'Cadre européen LRE et signature électronique', i: '📖', u: 'glossaire.html#eidas', cat: 'Glossaire' },
    { t: 'FALC · Facile À Lire et Comprendre', d: 'Standard d\'écriture accessible', i: '📖', u: 'glossaire.html#falc', cat: 'Glossaire' },

    /* Actions rapides */
    { t: 'Essayer gratuitement', d: 'Créer un compte sans CB', i: '🚀', u: 'inscription.html', cat: 'Action' },
    { t: 'Voir les tarifs', d: '4 plans dont un gratuit et un solidaire', i: '💳', u: 'tarifs.html', cat: 'Action' },
    { t: 'Devenir affilié', d: 'Programme 30% à vie', i: '💰', u: 'affiliation.html', cat: 'Action' },
    { t: 'Demander une démo', d: 'Démo Pro 30 minutes', i: '📅', u: 'contact.html?demande=demo', cat: 'Action' },
    { t: 'Plan solidaire gratuit', d: 'Pour bénéficiaires minima sociaux', i: '🤝', u: 'tarifs.html#solidaire', cat: 'Action' }
  ];

  /* === Styles === */
  const styles = `
    .sia-search-trigger {
      display: inline-flex; align-items: center; gap: 8px;
      background: rgba(255,255,255,0.85); backdrop-filter: blur(8px);
      border: 1px solid #e0e0e8; border-radius: 999px;
      padding: 7px 14px 7px 12px; cursor: pointer;
      color: #555; font-size: 13px; font-family: inherit;
      transition: all 0.15s; margin-right: 8px;
    }
    .sia-search-trigger:hover { background: white; border-color: #000091; color: #000091; transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,145,0.12); }
    .sia-search-trigger kbd { background: #f0f0fa; padding: 2px 6px; border-radius: 4px; font-size: 11px; font-family: 'SF Mono', monospace; color: #888; border: 1px solid #e4e4ee; }

    .sia-search-fab {
      position: fixed !important;
      bottom: 24px !important;
      right: 24px !important;
      left: auto !important;
      width: 56px; height: 56px; border-radius: 50%;
      background: linear-gradient(135deg, #000091, #6A6AF4);
      color: white; font-size: 22px; border: none; cursor: pointer;
      box-shadow: 0 8px 24px rgba(0,0,145,0.3); z-index: 8500;
      transition: transform 0.15s; display: flex; align-items: center; justify-content: center;
    }
    .sia-search-fab:hover { transform: scale(1.08); }
    @media (max-width: 720px) { .sia-search-fab { display: none; } }

    .sia-search-overlay {
      position: fixed; inset: 0; background: rgba(10,10,35,0.55);
      backdrop-filter: blur(8px);
      display: none; align-items: flex-start; justify-content: center;
      z-index: 99000; padding-top: 80px;
    }
    .sia-search-overlay.show { display: flex; }
    .sia-search-box {
      width: min(640px, 92vw); max-height: 70vh;
      background: white; border-radius: 18px; overflow: hidden;
      box-shadow: 0 24px 80px rgba(0,0,0,0.4);
      display: flex; flex-direction: column;
    }
    .sia-search-input-wrap {
      padding: 16px 18px; border-bottom: 1px solid #eee;
      display: flex; align-items: center; gap: 10px;
    }
    .sia-search-input-wrap input {
      flex: 1; border: none; outline: none;
      font-size: 17px; font-family: inherit;
      background: transparent;
    }
    .sia-search-input-wrap kbd {
      background: #f0f0fa; padding: 3px 8px; border-radius: 5px;
      font-size: 11px; color: #888; border: 1px solid #e4e4ee;
    }
    .sia-search-results {
      overflow-y: auto; padding: 8px 0;
    }
    .sia-search-section {
      padding: 12px 18px 6px; font-size: 11px;
      text-transform: uppercase; letter-spacing: 1px;
      font-weight: 700; color: #888;
    }
    .sia-search-item {
      display: flex; align-items: center; gap: 12px;
      padding: 10px 18px; cursor: pointer;
      transition: background 0.1s; border: none;
      width: 100%; text-align: left; background: none;
      font-family: inherit;
    }
    .sia-search-item:hover, .sia-search-item.selected { background: #f0f0fa; }
    .sia-search-item-icon { font-size: 22px; flex-shrink: 0; }
    .sia-search-item-body { flex: 1; min-width: 0; }
    .sia-search-item-title { font-size: 14px; font-weight: 600; color: #0a0a23; }
    .sia-search-item-desc { font-size: 12px; color: #888; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    .sia-search-item-cat {
      background: #E3E3FD; color: #000091;
      padding: 3px 8px; border-radius: 5px;
      font-size: 10px; font-weight: 700;
      flex-shrink: 0;
    }
    .sia-search-empty {
      padding: 32px 18px; text-align: center; color: #888; font-size: 14px;
    }
    .sia-search-footer {
      padding: 10px 18px; border-top: 1px solid #eee;
      display: flex; justify-content: space-between; align-items: center;
      font-size: 11px; color: #888;
    }
    .sia-search-footer kbd { background: #f0f0fa; padding: 2px 6px; border-radius: 4px; font-size: 10px; }
  `;
  const styleEl = document.createElement('style');
  styleEl.textContent = styles;
  document.head.appendChild(styleEl);

  /* === Overlay === */
  const overlay = document.createElement('div');
  overlay.className = 'sia-search-overlay';
  overlay.innerHTML = `
    <div class="sia-search-box" role="dialog" aria-label="Recherche universelle">
      <div class="sia-search-input-wrap">
        <span style="font-size:20px;">🔍</span>
        <input type="search" id="siaSearchInput" placeholder="Rechercher sur Simplif'IA · pages, modules, CERFAs, glossaire…" autocomplete="off">
        <kbd>ESC</kbd>
      </div>
      <div class="sia-search-results" id="siaSearchResults"></div>
      <div class="sia-search-footer">
        <span><kbd>↑</kbd><kbd>↓</kbd> naviguer · <kbd>↵</kbd> ouvrir</span>
        <span>${INDEX.length} entrées indexées</span>
      </div>
    </div>
  `;
  document.body.appendChild(overlay);

  const input = overlay.querySelector('#siaSearchInput');
  const results = overlay.querySelector('#siaSearchResults');

  let currentMatches = [];
  let selected = 0;

  function open() {
    overlay.classList.add('show');
    input.value = '';
    selected = 0;
    render('');
    setTimeout(() => input.focus(), 50);
  }
  function close() { overlay.classList.remove('show'); }

  function render(query) {
    const q = (query || '').toLowerCase().trim();
    if (!q) {
      /* Show recents + popular */
      const recents = JSON.parse(localStorage.getItem('sia.search.recent') || '[]').slice(0, 5);
      const popular = INDEX.filter(i => ['Module', 'Action', 'CERFA'].includes(i.cat)).slice(0, 8);
      let html = '';
      if (recents.length) {
        html += '<div class="sia-search-section">⏱ Récents</div>';
        recents.forEach((r, i) => html += renderItem(r, i));
      }
      html += '<div class="sia-search-section">⭐ Suggéré</div>';
      popular.forEach((p, i) => html += renderItem(p, recents.length + i));
      results.innerHTML = html;
      currentMatches = [...recents, ...popular];
      bind();
      return;
    }

    const matches = INDEX.filter(item => {
      const text = (item.t + ' ' + item.d + ' ' + (item.kw || '') + ' ' + item.cat).toLowerCase();
      return q.split(/\s+/).every(w => text.includes(w));
    }).slice(0, 50);

    currentMatches = matches;
    if (!matches.length) {
      results.innerHTML = '<div class="sia-search-empty">🔍 Aucun résultat pour <strong>"' + query + '"</strong><br><small>Essayez avec des mots-clés plus larges</small></div>';
      return;
    }

    /* Group by cat */
    const groups = {};
    matches.forEach((m, i) => {
      groups[m.cat] = groups[m.cat] || [];
      groups[m.cat].push({ item: m, idx: i });
    });

    let html = '';
    Object.keys(groups).forEach(cat => {
      html += '<div class="sia-search-section">' + cat + ' · ' + groups[cat].length + '</div>';
      groups[cat].forEach(g => html += renderItem(g.item, g.idx));
    });
    results.innerHTML = html;
    bind();
  }

  function renderItem(item, idx) {
    const sel = idx === selected ? 'selected' : '';
    return '<button class="sia-search-item ' + sel + '" data-idx="' + idx + '"><div class="sia-search-item-icon">' + item.i + '</div><div class="sia-search-item-body"><div class="sia-search-item-title">' + escapeHtml(item.t) + '</div><div class="sia-search-item-desc">' + escapeHtml(item.d) + '</div></div><span class="sia-search-item-cat">' + item.cat + '</span></button>';
  }

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
  }

  function bind() {
    overlay.querySelectorAll('.sia-search-item').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.dataset.idx);
        execute(currentMatches[idx]);
      });
      el.addEventListener('mouseenter', () => {
        const idx = parseInt(el.dataset.idx);
        selected = idx;
        overlay.querySelectorAll('.sia-search-item').forEach(x => x.classList.remove('selected'));
        el.classList.add('selected');
      });
    });
  }

  function execute(item) {
    if (!item) return;
    /* Save recent */
    const recents = JSON.parse(localStorage.getItem('sia.search.recent') || '[]');
    const filtered = recents.filter(r => r.t !== item.t).slice(0, 9);
    localStorage.setItem('sia.search.recent', JSON.stringify([item, ...filtered]));

    close();
    /* Navigate */
    if (item.u) {
      const cur = window.location.pathname.split('/').pop() || 'index.html';
      const [page, anchor] = item.u.split('#');
      if ((page === '' || page === cur) && anchor) {
        /* Same page → click tab or scroll to anchor */
        const tab = document.querySelector('[data-tab="' + anchor + '"]');
        if (tab) tab.click();
        else {
          const target = document.getElementById(anchor);
          if (target) target.scrollIntoView({ behavior: 'smooth' });
        }
      } else {
        window.location.href = item.u;
      }
    }
  }

  /* === Keyboard nav === */
  input.addEventListener('input', e => { selected = 0; render(e.target.value); });
  input.addEventListener('keydown', e => {
    if (e.key === 'Escape') { close(); return; }
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      selected = Math.min(selected + 1, currentMatches.length - 1);
      render(input.value);
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      selected = Math.max(selected - 1, 0);
      render(input.value);
    } else if (e.key === 'Enter') {
      e.preventDefault();
      execute(currentMatches[selected]);
    }
  });

  overlay.addEventListener('click', e => { if (e.target === overlay) close(); });

  /* === Cmd+K / Ctrl+K shortcut === */
  document.addEventListener('keydown', e => {
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
      e.preventDefault();
      open();
    }
  });

  /* === Inject trigger button into nav === */
  function injectTrigger() {
    /* Try to insert into existing nav */
    const ctaBox = document.querySelector('.site-nav-cta, .site-nav nav, .site-nav');
    if (!ctaBox || ctaBox.querySelector('.sia-search-trigger')) return;
    const btn = document.createElement('button');
    btn.className = 'sia-search-trigger';
    btn.innerHTML = '<span style="font-size:14px;">🔍</span><span>Rechercher</span><kbd>⌘K</kbd>';
    btn.addEventListener('click', open);
    /* Insert before the CTA buttons if possible */
    if (ctaBox.classList.contains('site-nav-cta')) {
      ctaBox.insertBefore(btn, ctaBox.firstChild);
    } else {
      ctaBox.appendChild(btn);
    }
  }

  /* === Floating FAB on every page (visible in scroll) === */
  function injectFAB() {
    if (document.getElementById('siaSearchFab')) return;
    const fab = document.createElement('button');
    fab.id = 'siaSearchFab';
    fab.className = 'sia-search-fab';
    // Force position EN BAS À DROITE via inline style (priorité max)
    fab.style.cssText = 'position:fixed!important;bottom:24px!important;right:24px!important;left:auto!important;z-index:8500;';
    fab.innerHTML = '🔍';
    fab.title = 'Rechercher (Cmd+K)';
    fab.addEventListener('click', open);
    document.body.appendChild(fab);

    // Watchdog · si une autre lib le repositionne à gauche, on le remet à droite toutes les 2s
    setInterval(() => {
      if (!document.body.contains(fab)) return;
      const cs = getComputedStyle(fab);
      if (cs.left !== 'auto' && parseFloat(cs.left) < 100) {
        fab.style.setProperty('left', 'auto', 'important');
        fab.style.setProperty('right', '24px', 'important');
      }
    }, 2000);
  }

  /* Init */
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => { injectTrigger(); injectFAB(); });
  } else {
    injectTrigger();
    injectFAB();
  }

  /* Expose for use elsewhere */
  window.openSiaSearch = open;
  window.closeSiaSearch = close;

  // console.log('[Simplif\'IA] Search.js loaded · ' + INDEX.length + ' entrées indexées · Cmd+K');
})();
