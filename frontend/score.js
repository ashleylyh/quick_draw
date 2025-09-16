import {toZh, formatTimestamp, buildCSVFromData } from './utils.js';

// Import jsPDF and html2canvas from CDN (will be loaded in HTML)
// These will be available as global variables: jsPDF and html2canvas

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
        &emsp;&emsp;
        <span class="player-label">難度：</span>
        <span class="player-value">${sessionData.difficulty === 'hard' ? '困難' : '簡單'}</span>
        &emsp;&emsp;
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
        const fileName = `quickdraw_score_${sessionData.player_name}_${new Date().toISOString().slice(0, 10)}.png`;
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

function setupPDFDownload(sessionData, drawingsData) {
    const downloadPdfBtn = document.getElementById('downloadPdfBtn');
    if (!downloadPdfBtn) return;
    
    downloadPdfBtn.textContent = '下載 PDF 報告';
    downloadPdfBtn.href = '#';
    downloadPdfBtn.removeAttribute('download');
    
    downloadPdfBtn.addEventListener('click', async function(e) {
        e.preventDefault();
        await generatePDFReport(sessionData, drawingsData);
    });
}

async function generatePDFReport(sessionData, drawingsData) {
    try {
        // Check if jsPDF and html2canvas are available
        if (typeof html2canvas === 'undefined') {
            alert('html2canvas 庫未載入，請重新整理頁面後再試');
            return;
        }
        
        // Check for jsPDF in different possible locations
        let jsPDF;
        if (window.jspdf && window.jspdf.jsPDF) {
            jsPDF = window.jspdf.jsPDF;
        } else if (window.jsPDF) {
            jsPDF = window.jsPDF;
        } else {
            alert('jsPDF 庫未載入，請重新整理頁面後再試');
            return;
        }

        // Show loading indicator
        const downloadPdfBtn = document.getElementById('downloadPdfBtn');
        const originalText = downloadPdfBtn.textContent;
        downloadPdfBtn.textContent = '生成中...';
        downloadPdfBtn.disabled = true;

        const pdf = new jsPDF('p', 'mm', 'a4');
        
        // Try to load Chinese font
        try {
            // Try local font file first
            let fontResponse;
            try {
                fontResponse = await fetch('./fonts/NotoSansTC.ttf');
            } catch (e) {
                // If local fails, try from backend
                return;
            }
            
            if (fontResponse.ok) {
                const fontData = await fontResponse.arrayBuffer();
                const fontBase64 = btoa(String.fromCharCode(...new Uint8Array(fontData)));
                pdf.addFileToVFS('./fonts/NotoSansTC.ttf', fontBase64);
                pdf.addFont('./fonts/NotoSansTC.ttf', 'NotoSansTC', 'normal');
                pdf.setFont('NotoSansTC');
                console.log('Chinese font loaded successfully');
            } else {
                throw new Error('Font file not found');
            }
        } catch (error) {
            console.warn('Failed to load Chinese font, using default font:', error);
            // Fallback to helvetica - Chinese characters may not display correctly
            pdf.setFont('helvetica');
        }
        
        
        // Page 1: Summary and Results Table
        await addHeaderToPDF(pdf, sessionData);
        await addResultsTableToPDF(pdf, sessionData, drawingsData);
        
        // Page 2: Player Drawings
        pdf.addPage();
        await addPlayerDrawingsToPDF(pdf, drawingsData);
        
        // Page 3: Visualizations
        pdf.addPage();
        await addVisualizationsToPDF(pdf);
        
        // Save the PDF
        const fileName = `quickdraw_report_${sessionData.player_name}_${new Date().toISOString().slice(0, 10)}.pdf`;
        pdf.save(fileName);
        
        // Reset button
        downloadPdfBtn.textContent = originalText;
        downloadPdfBtn.disabled = false;
        
    } catch (error) {
        console.error('Error generating PDF:', error);
        alert('PDF 生成失敗，請再試一次');
        
        // Reset button
        const downloadPdfBtn = document.getElementById('downloadPdfBtn');
        downloadPdfBtn.textContent = '下載 PDF 報告';
        downloadPdfBtn.disabled = false;
    }
}

