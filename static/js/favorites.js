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
    card.className =
