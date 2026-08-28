function renderResults(results) {
  const resultsContainer = document.getElementById('results-container');
  resultsContainer.innerHTML = '';

  if (!results || results.length === 0) {
    resultsContainer.innerHTML = '<p style="color: var(--text-muted); text-align: center; grid-column: 1/-1;">Все роли заполнены или нет данных для анализа.</p>';
    return;
  }

  results.forEach(item => {
    const groupDiv = document.createElement('div');
    groupDiv.className = 'results-section';

    const title = document.createElement('h3');
    title.className = 'role-group-title';
    title.innerText = item.role;
    groupDiv.appendChild(title);

    const grid = document.createElement('div');
    grid.className = 'hero-cards-grid';

    // 1. Топ из пула пользователя
    if (item.data.top_favorite) {
      grid.appendChild(createHeroCardHTML(item.data.top_favorite, 'badge-purple', '★ ИЗ ВАШЕГО ПУЛА'));
    }

    // 2. Максимальный винрейт
    if (item.data.top_winrate) {
      grid.appendChild(createHeroCardHTML(item.data.top_winrate, 'badge-yellow', '★ МАКС. ВИНРЕЙТ'));
    }

    // 3. Максимальное количество матчей
    if (item.data.top_games) {
      grid.appendChild(createHeroCardHTML(item.data.top_games, 'badge-blue', '📊 МАКС. МАТЧЕЙ', true));
    }

    // 4. Остальные рекомендации
    if (item.data.others) {
      item.data.others.forEach(hero => {
        grid.appendChild(createHeroCardHTML(hero));
      });
    }

    groupDiv.appendChild(grid);
    resultsContainer.appendChild(groupDiv);
  });
}

function createHeroCardHTML(hero, badgeClass = '', badgeText = '', prioritizeGames = false) {
  const card = document.createElement('div');
  card.className = `result-hero-card ${badgeClass}`;

  let badgeMarkup = '';
  if (badgeText) {
    badgeMarkup = `<div class="card-top-badge">${badgeText}</div>`;
  }

  let statsMarkup = '';
  if (prioritizeGames) {
    statsMarkup = `Матчей: ${hero.games} (<span class="val-green">${hero.winrate}% WR</span>)`;
  } else {
    statsMarkup = `Винрейт: <span class="val-green">${hero.winrate}%</span> (${hero.games} игр)`;
  }

  card.innerHTML = `
    ${badgeMarkup}
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
