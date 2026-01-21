// Global state
let currentMatch = null;
let databaseData = [];

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    loadDatabase();
    setupEventListeners();
    setupScreenshotUpload();
    setupPlayerSearch();
    setupStatsSubtabs();
});

function escapeHtml(str) {
    if (str === null || str === undefined) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function renderLeaderBadgesHtml(player, maxBadges = null) {
    if (!player) return '';
    const badges = [];
    
    // Champions (rank #1)
    if (player.is_adr_champion) badges.push('<span class="leader-badge adr champion">ADR Champion</span>');
    if (player.is_kpr_champion) badges.push('<span class="leader-badge kpr champion">KPR Champion</span>');
    if (player.is_rating_champion) badges.push('<span class="leader-badge rating champion">Rating Champion</span>');
    if (player.is_kd_champion) badges.push('<span class="leader-badge kd champion">K/D Champion</span>');
    if (player.is_apr_champion) badges.push('<span class="leader-badge apr champion">APR Champion</span>');
    
    // Leaders (rank #2-5)
    if (player.is_adr_leader) badges.push('<span class="leader-badge adr leader">ADR Leader</span>');
    if (player.is_kpr_leader) badges.push('<span class="leader-badge kpr leader">KPR Leader</span>');
    if (player.is_rating_leader) badges.push('<span class="leader-badge rating leader">Rating Leader</span>');
    if (player.is_kd_leader) badges.push('<span class="leader-badge kd leader">K/D Leader</span>');
    if (player.is_apr_leader) badges.push('<span class="leader-badge apr leader">APR Leader</span>');
    
    // Cold Champions (worst rank #1)
    if (player.is_adr_cold_champion) badges.push('<span class="leader-badge adr cold-champion">ADR Cold</span>');
    if (player.is_kpr_cold_champion) badges.push('<span class="leader-badge kpr cold-champion">KPR Cold</span>');
    if (player.is_rating_cold_champion) badges.push('<span class="leader-badge rating cold-champion">Rating Cold</span>');
    if (player.is_kd_cold_champion) badges.push('<span class="leader-badge kd cold-champion">K/D Cold</span>');
    if (player.is_apr_cold_champion) badges.push('<span class="leader-badge apr cold-champion">APR Cold</span>');
    
    // Cold Leaders (worst rank #2-5)
    if (player.is_adr_cold_leader) badges.push('<span class="leader-badge adr cold-leader">ADR Cold</span>');
    if (player.is_kpr_cold_leader) badges.push('<span class="leader-badge kpr cold-leader">KPR Cold</span>');
    if (player.is_rating_cold_leader) badges.push('<span class="leader-badge rating cold-leader">Rating Cold</span>');
    if (player.is_kd_cold_leader) badges.push('<span class="leader-badge kd cold-leader">K/D Cold</span>');
    if (player.is_apr_cold_leader) badges.push('<span class="leader-badge apr cold-leader">APR Cold</span>');
    
    if (badges.length === 0) return '';
    
    // If maxBadges is specified and we have more badges, show overflow indicator
    if (maxBadges !== null && badges.length > maxBadges) {
        const visibleBadges = badges.slice(0, maxBadges);
        const remaining = badges.length - maxBadges;
        return `<div class="leader-badges has-overflow" data-remaining="+${remaining}">${visibleBadges.join('')}</div>`;
    }
    
    return `<div class="leader-badges">${badges.join('')}</div>`;
}

// Tab switching
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.dataset.tab;
            
            // Update buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update content
            tabContents.forEach(content => {
                content.classList.remove('active');
                if (content.id === `${targetTab}-tab`) {
                    content.classList.add('active');
                }
            });
            
            // Load player list when stats tab is opened
            if (targetTab === 'stats') {
                loadPlayerList();
                // Load map stats if map stats sub-tab is active
                const mapStatsSubtab = document.getElementById('map-stats-subtab');
                if (mapStatsSubtab && mapStatsSubtab.classList.contains('active')) {
                    loadMapStats();
                }
                // Load match history if match history sub-tab is active
                const matchHistorySubtab = document.getElementById('match-history-subtab');
                if (matchHistorySubtab && matchHistorySubtab.classList.contains('active')) {
                    loadAllMatchHistory();
                }
                // Load records if records sub-tab is active
                const recordsSubtab = document.getElementById('records-subtab');
                if (recordsSubtab && recordsSubtab.classList.contains('active')) {
                    loadRecords();
                }
            }
        });
    });
}

// Load database
async function loadDatabase() {
    try {
        const response = await fetch('/api/database');
        databaseData = await response.json();
        renderDatabaseTable(databaseData);
    } catch (error) {
        console.error('Error loading database:', error);
    }
}

// Render database table
function renderDatabaseTable(players) {
    const tbody = document.getElementById('database-tbody');
    tbody.innerHTML = '';
    
    players.forEach((player, index) => {
        const row = document.createElement('tr');
        
        // Determine streak display - only show streaks of 3 or more
        let streakDisplay = '';
        let playerNameClass = '';
        if (player.streak_type === 'win' && player.streak_count >= 3) {
            streakDisplay = `🔥 ${player.streak_count}`;
            row.classList.add('win-streak');
        } else if (player.streak_type === 'loss' && player.streak_count >= 3) {
            streakDisplay = `❄️ ${player.streak_count}`;
            playerNameClass = 'lose-streak-name';
            row.classList.add('lose-streak');
        }
        
        // Add rank position styling for top 3
        if (index < 3) {
            row.classList.add(`rank-${index + 1}`);
        }
        
        // Add top 3 highlighting classes for stats (rank 1, 2, or 3)
        const ratingClass = player.top3_rating_rank > 0 ? `top3-stat rank-${player.top3_rating_rank}` : '';
        const kdClass = player.top3_kd_rank > 0 ? `top3-stat rank-${player.top3_kd_rank}` : '';
        const kprClass = player.top3_kpr_rank > 0 ? `top3-stat rank-${player.top3_kpr_rank}` : '';
        const dprClass = player.top3_dpr_rank > 0 ? `top3-stat rank-${player.top3_dpr_rank}` : '';
        const aprClass = player.top3_apr_rank > 0 ? `top3-stat rank-${player.top3_apr_rank}` : '';
        const adrClass = player.top3_adr_rank > 0 ? `top3-stat rank-${player.top3_adr_rank}` : '';
        
        // Add online indicator
        const onlineIndicator = player.is_online ? '<span class="online-indicator" title="Online"></span>' : '';
        
        row.innerHTML = `
            <td class="player-cell ${playerNameClass}">
                <img src="${player.rank_icon}" alt="${player.rank}" class="rank-icon">
                ${onlineIndicator}
                <span class="player-name">${player.name}</span>
                ${streakDisplay ? `<span class="streak-badge">${streakDisplay}</span>` : ''}
            </td>
            <td class="number-cell elo-cell">${player.elo}</td>
            <td class="number-cell ${ratingClass}">${player.rating}</td>
            <td class="number-cell">${player.matches}</td>
            <td class="number-cell win-cell">${player.wins}</td>
            <td class="number-cell loss-cell">${player.losses}</td>
            <td class="number-cell ${kdClass}">${player.kd}</td>
            <td class="number-cell ${kprClass}">${player.kpr || '0.000'}</td>
            <td class="number-cell ${dprClass}">${player.dpr || '0.000'}</td>
            <td class="number-cell ${aprClass}">${player.apr || '0.000'}</td>
            <td class="number-cell ${adrClass}">${player.adr}</td>
        `;
        tbody.appendChild(row);
    });
}

