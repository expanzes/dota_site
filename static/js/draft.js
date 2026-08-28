let heroesList = [];

async function loadHeroes() {
  try {
    const response = await fetch('/api/heroes');
    if (response.ok) {
      heroesList = await response.json();
      populateHeroesDatalist();
    }
  } catch (err) {
    console.error('Ошибка загрузки списка героев:', err);
  }
}

function populateHeroesDatalist() {
  const datalist = document.getElementById('heroes-list');
  if (!datalist) return;
  
  datalist.innerHTML = '';
  heroesList.forEach(hero => {
    const option = document.createElement('option');
    option.value = hero.name;
    datalist.appendChild(option);
  });
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
