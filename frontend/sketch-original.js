// === 基本參數 ===
const IMAGE_SIZE = 784;          // 28*28
const PER_ROUND = 4;             // 每回合 4 個候選
const NUM_ROUNDS = 6;            // 共 6 題
const TIME_LIMIT_SEC = 20;       // 每題 20 秒
const TIME_LIMIT_MS = TIME_LIMIT_SEC * 1000;
const TOP_SHOW = 3;              // 顯示前 3 名
const BRUSH_WEIGHT = 12.5;          // 畫筆粗細（可自由調整）
const CANVAS_SIDE  = 350;         // 畫布邊長（想放大就改這裡，如 640、768）
// 顯示前 3 名

// 檔案上傳伺服器（請確認此伺服器允許 CORS 與 PUT/POST 上傳）
const SERVER_BASE = 'http://140.109.74.39:8000/YunJer_in_Data/Task5_openhouse/Test1_doodle_Net/demo/DoodleClassifier_345/game_record';

// === 365 類（順序需與模型輸出一致） ===
const CLASSES = ['flashlight','belt','mushroom','pond','strawberry','pineapple','sun','cow','ear','bush','pliers','watermelon','apple','baseball','feather','shoe','leaf','lollipop','crown','ocean','horse','mountain','mosquito','mug','hospital','saw','castle','angel','underwear','traffic_light','cruise_ship','marker','blueberry','flamingo','face','hockey_stick','bucket','campfire','asparagus','skateboard','door','suitcase','skull','cloud','paint_can','hockey_puck','steak','house_plant','sleeping_bag','bench','snowman','arm','crayon','fan','shovel','leg','washing_machine','harp','toothbrush','tree','bear','rake','megaphone','knee','guitar','calculator','hurricane','grapes','paintbrush','couch','nose','square','wristwatch','penguin','bridge','octagon','submarine','screwdriver','rollerskates','ladder','wine_bottle','cake','bracelet','broom','yoga','finger','fish','line','truck','snake','bus','stitches','snorkel','shorts','bowtie','pickup_truck','tooth','snail','foot','crab','school_bus','train','dresser','sock','tractor','map','hedgehog','coffee_cup','computer','matches','beard','frog','crocodile','bathtub','rain','moon','bee','knife','boomerang','lighthouse','chandelier','jail','pool','stethoscope','frying_pan','cell_phone','binoculars','purse','lantern','birthday_cake','clarinet','palm_tree','aircraft_carrier','vase','eraser','shark','skyscraper','bicycle','sink','teapot','circle','tornado','bird','stereo','mouth','key','hot_dog','spoon','laptop','cup','bottlecap','The_Great_Wall_of_China','The_Mona_Lisa','smiley_face','waterslide','eyeglasses','ceiling_fan','lobster','moustache','carrot','garden','police_car','postcard','necklace','helmet','blackberry','beach','golf_club','car','panda','alarm_clock','t-shirt','dog','bread','wine_glass','lighter','flower','bandage','drill','butterfly','swan','owl','raccoon','squiggle','calendar','giraffe','elephant','trumpet','rabbit','trombone','sheep','onion','church','flip_flops','spreadsheet','pear','clock','roller_coaster','parachute','kangaroo','duck','remote_control','compass','monkey','rainbow','tennis_racquet','lion','pencil','string_bean','oven','star','cat','pizza','soccer_ball','syringe','flying_saucer','eye','cookie','floor_lamp','mouse','toilet','toaster','The_Eiffel_Tower','airplane','stove','cello','stop_sign','tent','diving_board','light_bulb','hammer','scorpion','headphones','basket','spider','paper_clip','sweater','ice_cream','envelope','sea_turtle','donut','hat','hourglass','broccoli','jacket','backpack','book','lightning','drums','snowflake','radio','banana','camel','canoe','toothpaste','chair','picture_frame','parrot','sandwich','lipstick','pants','violin','brain','power_outlet','triangle','hamburger','dragon','bulldozer','cannon','dolphin','zebra','animal_migration','camouflage','scissors','basketball','elbow','umbrella','windmill','table','rifle','hexagon','potato','anvil','sword','peanut','axe','television','rhinoceros','baseball_bat','speedboat','sailboat','zigzag','garden_hose','river','house','pillow','ant','tiger','stairs','cooler','see_saw','piano','fireplace','popsicle','dumbbell','mailbox','barn','hot_tub','teddy-bear','fork','dishwasher','peas','hot_air_balloon','keyboard','microwave','wheel','fire_hydrant','van','camera','whale','candle','octopus','pig','swing_set','helicopter','saxophone','passport','bat','ambulance','diamond','goatee','fence','grass','mermaid','motorbike','microphone','toe','cactus','nail','telephone','hand','squirrel','streetlight','bed','firetruck'];

