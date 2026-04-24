// js/api.js — central API client + auth helpers

const API = (() => {
  const BASE = window.API_BASE = "https://campus-events-management-system.onrender.com";

  // ── TOKEN ────────────────────────────────────────────────────────────────
  const getToken  = ()    => localStorage.getItem('ce_token');
  const getUser   = ()    => JSON.parse(localStorage.getItem('ce_user') || 'null');
  const setAuth   = (tok, user) => {
    localStorage.setItem('ce_token', tok);
    localStorage.setItem('ce_user', JSON.stringify(user));
  };
  const clearAuth = ()    => {
    localStorage.removeItem('ce_token');
    localStorage.removeItem('ce_user');
  };
  const isLoggedIn = () => !!getToken();

  // ── FETCH WRAPPER ─────────────────────────────────────────────────────────
  async function request(method, path, body = null, auth = false) {
    const headers = { 'Content-Type': 'application/json' };
    if (auth || getToken()) headers['Authorization'] = `Bearer ${getToken()}`;
    const opts = { method, headers };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${BASE}${path}`, opts);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw { status: res.status, message: data.detail || 'Request failed' };
    return data;
  }

  const get  = (path, auth = false) => request('GET',    path, null, auth);
  const post = (path, body, auth = false) => request('POST',   path, body, auth);
  const del  = (path, auth = true)  => request('DELETE', path, null, auth);

  // ── AUTH ENDPOINTS ────────────────────────────────────────────────────────
  async function register(name, email, password) {
    const data = await post('/api/auth/register', { name, email, password });
    setAuth(data.token, data.user);
    return data;
  }
  async function login(email, password) {
    const data = await post('/api/auth/login', { email, password });
    setAuth(data.token, data.user);
    return data;
  }
  function logout() {
    clearAuth();
    window.location.href = '/';
  }

  // ── EVENT ENDPOINTS ───────────────────────────────────────────────────────
  const getEvents     = (q = '') => get(`/api/events${q ? '?q=' + encodeURIComponent(q) : ''}`);
  const getEvent      = (id)     => get(`/api/events/${id}`);
  const registerEvent = (id, payload) => post(`/api/events/${id}/register`, payload, true);

  // ── PROFILE ENDPOINTS ──────────────────────────────────────────────────────
  const getMyRegistrations  = ()    => get('/api/my-registrations', true);
  const cancelRegistration  = (id)  => del(`/my-registrations/${id}`);

  return {
    getToken, getUser, isLoggedIn, clearAuth, setAuth,
    register, login, logout,
    getEvents, getEvent, registerEvent,
    getMyRegistrations, cancelRegistration,
  };
})();

// ── TOAST ──────────────────────────────────────────────────────────────────
function toast(message, type = 'info', duration = 3500) {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✓', error: '✕', info: '●' };
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.innerHTML = `<span style="font-size:1rem;">${icons[type] || '●'}</span><span>${message}</span>`;
  container.appendChild(t);
  setTimeout(() => {
    t.style.animation = 'slide-out .3s ease forwards';
    setTimeout(() => t.remove(), 300);
  }, duration);
}

// ── NAVBAR HYDRATION ───────────────────────────────────────────────────────
function hydrateNavbar() {
  const user = API.getUser();
  const authLinks = document.getElementById('auth-links');
  const userMenu  = document.getElementById('user-menu');
  if (!authLinks || !userMenu) return;

  if (user) {
    authLinks.style.display = 'none';
    userMenu.style.display  = 'flex';
    const initials = user.name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0,2);
    const av = document.getElementById('nav-avatar');
    if (av) av.textContent = initials;
    const nm = document.getElementById('nav-username');
    if (nm) nm.textContent = user.name.split(' ')[0];
  } else {
    authLinks.style.display = 'flex';
    userMenu.style.display  = 'none';
  }
}

// ── FORMAT HELPERS ─────────────────────────────────────────────────────────
function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleDateString('en-IN', { day:'numeric', month:'short', year:'numeric' });
}
function daysUntil(dateStr) {
  const diff = new Date(dateStr) - new Date();
  const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
  if (days < 0)  return 'Past';
  if (days === 0) return 'Today';
  if (days === 1) return 'Tomorrow';
  return `In ${days} days`;
}
function requireAuth(redirect = 'pages/login.html') {
  if (!API.isLoggedIn()) { window.location.href = redirect; return false; }
  return true;
}

// ── MOBILE MENU ────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  hydrateNavbar();
  const ham = document.getElementById('hamburger');
  const mob = document.getElementById('mobile-menu');
  if (ham && mob) {
    ham.addEventListener('click', () => mob.classList.toggle('open'));
    mob.querySelectorAll('a').forEach(a => a.addEventListener('click', () => mob.classList.remove('open')));
    document.addEventListener('click', e => {
      if (!ham.contains(e.target) && !mob.contains(e.target)) mob.classList.remove('open');
    });
  }
  // logout buttons
  document.querySelectorAll('[data-logout]').forEach(el =>
    el.addEventListener('click', e => { e.preventDefault(); API.logout(); })
  );
});