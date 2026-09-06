let currentUser = null;
let authMode = 'login';
let pendingUsername = '';

function switchAuthMode(mode) {
  authMode = mode;
  document.getElementById('tab-login').classList.toggle('active', mode === 'login');
  document.getElementById('tab-register').classList.toggle('active', mode === 'register');
  document.getElementById('email-group').style.display = (mode === 'register') ? 'block' : 'none';
  document.getElementById('auth-error').style.display = 'none';
}

async function submitAuth() {
  const username = document.getElementById('auth-username').value.trim();
  const password = document.getElementById('auth-password').value;
  const email = document.getElementById('auth-email') ? document.getElementById('auth-email').value.trim() : '';
  const errorBox = document.getElementById('auth-error');

  if (!username || !password || (authMode === 'register' && !email)) {
      errorBox.innerText = "Заполните все поля!";
      errorBox.style.display = 'block';
      return;
  }

  const payload = { username, password };
  if (authMode === 'register') payload.email = email;

  try {
    const res = await fetch(`/api/${authMode}`, {
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
  const nameDisplay = document.getElementById('user-display-name');
  try {
      const res = await fetch('/api/me');
      const serverUser = await res.json();

      if (serverUser.logged_in) {
          currentUser = serverUser;
          if (nameDisplay) nameDisplay.innerHTML = serverUser.username + (serverUser.is_premium ? ' <i class="fas fa-crown premium-icon"></i>' : '');
          if (window.location.pathname === '/auth') window.location.href = '/profile';
      } else {
          if (window.location.pathname !== '/auth' && window.location.pathname !== '/') {
              window.location.href = '/auth';
          }
      }
  } catch (e) {}
});
