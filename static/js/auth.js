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
  const emailInput = document.getElementById('auth-email');
  const email = emailInput ? emailInput.value.trim() : '';
  const errorBox = document.getElementById('auth-error');

  if (!username || !password || ((authMode === 'register' || authMode === 'steam_register') && !email)) {
      errorBox.innerText = "Заполните все поля!";
      errorBox.style.display = 'block';
      return;
  }

  const payload = { username, password };
  if (authMode === 'register' || authMode === 'steam_register') payload.email = email;

  // Если это режим привязки Steam, отправляем данные на специальный роут
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
    // 1. Проверяем URL на наличие ?mode=steam
    const params = new URLSearchParams(window.location.search);
    if (params.get('mode') === 'steam') {
        authMode = 'steam_register';
        
        // Убираем вкладки Вход/Регистрация и ставим заголовок
        const tabsContainer = document.querySelector('.auth-tabs');
        if (tabsContainer) {
            tabsContainer.innerHTML = '<h3 style="color: var(--accent-yellow); margin-bottom: 10px; width: 100%; font-size: 1.1rem;">Завершение привязки Steam</h3>';
        }
        
        // Убеждаемся, что поле email существует и отображается
        let emailGroup = document.getElementById('email-group');
        if (!emailGroup) {
            const card = document.getElementById('main-auth-box');
            emailGroup = document.createElement('div');
            emailGroup.id = 'email-group';
            emailGroup.innerHTML = `<input type="email" id="auth-email" class="auth-input" placeholder="E-mail">`;
            card.insertBefore(emailGroup, document.getElementById('auth-password'));
        } else {
            emailGroup.style.display = 'block';
        }
        return; // Останавливаем выполнение, чтобы не сработал редирект профиля ниже
    }

    // 2. Обычная загрузка и проверка сессии, если мы не в режиме Steam
    try {
        const res = await fetch('/api/me');
        const serverUser = await res.json();
        
        // Если уже авторизован, уводим с /auth на /profile
        if (serverUser.logged_in) {
            if (window.location.pathname === '/auth') window.location.href = '/profile';
        } else {
            // Если не авторизован и находится не на главной и не на /auth — выкидываем на /auth
            if (window.location.pathname !== '/auth' && window.location.pathname !== '/') {
                window.location.href = '/auth';
            }
        }
    } catch (e) {}
});
