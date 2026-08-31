let currentUser = null;

function enterAsGuest() {
  const welcome = document.getElementById('welcome-screen');
  const mainApp = document.getElementById('main-app');
  if (welcome) welcome.classList.add('hidden');
  if (mainApp) mainApp.classList.remove('hidden');
  
  const nameDisplay = document.getElementById('user-display-name');
  if (nameDisplay) nameDisplay.innerText = 'Гость';
  
  // Если есть функция загрузки героев (в drafts.html), запускаем
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
        document.getElementById('auth-error').classList.add('hidden');
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
      // Сохраняем данные для синхронизации между страницами
      localStorage.setItem('dota_user', JSON.stringify(data));
      // Перезагружаем, чтобы main.py отдал страницу в состоянии "залогинен"
      location.reload();
    } else {
      const err = await res.json();
      errorBox.innerText = err.detail || "Ошибка авторизации";
      errorBox.classList.remove('hidden');
    }
  } catch (e) {
    errorBox.innerText = "Ошибка соединения с сервером";
    errorBox.classList.remove('hidden');
  }
}

function loginWithSteam() {
    // Переход на бэкенд-роут Steam Auth
    window.location.href = '/api/login/steam';
}

function logout() {
    localStorage.removeItem('dota_user');
    // Удаляем сессионную куку (опционально, бэкенд тоже проверит)
    document.cookie = "session=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
    window.location.href = '/';
}

// Проверка состояния при загрузке любой страницы
window.addEventListener('DOMContentLoaded', async () => {
  const welcome = document.getElementById('welcome-screen');
  const mainApp = document.getElementById('main-app');
  const nameDisplay = document.getElementById('user-display-name');

  // 1. Проверяем локальное хранилище
  const savedUser = localStorage.getItem('dota_user');
  
  // 2. Параллельно спрашиваем бэкенд (для Steam сессий)
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
      } else if (savedUser) {
          // Если сервер не знает, но в локале есть (старый вход по паролю)
          currentUser = JSON.parse(savedUser);
          if (welcome) welcome.classList.add('hidden');
          if (mainApp) mainApp.classList.remove('hidden');
          if (nameDisplay) nameDisplay.innerText = currentUser.username;
          if (typeof loadHeroes === 'function') loadHeroes();
      }
  } catch (e) {
      console.warn("Авторизация не проверена:", e);
  }
});
