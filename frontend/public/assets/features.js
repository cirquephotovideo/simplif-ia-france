/* ============================================================================
 * Simplif'IA France · Système de toggles de fonctionnalités
 * Partagé entre admin.html (gestion) et app.html (application)
 * Stockage : localStorage "sia.features" (JSON)
 * ============================================================================ */
(function () {
  'use strict';

  // === DÉFINITION DES FEATURES ===
  // chaque feature : id, label, description, group, enabled (default)
  const FEATURES_CATALOG = [
    // --- Modules produit (app.html) ---
    { id: 'app.module.lea',        group: 'Modules App',     label: '🎙 Maître Léa · IA juridique',     desc: 'Avatar IA + chat sourcé Légifrance',                enabled: true },
    { id: 'app.module.antijargon', group: 'Modules App',     label: '📖 Anti-jargon · 3 niveaux',        desc: 'Traduction courriers admin (original/FALC/impact)', enabled: true },
    { id: 'app.module.cerfa',      group: 'Modules App',     label: '📝 CERFA · pré-remplissage',        desc: 'Catalogue 17 CERFAs + auto-fill',                   enabled: true },
    { id: 'app.module.coffre',     group: 'Modules App',     label: '🔒 Coffre-fort AES-256',           desc: 'Stockage chiffré zero-knowledge',                   enabled: true },
    { id: 'app.module.lre',        group: 'Modules App',     label: '✉️ LRE AR24 eIDAS',                desc: 'Envoi de Lettres Recommandées Électroniques',       enabled: true },
    { id: 'app.module.agent',      group: 'Modules App',     label: '🖱 Clic-par-clic',                 desc: 'Agent navigateur autonome',                         enabled: true },
    { id: 'app.module.etrangers',  group: 'Modules App',     label: '🌍 Étrangers · papiers résidence', desc: 'Titres de séjour, naturalisation, regroupement, OQTF · 10 langues', enabled: true },

    // --- KPIs greeting ---
    { id: 'app.kpi.coffre',        group: 'KPIs Accueil',    label: '📦 KPI Coffre-fort (74 docs)',     desc: 'Carte stats du coffre en haut',                     enabled: true },
    { id: 'app.kpi.demarches',     group: 'KPIs Accueil',    label: '⚠️ KPI Démarches urgentes',         desc: 'Carte démarches avec échéance proche',              enabled: true },
    { id: 'app.kpi.aides',         group: 'KPIs Accueil',    label: '💰 KPI Aides détectées',           desc: 'Carte aides éligibles potentielles',                enabled: true },

    // --- Features transversales ---
    { id: 'app.feat.rating',       group: 'Fonctionnalités', label: '⭐ Notation 5 étoiles',             desc: 'Chip + FAB pour noter l\'app',                       enabled: true },
    { id: 'app.feat.falc',         group: 'Fonctionnalités', label: '🅰️ Mode FALC',                     desc: 'Mode Facile À Lire et Comprendre',                  enabled: true },
    { id: 'app.feat.voice',        group: 'Fonctionnalités', label: '🔊 Lecture vocale Léa',            desc: 'Synthèse vocale ElevenLabs des réponses',           enabled: true },
    { id: 'app.feat.zen',          group: 'Fonctionnalités', label: '🧘 Mode Zen',                      desc: 'Layout minimaliste monochrome',                     enabled: true },
    { id: 'app.feat.search',       group: 'Fonctionnalités', label: '🔍 Recherche universelle Cmd+K',   desc: 'Palette de recherche globale',                      enabled: true },
    { id: 'app.feat.suitepro',     group: 'Fonctionnalités', label: '💼 Suite Pro (FAB)',               desc: 'Module pro : factures, devis, URSSAF...',           enabled: true },
    { id: 'app.feat.pensemaison',  group: 'Fonctionnalités', label: '🏠 Pense-Maison (FAB)',            desc: 'Module foyer : abonnements, garanties...',          enabled: true },
    { id: 'app.feat.sophie',       group: 'Fonctionnalités', label: '🤖 Agent Sophie',                  desc: 'Agent IA secret de tri courriers',                  enabled: true },

    // --- Pages publiques ---
    { id: 'site.page.tarifs',      group: 'Pages Publiques', label: '💰 Page Tarifs',                   desc: '/tarifs.html · 4 plans',                            enabled: true },
    { id: 'site.page.blog',        group: 'Pages Publiques', label: '📰 Page Blog',                     desc: '/blog.html · articles juridiques',                  enabled: true },
    { id: 'site.page.presse',      group: 'Pages Publiques', label: '📰 Page Presse',                   desc: '/presse.html · kit média',                          enabled: true },
    { id: 'site.page.affiliation', group: 'Pages Publiques', label: '💎 Page Affiliation',              desc: '/affiliation.html · 30% à vie',                     enabled: true },
    { id: 'site.page.carrieres',   group: 'Pages Publiques', label: '👥 Page Carrières',                desc: '/carrieres.html · 12 postes',                       enabled: true },
    { id: 'site.page.webinaires',  group: 'Pages Publiques', label: '📺 Page Webinaires',               desc: '/webinaires.html · sessions live',                  enabled: true },

    // --- Back-office (admin.html) ---
    { id: 'admin.cerveau',         group: 'Back-office',     label: '🧠 Cerveau · Roadmap',             desc: 'Dashboard prédictif futuriste',                     enabled: true },
    { id: 'admin.cms',             group: 'Back-office',     label: '📝 CMS · Pages site',              desc: 'Gestion contenu (blog, FAQ, équipe...)',            enabled: true },
    { id: 'admin.telegram',        group: 'Back-office',     label: '✈️ Telegram bot',                  desc: 'Connexion bidirectionnelle',                        enabled: true },
    { id: 'admin.inbox.urgent',    group: 'Back-office',     label: '🚨 Onglet Urgent + gyrophare',     desc: 'Tab rouge animé pour mails urgents',                enabled: true },
    { id: 'admin.vault.pin',       group: 'Back-office',     label: '🔐 Coffre-fort · code PIN',        desc: 'Système 192401 + alertes intrusion',                enabled: true },
    { id: 'admin.vault.requests',  group: 'Back-office',     label: '📩 Demandes accès employés',       desc: 'Messages employés pour code temporaire',            enabled: true },
    { id: 'admin.live.stats',      group: 'Back-office',     label: '📊 Stats live sidebar',            desc: 'MRR / Live / NPS qui s\'actualisent',               enabled: true },

    // --- IA Gemini ---
    { id: 'ai.chat',               group: 'IA Gemini',       label: '💬 Chat Maître Léa',               desc: 'Endpoint /api/ai/chat',                             enabled: true },
    { id: 'ai.ocr',                group: 'IA Gemini',       label: '👁 OCR multimodal',                desc: 'Scan de documents par Gemini Vision',                enabled: true },
    { id: 'ai.cerfa_prefill',      group: 'IA Gemini',       label: '📝 Pré-remplissage CERFA',         desc: 'Auto-fill depuis données coffre',                   enabled: true },
    { id: 'ai.classify',           group: 'IA Gemini',       label: '🏷 Classification courriers',      desc: 'Type, priorité, action',                            enabled: true },
    { id: 'ai.detect_aids',        group: 'IA Gemini',       label: '💶 Détection aides éligibles',     desc: 'APL, prime activité, etc.',                         enabled: true },
    { id: 'ai.letter',             group: 'IA Gemini',       label: '⚖️ Génération RAPO/lettre',         desc: 'Recours formels sourcés',                           enabled: true },
    { id: 'ai.translate',          group: 'IA Gemini',       label: '🌍 Traduction multilingue',        desc: 'FR ↔ EN/AR/ES/...',                                 enabled: true },
    { id: 'ai.fact_check',         group: 'IA Gemini',       label: '✅ Fact-check sourcé',             desc: 'Vérification factuelle',                            enabled: true }
  ];

  const STORAGE_KEY = 'sia.features';

  function loadOverrides() {
    try { return JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}'); }
    catch (e) { return {}; }
  }
  function saveOverrides(map) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(map));
  }

  function isEnabled(featureId) {
    const overrides = loadOverrides();
    if (Object.prototype.hasOwnProperty.call(overrides, featureId)) {
      return !!overrides[featureId];
    }
    const f = FEATURES_CATALOG.find(x => x.id === featureId);
    return f ? f.enabled : true;
  }

  function setEnabled(featureId, value) {
    const overrides = loadOverrides();
    overrides[featureId] = !!value;
    saveOverrides(overrides);
    document.dispatchEvent(new CustomEvent('sia:feature-changed', {
      detail: { id: featureId, enabled: !!value }
    }));
    applyToDOM();
  }

  function reset() {
    localStorage.removeItem(STORAGE_KEY);
    document.dispatchEvent(new CustomEvent('sia:features-reset'));
    applyToDOM();
  }

  /** Applique les toggles aux éléments avec data-feature="id" */
  function applyToDOM(root) {
    const scope = root || document;
    scope.querySelectorAll('[data-feature]').forEach(el => {
      const id = el.getAttribute('data-feature');
      if (!id) return;
      const on = isEnabled(id);
      if (on) {
        el.style.display = '';
        el.removeAttribute('data-feature-hidden');
      } else {
        el.style.display = 'none';
        el.setAttribute('data-feature-hidden', '1');
      }
    });
  }

  function getCatalog() { return FEATURES_CATALOG.slice(); }

  function stats() {
    const overrides = loadOverrides();
    const total = FEATURES_CATALOG.length;
    let active = 0;
    FEATURES_CATALOG.forEach(f => {
      const v = Object.prototype.hasOwnProperty.call(overrides, f.id) ? overrides[f.id] : f.enabled;
      if (v) active++;
    });
    return { total, active, disabled: total - active };
  }

  // === API publique ===
  window.siaFeatures = {
    catalog: getCatalog,
    isEnabled,
    setEnabled,
    reset,
    apply: applyToDOM,
    stats
  };

  // === Auto-apply à DOMContentLoaded ===
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => applyToDOM());
  } else {
    applyToDOM();
  }

  // === Re-apply après mutations (pour éléments injectés tard) ===
  let mutationTimeout = null;
  if (typeof MutationObserver !== 'undefined') {
    const observer = new MutationObserver(() => {
      clearTimeout(mutationTimeout);
      mutationTimeout = setTimeout(() => applyToDOM(), 200);
    });
    document.addEventListener('DOMContentLoaded', () => {
      observer.observe(document.body, { childList: true, subtree: true });
    });
  }
})();
