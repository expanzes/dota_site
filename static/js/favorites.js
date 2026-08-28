let userFavorites = new Set();

async function loadUserFavorites() {
  if (!currentUser || !currentUser.user_id) return;

  try {
    const response = await fetch(`/api/favorites/${currentUser.user_id}`);
    if (response.ok) {
      const data = await response.json();
      userFavorites = new Set(data);
    }
  } catch (err) {
    console.error('Ошибка загрузки избранных героев:', err);
  }
}

function openFavModal() {
  document.getElementById('fav-modal').classList.remove('hidden');
  renderFavHeroes();
}

function closeFavModal() {
  document.getElementById('fav-modal').classList.add('hidden');
}

function renderFavHeroes() {
  const container = document.getElementById('fav-heroes-container');
  const search = document.getElementById('fav-search-input').value.toLowerCase();
  container.innerHTML = '';

  if (typeof heroesList === 'undefined' || heroesList.length === 0) {
    container.innerHTML = '<p style="color: var(--text-muted); text-align: center; grid-column: 1/-1;">Список героев пуст</p>';
    return;
  }

  const filtered = heroesList.filter(h => h.name.toLowerCase().includes(search));

  filtered.forEach(hero => {
    const isSelected = userFavorites.has(hero.name);
    const card = document.createElement('div');
    card.className = `fav-hero-card ${isSelected ? 'selected' : ''}`;
    card.innerHTML = `
      <img src="${hero.img}" alt="${hero.name}">
      <span>${hero.name}</span>
    `;
    card.onclick = () => {
      if (userFavorites.has(hero.name)) {
        userFavorites.delete(hero.name);
      } else {
        userFavorites.add(hero.name);
      }
      renderFavHeroes();
    };
    container.appendChild(card);
  });
}

function filterFavHeroes() {
  renderFavHeroes();
}

async function saveFavorites() {
  if (!currentUser || !currentUser.user_id) return;

  try {
    await fetch('/api/favorites', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUser.user_id,
        heroes: Array.from(userFavorites)
      })
    });
    closeFavModal();
  } catch (err) {
    alert('Не удалось сохранить список избранных героев');
  }
}
