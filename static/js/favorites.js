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
      allHeroesForFavorites.sort((a, b) => a.name.localeCompare(b.name));
    }

    if (typeof currentUser !== 'undefined' && currentUser && currentUser.user_id) {
      const favRes = await fetch(`/api/favorites?user_id=${currentUser.user_id}`);
      if (favRes.ok) {
        const favData = await favRes.json();
        const list = favData.favorite_ids || [];
        selectedFavoriteIds = new Set(list.map(Number));
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
    const heroId = Number(hero.id);
    const isSelected = selectedFavoriteIds.has(heroId);
    card.className = `fav-hero-card ${isSelected ? 'selected' : ''}`;
    card.dataset.id = heroId;

    card.innerHTML = `
      <img src="${hero.img}" alt="${hero.name}">
      <span>${hero.name}</span>
    `;

    card.onclick = () => {
      if (selectedFavoriteIds.has(heroId)) {
        selectedFavoriteIds.delete(heroId);
        card.classList.remove('selected');
      } else {
        selectedFavoriteIds.add(heroId);
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
        user_id: String(currentUser.user_id),
        favorite_ids: Array.from(selectedFavoriteIds).map(Number)
      })
    });

    if (response.ok) {
      closeFavModal();
      updateGlobalBanList(); // <-- ДОБАВЬ ЭТУ СТРОЧКУ
      if (typeof loadUserProfile === 'function') {
        loadUserProfile();
      }
    } else {
      const errDetails = await response.json().catch(() => ({}));
      console.error('Ошибка от сервера:', errDetails);
      alert('Не удалось сохранить изменения.');
    }
  } catch (err) {
    console.error('Ошибка сохранения любимых героев:', err);
  }
}

async function updateGlobalBanList() {
    const section = document.getElementById('personal-ban-section');
    const slotsContainer = document.getElementById('global-ban-slots');

    const user = currentUser || JSON.parse(localStorage.getItem('dota_user'));
    if (!user || !user.user_id) {
        section.classList.add('hidden');
        return;
    }

    try {
        const response = await fetch(`/api/global-bans?user_id=${user.user_id}`);
        if (!response.ok) return;

        const data = await response.json();
        const bans = data.bans || [];

        if (bans.length > 0) {
            section.classList.remove('hidden');
            slotsContainer.innerHTML = '';
            bans.forEach(hero => {
                const slot = document.createElement('div');
                slot.className = 'ban-slot active';
                slot.innerHTML = `<img src="${hero.img}" title="${hero.name}"><div class="ban-slot-label">BAN</div>`;
                slotsContainer.appendChild(slot);
            });
            for (let i = bans.length; i < 4; i++) {
                const empty = document.createElement('div');
                empty.className = 'ban-slot';
                slotsContainer.appendChild(empty);
            }
        }
    } catch (err) { console.error(err); }
}
