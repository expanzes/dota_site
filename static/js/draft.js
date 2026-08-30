let heroesList = [];

const HERO_ALIASES = {
  "Anti-Mage": ["am", "ам", "антимаг"],
  "Shadow Fiend": ["sf", "сф", "невермор", "nevermore"],
  "Phantom Assassin": ["pa", "па", "фантомка"],
  "Phantom Lancer": ["pl", "пл", "лансер"],
  "Crystal Maiden": ["cm", "цм", "рилай"],
  "Queen of Pain": ["qop", "квопа"],
  "Wraith King": ["wk", "вк", "папич", "leoric"],
  "Nature's Prophet": ["np", "фурион"],
  "Outworld Destroyer": ["od", "од"],
  "Dragon Knight": ["dk", "дк"],
  "Chaos Knight": ["ck", "цк"],
  "Terrorblade": ["tb", "тб"],
  "Templar Assassin": ["ta", "та"],
  "Spirit Breaker": ["sb", "бара"],
  "Earthshaker": ["es", "шейкер"],
  "Earth Spirit": ["земеля"],
  "Ember Spirit": ["эмбер"],
  "Storm Spirit": ["шторм"],
  "Faceless Void": ["fv", "воид", "купол"],
  "Bloodseeker": ["bs", "бс"],
  "Bounty Hunter": ["bh", "бх"],
  "Windranger": ["wr", "вр"],
  "Witch Doctor": ["wd", "вд"],
  "Sand King": ["sk", "ск"],
  "Centaur Warrunner": ["кентавр"],
  "Bristleback": ["bb", "брист"],
  "Pudge": ["пудж", "мясо"],
  "Invoker": ["инвокер", "вокер"],
  "Mirana": ["потма"],
  "Clockwerk": ["клок"],
  "Timbersaw": ["тимбер"],
  "Tinker": ["тинкер"],
  "Sniper": ["снайпер", "дед"],
  "Zeus": ["зевс", "zuus"],
  "Lifestealer": ["ls", "гуля"],
  "Slark": ["сларк", "рыба"],
  "Juggernaut": ["джаггер"],
  "Morphling": ["морф"],
  "Sven": ["свен"],
  "Tiny": ["тини"],
  "Axe": ["акс"],
  "Viper": ["вайпер"],
  "Slardar": ["селедка"],
  "Largo": ["лягушка", "ларго"],
  "Lone Druid": ["мишка", "лд"],
  "Kez": ["кез", "птица"]
};

const ALLY_LABELS = ["Керри", "Мид", "Тройка", "Четверка", "Пятерка"];

const initDraftInputs = () => {
    const allies = document.getElementById('allies-inputs');
    const enemies = document.getElementById('enemies-inputs');
    if (!allies || !enemies) return;

    allies.innerHTML = ''; enemies.innerHTML = '';

    for(let i=1; i<=5; i++) {
        allies.innerHTML += createSlotHTML(`my-pos${i}`, ALLY_LABELS[i-1]);
        enemies.innerHTML += createSlotHTML(`enemy-${i}`, `Враг ${i}`);
    }
    setupCustomAutocomplete();
};

function createSlotHTML(id, label) {
    return `
        <div class="input-field-group">
            <label>${label}</label>
            <div class="hero-slot" id="slot-container-${id}">
                <img src="" class="slot-hero-img" id="img-${id}">
                <div class="autocomplete-wrapper" style="flex:1">
                    <input type="text" id="${id}" placeholder="Выбрать..." autocomplete="off">
                    <button type="button" class="clear-input-btn" onclick="clearSingleInput('${id}')">&times;</button>
                </div>
            </div>
        </div>`;
}

async function loadHeroes() {
    const response = await fetch('/api/heroes');
    if (response.ok) {
        heroesList = await response.json();
        initDraftInputs();
    }
}

