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

// Соответствие позиций для фильтрации рекомендуемых героев
const HERO_POSITIONS = {
  "Anti-Mage": [1], "Phantom Assassin": [1], "Phantom Lancer": [1], "Terrorblade": [1], "Faceless Void": [1], "Slark": [1], "Juggernaut": [1], "Morphling": [1, 2], "Sven": [1], "Clinkz": [1, 2], "Naga Siren": [1], "Monkey King": [1, 2], "Lifestealer": [1], "Ursa": [1, 2, 3], "Bloodseeker": [1, 2], "Drow Ranger": [1], "Spectre": [1], "Medusa": [1], "Luna": [1], "Troll Warlord": [1], "Sniper": [1, 2], "Razor": [1, 2, 3],
  "Shadow Fiend": [2], "Queen of Pain": [2], "Outworld Destroyer": [2], "Ember Spirit": [2], "Storm Spirit": [2], "Void Spirit": [2], "Invoker": [2], "Tinker": [2], "Zeus": [2], "Puck": [2], "Templar Assassin": [2], "Lina": [2], "Pangolier": [2], "Dragon Knight": [2, 3], "Earth Spirit": [2, 4],
  "Centaur Warrunner": [3], "Bristleback": [3], "Axe": [3], "Mars": [3], "Tidehunter": [3], "Slardar": [3], "Underlord": [3], "Legion Commander": [3], "Doom": [3], "Dark Seer": [3], "Night Stalker": [3], "Primal Beast": [3], "Sand King": [3], "Timbersaw": [3], "Enigma": [3, 4], "Magnus": [3], "Beastmaster": [3], "Bane": [3, 5],
  "Crystal Maiden": [5], "Witch Doctor": [4, 5], "Ancient Apparition": [4, 5], "Rubick": [4], "Mirana": [4], "Bounty Hunter": [4], "Spirit Breaker": [4], "Earthshaker": [4], "Clockwerk": [4], "Pudge": [4], "Techies": [4], "Lion": [4, 5], "Shadow Shaman": [4, 5], "Ogre Magi": [4, 5], "Jakiro": [4, 5], "Dazzle": [5], "Oracle": [5], "Skywrath Mage": [4], "Vengeful Spirit": [4, 5], "Disruptor": [5], "Treant Protector": [5], "Keeper of the Light": [4, 5], "Silencer": [4, 5], "Chen": [5], "Enchantress": [4, 5], "Grimstroke": [4, 5], "Hoodwink": [4], "Snapfire": [4, 5]
};

function getPosNumber(roleName) {
  if (roleName.includes('Поз 1') || roleName.includes('Керри')) return 1;
  if (roleName.includes('Поз 2') || roleName.includes('Мид')) return 2;
  if (roleName.includes('Поз 3') || roleName.includes('Тройка')) return 3;
  if (roleName.includes('Поз 4') || roleName.includes('Четверка')) return 4;
  if (roleName.includes('Поз 5') || roleName.includes('Пятерка')) return 5;
  return null;
}

function isHeroFitForPos(heroName, posNum) {
  if (!posNum) return true;
  const allowed = HERO_POSITIONS[heroName];
  if (!allowed) return true;
  return allowed.includes(posNum);
}

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
        user_id: typeof currentUser !== 'undefined' && currentUser ? currentUser.user_id : null
      })
    });

    if (!response.ok) {
      resultsContainer.innerHTML = '<p style="color: var(--accent-red); text-align: center;">Ошибка при анализе драфта</p>';
      return;
    }

    const data = await response.json();
    renderResults(data.results);
  } catch (err) {
    resultsContainer.innerHTML = '<p style="color: var(--accent-red); text-align: center;">Ошибка соединения с сервером</p>';
  }
}