async function addHeaderToPDF(pdf, sessionData) {
    // Title
    pdf.setFontSize(20);
    // Try to use Chinese font, fallback to helvetica
    try {
        pdf.setFont('./fonts/NotoSansTC', 'bold');
    } catch (e) {
        pdf.setFont('helvetica', 'bold');
    }
    pdf.text('QuickDraw 成績報告', 105, 20, { align: 'center' });
    
    // Player info
    pdf.setFontSize(12);
    try {
        pdf.setFont('./fonts/NotoSansTC', 'normal');
    } catch (e) {
        pdf.setFont('helvetica', 'normal');
    }
    
    let formattedTime = '未知時間';
    if (sessionData.timestamp) {
        try {
            formattedTime = formatTimestamp(sessionData.timestamp);
        } catch (error) {
            formattedTime = sessionData.timestamp;
        }
    }
    
    const playerName = sessionData.player_name || '未知';
    const difficulty = sessionData.difficulty === 'hard' ? '困難' : '簡單';
    
    pdf.text(`參賽者：${playerName}`, 20, 35);
    pdf.text(`難度：${difficulty}`, 20, 45);
    pdf.text(`時間：${formattedTime}`, 20, 55);
    
    return 65; // Return next Y position
}

async function addResultsTableToPDF(pdf, sessionData, drawingsData) {
    let y = 75;
    
    // Table title
    pdf.setFontSize(14);
    try {
        pdf.setFont('./fonts/NotoSansTC', 'bold');
    } catch (e) {
        pdf.setFont('helvetica', 'bold');
    }
    pdf.text('遊戲結果', 20, y);
    y += 15;
    
    // Table headers
    pdf.setFontSize(10);
    try {
        pdf.setFont('./fonts/NotoSansTC', 'bold');
    } catch (e) {
        pdf.setFont('helvetica', 'bold');
    }
    const headers = ['題次', '指定', 'TOP1', '耗時', '逾時', '正確', '分數'];
    const colWidths = [20, 30, 45, 20, 20, 20, 25];
    let x = 20;
    
    headers.forEach((header, i) => {
        pdf.text(header, x, y);
        x += colWidths[i];
    });
    y += 10;
    
    // Table data
    try {
        pdf.setFont('./fonts/NotoSansTC', 'normal');
    } catch (e) {
        pdf.setFont('helvetica', 'normal');
    }
    let totalScore = 0;
    
    if (drawingsData && Array.isArray(drawingsData)) {
        let sessionRounds = [];
        if (typeof sessionData.rounds === 'string') {
            try {
                sessionRounds = JSON.parse(sessionData.rounds);
            } catch (e) {
                sessionRounds = [];
            }
        } else if (Array.isArray(sessionData.rounds)) {
            sessionRounds = sessionData.rounds;
        }
        
        drawingsData.forEach(d => {
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
            const isCorrect = sorted[0] && sorted[0].name === d.prompt;
            const score = predictions[d.prompt] ? (predictions[d.prompt] * 100) : 0;
            totalScore += score;
            
            x = 20;
            const rowData = [
                d.round.toString(),
                toZh(d.prompt),
                top1.length > 20 ? top1.substring(0, 17) + '...' : top1,
                `${d.time_spent_sec}s`,
                d.timed_out ? '是' : '否',
                isCorrect ? '✓' : '✗',
                score.toFixed(1)
            ];
            
            rowData.forEach((data, i) => {
                pdf.text(data, x, y);
                x += colWidths[i];
            });
            y += 8;
            
            if (y > 270) { // If near bottom of page, add new page
                pdf.addPage();
                y = 30;
            }
        });
    }
    
    // Total score
    y += 10;
    pdf.setFontSize(14);
    try {
        pdf.setFont('./fonts/NotoSansTC', 'bold');
    } catch (e) {
        pdf.setFont('helvetica', 'bold');
    }
    pdf.text(`總分：${totalScore.toFixed(1)} 分`, 20, y);
}

async function addPlayerDrawingsToPDF(pdf, drawingsData) {
    let y = 30;
    
    // Title
    pdf.setFontSize(16);
    try {
        pdf.setFont('./fonts/NotoSansTC', 'bold');
    } catch (e) {
        pdf.setFont('helvetica', 'bold');
    }
    pdf.text('玩家繪圖', 20, y);
    y += 20;
    
    if (!drawingsData || !Array.isArray(drawingsData) || drawingsData.length === 0) {
        pdf.setFontSize(12);
        try {
            pdf.setFont('./fonts/NotoSansTC', 'normal');
        } catch (e) {
            pdf.setFont('helvetica', 'normal');
        }
        pdf.text('無繪圖資料', 20, y);
        return;
    }
    
    // Add drawings in a grid
    const imagesPerRow = 2;
    const imageWidth = 80;
    const imageHeight = 60;
    const spacing = 10;
    let col = 0;
    
    for (let i = 0; i < drawingsData.length; i++) {
        const drawing = drawingsData[i];
        const x = 20 + col * (imageWidth + spacing);
        
        // Add drawing label
        pdf.setFontSize(10);
        try {
            pdf.setFont('./fonts/NotoSansTC', 'normal');
        } catch (e) {
            pdf.setFont('helvetica', 'normal');
        }
        pdf.text(`第${drawing.round}題：${toZh(drawing.prompt)}`, x, y);
        
        try {
            // Add the drawing image
            const imageData = `data:image/png;base64,${drawing.original_image_data}`;
            pdf.addImage(imageData, 'PNG', x, y + 5, imageWidth, imageHeight);
        } catch (error) {
            console.error('Error adding image to PDF:', error);
            pdf.text('圖片載入失敗', x, y + 30);
        }
        
        col++;
        if (col >= imagesPerRow) {
            col = 0;
            y += imageHeight + 25;
            
            if (y > 200) { // If near bottom of page, add new page
                pdf.addPage();
                y = 30;
            }
        }
    }
}

