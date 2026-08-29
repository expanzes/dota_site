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
  "Faceless Void": ["fv", "фв", "воид", "void", "купол"],
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
  "Zeus": ["зевс", "zuus"],
  "Lifestealer": ["ls", "лс", "гуля", "naix"],
  "Slark": ["сларк", "рыба"],
  "Juggernaut": ["джаггер", "юрнаеро"],
  "Morphling": ["морф", "вода"],
  "Sven": ["свен"],
  "Tiny": ["типи", "тинт"],
  "Axe": ["акс"],
  "Viper": ["вайпер"],
  "Venomancer": ["веномансер", "вено"],
  "Vengeful Spirit": ["венга"],
  "Slardar": ["селедка", "рыба", "слардар"],
  "Largo": ["лягушка", "бард", "батрахос", "ларго"],
  "Primal Beast": ["праймал", "динозавр", "бык"],
  "Lone Druid": ["мишка", "друид", "лд"],
  "Kez": ["кез", "птица", "петух"]
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
  const q = input.value.toLowerCase().trim();
  if (!q && input !== document.activeElement) return;

  const filtered = heroesList.filter(h => {
    const nameMatch = h.name.toLowerCase().includes(q);
    const aliasMatch = HERO_ALIASES[h.name] && HERO_ALIASES[h.name].some(a => a.toLowerCase().includes(q));
    return nameMatch || aliasMatch;
  });

  if (filtered.length === 0) return;

  d = document.createElement('div');
  d.className = 'autocomplete-dropdown';
  filtered.slice(0, 12).forEach(h => {
    const item = document.createElement('div');
    item.className = 'autocomplete-item';
    item.innerHTML = `<img src="${h.img}"><span>${h.name}</span>`;
    item.onmousedown = (e) => {
      e.preventDefault();
      input.value = h.name;
      d.remove();
    };
    d.appendChild(item);
  });
  wrapper.appendChild(d);
}

async function analyzeDraft() {
  const my_team = { 
    pos1: document.getElementById('my-pos1').value, 
    pos2: document.getElementById('my-pos2').value, 
    pos3: document.getElementById('my-pos3').value, 
    pos4: document.getElementById('my-pos4').value, 
    pos5: document.getElementById('my-pos5').value 
  };
  const enemy_team = [1,2,3,4,5].map(i => document.getElementById(`enemy-${i}`).value).filter(v => v);
  
  const resContainer = document.getElementById('results-container');
  resContainer.innerHTML = '<p style="text-align:center; color:var(--text-muted); padding:20px;">Идет глубокий анализ матчапов и синергии...</p>';

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST', 
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ my_team, enemy_team, user_id: currentUser?.user_id })
    });
    
    if (!res.ok) throw new Error();
    const data = await res.json();
    renderResults(data.results);
  } catch (err) {
    resContainer.innerHTML = '<p style="text-align:center; color:var(--accent-red);">Ошибка связи с сервером.</p>';
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
    
    // ОБНОВЛЕННЫЕ ЗАГОЛОВКИ ПЛАШЕК
    if (item.data.top_favorite) topRow.appendChild(createCard(item.data.top_favorite, 'favorite', 'ИЗ ВАШЕГО ПУЛА'));
    if (item.data.top_winrate) topRow.appendChild(createCard(item.data.top_winrate, 'winrate', 'ЛУЧШИЙ ВАРИАНТ'));
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
  div.innerHTML = `
    <div class="top-pick-label">${label}</div>
    <img src="${h.img}" alt="${h.name}">
    <div class="top-pick-hero-name">${h.name}</div>
    <div class="top-pick-hero-stats">
        Прогноз WR: <span class="val-green">${h.winrate}%</span><br>
        Контрпик: <span style="color:${advColor}">${h.advantage >= 0 ? '+':''}${h.advantage}%</span>
    </div>`;
  return div;
}

function createHeroSmallCard(h) {
  const div = document.createElement('div');
  div.className = 'result-hero-card';
  const advColor = h.advantage >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
  div.innerHTML = `
    <img src="${h.img}" alt="${h.name}">
    <div class="hero-info">
      <span class="hero-name">${h.name} <span style="color:${advColor}; font-size:0.75rem;">${h.advantage >= 0 ? '+':''}${h.advantage}%</span></span>
      <span class="hero-stats">Итоговый WR: ${h.winrate}%</span>
    </div>`;
  return div;
}

function clearInputs() {
  ['my-pos1','my-pos2','my-pos3','my-pos4','my-pos5','enemy-1','enemy-2','enemy-3','enemy-4','enemy-5'].forEach(id => document.getElementById(id).value = '');
  document.getElementById('results-container').innerHTML = '';
}
function clearSingleInput(id) { 
  const el = document.getElementById(id);
  if(el) { el.value = ''; el.focus(); }
}

document.addEventListener('DOMContentLoaded', () => {
  setupCustomAutocomplete();
  loadHeroes();
});
