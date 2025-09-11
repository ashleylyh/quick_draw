import {toZh, formatTimestamp, buildCSVFromData } from './utils.js';

// Individual API-calling functions
async function fetchSessionResults(sessionId) {
    try {
        const response = await fetch(`http://localhost:8000/api/session/${sessionId}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        throw error;
    }
}

async function fetchPlayerDrawings(sessionId) {
    try {
        const response = await fetch(`http://localhost:8000/api/drawing/${sessionId}`);
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return await response.json();
    } catch (error) {
        throw error;
    }
}

async function fetchUMAPVisualization(sessionId) {
    try {
        console.log(`Fetching UMAP visualization for session: ${sessionId}`);
        const response = await fetch(`http://localhost:8000/api/umap/${sessionId}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`UMAP API error: ${response.status} ${response.statusText}`, errorText);
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('UMAP API response:', data);
        return data;
    } catch (error) {
        console.error('Error fetching UMAP visualization:', error);
        throw error;
    }
}

async function fetchRadarChart(sessionId) {
    try {
        console.log(`Fetching radar chart for session: ${sessionId}`);
        const response = await fetch(`http://localhost:8000/api/radar/${sessionId}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Radar API error: ${response.status} ${response.statusText}`, errorText);
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Radar API response:', data);
        return data;
    } catch (error) {
        console.error('Error fetching radar chart:', error);
        throw error;
    }
}

// Individual population functions (no API calls)
function populateSessionInfo(sessionData) {
    const playerInfo = document.getElementById('playerInfo');
    if (!playerInfo) return;

    // Handle timestamp formatting with error checking
    let formattedTime = '未知時間';
    if (sessionData.timestamp) {
        try {
            formattedTime = formatTimestamp(sessionData.timestamp);
        } catch (error) {
            formattedTime = sessionData.timestamp; // Fallback to raw timestamp
        }
    }
    
    playerInfo.innerHTML = `參賽者：${sessionData.player_name || '未知'}&emsp;&emsp;難度：${sessionData.difficulty === 'hard' ? '困難' : '簡單'}&emsp;&emsp;時間：${formattedTime}`;
}

function populateResultsTable(sessionData, drawingsData) {
    const resultsBody = document.getElementById('resultsBody');
    if (!resultsBody) return;

    let sessionRounds = [];
    if (typeof sessionData.rounds === 'string') {
        try {
            sessionRounds = JSON.parse(sessionData.rounds);
        } catch (e) {
            sessionRounds = [];
        }
    } else if (Array.isArray(sessionData.rounds)) {
        sessionRounds = sessionData.rounds;
    } else {
        sessionRounds = [];
    }

    let totalScore = 0;
    const rows = (drawingsData || []).map(d => {
        const predictions = typeof d.predictions === 'string' ? JSON.parse(d.predictions) : (d.predictions || {});
        const roundChoices = sessionRounds[d.round - 1] || [];
        let filteredPredictions = predictions;
        if (roundChoices.length > 0) {
            filteredPredictions = {};
            roundChoices.forEach(choice => {
                if (predictions[choice] !== undefined) {
                    filteredPredictions[choice] = predictions[choice];
                }
            });
        }
        const sorted = Object.entries(filteredPredictions).map(([name,p])=>({name,p})).sort((a,b)=>b.p-a.p);
        const top1 = sorted[0] ? `${toZh(sorted[0].name)} (${(sorted[0].p*100).toFixed(1)}%)` : '-';
        
        // Check correctness - if top1 prediction matches the prompt
        const isCorrect = sorted[0] && sorted[0].name === d.prompt;
        const correctnessDisplay = isCorrect ? 
            '<span class="correct-indicator correct">✓</span>' : 
            '<span class="correct-indicator incorrect">✗</span>';
        
        // Calculate score - use the probability for the correct prompt
        const score = predictions[d.prompt] ? (predictions[d.prompt] * 100) : 0;
        totalScore += score;
        const scoreDisplay = `<span class="score-cell">${score.toFixed(1)}</span>`;
        
        return `<tr>
            <td>${d.round}</td>
            <td>${toZh(d.prompt)}</td>
            <td>${top1}</td>
            <td>${d.time_spent_sec}s</td>
            <td>${d.timed_out ? '是' : '否'}</td>
            <td>${correctnessDisplay}</td>
            <td>${scoreDisplay}</td>
        </tr>`;
    }).join('');
    
    resultsBody.innerHTML = rows;
    
    // Update total score display
    updateTotalScore(totalScore);
}

function updateTotalScore(totalScore) {
    const totalScoreValue = document.getElementById('totalScoreValue');
    if (totalScoreValue) {
        totalScoreValue.textContent = totalScore.toFixed(1);
    }
}

function populatePlayerDrawings(drawingsData) {
    const drawingsGrid = document.getElementById('drawingsGrid');
    if (!drawingsGrid) return;

    drawingsGrid.innerHTML = '';
    
    if (!drawingsData || !Array.isArray(drawingsData) || drawingsData.length === 0) {
        drawingsGrid.innerHTML = '<div class="loading-message">無繪圖資料 (資料為空)</div>';
        return;
    }
    
    drawingsData.forEach((d, idx) => {
        try {
            const drawingItem = document.createElement('div');
            drawingItem.className = 'drawing-item';
            drawingItem.innerHTML = `
                <div class="drawing-label">第${d.round || idx + 1}題：${toZh(d.prompt || '未知題目')}</div>
                <img src="data:image/png;base64,${d.image_base64}" 
                     alt="drawing ${idx+1}" 
                     class="drawing-image">
            `;
            drawingsGrid.appendChild(drawingItem);
        } catch (error) {
            drawingItem.innerHTML = '<div class="loading-message">無法顯示繪圖</div>';
        }
    });
}

function populateUMAPVisualization(umapData) {
    const umapImage = document.getElementById('umapImage');
    const umapLoading = document.getElementById('umapLoading');
    
    console.log('populateUMAPVisualization called with:', umapData);
    
    if (!umapImage || !umapLoading) {
        console.error('UMAP DOM elements not found:', {
            umapImage: !!umapImage,
            umapLoading: !!umapLoading
        });
        return;
    }
    
    if (umapData && umapData.status === 'success' && umapData.image_base64) {
        console.log('UMAP data is valid, setting image source');
        
        // Add error handling for image loading
        umapImage.onload = function() {
            console.log('UMAP image loaded successfully');
            umapImage.style.display = 'block';
            umapLoading.style.display = 'none';
        };
        
        umapImage.onerror = function() {
            console.error('Failed to load UMAP image');
            umapLoading.textContent = '圖片載入失敗';
            umapImage.style.display = 'none';
        };
        
        umapImage.src = `data:image/png;base64,${umapData.image_base64}`;
        
        // Show additional info if available
        if (umapData.embeddings_count) {
            console.log(`UMAP generated from ${umapData.embeddings_count} embeddings`);
        }
        if (umapData.skipped_classes && umapData.skipped_classes.length > 0) {
            console.warn('Some classes were skipped:', umapData.skipped_classes);
        }
        
    } else {
        console.error('UMAP data is invalid:', {
            hasData: !!umapData,
            status: umapData?.status,
            hasImage: !!umapData?.image_base64,
            fullData: umapData
        });
        
        let errorMessage = 'UMAP載入失敗';
        if (umapData?.status === 'error') {
            errorMessage += `: ${umapData.error || '未知錯誤'}`;
        } else if (!umapData) {
            errorMessage += ': 無回應資料';
        } else if (!umapData.image_base64) {
            errorMessage += ': 無圖片資料';
        }
        
        umapLoading.textContent = errorMessage;
        umapImage.style.display = 'none';
        umapLoading.style.display = 'block';
    }
}

function populateRadarChart(radarData) {
    const radarImage = document.getElementById('radarImage');
    const radarLoading = document.getElementById('radarLoading');
    
    console.log('populateRadarChart called with:', radarData);
    
    if (!radarImage || !radarLoading) {
        console.error('Radar DOM elements not found:', {
            radarImage: !!radarImage,
            radarLoading: !!radarLoading
        });
        return;
    }
    
    if (radarData && radarData.status === 'success' && radarData.image_base64) {
        console.log('Radar data is valid, setting image source');
        
        // Add error handling for image loading
        radarImage.onload = function() {
            console.log('Radar image loaded successfully');
            radarImage.style.display = 'block';
            radarLoading.style.display = 'none';
        };
        
        radarImage.onerror = function() {
            console.error('Failed to load radar image');
            radarLoading.textContent = '雷達圖載入失敗';
            radarImage.style.display = 'none';
        };
        
        radarImage.src = `data:image/png;base64,${radarData.image_base64}`;
        
        // Show additional info if available
        if (radarData.drawings_count) {
            console.log(`Radar chart generated from ${radarData.drawings_count} drawings`);
        }
        if (radarData.prompts && radarData.probabilities) {
            console.log('Radar data:', {
                prompts: radarData.prompts,
                probabilities: radarData.probabilities
            });
        }
        
    } else {
        console.error('Radar data is invalid:', {
            hasData: !!radarData,
            status: radarData?.status,
            hasImage: !!radarData?.image_base64,
            fullData: radarData
        });
        
        let errorMessage = '雷達圖載入失敗';
        if (radarData?.status === 'error') {
            errorMessage += `: ${radarData.error || '未知錯誤'}`;
        } else if (!radarData) {
            errorMessage += ': 無回應資料';
        } else if (!radarData.image_base64) {
            errorMessage += ': 無圖片資料';
        }
        
        radarLoading.textContent = errorMessage;
        radarImage.style.display = 'none';
        radarLoading.style.display = 'block';
    }
}

function setupCSVDownload(sessionData, drawingsData) {
    const downloadBtn = document.getElementById('downloadBtn');
    if (!downloadBtn) return;
    
    const data = {
        session: sessionData,
        drawings: drawingsData
    };
    
    const csvContent = buildCSVFromData(data);
    const csvBlob = new Blob([csvContent], { type: 'text/csv;charset=utf-8' });
    const csvUrl = URL.createObjectURL(csvBlob);
    
    downloadBtn.href = csvUrl;
    downloadBtn.download = `quickdraw_logs_${sessionData.session_id}.csv`;
}

// Second level function that coordinates all individual functions
async function populateAll(sessionId) {
    try {
        // Show loading states
        const playerInfo = document.getElementById('playerInfo');
        const resultsBody = document.getElementById('resultsBody');
        const drawingsGrid = document.getElementById('drawingsGrid');
        const umapLoading = document.getElementById('umapLoading');
        const radarLoading = document.getElementById('radarLoading');
        
        if (playerInfo) playerInfo.innerHTML = '載入中...';
        if (resultsBody) resultsBody.innerHTML = '<tr><td colspan="5">載入中...</td></tr>';
        if (drawingsGrid) drawingsGrid.innerHTML = '<div class="loading-message">載入中...</div>';
        if (umapLoading) umapLoading.textContent = '載入中...';
        if (radarLoading) radarLoading.textContent = '載入中...';

        // Fetch all data
        const [sessionResults, drawingsResults, umapResults, radarResults] = await Promise.allSettled([
            fetchSessionResults(sessionId),
            fetchPlayerDrawings(sessionId),
            fetchUMAPVisualization(sessionId),
            fetchRadarChart(sessionId)
        ]);

        console.log('Umap Results:', umapResults);
        console.log('Radar Results:', radarResults);
        // Handle session results
        if (sessionResults.status === 'fulfilled') {
            const sessionData = sessionResults.value.session || sessionResults.value;
            populateSessionInfo(sessionData);
            
            // Also handle drawings data if available for results table
            if (drawingsResults.status === 'fulfilled') {
                const drawingsData = drawingsResults.value.drawing || drawingsResults.value;
                populateResultsTable(sessionData, drawingsData);
                // setupCSVDownload(sessionData, drawingsData);
            }
        } else {
            if (playerInfo) playerInfo.innerHTML = '載入失敗';
            if (resultsBody) resultsBody.innerHTML = '<tr><td colspan="5">載入失敗</td></tr>';
        }

        // Handle player drawings
        if (drawingsResults.status === 'fulfilled') {
            const drawingsData = drawingsResults.value.drawing || drawingsResults.value;
            populatePlayerDrawings(drawingsData);
        } else {
            if (drawingsGrid) drawingsGrid.innerHTML = '<div class="loading-message">繪圖載入失敗</div>';
        }

        // Handle UMAP visualization
        if (umapResults.status === 'fulfilled') {
            console.log('UMAP request fulfilled successfully');
            populateUMAPVisualization(umapResults.value);
        } else {
            console.error('UMAP request failed:', umapResults.reason);
            if (umapLoading) {
                let errorMessage = 'UMAP載入失敗';
                if (umapResults.reason?.message) {
                    errorMessage += `: ${umapResults.reason.message}`;
                }
                umapLoading.textContent = errorMessage;
            }
        }

        // Handle Radar chart
        if (radarResults.status === 'fulfilled') {
            console.log('Radar request fulfilled successfully');
            populateRadarChart(radarResults.value);
        } else {
            console.error('Radar request failed:', radarResults.reason);
            if (radarLoading) {
                let errorMessage = '雷達圖載入失敗';
                if (radarResults.reason?.message) {
                    errorMessage += `: ${radarResults.reason.message}`;
                }
                radarLoading.textContent = errorMessage;
            }
        }

    } catch (error) {
        const playerInfo = document.getElementById('playerInfo');
        const resultsBody = document.getElementById('resultsBody');
        if (playerInfo) playerInfo.innerHTML = '載入錯誤';
        if (resultsBody) resultsBody.innerHTML = '<tr><td colspan="5">資料處理錯誤</td></tr>';
    }
}

// Main load function (no API calls)
function loadResults() {
    const urlParams = new URLSearchParams(window.location.search);
    const sessionId = urlParams.get('sessionId');
    
    if (sessionId) {
        populateAll(sessionId);
    } else if (window.scoreData) {
        // Handle legacy data if needed
        const sessionData = window.scoreData.session;
        const drawingsData = window.scoreData.drawings;
        
        populateSessionInfo(sessionData);
        populateResultsTable(sessionData, drawingsData);
        populatePlayerDrawings(drawingsData);
        setupCSVDownload(sessionData, drawingsData);
    } else {
        const playerInfo = document.getElementById('playerInfo');
        const resultsBody = document.getElementById('resultsBody');
        if (playerInfo) playerInfo.innerHTML = '無資料';
        if (resultsBody) resultsBody.innerHTML = '<tr><td colspan="5">無法載入成績資料</td></tr>';
        alert('無法載入成績資料');
    }
}

// Event listeners
document.getElementById('restartBtn').addEventListener('click', function() {
    if (window.opener && typeof window.opener.restartGame === 'function') {
        window.opener.restartGame();
        window.close();
    } else {
        alert('請回到主畫面按重新開始');
    }
});

document.addEventListener('DOMContentLoaded', function() {
    loadResults();
});