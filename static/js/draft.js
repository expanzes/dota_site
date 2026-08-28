let heroesList = [];

// База сокращений, сленга и русских названий
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
  "Centaur Warrunner": ["кентавр", "кентавр"],
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
      setupCustomAutocomplete();
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
  });

  // Закрываем меню при клике вне его
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

  // Прямое совпадение по имени
  if (name.includes(q)) return true;

  // Проверка псевдонимов и русских названий
  const aliases = HERO_ALIASES[hero.name] || [];
  return aliases.some(alias => alias.toLowerCase().includes(q));
}

function renderDropdown(input, wrapper) {
  // Удаляем старое меню
  const oldDropdown = wrapper.querySelector('.autocomplete-dropdown');
  if (oldDropdown) oldDropdown.remove();

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
  resultsContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center; grid-column: 1/-1;">Идет анализ...</p>';

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        my_team: myTeam,
        enemy_team: enemyTeam,
        user_id: typeof currentUser !== 'undefined' && currentUser ? currentUser.user_id : null
      })
    });

    if (!response.ok) {
      resultsContainer.innerHTML = '<p style="color: var(--accent-red); text-align: center; grid-column: 1/-1;">Ошибка при анализе драфта</p>';
      return;
    }

    const data = await response.json();
    renderResults(data.results);
  } catch (err) {
    resultsContainer.innerHTML = '<p style="color: var(--accent-red); text-align: center; grid-column: 1/-1;">Ошибка соединения с сервером</p>';
  }
}

function renderResults(results) {
  const resultsContainer = document.getElementById('results-container');
  resultsContainer.innerHTML = '';

  if (!results || results.length === 0) {
    resultsContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center; grid-column: 1/-1;">Все роли заполнены или нет данных для анализа.</p>';
    return;
  }

  results.forEach(item => {
    const card = document.createElement('div');
    card.style.background = 'var(--bg-card)';
    card.style.border = '1px solid var(--border-color)';
    card.style.borderRadius = '12px';
    card.style.padding = '16px';

    let html = `<h4 style="color: var(--accent-blue); margin-bottom: 12px; font-size: 1.1rem;">${item.role}</h4>`;

    if (item.data.top_winrate) {
      html += `
        <div style="display: flex; align-items: center; gap: 12px;">
          <img src="${item.data.top_winrate.img}" style="width: 50px; border-radius: 4px;" alt="${item.data.top_winrate.name}">
          <div>
            <div style="font-weight: bold; color: var(--text-main);">${item.data.top_winrate.name}</div>
            <div style="font-size: 0.85rem; color: var(--accent-green);">
              Винрейт: ${item.data.top_winrate.winrate}% (${item.data.top_winrate.games} игр)
            </div>
          </div>
        </div>
      `;
    }

    card.innerHTML = html;
    resultsContainer.appendChild(card);
  });
}

function clearInputs() {
  const inputIds = [
    'my-pos1', 'my-pos2', 'my-pos3', 'my-pos4', 'my-pos5',
    'enemy-1', 'enemy-2', 'enemy-3', 'enemy-4', 'enemy-5'
  ];
  
  inputIds.forEach(id => {
    const input = document.getElementById(id);
    if (input) input.value = '';
  });
  
  document.getElementById('results-container').innerHTML = '';
}
