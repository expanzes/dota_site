let allHeroes = [];
let selectedHeroes = [];

async function fetchHeroesList() {
    const cachedHeroes = localStorage.getItem('dh_all_heroes');
    if (cachedHeroes) { allHeroes = JSON.parse(cachedHeroes); return; }
    try {
        const res = await fetch('https://api.opendota.com/api/heroes');
        allHeroes = await res.json();
        allHeroes.sort((a, b) => a.localized_name.localeCompare(b.localized_name));
        localStorage.setItem('dh_all_heroes', JSON.stringify(allHeroes));
    } catch (e) { console.error(e); }
}

async function loadFavorites() {
    try {
        const res = await fetch(`/api/favorites?user_id=${currentUserSiteId}`);
        const data = await res.json();
        selectedHeroes = data.favorite_ids || [];
        renderFavSlots();
    } catch (e) { console.error(e); }
}

function renderFavSlots() {
    const container = document.getElementById('fav-heroes-container');
    container.innerHTML = '';
    let displayHeroes = [];
    if (selectedHeroes.length > 0) {
        let shuffled = [...selectedHeroes].sort(() => 0.5 - Math.random());
        displayHeroes = shuffled.slice(0, 3);
    }
    for (let i = 0; i < 3; i++) {
        let slotHtml = `<div class="fav-hero-slot" onclick="openHeroesModal()"><i class="fas fa-plus"></i></div>`;
        if (displayHeroes[i]) {
            const hero = allHeroes.find(h => h.id === displayHeroes[i]);
            if (hero) {
                const imgName = hero.name.replace('npc_dota_hero_', '');
                slotHtml = `<div class="fav-hero-slot" onclick="openHeroesModal()"><img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/${imgName}.png" title="${hero.localized_name}"></div>`;
            }
        }
        container.innerHTML += slotHtml;
    }
}

function openHeroesModal() { renderHeroesGrid(); document.getElementById('hero-search').value = ''; document.getElementById('heroes-modal').classList.remove('hidden'); }
function closeHeroesModal() { document.getElementById('heroes-modal').classList.add('hidden'); }
function filterHeroes() { renderHeroesGrid(); }

function renderHeroesGrid() {
    const q = document.getElementById('hero-search').value.toLowerCase();
    document.getElementById('heroes-grid').innerHTML = allHeroes.filter(h => h.localized_name.toLowerCase().includes(q)).map(h => {
        const isSelected = selectedHeroes.includes(h.id);
        const imgName = h.name.replace('npc_dota_hero_', '');
        return `
            <div class="fav-hero-card ${isSelected ? 'selected' : ''}" onclick="toggleHero(${h.id})">
                <img src="https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/heroes/${imgName}.png">
                <div style="font-size: 0.75rem; color: #aaa; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${h.localized_name}</div>
            </div>`;
    }).join('');
}

function toggleHero(id) {
    if (selectedHeroes.includes(id)) { selectedHeroes = selectedHeroes.filter(hId => hId !== id); } 
    else { selectedHeroes.push(id); }
    renderHeroesGrid();
}

async function saveHeroes() {
    try {
        const res = await fetch('/api/favorites', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ user_id: currentUserSiteId, favorite_ids: selectedHeroes }) });
        if (res.ok) { renderFavSlots(); closeHeroesModal(); }
    } catch(e) { console.error(e); }
}
