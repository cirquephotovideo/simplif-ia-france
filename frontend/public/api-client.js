/**
 * SDK JavaScript Simplif'IA France · Browser side
 * Usage : import "/api-client.js" → window.api.*
 */
(function () {
  const API_BASE = window.SIMPLIFIA_API_BASE || '/api';
  const TOKEN_KEY = 'simplifia.access';
  const REFRESH_KEY = 'simplifia.refresh';

  function getToken() { return localStorage.getItem(TOKEN_KEY); }
  function setTokens(access, refresh) {
    localStorage.setItem(TOKEN_KEY, access);
    if (refresh) localStorage.setItem(REFRESH_KEY, refresh);
  }
  function clearTokens() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_KEY);
  }

  async function request(path, opts = {}) {
    const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    const res = await fetch(API_BASE + path, { ...opts, headers });
    if (res.status === 401 && opts._retry !== true) {
      const ok = await tryRefresh();
      if (ok) return request(path, { ...opts, _retry: true });
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Erreur API');
    }
    const ct = res.headers.get('Content-Type') || '';
    if (ct.includes('application/json')) return res.json();
    if (ct.includes('audio/')) return res.blob();
    return res.text();
  }

  async function tryRefresh() {
    const rt = localStorage.getItem(REFRESH_KEY);
    if (!rt) return false;
    try {
      const r = await fetch(API_BASE + '/auth/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: rt }),
      });
      if (!r.ok) return false;
      const data = await r.json();
      setTokens(data.access_token, data.refresh_token);
      return true;
    } catch { return false; }
  }

  window.api = {
    // Auth
    register: (data) => request('/auth/register', { method: 'POST', body: JSON.stringify(data) }),
    login: async (email, password) => {
      const data = await request('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
      setTokens(data.access_token, data.refresh_token);
      return data;
    },
    logout: async () => { try { await request('/auth/logout', { method: 'POST' }); } catch {} clearTokens(); },
    me: () => request('/auth/me'),

    // Vault
    listDocs: (category) => request('/vault' + (category ? `?category=${category}` : '')),
    uploadDoc: async (file, name, category) => {
      const fd = new FormData();
      fd.append('file', file);
      fd.append('name', name);
      fd.append('category', category || 'autre');
      const headers = {};
      const t = getToken(); if (t) headers.Authorization = `Bearer ${t}`;
      const r = await fetch(API_BASE + '/vault/upload', { method: 'POST', headers, body: fd });
      if (!r.ok) throw new Error((await r.json()).detail || 'Upload échoué');
      return r.json();
    },
    deleteDoc: (id) => request(`/vault/${id}`, { method: 'DELETE' }),

    // Démarches
    listDemarches: (status) => request('/demarches' + (status ? `?status=${status}` : '')),
    createDemarche: (data) => request('/demarches', { method: 'POST', body: JSON.stringify(data) }),
    updateDemarche: (id, data) => request(`/demarches/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),

    // CERFAs
    listCerfas: (q, category) => {
      const p = new URLSearchParams();
      if (q) p.set('q', q); if (category) p.set('category', category);
      return request('/cerfas' + (p.toString() ? '?' + p : ''));
    },

    // IA
    chat: (question, falc = false) => request('/ai/chat', { method: 'POST', body: JSON.stringify({ question, falc }) }),
    translate: (text) => request('/ai/translate', { method: 'POST', body: JSON.stringify({ text }) }),

    // TTS
    speak: async (text, voiceId) => {
      const r = await fetch(API_BASE + '/tts/synthesize', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
        body: JSON.stringify({ text, voice_id: voiceId }),
      });
      if (!r.ok) throw new Error('TTS échoué');
      return r.blob();
    },

    // APIs Gouv
    searchAddress: (q) => request('/gouv/address/search?q=' + encodeURIComponent(q)),
    searchCompany: (q) => request('/gouv/company/search?q=' + encodeURIComponent(q)),
    findCAF: (cp) => request('/gouv/admin/caf?postal_code=' + cp),
    communes: (cp) => request('/gouv/communes?postal_code=' + cp),

    // Admin
    dashboard: () => request('/admin/dashboard'),
    auditLogs: (skip = 0, limit = 100) => request(`/admin/audit?skip=${skip}&limit=${limit}`),
    listUsers: () => request('/users'),

    // Utils
    isAuthenticated: () => !!getToken(),
    clearTokens,
  };
})();