function updateHeroSlotUI(inputId) {
    const input = document.getElementById(inputId);
    const container = document.getElementById(`slot-container-${inputId}`);
    const img = document.getElementById(`img-${inputId}`);
    const hero = heroesList.find(h => h.name === input.value);

    if (hero) {
        container.classList.add('filled');
        img.src = hero.img;
    } else {
        container.classList.remove('filled');
        img.src = '';
    }
}

function setupCustomAutocomplete() {
    document.querySelectorAll('.hero-slot input').forEach(input => {
        input.addEventListener('focus', () => renderDropdown(input, input.parentElement));
        input.addEventListener('input', () => {
            renderDropdown(input, input.parentElement);
            updateHeroSlotUI(input.id);
        });
    });
}

function renderDropdown(input, wrapper) {
    const old = wrapper.querySelector('.autocomplete-dropdown');
    if (old) old.remove();

    const q = input.value.toLowerCase().trim();
    const filtered = heroesList.filter(h => {
        const nameMatch = h.name.toLowerCase().includes(q);
        const aliasMatch = HERO_ALIASES[h.name] && HERO_ALIASES[h.name].some(a => a.includes(q));
        return nameMatch || aliasMatch;
    });

    if (filtered.length === 0) return;

    const dropdown = document.createElement('div');
    dropdown.className = 'autocomplete-dropdown';
    filtered.slice(0, 10).forEach(hero => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.innerHTML = `<img src="${hero.img}" width="35" style="border-radius:3px;"><span>${hero.name}</span>`;
        item.onmousedown = (e) => {
            e.preventDefault();
            input.value = hero.name;
            updateHeroSlotUI(input.id);
            dropdown.remove();
            input.dispatchEvent(new Event('input'));
        };
        dropdown.appendChild(item);
    });
    wrapper.appendChild(dropdown);
}

async function analyzeDraft() {
    const myTeam = { pos1: document.getElementById('my-pos1').value, pos2: document.getElementById('my-pos2').value, pos3: document.getElementById('my-pos3').value, pos4: document.getElementById('my-pos4').value, pos5: document.getElementById('my-pos5').value };
    const enemyTeam = [1,2,3,4,5].map(i => document.getElementById(`enemy-${i}`).value).filter(v => v.trim() !== "");
    const resContainer = document.getElementById('results-container');
    resContainer.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:40px;">Глубокий анализ драфта...</p>';

    const response = await fetch('/api/analyze', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ my_team: myTeam, enemy_team: enemyTeam, user_id: currentUser ? currentUser.user_id : null })
    });
    if (response.ok) {
        const data = await response.json();
        renderResults(data.results);
    }
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
    div.innerHTML = `<div class="top-pick-label">${label}</div><img src="${h.img}"><div style="font-weight:bold;">${h.name}</div><div style="font-size:0.85rem; color:var(--text-muted);">Прогноз WR: <span class="val-green">${h.winrate}%</span><br>Контрпик: <span style="color:${cl}">${h.advantage >= 0 ? '+':''}${h.advantage}%</span></div>`;
    return div;
}

function createHeroSmallCard(h) {
    const div = document.createElement('div');
    div.className = 'result-hero-card';
    const cl = h.advantage >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
    div.innerHTML = `<img src="${h.img}"><div class="hero-info"><div style="font-size:0.95rem; font-weight:bold;">${h.name} <span style="color:${cl}; font-size:0.7rem;">${h.advantage >= 0 ? '+':''}${h.advantage}%</span></div><div style="font-size:0.8rem; color:var(--text-muted);">WR: ${h.winrate}%</div></div>`;
    return div;
}

function clearSingleInput(id) { 
    const el = document.getElementById(id);
    if (el) { el.value = ''; updateHeroSlotUI(id); el.dispatchEvent(new Event('input')); }
}

function clearInputs() {
    for(let i=1; i<=5; i++) {
        clearSingleInput(`my-pos${i}`);
        clearSingleInput(`enemy-${i}`);
    }
    document.getElementById('results-container').innerHTML = '';
}

document.addEventListener('DOMContentLoaded', () => { loadHeroes(); });
