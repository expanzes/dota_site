let currentUserSiteId = '';
let currentSecurityMode = '';
let isViewingOtherProfile = false;

window.addEventListener('DOMContentLoaded', () => {
    const cachedUser = sessionStorage.getItem('dh_user');
    if (cachedUser) renderUserUI(JSON.parse(cachedUser));
    
    const cachedMatches = sessionStorage.getItem('dh_matches');
    if (cachedMatches && typeof renderMatches === 'function') renderMatches(JSON.parse(cachedMatches));

    fetchData();
});

async function fetchData() {
    try {
        const res = await fetch('/api/me');
        const user = await res.json();
        if (!user.logged_in) return window.location.href = '/auth';
        
        currentUserSiteId = user.site_id;
        sessionStorage.setItem('dh_user', JSON.stringify(user));
        renderUserUI(user);

        if (typeof fetchHeroesList === 'function') {
            await fetchHeroesList();
            await loadFavorites();
            await loadFriends();
        }

        if (user.steam_linked && typeof loadRecentMatches === 'function') loadRecentMatches();
        else if (!user.steam_linked) document.getElementById('matches-list').innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 30px;">Привяжите Steam, чтобы увидеть историю.</div>';
    } catch(e) { console.error("Data error", e); }
}

function renderUserUI(user) {
    let nameHtml = user.username;
    if (user.is_premium) nameHtml += ' <i class="fas fa-crown premium-icon" title="Premium"></i>';
    
    const usernameEl = document.getElementById('display-username');
    usernameEl.innerHTML = nameHtml;
    usernameEl.classList.remove('skeleton', 'skeleton-text');
    
    document.getElementById('display-site-id').innerText = user.site_id;
    document.getElementById('display-email').innerText = user.email || 'Не привязана';
    document.getElementById('display-score').innerText = user.invoker_score || 0;
    if (user.avatar) document.getElementById('profile-avatar').src = user.avatar;
    
    document.getElementById('btn-link-steam').style.display = user.steam_linked ? 'none' : 'block';
    
    // Кнопка ред. ника показывается только для своего профиля
    document.getElementById('btn-edit-name').style.display = isViewingOtherProfile ? 'none' : 'block';
    
    const baseImg = document.getElementById('rank-medal');
    const nameText = document.getElementById('display-rank');

    if (!user.rank || user.rank === 0) {
        baseImg.src = "/static/ranks/0.png";
        baseImg.style.display = "block";
        nameText.innerText = "TBD";
    } else {
        baseImg.src = `/static/ranks/${user.rank}.png`;
        baseImg.style.display = "block";
        const badge = Math.floor(user.rank / 10);
        const star = user.rank % 10;
        let approxMmr = (badge - 1) * 770 + star * 154;
        nameText.innerText = '~ ' + (badge === 8 ? '5600+' : approxMmr);
    }
}

// Редактирование ника
function openNameEditor() {
    document.getElementById('display-username').style.display = 'none';
    document.getElementById('btn-edit-name').style.display = 'none';
    document.getElementById('edit-name-form').classList.remove('hidden');
    document.getElementById('new-username-input').focus();
}

async function submitNameChange(e) {
    e.preventDefault();
    const newName = document.getElementById('new-username-input').value.trim();
    const errBox = document.getElementById('name-error');
    if (newName.length < 3 || newName.length > 15) { errBox.innerText = 'От 3 до 15 символов'; errBox.style.display = 'block'; return; }
    
    const res = await fetch('/api/update-username', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ site_id: currentUserSiteId, new_username: newName }) });
    if (res.ok) { sessionStorage.removeItem('dh_user'); window.location.reload(); }
    else { const data = await res.json(); errBox.innerText = data.detail || "Ошибка"; errBox.style.display = 'block'; }
}

// Аватар
function uploadAvatar(input) {
    if (!input.files || !input.files[0]) return;
    const reader = new FileReader();
    reader.onload = async (e) => {
        const base64 = e.target.result;
        const res = await fetch('/api/update-avatar', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ avatar_base64: base64 }) });
        if (res.ok) { document.getElementById('profile-avatar').src = base64; sessionStorage.removeItem('dh_user'); }
    };
    reader.readAsDataURL(input.files[0]);
}

// Безопасность
function openSecurityModal(mode) { currentSecurityMode = mode; document.getElementById('sec-error').style.display='none'; document.getElementById('sec-step-1').classList.remove('hidden'); document.getElementById('sec-step-2').classList.add('hidden'); document.getElementById('security-modal').classList.remove('hidden'); }
function closeSecurityModal() { document.getElementById('security-modal').classList.add('hidden'); }
async function requestSecurityCode() {
    const res = await fetch('/api/security/request-code', {method: 'POST'});
    if(res.ok) { document.getElementById('sec-step-1').classList.add('hidden'); document.getElementById('sec-step-2').classList.remove('hidden'); document.getElementById('sec-new-email').classList.toggle('hidden', currentSecurityMode !== 'email'); document.getElementById('sec-new-password').classList.toggle('hidden', currentSecurityMode !== 'password'); }
    else { document.getElementById('sec-error').innerText = "Ошибка отправки"; document.getElementById('sec-error').style.display='block'; }
}
async function submitSecurityChange() {
    const code = document.getElementById('sec-code').value.trim();
    const newValue = currentSecurityMode === 'email' ? document.getElementById('sec-new-email').value.trim() : document.getElementById('sec-new-password').value;
    if(code.length !== 6 || !newValue) return;
    const res = await fetch(`/api/security/change-${currentSecurityMode}`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({code, new_value: newValue}) });
    if(res.ok) { sessionStorage.removeItem('dh_user'); window.location.reload(); }
    else { document.getElementById('sec-error').innerText = "Неверный код"; document.getElementById('sec-error').style.display='block'; }
}

async function logout() { sessionStorage.clear(); await fetch('/api/logout', { method: 'POST' }); window.location.href = '/auth'; }
