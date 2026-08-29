let heroesList = [];
const HERO_ALIASES = {
  "Anti-Mage": ["am", "ам", "антимаг"],
  "Shadow Fiend": ["sf", "сф", "невермор", "nevermore"],
  "Phantom Assassin": ["pa", "па", "фантомка"],
  "Phantom Lancer": ["pl", "пл", "лансер"],
  "Crystal Maiden": ["cm", "цм", "рилай"],
  "Queen of Pain": ["qop", "квопа"],
  "Wraith King": ["wk", "вк", "папич", "леорик", "leoric", "skeleton king"],
  "Nature's Prophet": ["np", "нп", "фурион", "furion"],
  "Outworld Destroyer": ["od", "од", "деструктор"],
  "Dragon Knight": ["dk", "дк", "рыцарь"],
  "Chaos Knight": ["ck", "цк", "хаос"],
  "Terrorblade": ["tb", "тб", "террор"],
  "Templar Assassin": ["ta", "та", "темплярка"],
  "Spirit Breaker": ["sb", "сб", "бара", "баратрум"],
  "Earthshaker": ["es", "шейкер", "shaker"],
  "Earth Spirit": ["земеля"],
  "Ember Spirit": ["эмбер"],
  "Storm Spirit": ["шторм"],
  "Faceless Void": ["fv", "фв", "воид", "void"],
  "Bloodseeker": ["bs", "бс", "сикер"],
  "Bounty Hunter": ["bh", "бх", "баунти"],
  "Windranger": ["wr", "вр", "виндраннер"],
  "Witch Doctor": ["wd", "вд", "доктор"],
  "Sand King": ["sk", "ск", "скорпион"],
  "Centaur Warrunner": ["кентавр"],
  "Bristleback": ["bb", "бб", "брист", "еж"],
  "Pudge": ["пудж", "мясо", "падж", "hook"],
  "Invoker": ["инвокер", "вокер", "каель"],
  "Mirana": ["potm", "потма", "мирана"],
  "Clockwerk": ["клок"],
  "Timbersaw": ["тимбер"],
  "Tinker": ["тинкер"],
  "Sniper": ["снайпер", "дед"],
  "Zeus": ["зевс"],
  "Lifestealer": ["ls", "лс", "гуля", "naix"],
  "Slark": ["сларк", "рыба"],
  "Juggernaut": ["джаггер", "юрнаеро"],
  "Morphling": ["морф", "вода"],
  "Sven": ["свен"],
  "Tiny": ["типи", "тинт"],
  "Axe": ["акс"],
  "Viper": ["вайпер"],
  "Venomancer": ["веномансер", "вено"],
  "Vengeful Spirit": ["венга"]
};

async function loadHeroes() {
  const res = await fetch('/api/heroes');
  if (res.ok) heroesList = await res.json();
}

function setupCustomAutocomplete() {
  const ids = ['my-pos1','my-pos2','my-pos3','my-pos4','my-pos5','enemy-1','enemy-2','enemy-3','enemy-4','enemy-5'];
  ids.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', () => renderDropdown(el, el.parentElement));
      el.addEventListener('focus', () => renderDropdown(el, el.parentElement));
    }
  });
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.autocomplete-wrapper')) document.querySelectorAll('.autocomplete-dropdown').forEach(d => d.remove());
  });
}

function renderDropdown(input, wrapper) {
  let d = wrapper.querySelector('.autocomplete-dropdown');
  if (d) d.remove();
  const q = input.value.toLowerCase();
  const filtered = heroesList.filter(h => h.name.toLowerCase().includes(q) || (HERO_ALIASES[h.name] && HERO_ALIASES[h.name].some(a => a.includes(q))));
  if (filtered.length === 0) return;
  d = document.createElement('div');
  d.className = 'autocomplete-dropdown';
  filtered.slice(0, 10).forEach(h => {
    const item = document.createElement('div');
    item.className = 'autocomplete-item';
    item.innerHTML = `<img src="${h.img}"><span>${h.name}</span>`;
    item.onmousedown = () => { input.value = h.name; d.remove(); };
    d.appendChild(item);
  });
  wrapper.appendChild(d);
}

async function analyzeDraft() {
  const my_team = { pos1: document.getElementById('my-pos1').value, pos2: document.getElementById('my-pos2').value, pos3: document.getElementById('my-pos3').value, pos4: document.getElementById('my-pos4').value, pos5: document.getElementById('my-pos5').value };
  const enemy_team = [1,2,3,4,5].map(i => document.getElementById(`enemy-${i}`).value).filter(v => v);
  const resContainer = document.getElementById('results-container');
  resContainer.innerHTML = '<p style="text-align:center; color:var(--text-muted);">Анализируем...</p>';
  const res = await fetch('/api/analyze', {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({ my_team, enemy_team, user_id: currentUser?.user_id })
  });
  const data = await res.json();
  renderResults(data.results);
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
    if (item.data.top_favorite) topRow.appendChild(createCard(item.data.top_favorite, 'favorite', 'Из пула'));
    if (item.data.top_winrate) topRow.appendChild(createCard(item.data.top_winrate, 'winrate', 'Лучший WR'));
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
  const advColor = h.advantage >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
  div.innerHTML = `<div class="top-pick-label">${label}</div><img src="${h.img}"><div class="top-pick-hero-name">${h.name}</div><div class="top-pick-hero-stats">WR: ${h.winrate}% <span style="color:${advColor}">${h.advantage >= 0 ? '+':''}${h.advantage}%</span></div>`;
  return div;
}

function createHeroSmallCard(h) {
  const div = document.createElement('div');
  div.className = 'result-hero-card';
  const advColor = h.advantage >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
  div.innerHTML = `<img src="${h.img}"><div class="hero-info"><span class="hero-name">${h.name} <span style="color:${advColor}; font-size:0.7rem;">${h.advantage >= 0 ? '+':''}${h.advantage}%</span></span><span class="hero-stats">Итоговый WR: ${h.winrate}%</span></div>`;
  return div;
}

function clearInputs() {
  ['my-pos1','my-pos2','my-pos3','my-pos4','my-pos5','enemy-1','enemy-2','enemy-3','enemy-4','enemy-5'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('results-container').innerHTML = '';
}
function clearSingleInput(id) { document.getElementById(id).value = ''; }

document.addEventListener('DOMContentLoaded', () => {
  setupCustomAutocomplete();
  loadHeroes();
});