function renderResults(results) {
  const resultsContainer = document.getElementById('results-container');
  resultsContainer.innerHTML = '';

  if (!results || results.length === 0) {
    resultsContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center;">Все роли заполнены или нет данных для анализа.</p>';
    return;
  }

  const shownHeroNames = new Set();

  results.forEach(item => {
    const posNum = getPosNumber(item.role);

    const groupDiv = document.createElement('div');
    groupDiv.className = 'results-section';

    const title = document.createElement('h3');
    title.className = 'role-group-title';
    title.innerText = item.role;
    groupDiv.appendChild(title);

    // --- Топ-3 плашки (подиум): любимый / лучший винрейт / больше всего игр ---
    const topRow = document.createElement('div');
    topRow.className = 'top-picks-row';

    let topCardsAdded = 0;

    if (item.data.top_favorite && isHeroFitForPos(item.data.top_favorite.name, posNum) && !shownHeroNames.has(item.data.top_favorite.name)) {
      topRow.appendChild(createTopPickCardHTML(item.data.top_favorite, 'favorite', 'Из вашего пула'));
      shownHeroNames.add(item.data.top_favorite.name);
      topCardsAdded++;
    }

    if (item.data.top_winrate && isHeroFitForPos(item.data.top_winrate.name, posNum) && !shownHeroNames.has(item.data.top_winrate.name)) {
      topRow.appendChild(createTopPickCardHTML(item.data.top_winrate, 'winrate', 'Самый высокий винрейт'));
      shownHeroNames.add(item.data.top_winrate.name);
      topCardsAdded++;
    }

    if (item.data.top_games && isHeroFitForPos(item.data.top_games.name, posNum) && !shownHeroNames.has(item.data.top_games.name)) {
      topRow.appendChild(createTopPickCardHTML(item.data.top_games, 'games', 'Больше всего игр'));
      shownHeroNames.add(item.data.top_games.name);
      topCardsAdded++;
    }

    // Фолбэк, если после жёсткой фильтрации по позиции подиум пуст
    if (topCardsAdded === 0 && item.data.top_winrate) {
      topRow.appendChild(createTopPickCardHTML(item.data.top_winrate, 'winrate', 'Самый высокий винрейт'));
      topCardsAdded++;
    }

    if (topCardsAdded > 0) {
      groupDiv.appendChild(topRow);
    }

    // --- Остальные неплохие варианты ---
    const others = (item.data.others || []).filter(
      hero => isHeroFitForPos(hero.name, posNum) && !shownHeroNames.has(hero.name)
    );

    if (others.length > 0) {
      const othersTitle = document.createElement('div');
      othersTitle.className = 'other-picks-title';
      othersTitle.innerText = 'Другие варианты на основе OpenDota';
      groupDiv.appendChild(othersTitle);

      const grid = document.createElement('div');
      grid.className = 'hero-cards-grid';

      others.forEach(hero => {
        grid.appendChild(createHeroCardHTML(hero));
        shownHeroNames.add(hero.name);
      });

      groupDiv.appendChild(grid);
    }

    resultsContainer.appendChild(groupDiv);
  });
}

function createTopPickCardHTML(hero, type, label) {
  const card = document.createElement('div');
  card.className = `top-pick-card ${type}`;

  card.innerHTML = `
    <div class="top-pick-label">${label}</div>
    <img src="${hero.img}" alt="${hero.name}">
    <div class="top-pick-hero-name">${hero.name}</div>
    <div class="top-pick-hero-stats">Винрейт: <span class="val-green">${hero.winrate}%</span> (${hero.games} игр)</div>
  `;

  return card;
}

function createHeroCardHTML(hero) {
  const card = document.createElement('div');
  card.className = 'result-hero-card';

  const statsMarkup = `Винрейт: <span class="val-green">${hero.winrate}%</span> (${hero.games} игр)`;

  card.innerHTML = `
    <img src="${hero.img}" alt="${hero.name}">
    <div class="hero-info">
      <span class="hero-name">${hero.name}</span>
      <span class="hero-stats">${statsMarkup}</span>
    </div>
  `;

  return card;
}

function clearInputs() {
  const inputIds = [
    'my-pos1', 'my-pos2', 'my-pos3', 'my-pos4', 'my-pos5',
    'enemy-1', 'enemy-2', 'enemy-3', 'enemy-4', 'enemy-5'
  ];
  
  inputIds.forEach(id => {
    const input = document.getElementById(id);
    if (input) {
      input.value = '';
      input.dispatchEvent(new Event('input'));
    }
  });
  
  document.getElementById('results-container').innerHTML = '';
}

document.addEventListener('DOMContentLoaded', () => {
  setupCustomAutocomplete();
  loadHeroes();
});
