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

// НОВАЯ ЛОГИКА ОТРИСОВКИ РЕЗУЛЬТАТОВ
function renderResults(results) {
    const container = document.getElementById('results-container');
    container.innerHTML = '';
    
    if (!results || results.length === 0) {
        container.innerHTML = '<div style="color: var(--text-muted); text-align: center; padding: 20px;">Не удалось подобрать героев. Проверьте правильность введенных данных.</div>';
        return;
    }

    results.forEach(item => {
        const section = document.createElement('div');
        section.className = 'results-section';
        section.style.marginBottom = '30px';
        
        let cardsHtml = '';
        
        item.candidates.forEach(hero => {
            const advColor = hero.advantage > 0 ? 'var(--accent-green)' : 'var(--accent-red)';
            const advSign = hero.advantage > 0 ? '+' : '';
            
            // Компактный бейджик внутри карточки рядом с именем
            const favBadge = hero.is_favorite 
                ? `<span style="background: var(--accent-yellow); color: #000; font-size: 0.7rem; font-weight: 900; padding: 3px 8px; border-radius: 6px; margin-left: 10px; text-transform: uppercase; vertical-align: middle;"><i class="fas fa-star"></i> Любимый</span>` 
                : '';
            
            // Стилизация самой карточки (желтая рамка слева для любимого героя)
            const cardStyle = hero.is_favorite 
                ? 'border: 1px solid var(--accent-yellow); border-left: 4px solid var(--accent-yellow);' 
                : 'border: 1px solid var(--border-color); border-left: 4px solid transparent;';

            cardsHtml += `
                <div style="background: var(--bg-card); ${cardStyle} border-radius: 8px; margin-bottom: 12px; transition: 0.2s;">
                    <div style="display: flex; padding: 12px; gap: 15px; align-items: center;">
                        <img src="${hero.img}" style="width: 80px; height: 45px; object-fit: cover; border-radius: 6px; box-shadow: 0 4px 10px rgba(0,0,0,0.5);">
                        <div style="display: flex; flex-direction: column; justify-content: center; width: 100%;">
                            <div style="font-weight: 900; font-size: 1.1rem; margin-bottom: 5px; color: white; display: flex; align-items: center;">
                                ${hero.name} ${favBadge}
                            </div>
                            <div style="display: flex; justify-content: space-between; font-size: 0.85rem; font-weight: 700; color: var(--text-muted);">
                                <span>Винрейт: <span style="color: var(--accent-green);"><i class="fas fa-trophy"></i> ${hero.winrate.toFixed(1)}%</span></span>
                                <span>Контрпик: <span style="color: ${advColor};"><i class="fas fa-crosshairs"></i> ${advSign}${hero.advantage.toFixed(1)}%</span></span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });

        // Формируем заголовок роли
        section.innerHTML = `
            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 15px;">
                <div style="width: 4px; height: 20px; background: var(--accent-red); border-radius: 2px;"></div>
                <h3 style="color: white; font-weight: 900; font-size: 1.1rem; text-transform: uppercase; margin: 0;">${item.role}</h3>
            </div>
            ${cardsHtml}
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
