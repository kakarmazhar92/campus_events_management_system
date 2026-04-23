// js/navbar.js — injects navbar + toast container into page

(function () {
  const isRoot = !window.location.pathname.includes('/pages/');
  const root   = isRoot ? '' : '../';

  document.body.insertAdjacentHTML('afterbegin', `
  <nav class="navbar">
    <a href="${root}index.html" class="navbar-brand">Campus<span>Events</span></a>

    <div class="navbar-actions" id="auth-links" style="display:none">
      <a href="${root}pages/login.html"    class="nav-link">Sign In</a>
      <a href="${root}pages/register.html" class="btn btn-primary btn-sm">Sign Up</a>
    </div>

    <div class="navbar-actions" id="user-menu" style="display:none">
      <a href="${root}index.html"          class="nav-link">Events</a>
      <a href="${root}pages/profile.html"  class="nav-link">Profile</a>
      <div class="nav-avatar" id="nav-avatar" title="Profile" onclick="window.location.href='${root}pages/profile.html'"></div>
      <button class="btn btn-ghost btn-sm" data-logout>Logout</button>
    </div>

    <button class="hamburger" id="hamburger" aria-label="Menu">
      <span></span><span></span><span></span>
    </button>
  </nav>

  <div class="mobile-menu" id="mobile-menu">
    <a href="${root}index.html"          class="nav-link">🎓 Events</a>
    <a href="${root}pages/profile.html"  class="nav-link">👤 Profile</a>
    <a href="${root}pages/login.html"    class="nav-link" id="mob-login">Sign In</a>
    <a href="${root}pages/register.html" class="nav-link" id="mob-register">Sign Up</a>
    <a href="#" class="nav-link" data-logout id="mob-logout" style="display:none">Logout</a>
  </div>

  <div id="toast-container"></div>
  `);

  // After inject, sync mobile menu auth state
  document.addEventListener('DOMContentLoaded', () => {
    if (API.isLoggedIn()) {
      const ml = document.getElementById('mob-login');
      const mr = document.getElementById('mob-register');
      const mo = document.getElementById('mob-logout');
      if (ml) ml.style.display = 'none';
      if (mr) mr.style.display = 'none';
      if (mo) mo.style.display = 'block';
      const nm = document.getElementById('nav-username');
      if (nm) nm.textContent = (API.getUser()?.name || '').split(' ')[0];
    }
  });
})();