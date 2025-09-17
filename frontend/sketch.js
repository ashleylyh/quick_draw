import { toZh } from './utils.js';

'use strict';
// ===== Constants =====
const CANVAS_SIDE = 280;        // larger canvas for better drawing
const TIME_LIMIT_SEC = 20;
const TIME_LIMIT_MS = TIME_LIMIT_SEC * 1000;
const TOP_SHOW = 3;
const NUM_ROUNDS = 6;
const BRUSH_WEIGHT = 10;
const API_BASE = 'http://localhost:8000/api';

// ===== State =====
let cnv;
let sessionId;
let playerName = '';
let playerGender = '';
let playerAge = '';
let difficulty = 'simple';
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

// ===== DOM helpers =====
const $ = id => document.getElementById(id);

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
    const resp = await fetch(`${API_BASE}/sessions`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ player_name: playerName, gender: playerGender, age: parseInt(playerAge), difficulty })
    });
    if (!resp.ok) throw new Error(`Server error: ${resp.status}`);
    const data = await resp.json();
    sessionId = data.session_id; activeRounds = data.rounds || []; activePrompts = data.prompts || [];
    roundIdx = 0; logs.length = 0;
    updateBadge(); applyRound(roundIdx); showView('view-instruct');
  } catch (err) {
    console.error(err); box && (box.textContent = '遊戲啟動失敗，請檢查網路或重試');
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
  if (previewId) clearInterval(previewId); previewId = setInterval(previewPredict, 900);
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
  if (locked) return; const resEl = $('res'); if (!resEl) return;
  try {
    const imageData = getInputImageAsBase64();
    if (!imageData) { resEl.innerHTML = '即時預覽：請開始繪畫...'; return; }
    const roundChoices = activeRounds[roundIdx] || [];
    const resp = await fetch(`${API_BASE}/predict-realtime`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ image_data: imageData, choices: roundChoices })
    });
    if (!resp.ok) { resEl.innerHTML = '即時預覽：分析中...'; return; }
    const result = await resp.json();
    if (result.success && result.predictions) {
      const sorted = Object.entries(result.predictions).map(([name,p])=>({name,p})).sort((a,b)=>b.p-a.p);
      const top3 = sorted.slice(0,3);
      resEl.innerHTML = top3.length ? ('即時：' + top3.map(t=>`${toZh(t.name)} ${(t.p*100).toFixed(1)}%`).join('，')) : '即時預覽：繪圖中...';
    } else {
      resEl.innerHTML = '即時預覽：分析中...';
    }
  } catch (e) {
    console.error(e); resEl.innerHTML = '即時預覽：繪圖中...';
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
    // Use the SAME image processing as previewPredict
    const imageData = getInputImageAsBase64();
    if (!imageData) throw new Error('Failed to get image data');
    // Convert base64 data URL to blob (same format as before for backend compatibility)
    const response = await fetch(imageData);
    const blob = await response.blob();

    // Get original canvas image as base64 for visualization
    const originalImageData = getOriginalCanvasAsBase64();
    if (!originalImageData) throw new Error('Failed to get original image data');
    // Convert base64 data URL to blob (same format as before for backend compatibility)
    const originalResponse = await fetch(originalImageData);
    const originalBlob = await originalResponse.blob();


    const formData = new FormData();
    formData.append('session_id', sessionId);
    // NOTE: backend currently expects 1-based round index
    formData.append('round', String(roundIdx + 1));
    formData.append('prompt', currentPrompt);
    formData.append('time_spent_sec', spentSec.toFixed(2));
    formData.append('timed_out', String(timedOut));
    formData.append('drawing', blob, `${sessionId}_round${roundIdx+1}_${currentPrompt}.png`);
    formData.append('original_image_data', originalBlob, `${sessionId}_round${roundIdx+1}_${currentPrompt}_original.png`);

    const resEl = $('res'); if (resEl) resEl.innerHTML = '正在分析您的繪圖...';
    const resp = await fetch(`${API_BASE}/predict`, { method: 'POST', body: formData });
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
  playerName = ''; playerGender = ''; playerAge = ''; difficulty = 'simple';
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
