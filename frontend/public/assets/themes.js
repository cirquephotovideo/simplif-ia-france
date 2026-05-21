/* ============================================================================
   Simplif'IA · Theme switcher (Pack 21 v2)
   Thème par défaut : FAMILIAL (rouge / jaune / vert doux)
   Alternative : MARBRE & OR (noir + doré + étoiles)
   Persisté en localStorage (clé: sia.theme)
   ============================================================================ */
(function () {
  const DEFAULT_THEME = 'familial';

  const THEMES = [
    {
      id: 'familial',
      name: 'Familial',
      desc: 'Doux et accessible · couleurs pour tous les âges',
      icon: '🌿',
      swatch: 'linear-gradient(135deg, #C73032 0%, #E8B53A 50%, #5A8F4F 100%)'
    },
    {
      id: 'marbre',
      name: 'Marbre & Or',
      desc: 'Noir profond · marbre doré · étoiles scintillantes',
      icon: '✨',
      swatch: 'linear-gradient(135deg, #08070D 0%, #D4AF37 50%, #FFD700 100%)'
    },
    {
      id: '',
      name: 'Moderne',
      desc: 'Blanc épuré · bleu Marianne · style original',
      icon: '⚪',
      swatch: 'linear-gradient(135deg, #FFFFFF 0%, #000091 50%, #E1000F 100%)'
    }
  ];

  function getTheme() {
    /* Premier visiteur sans choix : on applique le DEFAULT_THEME (Familial) */
    const stored = localStorage.getItem('sia.theme');
    if (stored === null) return DEFAULT_THEME;
    return stored;
  }

  function applyTheme(id) {
    if (id) document.body.setAttribute('data-theme', id);
    else document.body.removeAttribute('data-theme');
    localStorage.setItem('sia.theme', id);
    document.dispatchEvent(new CustomEvent('sia:theme-changed', { detail: { theme: id } }));
  }

  function renderMenu() {
    const current = getTheme();
    const menu = document.getElementById('siaThemeMenu');
    if (!menu) return;
    menu.innerHTML = `
      <div style="padding:10px 14px 6px;font-size:11px;text-transform:uppercase;letter-spacing:0.1em;font-weight:700;color:#888;">
        Choisir l'apparence
      </div>
      ${THEMES.map(t => `
        <button class="sia-theme-option ${t.id === current ? 'active' : ''}" data-theme-id="${t.id}" type="button">
          <div class="sia-theme-swatch" style="background:${t.swatch};"></div>
          <div class="sia-theme-info">
            <div class="sia-theme-name">${t.icon} ${t.name}</div>
            <div class="sia-theme-desc">${t.desc}</div>
          </div>
          ${t.id === current ? '<span style="color:#5A8F4F;font-weight:800;">✓</span>' : ''}
        </button>
      `).join('')}
      <div style="padding:10px 14px;font-size:11px;color:#888;border-top:1px solid #eee;margin-top:4px;">
        Votre choix est mémorisé · valable sur toutes les pages
      </div>
    `;
    menu.querySelectorAll('.sia-theme-option').forEach(btn => {
      btn.addEventListener('click', () => {
        applyTheme(btn.dataset.themeId);
        renderMenu();
        setTimeout(() => menu.classList.remove('open'), 600);
      });
    });
  }

  function injectNavSwitcher() {
    /* Bouton dans la nav (visible, pas caché en FAB) */
    const navCta = document.querySelector('.site-nav-cta');
    if (!navCta || navCta.querySelector('.sia-nav-theme')) return;
    const btn = document.createElement('button');
    btn.className = 'sia-nav-theme';
    btn.type = 'button';
    btn.setAttribute('aria-label', 'Changer de thème');
    btn.title = 'Changer le thème du site';
    btn.innerHTML = '🎨 <span class="sia-nav-theme-label">Thème</span>';
    btn.addEventListener('click', e => {
      e.stopPropagation();
      toggleMenu();
    });
    navCta.insertBefore(btn, navCta.firstChild);
  }

  function toggleMenu() {
    const menu = document.getElementById('siaThemeMenu');
    if (!menu) return;
    menu.classList.toggle('open');
    if (menu.classList.contains('open')) renderMenu();
  }

  function init() {
    /* Appliquer le thème dès que possible (anti-flash) */
    const current = getTheme();
    if (current) document.body.setAttribute('data-theme', current);

    /* Bouton flottant 🎨 (en plus du nav button) pour mobile */
    if (!document.getElementById('siaThemeSwitcher')) {
      const btn = document.createElement('button');
      btn.id = 'siaThemeSwitcher';
      btn.className = 'sia-theme-switcher';
      btn.title = 'Changer le thème du site';
      btn.setAttribute('aria-label', 'Changer de thème');
      btn.textContent = '🎨';
      btn.addEventListener('click', e => {
        e.stopPropagation();
        toggleMenu();
      });
      document.body.appendChild(btn);
    }

    /* Menu */
    if (!document.getElementById('siaThemeMenu')) {
      const menu = document.createElement('div');
      menu.id = 'siaThemeMenu';
      menu.className = 'sia-theme-menu';
      document.body.appendChild(menu);
    }

    /* Bouton dans nav */
    injectNavSwitcher();

    /* Click outside ferme le menu */
    document.addEventListener('click', e => {
      const menu = document.getElementById('siaThemeMenu');
      const fab = document.getElementById('siaThemeSwitcher');
      const navBtn = document.querySelector('.sia-nav-theme');
      if (menu && !menu.contains(e.target) && e.target !== fab && navBtn !== e.target && !navBtn?.contains(e.target)) {
        menu.classList.remove('open');
      }
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') document.getElementById('siaThemeMenu')?.classList.remove('open');
    });

    /* Si premier visiteur : poser explicitement le defaut pour persister */
    if (localStorage.getItem('sia.theme') === null) {
      localStorage.setItem('sia.theme', DEFAULT_THEME);
    }
  }

  /* Init aussitôt que possible (DOM not required for setAttribute on body) */
  if (document.body) {
    const current = getTheme();
    if (current) document.body.setAttribute('data-theme', current);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  /* API publique */
  window.siaTheme = {
    get: getTheme,
    set: applyTheme,
    list: () => [...THEMES]
  };

  // console.log('[Simplif\'IA] Themes loaded · default=' + DEFAULT_THEME + ' · current=' + getTheme());
})();
