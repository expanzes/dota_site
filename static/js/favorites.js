let allHeroes = [];
let selectedFavoriteIds = new Set();

async function openFavModal() {
    const modal = document.getElementById('fav-modal');
    modal.classList.remove('hidden');
    
    // Загружаем список героев, если еще не загружен
    if (allHeroes.length === 0) {
        const res = await fetch('/api/heroes');
        allHeroes = await res.json();
    }

    // Загружаем текущие избранные с сервера
    if (currentUser) {
        const favRes = await fetch(`/api/favorites?user_id=${currentUser.user_id}`);
        const data = await favRes.json();
        selectedFavoriteIds = new Set(data.favorite_ids || []);
    }

    renderFavGrid();
}

function closeFavModal() {
    document.getElementById('fav-modal').classList.add('hidden');
}

function renderFavGrid(query = "") {
    const container = document.getElementById('fav-heroes-container');
    container.innerHTML = "";
    
    const q = query.toLowerCase().trim();

    const filtered = allHeroes.filter(h => h.name.toLowerCase().includes(q));

    filtered.forEach(h => {
        const card = document.createElement('div');
        const isSelected = selectedFavoriteIds.has(h.id);
        card.className = `fav-hero-card ${isSelected ? 'selected' : ''}`;
        
        card.innerHTML = `
            <img src="${h.img}" alt="${h.name}">
            <span>${h.name}</span>
        `;

        card.onclick = () => {
            if (selectedFavoriteIds.has(h.id)) {
                selectedFavoriteIds.delete(h.id);
                card.classList.remove('selected');
            } else {
                selectedFavoriteIds.add(h.id);
                card.classList.add('selected');
            }
        };

        container.appendChild(card);
    });
}

function filterFavHeroes() {
    const val = document.getElementById('fav-search-input').value;
    renderFavGrid(val);
}

async function saveFavorites() {
    if (!currentUser) return;

    const res = await fetch('/api/favorites', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            user_id: currentUser.user_id,
            favorite_ids: Array.from(selectedFavoriteIds)
        })
    });

    if (res.ok) {
        closeFavModal();
        alert("Список любимых героев обновлен!");
    }
}