// ====== 簡單模式：多欄組合清單（每行一組候選；空白/Tab 分隔） ======
const POOL_TEXT = `
eyeglasses	bus	crab	camera	lollipop	ice_cream
eyeglasses	bus	crab	map	lollipop	ice_cream
eyeglasses	car	crab	camera	lollipop	ice_cream
eyeglasses	car	crab	map	lollipop	ice_cream
eyeglasses	bus	crab	camera	donut	hot_air_balloon
eyeglasses	bus	crab	map	donut	hot_air_balloon
eyeglasses	car	crab	camera	donut	hot_air_balloon
eyeglasses	car	crab	map	donut	hot_air_balloon
eyeglasses	bus	calculator	octopus	lollipop	ice_cream
eyeglasses	car	calculator	octopus	lollipop	ice_cream
eyeglasses	bus	calculator	octopus	donut	hot_air_balloon
eyeglasses	car	calculator	octopus	donut	hot_air_balloon
eyeglasses	bus	clock	camera	lollipop	helicopter
eyeglasses	bus	clock	map	lollipop	helicopter
eyeglasses	car	clock	camera	lollipop	helicopter
eyeglasses	car	clock	map	lollipop	helicopter
eyeglasses	envelope	crab	ambulance	lollipop	ice_cream
eyeglasses	envelope	crab	ambulance	donut	hot_air_balloon
eyeglasses	envelope	clock	octopus	lollipop	police_car
eyeglasses	envelope	clock	ambulance	lollipop	helicopter
eyeglasses	strawberry	crab	camera	lollipop	police_car
eyeglasses	strawberry	crab	map	lollipop	police_car
eyeglasses	strawberry	calculator	octopus	lollipop	police_car
eyeglasses	strawberry	calculator	ambulance	lollipop	helicopter
tree	bus	camel	camera	donut	helicopter
tree	bus	camel	map	donut	helicopter
tree	car	camel	camera	donut	helicopter
tree	car	camel	map	donut	helicopter	
umbrella	bus	camel	camera	donut	helicopter
umbrella	bus	camel	map	donut	helicopter
umbrella	car	camel	camera	donut	helicopter
umbrella	car	camel	map	donut	helicopter
tree	bus	crab	camera	bicycle	ice_cream
tree	bus	crab	camera	see_saw	ice_cream
tree	bus	crab	map	bicycle	ice_cream
tree	bus	crab	map	see_saw	ice_cream
tree	car	crab	camera	bicycle	ice_cream
tree	car	crab	camera	see_saw	ice_cream
tree	car	crab	map	bicycle	ice_cream
tree	car	crab	map	see_saw	ice_cream
umbrella	bus	crab	camera	bicycle	ice_cream
umbrella	bus	crab	camera	see_saw	ice_cream
umbrella	bus	crab	map	bicycle	ice_cream
umbrella	bus	crab	map	see_saw	ice_cream
umbrella	car	crab	camera	bicycle	ice_cream
umbrella	car	crab	camera	see_saw	ice_cream
umbrella	car	crab	map	bicycle	ice_cream
umbrella	car	crab	map	see_saw	ice_cream
tree	bus	calculator	octopus	bicycle	ice_cream
tree	bus	calculator	octopus	see_saw	ice_cream
tree	car	calculator	octopus	bicycle	ice_cream
tree	car	calculator	octopus	see_saw	ice_cream
umbrella	bus	calculator	octopus	bicycle	ice_cream
umbrella	bus	calculator	octopus	see_saw	ice_cream
umbrella	car	calculator	octopus	bicycle	ice_cream
umbrella	car	calculator	octopus	see_saw	ice_cream
tree	bus	clock	camera	bicycle	helicopter
tree	bus	clock	camera	see_saw	helicopter
tree	bus	clock	map	bicycle	helicopter
tree	bus	clock	map	see_saw	helicopter
tree	car	clock	camera	bicycle	helicopter
tree	car	clock	camera	see_saw	helicopter
tree	car	clock	map	bicycle	helicopter
tree	car	clock	map	see_saw	helicopter
umbrella	bus	clock	camera	bicycle	helicopter
umbrella	bus	clock	camera	see_saw	helicopter
umbrella	bus	clock	map	bicycle	helicopter
umbrella	bus	clock	map	see_saw	helicopter
umbrella	car	clock	camera	bicycle	helicopter
umbrella	car	clock	camera	see_saw	helicopter
umbrella	car	clock	map	bicycle	helicopter
umbrella	car	clock	map	see_saw	helicopter
tree	envelope	camel	octopus	donut	police_car
umbrella	envelope	camel	octopus	donut	police_car
tree	envelope	camel	ambulance	donut	helicopter
umbrella	envelope	camel	ambulance	donut	helicopter
tree	envelope	crab	ambulance	bicycle	ice_cream
tree	envelope	crab	ambulance	see_saw	ice_cream
umbrella	envelope	crab	ambulance	bicycle	ice_cream
umbrella	envelope	crab	ambulance	see_saw	ice_cream
tree	envelope	clock	octopus	bicycle	police_car
tree	envelope	clock	octopus	see_saw	police_car
umbrella	envelope	clock	octopus	bicycle	police_car
umbrella	envelope	clock	octopus	see_saw	police_car
tree	envelope	clock	ambulance	bicycle	helicopter
tree	envelope	clock	ambulance	see_saw	helicopter
umbrella	envelope	clock	ambulance	bicycle	helicopter
umbrella	envelope	clock	ambulance	see_saw	helicopter
tree	strawberry	crab	camera	bicycle	police_car
tree	strawberry	crab	camera	see_saw	police_car
tree	strawberry	crab	map	bicycle	police_car
tree	strawberry	crab	map	see_saw	police_car
umbrella	strawberry	crab	camera	bicycle	police_car
umbrella	strawberry	crab	camera	see_saw	police_car
umbrella	strawberry	crab	map	bicycle	police_car
umbrella	strawberry	crab	map	see_saw	police_car
tree	strawberry	calculator	octopus	bicycle	police_car
tree	strawberry	calculator	octopus	see_saw	police_car
umbrella	strawberry	calculator	octopus	bicycle	police_car
umbrella	strawberry	calculator	octopus	see_saw	police_car
tree	strawberry	calculator	ambulance	bicycle	helicopter
tree	strawberry	calculator	ambulance	see_saw	helicopter
umbrella	strawberry	calculator	ambulance	bicycle	helicopter
umbrella	strawberry	calculator	ambulance	see_saw	helicopter
spider	bus	camel	camera	lollipop	ice_cream
spider	bus	camel	map	lollipop	ice_cream
spider	car	camel	camera	lollipop	ice_cream
spider	car	camel	map	lollipop	ice_cream
spider	bus	camel	camera	donut	hot_air_balloon
spider	bus	camel	map	donut	hot_air_balloon
spider	car	camel	camera	donut	hot_air_balloon
spider	car	camel	map	donut	hot_air_balloon
spider	bus	clock	camera	bicycle	hot_air_balloon
spider	bus	clock	camera	see_saw	hot_air_balloon
spider	bus	clock	map	bicycle	hot_air_balloon
spider	bus	clock	map	see_saw	hot_air_balloon
spider	car	clock	camera	bicycle	hot_air_balloon
spider	car	clock	camera	see_saw	hot_air_balloon
spider	car	clock	map	bicycle	hot_air_balloon
spider	car	clock	map	see_saw	hot_air_balloon
spider	envelope	camel	ambulance	lollipop	ice_cream
spider	envelope	camel	ambulance	donut	hot_air_balloon
spider	envelope	clock	ambulance	bicycle	hot_air_balloon
spider	envelope	clock	ambulance	see_saw	hot_air_balloon
spider	strawberry	camel	camera	lollipop	police_car
spider	strawberry	camel	map	lollipop	police_car
spider	strawberry	calculator	ambulance	bicycle	hot_air_balloon
spider	strawberry	calculator	ambulance	see_saw	hot_air_balloon
`.trim();

