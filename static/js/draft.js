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
        // Здесь важно, чтобы img был внутри item
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
    const container = input.parentElement;
    const img = container.querySelector('.slot-hero-img');
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
    container.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:60px;">Анализ Immortal-меты...</p>';

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
        section.innerHTML = `<h3 style="font-size:1.2rem; font-weight:900; color:#fff; margin-bottom:20px; padding-left:15px; border-left:4px solid var(--accent-red); text-transform:uppercase;">${item.role}</h3>`;
        
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
        <div style="font-size:0.6rem; font-weight:900; letter-spacing:2px; color:var(--text-muted); margin-bottom:10px;">${label}</div>
        <img src="${h.img}" style="width:140px; border-radius:10px; margin-bottom:10px;">
        <div style="font-size:1.3rem; font-weight:900; margin-bottom:10px;">${h.name}</div>
        <div style="display:flex; justify-content:center; gap:15px; background:rgba(0,0,0,0.2); padding:10px; border-radius:50px;">
            <div style="text-align:center;"><span style="font-size:0.6rem; color:var(--text-muted); display:block; text-transform:uppercase;">Winrate</span><span style="font-weight:900; color:var(--accent-green);">${h.winrate}%</span></div>
            <div style="width:1px; background:rgba(255,255,255,0.1)"></div>
            <div style="text-align:center;"><span style="font-size:0.6rem; color:var(--text-muted); display:block; text-transform:uppercase;">Advantage</span><span style="font-weight:900; color:${cl};">${h.advantage >= 0 ? '+' : ''}${h.advantage}%</span></div>
        </div>`;
    return div;
}

function createHeroSmallCard(h) {
    const div = document.createElement('div');
    div.className = 'result-hero-card';
    div.style = "background:#11141b; border:1px solid var(--border-color); border-radius:12px; padding:10px; display:flex; align-items:center; gap:12px;";
    const cl = h.advantage >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
    div.innerHTML = `
        <img src="${h.img}" style="width:60px; border-radius:4px;">
        <div>
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
