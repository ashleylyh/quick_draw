import { toZh } from './utils.js';

'use strict';
// ===== Constants =====
const CANVAS_SIDE = 280;        // larger canvas for better drawing
const TIME_LIMIT_SEC = 20;
const TIME_LIMIT_MS = TIME_LIMIT_SEC * 1000;
const TOP_SHOW = 3;
const NUM_ROUNDS = 6;
const BRUSH_WEIGHT = 10;
const API_BASE = window.CONFIG.API_BASE;

// ===== State =====
let cnv;
let sessionId;
let playerName = '';
let playerGender = '';
let playerAge = '';
let difficulty = 'easy';  // Fixed: changed from 'simple' to 'easy' to match form values
let roundIdx = 0;
let currentPrompt = '';
let activeRounds = [];
let activePrompts = [];
let timerId = null;
let previewId = null;
let timeLeftMs = TIME_LIMIT_MS;
let drawStartAt = 0;
let locked = false;
const logs = [];

// ===== Real-time variables =====
let realTimeConnected = false;
// let apiClient;
let realTimeManager;

// ===== DOM helpers =====
const $ = id => document.getElementById(id);

// Initialize real-time features when available
function initializeRealTime() {
  if (window.realTimeManager) {
    realTimeManager = window.realTimeManager;
    // apiClient = window.apiClient;
    
    // Setup event handlers
    realTimeManager.onGameEvent = handleGameEvent;
    realTimeManager.onConnectionChange = handleConnectionChange;
    
    // Connect to SSE for general events
    realTimeManager.connectSSE();
    
    console.log('Real-time features initialized');
  } else {
    console.warn('Real-time features not available, falling back to polling');
  }
}

// Handle real-time game events
function handleGameEvent(event) {
  console.log('Received game event:', event);
  
  switch (event.event_type) {
    case 'game_session_completed':
      if (event.session_id === sessionId) {
        showNotification('遊戲完成！結果已更新', 'success');
      }
      break;
      
    case 'game_round_completed':
      if (event.session_id === sessionId) {
        showNotification(`第 ${event.data.round} 題已提交`, 'info');
      }
      break;
  }
}

// Handle connection status changes
function handleConnectionChange(connected) {
  realTimeConnected = connected;
  updateConnectionStatus();
}

// Update connection status indicator
function updateConnectionStatus() {
  // This will be handled by the connection indicator in realtime.js
  console.log(`Real-time connection: ${realTimeConnected ? 'Connected' : 'Disconnected'}`);
}

// Show notification to user
function showNotification(message, type = 'info') {
  // Create notification element
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.style.cssText = `
    position: fixed;
    top: 60px;
    right: 10px;
    padding: 12px 16px;
    border-radius: 4px;
    color: white;
    font-size: 14px;
    z-index: 1001;
    max-width: 300px;
    word-wrap: break-word;
    animation: slideIn 0.3s ease;
  `;
  
  // Set background color based on type
  const colors = {
    success: '#4CAF50',
    error: '#f44336',
    warning: '#ff9800',
    info: '#2196F3'
  };
  notification.style.backgroundColor = colors[type] || colors.info;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  // Auto remove after 4 seconds
  setTimeout(() => {
    if (notification.parentNode) {
      notification.style.animation = 'slideOut 0.3s ease';
      setTimeout(() => notification.remove(), 300);
    }
  }, 4000);
}

// Add CSS animation for notifications
if (!document.getElementById('notification-styles')) {
  const style = document.createElement('style');
  style.id = 'notification-styles';
  style.textContent = `
    @keyframes slideIn {
      from { transform: translateX(100%); opacity: 0; }
      to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
      from { transform: translateX(0); opacity: 1; }
      to { transform: translateX(100%); opacity: 0; }
    }
  `;
  document.head.appendChild(style);
}

// Make showNotification globally available
window.showNotification = showNotification;

// Isolate form inputs from p5's global event handlers
function isolateInputs() {
  const inputs = document.querySelectorAll('input, button');
  inputs.forEach(el => {
    ['mousedown','touchstart','keydown'].forEach(ev => {
      el.addEventListener(ev, e => e.stopPropagation());
    });
  });
  // focus name on load
  const playerInput = $('player');
  if (playerInput) setTimeout(() => playerInput.focus(), 100);
}

// ===== View helpers =====
function showView(viewId) {
  ['view-form','view-instruct','view-draw','view-done'].forEach(v => {
    const el = $(v);
    if (!el) return;
    el.classList.toggle('active', v === viewId);
  });
  updateHeaderImageVisibility(viewId);
  updateBadgeVisibility(viewId);

}

function updateHeaderImageVisibility(viewId) {
if (viewId === 'view-form') {
  document.body.classList.add('show-header-image');
} else {
  document.body.classList.remove('show-header-image');
}
}

