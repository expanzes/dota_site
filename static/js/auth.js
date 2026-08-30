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

function openAuthModal() { document.getElementById('auth-modal').classList.remove('hidden'); }
function closeAuthModal() { document.getElementById('auth-modal').classList.add('hidden'); }

let authMode = 'login';
function switchAuthMode(mode) {
  authMode = mode;
  document.getElementById('tab-login').classList.toggle('active', mode === 'login');
  document.getElementById('tab-register').classList.toggle('active', mode === 'register');
}

async function submitAuth() {
  const username = document.getElementById('auth-username').value;
  const password = document.getElementById('auth-password').value;
  const res = await fetch(`/api/${authMode}`, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({username, password})
  });
  if (res.ok) {
    const data = await res.json();
    localStorage.setItem('dota_user', JSON.stringify(data));
    location.reload();
  } else {
    const err = await res.json();
    document.getElementById('auth-error').innerText = err.detail || "Ошибка";
    document.getElementById('auth-error').classList.remove('hidden');
  }
}

function logout() { localStorage.removeItem('dota_user'); location.href = '/'; }

window.addEventListener('DOMContentLoaded', () => {
  const savedUser = localStorage.getItem('dota_user');
  const welcome = document.getElementById('welcome-screen');
  const mainApp = document.getElementById('main-app');
  const nameDisplay = document.getElementById('user-display-name');

  if (savedUser) {
    currentUser = JSON.parse(savedUser);
    if (welcome) welcome.classList.add('hidden');
    if (mainApp) mainApp.classList.remove('hidden');
    if (nameDisplay) nameDisplay.innerText = currentUser.username;
    if (typeof loadHeroes === 'function') loadHeroes();
    // На странице профиля ставим имя
    const profileName = document.getElementById('profile-user-name');
    if (profileName) profileName.innerText = currentUser.username;
  }
});
