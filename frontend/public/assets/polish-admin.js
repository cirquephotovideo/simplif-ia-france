/* ============================================================================
   Simplif'IA · Pack 23 ADMIN · Petits détails côté pilote
   Chargé uniquement sur admin.html
   ============================================================================ */
(function () {
  if (!document.querySelector('aside.sidebar')) return;

  /* ========================================================================
     1) COMPTEUR CAFÉ · pour celui qui pilote la boîte
     ====================================================================== */
  const COFFEE_KEY = 'sia.admin.coffees';
  let coffees = parseInt(localStorage.getItem(COFFEE_KEY) || '0', 10);

  function injectCoffeeCounter() {
    const sidebar = document.querySelector('aside.sidebar');
    if (!sidebar || sidebar.querySelector('.sia-coffee')) return;
    const div = document.createElement('div');
    div.className = 'sia-coffee';
    div.style.cssText = 'margin-top:auto;padding:14px 16px;border-top:1px solid rgba(255,255,255,0.06);font-size:11px;color:rgba(255,255,255,0.4);cursor:pointer;transition:color .15s;user-select:none;';
    div.innerHTML = `☕ <span class="sia-coffee-n">${coffees}</span> café${coffees > 1 ? 's' : ''} aujourd\'hui`;
    div.title = 'Cliquer pour ajouter un café';
    div.addEventListener('click', () => {
      coffees++;
      localStorage.setItem(COFFEE_KEY, String(coffees));
      const n = div.querySelector('.sia-coffee-n');
      if (n) n.textContent = coffees;
      div.innerHTML = `☕ <span class="sia-coffee-n">${coffees}</span> café${coffees > 1 ? 's' : ''} aujourd\'hui`;
      if (coffees === 5) {
        window.adToast?.('☕ 5 cafés · Sophie suggère un verre d\'eau', true);
      } else if (coffees === 10) {
        window.adToast?.('☕☕☕ 10 cafés · Marie Curie a fait ses meilleures découvertes la nuit aussi', true);
      } else if (coffees >= 20) {
        window.adToast?.('💀 20 cafés. On commence à s\'inquiéter.', true);
        coffees = 0;
        localStorage.setItem(COFFEE_KEY, '0');
      } else {
        div.style.color = '#FFD83D';
        setTimeout(() => div.style.color = 'rgba(255,255,255,0.4)', 600);
      }
    });
    sidebar.appendChild(div);
  }

  /* ========================================================================
     2) "BUILT WITH ❤️ IN PARIS" badge subtil en bas de chaque panel
     ====================================================================== */
  function injectBuiltWithLove() {
    const main = document.querySelector('main') || document.body;
    if (main.querySelector('.sia-built-with-love')) return;
    const div = document.createElement('div');
    div.className = 'sia-built-with-love';
    div.style.cssText = 'position:fixed;bottom:8px;right:14px;font-size:10px;color:rgba(0,0,0,0.25);font-style:italic;pointer-events:none;letter-spacing:0.02em;z-index:1;user-select:none;';
    div.innerHTML = 'Built with <span style="color:#E1000F;">♥</span> in Paris 11e';
    document.body.appendChild(div);
  }
  setTimeout(injectBuiltWithLove, 600);

  /* ========================================================================
     3) WIDGET "OPÉRATIONS DU JOUR" mini-stat hover en haut
     ====================================================================== */
  const DAY_STATS = {
    nouveaux: Math.floor(Math.random() * 30) + 10,
    demarches: Math.floor(Math.random() * 200) + 100,
    lre: Math.floor(Math.random() * 30) + 5,
    revenue: Math.floor(Math.random() * 2000) + 500
  };

  function injectDayStats() {
    const topbar = document.querySelector('.topbar') || document.querySelector('header');
    if (!topbar || document.getElementById('siaDayStats')) return;
    const widget = document.createElement('div');
    widget.id = 'siaDayStats';
    widget.style.cssText = 'display:none;position:absolute;top:60px;right:24px;background:white;border:1px solid #eee;border-radius:14px;padding:14px;box-shadow:0 12px 32px rgba(0,0,0,0.15);min-width:260px;z-index:9999;';
    widget.innerHTML = `
      <div style="font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.08em;font-weight:700;margin-bottom:10px;">Opérations · ${new Date().toLocaleDateString('fr-FR')}</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;">
        <div><div style="font-size:11px;color:#888;">Nouveaux</div><div style="font-size:18px;font-weight:800;color:#18753C;">+${DAY_STATS.nouveaux}</div></div>
        <div><div style="font-size:11px;color:#888;">Démarches</div><div style="font-size:18px;font-weight:800;color:#000091;">${DAY_STATS.demarches}</div></div>
        <div><div style="font-size:11px;color:#888;">LRE envoyées</div><div style="font-size:18px;font-weight:800;color:#FF6F00;">${DAY_STATS.lre}</div></div>
        <div><div style="font-size:11px;color:#888;">Revenue</div><div style="font-size:18px;font-weight:800;color:#18753C;">${DAY_STATS.revenue} €</div></div>
      </div>
    `;
    document.body.appendChild(widget);

    /* Indicateur clignote vert dans le topbar */
    const dot = document.createElement('span');
    dot.style.cssText = 'display:inline-block;width:8px;height:8px;background:#18753C;border-radius:50%;margin-left:8px;animation:siaPulse 2s ease-in-out infinite;cursor:pointer;';
    dot.title = 'Activité temps réel · cliquez pour voir';
    dot.addEventListener('click', e => {
      e.stopPropagation();
      widget.style.display = widget.style.display === 'block' ? 'none' : 'block';
    });
    document.addEventListener('click', e => { if (!widget.contains(e.target) && e.target !== dot) widget.style.display = 'none'; });

    const search = topbar.querySelector('.topbar-search') || topbar;
    search.appendChild(dot);

    if (!document.getElementById('siaPulseAnim')) {
      const s = document.createElement('style');
      s.id = 'siaPulseAnim';
      s.textContent = '@keyframes siaPulse{0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(24,117,60,0.4)}50%{opacity:0.8;box-shadow:0 0 0 8px rgba(24,117,60,0)}}';
      document.head.appendChild(s);
    }
  }
  setTimeout(injectDayStats, 900);

  /* ========================================================================
     4) MOTIVATIONAL QUOTE au démarrage (toast subtil après 4s)
     ====================================================================== */
  const ADMIN_QUOTES = [
    '« Le travail bien fait est la meilleure publicité. » — Anonyme',
    '« 90% du succès, c\'est juste de se montrer. » — Woody Allen',
    '« Aujourd\'hui est le premier jour du reste du back-office. » — Vous, peut-être',
    '« Ship it. Tomorrow is too late. » — Reid Hoffman',
    '« Les meilleurs admins lisent les logs. » — Proverbe DevOps',
    '« Un utilisateur heureux en vaut deux. » — Stratégie commerciale française'
  ];

  if (!sessionStorage.getItem('sia.admin.quote.shown')) {
    setTimeout(() => {
      const q = ADMIN_QUOTES[Math.floor(Math.random() * ADMIN_QUOTES.length)];
      if (window.adToast) window.adToast(q, true);
      sessionStorage.setItem('sia.admin.quote.shown', '1');
    }, 4000);
  }

  /* ========================================================================
     5) RACCOURCI CLAVIER "G + D" → dashboard, "G + I" → inbox, etc.
     ====================================================================== */
  let gMode = false;
  let gTimer = null;
  document.addEventListener('keydown', e => {
    if (e.target.matches('input, textarea, select, [contenteditable]')) return;
    if (e.key === 'g' && !e.metaKey && !e.ctrlKey) {
      gMode = true;
      clearTimeout(gTimer);
      gTimer = setTimeout(() => gMode = false, 1500);
      return;
    }
    if (gMode) {
      const map = {
        'd': 'dashboard', 'i': 'inbox', 'u': 'users', 'w': 'waitlist',
        'p': 'press', 'a': 'api', 's': 'settings', 'c': 'cerveau'
      };
      const target = map[e.key];
      if (target) {
        const btn = document.querySelector(`[data-go="${target}"]`);
        if (btn) {
          btn.click();
          window.adToast?.(`Nav · ${target}`, true);
        }
        gMode = false;
      }
    }
  });

  /* ========================================================================
     6) TEMPS PASSÉ DANS L'ADMIN aujourd'hui (tracking session)
     ====================================================================== */
  const startTime = Date.now();
  window.addEventListener('beforeunload', () => {
    const minutes = Math.floor((Date.now() - startTime) / 60000);
    const dayKey = 'sia.admin.time.' + new Date().toISOString().slice(0, 10);
    const prev = parseInt(localStorage.getItem(dayKey) || '0', 10);
    localStorage.setItem(dayKey, String(prev + minutes));
  });

  /* ========================================================================
     7) Run init
     ====================================================================== */
  setTimeout(injectCoffeeCounter, 800);

  // console.log('[Admin Polish] Pack 23 admin · ☕ compteur café · 📊 stats jour · ⌨ raccourcis G+letter · ❤ built in Paris');
})();
