let heroesList = [];

async function loadHeroes() {
    try {
        const response = await fetch('/api/heroes');
        if (response.ok) {
            heroesList = await response.json();
            heroesList.sort((a, b) => a.name.localeCompare(b.name));
            setupCustomAutocomplete();
        }
    } catch (e) { console.error("Error loading heroes", e); }
}

function setupCustomAutocomplete() {
    document.querySelectorAll('.hero-slot input').forEach(input => {
        input.addEventListener('focus', () => renderDropdown(input));
        input.addEventListener('input', () => { renderDropdown(input); updateHeroSlotUI(input.id); });
    });
    document.addEventListener('click', (e) => { 
        if (!e.target.closest('.hero-slot')) {
            document.querySelectorAll('.autocomplete-dropdown').forEach(d => d.remove());
        }
    });
}

function renderDropdown(input) {
    const wrapper = input.parentElement;
    document.querySelectorAll('.autocomplete-dropdown').forEach(d => d.remove());
    
    const q = input.value.toLowerCase().trim();
    const filtered = q === "" 
        ? heroesList 
        : heroesList.filter(h => h.name.toLowerCase().includes(q) || 
          (h.aliases && h.aliases.some(a => a.toLowerCase().includes(q))));
    
    if (filtered.length === 0) return;

    const d = document.createElement('div');
    d.className = 'autocomplete-dropdown';
    
    filtered.forEach(h => {
        const item = document.createElement('div');
        item.className = 'autocomplete-item';
        item.innerHTML = `<img src="${h.img}"><span>${h.name}</span>`;
        item.onmousedown = (e) => {
            e.preventDefault();
            input.value = h.name;
            updateHeroSlotUI(input.id);
            d.remove();
        };
        d.appendChild(item);
    });
    wrapper.appendChild(d);
}

function updateHeroSlotUI(inputId) {
    const input = document.getElementById(inputId);
    const container = document.getElementById(`slot-container-${inputId}`);
    const img = document.getElementById(`img-${inputId}`);
    const hero = heroesList.find(h => h.name.toLowerCase() === input.value.toLowerCase());
    if (hero) { container.classList.add('filled'); img.src = hero.img; } 
    else { container.classList.remove('filled'); img.src = ''; }
}

async function analyzeDraft() {
    const myTeam = { 
        pos1: document.getElementById('my-pos1').value, 
        pos2: document.getElementById('my-pos2').value,
        pos3: document.getElementById('my-pos3').value, 
        pos4: document.getElementById('my-pos4').value, 
        pos5: document.getElementById('my-pos5').value 
    };
    const enemyTeam = [1,2,3,4,5].map(i => document.getElementById(`enemy-${i}`).value).filter(v => v.trim() !== "");
    
    const container = document.getElementById('results-container');
    container.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:60px; font-size:1.1rem;">Анализ текущей меты...</p>';

    const user = JSON.parse(localStorage.getItem('dota_user'));
    
    const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ my_team: myTeam, enemy_team: enemyTeam, user_id: user ? user.site_id : null })
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
        if (item.data.top_favorite) topRow.appendChild(createCard(item.data.top_favorite, 'favorite', 'ВАШ ПУЛ'));
        if (item.data.top_winrate) topRow.appendChild(createCard(item.data.top_winrate, 'winrate', 'ЛУЧШИЙ ВИНРЕЙТ'));
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
    const cl = h.advantage >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
    div.innerHTML = `
        <div class="top-pick-label">${label}</div>
        <img src="${h.img}">
        <div class="top-pick-hero-name">${h.name}</div>
        <div class="card-stats-grid">
            <div class="stat-box"><span class="stat-label">Winrate</span><span class="stat-value" style="color:var(--accent-green)">${h.winrate}%</span></div>
            <div style="width:1px; background:rgba(255,255,255,0.1)"></div>
            <div class="stat-box"><span class="stat-label">Advantage</span><span class="stat-value" style="color:${cl}">${h.advantage >= 0 ? '+' : ''}${h.advantage}%</span></div>
        </div>`;
    return div;
}

function createHeroSmallCard(h) {
    const div = document.createElement('div');
    div.className = 'result-hero-card';
    const cl = h.advantage >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
    div.innerHTML = `
        <img src="${h.img}">
        <div class="hero-info">
            <div style="font-weight:700; font-size:0.85rem; color:#fff;">${h.name}</div>
            <div style="font-size:0.75rem; color:var(--text-muted)">${h.winrate}% <span style="color:${cl}">${h.advantage >= 0 ? '+' : ''}${h.advantage}%</span></div>
        </div>`;
    return div;
}

function clearSingleInput(id) { 
    const el = document.getElementById(id); if (el) { el.value = ''; updateHeroSlotUI(id); } 
}

function clearInputs() { 
    document.querySelectorAll('.hero-slot input').forEach(input => { input.value = ''; updateHeroSlotUI(input.id); });
    document.getElementById('results-container').innerHTML = ''; 
}

document.addEventListener('DOMContentLoaded', loadHeroes);
