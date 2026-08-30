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
let lastSpellName = "";
let score = 0;
let timeLeft = 30;
let timerId = null;
let isGameActive = false;

function initApp() {
    document.getElementById('start-screen').classList.remove('hidden');
    document.getElementById('game-screen').classList.add('hidden');
    document.getElementById('result-screen').classList.add('hidden');
}

function startGame() {
    isGameActive = true;
    score = 0;
    timeLeft = 30;
    currentOrbs = [];
    
    document.getElementById('start-screen').classList.add('hidden');
    document.getElementById('result-screen').classList.add('hidden');
    document.getElementById('game-screen').classList.remove('hidden');
    
    document.getElementById('score-display').innerText = score;
    updateTimerUI();
    updateOrbsUI();
    nextSpell();

    timerId = setInterval(() => {
        timeLeft--;
        updateTimerUI();
        if (timeLeft <= 0) endGame();
    }, 1000);
}

function updateTimerUI() {
    const el = document.getElementById('timer');
    if (!el) return;
    el.innerText = timeLeft;
    if (timeLeft <= 5) el.classList.add('timer-low');
    else el.classList.remove('timer-low');
}

function nextSpell() {
    let next;
    do {
        next = INVOKER_SPELLS[Math.floor(Math.random() * INVOKER_SPELLS.length)];
    } while (next.name === lastSpellName);
    
    targetSpell = next;
    lastSpellName = next.name;
    document.getElementById('target-spell-img').src = targetSpell.img;
    document.getElementById('target-spell-name').innerText = targetSpell.name;
}

function addOrb(type) {
    if (!isGameActive) return;
    currentOrbs.push(type);
    if (currentOrbs.length > 3) currentOrbs.shift();
    updateOrbsUI();
}

function updateOrbsUI() {
    for (let i = 0; i < 3; i++) {
        const orbEl = document.getElementById(`orb-${i}`);
        if (!orbEl) continue;
        orbEl.className = 'orb';
        if (currentOrbs[i] === 'Q') orbEl.classList.add('quas');
        if (currentOrbs[i] === 'W') orbEl.classList.add('wex');
        if (currentOrbs[i] === 'E') orbEl.classList.add('exort');
    }
}

function invoke() {
    if (!isGameActive || !targetSpell) return;
    
    const cur = [...currentOrbs].sort().join('');
    const tar = targetSpell.keys.split('').sort().join('');
    const cont = document.querySelector('.game-container');

    if (cur === tar) {
        score++;
        document.getElementById('score-display').innerText = score;
        cont.style.boxShadow = "0 0 40px var(--accent-green)";
        setTimeout(() => cont.style.boxShadow = "", 200);
        nextSpell();
    } else {
        cont.style.boxShadow = "0 0 40px var(--accent-red)";
        setTimeout(() => cont.style.boxShadow = "", 200);
    }
}

async function endGame() {
    isGameActive = false;
    clearInterval(timerId);
    document.getElementById('game-screen').classList.add('hidden');
    document.getElementById('result-screen').classList.remove('hidden');
    document.getElementById('final-score').innerText = score;

    // Сохранение рекорда, если пользователь залогинен
    const savedUser = localStorage.getItem('dota_user');
    if (savedUser) {
        const user = JSON.parse(savedUser);
        await fetch('/api/save-invoker-score', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: user.username, score: score })
        });
    }
}

document.addEventListener('keydown', (e) => {
    if (e.target.tagName === 'INPUT') return;
    const code = e.code;
    if (code === 'KeyQ') addOrb('Q');
    else if (code === 'KeyW') addOrb('W');
    else if (code === 'KeyE') addOrb('E');
    else if (code === 'KeyR') invoke();
    else if (code === 'Enter' && !isGameActive) startGame();
});

window.onload = initApp;
