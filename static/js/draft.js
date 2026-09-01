let heroesList = [];

async function loadHeroes() {
    try {
        const response = await fetch('/api/heroes');
        if (response.ok) {
            heroesList = await response.json();
            setupCustomAutocomplete();
        }
    } catch (e) { console.error("Ошибка загрузки героев", e); }
}

function setupCustomAutocomplete() {
    const inputs = document.querySelectorAll('.hero-slot input');
    inputs.forEach(input => {
        input.addEventListener('focus', () => renderDropdown(input));
        input.addEventListener('input', () => {
            renderDropdown(input);
            updateHeroSlotUI(input.id);
        });
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.hero-slot')) {
            document.querySelectorAll('.autocomplete-dropdown').forEach(d => d.remove());
        }
    });
}

function renderDropdown(input) {
    const wrapper = input.parentElement; // .hero-slot
    document.querySelectorAll('.autocomplete-dropdown').forEach(d => d.remove());
    
    const q = input.value.toLowerCase().trim();
    const filtered = q === "" 
        ? heroesList.slice(0, 15) 
        : heroesList.filter(h => 
            h.name.toLowerCase().includes(q) || 
            (h.aliases && h.aliases.some(a => a.toLowerCase().includes(q)))
          );
    
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
    const container = document.getElementById(`cont-${inputId}`);
    const img = document.getElementById(`img-${inputId}`);
    
    const hero = heroesList.find(h => h.name.toLowerCase() === input.value.toLowerCase());
    
    if (hero) {
        container.classList.add('filled');
        img.src = hero.img;
        img.style.display = 'block';
    } else {
        container.classList.remove('filled');
        img.src = '';
        img.style.display = 'none';
    }
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
    container.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:40px;">Анализ драфта...</p>';

    const savedUser = localStorage.getItem('dota_user');
    const user = savedUser ? JSON.parse(savedUser) : null;

    const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
            my_team: myTeam, 
            enemy_team: enemyTeam, 
            user_id: user ? user.site_id : null 
        })
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
        section.innerHTML = `<h3 style="border-left:4px solid var(--accent-red); padding-left:15px; margin-bottom:15px;">${item.role}</h3>`;
        
        const grid = document.createElement('div');
        grid.className = 'hero-cards-grid';
        
        item.data.others.forEach(h => {
            if(h) {
                const card = document.createElement('div');
                card.className = 'result-card';
                card.innerHTML = `<img src="${h.img}"><div><b>${h.name}</b></div><div style="color:var(--accent-green)">${h.winrate}% Win</div>`;
                grid.appendChild(card);
            }
        });
        section.appendChild(grid);
        container.appendChild(section);
    });
}

function clearInputs() {
    const inputs = document.querySelectorAll('.hero-slot input');
    inputs.forEach(i => {
        i.value = '';
        updateHeroSlotUI(i.id);
    });
    document.getElementById('results-container').innerHTML = '';
}

document.addEventListener('DOMContentLoaded', loadHeroes);
