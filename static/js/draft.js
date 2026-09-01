let heroesList = [];

const ALLY_LABELS = ["Керри", "Мид", "Тройка", "Четверка", "Пятерка"];

const initDraftInputs = () => {
    const allies = document.getElementById('allies-inputs');
    const enemies = document.getElementById('enemies-inputs');
    if (!allies || !enemies) return;
    allies.innerHTML = ''; enemies.innerHTML = '';
    for(let i=1; i<=5; i++) {
        allies.innerHTML += createSlotHTML(`my-pos${i}`, ALLY_LABELS[i-1]);
        enemies.innerHTML += createSlotHTML(`enemy-${i}`, `ВРАГ ${i}`);
    }
    setupCustomAutocomplete();
};

function createSlotHTML(id, label) {
    return `<div class="input-field-group"><label>${label}</label><div class="hero-slot" id="slot-container-${id}"><img src="" class="slot-hero-img" id="img-${id}"><input type="text" id="${id}" placeholder="Выбрать..." autocomplete="off"><button type="button" class="clear-input-btn" onclick="clearSingleInput('${id}')">&times;</button></div></div>`;
}

async function loadHeroes() {
    const response = await fetch('/api/heroes');
    if (response.ok) { heroesList = await response.json(); initDraftInputs(); }
}

function updateHeroSlotUI(inputId) {
    const input = document.getElementById(inputId);
    const container = document.getElementById(`slot-container-${inputId}`);
    const img = document.getElementById(`img-${inputId}`);
    if(!input || !container || !img) return;
    const hero = heroesList.find(h => h.name.toLowerCase() === input.value.toLowerCase());
    if (hero) { container.classList.add('filled'); img.src = hero.img; } 
    else { container.classList.remove('filled'); img.src = ''; }
}

function setupCustomAutocomplete() {
    document.querySelectorAll('.hero-slot input').forEach(input => {
        input.addEventListener('focus', () => renderDropdown(input));
        input.addEventListener('input', () => { renderDropdown(input); updateHeroSlotUI(input.id); });
    });
    document.addEventListener('click', (e) => { if (!e.target.closest('.hero-slot')) document.querySelectorAll('.autocomplete-dropdown').forEach(d => d.remove()); });
}

function renderDropdown(input) {
    const wrapper = input.parentElement;
    document.querySelectorAll('.autocomplete-dropdown').forEach(d => d.remove());
    const q = input.value.toLowerCase().trim();
    const filtered = heroesList.filter(h => h.name.toLowerCase().includes(q));
    if (filtered.length === 0) return;
    const d = document.createElement('div');
    d.className = 'autocomplete-dropdown';
    filtered.slice(0, 10).forEach(h => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.innerHTML = `<img src="${h.img}"><span>${h.name}</span>`;
        item.onmousedown = (e) => { e.preventDefault(); input.value = h.name; updateHeroSlotUI(input.id); document.querySelectorAll('.autocomplete-dropdown').forEach(el => el.remove()); };
        d.appendChild(item);
    });
    wrapper.appendChild(d);
}

async function analyzeDraft() {
    const myTeam = { pos1: document.getElementById('my-pos1').value, pos2: document.getElementById('my-pos2').value, pos3: document.getElementById('my-pos3').value, pos4: document.getElementById('my-pos4').value, pos5: document.getElementById('my-pos5').value };
    const enemyTeam = [1,2,3,4,5].map(i => document.getElementById(`enemy-${i}`).value).filter(v => v.trim() !== "");
    const resContainer = document.getElementById('results-container');
    resContainer.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:40px;">Анализируем...</p>';
    
    const user = JSON.parse(localStorage.getItem('dota_user'));

    const response = await fetch('/api/analyze', { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify({ 
            my_team: myTeam, 
            enemy_team: enemyTeam, 
            user_id: user ? user.site_id : null 
        }) 
    });
    if (response.ok) { const data = await response.json(); renderResults(data.results); }
}

function renderResults(results) {
    const container = document.getElementById('results-container');
    container.innerHTML = '';
    results.forEach(item => {
        const section = document.createElement('div');
        section.className = 'results-section';
        section.innerHTML = `<h3 class="role-group-title">${item.role}</h3>`;
        const topRow = document.createElement('div');
        topRow.className = 'top-picks-row';
        if (item.data.top_favorite) topRow.appendChild(createCard(item.data.top_favorite, 'favorite', 'ИЗ ПУЛА'));
        if (item.data.top_winrate) topRow.appendChild(createCard(item.data.top_winrate, 'winrate', 'ЛУЧШИЙ WR'));
        section.appendChild(topRow);
        const grid = document.createElement('div');
        grid.className = 'hero-cards-grid';
        item.data.others.forEach(h => { if(h) grid.appendChild(createHeroSmallCard(h)); });
        section.appendChild(grid);
        container.appendChild(section);
    });
}

function createCard(h, type, label) {
    const div = document.createElement('div');
    div.className = `top-pick-card ${type}`;
    div.innerHTML = `<div class="top-pick-label">${label}</div><img src="${h.img}"><div class="hero-name">${h.name}</div><div>WR: ${h.winrate}%</div>`;
    return div;
}

function createHeroSmallCard(h) {
    const div = document.createElement('div');
    div.className = 'result-hero-card';
    div.innerHTML = `<img src="${h.img}"><div class="hero-name">${h.name}</div><div>${h.winrate}%</div>`;
    return div;
}

function clearSingleInput(id) { const el = document.getElementById(id); if (el) { el.value = ''; updateHeroSlotUI(id); } }
function clearInputs() { for(let i=1; i<=5; i++) { clearSingleInput(`my-pos${i}`); clearSingleInput(`enemy-${i}`); } document.getElementById('results-container').innerHTML = ''; }
document.addEventListener('DOMContentLoaded', () => { loadHeroes(); });
