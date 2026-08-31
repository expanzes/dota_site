let currentUser = null;

function enterAsGuest() {
  const welcome = document.getElementById('welcome-screen');
  const mainApp = document.getElementById('main-app');
  if (welcome) welcome.classList.add('hidden');
  if (mainApp) mainApp.classList.remove('hidden');
  const nameDisplay = document.getElementById('user-display-name');
  if (nameDisplay) nameDisplay.innerText = 'Гость';
  if (typeof loadHeroes === 'function') loadHeroes();
}

function openAuthModal() { 
    const modal = document.getElementById('auth-modal');
    if(modal) modal.classList.remove('hidden'); 
}

function closeAuthModal() { 
    const modal = document.getElementById('auth-modal');
    if(modal) {
        modal.classList.add('hidden'); 
        const err = document.getElementById('auth-error');
        if(err) err.classList.add('hidden');
    }
}

let authMode = 'login';
function switchAuthMode(mode) {
  authMode = mode;
  document.getElementById('tab-login').classList.toggle('active', mode === 'login');
  document.getElementById('tab-register').classList.toggle('active', mode === 'register');
}

async function submitAuth() {
  const username = document.getElementById('auth-username').value;
  const password = document.getElementById('auth-password').value;
  const errorBox = document.getElementById('auth-error');

  try {
    const res = await fetch(`/api/${authMode}`, {
      method: 'POST', 
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({username, password})
    });

    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('dota_user', JSON.stringify(data));
      // ПОСЛЕ РЕГИ/ЛОГИНА СРАЗУ КИДАЕМ В ПРОФИЛЬ
      window.location.href = '/profile';
    } else {
      const err = await res.json();
      errorBox.innerText = err.detail || "Ошибка";
      errorBox.classList.remove('hidden');
    }
  } catch (e) {
    errorBox.innerText = "Ошибка соединения";
    errorBox.classList.remove('hidden');
  }
}

function loginWithSteam() { window.location.href = '/api/login/steam'; }

function logout() {
    localStorage.removeItem('dota_user');
    document.cookie = "session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    window.location.href = '/';
}

window.addEventListener('DOMContentLoaded', async () => {
  const welcome = document.getElementById('welcome-screen');
  const mainApp = document.getElementById('main-app');
  const nameDisplay = document.getElementById('user-display-name');

  try {
      const res = await fetch('/api/me');
      const serverUser = await res.json();

      if (serverUser.logged_in) {
          currentUser = serverUser;
          localStorage.setItem('dota_user', JSON.stringify(serverUser));
          if (welcome) welcome.classList.add('hidden');
          if (mainApp) mainApp.classList.remove('hidden');
          if (nameDisplay) nameDisplay.innerText = serverUser.username;
          if (typeof loadHeroes === 'function') loadHeroes();
      } else {
          // Если не залогинен и не на главной - кидаем на главную (защита профиля)
          if (window.location.pathname === '/profile') {
              window.location.href = '/';
          }
      }
  } catch (e) { console.warn("Session check failed"); }
});
