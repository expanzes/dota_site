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
let isGameActive = false;

function startGame() {
    score = 0;
    isGameActive = true;
    document.getElementById('score').innerText = score;
    nextSpell();
}

function nextSpell() {
    targetSpell = INVOKER_SPELLS[Math.floor(Math.random() * INVOKER_SPELLS.length)];
    document.getElementById('target-spell-img').src = targetSpell.img;
    document.getElementById('target-spell-name').innerText = targetSpell.name;
}

function updateOrbsUI() {
    for (let i = 0; i < 3; i++) {
        const orbEl = document.getElementById(`orb-${i}`);
        orbEl.className = 'orb'; // Reset
        if (currentOrbs[i]) {
            if (currentOrbs[i] === 'Q') orbEl.classList.add('quas');
            if (currentOrbs[i] === 'W') orbEl.classList.add('wex');
            if (currentOrbs[i] === 'E') orbEl.classList.add('exort');
        }
    }
}

function addOrb(type) {
    currentOrbs.push(type);
    if (currentOrbs.length > 3) currentOrbs.shift();
    updateOrbsUI();
}

function invoke() {
    if (!targetSpell) return;
    
    // Сортируем нажатые клавиши и нужные клавиши, чтобы порядок не ролял (как в доте)
    const currentCombo = currentOrbs.slice().sort().join('');
    const targetCombo = targetSpell.keys.split('').sort().join('');

    if (currentCombo === targetCombo) {
        score++;
        document.getElementById('score').innerText = score;
        // Эффект успеха
        document.querySelector('.game-container').style.borderColor = 'var(--accent-green)';
        setTimeout(() => document.querySelector('.game-container').style.borderColor = 'var(--border-color)', 200);
        nextSpell();
    } else {
        // Эффект провала
        document.querySelector('.game-container').style.borderColor = 'var(--accent-red)';
        setTimeout(() => document.querySelector('.game-container').style.borderColor = 'var(--border-color)', 200);
    }
}

// Слушатель клавиатуры
document.addEventListener('keydown', (e) => {
    const key = e.key.toUpperCase();
    if (key === 'Q') addOrb('Q');
    if (key === 'W') addOrb('W');
    if (key === 'E') addOrb('E');
    if (key === 'R') invoke();
});

// Запуск при загрузке
window.onload = startGame;
