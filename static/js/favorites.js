let allHeroesForFavorites = [];
let selectedFavoriteIds = new Set();

async function openFavModal() {
  const modal = document.getElementById('fav-modal');
  if (modal) {
    modal.classList.remove('hidden');
    modal.style.display = 'flex';
  }
  await loadFavoritesModalData();
}

function closeFavModal() {
  const modal = document.getElementById('fav-modal');
  if (modal) {
    modal.classList.add('hidden');
    modal.style.display = 'none';
  }
}

async function loadFavoritesModalData() {
  try {
    const heroesRes = await fetch('/api/heroes');
    if (heroesRes.ok) {
      allHeroesForFavorites = await heroesRes.json();
      // Сортировка героев по алфавиту (A–Z)
      allHeroesForFavorites.sort((a, b) => a.name.localeCompare(b.name));
    }

    if (typeof currentUser !== 'undefined' && currentUser && currentUser.user_id) {
      const favRes = await fetch(`/api/favorites?user_id=${currentUser.user_id}`);
      if (favRes.ok) {
        const favData = await favRes.json();
        selectedFavoriteIds = new Set(favData.favorite_ids || []);
      }
    }

    renderFavGrid();
  } catch (err) {
    console.error('Ошибка при загрузке любимых героев:', err);
  }
}

function renderFavGrid(searchQuery = '') {
  const container = document.getElementById('fav-heroes-container');
  if (!container) return;

  container.innerHTML = '';
  const q = searchQuery.toLowerCase().trim();

  const filtered = allHeroesForFavorites.filter(hero => {
    if (!q) return true;
    return hero.name.toLowerCase().includes(q);
  });

  filtered.forEach(hero => {
    const card = document.createElement('div');
    const isSelected = selectedFavoriteIds.has(hero.id);
    card.className = `fav-hero-card ${isSelected ? 'selected' : ''}`;
    card.dataset.id = hero.id;

    card.innerHTML = `
      <img src="${hero.img}" alt="${hero.name}">
      <span>${hero.name}</span>
    `;

    card.onclick = () => {
      if (selectedFavoriteIds.has(hero.id)) {
        selectedFavoriteIds.delete(hero.id);
        card.classList.remove('selected');
      } else {
        selectedFavoriteIds.add(hero.id);
        card.classList.add('selected');
      }
    };

    container.appendChild(card);
  });
}

function filterFavHeroes() {
  const input = document.getElementById('fav-search-input');
  const query = input ? input.value : '';
  renderFavGrid(query);
}

async function saveFavorites() {
  if (typeof currentUser === 'undefined' || !currentUser || !currentUser.user_id) {
    alert('Пожалуйста, авторизуйтесь для сохранения любимых героев.');
    return;
  }

  try {
    const response = await fetch('/api/favorites', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_id: currentUser.user_id,
        favorite_ids: Array.from(selectedFavoriteIds)
      })
    });

    if (response.ok) {
      closeFavModal();
      if (typeof loadUserProfile === 'function') {
        loadUserProfile();
      }
    } else {
      alert('Не удалось сохранить изменения.');
    }
  } catch (err) {
    console.error('Ошибка сохранения любимых героев:', err);
  }
}
