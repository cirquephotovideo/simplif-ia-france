/* ==========================================================================
 * api-sync.js · Synchronise localStorage ↔ PostgreSQL via l'API FastAPI
 * Pattern : localStorage = cache local · API = source de vérité
 * Sync auto au load + après chaque modification + polling 30s
 * ========================================================================== */
(function () {
  'use strict';

  const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:8000/api'
    : '/api';

  const SYNC_KEYS = {
    'siaInbox': '/mails',
    'sia.vault.requests': '/vault-requests',
    'sia.admin.autopilot': '/settings/autopilot',
    'sia.pack25.urgent.removed': '/settings/urgent.removed',
    'sia.pack25.urgent.responses': '/settings/urgent.responses',
    'sia.demarches.pipeline': '/settings/demarches.pipeline',
    'siaRatings': '/settings/ratings',
    'sia.vault.access-log': '/settings/vault.access-log'
  };

  // === Fetch helper · gère erreurs réseau silencieusement (fallback localStorage) ===
  async function apiFetch(path, opts = {}) {
    try {
      const res = await fetch(API_BASE + path, {
        ...opts,
        headers: { 'Content-Type': 'application/json', ...(opts.headers || {}) },
        credentials: 'include'
      });
      if (!res.ok) throw new Error('HTTP ' + res.status);
      return await res.json();
    } catch (e) {
      console.warn('[api-sync] fetch failed', path, e.message);
      return null;
    }
  }

  // === Migration initiale : upload localStorage → DB si pas déjà fait ===
  async function migrateInitial() {
    const migrated = localStorage.getItem('sia.api.migrated');
    if (migrated === '1') return;

    let migratedSomething = false;

    // 1. Migration mails
    try {
      const inbox = JSON.parse(localStorage.getItem('siaInbox') || '[]');
      if (inbox.length) {
        const payload = inbox.map(m => ({
          external_id: m.id,
          from_name: m.from || '',
          from_email: m.email || '',
          initials: m.initials || '',
          avatar_var: m.avatarVar || 1,
          subject: m.subject || '',
          preview: m.preview || '',
          body: m.body || '',
          tag: (m.tag || 'contact').toLowerCase(),
          priority: m.priority || (m.urgent ? 'high' : 'medium'),
          is_urgent: !!m.urgent,
          is_follow_up: !!m.isFollowUp,
          unread: m.unread !== false,
          starred: !!m.starred,
          archived: !!m.archived,
          thread_of: m.threadOf || null,
          thread: Array.isArray(m.thread) ? m.thread : [],
          ai_suggest: m.aiSuggest || null
        }));
        const result = await apiFetch('/mails/bulk-import', { method: 'POST', body: JSON.stringify(payload) });
        if (result) {
          console.log(`[api-sync] ✓ ${result.imported} mails migrés en base`);
          migratedSomething = true;
        }
      }
    } catch (e) { console.warn('[api-sync] mail migration failed', e); }

    // 2. Migration vault requests
    try {
      const reqs = JSON.parse(localStorage.getItem('sia.vault.requests') || '[]');
      if (reqs.length) {
        const payload = reqs.map(r => ({
          external_id: r.id,
          employee_name: r.name || '',
          employee_email: r.email || '',
          employee_role: r.role || '',
          employee_dept: r.dept || '',
          employee_avatar: r.avatar || '',
          employee_color: r.color || '#6A6AF4',
          reason: r.reason || '',
          priority: (r.priority || 'medium').toLowerCase(),
          initiated_by_admin: !!r.initiatedByAdmin,
          thread: Array.isArray(r.thread) ? r.thread : []
        }));
        const result = await apiFetch('/vault-requests/bulk-import', { method: 'POST', body: JSON.stringify(payload) });
        if (result) {
          console.log(`[api-sync] ✓ ${result.imported} demandes coffre migrées en base`);
          migratedSomething = true;
        }
      }
    } catch (e) { console.warn('[api-sync] vault req migration failed', e); }

    // 3. Migration settings divers (key-value)
    const settingsKeys = [
      ['sia.admin.autopilot', 'autopilot'],
      ['sia.pack25.urgent.removed', 'urgent.removed'],
      ['sia.pack25.urgent.responses', 'urgent.responses'],
      ['sia.demarches.pipeline', 'demarches.pipeline'],
      ['siaRatings', 'ratings'],
      ['sia.vault.access-log', 'vault.access-log']
    ];
    for (const [lsKey, apiKey] of settingsKeys) {
      try {
        const raw = localStorage.getItem(lsKey);
        if (raw === null) continue;
        let value;
        try { value = JSON.parse(raw); } catch { value = raw; }
        await apiFetch('/settings/' + encodeURIComponent(apiKey), {
          method: 'PUT',
          body: JSON.stringify({ key: apiKey, value })
        });
        migratedSomething = true;
      } catch (e) { console.warn('[api-sync] setting migration failed', lsKey, e); }
    }

    if (migratedSomething) {
      localStorage.setItem('sia.api.migrated', '1');
      console.log('[api-sync] ✓ Migration localStorage → DB terminée');
    }
  }

  // === API publique sur window pour les autres scripts ===
  window.siaAPI = {
    base: API_BASE,
    fetch: apiFetch,

    // Mails
    async listMails(filter = 'all', search = null) {
      const params = new URLSearchParams({ filter });
      if (search) params.set('search', search);
      return await apiFetch('/mails?' + params);
    },
    async createMail(mail) {
      return await apiFetch('/mails', { method: 'POST', body: JSON.stringify(mail) });
    },
    async updateMail(id, patch) {
      return await apiFetch('/mails/' + encodeURIComponent(id), { method: 'PATCH', body: JSON.stringify(patch) });
    },
    async deleteMail(id) {
      return await apiFetch('/mails/' + encodeURIComponent(id), { method: 'DELETE' });
    },

    // Vault requests
    async listVaultRequests(status = null) {
      const params = status ? '?status=' + status : '';
      return await apiFetch('/vault-requests' + params);
    },
    async createVaultRequest(req) {
      return await apiFetch('/vault-requests', { method: 'POST', body: JSON.stringify(req) });
    },
    async updateVaultRequest(id, patch) {
      return await apiFetch('/vault-requests/' + encodeURIComponent(id), { method: 'PATCH', body: JSON.stringify(patch) });
    },
    async appendVaultMessage(id, msg) {
      return await apiFetch('/vault-requests/' + encodeURIComponent(id) + '/message', { method: 'POST', body: JSON.stringify(msg) });
    },

    // Settings (key-value)
    async getSetting(key) {
      return await apiFetch('/settings/' + encodeURIComponent(key));
    },
    async setSetting(key, value) {
      return await apiFetch('/settings/' + encodeURIComponent(key), {
        method: 'PUT',
        body: JSON.stringify({ key, value })
      });
    },

    // Migration helpers
    forceMigrate: migrateInitial,
    resetMigration() {
      localStorage.removeItem('sia.api.migrated');
      console.log('[api-sync] Migration flag reset · sera ré-exécutée au prochain load');
    }
  };

  // === Lance la migration au chargement de la page (non bloquant) ===
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setTimeout(migrateInitial, 1500));
  } else {
    setTimeout(migrateInitial, 1500);
  }
})();
