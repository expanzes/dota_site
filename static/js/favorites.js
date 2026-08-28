let allHeroesForFavorites = [];
let selectedFavoriteIds = new Set();

// Алиас на случай, если в HTML используется openFavorites() или openFavoritesModal()
function openFavorites() {
  openFavoritesModal();
}

async function openFavoritesModal() {
  const modal = document.getElementById('favorites-modal') || document.getElementById('favoritesModal');
  if (modal) {
    modal.style.display = 'flex';
    modal.classList.add('active');
    modal.classList.add('show');
  } else {
    console.error('Модальное окно любимых героев не найдено в HTML (favorites-modal)');
  }
  await loadFavoritesModalData();
}

function closeFavoritesModal() {
  const modal = document.getElementById('favorites-modal') || document.getElementById('favoritesModal');
  if (modal) {
    modal.style.display = 'none';
    modal.classList.remove('active');
    modal.classList.remove('show');
  }
}

async function loadFavoritesModalData() {
  try {
    const heroesRes = await fetch('/api/heroes');
    if (heroesRes.ok) {
      allHeroesForFavorites = await heroesRes.json();
      
      // Сортировка героев строго по алфавиту (A–Z)
      allHeroesForFavorites.sort((a, b) => a.name.localeCompare(b.name));
    }

    if (typeof currentUser !== 'undefined' && currentUser && currentUser.user_id) {
      const favRes = await fetch(`/api/favorites?user_id=${currentUser.user_id}`);
      if (favRes.ok) {
        const favData = await favRes.json();
        selectedFavoriteIds = new Set(favData.favorite_ids || []);
      }
    }

    renderFavoritesGrid();
  } catch (err) {
    console.error('Ошибка при загрузке героев:', err);
  }
}

function renderFavoritesGrid(searchQuery = '') {
  const grid = document.getElementById('favorites-grid') || document.getElementById('favoritesGrid');
  if (!grid) return;

  grid.innerHTML = '';
  const q = searchQuery.toLowerCase().trim();

  const filtered = allHeroesForFavorites.filter(hero => {
    if (!q) return true;
    return hero.name.toLowerCase().includes(q);
  });

  filtered.forEach(hero => {
    const card = document.createElement('div');
    card.className = `favorite-hero-card ${selectedFavoriteIds.has(hero.id) ? 'selected' : ''}`;
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

    grid.appendChild(card);
  });
}

function filterFavoritesSearch() {
  const input = document.getElementById('favorites-search-input') || document.getElementById('favoritesSearchInput');
  const query = input ? input.value : '';
  renderFavoritesGrid(query);
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
      closeFavoritesModal();
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
