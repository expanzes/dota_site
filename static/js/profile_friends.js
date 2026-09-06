function toggleFriendsSidebar() { document.getElementById('friends-sidebar').classList.toggle('open'); }

async function loadFriends() {
    try {
        const res = await fetch('/api/friends/list');
        const data = await res.json();
        
        const fList = document.getElementById('friends-list');
        const pList = document.getElementById('pending-requests-list');
        const pCont = document.getElementById('pending-requests-section');
        
        if (data.pending && data.pending.length > 0) {
            pCont.style.display = 'block';
            pList.innerHTML = data.pending.map(u => createUserRowHTML(u, 'pending')).join('');
        } else {
            pCont.style.display = 'none';
        }
        
        if (data.friends && data.friends.length > 0) {
            fList.innerHTML = data.friends.map(u => createUserRowHTML(u, 'friend')).join('');
        } else {
            fList.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 10px;">Список пуст.</div>';
        }
    } catch(e) { console.error(e); }
}

function createUserRowHTML(u, type) {
    const statusTextClass = u.is_online ? 'status-text-online' : 'status-text-offline';
    const statusText = u.is_online ? 'В сети' : 'Не в сети';
    const nameHtml = u.username + (u.is_premium ? ' <i class="fas fa-crown premium-icon"></i>' : '');
    const avatar = u.avatar || '/static/images/default_avatar.png';
    const rankText = (u.rank && u.rank > 0) ? `Tier ${u.rank}` : 'TBD';
    
    let buttons = '';
    if (type === 'friend') {
        buttons = `<button class="action-btn btn-reject" onclick="rejectFriend('${u.site_id}'); event.stopPropagation();"><i class="fas fa-user-minus"></i></button>`;
    } else if (type === 'pending') {
        buttons = `<button class="action-btn btn-add" onclick="acceptFriend('${u.site_id}'); event.stopPropagation();"><i class="fas fa-check"></i></button>
                   <button class="action-btn btn-reject" onclick="rejectFriend('${u.site_id}'); event.stopPropagation();"><i class="fas fa-times"></i></button>`;
    } else if (type === 'search') {
        if (u.friend_status === 'friends') buttons = `<span class="status-text">В друзьях</span>`;
        else if (u.friend_status === 'sent') buttons = `<span class="status-text">Отправлено</span>`;
        else if (u.friend_status === 'received') buttons = `<button class="action-btn btn-add" onclick="acceptFriend('${u.site_id}'); event.stopPropagation();"><i class="fas fa-check"></i></button>`;
        else buttons = `<button class="action-btn btn-add" onclick="sendFriendRequest('${u.site_id}'); event.stopPropagation();"><i class="fas fa-user-plus"></i></button>`;
    }
    
    // Клик по карточке должен переносить в чужой профиль (заглушка на будущее)
    return `
        <div class="friend-item" onclick="alert('Переход в профиль в разработке!')">
            <div class="friend-info">
                <img src="${avatar}" class="friend-avatar">
                <div class="friend-name-box">
                    <span class="friend-name">${nameHtml}</span>
                    <span class="${statusTextClass}">${statusText} • <span class="friend-rank-text">${rankText}</span></span>
                </div>
            </div>
            <div class="friend-actions">${buttons}</div>
        </div>`;
}

async function searchUsers() {
    const q = document.getElementById('friend-search-input').value.trim();
    const container = document.getElementById('search-results-list');
    if (!q) return container.innerHTML = '';
    try {
        const res = await fetch(`/api/users/search?q=${encodeURIComponent(q)}`);
        const data = await res.json();
        if (data.length > 0) {
            container.innerHTML = '<div class="friend-section-title">Результаты:</div>' + data.map(u => createUserRowHTML(u, 'search')).join('');
        } else {
            container.innerHTML = '<div style="color: var(--accent-red); margin-top:10px;">Игрок не найден.</div>';
        }
    } catch(e) { console.error(e); }
}

async function sendFriendRequest(id) { await fetch('/api/friends/request', { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({target_id: id}) }); searchUsers(); loadFriends(); }
async function acceptFriend(id) { await fetch('/api/friends/accept', { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({target_id: id}) }); searchUsers(); loadFriends(); }
async function rejectFriend(id) { await fetch('/api/friends/reject', { method: 'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({target_id: id}) }); searchUsers(); loadFriends(); }
