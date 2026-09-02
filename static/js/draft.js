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
    const wrapper = input.parentElement;
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
    container.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:40px; font-size:1.2rem;"><i class="fas fa-spinner fa-spin"></i> Анализируем миллионы матчей...</p>';

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

function buildCardHTML(hero, badgeText, badgeClass, cardTypeClass) {
    if (!hero) {
        return `
            <div class="result-card ${cardTypeClass} empty-card">
                <i class="fas fa-search" style="font-size: 1.5rem; margin-bottom:8px;"></i>
                <div>Нет данных<br><span style="font-size:0.75rem;">(или нет любимого героя)</span></div>
            </div>`;
    }

    const counterVal = hero.advantage.toFixed(1);
    const counterSign = hero.advantage > 0 ? '+' : '';
    const counterColorClass = hero.advantage >= 0 ? 'text-green' : 'text-red';

    return `
        <div class="result-card ${cardTypeClass}">
            <div class="card-left">
                <div class="card-badge ${badgeClass}">${badgeText}</div>
                <img src="${hero.img}" alt="${hero.name}">
            </div>
            <div class="card-right">
                <div class="hero-name">${hero.name}</div>
                <div class="stats-box">
                    <div class="stat-row">
                        <span>Винрейт:</span>
                        <span class="text-green"><i class="fas fa-trophy"></i> ${hero.winrate.toFixed(1)}%</span>
                    </div>
                    <div class="stat-row">
                        <span>Контрпик:</span>
                        <span class="${counterColorClass}"><i class="fas fa-crosshairs"></i> ${counterSign}${counterVal}%</span>
                    </div>
                </div>
            </div>
        </div>
    `;
}

function renderResults(results) {
    const container = document.getElementById('results-container');
    container.innerHTML = '';
    
    results.forEach(item => {
        const d = item.data;
        
        const topFavHTML = buildCardHTML(d.top_favorite, "★ Любимый герой", "badge-favorite", "main-card");
        const topWinHTML = buildCardHTML(d.top_winrate, "🔥 Топ Винрейт", "badge-top", "main-card");
        
        let altCardsHTML = '';
        d.others.forEach((hero) => {
            if (hero) {
                altCardsHTML += buildCardHTML(hero, "Хороший вариант", "badge-alt", "small-card");
            }
        });

        const section = document.createElement('div');
        section.className = 'results-section';
        section.innerHTML = `
            <h3 class="role-title">${item.role}</h3>
            
            <div class="top-picks-container">
                ${topFavHTML}
                ${topWinHTML}
            </div>
            
            <div class="alt-picks-container">
                ${altCardsHTML}
            </div>
        `;
        
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