function updateBadgeVisibility(viewId) {
  const badges = document.querySelectorAll('.badge');
  if (viewId === 'view-form') {
    badges.forEach(b => b.remove());
  } else {
    updateBadge();
  }
}

function updateBadge() {
  const difficultyText = difficulty === 'hard' ? '困難' : '簡單';
  const genderText = playerGender === 'male' ? '男' : playerGender === 'female' ? '女' : '其他';
  const badgeText = `${playerName} (${genderText}, ${playerAge}) — ${difficultyText}`;
  ['view-instruct','view-draw','view-done'].forEach(id => {
    const view = $(id); if (!view) return;
    const old = view.querySelector('.badge'); if (old) old.remove();
    const badge = document.createElement('div');
    badge.className = 'badge';
    badge.textContent = badgeText;
    view.appendChild(badge);
  });
}

// ===== Form start =====
async function onStartForm() {
  const nameVal = ($('player')?.value || '').trim();
  const genderEl = document.querySelector('input[name="gender"]:checked');
  const ageVal = ($('age')?.value || '').trim();
  const diffEl = document.querySelector('input[name="difficulty"]:checked');

  const errs = [];
  if (!nameVal) errs.push('請填寫姓名／暱稱');
  if (!genderEl) errs.push('請選擇性別');
  if (!ageVal) errs.push('請填寫年齡');
  if (!diffEl) errs.push('請選擇挑戰難度');
  const box = $('formError');
  if (errs.length) { box && (box.textContent = errs.join('、')); return; }
  box && (box.textContent = '');

  playerName = nameVal; playerGender = genderEl.value; playerAge = ageVal; difficulty = diffEl.value;

  try {
    // Show loading indicator
    const startBtn = $('startBtn');
    if (startBtn) {
      startBtn.disabled = true;
      startBtn.textContent = '啟動中...';
    }
    
    // Use simple fetch to the original API
    let data;
    const resp = await fetch(`${API_BASE}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        player_name: playerName, 
        gender: playerGender, 
        age: parseInt(playerAge), 
        difficulty 
      })
    });
    if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
    data = await resp.json();
    
    sessionId = data.session_id;
    activeRounds = data.rounds || [];
    activePrompts = data.prompts || [];
    roundIdx = 0;
    logs.length = 0;
    
    // Connect to real-time features for this session
    if (realTimeManager && sessionId) {
      realTimeManager.connectWebSocket(sessionId);
      showNotification('遊戲開始！已連接即時更新', 'success');
    }
    
    updateBadge();
    applyRound(roundIdx);
    showView('view-instruct');
    
  } catch (err) {
    console.error('Session creation error:', err);
    const errorMsg = err.message || '遊戲啟動失敗，請檢查網路或重試';
    box && (box.textContent = errorMsg);
    showNotification(errorMsg, 'error');
  } finally {
    // Reset button state
    const startBtn = $('startBtn');
    if (startBtn) {
      startBtn.disabled = false;
      startBtn.textContent = '填寫完成，開始挑戰！';
    }
  }
}

function applyRound(idx) {
  if (!activeRounds?.length || idx >= activeRounds.length) return;
  currentPrompt = activePrompts[idx];
  const instrEl = $('prompt'); if (instrEl) instrEl.textContent = `第 ${idx + 1} 題：請畫出「${toZh(currentPrompt)}」`;
  const drawEl = $('drawPrompt'); if (drawEl) drawEl.textContent = `請畫出「${toZh(currentPrompt)}」`;
  if (typeof background === 'function') background(255);
  const resEl = $('res'); if (resEl) resEl.innerHTML = '';
  const tu = $('timeUpMsg'); if (tu) tu.style.display = 'none';
  locked = false; timeLeftMs = TIME_LIMIT_MS;
}

function startDrawing() {
  drawStartAt = Date.now(); timeLeftMs = TIME_LIMIT_MS; locked = false;
  const resEl = $('res'); if (resEl) resEl.innerHTML = '';
  updateTimer();
  if (timerId) clearInterval(timerId); timerId = setInterval(updateTimer, 100);
  if (previewId) clearInterval(previewId); previewId = setInterval(previewPredict, 3000);
  showView('view-draw');
}

function updateTimer() {
  const now = Date.now(); const elapsed = now - drawStartAt; timeLeftMs = Math.max(0, TIME_LIMIT_MS - elapsed);
  const t = $('timer'); if (t) {
    const sec = (timeLeftMs/1000).toFixed(1);
    t.textContent = `時間倒計時：還剩下 ${sec} 秒`;
    const sInt = Math.ceil(timeLeftMs/1000);
    if (sInt <= 5) { t.style.color = 'var(--red)'; t.style.fontWeight = '800'; }
    else if (sInt <= 10) { t.style.color = 'var(--orange)'; t.style.fontWeight = '700'; }
    else { t.style.color = 'var(--text)'; t.style.fontWeight = '700'; }
  }
  if (timeLeftMs <= 0) {
    clearInterval(timerId); timerId = null; locked = true; const msg = $('timeUpMsg'); if (msg) msg.style.display = 'block';
  }
}

function getInputImageAsBase64() {
  if (!cnv) return null;
  const canvas = cnv.elt; const temp = document.createElement('canvas');
  temp.width = 28; temp.height = 28; const tctx = temp.getContext('2d');
  tctx.fillStyle = '#fff'; tctx.fillRect(0,0,28,28);
  tctx.drawImage(canvas, 0, 0, 28, 28);
  return temp.toDataURL('image/png');
}

async function previewPredict() {
  if (locked) return; 
  const resEl = $('res'); 
  if (!resEl) return;
  
  try {
    const imageData = getInputImageAsBase64();
    if (!imageData) { 
      resEl.innerHTML = '即時預覽：請開始繪畫...'; 
      return; 
    }
    
    const roundChoices = activeRounds[roundIdx] || [];
    
    // Use enhanced API client if available
  let result;

    // Fallback to direct fetch
    const resp = await fetch(`${API_BASE}/predict-realtime`, {
      method: 'POST', 
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_data: imageData, choices: roundChoices })
    });
    if (!resp.ok) { 
      resEl.innerHTML = '即時預覽：分析中...'; 
      return; 
    }
    result = await resp.json();
  
    
    if (result.success && result.predictions) {
      const sorted = Object.entries(result.predictions)
        .map(([name,p])=>({name,p}))
        .sort((a,b)=>b.p-a.p);
      const top3 = sorted.slice(0,3);
      
      if (top3.length) {
        const predictionText = top3
          .map(t=>`${toZh(t.name)} ${(t.p*100).toFixed(1)}%`)
          .join('，');
        resEl.innerHTML = `即時：${predictionText}`;
        
        // Add visual feedback for high confidence predictions
        const topConfidence = top3[0]?.p || 0;
        if (topConfidence > 0.8) {
          resEl.style.color = 'var(--success, #4CAF50)';
          resEl.style.fontWeight = 'bold';
        } else if (topConfidence > 0.5) {
          resEl.style.color = 'var(--warning, #ff9800)';
          resEl.style.fontWeight = 'normal';
        } else {
          resEl.style.color = 'var(--text)';
          resEl.style.fontWeight = 'normal';
        }
      } else {
        resEl.innerHTML = '即時預覽：繪圖中...';
      }
    } else {
      resEl.innerHTML = '即時預覽：分析中...';
    }
  } catch (e) {
    console.error('Preview prediction error:', e); 
    resEl.innerHTML = '即時預覽：繪圖中...';
    
    // Show error notification for critical failures
    if (e.message.includes('Rate limit') || e.message.includes('429')) {
      showNotification('預測請求過於頻繁，請稍候', 'warning');
    }
  }
}

function getOriginalCanvasAsBase64() {
    const canvas = cnv ? cnv.elt : document.querySelector('canvas');
    return canvas ? canvas.toDataURL('image/png') : null;
}

async function submitAnswer() {
  if (previewId) { clearInterval(previewId); previewId = null; }
  if (timerId) { clearInterval(timerId); timerId = null; }

  const spentSec = Math.max(0, (Date.now() - drawStartAt) / 1000);
  const timedOut = timeLeftMs <= 0 ? 1 : 0;

  try {
    // Get base64 image data (same processing as previewPredict)
    const imageData = getInputImageAsBase64();
    if (!imageData) throw new Error('Failed to get image data');

    // Get original canvas image as base64 for visualization
    const originalImageData = getOriginalCanvasAsBase64();
    if (!originalImageData) throw new Error('Failed to get original image data');

    // Create JSON payload for the BaseModel API
    const requestData = {
      session_id: sessionId,
      round: roundIdx + 1, // NOTE: backend expects 1-based round index
      prompt: currentPrompt,
      time_spent_sec: parseFloat(spentSec.toFixed(2)),
      timed_out: timedOut,
      drawing: imageData, // base64 data URL
      original_image_data: originalImageData // base64 data URL
    };

    const resEl = $('res'); if (resEl) resEl.innerHTML = '正在分析您的繪圖...';
    const resp = await fetch(`${API_BASE}/predict`, { 
      method: 'POST', 
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestData)
    });
    if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
    const result = await resp.json();

    const probsMap = result.predictions || {}; // server-side candidate-renorm
    const sorted = Object.entries(probsMap).map(([name,p])=>({name,p})).sort((a,b)=>b.p-a.p);
    const top = sorted.slice(0, TOP_SHOW);
    if (resEl) resEl.innerHTML = top.length ? ('Top-3: ' + top.map(t=>`${toZh(t.name)} ${(t.p*100).toFixed(1)}%`).join('，')) : '（無結果）';

    logs.push({ session_id: sessionId, player_name: playerName, gender: playerGender, age: playerAge, difficulty,
      round: roundIdx + 1, prompt: currentPrompt, time_spent_sec: spentSec.toFixed(2), timed_out: timedOut,
      probs_map: probsMap, embedding: result.embedding || [], timestamp: new Date().toISOString() });

    if (roundIdx < NUM_ROUNDS - 1) {
      roundIdx += 1; if (typeof background === 'function') background(255);
      if (resEl) resEl.innerHTML = '';
      const tu = $('timeUpMsg'); if (tu) tu.style.display = 'none';
      locked = false; timeLeftMs = TIME_LIMIT_MS; applyRound(roundIdx); showView('view-instruct');
    } else {
      showView('view-done');
      const btn = $('download'); if (btn) { btn.textContent = '點擊查看成績以及說明'; btn.onclick = openResultsPage; }
    }
  } catch (e) {
    console.error(e); const resEl = $('res'); if (resEl) resEl.innerHTML = '提交失敗，請重試';
  }
}

async function openResultsPage() {
  try {
    // Simply open score.html with sessionId parameter
    const w = window.open(`score.html?sessionId=${sessionId}`, '_blank');
    if (!w) { 
      alert('請允許彈出視窗以查看成績'); 
      return; 
    }
  } catch (e) { 
    console.error(e); 
    alert('無法載入成績頁面，請重試'); 
  }
}

// ===== Restart =====
window.restartGame = function restartGame() {
  try { if (timerId) clearInterval(timerId); } catch(_){}
  try { if (previewId) clearInterval(previewId); } catch(_){}
  timerId = null; previewId = null; locked = false; timeLeftMs = TIME_LIMIT_MS; roundIdx = 0; currentPrompt = '';
  if (typeof background === 'function') background(255);
  const resEl = $('res'); if (resEl) resEl.innerHTML = '';
  const tu = $('timeUpMsg'); if (tu) tu.style.display = 'none';
  if ($('player')) $('player').value = ''; if ($('age')) $('age').value = '';
  document.querySelectorAll('input[name="gender"]:checked').forEach(g=>g.checked=false);
  document.querySelectorAll('input[name="difficulty"]:checked').forEach(d=>d.checked=false);
  playerName = ''; playerGender = ''; playerAge = ''; difficulty = 'easy';
  activeRounds = []; activePrompts = []; logs.length = 0;
  sessionId = Date.now().toString(36) + Math.random().toString(36).slice(2, 9);
  showView('view-form');
}

// ===== p5 hooks =====
window.setup = function setup() {
  pixelDensity(1);
  cnv = createCanvas(CANVAS_SIDE, CANVAS_SIDE);
  background(255);
  cnv.parent('canvasContainer');

  const sb = document.getElementById('startBtn'); sb && sb.addEventListener('click', e => { e.preventDefault(); onStartForm(); });
  const ok = document.getElementById('instrOk'); ok && ok.addEventListener('click', startDrawing);
  const cl = document.getElementById('clearBtn'); cl && cl.addEventListener('click', () => { if (!locked) background(255); });
  const sub = document.getElementById('submitBtn'); sub && sub.addEventListener('click', submitAnswer);

  showView('view-form');
  isolateInputs();
}

window.draw = function draw() {
  if (locked) return;
  strokeWeight(BRUSH_WEIGHT); stroke(0);
  if (mouseIsPressed) line(pmouseX, pmouseY, mouseX, mouseY);
}
window.mousePressed = function mousePressed() {
  if (mouseX >= 0 && mouseX < width && mouseY >= 0 && mouseY < height && !locked) { stroke(0); strokeWeight(BRUSH_WEIGHT); point(mouseX, mouseY); return false; }
}
window.mouseDragged = function mouseDragged() {
  if (mouseX >= 0 && mouseX < width && mouseY >= 0 && mouseY < height && !locked) { stroke(0); strokeWeight(BRUSH_WEIGHT); line(pmouseX, pmouseY, mouseX, mouseY); return false; }
}
window.touchMoved = function touchMoved() {
  if (touchX >= 0 && touchX < width && touchY >= 0 && touchY < height && !locked) { stroke(0); strokeWeight(BRUSH_WEIGHT); line(ptouchX, ptouchY, touchX, touchY); return false; }
}

// ===== Initialize real-time features when DOM is ready =====
document.addEventListener('DOMContentLoaded', () => {
  // Wait a bit for realtime.js to load
  setTimeout(initializeRealTime, 100);
});

// Also initialize when the window loads (fallback)
window.addEventListener('load', () => {
  setTimeout(initializeRealTime, 100);
});
