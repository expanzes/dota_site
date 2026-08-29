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
  try {
    const response = await fetch('/api/heroes');
    if (response.ok) {
      heroesList = await response.json();
    }
  } catch (err) {
    console.error('Ошибка загрузки списка героев:', err);
  }
}

function setupCustomAutocomplete() {
  const inputIds = [
    'my-pos1', 'my-pos2', 'my-pos3', 'my-pos4', 'my-pos5',
    'enemy-1', 'enemy-2', 'enemy-3', 'enemy-4', 'enemy-5'
  ];

  inputIds.forEach(id => {
    const input = document.getElementById(id);
    if (!input) return;
    const wrapper = input.parentElement;
    input.addEventListener('focus', () => renderDropdown(input, wrapper));
    input.addEventListener('input', () => renderDropdown(input, wrapper));
    input.addEventListener('click', () => renderDropdown(input, wrapper));
  });

  document.addEventListener('click', (e) => {
    if (!e.target.closest('.autocomplete-wrapper')) {
      document.querySelectorAll('.autocomplete-dropdown').forEach(el => el.remove());
    }
  });
}

function matchHero(hero, query) {
  if (!query) return true;
  const q = query.toLowerCase().trim();
  const name = hero.name.toLowerCase();
  if (name.includes(q)) return true;
  const aliases = HERO_ALIASES[hero.name] || [];
  return aliases.some(alias => alias.toLowerCase().includes(q));
}

function renderDropdown(input, wrapper) {
  const oldDropdown = wrapper.querySelector('.autocomplete-dropdown');
  if (oldDropdown) oldDropdown.remove();

  if (!heroesList || heroesList.length === 0) return;

  const query = input.value;
  const filtered = heroesList.filter(h => matchHero(h, query));

  if (filtered.length === 0) return;

  const dropdown = document.createElement('div');
  dropdown.className = 'autocomplete-dropdown';

  filtered.slice(0, 15).forEach(hero => {
    const item = document.createElement('div');
    item.className = 'autocomplete-item';
    const aliases = HERO_ALIASES[hero.name] ? HERO_ALIASES[hero.name][0].toUpperCase() : '';

    item.innerHTML = `
      <img src="${hero.img}" alt="${hero.name}">
      <span class="hero-name">${hero.name}</span>
      ${aliases ? `<span class="hero-alias">${aliases}</span>` : ''}
    `;

    item.onmousedown = (e) => {
      e.preventDefault();
      input.value = hero.name;
      dropdown.remove();
    };
    dropdown.appendChild(item);
  });
  wrapper.appendChild(dropdown);
}

function clearSingleInput(inputId) {
  const input = document.getElementById(inputId);
  if (input) {
    input.value = '';
    input.dispatchEvent(new Event('input'));
  }
}

async function analyzeDraft() {
  const myTeam = {
    pos1: document.getElementById('my-pos1').value.trim(),
    pos2: document.getElementById('my-pos2').value.trim(),
    pos3: document.getElementById('my-pos3').value.trim(),
    pos4: document.getElementById('my-pos4').value.trim(),
    pos5: document.getElementById('my-pos5').value.trim()
  };

  const enemyTeam = [
    document.getElementById('enemy-1').value.trim(),
    document.getElementById('enemy-2').value.trim(),
    document.getElementById('enemy-3').value.trim(),
    document.getElementById('enemy-4').value.trim(),
    document.getElementById('enemy-5').value.trim()
  ].filter(name => name.length > 0);

  const resultsContainer = document.getElementById('results-container');
  resultsContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center;">Идет анализ...</p>';

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        my_team: myTeam,
        enemy_team: enemyTeam,
        user_id: (typeof currentUser !== 'undefined' && currentUser) ? currentUser.user_id : null
      })
    });

    if (!response.ok) {
      resultsContainer.innerHTML = '<p style="color: var(--accent-red); text-align: center;">Ошибка при анализе</p>';
      return;
    }

    const data = await response.json();
    renderResults(data.results);
  } catch (err) {
    resultsContainer.innerHTML = '<p style="color: var(--accent-red); text-align: center;">Ошибка соединения</p>';
  }
}

function renderResults(results) {
  const resultsContainer = document.getElementById('results-container');
  resultsContainer.innerHTML = '';

  if (!results || results.length === 0) {
    resultsContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center;">Все роли заполнены или нет данных.</p>';
    return;
  }

  results.forEach(item => {
    const groupDiv = document.createElement('div');
    groupDiv.className = 'results-section';

    const title = document.createElement('h3');
    title.className = 'role-group-title';
    title.innerText = item.role;
    groupDiv.appendChild(title);

    const topRow = document.createElement('div');
    topRow.className = 'top-picks-row';

    if (item.data.top_favorite) {
      topRow.appendChild(createTopPickCardHTML(item.data.top_favorite, 'favorite', 'Из вашего пула'));
    }
    if (item.data.top_winrate) {
      topRow.appendChild(createTopPickCardHTML(item.data.top_winrate, 'winrate', 'Самый высокий винрейт'));
    }
    groupDiv.appendChild(topRow);

    const others = item.data.others || [];
    if (others.length > 0) {
      const othersTitle = document.createElement('div');
      othersTitle.className = 'other-picks-title';
      othersTitle.innerText = 'Другие варианты на основе OpenDota';
      groupDiv.appendChild(othersTitle);

      const grid = document.createElement('div');
      grid.className = 'hero-cards-grid';
      others.filter(h => h !== null).forEach(hero => {
        grid.appendChild(createHeroCardHTML(hero));
      });
      groupDiv.appendChild(grid);
    }
    resultsContainer.appendChild(groupDiv);
  });
}

function createTopPickCardHTML(hero, type, label) {
  const card = document.createElement('div');
  card.className = `top-pick-card ${type}`;
  const advClass = hero.advantage >= 0 ? 'val-green' : 'accent-red';
  const advSign = hero.advantage >= 0 ? '+' : '';

  card.innerHTML = `
    <div class="top-pick-label">${label}</div>
    <img src="${hero.img}" alt="${hero.name}">
    <div class="top-pick-hero-name">${hero.name}</div>
    <div class="top-pick-hero-stats">
      Винрейт: <span class="val-green">${hero.winrate}%</span><br>
      Контрпик: <span class="${advClass}" style="font-weight: bold;">${advSign}${hero.advantage}%</span>
    </div>
  `;
  return card;
}

function createHeroCardHTML(hero) {
  const card = document.createElement('div');
  card.className = 'result-hero-card';
  const advClass = hero.advantage >= 0 ? 'val-green' : 'accent-red';
  const advSign = hero.advantage >= 0 ? '+' : '';

  card.innerHTML = `
    <img src="${hero.img}" alt="${hero.name}">
    <div class="hero-info">
      <span class="hero-name">${hero.name} <span class="${advClass}" style="font-size: 0.75rem;">${advSign}${hero.advantage}%</span></span>
      <span class="hero-stats">Итоговый WR: <span class="val-green">${hero.winrate}%</span></span>
    </div>
  `;
  return card;
}

function clearInputs() {
  const inputIds = [
    'my-pos1', 'my-pos2', 'my-pos3', 'my-pos4', 'my-pos5',
    'enemy-1', 'enemy-2', 'enemy-3', 'enemy-4', 'enemy-5'
  ];
  inputIds.forEach(id => clearSingleInput(id));
  document.getElementById('results-container').innerHTML = '';
}

document.addEventListener('DOMContentLoaded', () => {
  setupCustomAutocomplete();
  loadHeroes();
});