async function addVisualizationsToPDF(pdf) {
    let y = 30;
    
    // Title
    pdf.setFontSize(16);
    try {
        pdf.setFont('./fonts/NotoSansTC', 'bold');
    } catch (e) {
        pdf.setFont('helvetica', 'bold');
    }
    pdf.text('數據視覺化', 20, y);
    y += 20;
    
    // UMAP Visualization
    const umapImage = document.getElementById('umapImage');
    if (umapImage && umapImage.style.display !== 'none' && umapImage.src) {
        pdf.setFontSize(12);
        try {
            pdf.setFont('./fonts/NotoSansTC', 'bold');
        } catch (e) {
            pdf.setFont('helvetica', 'bold');
        }
        pdf.text('嵌入向量視覺化 (UMAP)', 20, y);
        y += 10;
        
        try {
            // Convert image to canvas and then to PDF
            const canvas = await html2canvas(umapImage, { 
                useCORS: true, 
                scale: 1,
                backgroundColor: '#ffffff'
            });
            const imgData = canvas.toDataURL('image/png');
            pdf.addImage(imgData, 'PNG', 20, y, 170, 100);
            y += 110;
        } catch (error) {
            console.error('Error adding UMAP to PDF:', error);
            try {
                pdf.setFont('./fonts/NotoSansTC', 'normal');
            } catch (e) {
                pdf.setFont('helvetica', 'normal');
            }
            pdf.text('UMAP 圖片載入失敗', 20, y);
            y += 20;
        }
    } else {
        pdf.setFontSize(12);
        try {
            pdf.setFont('./fonts/NotoSansTC', 'normal');
        } catch (e) {
            pdf.setFont('helvetica', 'normal');
        }
        pdf.text('UMAP 視覺化不可用', 20, y);
        y += 20;
    }
    
    // Radar Chart
    const radarImage = document.getElementById('radarImage');
    if (radarImage && radarImage.style.display !== 'none' && radarImage.src) {
        pdf.setFontSize(12);
        try {
            pdf.setFont('./fonts/NotoSansTC', 'bold');
        } catch (e) {
            pdf.setFont('helvetica', 'bold');
        }
        pdf.text('繪圖準確度雷達圖', 20, y);
        y += 10;
        
        try {
            const canvas = await html2canvas(radarImage, { 
                useCORS: true, 
                scale: 1,
                backgroundColor: '#ffffff'
            });
            const imgData = canvas.toDataURL('image/png');
            pdf.addImage(imgData, 'PNG', 20, y, 170, 100);
        } catch (error) {
            console.error('Error adding radar chart to PDF:', error);
            try {
                pdf.setFont('./fonts/NotoSansTC', 'normal');
            } catch (e) {
                pdf.setFont('helvetica', 'normal');
            }
            pdf.text('雷達圖載入失敗', 20, y);
        }
    } else {
        pdf.setFontSize(12);
        try {
            pdf.setFont('./fonts/NotoSansTC', 'normal');
        } catch (e) {
            pdf.setFont('helvetica', 'normal');
        }
        pdf.text('雷達圖不可用', 20, y);
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
                // Setup both screenshot and PDF download
                setTimeout(() => {
                    setupScreenshotDownload(sessionData, drawingsData);
                    setupPDFDownload(sessionData, drawingsData);
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
        // Setup both screenshot and PDF download
        setTimeout(() => {
            setupScreenshotDownload(sessionData, drawingsData);
            setupPDFDownload(sessionData, drawingsData);
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
    console.log('jsPDF available:', typeof window.jsPDF !== 'undefined');
    console.log('jspdf available:', typeof window.jspdf !== 'undefined');
    
    loadResults();
});