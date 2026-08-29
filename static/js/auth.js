let currentUser = null;

function enterAsGuest() {
  document.getElementById('welcome-screen').classList.add('hidden');
  document.getElementById('main-app').classList.remove('hidden');
  document.getElementById('user-display-name').innerText = 'Гость';
  document.getElementById('fav-btn').classList.add('hidden');
  loadHeroes();
}

function openAuthModal() {
  document.getElementById('auth-modal').classList.remove('hidden');
}

function closeAuthModal() {
  document.getElementById('auth-modal').classList.add('hidden');
  document.getElementById('auth-error').classList.add('hidden');
}

let authMode = 'login';

function switchAuthMode(mode) {
  authMode = mode;
  document.getElementById('tab-login').classList.toggle('active', mode === 'login');
  document.getElementById('tab-register').classList.toggle('active', mode === 'register');
  document.getElementById('auth-submit-btn').innerText = mode === 'login' ? 'Войти' : 'Зарегистрироваться';
  document.getElementById('auth-error').classList.add('hidden');
}

async function submitAuth() {
  const usernameInput = document.getElementById('auth-username').value.trim();
  const passwordInput = document.getElementById('auth-password').value.trim();
  const errorBox = document.getElementById('auth-error');

  if (!usernameInput || !passwordInput) {
    errorBox.innerText = 'Заполните все поля';
    errorBox.classList.remove('hidden');
    return;
  }

  const endpoint = authMode === 'login' ? '/api/login' : '/api/register';

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: usernameInput, password: passwordInput })
    });

    const data = await response.json();

    if (!response.ok) {
      errorBox.innerText = data.detail || 'Ошибка авторизации';
      errorBox.classList.remove('hidden');
      return;
    }

    currentUser = data;
    localStorage.setItem('dota_user', JSON.stringify(data));

    document.getElementById('welcome-screen').classList.add('hidden');
    document.getElementById('main-app').classList.remove('hidden');
    document.getElementById('user-display-name').innerText = data.username;
    document.getElementById('fav-btn').classList.remove('hidden');
    closeAuthModal();
    loadHeroes();
  } catch (err) {
    errorBox.innerText = 'Ошибка соединения с сервером';
    errorBox.classList.remove('hidden');
  }
}

function logout() {
  localStorage.removeItem('dota_user');
  location.reload();
}

window.addEventListener('DOMContentLoaded', () => {
  const savedUser = localStorage.getItem('dota_user');
  if (savedUser) {
    currentUser = JSON.parse(savedUser);
    document.getElementById('welcome-screen').classList.add('hidden');
    document.getElementById('main-app').classList.remove('hidden');
    document.getElementById('user-display-name').innerText = currentUser.username;
    document.getElementById('fav-btn').classList.remove('hidden');
    
    loadHeroes();
    updateGlobalBanList(); // <-- ДОБАВЬ ЭТУ СТРОЧКУ
  }
});
