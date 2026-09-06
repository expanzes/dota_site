let currentUser = null;
let authMode = 'login';
let pendingUsername = '';

function switchAuthMode(mode) {
  authMode = mode;
  document.getElementById('tab-login').classList.toggle('active', mode === 'login');
  document.getElementById('tab-register').classList.toggle('active', mode === 'register');
  document.getElementById('email-group').style.display = (mode === 'register' || mode === 'steam_register') ? 'block' : 'none';
  document.getElementById('auth-error').style.display = 'none';
}

async function submitAuth() {
  const username = document.getElementById('auth-username').value.trim();
  const password = document.getElementById('auth-password').value;
  const email = document.getElementById('auth-email') ? document.getElementById('auth-email').value.trim() : '';
  const errorBox = document.getElementById('auth-error');

  if (!username || !password || ((authMode === 'register' || authMode === 'steam_register') && !email)) {
      errorBox.innerText = "Заполните все поля!";
      errorBox.style.display = 'block';
      return;
  }

  const payload = { username, password };
  if (authMode === 'register' || authMode === 'steam_register') payload.email = email;

  // Если это регистрация через стим, обращаемся к новому роуту
  const apiRoute = authMode === 'steam_register' ? '/api/register/steam' : `/api/${authMode}`;

  try {
    const res = await fetch(apiRoute, {
      method: 'POST', 
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    
    const data = await res.json();

    if (res.ok) {
      if (data.status === 'pending_verification') {
          pendingUsername = data.username;
          document.getElementById('main-auth-box').style.display = 'none';
          document.getElementById('verify-box').style.display = 'block';
      } else {
          window.location.href = '/profile';
      }
    } else {
      if (res.status === 403) {
          pendingUsername = username;
          document.getElementById('main-auth-box').style.display = 'none';
          document.getElementById('verify-box').style.display = 'block';
      } else {
          errorBox.innerText = data.detail || "Ошибка";
          errorBox.style.display = 'block';
      }
    }
  } catch (e) {
    errorBox.innerText = "Ошибка соединения";
    errorBox.style.display = 'block';
  }
}

async function submitVerification() {
    const code = document.getElementById('verify-code').value.trim();
    const errorBox = document.getElementById('verify-error');
    
    if (code.length !== 6) {
        errorBox.innerText = "Код должен содержать 6 цифр";
        errorBox.style.display = 'block';
        return;
    }

    try {
        const res = await fetch(`/api/verify`, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username: pendingUsername, code})
        });
        if (res.ok) window.location.href = '/profile';
        else {
            const err = await res.json();
            errorBox.innerText = err.detail || "Неверный код";
            errorBox.style.display = 'block';
        }
    } catch(e) {
        errorBox.innerText = "Ошибка соединения";
        errorBox.style.display = 'block';
    }
}

function loginWithSteam() { window.location.href = '/api/login/steam'; }

async function logout() {
    try { await fetch('/api/logout', { method: 'POST' }); } catch (e) {}
    localStorage.removeItem('dota_user');
    window.location.href = '/auth';
}

window.addEventListener('DOMContentLoaded', async () => {
    // Проверка на Steam-регистрацию
    const params = new URLSearchParams(window.location.search);
    if (params.get('mode') === 'steam') {
        authMode = 'steam_register';
        document.querySelector('.auth-tabs').innerHTML = '<h3 style="color: var(--accent-yellow); margin-bottom: 20px; width: 100%;">Завершение привязки Steam</h3>';
        document.getElementById('email-group').style.display = 'block';
        return; // Останавливаем обычную проверку сессии
    }

    try {
        const res = await fetch('/api/me');
        const serverUser = await res.json();
        if (serverUser.logged_in) {
            if (window.location.pathname === '/auth') window.location.href = '/profile';
        } else {
            if (window.location.pathname !== '/auth' && window.location.pathname !== '/') {
                window.location.href = '/auth';
            }
        }
    } catch (e) {}
});
