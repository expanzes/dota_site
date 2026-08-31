let allHeroes = [];
let selectedFavoriteIds = new Set();

async function openFavModal() {
    const modal = document.getElementById('fav-modal');
    if (modal) modal.classList.remove('hidden');
    
    // 1. Загружаем всех героев, если еще не загружены
    if (allHeroes.length === 0) {
        try {
            const res = await fetch('/api/heroes');
            allHeroes = await res.json();
            // Сортируем по алфавиту для удобства
            allHeroes.sort((a, b) => a.name.localeCompare(b.name));
        } catch (e) {
            console.error("Не удалось загрузить список героев:", e);
        }
    }

    // 2. Берем текущего юзера из памяти или localStorage
    const user = currentUser || JSON.parse(localStorage.getItem('dota_user'));
    
    if (user && user.site_id) {
        try {
            // Запрашиваем текущее избранное с сервера по site_id
            const favRes = await fetch(`/api/favorites?user_id=${user.site_id}`);
            const data = await favRes.json();
            selectedFavoriteIds = new Set(data.favorite_ids || []);
        } catch (e) {
            console.error("Ошибка загрузки избранного:", e);
        }
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

    filtered.forEach(h => {
        const card = document.createElement('div');
        const heroId = parseInt(h.id);
        const isSelected = selectedFavoriteIds.has(heroId);
        
        card.className = `fav-hero-card ${isSelected ? 'selected' : ''}`;
        
        card.innerHTML = `
            <img src="${h.img}" alt="${h.name}">
            <span>${h.name}</span>
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
    if (input) renderFavGrid(input.value);
}

// ГЛАВНЫЙ ФИКС КНОПКИ СОХРАНИТЬ
async function saveFavorites() {
    // Берем актуального пользователя
    const user = currentUser || JSON.parse(localStorage.getItem('dota_user'));

    if (!user || !user.site_id) {
        alert("Пожалуйста, войдите в аккаунт, чтобы сохранить героев.");
        return;
    }

    const saveBtn = document.querySelector('.btn-save') || document.querySelector('#fav-modal .btn-primary');
    if (saveBtn) {
        saveBtn.innerText = "СОХРАНЕНИЕ...";
        saveBtn.disabled = true;
    }

    try {
        const response = await fetch('/api/favorites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_id: String(user.site_id), // Отправляем наш новый 10-значный ID
                favorite_ids: Array.from(selectedFavoriteIds).map(Number)
            })
        });

        if (response.ok) {
            closeFavModal();
            // Если мы в профиле, можно обновить интерфейс без перезагрузки
            if (typeof loadProfile === 'function') loadProfile();
        } else {
            const errData = await response.json();
            alert("Ошибка при сохранении: " + (errData.detail || "неизвестная ошибка"));
        }
    } catch (err) {
        console.error("Ошибка сети:", err);
        alert("Не удалось связаться с сервером");
    } finally {
        if (saveBtn) {
            saveBtn.innerText = "СОХРАНИТЬ";
            saveBtn.disabled = false;
        }
    }
}
