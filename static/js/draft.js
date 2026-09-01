function createCard(h, type, label) {
    const div = document.createElement('div');
    div.className = `top-pick-card ${type}`;
    const cl = h.advantage >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
    const sign = h.advantage >= 0 ? '+' : '';
    
    div.innerHTML = `
        <div class="top-pick-label">${label}</div>
        <img src="${h.img}">
        <div class="top-pick-hero-name">${h.name}</div>
        <div class="card-stats-grid">
            <div class="stat-box">
                <span class="stat-label">Winrate</span>
                <span class="stat-value" style="color:var(--accent-green)">${h.winrate}%</span>
            </div>
            <div style="width: 1px; background: rgba(255,255,255,0.1); margin: 5px 0;"></div>
            <div class="stat-box">
                <span class="stat-label">Counter</span>
                <span class="stat-value" style="color:${cl}">${sign}${h.advantage}%</span>
            </div>
        </div>
    `;
    return div;
}

function createHeroSmallCard(h) {
    const div = document.createElement('div');
    div.className = 'result-hero-card';
    const cl = h.advantage >= 0 ? 'var(--accent-green)' : 'var(--accent-red)';
    div.innerHTML = `
        <img src="${h.img}">
        <div class="hero-info">
            <div style="font-weight:800; font-size:0.85rem; color:#fff; margin-bottom:2px;">${h.name}</div>
            <div style="font-size:0.7rem; font-family:'Montserrat'; font-weight:700;">
                <span style="color:var(--text-muted)">WR:</span> ${h.winrate}% 
                <span style="color:${cl}; margin-left:8px;">${h.advantage >= 0 ? '+' : ''}${h.advantage}%</span>
            </div>
        </div>`;
    return div;
}