// ---- 轉陣列並過濾（只保留模型 CLASSES 內的類別；至少能湊出 PER_ROUND 個選項）----
const POOLS = POOL_TEXT.split('\n')
  .map(l => l.trim().split(/\s+/))
  .map(row => row.filter(c => CLASSES.includes(c)))
  .filter(row => row.length >= Math.min(PER_ROUND, 2));

// ====== 困難模式：固定候選，但每題題目『隨機 1 個』 ======
const HARD_ROUNDS = [
  ['fish','eyeglasses','camel','see_saw','bicycle','shark'],
  ['palm_tree','hot_air_balloon','lollipop','mushroom','umbrella','penguin','tree'],
  ['spider','octopus','hedgehog','campfire','crab','helicopter'],
  ['ambulance','police_car','car','truck','bus'],
  ['radio','map','envelope','camera','calculator','laptop'],
  ['clock','donut','wheel','ice_cream','apple','strawberry'], // ← 修正錯字
];

// ---- 隨機工具 ----
function randInt(n){ return Math.floor(Math.random() * n); }
function sampleUnique(arr, k){
  const pool = arr.slice(), out = [];
  for (let i = 0; i < k && pool.length; i++){
    const j = Math.floor(Math.random() * pool.length);
    out.push(pool.splice(j, 1)[0]);
  }
  return out;
}