// Setup screenshot upload
function setupScreenshotUpload() {
    const fileInput = document.getElementById('screenshot-file');
    const processBtn = document.getElementById('process-screenshot-btn');
    const statusDiv = document.getElementById('ocr-status');
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            processBtn.disabled = false;
            statusDiv.style.display = 'none';
        } else {
            processBtn.disabled = true;
        }
    });
    
    processBtn.addEventListener('click', async () => {
        const file = fileInput.files[0];
        if (!file) return;
        
        const formData = new FormData();
        formData.append('file', file);
        
        statusDiv.className = 'ocr-status info';
        statusDiv.textContent = 'Processing screenshot...';
        statusDiv.style.display = 'block';
        processBtn.disabled = true;
        
        try {
            const response = await fetch('/api/upload-screenshot', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.error) {
                statusDiv.className = 'ocr-status error';
                statusDiv.textContent = `Error: ${data.error}`;
                processBtn.disabled = false;
                return;
            }
            
            if (data.success && data.players && data.players.length > 0) {
                // Fill in the result tables with extracted stats
                fillResultsFromOCR(data.players);
                
                statusDiv.className = 'ocr-status success';
                statusDiv.textContent = `Successfully extracted stats for ${data.players.length} players! Please review and adjust if needed.`;
                
                // Show results container if hidden
                document.getElementById('results-container').style.display = 'grid';
            } else {
                statusDiv.className = 'ocr-status error';
                let errorMsg = data.message || 'Could not extract player stats.';
                if (data.raw_text && data.raw_text.length > 0) {
                    errorMsg += `\n\nOCR detected ${data.total_text_lines} text lines.`;
                    errorMsg += `\nFirst few lines: ${data.raw_text.slice(0, 5).join(', ')}`;
                    errorMsg += '\n\nPlease check:';
                    errorMsg += '\n1. Screenshot shows full stats table';
                    errorMsg += '\n2. Player names match database exactly';
                    errorMsg += '\n3. Text is clear and readable';
                }
                statusDiv.textContent = errorMsg;
                statusDiv.style.whiteSpace = 'pre-line';
            }
            
            processBtn.disabled = false;
        } catch (error) {
            statusDiv.className = 'ocr-status error';
            statusDiv.textContent = `Error: ${error.message}`;
            processBtn.disabled = false;
        }
    });
}

// Fill result tables from OCR data
function fillResultsFromOCR(players) {
    // Get current team players from the match
    if (!currentMatch) return;
    
    const team1Names = currentMatch.team_1.map(p => p.name);
    const team2Names = currentMatch.team_2.map(p => p.name);
    
    // Fill team 1 results
    const result1Tbody = document.getElementById('result-1-tbody');
    const result1Rows = result1Tbody.querySelectorAll('tr');
    result1Rows.forEach(row => {
        const nameInput = row.querySelector('input[data-stat="K"]');
        const playerName = nameInput.dataset.name;
        
        const ocrPlayer = players.find(p => p.name.toLowerCase() === playerName.toLowerCase());
        if (ocrPlayer) {
            row.querySelector('input[data-stat="K"]').value = ocrPlayer.k;
            row.querySelector('input[data-stat="D"]').value = ocrPlayer.d;
            row.querySelector('input[data-stat="A"]').value = ocrPlayer.a;
            row.querySelector('input[data-stat="ADR"]').value = ocrPlayer.adr;
            row.querySelector('input[data-stat="MVP"]').value = ocrPlayer.mvp;
        }
    });
    
    // Fill team 2 results
    const result2Tbody = document.getElementById('result-2-tbody');
    const result2Rows = result2Tbody.querySelectorAll('tr');
    result2Rows.forEach(row => {
        const nameInput = row.querySelector('input[data-stat="K"]');
        const playerName = nameInput.dataset.name;
        
        const ocrPlayer = players.find(p => p.name.toLowerCase() === playerName.toLowerCase());
        if (ocrPlayer) {
            row.querySelector('input[data-stat="K"]').value = ocrPlayer.k;
            row.querySelector('input[data-stat="D"]').value = ocrPlayer.d;
            row.querySelector('input[data-stat="A"]').value = ocrPlayer.a;
            row.querySelector('input[data-stat="ADR"]').value = ocrPlayer.adr;
            row.querySelector('input[data-stat="MVP"]').value = ocrPlayer.mvp;
        }
    });
}

