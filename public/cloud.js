// Toda alteração exige token CSRF da sessão autenticada.
const nativeFetch = window.fetch.bind(window);
let csrfToken;
window.fetch = async function(resource, options = {}) {
  const url = new URL(typeof resource === 'string' ? resource : resource.url, location.href);
  if (url.origin === location.origin && ['POST', 'PUT', 'PATCH', 'DELETE'].includes((options.method || 'GET').toUpperCase())) {
    if (!csrfToken) {
      const result = await nativeFetch('/api/session');
      if (!result.ok) { location.href = '/login'; throw new Error('Entre novamente no sistema.'); }
      csrfToken = (await result.json()).csrf;
    }
    const headers = new Headers(options.headers);
    headers.set('X-CSRF-Token', csrfToken);
    options = {...options, headers};
  }
  const response = await nativeFetch(resource, options);
  if (response.status === 401) location.href = '/login';
  return response;
};
document.addEventListener('DOMContentLoaded', async () => {
  const badge = document.querySelector('.local-badge'); if (badge) badge.textContent = '● ACESSO PRIVADO';
  const side = document.querySelector('.sidebar-bottom');
  if (side) {
    side.replaceChildren();
    const label = document.createElement('span'); label.textContent = 'Sessão privada · dados online'; side.append(label);
    const link = document.createElement('a'); link.href = '/api/full-backup'; link.textContent = '↓ Backup completo'; link.style.display = 'block'; link.style.marginTop = '15px'; side.append(link);
    const btn = document.createElement('button'); btn.textContent = 'Sair'; btn.className = 'primary'; btn.style.marginTop = '15px';
    btn.onclick = async () => { await fetch('/logout', {method:'POST'}); location.href='/login'; }; side.append(btn);
  }
  try { const response = await fetch('/api/state'); const data = await response.json(); const label = document.querySelector('.case-number'); if (label) label.textContent = data.case; } catch {}
});