// ====== 依難度產生本場題庫：回傳 {rounds, prompts} ======
function buildRounds(difficulty){
  if (difficulty === 'hard'){
    // 困難模式：每回合從對應候選清單中抽 PER_ROUND 個當選項，並隨機 1 個當本題目標
    const base = HARD_ROUNDS.map(row => row.filter(c => CLASSES.includes(c)));
    const rounds = base.map(row => sampleUnique(row, Math.min(PER_ROUND, row.length)));
    const prompts = rounds.map(choices => choices[randInt(choices.length)]);
    return { rounds, prompts };
  } else {
    // 簡單模式：128 道「題組」中，隨機抽 1 組給該參賽者整場使用
    if (!POOLS.length){
      // 安全保底：若沒有題組，就從所有 CLASSES 出題
      const rounds = Array.from({length: NUM_ROUNDS}, _ => sampleUnique(CLASSES, Math.min(PER_ROUND, CLASSES.length)));
      const prompts = rounds.map(choices => choices[randInt(choices.length)]);
      return { rounds, prompts };
    }

    // ① 抽一組題組（單行），並去重確保唯一類別
    const baseRow = POOLS[randInt(POOLS.length)];
    const poolSet = Array.from(new Set(baseRow.filter(c => CLASSES.includes(c))));

    // ② 先決定『本場每題的題目』：盡量使用不重複題目
    const shuffled = poolSet.slice();
    for (let i = shuffled.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    const uniqueCount = Math.min(NUM_ROUNDS, shuffled.length);
    const prompts = [];
    for (let i = 0; i < NUM_ROUNDS; i++) {
      // 若題組種類數 >= 題數：前 uniqueCount 題完全不重複
      // 若不足：後面開始循環（允許重複，但這只在題組太小時發生）
      const p = (i < uniqueCount) ? shuffled[i] : shuffled[i % shuffled.length];
      prompts.push(p);
    }

    // ③ 依每題題目，產生該回合候選，並確保題目有被包含在候選中
    const rounds = prompts.map(p => {
      const others = poolSet.filter(x => x !== p);
      const need = Math.max(0, Math.min(PER_ROUND - 1, others.length));
      const sampled = sampleUnique(others, need);
      const choices = sampled.concat([p]);
      // 洗牌候選，避免題目總是在同一位置
      for (let i = choices.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [choices[i], choices[j]] = [choices[j], choices[i]];
      }
      return choices;
    });

    return { rounds, prompts };
  }
}

// 英→中 顯示名稱（UI 用；CSV 仍寫英文）
const ZH_LABELS = {
  baseball_bat: '棒球棒', sword: '劍', candle: '蠟燭', carrot: '紅蘿蔔',
  baseball: '棒球', basketball: '籃球', soccer_ball: '足球', watermelon: '西瓜',
  bee: '蜜蜂', butterfly: '蝴蝶', angel: '天使', penguin: '企鵝',
  brain: '大腦', broccoli: '花椰菜', cloud: '雲朵', tree: '樹',
  microphone: '麥克風', tennis_racquet: '網球拍', light_bulb: '燈泡', ice_cream: '冰淇淋',
  clock: '時鐘', calculator: '計算機', calendar: '月曆', cell_phone: '手機',
  fish: '魚', eyeglasses: '眼鏡', camel: '駱駝', see_saw: '蹺蹺板',
  bicycle: '自行車', shark: '鯊魚',
  palm_tree: '棕櫚樹', hot_air_balloon: '熱氣球', lollipop: '棒棒糖',
  mushroom: '蘑菇', umbrella: '雨傘',
  spider: '蜘蛛', octopus: '章魚', hedgehog: '刺蝟', campfire: '營火',
  crab: '螃蟹', helicopter: '直升機',
  ambulance: '救護車', police_car: '警車', car: '汽車',
  truck: '卡車', bus: '公車',
  radio: '收音機', map: '地圖', envelope: '信封',
  camera: '相機', laptop: '筆電',
  donut: '甜甜圈', wheel: '車輪',
  apple: '蘋果', strawberry: '草莓'
};

function toZh(name){ return ZH_LABELS[name] || name; }

// === 狀態 ===
let model, cnv, embedModel;
let TARGET = [];
let idxMap = [];
let roundIdx = 0;
let currentPrompt = null;

// 玩家與紀錄
let sessionId = Date.now().toString(36);
let playerName = 'anonymous';
let playerGender = '';
let playerAge = '';
let difficulty = '';
const logs = [];

// 題庫（開始時由 buildRounds() 產生）
let activeRounds = [];
let activePrompts = [];

// 計時（把 locked 提前宣告，避免 TDZ）
let timerId = null;
let timeLeftMs = TIME_LIMIT_MS;
let drawStartAt = 0;
let locked = false; // 時間到鎖筆
let previewId = null; // 即時機率預覽計時器

// DOM helper
function $(id){ return document.getElementById(id); }
function ensureBadge(){
  var el = document.getElementById('playerBadge');
  if (!el){
    el = document.createElement('div');
    el.id = 'playerBadge';
    el.style.cssText = 'position:fixed;top:10px;right:12px;background:#111;color:#fff;padding:6px 10px;border-radius:999px;font-size:14px;display:inline-block;z-index:9999;';
    document.body.appendChild(el);
  }
  return el;
}

function difficultyZh(){
  return (difficulty === 'hard') ? '困難' : (difficulty ? '簡單' : '-');
}
function updateBadge(){
  var badge = ensureBadge();
  var name = playerName || '';
  var diff = difficultyZh();
  badge.textContent = '參賽者：' + name + '　挑戰難度：' + diff;
  badge.style.display = 'inline-block';
}
function showView(id){
  var ids = ['view-form','view-instruct','view-draw','view-done'];
  for (var i = 0; i < ids.length; i++){
    var el = $(ids[i]);
    if (el) el.classList.toggle('active', ids[i] === id);
  }
  // 每頁右上角名牌：初始頁面隱藏，其餘頁面顯示
  try {
    var badge = ensureBadge();
    if (id === 'view-form') {
      badge.style.display = 'none';
    } else {
      updateBadge();
      badge.style.display = 'inline-block';
    }
  } catch(e){}
}

// === 模型 ===
// 選擇一個最像「softmax 前 embedding」的層
function pickEmbeddingLayer(m){
  for (let i = m.layers.length - 1; i >= 0; i--){
    const L = m.layers[i];
    const conf = (typeof L.getConfig === 'function') ? L.getConfig() : {};
    const units = (conf && typeof conf.units === 'number') ? conf.units : null;
    const activation = conf && conf.activation;
    if (activation === 'softmax') continue;
    if (units === CLASSES.length) continue; // 類別輸出層
    if (i >= 1) return m.layers[i];
  }
  return null;
}

async function loadMyModel(){
  model = await tf.loadLayersModel('model/model.json');
  // 建立 embedding 抽取模型（選擇「softmax 前」的最佳層）
  try {
    const embLayer = pickEmbeddingLayer(model);
    if (embLayer) {
      embedModel = tf.model({inputs: model.inputs, outputs: embLayer.output});
      console.log('[Model] embedding layer =', embLayer.name || '(unnamed)');
    } else {
      const L = model.layers.length;
      embedModel = tf.model({inputs: model.inputs, outputs: model.layers[L-2].output});
      console.warn('[Model] fallback to second last layer as embedding');
    }
  } catch (e){
    console.warn('[Model] build embed model failed, fallback second-last:', e);
    const L = model.layers.length;
    embedModel = tf.model({inputs: model.inputs, outputs: model.layers[L-2].output});
  }
}

// === p5 初始化 ===
function setup(){
  loadMyModel();

  // 畫布（在作畫頁顯示）
  pixelDensity(1);                    // 避免 Retina 裝置畫面太模糊
cnv = createCanvas(CANVAS_SIDE, CANVAS_SIDE);
  background(255);
  cnv.parent('canvasContainer');

  // 綁事件
  var sb = $('startBtn'); if (sb) sb.addEventListener('click', function(e){ e.preventDefault(); onStartForm(); });
  var ok = $('instrOk'); if (ok) ok.addEventListener('click', startDrawing);
  var cl = $('clearBtn'); if (cl) cl.addEventListener('click', function(){ if (!locked) background(255); });
  var sub = $('submitBtn'); if (sub) sub.addEventListener('click', submitAnswer);
  var dl = $('download');
  if (dl) {
    dl.textContent = '點擊查看成績以及說明';
    dl.addEventListener('click', openResultsPage);
  }

  // 顯示第一頁
  showView('view-form');
}

function draw(){
  if (locked) return;
  strokeWeight(BRUSH_WEIGHT);
  stroke(0);
  if (mouseIsPressed) line(pmouseX, pmouseY, mouseX, mouseY);
}

// === 表單驗證 → 進入題目說明 ===
function onStartForm(){
  var nameVal = ($('player') && $('player').value || '').trim();
  var genderEl = document.querySelector('input[name="gender"]:checked');
  var ageVal = ($('age') && $('age').value || '').trim();
  var diffEl = document.querySelector('input[name="difficulty"]:checked');

  var err = [];
  if (!nameVal) err.push('請填寫姓名／暱稱');
  if (!genderEl) err.push('請選擇性別');
  if (!ageVal) err.push('請填寫年齡');
  if (!diffEl) err.push('請選擇挑戰難度');

  var box = $('formError');
  if (err.length){ if (box) box.textContent = err.join('、'); return; }
  if (box) box.textContent = '';

  // 存檔
  playerName = nameVal;
  playerGender = genderEl.value;
  playerAge = ageVal;
  difficulty = diffEl.value;

  // 依難度『隨機產生』題庫
  const { rounds, prompts } = buildRounds(difficulty);
  activeRounds  = rounds;
  activePrompts = prompts;
    
  // 更新名牌
  try { updateBadge(); } catch(e) {}

  // 第一回合
  roundIdx = 0;
  applyRound(roundIdx);
  showView('view-instruct');
}

// === 套用回合內容到畫面 ===
function applyRound(i){
  TARGET = activeRounds[i];
  idxMap = TARGET.map(function(n){ return CLASSES.indexOf(n); });

  if (idxMap.some(function(x){ return x < 0; })){
    console.error('題目設定錯誤：找不到類別於 CLASSES', TARGET);
    alert('題目設定錯誤，請重新整理或聯絡工作人員。');
  }

  currentPrompt = activePrompts[i] || TARGET[0];

  // 若固定目標不在該回合候選，給出警告但仍繼續
  if (TARGET.indexOf(currentPrompt) === -1) {
    console.warn('固定題目不在本回合候選中：', currentPrompt, '於', TARGET);
  }

  // 題目說明頁：置中顯示「第 N 題：請畫出『XXX』」
  var p = $('prompt');
  if (p) p.textContent = '第 ' + (i + 1) + ' 題：請畫出「' + toZh(currentPrompt) + '」';

  // 作畫頁頂端也顯示一次
  var dp = $('drawPrompt');
  if (dp) dp.textContent = '請畫出「' + toZh(currentPrompt) + '」';
}

// === 開始作畫（啟動倒數） ===
function startDrawing(){
  drawStartAt = Date.now();

  // 版面：置中資訊、放大提示文字、改按鈕文案、把按鈕移到畫布下方
  var view = document.getElementById('view-draw');
  if (view) view.style.textAlign = 'center';

  var dp = document.getElementById('drawPrompt');
  var tm = document.getElementById('timer');
  var header = tm ? tm.parentNode : null; // 原本是 .row

  if (header){
    // 取消橫向排列，改為直向兩行（第一行：提示；第二行：倒數）
    header.style.display = 'block';
    header.style.textAlign = 'center';
    if (dp) header.insertBefore(dp, header.firstChild);
  }

  if (dp){
    dp.style.fontSize = '28px';
    dp.style.fontWeight = '700';
    dp.style.margin = '6px 0 4px';
    dp.style.display = 'block';
  }
  if (tm){
    tm.style.display = 'block';
    tm.style.margin = '0 0 8px';
    tm.style.fontWeight = '600';
  }

  var tmsg = document.getElementById('timeUpMsg');
  if (tmsg){ tmsg.textContent = '時間到！請按「送出結果」進入下一題。'; }
  var cb = document.getElementById('clearBtn'); if (cb) cb.textContent = '清除重畫';
  var sb = document.getElementById('submitBtn'); if (sb) sb.textContent = '送出結果';
  var cc = document.getElementById('canvasContainer');
  var toolbar = cb ? cb.parentNode : null;
  if (cc && toolbar && toolbar !== cc.nextSibling){ cc.parentNode.insertBefore(toolbar, cc.nextSibling); }
  if (toolbar){ toolbar.style.justifyContent = 'center'; }

  // 清畫布與狀態
  background(255);
  locked = false;
  var timeMsg = document.getElementById('timeUpMsg'); if (timeMsg) timeMsg.style.display = 'none';
  timeLeftMs = TIME_LIMIT_MS;
  $('timer').textContent = '時間倒計時：還剩下 ' + (timeLeftMs/1000).toFixed(1) + ' 秒';

  // 清空上一題的結果並啟動即時預覽
  $('res').innerHTML = '';
  if (previewId) { clearInterval(previewId); previewId = null; }
  previewId = setInterval(previewPredict, 500); // 每 0.5 秒更新一次當回合機率

  if (timerId) clearInterval(timerId);
  timerId = setInterval(function(){
    timeLeftMs -= 100;
    if (timeLeftMs < 0) timeLeftMs = 0;
    $('timer').textContent = '時間倒計時：還剩下 ' + (timeLeftMs/1000).toFixed(1) + ' 秒';
    if (timeLeftMs <= 0){
      clearInterval(timerId);
      timerId = null;
      locked = true;
      $('timeUpMsg').style.display = 'block';
    }
  }, 100);

  showView('view-draw');
}

// === 畫布 → 28x28x1 ===
function getInputImage(){
  var inputs = [];
  var img = get();    // 取目前畫布影像（大小由 CANVAS_SIDE 決定，與模型無關）
  img.resize(28, 28);
  img.loadPixels();

  var row = [];
  for (var i = 0; i < IMAGE_SIZE; i++){
    var r = img.pixels[i * 4];
    var v = (255 - r) / 255;   // 黑=1 白=0
    row.push([v]);
    if (row.length === 28){ inputs.push(row); row = []; }
  }
  return inputs; // [28][28][1]
}

// === 即時預覽：在作畫時顯示當回合四類機率（不寫入 CSV） ===
function previewPredict(){
  if (!model || locked) return;
  var probsPicked;
  tf.tidy(function(){
    var x = tf.tensor([getInputImage()]);
    var y = model.predict(x).squeeze();
    var indices = tf.tensor1d(idxMap, 'int32');
    var picked = tf.gather(y, indices);
    var probs = picked.div(picked.sum());
    probsPicked = probs.dataSync();
  });
  var arr = Array.from(probsPicked);
  var items = arr.map(function(p,i){ return { name: TARGET[i], p: p }; })
                 .sort(function(a,b){ return b.p - a.p; });
  $('res').innerHTML = '即時：' + items.map(function(t){ return toZh(t.name) + ' ' + (t.p*100).toFixed(1) + '%'; }).join('，');
}

// === 提交：推論 + 紀錄 + 下一題/完成 ===
function submitAnswer(){
  if (previewId){ clearInterval(previewId); previewId = null; }
  if (!model){ $('res').textContent = '模型載入中…'; return; }

  if (timerId){ clearInterval(timerId); timerId = null; }
  var spentSec = Math.max(0, (Date.now() - drawStartAt) / 1000);
  var timedOut = timeLeftMs <= 0 ? 1 : 0;

  var probsPicked, embeddingVec;
  tf.tidy(function(){
    var x = tf.tensor([getInputImage()]);            // [1,28,28,1]
    // embedding（softmax 前）
    try {
      var e = embedModel.predict(x);
      embeddingVec = Array.from(e.flatten().dataSync());
    } catch(err){
      console.warn('Embedding 抽取失敗，改為空陣列：', err);
      embeddingVec = [];
    }
    // 分類機率（在當回合四類上做 re-normalize）
    var y = model.predict(x).squeeze();              // [365]
    var indices = tf.tensor1d(idxMap, 'int32');      // [4]
    var picked = tf.gather(y, indices);              // [4]
    var probs = picked.div(picked.sum());
    probsPicked = probs.dataSync();
  });

  // 轉為 {label: prob} 對照（不排序，CSV 走寬表欄位）
  var probsMap = {};
  for (var i=0;i<TARGET.length;i++) probsMap[TARGET[i]] = Number(probsPicked[i] || 0);

  // 顯示 Top-3（畫面用，CSV 不排名）
  var sorted = TARGET.map(function(n,i){ return { name:n, p: probsMap[n] }; }).sort(function(a,b){ return b.p - a.p; });
  var top = sorted.slice(0, TOP_SHOW);
  $('res').innerHTML = 'Top-3: ' + top.map(function(t){ return toZh(t.name) + ' ' + (t.p*100).toFixed(1) + '%'; }).join('，');

  // 儲存當前畫布 PNG（上傳）
  saveCanvasImageAndUpload(sessionId + '_R' + (roundIdx+1) + '_' + currentPrompt + '.png');

  // 紀錄一列（寬表：每類別一欄；另存 embedding）
  logs.push({
    session_id: sessionId,
    player_name: playerName,
    gender: playerGender,
    age: playerAge,
    difficulty: difficulty,
    round: roundIdx + 1,
    prompt: currentPrompt,
    time_spent_sec: spentSec.toFixed(2),
    timed_out: timedOut,
    probs_map: probsMap,          // {label: prob}
    embedding: embeddingVec,      // [e1,e2,...]
    timestamp: new Date().toISOString()
  });

  if (roundIdx < NUM_ROUNDS - 1){
    roundIdx += 1;
    background(255);
    $('res').innerHTML = '';
    $('timeUpMsg').style.display = 'none';
    locked = false;
    timeLeftMs = TIME_LIMIT_MS;

    applyRound(roundIdx);
    showView('view-instruct');
  } else {
    saveLogsToLocal();
    saveCSVToServer();
    showView('view-done');
    var done = $('view-done');
    if (done) {
      done.style.textAlign = 'center';
      var p = done.querySelector('p');
      if (p) p.textContent = '感謝參與!!';
      var btn = $('download');
      if (btn) btn.textContent = '點擊查看成績以及說明';
      // 若頁面有重開按鈕可在這裡綁定：const rb = $('restartBtn'); if (rb) rb.onclick = restartGame;
    }
  }
}

// === CSV 組裝文字（供儲存或下載用） ===
function buildCSVText(){
  if (!logs.length) return '';
  // 依本場次實際使用到的類別建立寬表（最多 24）
  var allTargets = getSessionTargets();
  var baseHeaders = ['session_id','player_name','gender','age','difficulty','round','prompt','time_spent_sec','timed_out','timestamp'];

  // 取本場次 embedding 最長長度，展開成 emb_0..emb_N
  var maxEmbLen = 0;
  for (var i=0;i<logs.length;i++) if (Array.isArray(logs[i].embedding))
    maxEmbLen = Math.max(maxEmbLen, logs[i].embedding.length);
  var embHeaders = [];
  for (var e=0;e<maxEmbLen;e++) embHeaders.push('emb_'+e);

  var headers = baseHeaders.concat(allTargets).concat(embHeaders);
  var lines = [headers.join(',')];

  for (var i=0;i<logs.length;i++){
    var r = logs[i];
    var row = [];

    // 基本欄
    baseHeaders.forEach(function(h){
      var v = (r[h] !== undefined ? r[h] : '');
      row.push('"' + String(v).replace(/"/g,'""') + '"');
    });

    // 機率欄（只有當回合的 4 類會有值）
    allTargets.forEach(function(t){
      var p = (r.probs_map && Object.prototype.hasOwnProperty.call(r.probs_map, t)) ? r.probs_map[t] : '';
      row.push(p === '' ? '' : (typeof p === 'number' ? p.toFixed(6) : String(p)));
    });

    // embedding：每個值一欄
    for (var e=0;e<maxEmbLen;e++){
      var val = (Array.isArray(r.embedding) && r.embedding[e] !== undefined) ? Number(r.embedding[e]) : '';
      row.push(val === '' ? '' : val.toFixed(6));
    }

    lines.push(row.join(','));
  }
  return lines.join('\n');
}


// === 儲存到 localStorage（不自動下載） ===
function saveLogsToLocal(){
  try {
    localStorage.setItem('quickdraw:csv:' + sessionId, buildCSVText());
    localStorage.setItem('quickdraw:logs:' + sessionId, JSON.stringify(logs));
  } catch(e) { console.warn('localStorage 儲存失敗：', e); }
}

// 依本場次實際用到的所有類別（依 round 順序、去重）
function getSessionTargets(){
  var used = [];
  for (var i=0;i<activeRounds.length;i++){
    var r = activeRounds[i] || [];
    for (var j=0;j<r.length;j++) if (used.indexOf(r[j]) === -1) used.push(r[j]);
  }
  return used;
}

// 上傳工具（嘗試 PUT，失敗則 POST；若皆失敗則提示，不自動下載）
async function uploadFile(filename, blob){
  const base = SERVER_BASE.replace(/\/+$/,'');
  const putUrl = base + '/' + encodeURIComponent(filename);
  try {
    let res = await fetch(putUrl, { method:'PUT', body: blob, headers:{'Content-Type': blob.type||'application/octet-stream'}, mode:'cors' });
    if (!res.ok) throw new Error('PUT '+res.status);
    console.log('[Upload] PUT ok:', putUrl);
    return true;
  } catch(e){
    console.warn('[Upload] PUT 失敗，改用 POST：', e);
    try {
      const fd = new FormData();
      fd.append('file', blob, filename);
      let res2 = await fetch(base, { method:'POST', body: fd, mode:'cors' });
      if (!res2.ok) throw new Error('POST '+res2.status);
      console.log('[Upload] POST ok:', base);
      return true;
    } catch(e2){
      console.error('[Upload] 上傳失敗（可能是伺服器未開放 CORS 或無上傳端點）:', e2);
      alert('⚠️ 檔案未能儲存到伺服器：' + base + '\n請確認伺服器允許 CORS，且此路徑支援 PUT 或 POST 上傳。');

      return false;
    }
  }
}

function getCanvasPNGBlob(){
  return new Promise(function(resolve){
    try {
      (cnv && cnv.elt ? cnv.elt : document.querySelector('canvas')).toBlob(function(b){ resolve(b); }, 'image/png');
    } catch(e){
      // 最後手段：dataURL 轉 blob
      try {
        var c = (cnv && cnv.elt) ? cnv.elt : document.querySelector('canvas');
        var data = c.toDataURL('image/png');
        var byteString = atob(data.split(',')[1]);
        var mimeString = data.split(',')[0].split(':')[1].split(';')[0];
        var ab = new ArrayBuffer(byteString.length);
        var ia = new Uint8Array(ab);
        for (var i = 0; i < byteString.length; i++) ia[i] = byteString.charCodeAt(i);
        resolve(new Blob([ab], {type: mimeString}));
      } catch(e2){ resolve(new Blob([])); }
    }
  });
}

async function saveCanvasImageAndUpload(filename){
  try {
    const blob = await getCanvasPNGBlob();
    if (blob && blob.size) {
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url; a.download = filename; document.body.appendChild(a);
      a.click(); a.remove();
      setTimeout(function(){ URL.revokeObjectURL(url); }, 0);
    }
  } catch(e){ console.warn('saveCanvasImageAndUpload error:', e); }
}


async function saveCSVToServer(){
  try {
    const text = buildCSVText();
    const blob = new Blob([text], {type:'text/csv;charset=utf-8'});
    const fn = sessionId + '_results.csv';
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = fn; document.body.appendChild(a);
    a.click(); a.remove();
    setTimeout(function(){ URL.revokeObjectURL(url); }, 0);
  } catch(e){ console.warn('saveCSVToServer error:', e); }
}


// 重新開始整個遊戲（清空狀態，回到第一頁）
function restartGame(){
  try { if (timerId) clearInterval(timerId); } catch(_){ }
  try { if (previewId) clearInterval(previewId); } catch(_){ }
  timerId = null; previewId = null; locked = false;
  timeLeftMs = TIME_LIMIT_MS; roundIdx = 0; currentPrompt = null;
  background(255);
  var r = $('res'); if (r) r.innerHTML = '';
  var t = $('timeUpMsg'); if (t) t.style.display = 'none';

  // 清空表單
  if ($('player')) $('player').value = '';
  if ($('age')) $('age').value = '';
  var gs = document.querySelectorAll('input[name="gender"]:checked');
  for (var i=0;i<gs.length;i++) gs[i].checked = false;
  var ds = document.querySelectorAll('input[name="difficulty"]:checked');
  for (var j=0;j<ds.length;j++) ds[j].checked = false;

  // 玩家資訊與題庫恢復預設（清空，待開始時再 buildRounds）
  playerName = 'anonymous'; playerGender = ''; playerAge = ''; difficulty = '';
  activeRounds = [];
  activePrompts = [];

  // 新場次
  sessionId = Date.now().toString(36);
  logs.length = 0;

  // 隱藏名牌，回到第一頁
  try { ensureBadge().style.display = 'none'; } catch(_){ }
  showView('view-form');
}


// === 開新視窗顯示成績與說明（可選下載連結） ===
function openResultsPage(){
  var csv = buildCSVText();
  var rows = logs.map(function(r){
    var top1 = '-';
    if (r.probs_map && Object.keys(r.probs_map).length){
      var arr = Object.keys(r.probs_map).map(function(k){ return { name: k, p: r.probs_map[k] }; });
      arr.sort(function(a,b){ return b.p - a.p; });
      top1 = toZh(arr[0].name) + ' (' + (arr[0].p*100).toFixed(1) + '%)';
    }
    return '<tr>'+
      '<td>'+ r.round +'</td>'+
      '<td>'+ toZh(r.prompt) +'</td>'+
      '<td>'+ top1 +'</td>'+
      '<td>'+ r.time_spent_sec +'s</td>'+
      '<td>'+ (r.timed_out? '是':'否') +'</td>'+
    '</tr>';
  }).join('');

  var blob = new Blob([csv], {type:'text/csv'});
  var csvUrl = URL.createObjectURL(blob);

  var html = `
<!doctype html>
<meta charset="utf-8">
<title>成績與說明</title>
<style>
 body{font-family:system-ui,Segoe UI,Roboto,Noto Sans TC,sans-serif;padding:24px;}
 h1{margin:0 0 12px;}
 table{border-collapse:collapse;width:100%;margin-top:12px;}
 th,td{border:1px solid #ddd;padding:8px 10px;text-align:center;}
 th{background:#f7f7f7;}
 .muted{color:#666;}
 .btn{display:inline-block;margin-top:12px;padding:8px 12px;border:1px solid #111;text-decoration:none;color:#111;border-radius:8px;}
 .btn.secondary{margin-left:8px;}
</style>
<h1>成績與說明</h1>
<p class="muted">參賽者：${playerName}　難度：${(difficulty==='hard'?'困難':'簡單')}　場次：${sessionId}</p>
<table>
<thead><tr><th>題次</th><th>指定</th><th>TOP1</th><th>耗時</th><th>逾時</th></tr></thead>
<tbody>${rows}</tbody>
</table>
<a class="btn" href="${csvUrl}" download="quickdraw_logs_${sessionId}.csv">下載 CSV（可選）</a>
<button id="restartBtn" class="btn secondary">重新開始遊戲</button>
<script>
  (function(){
    var btn = document.getElementById('restartBtn');
    if (btn) btn.addEventListener('click', function(){
      if (window.opener && typeof window.opener.restartGame === 'function') {
        window.opener.restartGame();
        window.close();
      } else {
        alert('請回到主畫面按重新開始');
      }
    });
  })();
</script>`;

  var w = window.open('','_blank');
  if (!w) { alert('請允許彈出視窗以查看成績'); return; }
  w.document.write(html);
  w.document.close();
}
