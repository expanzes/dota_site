const INVOKER_SPELLS = [
    { name: "Cold Snap", keys: "QQQ", img: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/invoker_cold_snap.png" },
    { name: "Ghost Walk", keys: "QQW", img: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/invoker_ghost_walk.png" },
    { name: "Ice Wall", keys: "QQE", img: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/invoker_ice_wall.png" },
    { name: "EMP", keys: "WWW", img: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/invoker_emp.png" },
    { name: "Tornado", keys: "WWQ", img: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/invoker_tornado.png" },
    { name: "Alacrity", keys: "WWE", img: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/invoker_alacrity.png" },
    { name: "Sun Strike", keys: "EEE", img: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/invoker_sun_strike.png" },
    { name: "Forge Spirit", keys: "EEQ", img: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/invoker_forge_spirit.png" },
    { name: "Chaos Meteor", keys: "EEW", img: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/invoker_chaos_meteor.png" },
    { name: "Deafening Blast", keys: "QWE", img: "https://cdn.cloudflare.steamstatic.com/apps/dota2/images/dota_react/abilities/invoker_deafening_blast.png" }
];

let currentOrbs = [];
let targetSpell = null;
let score = 0;

function startGame() {
    console.log("Инвокер: Игра началась!");
    score = 0;
    const scoreEl = document.getElementById('score');
    if (scoreEl) scoreEl.innerText = score;
    nextSpell();
}

function nextSpell() {
    targetSpell = INVOKER_SPELLS[Math.floor(Math.random() * INVOKER_SPELLS.length)];
    const imgEl = document.getElementById('target-spell-img');
    const nameEl = document.getElementById('target-spell-name');
    
    if (imgEl) imgEl.src = targetSpell.img;
    if (nameEl) nameEl.innerText = targetSpell.name;
    console.log("Цель:", targetSpell.name, targetSpell.keys);
}

function updateOrbsUI() {
    for (let i = 0; i < 3; i++) {
        const orbEl = document.getElementById(`orb-${i}`);
        if (!orbEl) continue;
        
        orbEl.className = 'orb'; // Сброс классов
        const orbType = currentOrbs[i];
        
        if (orbType === 'Q') orbEl.classList.add('quas');
        else if (orbType === 'W') orbEl.classList.add('wex');
        else if (orbType === 'E') orbEl.classList.add('exort');
    }
}

function addOrb(type) {
    currentOrbs.push(type);
    if (currentOrbs.length > 3) {
        currentOrbs.shift(); // Оставляем только последние 3 сферы
    }
    updateOrbsUI();
}

function invoke() {
    if (!targetSpell) return;
    
    // Сортируем нажатые сферы и нужные для заклинания (порядок в Доте не важен)
    const currentCombo = [...currentOrbs].sort().join('');
    const targetCombo = targetSpell.keys.split('').sort().join('');

    const container = document.querySelector('.game-container');

    if (currentCombo === targetCombo) {
        score++;
        const scoreEl = document.getElementById('score');
        if (scoreEl) scoreEl.innerText = score;
        
        // Вспышка зеленым при успехе
        if (container) {
            container.style.boxShadow = "0 0 30px var(--accent-green)";
            setTimeout(() => container.style.boxShadow = "", 300);
        }
        nextSpell();
    } else {
        // Вспышка красным при ошибке
        if (container) {
            container.style.boxShadow = "0 0 30px var(--accent-red)";
            setTimeout(() => container.style.boxShadow = "", 300);
        }
    }
}

// Обработка клавиш
function handleKeyDown(e) {
    const key = e.key.toUpperCase();
    
    // Проверяем, что пользователь не пишет в каком-то поле ввода (если оно появится)
    if (e.target.tagName === 'INPUT') return;

    if (key === 'Q' || key === 'W' || key === 'E') {
        addOrb(key);
    } else if (key === 'R') {
        invoke();
    }
}

// Принудительная инициализация
document.addEventListener('keydown', handleKeyDown);

// Запуск игры после того, как всё дерево DOM построено
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startGame);
} else {
    startGame();
}
