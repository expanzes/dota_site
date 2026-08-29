let selectedFavoriteIds = new Set();
async function openFavModal() {
    document.getElementById('fav-modal').classList.remove('hidden');
    const res = await fetch(`/api/favorites?user_id=${currentUser.user_id}`);
    const data = await res.json();
    selectedFavoriteIds = new Set(data.favorite_ids);
    renderFavGrid();
}
function closeFavModal() { document.getElementById('fav-modal').classList.add('hidden'); }
async function renderFavGrid(q = "") {
    const container = document.getElementById('fav-heroes-container');
    container.innerHTML = "";
    const heroes = await (await fetch('/api/heroes')).json();
    heroes.filter(h => h.name.toLowerCase().includes(q.toLowerCase())).forEach(h => {
        const div = document.createElement('div');
        div.className = `fav-hero-card ${selectedFavoriteIds.has(h.id) ? 'selected' : ''}`;
        div.innerHTML = `<img src="${h.img}"><span>${h.name}</span>`;
        div.onclick = () => {
            if (selectedFavoriteIds.has(h.id)) selectedFavoriteIds.delete(h.id);
            else selectedFavoriteIds.add(h.id);
            renderFavGrid(q);
        };
        container.appendChild(div);
    });
}
async function saveFavorites() {
    await fetch('/api/favorites', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({user_id: currentUser.user_id, favorite_ids: Array.from(selectedFavoriteIds)})
    });
    closeFavModal();
    updateGlobalBanList();
}
async function updateGlobalBanList() {
    const res = await fetch(`/api/global-bans?user_id=${currentUser.user_id}`);
    const data = await res.json();
    const container = document.getElementById('global-ban-slots');
    const section = document.getElementById('personal-ban-section');
    if (!data.bans.length) return section.classList.add('hidden');
    section.classList.remove('hidden');
    container.innerHTML = "";
    data.bans.forEach(h => {
        const div = document.createElement('div');
        div.className = 'ban-slot active';
        div.innerHTML = `<img src="${h.img}"><div class="ban-slot-label">BAN</div>`;
        container.appendChild(div);
    });
}