// Setup event listeners
function setupEventListeners() {
    // Auto-update online players every hour
    async function updateOnlinePlayers() {
        try {
            const response = await fetch('/api/update-online-players', { method: 'GET' });
            const data = await response.json();
            if (data.success) {
                updateTop3(data.top_3);
                // Reload database to update online indicators
                await loadDatabase();
                console.log('Online players updated automatically');
            }
        } catch (error) {
            console.error('Error updating online players:', error);
        }
    }
    
    // Update online players immediately on load
    updateOnlinePlayers();
    
    // Set up automatic updates every hour (3600000 milliseconds)
    setInterval(updateOnlinePlayers, 3600000);
    
    // Create game
    document.getElementById('create-game-btn').addEventListener('click', async () => {
        // Get online players from the table (players with online indicator)
        const onlinePlayers = Array.from(document.querySelectorAll('.online-indicator'))
            .map(indicator => {
                const playerCell = indicator.closest('.player-cell');
                const playerNameSpan = playerCell.querySelector('.player-name');
                return playerNameSpan ? playerNameSpan.textContent.trim() : null;
            })
            .filter(name => name !== null);
        
        if (onlinePlayers.length < 10) {
            alert('Not enough online players. Please wait for the automatic update.');
            return;
        }
        
        const onlineList = onlinePlayers;
        
        if (onlineList.length < 10) {
            alert('Need at least 10 online players to create a match');
            return;
        }
        
        try {
            const response = await fetch('/api/create-match', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ online_players: onlineList })
            });
            
            if (!response.ok) {
                const error = await response.json();
                alert(error.error || 'Error creating match');
                return;
            }
            
            currentMatch = await response.json();
            renderMatch(currentMatch);
            document.getElementById('submit-match-btn').disabled = false;
            document.getElementById('save-match-btn').disabled = false;
        } catch (error) {
            console.error('Error creating match:', error);
            alert('Error creating match');
        }
    });
    
    // Submit match
    document.getElementById('submit-match-btn').addEventListener('click', async () => {
        if (!currentMatch) return;
        
        const result1 = getResultData('result-1-tbody');
        const result2 = getResultData('result-2-tbody');
        const winTeam = document.getElementById('win-team').value;
        const team1Score = parseInt(document.getElementById('team1-score').value) || 16;
        const team2Score = parseInt(document.getElementById('team2-score').value) || 14;
        
        // Validate
        if (!validateResults(result1, result2)) {
            alert('Please fill in all match results');
            return;
        }
        
        if (team1Score < 0 || team1Score > 30 || team2Score < 0 || team2Score > 30) {
            alert('Match scores must be between 0 and 30');
            return;
        }
        
        try {
            const response = await fetch('/api/submit-match', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    team_1_result: result1,
                    team_2_result: result2,
                    t1_gain: currentMatch.t1_gain,
                    t2_gain: currentMatch.t2_gain,
                    win_team: winTeam,
                    team1_score: team1Score,
                    team2_score: team2Score,
                    map: currentMatch.map
                })
            });
            
            const data = await response.json();
            if (data.success) {
                updateTop3(data.top_3);
                await loadDatabase();
                alert('Match submitted successfully!');
                resetMatch();
            }
        } catch (error) {
            console.error('Error submitting match:', error);
            alert('Error submitting match');
        }
    });
    
    // Save match
    document.getElementById('save-match-btn').addEventListener('click', () => {
        if (!currentMatch) return;
        
        const result1 = getResultData('result-1-tbody');
        const result2 = getResultData('result-2-tbody');
        
        // This is handled server-side when submitting
        alert('Match will be saved when you submit it');
    });
}

// Render match
function renderMatch(match) {
    // Show match setup
    document.getElementById('match-setup').style.display = 'block';
    
    // Update match info
    document.getElementById('map-name').textContent = match.map;
    document.getElementById('elo-diff').textContent = match.elo_diff;
    document.getElementById('t1-gain').textContent = match.t1_gain;
    document.getElementById('t2-gain').textContent = match.t2_gain;
    
    // Render teams as cards
    renderTeam('team-1-cards', match.team_1);
    renderTeam('team-2-cards', match.team_2);
    
    // Initialize results tables
    initializeResults('result-1-tbody', match.team_1);
    initializeResults('result-2-tbody', match.team_2);
    
    // Show results container
    document.getElementById('results-container').style.display = 'grid';
    
    // Show command
    document.getElementById('command-box').style.display = 'block';
    document.getElementById('command-text').value = match.command;
    
    // Show screenshot upload
    document.getElementById('screenshot-upload').style.display = 'block';
}

// Render team cards (Faceit style)
function renderTeam(cardsId, team) {
    const container = document.getElementById(cardsId);
    container.innerHTML = '';
    
    team.forEach(player => {
        // Determine streak display - only show streaks of 3 or more
        let streakDisplay = '';
        if (player.streak_type === 'win' && player.streak_count >= 3) {
            streakDisplay = `🔥 ${player.streak_count}`;
        } else if (player.streak_type === 'loss' && player.streak_count >= 3) {
            streakDisplay = `❄️ ${player.streak_count}`;
        }
        
        // Check if player is top 10 (rank 10 or above)
        const isTop10 = player.rank && player.rank <= 10;
        
        const card = document.createElement('div');
        card.className = `player-card ${isTop10 ? 'top-10-player' : ''}`;
        card.innerHTML = `
            <div class="player-card-left">
                <img src="${player.rank_icon}" alt="rank" class="player-card-rank">
                <div class="player-card-name-container">
                    <span class="player-card-name">
                        ${player.name}
                        ${streakDisplay ? `<span class="player-card-streak">${streakDisplay}</span>` : ''}
                        ${renderLeaderBadgesHtml(player, 3)}
                    </span>
                    <span class="player-card-rank-text">Rank #${player.rank || 'N/A'}</span>
                </div>
            </div>
            <div class="player-card-stats">
                <div class="player-stat">
                    <span class="player-stat-label">K/D</span>
                    <span class="player-stat-value kd">${player.kd}</span>
                </div>
                <div class="player-stat">
                    <span class="player-stat-label">ELO</span>
                    <span class="player-stat-value elo">${player.elo}</span>
                </div>
            </div>
        `;
        container.appendChild(card);
    });
}

