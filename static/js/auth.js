let currentUser = null;
const enterAsGuest = () => {
    document.getElementById('welcome-screen').classList.add('hidden');
    document.getElementById('main-app').classList.remove('hidden');
    loadHeroes();
};
const openAuthModal = () => document.getElementById('auth-modal').classList.remove('hidden');
const closeAuthModal = () => document.getElementById('auth-modal').classList.add('hidden');
let authMode = 'login';
const switchAuthMode = (mode) => {
    authMode = mode;
    document.getElementById('tab-login').className = mode === 'login' ? 'active' : '';
    document.getElementById('tab-register').className = mode === 'register' ? 'active' : '';
};
async function submitAuth() {
    const username = document.getElementById('auth-username').value;
    const password = document.getElementById('auth-password').value;
    const res = await fetch(`/api/${authMode}`, {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({username, password})
    });
    if (res.ok) {
        currentUser = await res.json();
        localStorage.setItem('dota_user', JSON.stringify(currentUser));
        location.reload();
    } else {
        alert("Ошибка авторизации");
    }
}
const logout = () => { localStorage.removeItem('dota_user'); location.reload(); };
window.addEventListener('DOMContentLoaded', () => {
    const saved = localStorage.getItem('dota_user');
    if (saved) {
        currentUser = JSON.parse(saved);
        enterAsGuest();
        document.getElementById('user-display-name').innerText = currentUser.username;
        document.getElementById('fav-btn').classList.remove('hidden');
        updateGlobalBanList();
    }
});
