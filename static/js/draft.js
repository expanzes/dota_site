let heroesList = [];

const HERO_ALIASES = {
  "Anti-Mage": ["am", "антимаг"], "Shadow Fiend": ["sf", "сф", "невермор"],
  "Phantom Assassin": ["pa", "па", "фантомка"], "Phantom Lancer": ["pl", "пл"],
  "Wraith King": ["wk", "вк", "папич"], "Pudge": ["пудж", "мясо"], "Slardar": ["селедка"],
  "Largo": ["лягушка"], "Spirit Breaker": ["бара"], "Faceless Void": ["воид", "купол"],
  "Lone Druid": ["мишка", "друид", "лд"], "Kez": ["птица", "кез"]
};

const ALLY_LABELS = ["Поз 1 — Керри", "Поз 2 — Мид", "Поз 3 — Тройка", "Поз 4 — Четверка", "Поз 5 — Пятерка"];

const initDraftInputs = () => {
    const allies = document.getElementById('allies-inputs');
    const enemies = document.getElementById('enemies-inputs');
    if (!allies || !enemies) return;
    allies.innerHTML = ''; enemies.innerHTML = '';
    for(let i=1; i<=5; i++) {
        allies.innerHTML += `<div class="input-field-group"><label>${ALLY_LABELS[i-1]}</label><div class="autocomplete-wrapper"><input type="text" id="my-pos${i}" placeholder="Выберите героя..." autocomplete="off"><button type="button" class="clear-input-btn" onclick="clearSingleInput('my-pos${i}')">&times;</button></div></div>`;
        enemies.innerHTML += `<div class="input-field-group"><label>Враг ${i}</label><div class="autocomplete-wrapper"><input type="text" id="enemy-${i}" placeholder="Выберите героя..." autocomplete="off"><button type="button" class="clear-input-btn" onclick="clearSingleInput('enemy-${i}')">&times;</button></div></div>`;
    }
    setupCustomAutocomplete();
};

async function loadHeroes() {
    const response = await fetch('/api/heroes');
    if (response.ok) { heroesList = await response.json(); initDraftInputs(); }
}

function setupCustomAutocomplete() {
    document.querySelectorAll('.autocomplete-wrapper input').forEach(input => {
        input.addEventListener('focus', () => renderDropdown(input, input.parentElement));
        input.addEventListener('input', () => renderDropdown(input, input.parentElement));
    });
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.autocomplete-wrapper')) document.querySelectorAll('.autocomplete-dropdown').forEach(el => el.remove());
    });
}

function renderDropdown(input, wrapper) {
    const old = wrapper.querySelector('.autocomplete-dropdown');
    if (old) old.remove();
    const q = input.value.toLowerCase().trim();
    const filtered = heroesList.filter(h => h.name.toLowerCase().includes(q) || (HERO_ALIASES[h.name] && HERO_ALIASES[h.name].some(a => a.includes(q))));
    if (filtered.length === 0) return;
    const dropdown = document.createElement('div');
    dropdown.className = 'autocomplete-dropdown';
    filtered.slice(0, 12).forEach(hero => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.innerHTML = `<img src="${hero.img}"><span>${hero.name}</span>`;
        item.onmousedown = (e) => { e.preventDefault(); input.value = hero.name; dropdown.remove(); input.dispatchEvent(new Event('input')); };
        dropdown.appendChild(item);
    });
    wrapper.appendChild(dropdown);
}

async function analyzeDraft() {
    const myTeam = { pos1: document.getElementById('my-pos1').value, pos2: document.getElementById('my-pos2').value, pos3: document.getElementById('my-pos3').value, pos4: document.getElementById('my-pos4').value, pos5: document.getElementById('my-pos5').value };
    const enemyTeam = [1,2,3,4,5].map(i => document.getElementById(`enemy-${i}`).value).filter(v => v.trim() !== "");
    const resContainer = document.getElementById('results-container');
    resContainer.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:40px;">Анализируем...</p>';
    const response = await fetch('/api/analyze', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ my_team: myTeam, enemy_team: enemyTeam, user_id: currentUser ? currentUser.user_id : null }) });
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
        if (item.data.top_favorite) topRow.appendChild(createCard(item.data.top_favorite, 'favorite', 'ИЗ ВАШЕГО ПУЛА'));
        if (item.data.top_winrate) topRow.appendChild(createCard(item.data.top_winrate, 'winrate', 'ЛУЧШИЙ ВАРИАНТ'));
        section.appendChild(topRow);
        const grid = document.createElement('div');
        grid.className = 'hero-cards-grid';
        item.data.others.forEach(h => { if (h) grid.appendChild(createHeroSmallCard(h)); });
        section.appendChild(grid);
        container.appendChild(section);
    });
}

function createCard(h, type, label) {
    const div = document.createElement('div');
    div.className = `top-pick-card ${type}`;
    const cl = h.advantage >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
    div.innerHTML = `<div class="top-pick-label" style="font-size:0.7rem; font-weight:800; margin-bottom:12px;">${label}</div><img src="${h.img}"><div style="font-weight:bold;">${h.name}</div><div style="font-size:0.85rem; color:var(--text-muted);">WR: <span class="val-green">${h.winrate}%</span><br>Контрпик: <span style="color:${cl}">${h.advantage >= 0 ? '+':''}${h.advantage}%</span></div>`;
    return div;
}

function createHeroSmallCard(h) {
    const div = document.createElement('div');
    div.className = 'result-hero-card';
    const cl = h.advantage >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
    div.innerHTML = `<img src="${h.img}"><div class="hero-info"><div style="font-size:0.95rem; font-weight:bold;">${h.name} <span style="color:${cl}; font-size:0.7rem;">${h.advantage >= 0 ? '+':''}${h.advantage}%</span></div><div style="font-size:0.8rem; color:var(--text-muted);">WR: ${h.winrate}%</div></div>`;
    return div;
}

function clearSingleInput(id) { const el = document.getElementById(id); if (el) { el.value = ''; el.dispatchEvent(new Event('input')); } }
function clearInputs() { for(let i=1; i<=5; i++) { clearSingleInput(`my-pos${i}`); clearSingleInput(`enemy-${i}`); } document.getElementById('results-container').innerHTML = ''; }
document.addEventListener('DOMContentLoaded', () => { loadHeroes(); });
