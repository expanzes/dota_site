// Динамическая генерация полей ввода
const initInputs = () => {
    const allies = document.getElementById('allies-inputs');
    const enemies = document.getElementById('enemies-inputs');
    for(let i=1; i<=5; i++) {
        allies.innerHTML += `<div class="input-field-group"><label>Поз ${i}</label><div class="autocomplete-wrapper"><input type="text" id="my-pos${i}" placeholder="Герой..."><button onclick="clearSingleInput('my-pos${i}')">&times;</button></div></div>`;
        enemies.innerHTML += `<div class="input-field-group"><label>Враг ${i}</label><div class="autocomplete-wrapper"><input type="text" id="enemy-${i}" placeholder="Герой..."><button onclick="clearSingleInput('enemy-${i}')">&times;</button></div></div>`;
    }
};
async function analyzeDraft() {
    const my_team = {};
    for(let i=1; i<=5; i++) my_team[`pos${i}`] = document.getElementById(`my-pos${i}`).value;
    const enemy_team = [];
    for(let i=1; i<=5; i++) { const v = document.getElementById(`enemy-${i}`).value; if(v) enemy_team.push(v); }
    
    const res = await fetch('/api/analyze', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({my_team, enemy_team, user_id: currentUser?.user_id})
    });
    const data = await res.json();
    renderResults(data.results);
}
function renderResults(results) {
    const container = document.getElementById('results-container');
    container.innerHTML = "";
    results.forEach(item => {
        const section = document.createElement('div');
        section.className = 'results-section';
        section.innerHTML = `<h3 class="role-group-title">${item.role}</h3>`;
        const row = document.createElement('div');
        row.className = 'top-picks-row';
        if(item.data.top_favorite) row.innerHTML += createCard(item.data.top_favorite, 'favorite', 'Твой пул');
        if(item.data.top_winrate) row.innerHTML += createCard(item.data.top_winrate, 'winrate', 'Лучший WR');
        section.appendChild(row);
        container.appendChild(section);
    });
}
function createCard(h, type, label) {
    const cl = h.advantage >= 0 ? 'val-green' : 'accent-red';
    return `<div class="top-pick-card ${type}"><div class="top-pick-label">${label}</div><img src="${h.img}"><div class="top-pick-hero-name">${h.name}</div><div class="top-pick-hero-stats">WR: ${h.winrate}% <span class="${cl}">${h.advantage >= 0 ? '+':''}${h.advantage}%</span></div></div>`;
}
document.addEventListener('DOMContentLoaded', () => { initInputs(); setupCustomAutocomplete(); });
