let heroesList = [];

// ПОЛНЫЙ СПИСОК АЛИАСОВ (НИ ОДНОГО НЕ УДАЛЕНО)
const HERO_ALIASES = {
  "Anti-Mage": ["am", "ам", "антимаг"],
  "Shadow Fiend": ["sf", "сф", "невермор", "nevermore"],
  "Phantom Assassin": ["pa", "па", "фантомка"],
  "Phantom Lancer": ["pl", "пл", "лансер"],
  "Crystal Maiden": ["cm", "цм", "рилай"],
  "Queen of Pain": ["qop", "квопа"],
  "Wraith King": ["wk", "вк", "папич", "леорик", "leoric", "skeleton king"],
  "Nature's Prophet": ["np", "нп", "фурион", "furion"],
  "Outworld Destroyer": ["od", "од", "деструктор"],
  "Dragon Knight": ["dk", "дк", "рыцарь"],
  "Chaos Knight": ["ck", "цк", "хаос"],
  "Terrorblade": ["tb", "тб", "террор"],
  "Templar Assassin": ["ta", "та", "темплярка"],
  "Spirit Breaker": ["sb", "сб", "бара", "баратрум"],
  "Earthshaker": ["es", "шейкер", "shaker"],
  "Earth Spirit": ["земеля"],
  "Ember Spirit": ["эмбер"],
  "Storm Spirit": ["шторм"],
  "Faceless Void": ["fv", "фв", "воид", "void", "купол"],
  "Bloodseeker": ["bs", "бс", "сикер"],
  "Bounty Hunter": ["bh", "бх", "баунти"],
  "Windranger": ["wr", "вр", "виндраннер"],
  "Witch Doctor": ["wd", "вд", "доктор"],
  "Sand King": ["sk", "ск", "скорпион"],
  "Centaur Warrunner": ["кентавр"],
  "Bristleback": ["bb", "бб", "брист", "еж"],
  "Pudge": ["пудж", "мясо", "падж", "hook"],
  "Invoker": ["инвокер", "вокер", "каель"],
  "Mirana": ["potm", "потма", "мирана"],
  "Clockwerk": ["клок"],
  "Timbersaw": ["тимбер"],
  "Tinker": ["тинкер"],
  "Sniper": ["снайпер", "дед"],
  "Zeus": ["зевс", "zuus"],
  "Lifestealer": ["ls", "лс", "гуля", "naix"],
  "Slark": ["сларк", "рыба"],
  "Juggernaut": ["джаггер", "юрнаеро"],
  "Morphling": ["морф", "вода"],
  "Sven": ["свен"],
  "Tiny": ["типи", "тинт"],
  "Axe": ["акс"],
  "Viper": ["вайпер"],
  "Venomancer": ["веномансер", "вено"],
  "Vengeful Spirit": ["венга"],
  "Slardar": ["селедка", "рыба", "слардар"],
  "Largo": ["лягушка", "бард", "батрахос", "ларго"],
  "Primal Beast": ["праймал", "динозавр", "бык"],
  "Lone Druid": ["мишка", "друид", "лд"],
  "Kez": ["кез", "птица", "петух"]
};

const ALLY_LABELS = [
    "Поз 1 — Керри",
    "Поз 2 — Мид",
    "Поз 3 — Тройка",
    "Поз 4 — Четверка",
    "Поз 5 — Пятерка"
];

// Инициализация полей ввода (как на фото 2)
const initDraftInputs = () => {
    const allies = document.getElementById('allies-inputs');
    const enemies = document.getElementById('enemies-inputs');
    if (!allies || !enemies) return;

    allies.innerHTML = ''; 
    enemies.innerHTML = '';

    // Генерация Моей команды
    for(let i=1; i<=5; i++) {
        allies.innerHTML += `
            <div class="input-field-group">
                <label>${ALLY_LABELS[i-1]}</label>
                <div class="autocomplete-wrapper">
                    <input type="text" id="my-pos${i}" placeholder="Выберите героя..." autocomplete="off">
                    <button type="button" class="clear-input-btn" onclick="clearSingleInput('my-pos${i}')">&times;</button>
                </div>
            </div>`;
    }

    // Генерация Врагов
    for(let i=1; i<=5; i++) {
        enemies.innerHTML += `
            <div class="input-field-group">
                <label>Враг ${i}</label>
                <div class="autocomplete-wrapper">
                    <input type="text" id="enemy-${i}" placeholder="Выберите героя..." autocomplete="off">
                    <button type="button" class="clear-input-btn" onclick="clearSingleInput('enemy-${i}')">&times;</button>
                </div>
            </div>`;
    }
    setupCustomAutocomplete();
};

async function loadHeroes() {
    try {
        const response = await fetch('/api/heroes');
        if (response.ok) {
            heroesList = await response.json();
            initDraftInputs();
        }
    } catch (err) { console.error('Ошибка загрузки героев:', err); }
}

function setupCustomAutocomplete() {
    const inputs = document.querySelectorAll('.autocomplete-wrapper input');
    inputs.forEach(input => {
        input.addEventListener('focus', () => renderDropdown(input, input.parentElement));
        input.addEventListener('input', () => renderDropdown(input, input.parentElement));
    });

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.autocomplete-wrapper')) {
            document.querySelectorAll('.autocomplete-dropdown').forEach(el => el.remove());
        }
    });
}

function renderDropdown(input, wrapper) {
    const old = wrapper.querySelector('.autocomplete-dropdown');
    if (old) old.remove();

    const q = input.value.toLowerCase().trim();
    const filtered = heroesList.filter(h => {
        const nameMatch = h.name.toLowerCase().includes(q);
        const aliasMatch = HERO_ALIASES[h.name] && HERO
