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
let lastSpellName = ""; // Храним имя предыдущего скилла
let score = 0;

function startGame() {
    console.log("Инвокер: Тренировка запущена!");
    score = 0;
    const scoreEl = document.getElementById('score');
    if (scoreEl) scoreEl.innerText = score;
    nextSpell();
}

function nextSpell() {
    let next;
    // Цикл выбирает новый скилл, пока он совпадает с предыдущим
    do {
        next = INVOKER_SPELLS[Math.floor(Math.random() * INVOKER_SPELLS.length)];
    } while (next.name === lastSpellName);

    targetSpell = next;
    lastSpellName = next.name;

    const imgEl = document.getElementById('target-spell-img');
    const nameEl = document.getElementById('target-spell-name');
    
    if (imgEl) imgEl.src = targetSpell.img;
    if (nameEl) nameEl.innerText = targetSpell.name;
}

function updateOrbsUI() {
    for (let i = 0; i < 3; i++) {
        const orbEl = document.getElementById(`orb-${i}`);
        if (!orbEl) continue;
        
        orbEl.className = 'orb'; // Сброс
        const orbType = currentOrbs[i];
        
        if (orbType === 'Q') orbEl.classList.add('quas');
        else if (orbType === 'W') orbEl.classList.add('wex');
        else if (orbType === 'E') orbEl.classList.add('exort');
    }
}

function addOrb(type) {
    currentOrbs.push(type);
    if (currentOrbs.length > 3) {
        currentOrbs.shift();
    }
    updateOrbsUI();
}

function invoke() {
    if (!targetSpell) return;
    
    const currentCombo = [...currentOrbs].sort().join('');
    const targetCombo = targetSpell.keys.split('').sort().join('');

    const container = document.querySelector('.game-container');

    if (currentCombo === targetCombo) {
        score++;
        const scoreEl = document.getElementById('score');
        if (scoreEl) scoreEl.innerText = score;
        
        if (container) {
            container.style.boxShadow = "0 0 30px var(--accent-green)";
            setTimeout(() => container.style.boxShadow = "", 300);
        }
        nextSpell();
    } else {
        if (container) {
            container.style.boxShadow = "0 0 30px var(--accent-red)";
            setTimeout(() => container.style.boxShadow = "", 300);
        }
    }
}

// ОБРАБОТКА КЛАВИШ ЧЕРЕЗ e.code (физическое нажатие)
function handleKeyDown(e) {
    if (e.target.tagName === 'INPUT') return;

    const code = e.code; // KeyQ, KeyW, KeyE, KeyR и т.д.

    if (code === 'KeyQ') {
        addOrb('Q');
    } else if (code === 'KeyW') {
        addOrb('W');
    } else if (code === 'KeyE') {
        addOrb('E');
    } else if (code === 'KeyR') {
        invoke();
    }
}

// Принудительно вешаем слушатель
document.addEventListener('keydown', handleKeyDown);

// Инициализация
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startGame);
} else {
    startGame();
}