// Initialize results table
function initializeResults(tbodyId, team) {
    const tbody = document.getElementById(tbodyId);
    tbody.innerHTML = '';
    
    team.forEach(player => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${player.name}</td>
            <td><input type="number" min="0" value="0" data-name="${player.name}" data-stat="K"></td>
            <td><input type="number" min="0" value="0" data-name="${player.name}" data-stat="D"></td>
            <td><input type="number" min="0" value="0" data-name="${player.name}" data-stat="A"></td>
            <td><input type="number" min="0" value="0" data-name="${player.name}" data-stat="ADR"></td>
            <td><input type="number" min="0" max="1" value="0" data-name="${player.name}" data-stat="MVP"></td>
        `;
        tbody.appendChild(row);
    });
}

// Get result data
function getResultData(tbodyId) {
    const tbody = document.getElementById(tbodyId);
    const rows = tbody.querySelectorAll('tr');
    const result = [];
    
    rows.forEach(row => {
        const inputs = row.querySelectorAll('input');
        const player = {
            Name: inputs[0].dataset.name,
            K: parseInt(inputs[0].value) || 0,
            D: parseInt(inputs[1].value) || 0,
            A: parseInt(inputs[2].value) || 0,
            ADR: parseInt(inputs[3].value) || 0,
            MVP: parseInt(inputs[4].value) || 0
        };
        result.push(player);
    });
    
    return result;
}

// Validate results
function validateResults(result1, result2) {
    const allFilled = [...result1, ...result2].every(player => {
        return player.K >= 0 && player.D >= 0 && player.A >= 0 && 
               player.ADR >= 0 && player.MVP >= 0 && player.MVP <= 1;
    });
    return allFilled;
}

// Update top 3
function updateTop3(top3) {
    if (top3 && top3.length >= 3) {
        // Update names
        document.getElementById('top-1-name').textContent = top3[0].Name;
        document.getElementById('top-2-name').textContent = top3[1].Name;
        document.getElementById('top-3-name').textContent = top3[2].Name;
        
        // Update ELO values
        const topPlayers = document.querySelectorAll('.top-player .elo');
        topPlayers[0].textContent = `${top3[0].ELO} ELO`;
        topPlayers[1].textContent = `${top3[1].ELO} ELO`;
        topPlayers[2].textContent = `${top3[2].ELO} ELO`;
        
        // Update rank icons
        if (top3[0].rank_icon) {
            document.getElementById('top-1-icon').src = top3[0].rank_icon;
            document.getElementById('top-1-icon').style.display = 'block';
        }
        if (top3[1].rank_icon) {
            document.getElementById('top-2-icon').src = top3[1].rank_icon;
            document.getElementById('top-2-icon').style.display = 'block';
        }
        if (top3[2].rank_icon) {
            document.getElementById('top-3-icon').src = top3[2].rank_icon;
            document.getElementById('top-3-icon').style.display = 'block';
        }
    }
}

// Initialize top 3 rank icons on page load
document.addEventListener('DOMContentLoaded', () => {
    // Get rank icons from initial data if available
    const top1Icon = document.getElementById('top-1-icon');
    const top2Icon = document.getElementById('top-2-icon');
    const top3Icon = document.getElementById('top-3-icon');
    
    // These will be set from server-side template initially
    if (top1Icon && !top1Icon.src) {
        top1Icon.style.display = 'none';
    }
    if (top2Icon && !top2Icon.src) {
        top2Icon.style.display = 'none';
    }
    if (top3Icon && !top3Icon.src) {
        top3Icon.style.display = 'none';
    }
});

// Reset match
function resetMatch() {
    currentMatch = null;
    document.getElementById('match-setup').style.display = 'none';
    document.getElementById('results-container').style.display = 'none';
    document.getElementById('command-box').style.display = 'none';
    document.getElementById('screenshot-upload').style.display = 'none';
    document.getElementById('submit-match-btn').disabled = true;
    document.getElementById('save-match-btn').disabled = true;
    
    // Reset file input
    document.getElementById('screenshot-file').value = '';
    document.getElementById('process-screenshot-btn').disabled = true;
    document.getElementById('ocr-status').style.display = 'none';
}

// Load player list for search
async function loadPlayerList() {
    try {
        const response = await fetch('/api/database');
        const players = await response.json();
        const datalist = document.getElementById('player-list');
        if (datalist) {
            datalist.innerHTML = '';
            players.forEach(player => {
                const option = document.createElement('option');
                option.value = player.name;
                datalist.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error loading player list:', error);
    }
}

// Setup statistics sub-tabs
function setupStatsSubtabs() {
    const subtabButtons = document.querySelectorAll('.stats-subtab-btn');
    const subtabContents = document.querySelectorAll('.stats-subtab-content');
    
    subtabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetSubtab = btn.getAttribute('data-subtab');
            
            // Remove active class from all buttons and contents
            subtabButtons.forEach(b => b.classList.remove('active'));
            subtabContents.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked button and corresponding content
            btn.classList.add('active');
            document.getElementById(`${targetSubtab}-subtab`).classList.add('active');
            
            // Load map stats if switching to map stats tab
            if (targetSubtab === 'map-stats') {
                loadMapStats();
            }
            // Load match history if switching to match history tab
            if (targetSubtab === 'match-history') {
                loadAllMatchHistory();
            }
            // Load records if switching to records tab
            if (targetSubtab === 'records') {
                loadRecords();
            }
        });
    });
}

// Load and display records
async function loadRecords() {
    try {
        const response = await fetch('/api/records');
        const data = await response.json();

        const container = document.getElementById('records-cards');
        const noRecordsMsg = document.getElementById('no-records-message');
        if (!container || !noRecordsMsg) return;

        if (!data.success || !data.records || Object.keys(data.records).length === 0) {
            container.style.display = 'none';
            noRecordsMsg.style.display = 'block';
            return;
        }

        const r = data.records;
        container.style.display = 'grid';
        noRecordsMsg.style.display = 'none';
        container.innerHTML = '';

        function matchLine(m) {
            if (!m) return '-';
            const map = m.map_name ? ` • ${escapeHtml(m.map_name)}` : '';
            const score = (m.team1_score !== undefined && m.team2_score !== undefined) ? ` • ${m.team1_score}-${m.team2_score}` : '';
            return `Match ${m.match_num}${map}${score}`;
        }

        function playerLine(p, fmt) {
            if (!p) return { title: '-', subtitle: '-', value: '-' };
            const map = p.map_name ? ` • ${escapeHtml(p.map_name)}` : '';
            const score = (p.team1_score !== undefined && p.team2_score !== undefined) ? ` • ${p.team1_score}-${p.team2_score}` : '';
            return {
                title: `${escapeHtml(p.player)}`,
                subtitle: `Match ${p.match_num}${map}${score}`,
                value: fmt(p.value)
            };
        }

        const cards = [
            {
                label: 'Longest Match',
                value: r.longest_match ? `${r.longest_match.total_rounds} rounds` : '-',
                subtitle: matchLine(r.longest_match),
                matchNum: r.longest_match ? r.longest_match.match_num : null
            },
            {
                label: 'Shortest Match',
                value: r.shortest_match ? `${r.shortest_match.total_rounds} rounds` : '-',
                subtitle: matchLine(r.shortest_match),
                matchNum: r.shortest_match ? r.shortest_match.match_num : null
            },
            (() => {
                const p = playerLine(r.highest_kills_single_match, v => `${Math.round(v)} kills`);
                return { label: 'Highest Kills (Single Match)', value: p.value, subtitle: `${p.title} • ${p.subtitle}`, matchNum: r.highest_kills_single_match ? r.highest_kills_single_match.match_num : null };
            })(),
            (() => {
                const p = playerLine(r.highest_deaths_single_match, v => `${Math.round(v)} deaths`);
                return { label: 'Highest Deaths (Single Match)', value: p.value, subtitle: `${p.title} • ${p.subtitle}`, matchNum: r.highest_deaths_single_match ? r.highest_deaths_single_match.match_num : null };
            })(),
            (() => {
                const p = playerLine(r.highest_rating_single_match, v => Number(v).toFixed(2));
                return { label: 'Highest Rating (Single Match)', value: p.value, subtitle: `${p.title} • ${p.subtitle}`, matchNum: r.highest_rating_single_match ? r.highest_rating_single_match.match_num : null };
            })(),
            (() => {
                const p = playerLine(r.highest_kpr_single_match, v => Number(v).toFixed(3));
                return { label: 'Highest KPR (Single Match)', value: p.value, subtitle: `${p.title} • ${p.subtitle}`, matchNum: r.highest_kpr_single_match ? r.highest_kpr_single_match.match_num : null };
            })(),
            (() => {
                const p = playerLine(r.highest_adr_single_match, v => Number(v).toFixed(0));
                return { label: 'Highest ADR (Single Match)', value: p.value, subtitle: `${p.title} • ${p.subtitle}`, matchNum: r.highest_adr_single_match ? r.highest_adr_single_match.match_num : null };
            })(),
            (() => {
                const p = playerLine(r.lowest_kpr_single_match, v => Number(v).toFixed(3));
                return { label: 'Lowest KPR (Single Match)', value: p.value, subtitle: `${p.title} • ${p.subtitle}`, matchNum: r.lowest_kpr_single_match ? r.lowest_kpr_single_match.match_num : null };
            })(),
            (() => {
                const p = playerLine(r.lowest_rating_single_match, v => Number(v).toFixed(2));
                return { label: 'Lowest Rating (Single Match)', value: p.value, subtitle: `${p.title} • ${p.subtitle}`, matchNum: r.lowest_rating_single_match ? r.lowest_rating_single_match.match_num : null };
            })(),
        ];

        cards.forEach(c => {
            const card = document.createElement('div');
            card.className = 'record-card';
            const matchNum = c.matchNum;
            if (matchNum) {
                card.classList.add('clickable');
                card.addEventListener('click', () => {
                    const num = parseInt(matchNum, 10);
                    if (!isNaN(num) && typeof showMatchDetails === 'function') {
                        showMatchDetails(num);
                    }
                });
            }
            card.innerHTML = `
                <div class="record-card-header">
                    <div class="record-card-title">${escapeHtml(c.label)}</div>
                </div>
                <div class="record-card-value">${escapeHtml(c.value)}</div>
                <div class="record-card-subtitle">${c.subtitle || '-'}</div>
            `;
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading records:', error);
    }
}

// Load and display map statistics
async function loadMapStats() {
    try {
        const response = await fetch('/api/map-stats');
        const data = await response.json();
        
        const container = document.getElementById('map-stats-cards');
        const noMapsMsg = document.getElementById('no-maps-message');
        
        if (!container || !noMapsMsg) return;
        
        if (!data.success || !data.maps || data.maps.length === 0) {
            container.style.display = 'none';
            noMapsMsg.style.display = 'block';
            return;
        }
        
        container.style.display = 'grid';
        noMapsMsg.style.display = 'none';
        container.innerHTML = '';
        
        data.maps.forEach(map => {
            const card = document.createElement('div');
            card.className = 'map-stat-card';
            
            // Get map image path
            const mapImagePath = getMapImagePath(map.map_name);
            if (mapImagePath) {
                card.style.setProperty('--map-bg-image', `url('${mapImagePath}')`);
                card.setAttribute('data-map', map.map_name.toLowerCase());
            }
            
            card.innerHTML = `
                <div class="map-card-overlay"></div>
                <div class="map-card-content">
                    <div class="map-card-header">
                        <h3 class="map-name">${map.map_name}</h3>
                    </div>
                    <div class="map-stats-grid">
                        <div class="map-stat-item">
                            <label>Games Played</label>
                            <span class="map-stat-value">${map.num_games}</span>
                        </div>
                        <div class="map-stat-item">
                            <label>Total Rounds</label>
                            <span class="map-stat-value">${map.total_rounds}</span>
                        </div>
                        <div class="map-stat-item">
                            <label>Avg Rounds</label>
                            <span class="map-stat-value highlight">${map.avg_rounds}</span>
                        </div>
                    </div>
                </div>
            `;
            
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading map stats:', error);
    }
}

// Player search
function setupPlayerSearch() {
    const searchBtn = document.getElementById('search-player-btn');
    const searchInput = document.getElementById('player-search');
    
    if (searchBtn) {
        searchBtn.addEventListener('click', searchPlayer);
    }
    
    if (searchInput) {
        searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                searchPlayer();
            }
        });
    }
}

async function searchPlayer() {
    const playerName = document.getElementById('player-search').value.trim();
    if (!playerName) {
        alert('Please enter a player name');
        return;
    }
    
    try {
        const response = await fetch(`/api/player-stats/${encodeURIComponent(playerName)}`);
        if (!response.ok) {
            if (response.status === 404) {
                alert('Player not found');
                return;
            }
            throw new Error('Failed to fetch player stats');
        }
        
        const stats = await response.json();
        displayPlayerStats(stats);
    } catch (error) {
        console.error('Error fetching player stats:', error);
        alert('Error fetching player stats');
    }
}

function displayPlayerStats(stats) {
    // Show container
    document.getElementById('player-stats-container').style.display = 'block';
    
    // Update header
    document.getElementById('player-name').textContent = stats.name;
    document.getElementById('player-rank-icon').src = stats.rank_icon;
    document.getElementById('player-elo').textContent = `${stats.elo} ELO`;
    document.getElementById('player-matches').textContent = `${stats.matches} Matches`;
    document.getElementById('player-winrate').textContent = `${stats.win_rate}% WR`;

    // Leader badges (global #1 from Database rankings)
    const leaderBadgesContainer = document.getElementById('player-leader-badges');
    const rankingContainer = document.getElementById('player-ranking');
    const dbPlayer = databaseData.find(p => p.name === stats.name);
    if (leaderBadgesContainer) {
        leaderBadgesContainer.innerHTML = renderLeaderBadgesHtml(dbPlayer);
    }
    if (rankingContainer) {
        const eloRank = dbPlayer && dbPlayer.elo_rank ? dbPlayer.elo_rank : null;
        rankingContainer.innerHTML = eloRank ? `<span class="player-rank-pill">Rank #${eloRank}</span>` : '';
    }
    
    // Update overview stats
    document.getElementById('stat-wins').textContent = stats.wins;
    document.getElementById('stat-losses').textContent = stats.losses;
    document.getElementById('stat-kd').textContent = stats.kd.toFixed(2);
    document.getElementById('stat-rating').textContent = stats.rating.toFixed(2);
    
    // Update per round stats
    document.getElementById('stat-kpr').textContent = stats.kpr.toFixed(3);
    document.getElementById('stat-dpr').textContent = stats.dpr.toFixed(3);
    document.getElementById('stat-apr').textContent = stats.apr.toFixed(3);
    document.getElementById('stat-adr').textContent = stats.adr.toFixed(2);
    
    // Update per match stats
    document.getElementById('stat-kpm').textContent = stats.kpm.toFixed(2);
    document.getElementById('stat-dpm').textContent = stats.dpm.toFixed(2);
    document.getElementById('stat-apm').textContent = stats.apm.toFixed(2);
    document.getElementById('stat-mvp').textContent = stats.mvp_count;
    
    // Update totals
    document.getElementById('stat-total-kills').textContent = stats.total_kills;
    document.getElementById('stat-total-deaths').textContent = stats.total_deaths;
    document.getElementById('stat-total-assists').textContent = stats.total_assists;
    document.getElementById('stat-current-elo').textContent = stats.elo;
    
    // Draw ELO graph
    drawELOGraph(stats);
    
    // Display match history
    displayMatchHistory(stats.match_history);
}

