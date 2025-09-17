import {toZh, formatTimestamp, buildCSVFromData } from './utils.js';

// Import html2canvas from CDN (will be loaded in HTML)
// QR codes are generated on the backend and stored in Redis database

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

async function fetchBothPlots(sessionId) {
    try {
        console.log(`Fetching both plots for session: ${sessionId}`);
        const response = await fetch(`http://localhost:8000/api/plots/${sessionId}`);
        
        if (!response.ok) {
            const errorText = await response.text();
            console.error(`Both plots API error: ${response.status} ${response.statusText}`, errorText);
            throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`);
        }
        
        const data = await response.json();
        console.log('Both plots API response:', data);
        return data;
    } catch (error) {
        console.error('Error fetching both plots:', error);
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
    playerInfo.innerHTML = `
        <span class="player-label">參賽者：</span>
        <span class="player-value">${sessionData.player_name || '未知'}</span>
        &emsp;&emsp;&emsp;
        <span class="player-label">難度：</span>
        <span class="player-value">${sessionData.difficulty === 'hard' ? '困難' : '簡單'}</span>
        &emsp;&emsp;&emsp;
        <span class="player-label">時間：</span>
        <span class="player-value">${formattedTime}</span>
    `;
    // playerInfo.innerHTML = `參賽者：${sessionData.player_name || '未知'}&emsp;&emsp;難度：${sessionData.difficulty === 'hard' ? '困難' : '簡單'}&emsp;&emsp;時間：${formattedTime}`;
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
    let totalTime = 0;
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
        
        // Add time to total
        totalTime += parseFloat(d.time_spent_sec) || 0;
        
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
    
    // Update total score and time displays
    updateTotalScore(totalScore);
    updateTotalTime(totalTime);
}

function updateTotalScore(totalScore) {
    const totalScoreValue = document.getElementById('totalScoreValue');
    if (totalScoreValue) {
        totalScoreValue.textContent = totalScore.toFixed(1);
    }
}

function updateTotalTime(totalTime) {
    const totalTimeValue = document.getElementById('totalTimeValue');
    if (totalTimeValue) {
        totalTimeValue.textContent = totalTime.toFixed(1);
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
                <img src="data:image/png;base64,${d.original_image_data}" 
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

function setupScreenshotDownload(sessionData, drawingsData) {
    const downloadBtn = document.getElementById('downloadBtn');
    if (!downloadBtn) return;
    
    downloadBtn.textContent = '下載成績截圖';
    downloadBtn.href = '#';
    downloadBtn.removeAttribute('download');
    
    downloadBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        await generateScreenshot(sessionData, drawingsData);
    });
}

async function generateScreenshot(sessionData, drawingsData) {
    try {
        // Check if html2canvas is available
        if (typeof html2canvas === 'undefined') {
            alert('html2canvas 庫未載入，請重新整理頁面後再試');
            return;
        }

        // Show loading indicator
        const downloadBtn = document.getElementById('downloadBtn');
        const originalText = downloadBtn.textContent;
        downloadBtn.textContent = '截圖中...';
        downloadBtn.disabled = true;

        // Get the main score container - adjust selector based on your HTML structure
        const scoreContainer = document.querySelector('.score-card') || document.querySelector('.container') || document.body;
        
        // Generate screenshot
        const canvas = await html2canvas(scoreContainer, { 
            useCORS: true, 
            scale: 2, // Higher quality
            backgroundColor: '#ffffff',
            width: scoreContainer.scrollWidth,
            height: scoreContainer.scrollHeight,
            allowTaint: false,
            logging: false
        });
        
        // Convert to image data
        const imgData = canvas.toDataURL('image/png');
        
        // Create download link
        const link = document.createElement('a');
        link.href = imgData;
        const fileName = `quickdraw_score_${sessionData.player_name}_${sessionData.session_id}.png`;
        link.download = fileName;
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // Reset button
        downloadBtn.textContent = originalText;
        downloadBtn.disabled = false;
        
    } catch (error) {
        console.error('Error generating screenshot:', error);
        alert('截圖生成失敗，請再試一次');
        
        // Reset button
        const downloadBtn = document.getElementById('downloadBtn');
        downloadBtn.textContent = '下載成績截圖';
        downloadBtn.disabled = false;
    }
}

// QR Code functionality
function setupQRDownload(sessionData, drawingsData) {
    const qrBtn = document.getElementById('qrBtn');
    const qrModal = document.getElementById('qrModal');
    const qrCloseBtn = document.getElementById('qrCloseBtn');
    
    if (!qrBtn || !qrModal || !qrCloseBtn) return;
    
    // QR button click handler
    qrBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        await generateQRCode(sessionData, drawingsData);
    });
    
    // Close modal handlers
    qrCloseBtn.addEventListener('click', function() {
        qrModal.style.display = 'none';
    });
    
    qrModal.addEventListener('click', function(e) {
        if (e.target === qrModal) {
            qrModal.style.display = 'none';
        }
    });
}

async function generateQRCode(sessionData, drawingsData) {
    const qrModal = document.getElementById('qrModal');
    const qrCodeContainer = document.getElementById('qrCodeContainer');
    const qrStatus = document.getElementById('qrStatus');
    const qrBtn = document.getElementById('qrBtn');
    const qrTimestamp = document.getElementById('qrTimestamp');
    
    try {
        // Show modal and loading state
        qrModal.style.display = 'flex';
        qrCodeContainer.innerHTML = '';
        qrStatus.textContent = '檢查現有 QR 碼...';
        qrStatus.className = '';
        
        // Clear timestamp
        if (qrTimestamp) {
            qrTimestamp.style.display = 'none';
            qrTimestamp.textContent = '';
        }
        
        // Disable QR button
        const originalText = qrBtn.textContent;
        qrBtn.textContent = '檢查中...';
        qrBtn.disabled = true;
        
        // Check if QR code already exists in Redis
        const existingQR = await checkExistingQRCode(sessionData.session_id);
        
        let qrImageBase64;
        let shareableUrl;
        // let cacheStatus;
        let createdAt;
        
        if (existingQR.exists) {
            qrStatus.textContent = '使用資料庫中的 QR 碼...';
            qrImageBase64 = existingQR.qrImageBase64;
            shareableUrl = existingQR.shareableUrl;
            // cacheStatus = '（從資料庫載入）';
            createdAt = existingQR.createdAt;
        } else {
            // Generate screenshot first
            qrStatus.textContent = '生成截圖中...';
            const screenshotBlob = await generateScreenshotBlob(sessionData);
            
            // Upload screenshot to backend
            qrStatus.textContent = '上傳截圖中...';
            shareableUrl = await uploadScreenshot(screenshotBlob, sessionData);
            
            // Generate QR code on backend and store in Redis
            qrStatus.textContent = '生成 QR 碼並存入資料庫...';
            const qrResult = await generateQRCodeOnBackend(sessionData.session_id, sessionData.player_name, shareableUrl);
            qrImageBase64 = qrResult.qrImageBase64;
            // cacheStatus = '（新生成並存入資料庫）';
            createdAt = qrResult.createdAt;
        }
        
        // Display QR code from base64 data
        qrStatus.textContent = '顯示 QR 碼...';
        
        // Create image element for QR code
        const img = document.createElement('img');
        img.src = `data:image/png;base64,${qrImageBase64}`;
        img.style.border = '1px solid #ddd';
        img.style.borderRadius = '8px';
        img.style.backgroundColor = '#ffffff';
        img.style.display = 'block';
        img.style.margin = '0 auto';
        img.style.maxWidth = '256px';
        img.style.height = 'auto';
        
        // Add the image to the container
        qrCodeContainer.appendChild(img);
        
        // Show success message with cache status
        qrStatus.textContent = `完成！掃描 QR 碼即可下載`;
        qrStatus.className = 'success';
        
        // Add timestamp information if available
        if (createdAt && qrTimestamp) {
            const timestamp = new Date(createdAt).toLocaleString('zh-TW');
            qrTimestamp.textContent = `建立時間: ${timestamp}`;
            qrTimestamp.style.display = 'block';
        }
        
        // Reset button
        qrBtn.textContent = originalText;
        qrBtn.disabled = false;
        
    } catch (error) {
        console.error('Error generating QR code:', error);
        qrStatus.textContent = `生成失敗: ${error.message}`;
        qrStatus.className = 'error';
        
        // Reset button
        qrBtn.textContent = originalText;
        qrBtn.disabled = false;
    }
}

async function generateScreenshotBlob(sessionData) {
    // Check if html2canvas is available
    if (typeof html2canvas === 'undefined') {
        throw new Error('html2canvas 庫未載入');
    }

    // Get the main score container
    const scoreContainer = document.querySelector('.score-card') || document.querySelector('.container') || document.body;
    
    // Generate screenshot
    const canvas = await html2canvas(scoreContainer, { 
        useCORS: true, 
        scale: 2, // Higher quality
        backgroundColor: '#ffffff',
        width: scoreContainer.scrollWidth,
        height: scoreContainer.scrollHeight,
        allowTaint: false,
        logging: false
    });
    
    // Convert canvas to blob
    return new Promise((resolve, reject) => {
        canvas.toBlob((blob) => {
            if (blob) {
                resolve(blob);
            } else {
                reject(new Error('無法生成截圖'));
            }
        }, 'image/png');
    });
}

// QR Code checking and generation functions
async function checkExistingQRCode(sessionId) {
    try {
        const response = await fetch(`http://localhost:8000/api/qr-code/${sessionId}`);
        if (!response.ok) {
            if (response.status === 404) {
                return { exists: false };
            }
            throw new Error(`檢查失敗: ${response.status}`);
        }
        
        const result = await response.json();
        if (result.status === 'exists') {
            return {
                exists: true,
                qrImageBase64: result.qr_image_base64,
                shareableUrl: result.shareable_url,
                createdAt: result.created_at
            };
        } else {
            return { exists: false };
        }
    } catch (error) {
        console.warn('Error checking existing QR code:', error);
        // If check fails, proceed with new generation
        return { exists: false };
    }
}

async function generateQRCodeOnBackend(sessionId, playerName, shareableUrl) {
    try {
        const formData = new FormData();
        formData.append('sessionId', sessionId);
        formData.append('playerName', playerName);
        formData.append('shareableUrl', shareableUrl);
        
        const response = await fetch('http://localhost:8000/api/generate-qr-code', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorText = await response.text();
            throw new Error(`QR 碼生成失敗: ${response.status} ${errorText}`);
        }
        
        const result = await response.json();
        if (result.status === 'success') {
            return {
                qrImageBase64: result.qr_image_base64,
                shareableUrl: result.shareable_url,
                createdAt: result.created_at,
                fromCache: result.from_cache || false
            };
        } else {
            throw new Error(result.error || 'QR 碼生成失敗');
        }
    } catch (error) {
        console.error('Error generating QR code on backend:', error);
        throw error;
    }
}

async function uploadScreenshot(blob, sessionData) {
    const formData = new FormData();
    formData.append('screenshot', blob, `quickdraw_${sessionData.player_name}_${sessionData.session_id}.png`);
    formData.append('sessionId', sessionData.session_id || 'unknown');
    formData.append('playerName', sessionData.player_name || 'unknown');
    
    const response = await fetch('http://localhost:8000/api/upload-screenshot', {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`上傳失敗: ${response.status} ${errorText}`);
    }
    
    const result = await response.json();
    if (result.status === 'success' && result.shareableUrl) {
        console.log('Screenshot uploaded successfully');
        return result.shareableUrl;
    } else {
        throw new Error(result.error || '上傳失敗');
    }
}

// Alternative function that uses the combined plots endpoint for better performance
async function populateAllWithCombinedPlots(sessionId) {
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

        // Fetch basic data and plots in parallel
        const [sessionResults, drawingsResults, plotsResults] = await Promise.allSettled([
            fetchSessionResults(sessionId),
            fetchPlayerDrawings(sessionId),
            fetchBothPlots(sessionId)
        ]);

        console.log('Plots Results:', plotsResults);
        
        // Handle session results
        if (sessionResults.status === 'fulfilled') {
            const sessionData = sessionResults.value.session || sessionResults.value;
            populateSessionInfo(sessionData);
            
            // Also handle drawings data if available for results table
            if (drawingsResults.status === 'fulfilled') {
                const drawingsData = drawingsResults.value.drawing || drawingsResults.value;
                populateResultsTable(sessionData, drawingsData);
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

        // Handle both plots
        if (plotsResults.status === 'fulfilled') {
            const plotsData = plotsResults.value;
            console.log('Both plots request fulfilled successfully');
            
            // Handle UMAP
            if (plotsData.umap && plotsData.umap.status === 'success') {
                populateUMAPVisualization(plotsData.umap);
            } else {
                if (umapLoading) {
                    let errorMessage = 'UMAP載入失敗';
                    if (plotsData.umap?.error) {
                        errorMessage += `: ${plotsData.umap.error}`;
                    }
                    umapLoading.textContent = errorMessage;
                }
            }
            
            // Handle Radar
            if (plotsData.radar && plotsData.radar.status === 'success') {
                populateRadarChart(plotsData.radar);
            } else {
                if (radarLoading) {
                    let errorMessage = '雷達圖載入失敗';
                    if (plotsData.radar?.error) {
                        errorMessage += `: ${plotsData.radar.error}`;
                    }
                    radarLoading.textContent = errorMessage;
                }
            }
        } else {
            console.error('Both plots request failed:', plotsResults.reason);
            if (umapLoading) umapLoading.textContent = 'UMAP載入失敗';
            if (radarLoading) radarLoading.textContent = '雷達圖載入失敗';
        }

    } catch (error) {
        const playerInfo = document.getElementById('playerInfo');
        const resultsBody = document.getElementById('resultsBody');
        if (playerInfo) playerInfo.innerHTML = '載入錯誤';
        if (resultsBody) resultsBody.innerHTML = '<tr><td colspan="5">資料處理錯誤</td></tr>';
    }
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
                // Setup screenshot download and QR code
                setTimeout(() => {
                    setupScreenshotDownload(sessionData, drawingsData);
                    setupQRDownload(sessionData, drawingsData);
                }, 1000);
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
    const useCombinedApi = urlParams.get('combined') !== 'true'; // Default to true
    
    if (sessionId) {
        // if (useCombinedApi) {
        //     console.log('Using combined plots API for better performance');
        //     populateAllWithCombinedPlots(sessionId);
        // } else {
            console.log('Using separate API calls');
            populateAll(sessionId);
        // }
    } else if (window.scoreData) {
        // Handle legacy data if needed
        const sessionData = window.scoreData.session;
        const drawingsData = window.scoreData.drawings;
        
        populateSessionInfo(sessionData);
        populateResultsTable(sessionData, drawingsData);
        populatePlayerDrawings(drawingsData);
        // Setup screenshot download and QR code
        setTimeout(() => {
            setupScreenshotDownload(sessionData, drawingsData);
            setupQRDownload(sessionData, drawingsData);
        }, 1000);
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
    // Log library availability on page load
    console.log('Page loaded, checking libraries...');
    console.log('html2canvas available:', typeof html2canvas !== 'undefined');
    console.log('qrcode available:', typeof QRCode !== 'undefined');
    
    loadResults();
});
