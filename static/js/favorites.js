let allHeroes = [];
let selectedFavoriteIds = new Set();
let isDataLoaded = false;

// Запускаем загрузку сразу при подключении скрипта
async function preloadFavoritesData() {
    try {
        const res = await fetch('/api/heroes');
        allHeroes = await res.json();
        allHeroes.sort((a, b) => a.name.localeCompare(b.name));
        
        const user = currentUser || JSON.parse(localStorage.getItem('dota_user'));
        if (user && user.site_id) {
            const favRes = await fetch(`/api/favorites?user_id=${user.site_id}`);
            const data = await favRes.json();
            selectedFavoriteIds = new Set(data.favorite_ids || []);
        }
        isDataLoaded = true;
        console.log("Данные героев предзагружены");
    } catch (e) {
        console.error("Ошибка предзагрузки:", e);
    }
}

async function openFavModal() {
    const modal = document.getElementById('fav-modal');
    if (modal) modal.classList.remove('hidden');
    
    // Если данные еще не успели загрузиться (редкий случай), ждем
    if (!isDataLoaded) {
        const container = document.getElementById('fav-heroes-container');
        if (container) container.innerHTML = "<p style='padding:20px; color:white;'>Загрузка героев...</p>";
        await preloadFavoritesData();
    }

    renderFavGrid();
}

function closeFavModal() {
    const modal = document.getElementById('fav-modal');
    if (modal) modal.classList.add('hidden');
}

function renderFavGrid(query = "") {
    const container = document.getElementById('fav-heroes-container');
    if (!container) return;
    
    container.innerHTML = "";
    const q = query.toLowerCase().trim();
    const filtered = allHeroes.filter(h => h.name.toLowerCase().includes(q));

    // Используем DocumentFragment для ускорения отрисовки 127 элементов
    const fragment = document.createDocumentFragment();

    filtered.forEach(h => {
        const card = document.createElement('div');
        const heroId = parseInt(h.id);
        const isSelected = selectedFavoriteIds.has(heroId);
        
        card.className = `fav-hero-card ${isSelected ? 'selected' : ''}`;
        card.innerHTML = `<img src="${h.img}" loading="lazy"><span>${h.name}</span>`;

        card.onclick = () => {
            if (selectedFavoriteIds.has(heroId)) {
                selectedFavoriteIds.delete(heroId);
                card.classList.remove('selected');
            } else {
                selectedFavoriteIds.add(heroId);
                card.classList.add('selected');
            }
        };
        fragment.appendChild(card);
    });

    container.appendChild(fragment);
}

function filterFavHeroes() {
    const input = document.getElementById('fav-search-input');
    if (input) renderFavGrid(input.value);
}

async function saveFavorites() {
    const user = currentUser || JSON.parse(localStorage.getItem('dota_user'));
    if (!user || !user.site_id) return;

    const saveBtn = document.querySelector('.btn-save') || document.querySelector('#fav-modal .btn-primary');
    if (saveBtn) { saveBtn.innerText = "СОХРАНЕНИЕ..."; saveBtn.disabled = true; }

    try {
        const response = await fetch('/api/favorites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: String(user.site_id),
                favorite_ids: Array.from(selectedFavoriteIds).map(Number)
            })
        });

        if (response.ok) {
            closeFavModal();
            if (typeof loadProfile === 'function') loadProfile();
        }
    } catch (err) {
        alert("Ошибка сети");
    } finally {
        if (saveBtn) { saveBtn.innerText = "СОХРАНИТЬ"; saveBtn.disabled = false; }
    }
}

// Инициализация при загрузке страницы
preloadFavoritesData();
