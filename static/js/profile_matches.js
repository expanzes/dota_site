async function loadRecentMatches() {
    try {
        const res = await fetch('/api/recent-matches');
        const matches = await res.json();
        sessionStorage.setItem('dh_matches', JSON.stringify(matches));
        renderMatches(matches);
    } catch (e) { console.error(e); }
}

function renderMatches(matches) {
    const container = document.getElementById('matches-list');
    if (!matches || matches.length === 0) {
        container.innerHTML = '<div style="text-align: center; color: var(--text-muted); padding: 20px;">Нет данных о матчах.</div>';
        return;
    }
    container.innerHTML = matches.map(m => {
        const mins = Math.floor(m.duration / 60);
        const secs = (m.duration % 60).toString().padStart(2, '0');
        const nw = m.net_worth ? (m.net_worth / 1000).toFixed(1) + 'k' : '—';
        return `
        <div class="match-row">
            <div class="match-left">
                <img src="${m.hero_img || '/static/images/default_hero.png'}" class="match-hero-img" title="Герой">
                <div class="match-result ${m.is_win ? 'win' : 'loss'}">${m.is_win ? 'W' : 'L'}</div>
            </div>
            <div class="match-center">
                <span style="color:#fff;">${m.kills}</span>
                <span style="color:var(--text-muted); margin: 0 4px;">/</span>
                <span style="color:var(--accent-red);">${m.deaths}</span>
                <span style="color:var(--text-muted); margin: 0 4px;">/</span>
                <span style="color:#aaa;">${m.assists}</span>
            </div>
            <div class="match-right">
                <span class="match-networth"><i class="fas fa-coins"></i> ${nw}</span>
                <span><i class="far fa-clock"></i> ${mins}:${secs}</span>
            </div>
        </div>`;
    }).join('');
}