async function drawELOGraph(stats) {
    const canvas = document.getElementById('elo-graph');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // HiDPI canvas
    const cssWidth = canvas.offsetWidth || 600;
    const cssHeight = 200;
    const dpr = window.devicePixelRatio || 1;
    canvas.width = Math.floor(cssWidth * dpr);
    canvas.height = Math.floor(cssHeight * dpr);
    canvas.style.width = `${cssWidth}px`;
    canvas.style.height = `${cssHeight}px`;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    
    // Clear canvas
    ctx.clearRect(0, 0, cssWidth, cssHeight);
    
    // Fetch daily ELO history
    let history = [];
    try {
        const res = await fetch(`/api/elo-history/${encodeURIComponent(stats.name)}`);
        const data = await res.json();
        if (data && data.success && Array.isArray(data.history)) {
            history = data.history;
        }
    } catch (e) {
        // fall back to point
    }

    // If no history yet, show a single point (today)
    if (!history || history.length === 0) {
        ctx.fillStyle = '#9ca3af';
        ctx.font = '14px Arial';
        ctx.textAlign = 'center';
        ctx.fillText('No daily ELO history yet', cssWidth / 2, cssHeight / 2 - 8);
        if (stats.elo !== undefined) {
            ctx.fillStyle = '#f97316';
            ctx.beginPath();
            ctx.arc(cssWidth / 2, cssHeight / 2 + 18, 6, 0, Math.PI * 2);
            ctx.fill();
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 13px Arial';
            ctx.fillText(`${stats.elo} ELO`, cssWidth / 2, cssHeight / 2 + 40);
        }
        return;
    }

    const pad = 28;
    const w = cssWidth;
    const h = cssHeight;
    const plotW = w - pad * 2;
    const plotH = h - pad * 2;
    const values = history.map(p => Number(p.elo));
    let minE = Math.min(...values);
    let maxE = Math.max(...values);
    if (minE === maxE) {
        minE -= 10;
        maxE += 10;
    }
    const n = history.length;

    // Grid
    ctx.strokeStyle = 'rgba(255,255,255,0.06)';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = pad + (plotH * i) / 4;
        ctx.beginPath();
        ctx.moveTo(pad, y);
        ctx.lineTo(w - pad, y);
        ctx.stroke();
    }

    // Axes labels (min/max)
    ctx.fillStyle = 'rgba(255,255,255,0.7)';
    ctx.font = '11px Arial';
    ctx.textAlign = 'left';
    ctx.fillText(`${maxE}`, pad, pad - 8);
    ctx.fillText(`${minE}`, pad, h - pad + 16);

    // Line
    const xFor = (i) => pad + (plotW * (n === 1 ? 0.5 : i / (n - 1)));
    const yFor = (elo) => pad + plotH * (1 - (elo - minE) / (maxE - minE));

    ctx.strokeStyle = '#f97316';
    ctx.lineWidth = 2;
    ctx.beginPath();
    history.forEach((p, i) => {
        const x = xFor(i);
        const y = yFor(Number(p.elo));
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // Last point + label
    const last = history[history.length - 1];
    const lx = xFor(history.length - 1);
    const ly = yFor(Number(last.elo));
    ctx.fillStyle = '#f97316';
    ctx.beginPath();
    ctx.arc(lx, ly, 4, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#ffffff';
    ctx.font = 'bold 12px Arial';
    ctx.textAlign = 'right';
    ctx.fillText(`${last.elo} ELO`, w - pad, pad - 8);
}

function displayMatchHistory(matchHistory) {
    const container = document.getElementById('match-history-cards');
    const noMatchesMsg = document.getElementById('no-matches-message');
    
    if (!container || !noMatchesMsg) return;
    
    if (!matchHistory || matchHistory.length === 0) {
        container.style.display = 'none';
        noMatchesMsg.style.display = 'block';
        return;
    }
    
    container.style.display = 'grid';
    noMatchesMsg.style.display = 'none';
    container.innerHTML = '';
    
    // Sort by match ID (newest first)
    matchHistory.sort((a, b) => {
        const aNum = parseInt(a.match_id.replace('match_', ''));
        const bNum = parseInt(b.match_id.replace('match_', ''));
        return bNum - aNum;
    });
    
    matchHistory.forEach(match => {
        const card = document.createElement('div');
        card.className = `match-history-card ${match.player_stats.won ? 'won' : 'lost'}`;
        
        // Set map background if available
        if (match.map) {
            const mapImagePath = getMapImagePath(match.map);
            if (mapImagePath) {
                card.style.setProperty('--map-bg-image', `url('${mapImagePath}')`);
                card.setAttribute('data-map', match.map.toLowerCase());
            }
        }
        
        const stats = match.player_stats;
        card.innerHTML = `
            <div class="match-card-overlay"></div>
            <div class="match-card-content">
                <div class="match-card-header">
                    <span class="match-id">${match.match_id}</span>
                    <span class="match-result ${stats.won ? 'won' : 'lost'}">${stats.won ? 'Won' : 'Lost'}</span>
                    ${match.map ? `<span class="match-map">${match.map}</span>` : ''}
                </div>
                <div class="match-stats-grid">
                    <div class="match-stat-item">
                        <label>Kills</label>
                        <span>${stats.k}</span>
                    </div>
                    <div class="match-stat-item">
                        <label>Deaths</label>
                        <span>${stats.d}</span>
                    </div>
                    <div class="match-stat-item">
                        <label>Assists</label>
                        <span>${stats.a}</span>
                    </div>
                    <div class="match-stat-item">
                        <label>ADR</label>
                        <span>${stats.adr}</span>
                    </div>
                    <div class="match-stat-item">
                        <label>K/D</label>
                        <span>${(stats.k / (stats.d || 1)).toFixed(2)}</span>
                    </div>
                    <div class="match-stat-item">
                        <label>MVP</label>
                        <span>${stats.mvp > 0 ? '⭐' : '-'}</span>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(card);
    });
}

// Global variable for match history pagination
let allMatches = [];
let currentMatchPage = 1;
const matchesPerPage = 10;

// Load and display all match history
async function loadAllMatchHistory(page = 1) {
    try {
        const response = await fetch('/api/all-matches');
        const data = await response.json();
        
        const container = document.getElementById('all-match-history-cards');
        const noMatchesMsg = document.getElementById('no-all-matches-message');
        const pagination = document.getElementById('match-pagination');
        
        if (!container || !noMatchesMsg || !pagination) return;
        
        if (!data.success || !data.matches || data.matches.length === 0) {
            container.style.display = 'none';
            noMatchesMsg.style.display = 'block';
            pagination.style.display = 'none';
            return;
        }
        
        allMatches = data.matches;
        currentMatchPage = page;
        
        // Calculate pagination
        const totalPages = Math.ceil(allMatches.length / matchesPerPage);
        const startIndex = (page - 1) * matchesPerPage;
        const endIndex = startIndex + matchesPerPage;
        const matchesToShow = allMatches.slice(startIndex, endIndex);
        
        container.style.display = 'flex';
        noMatchesMsg.style.display = 'none';
        container.innerHTML = '';
        
        matchesToShow.forEach(match => {
            const card = document.createElement('div');
            card.className = 'match-history-card';
            card.setAttribute('data-match-num', match.match_num);
            
            // Set map background if available
            if (match.map_name) {
                const mapImagePath = getMapImagePath(match.map_name);
                if (mapImagePath) {
                    card.style.setProperty('--map-bg-image', `url('${mapImagePath}')`);
                    card.setAttribute('data-map', match.map_name.toLowerCase());
                }
            }
            
            const team1Won = match.winning_team === 'Team 1';
            const team2Won = match.winning_team === 'Team 2';
            
            card.innerHTML = `
                <div class="match-card-overlay"></div>
                <div class="match-card-content">
                    <div class="match-card-header">
                        <span class="match-id">Match ${match.match_num}</span>
                        ${match.map_name ? `<span class="match-map">${match.map_name}</span>` : ''}
                    </div>
                    <div class="match-score-display">
                        <div class="team-score ${team1Won ? 'winner' : ''}">
                            <div class="team-name">Team 1</div>
                            <div class="score-value">${match.team1_score}</div>
                        </div>
                        <div class="score-separator">-</div>
                        <div class="team-score ${team2Won ? 'winner' : ''}">
                            <div class="team-name">Team 2</div>
                            <div class="score-value">${match.team2_score}</div>
                        </div>
                    </div>
                    <div class="match-card-footer">
                        <span class="match-rounds">${match.total_rounds} rounds</span>
                        <span class="match-mvp">${match.mvp_name ? `MVP: ${match.mvp_name}` : 'MVP: -'}</span>
                        <span class="match-date">${new Date(match.created_at).toLocaleDateString()}</span>
                    </div>
                </div>
            `;
            
            // Add click event to show match details
            card.addEventListener('click', () => {
                showMatchDetails(match.match_num);
            });
            
            container.appendChild(card);
        });
        
        // Render pagination
        renderMatchPagination(totalPages, page);
    } catch (error) {
        console.error('Error loading match history:', error);
    }
}

// Render pagination controls
function renderMatchPagination(totalPages, currentPage) {
    const pagination = document.getElementById('match-pagination');
    if (!pagination) return;
    
    if (totalPages <= 1) {
        pagination.style.display = 'none';
        return;
    }
    
    pagination.style.display = 'flex';
    pagination.innerHTML = '';
    
    // Previous button
    const prevBtn = document.createElement('button');
    prevBtn.className = 'pagination-btn';
    prevBtn.textContent = '←';
    prevBtn.disabled = currentPage === 1;
    prevBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            loadAllMatchHistory(currentPage - 1);
        }
    });
    pagination.appendChild(prevBtn);
    
    // Page numbers
    const pageNumbers = document.createElement('div');
    pageNumbers.className = 'pagination-numbers';
    
    // Show first page
    if (currentPage > 3) {
        const firstBtn = createPageButton(1, currentPage);
        pageNumbers.appendChild(firstBtn);
        if (currentPage > 4) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'pagination-ellipsis';
            ellipsis.textContent = '...';
            pageNumbers.appendChild(ellipsis);
        }
    }
    
    // Show pages around current page
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        const pageBtn = createPageButton(i, currentPage);
        pageNumbers.appendChild(pageBtn);
    }
    
    // Show last page
    if (currentPage < totalPages - 2) {
        if (currentPage < totalPages - 3) {
            const ellipsis = document.createElement('span');
            ellipsis.className = 'pagination-ellipsis';
            ellipsis.textContent = '...';
            pageNumbers.appendChild(ellipsis);
        }
        const lastBtn = createPageButton(totalPages, currentPage);
        pageNumbers.appendChild(lastBtn);
    }
    
    pagination.appendChild(pageNumbers);
    
    // Next button
    const nextBtn = document.createElement('button');
    nextBtn.className = 'pagination-btn';
    nextBtn.textContent = '→';
    nextBtn.disabled = currentPage === totalPages;
    nextBtn.addEventListener('click', () => {
        if (currentPage < totalPages) {
            loadAllMatchHistory(currentPage + 1);
        }
    });
    pagination.appendChild(nextBtn);
}

// Create a page number button
function createPageButton(pageNum, currentPage) {
    const btn = document.createElement('button');
    btn.className = 'pagination-page-btn';
    if (pageNum === currentPage) {
        btn.classList.add('active');
    }
    btn.textContent = pageNum;
    btn.addEventListener('click', () => {
        loadAllMatchHistory(pageNum);
    });
    return btn;
}

// Show match details modal
async function showMatchDetails(matchNum) {
    try {
        const response = await fetch(`/api/match-details/${matchNum}`);
        const data = await response.json();
        
        if (!data.success) {
            alert('Error loading match details');
            return;
        }
        
        const modal = document.getElementById('match-details-modal');
        const content = document.getElementById('match-details-content');
        
        const match = data.match;
        const team1Stats = data.team1_stats || [];
        const team2Stats = data.team2_stats || [];
        const metadata = data.metadata || {};
        
        const team1Won = match.winning_team === 'Team 1';
        const team2Won = match.winning_team === 'Team 2';
        
        // Build match details HTML (Faceit style)
        let html = `
            <div class="match-details-header">
                <div class="match-details-title">
                    <h2>Match ${match.match_num}</h2>
                    ${match.map_name ? `<span class="match-details-map">${match.map_name}</span>` : ''}
                </div>
                <div class="match-details-score">
                    <div class="team-detail-score ${team1Won ? 'winner' : ''}">
                        <div class="team-detail-name">Team 1</div>
                        <div class="team-detail-score-value">${match.team1_score}</div>
                    </div>
                    <div class="score-separator-large">-</div>
                    <div class="team-detail-score ${team2Won ? 'winner' : ''}">
                        <div class="team-detail-name">Team 2</div>
                        <div class="team-detail-score-value">${match.team2_score}</div>
                    </div>
                </div>
            </div>
            <div class="match-details-teams">
                <div class="team-details ${team1Won ? 'winner-team' : ''}">
                    <div class="team-details-header">
                        <h3>Team 1 ${team1Won ? '<span class="winner-badge">WIN</span>' : ''}</h3>
                    </div>
                    <div class="team-players-list">
                        <div class="player-stats-header">
                            <div class="player-header-name">Player</div>
                            <div class="player-header-stats">
                                <span class="stat-header">K</span>
                                <span class="stat-header">D</span>
                                <span class="stat-header">A</span>
                                <span class="stat-header">ADR</span>
                            </div>
                        </div>
                        ${team1Stats.map(player => `
                            <div class="player-detail-row ${player.MVP > 0 ? 'mvp-player' : ''}">
                                <div class="player-detail-name">${player.Name || 'Unknown'}</div>
                                <div class="player-detail-stats">
                                    <span class="stat-k">${player.K || 0}</span>
                                    <span class="stat-d">${player.D || 0}</span>
                                    <span class="stat-a">${player.A || 0}</span>
                                    <span class="stat-adr">${player.ADR || 0}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
                <div class="team-details ${team2Won ? 'winner-team' : ''}">
                    <div class="team-details-header">
                        <h3>Team 2 ${team2Won ? '<span class="winner-badge">WIN</span>' : ''}</h3>
                    </div>
                    <div class="team-players-list">
                        <div class="player-stats-header">
                            <div class="player-header-name">Player</div>
                            <div class="player-header-stats">
                                <span class="stat-header">K</span>
                                <span class="stat-header">D</span>
                                <span class="stat-header">A</span>
                                <span class="stat-header">ADR</span>
                            </div>
                        </div>
                        ${team2Stats.map(player => `
                            <div class="player-detail-row ${player.MVP > 0 ? 'mvp-player' : ''}">
                                <div class="player-detail-name">${player.Name || 'Unknown'}</div>
                                <div class="player-detail-stats">
                                    <span class="stat-k">${player.K || 0}</span>
                                    <span class="stat-d">${player.D || 0}</span>
                                    <span class="stat-a">${player.A || 0}</span>
                                    <span class="stat-adr">${player.ADR || 0}</span>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
        content.innerHTML = html;
        modal.classList.add('active');
        
        // Close modal handlers
        const closeBtn = document.getElementById('match-modal-close');
        const overlay = modal.querySelector('.match-modal-overlay');
        
        closeBtn.onclick = () => closeMatchModal();
        overlay.onclick = () => closeMatchModal();
        
        // Close on ESC key
        document.addEventListener('keydown', function escHandler(e) {
            if (e.key === 'Escape') {
                closeMatchModal();
                document.removeEventListener('keydown', escHandler);
            }
        });
    } catch (error) {
        console.error('Error loading match details:', error);
        alert('Error loading match details');
    }
}

function closeMatchModal() {
    const modal = document.getElementById('match-details-modal');
    modal.classList.remove('active');
}

function getMapImagePath(mapName) {
    // Map names to image file names
    const mapImageMap = {
        'dust2': '/assets/maps/dust2.jpg',
        'inferno': '/assets/maps/inferno.jpg',
        'mirage': '/assets/maps/mirage.jpg',
        'vertigo': '/assets/maps/vertigo.jpg',
        'anubis': '/assets/maps/anubis.jpg',
        'ancient': '/assets/maps/ancient.jpeg',
        'train': '/assets/maps/train.jpg',
        'nuke': '/assets/maps/nuke.png'
    };
    
    const normalizedName = mapName.toLowerCase();
    return mapImageMap[normalizedName] || null;
}

