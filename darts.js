// Sonar — the daily word game on the console. Six rounds a day on one board: the board's two axes
// are general spectrums fixed for the day, and every round has its own category. Rounds 1–3 set a
// random target, round 4 the centre bull, round 5 is reversed (you are given a word and tap where it
// sits), round 6 is the boss (as many words as you can at one target before the clock runs out).
// A hit scores its ring plus a point for every second left; no answer scores nothing.
// Data comes from puzzles/arena/ (built by build.py): every word's position on the six general
// spectrums and its fit for each category, plus each category's hand-picked words.
(() => {
const ROUNDS = 6;
const ROUND_SECONDS = 30;     // the countdown for each round
const URGENT_SECONDS = 5;     // the console goes red from here
const MAX_POINTS = 50;        // a word on the dot scores this
const FALLOFF = 1.0;          // points fall to zero this many units from the dot
const BULL = 0.1;             // within this distance counts as a bullseye
const MIN_R = 0.3, MAX_R = 0.75;  // random targets sit in this band, clear of the centre
const REACH = 0.2;            // a target must have a curated word within this distance
const KINDS = ['target', 'target', 'target', 'centre', 'reverse', 'boss'];
const SHARDS = 256;
const FIT_THRESHOLD = 25;     // category fit is 0..100; lenient so real words are rarely refused
const C = 300, R = 215;       // board centre and the length of one unit, in SVG units
const GRID = 0.25;            // matrix spacing, in units
const LABEL_GAP = 12;         // axis words sit this far inside the rim

// ---- Scoring: the one place to change the rule ----
const pointsFor = d => Math.round(MAX_POINTS * Math.max(0, 1 - d / FALLOFF)); // straight line from the dot outwards
const timeBonus = (points, secondsLeft) => points > 0 ? Math.round(secondsLeft) : 0; // a point per second left, hits only
const bullseye = d => d <= BULL;

// ---- Looks: the Graphite console (Abyss survives behind ?theme=abyss) ----
const THEMES = {
  graphite: { disc: '#0a1a11', grid: '#16412b', axis: '#3f8b63', rings: ['#eafff2', '#a7ecc6', '#86d8a8', '#3f8b63'], ringText: '#c9f5db', target: '#4fc3ff', targetDim: '#2b6f93',
              past: '#3f8b63', pastText: '#86d8a8', answer: '#d9a441', leader: '#a7ecc6', ink: '#06090a' },
  abyss:    { disc: '#040c07', grid: '#0f2a1c', axis: '#245c3f', rings: ['#ffffff', '#8ff0b8', '#5fbf8a', '#245c3f'], ringText: '#d6ffe6', target: '#5ccfff', targetDim: '#245a78',
              past: '#245c3f', pastText: '#5fbf8a', answer: '#c9933a', leader: '#8ff0b8', ink: '#020403' },
};
let theme = THEMES.graphite;

// ---- State ----
let arena;                 // arena.json: spectrums, categories, pairs, curated, launch
let date, dayNumber;
let axes = [0, 1];         // indexes into arena.spectrums: left→right, bottom→top
let catOrder = [];         // category index for each round
let targets = [];          // {x, y} per round (null for the reverse round)
let reverseWord = null;    // {word, x, y} for round 5
let phase = 'idle';        // idle → playing → between → … → over
let roundIdx = 0;          // the round being played or just finished
let roundStart = 0;        // when the current round's clock started
let rounds = [];           // results: {kind, cat, word, x, y, points, bonus, score, seconds, hits, click}
let bossHits = [];         // this round's hits while the boss round runs: {word, x, y, points}
let pending = false;       // a word is being looked up or animated
const shardCache = new Map();

const $ = id => document.getElementById(id);
const svg = $('d-board');
const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;');
const normalise = s => s.trim().toLowerCase().replace(/[^a-z\s-]/g, '').replace(/[\s-]+/g, ' ').trim();
const sx = x => C + x * R, sy = y => C - y * R;
const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y);
const bearing = p => String(Math.round(((Math.atan2(p.x, p.y) * 180 / Math.PI) + 360) % 360)).padStart(3, '0') + '°';
const range = p => Math.hypot(p.x, p.y).toFixed(2);
const brgRng = p => `BRG ${bearing(p)} RNG ${range(p)}`;
const fmt = sec => { const m = Math.floor(sec / 60), s = sec - m * 60; return `${String(m).padStart(2, '0')}:${s.toFixed(1).padStart(4, '0')}`; };
const cat = k => arena.categories[catOrder[k]];
const kind = k => KINDS[k];
const total = () => rounds.reduce((s, r) => s + (r ? r.score : 0), 0);
const elapsed = () => (Date.now() - roundStart) / 1000;
const remaining = () => Math.max(0, ROUND_SECONDS - elapsed());

// ---- Seeded random: everyone gets the same day ----
function fnv1a(s) { let h = 0x811c9dc5; for (const b of new TextEncoder().encode(s)) h = Math.imul(h ^ b, 0x01000193) >>> 0; return h; }
function mulberry32(a) { return () => { a = (a + 0x6D2B79F5) >>> 0; let t = Math.imul(a ^ (a >>> 15), 1 | a); t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t; return ((t ^ (t >>> 14)) >>> 0) / 4294967296; }; }

const curatedWords = ci => Object.entries(arena.curated[arena.categories[ci].id]).map(([word, p]) => ({ word, x: p[axes[0]] / 100, y: p[axes[1]] / 100 }));

// The day's layout: an axis pair, a category for every round, a target per round in different quarters
// (each reachable by one of its category's curated words), the centre bull for round 4, and the word
// for the reverse round.
function setUpDay(rand) {
  axes = arena.pairs[dayNumber % arena.pairs.length];
  const cats = arena.categories.map((_, i) => i);
  for (let i = cats.length - 1; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [cats[i], cats[j]] = [cats[j], cats[i]]; }
  catOrder = Array.from({ length: ROUNDS }, (_, k) => cats[k % cats.length]);
  const quarters = [0, 1, 2, 3];
  for (let i = 3; i > 0; i--) { const j = Math.floor(rand() * (i + 1)); [quarters[i], quarters[j]] = [quarters[j], quarters[i]]; }
  const randomTarget = (qd, words) => {
    let best = null;
    for (let tries = 0; tries < 40; tries++) {
      const ang = (qd + 0.1 + 0.8 * rand()) * Math.PI / 2, r = Math.sqrt(MIN_R ** 2 + (MAX_R ** 2 - MIN_R ** 2) * rand());
      const t = { x: Math.round(100 * r * Math.cos(ang)) / 100, y: Math.round(100 * r * Math.sin(ang)) / 100 };
      const near = words.length ? Math.min(...words.map(w => dist(w, t))) : 0;
      if (!best || near < best.near) best = { t, near };
      if (near <= REACH) break;
    }
    return best.t;
  };
  targets = KINDS.map((kd, k) => {
    if (kd === 'centre') return { x: 0, y: 0 };
    if (kd === 'reverse') return null;
    return randomTarget(kd === 'boss' ? quarters[3] : quarters[k], curatedWords(catOrder[k]));
  });
  const pool = curatedWords(catOrder[KINDS.indexOf('reverse')]).filter(w => Math.hypot(w.x, w.y) <= 0.9 && Math.hypot(w.x, w.y) >= 0.15);
  reverseWord = pool.length ? pool[Math.floor(rand() * pool.length)] : curatedWords(catOrder[4])[0];
}

// ---- Word lookup ----
async function shard(word) {
  const key = (fnv1a(word) % SHARDS).toString(16).padStart(2, '0');
  if (!shardCache.has(key)) shardCache.set(key, fetch(`puzzles/arena/w/${key}.json`).then(r => r.ok ? r.json() : {}));
  return shardCache.get(key);
}
// Position on the day's axes and fit for the round's category; null if unknown.
async function lookup(word, ci) {
  const parts = word.split(' ');
  const entries = await Promise.all(parts.map(async p => (await shard(p))[p]));
  if (entries.some(e => !e)) return null;
  const at = i => entries.reduce((s, e) => s + e[i], 0) / entries.length / 100;
  return { x: at(axes[0]), y: at(axes[1]), fit: Math.min(...entries.map(e => e[6 + ci])) };
}

// ---- Scope ----
function consoleTargetSvg(x, y, n, live) {
  if (!live) {
    return `<g class="target past"><circle cx="${x}" cy="${y}" r="4" fill="${theme.targetDim}"/>` +
           `<text x="${x}" y="${y - 10}" font-size="13" fill="${theme.targetDim}" text-anchor="middle">${n}</text></g>`;
  }
  const ring = FALLOFF * R * 0.5; // the pulse runs out to half the fall-off distance
  return `<g class="target live"><circle class="pulse" cx="${x}" cy="${y}" r="${ring}" fill="none" stroke="${theme.target}" stroke-width="2"/>` +
         `<circle cx="${x}" cy="${y}" r="16" fill="${theme.target}" fill-opacity="0.12"/>` +
         `<circle class="dot" cx="${x}" cy="${y}" r="7" fill="${theme.target}"/>` +
         `<text x="${x}" y="${y + 30}" font-size="12" fill="${theme.target}" text-anchor="middle" letter-spacing="2">T${n}</text></g>`;
}
function returnSvg(x, y, faded) {
  return `<g opacity="${faded ? 0.6 : 1}"><circle cx="${x}" cy="${y}" r="11" fill="none" stroke="${theme.pastText}" stroke-width="1.2"/><circle cx="${x}" cy="${y}" r="4.5" fill="${theme.ringText}"/></g>`;
}
function sweepSvg() {
  let s = '<g class="sweep">';
  for (let k = 0; k < 8; k++) {
    const a0 = -k * 7 * Math.PI / 180, a1 = -(k + 1) * 7 * Math.PI / 180;
    s += `<path d="M${C},${C} L${C + R * Math.sin(a0)},${C - R * Math.cos(a0)} A${R},${R} 0 0 0 ${C + R * Math.sin(a1)},${C - R * Math.cos(a1)} Z" fill="${theme.axis}" opacity="${0.4 * (1 - k / 8)}"/>`;
  }
  return s + `<line x1="${C}" y1="${C}" x2="${C}" y2="${C - R}" stroke="${theme.rings[0]}" stroke-width="2" opacity="0.85"/></g>`;
}
function consoleSvg() {
  let s = `<circle cx="${C}" cy="${C}" r="${R + 3}" fill="none" stroke="${theme.axis}" stroke-width="1.2"/>`;
  for (let d = 0; d < 360; d += 5) {
    const a = d * Math.PI / 180, major = d % 30 === 0, len = major ? 14 : d % 10 === 0 ? 9 : 5;
    s += `<line x1="${C + (R + 6) * Math.sin(a)}" y1="${C - (R + 6) * Math.cos(a)}" x2="${C + (R + 6 + len) * Math.sin(a)}" y2="${C - (R + 6 + len) * Math.cos(a)}" stroke="${major ? theme.pastText : theme.axis}" stroke-width="${major ? 1.6 : 1}"/>`;
    if (major) s += `<text class="bearing" x="${C + (R + 36) * Math.sin(a)}" y="${C - (R + 36) * Math.cos(a) + 5}" text-anchor="middle">${String(d).padStart(3, '0')}</text>`;
  }
  const kd = kind(roundIdx), tg = targets[roundIdx];
  const tl = phase === 'idle' ? 'Standby' : phase === 'over' ? 'All rounds complete' : kd === 'reverse' ? 'Reverse bearing' : kd === 'boss' ? 'Boss contact' : 'Active sonar';
  s += `<text class="corner" x="14" y="26">${tl}</text><text class="corner" x="14" y="48">Rng scale 1.00</text>`;
  const tr = phase === 'idle' || phase === 'over' ? '' : kd === 'reverse' ? `Word ${esc(reverseWord.word)}` : `Target ${roundIdx + 1}`;
  s += `<text class="corner" x="586" y="26" text-anchor="end">${tr}</text><text class="corner" x="586" y="48" text-anchor="end">${tg && phase !== 'idle' && phase !== 'over' ? brgRng(tg) : ''}</text>`;
  s += `<text class="corner" x="14" y="586">${phase === 'idle' ? 'Press Enter to start' : `Round ${Math.min(roundIdx + 1, ROUNDS)}/${ROUNDS}`}</text>`;
  s += `<text class="corner" x="586" y="586" text-anchor="end">Score ${total()}</text>`;
  return s;
}

function render() {
  if (!arena) return;
  const [X, Y] = axes.map(i => arena.spectrums[i]);
  let s = `<defs><clipPath id="d-clip"><circle cx="${C}" cy="${C}" r="${R}"/></clipPath>` +
          `<radialGradient id="d-glass"><stop offset="0" stop-color="${theme.grid}"/><stop offset="0.6" stop-color="${theme.disc}"/><stop offset="1" stop-color="${theme.ink}"/></radialGradient></defs>`;
  s += `<circle cx="${C}" cy="${C}" r="${R}" fill="url(#d-glass)"/>`;
  s += consoleSvg();
  s += '<g clip-path="url(#d-clip)">';
  for (const f of [0.25, 0.5, 0.75]) s += `<circle cx="${C}" cy="${C}" r="${R * f}" fill="none" stroke="${theme.grid}" stroke-width="2"/>`;
  s += sweepSvg();
  for (let v = -1; v <= 1.001; v += GRID) {
    const main = Math.abs(v) < 1e-9, col = main ? theme.axis : theme.grid, w = main ? 3 : 2;
    s += `<line x1="${sx(v)}" y1="${sy(-1)}" x2="${sx(v)}" y2="${sy(1)}" stroke="${col}" stroke-width="${w}"/>`;
    s += `<line x1="${sx(-1)}" y1="${sy(v)}" x2="${sx(1)}" y2="${sy(v)}" stroke="${col}" stroke-width="${w}"/>`;
  }
  // Targets: past ones faded, the current one live.
  if (phase !== 'idle') targets.forEach((t, k) => {
    if (!t) return;
    if (k < roundIdx || phase === 'over') { if (rounds[k]) s += consoleTargetSvg(sx(t.x), sy(t.y), k + 1, false); }
    else if (k === roundIdx) s += consoleTargetSvg(sx(t.x), sy(t.y), k + 1, true);
  });
  s += `<text class="axis" x="${sx(-1) + LABEL_GAP}" y="${C - 10}" text-anchor="start">${esc(X.low)}</text>`;
  s += `<text class="axis" x="${sx(1) - LABEL_GAP}" y="${C - 10}" text-anchor="end">${esc(X.high)}</text>`;
  s += `<text class="axis" x="${C}" y="${sy(1) + 42}" text-anchor="middle">${esc(Y.high)}</text>`;
  s += `<text class="axis" x="${C}" y="${sy(-1) - 28}" text-anchor="middle">${esc(Y.low)}</text>`;
  s += '</g>';
  // Returns: every answered round's word(s); the reverse round shows the tap and the truth.
  const labels = [];
  rounds.forEach((r, k) => {
    if (!r) return;
    const faded = k !== roundIdx || phase === 'over';
    if (r.kind === 'reverse') {
      if (r.click) s += `<circle cx="${sx(r.click.x)}" cy="${sy(r.click.y)}" r="9" fill="none" stroke="${theme.answer}" stroke-width="1.6" opacity="${faded ? 0.6 : 1}"/>`;
      if (r.click) s += `<line x1="${sx(r.click.x)}" y1="${sy(r.click.y)}" x2="${sx(r.x)}" y2="${sy(r.y)}" stroke="${theme.leader}" stroke-width="1.5" stroke-dasharray="4 6" opacity="${faded ? 0.5 : 0.9}"/>`;
      s += returnSvg(sx(r.x), sy(r.y), faded);
      labels.push({ x: sx(r.x), y: sy(r.y), word: r.word, cls: 'tag' });
      return;
    }
    const hits = r.kind === 'boss' ? r.hits : (r.word ? [r] : []);
    for (const h of hits) { s += returnSvg(sx(h.x), sy(h.y), faded); labels.push({ x: sx(h.x), y: sy(h.y), word: h.word, cls: 'tag' }); }
  });
  if (phase === 'playing' && kind(roundIdx) === 'boss') for (const h of bossHits) { s += returnSvg(sx(h.x), sy(h.y), false); labels.push({ x: sx(h.x), y: sy(h.y), word: h.word, cls: 'tag' }); }
  if (phase === 'over') for (const a of answers()) if (a && a.best && !labels.some(l => l.word === a.best.word)) { s += `<circle cx="${sx(a.best.x)}" cy="${sy(a.best.y)}" r="6" fill="${theme.answer}" stroke="${theme.ink}" stroke-width="2"/>`; labels.push({ x: sx(a.best.x), y: sy(a.best.y), word: a.best.word, cls: 'tag ans' }); }
  for (const l of labels) {
    const right = l.x < C + R * 0.55, w = (l.word.length + 2) * 11;
    l.tx = right ? l.x + 16 : l.x - 16; l.anchor = right ? 'start' : 'end'; l.ty = l.y + 7;
    l.x0 = right ? l.tx : l.tx - w; l.x1 = l.x0 + w;
  }
  for (let pass = 0; pass < 4; pass++) for (let a = 0; a < labels.length; a++) for (let b = a + 1; b < labels.length; b++) {
    const A = labels[a], B = labels[b];
    if (A.x0 < B.x1 && B.x0 < A.x1 && Math.abs(A.ty - B.ty) < 22) B.ty = A.ty + 22;
  }
  for (const l of labels) s += `<text class="${l.cls}" x="${l.tx}" y="${l.ty}" text-anchor="${l.anchor}">${esc(l.word)}</text>`;
  svg.innerHTML = s;
  $('d-stage').classList.toggle('reverse', phase === 'playing' && kind(roundIdx) === 'reverse');
  renderSide();
}

// ---- The other screens ----
function renderSide() {
  const st = $('d-status'); let stText = st.querySelector('span'); if (!stText) { stText = document.createElement('span'); st.prepend(stText); }
  stText.innerHTML = phase === 'over' ? `<b>Final</b><b>${total()} pts</b>` : phase === 'idle' ? `<b>Sonar #${dayNumber}</b><b>${ROUNDS} rounds</b>` : `<b>Round ${roundIdx + 1} of ${ROUNDS}</b><b>Score ${total()}</b>`;
  $('d-category').innerHTML = phase === 'idle' ? `<div class="cat-name dim">—</div>` : `<div class="cat-name">${esc(cat(roundIdx).name)}</div>`;
  // Log: one row per round played, plus the round in play.
  $('d-readout').innerHTML = Array.from({ length: ROUNDS }, (_, k) => {
    const r = rounds[k], kd = kind(k), name = phase === 'idle' ? '' : (k <= roundIdx ? cat(k).name : '');
    const tag = kd === 'centre' ? ' · centre' : kd === 'reverse' ? ' · reverse' : kd === 'boss' ? ' · boss' : '';
    if (r) {
      const what = r.kind === 'boss' ? `${r.hits.length} hit${r.hits.length === 1 ? '' : 's'}` : r.kind === 'reverse' ? esc(r.word) : (r.word ? esc(r.word) : 'no answer');
      const detail = r.kind === 'boss' ? `${r.hits.map(h => `${esc(h.word)} ${h.points}`).join(' · ') || 'nothing landed'}` : r.word ? `${r.points} hit + ${r.bonus} time · ${fmt(r.seconds)}` : `time up`;
      return `<li class="done"><span class="n">${k + 1}</span><span class="w">${esc(name)}${tag} · ${what}</span><span class="s">${r.score}</span><span class="brg">${detail}</span></li>`;
    }
    if (k === roundIdx && phase === 'playing') return `<li class="cur"><span class="n">${k + 1}</span><span class="w">${esc(name)}${tag}</span><span class="s"></span><span class="brg">${kd === 'reverse' ? `where is ${esc(reverseWord.word)}?` : brgRng(targets[k])}</span></li>`;
    return '';
  }).join('');
  renderAxes();
}
// Axis analysis: each spectrum as a vertical bar; the target hollow, the latest word solid.
function renderAxes() {
  const r = rounds[roundIdx], kd = kind(roundIdx);
  let tg = targets[roundIdx], word = null;
  if (kd === 'reverse') { tg = reverseWord; word = r && r.click ? r.click : null; }
  else if (kd === 'boss') word = (r && r.hits.length ? r.hits[r.hits.length - 1] : bossHits[bossHits.length - 1]) || null;
  else word = r && r.word ? r : null;
  if (phase === 'idle' || !tg) { $('d-axes').innerHTML = ''; return; }
  const top = 70, bottom = 450, cols = [95, 215], rows = axes.map((i, k) => {
    const sp = arena.spectrums[i], x = cols[k], py = v => bottom - (v + 1) / 2 * (bottom - top);
    const tv = k === 0 ? tg.x : tg.y, wv = word ? (k === 0 ? word.x : word.y) : null;
    let out = `<text x="${x}" y="${top - 26}" text-anchor="middle" font-size="12" letter-spacing="1.5" fill="${theme.ringText}">${esc(sp.high.toUpperCase())}</text>` +
              `<text x="${x}" y="${bottom + 34}" text-anchor="middle" font-size="12" letter-spacing="1.5" fill="${theme.ringText}">${esc(sp.low.toUpperCase())}</text>` +
              `<line x1="${x}" y1="${top}" x2="${x}" y2="${bottom}" stroke="${theme.axis}" stroke-width="1"/>`;
    for (const v of [-1, -0.5, 0, 0.5, 1]) out += `<line x1="${x - (v === 0 ? 10 : 5)}" y1="${py(v)}" x2="${x + (v === 0 ? 10 : 5)}" y2="${py(v)}" stroke="${theme.axis}"/>`;
    if (wv !== null) {
      const cl = Math.max(-1.08, Math.min(1.08, wv)), gap = wv - tv;
      out += `<line x1="${x}" y1="${py(tv)}" x2="${x}" y2="${py(cl)}" stroke="${theme.leader}" stroke-width="3" stroke-opacity="0.45"/><circle cx="${x}" cy="${py(cl)}" r="5" fill="${theme.leader}"/>`;
      out += `<text x="${x + 14}" y="${(py(tv) + py(cl)) / 2 + 4}" font-size="11" fill="${theme.answer}">${Math.abs(gap) < 0.12 ? 'ON' : `${gap > 0 ? '+' : '−'}${Math.abs(gap).toFixed(2)}`}</text>`;
    }
    return out + `<circle cx="${x}" cy="${py(tv)}" r="6" fill="${theme.target}"/>`;
  });
  $('d-axes').innerHTML = rows.join('') + `<text x="150" y="508" text-anchor="middle" font-size="10" letter-spacing="1" fill="${theme.axis}">○ ${kd === 'reverse' ? 'TRUE' : 'TARGET'}   ● ${kd === 'reverse' ? 'YOUR TAP' : 'YOUR WORD'}</text>`;
}

// For the end: the curated words that would have scored most on each target round.
function answers() {
  return targets.map((tg, k) => {
    if (!tg) return null;
    const hits = curatedWords(catOrder[k]).map(w => ({ ...w, d: dist(w, tg), points: pointsFor(dist(w, tg)) })).filter(w => w.points > 0).sort((a, b) => a.d - b.d);
    return { hits: hits.slice(0, 4), best: hits[0] };
  });
}

// ---- Timer ----
const running = () => phase === 'playing' && !pending;
function tick() {
  if (!arena) return;
  let shown, urgent = false;
  if (phase === 'playing') { const rem = remaining(); if (rem <= 0 && !pending) return timeOut(); shown = rem; urgent = rem <= URGENT_SECONDS; }
  else if (phase === 'between') shown = Math.max(0, ROUND_SECONDS - rounds[roundIdx].seconds);
  else if (phase === 'over') shown = rounds.reduce((s, r) => s + (r ? r.seconds : 0), 0);
  else shown = ROUND_SECONDS;
  $('d-clock').textContent = fmt(shown);
  $('d-clock-label').textContent = phase === 'over' ? 'total time' : phase === 'idle' ? 'per round' : `round ${roundIdx + 1}`;
  document.body.classList.toggle('urgent', urgent);
}
setInterval(tick, 100);

// ---- Flow ----
function say(text) { $('d-message').textContent = text; }
function note(text) { $('d-logstatus').textContent = text; }
function showInput(on) { $('d-form').hidden = !on; if (on) { $('d-guess').value = ''; placeCursor(); $('d-guess').focus(); } }

function startGame() { if (phase !== 'idle') return; roundIdx = 0; rounds = []; startRound(); }
function startRound() {
  phase = 'playing'; bossHits = []; roundStart = Date.now(); note('');
  const kd = kind(roundIdx), c = cat(roundIdx).name;
  if (kd === 'reverse') { showInput(false); say(`Where does "${reverseWord.word}" sit? Tap the scope.`); }
  else { say(''); showInput(true); if (kd === 'boss') note(`Boss round: as many ${c.toLowerCase()} words as you can.`); }
  render(); save();
}
function finishRound(result) {
  rounds[roundIdx] = result; phase = 'between'; pending = false;
  showInput(false);
  const next = roundIdx + 1 < ROUNDS ? `Press Enter for round ${roundIdx + 2}.` : 'Press Enter for the result.';
  const line = result.kind === 'boss' ? `Boss: ${result.hits.length} hit${result.hits.length === 1 ? '' : 's'} for ${result.score} pts.`
    : !result.word ? 'Time up. 0 pts.' : `${result.word} · ${result.points} hit + ${result.bonus} time = ${result.score} pts.`;
  say(`${line}  ${next}`); note('');
  document.body.classList.remove('urgent');
  render(); save();
}
function nextRound() {
  if (roundIdx + 1 >= ROUNDS) return endGame();
  roundIdx += 1; startRound();
}
function timeOut() {
  if (phase !== 'playing') return;
  if (kind(roundIdx) === 'boss') return finishRound({ kind: 'boss', cat: catOrder[roundIdx], hits: bossHits, score: bossHits.reduce((s, h) => s + h.points, 0), seconds: ROUND_SECONDS, word: null });
  finishRound({ kind: kind(roundIdx), cat: catOrder[roundIdx], word: null, points: 0, bonus: 0, score: 0, seconds: ROUND_SECONDS, x: reverseWord && kind(roundIdx) === 'reverse' ? reverseWord.x : NaN, y: reverseWord && kind(roundIdx) === 'reverse' ? reverseWord.y : NaN });
}

async function submitWord() {
  const word = normalise($('d-guess').value);
  if (!word || pending) return;
  const kd = kind(roundIdx), ci = catOrder[roundIdx];
  if (kd === 'boss' && bossHits.some(h => h.word === word)) return note(`"${word}" already landed.`);
  pending = true;
  const secondsAt = Math.min(ROUND_SECONDS, elapsed());
  const entry = await lookup(word, ci);
  if (!entry) { pending = false; return note(`"${word}" isn't a word I know.`); }
  if (entry.fit < (cat(roundIdx).threshold ?? FIT_THRESHOLD)) { pending = false; return note(`"${word}" doesn't look like ${cat(roundIdx).name.toLowerCase()} to me.`); }
  $('d-guess').value = ''; placeCursor(); note('');
  const tg = targets[roundIdx], d = dist(entry, tg), points = pointsFor(d);
  pingSound();
  await animatePing(entry);
  if (kd === 'boss') {
    bossHits.push({ word, x: entry.x, y: entry.y, points, d });
    pending = false;
    note(points ? `${word} · ${points} pts${bullseye(d) ? ' · bullseye' : ''}` : `${word} · missed`);
    if (remaining() <= 0) return timeOut();
    render(); return;
  }
  const bonus = timeBonus(points, ROUND_SECONDS - secondsAt);
  finishRound({ kind: kd, cat: ci, word, x: entry.x, y: entry.y, d, points, bonus, score: points + bonus, seconds: Math.round(secondsAt * 10) / 10 });
}

// The reverse round: a tap on the scope is the answer.
function scopeTap(e) {
  if (phase !== 'playing' || kind(roundIdx) !== 'reverse' || pending) return;
  const box = svg.getBoundingClientRect(), scale = 600 / Math.min(box.width, box.height);
  const ox = (box.width - 600 / scale) / 2, oy = (box.height - 600 / scale) / 2; // the 600-box is letterboxed in the stage
  const px = (e.clientX - box.left - ox) * scale, py = (e.clientY - box.top - oy) * scale;
  const click = { x: (px - C) / R, y: (C - py) / R };
  if (Math.hypot(click.x, click.y) > 1.05) return note('Tap inside the scope.');
  const secondsAt = Math.min(ROUND_SECONDS, elapsed()), d = dist(click, reverseWord), points = pointsFor(d), bonus = timeBonus(points, ROUND_SECONDS - secondsAt);
  pingSound();
  finishRound({ kind: 'reverse', cat: catOrder[roundIdx], word: reverseWord.word, x: reverseWord.x, y: reverseWord.y, click, d, points, bonus, score: points + bonus, seconds: Math.round(secondsAt * 10) / 10 });
}

function endGame() {
  phase = 'over';
  showInput(false); say('');
  document.body.classList.add('d-over'); document.body.classList.remove('urgent');
  const sum = total(), bulls = rounds.filter(r => r && r.kind !== 'boss' && r.d !== undefined && bullseye(r.d)).length + rounds.filter(r => r && r.kind === 'boss').reduce((n, r) => n + r.hits.filter(h => bullseye(h.d)).length, 0);
  $('d-result').textContent = `Sonar #${dayNumber}: ${sum} points${bulls ? `, ${bulls} bullseye${bulls > 1 ? 's' : ''}` : ''}.`;
  $('d-share-text').textContent = `Sonar #${dayNumber} · ${sum} pts · ${rounds.map(r => r ? r.score : 0).join(' ')}`;
  $('d-share').hidden = false;
  $('d-reveal').innerHTML = answers().map((a, k) => {
    if (!a) return `<li><span class="n">${k + 1}</span><span class="hint">reverse: "${esc(reverseWord.word)}" sat at ${brgRng(reverseWord)}</span></li>`;
    const r = rounds[k], you = r.kind === 'boss' ? `${r.hits.length} hits` : r.word ? `you: ${esc(r.word)} ${r.points}` : 'no answer';
    const list = a.hits.length ? a.hits.map(h => `${esc(h.word)} <span class="s">${h.points}</span>`).join(', ') : 'nothing curated scores here';
    return `<li><span class="n">${k + 1}</span><span class="hint">${esc(cat(k).name)} · ${you} · best: ${list}</span></li>`;
  }).join('');
  $('d-reveal-wrap').hidden = false;
  render(); save();
}
function again() { // practice: a fresh unseeded day on the same axes; not saved
  practice = true;
  setUpDay(Math.random); axes = arena.pairs[dayNumber % arena.pairs.length];
  rounds = []; roundIdx = 0; phase = 'idle'; bossHits = [];
  document.body.classList.remove('d-over'); $('d-share').hidden = true; $('d-reveal-wrap').hidden = true; $('d-result').textContent = '';
  say('Practice. Press Enter to start.'); render();
}
let practice = false;

// ---- The ping: a pulse from the centre out to the word, which echoes back as a flash ----
const stage = $('d-stage'), ping = $('d-ping'), flash = $('d-flash');
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function animatePing(landing) {
  const box = svg.getBoundingClientRect(), side = Math.min(box.width, box.height), rim = side * R / 600;
  const cx = box.left - stage.getBoundingClientRect().left + box.width / 2, cy = box.top - stage.getBoundingClientRect().top + box.height / 2;
  const reach = Math.min(1.45, Math.max(0.15, Math.hypot(landing.x, landing.y))), dur = 250 + 350 * reach;
  ping.style.display = 'block';
  await ping.animate([{ left: `${cx}px`, top: `${cy}px`, width: '0px', height: '0px', opacity: 1 }, { left: `${cx - rim * reach}px`, top: `${cy - rim * reach}px`, width: `${2 * rim * reach}px`, height: `${2 * rim * reach}px`, opacity: 0.15 }], { duration: dur, easing: 'linear', fill: 'forwards' }).finished;
  ping.style.display = 'none';
  const lx = cx + landing.x * rim, ly = cy - landing.y * rim, fs = side * 0.06;
  flash.style.display = 'block';
  await flash.animate([{ left: `${lx - fs / 2}px`, top: `${ly - fs / 2}px`, width: `${fs}px`, height: `${fs}px`, opacity: 1 }, { left: `${lx - fs / 8}px`, top: `${ly - fs / 8}px`, width: `${fs / 4}px`, height: `${fs / 4}px`, opacity: 0 }], { duration: 300, easing: 'ease-out', fill: 'forwards' }).finished;
  flash.style.display = 'none';
}

// ---- The terminal's cursor: a blinking underline where the next letter goes ----
const guess = $('d-guess'), cursor = $('d-cursor');
function placeCursor() {
  if ($('d-form').hidden) { cursor.style.display = 'none'; return; }
  cursor.style.display = 'block';
  const cs = getComputedStyle(guess), ctx = placeCursor.ctx || (placeCursor.ctx = document.createElement('canvas').getContext('2d'));
  ctx.font = `${cs.fontWeight} ${cs.fontSize} ${cs.fontFamily}`;
  const ls = parseFloat(cs.letterSpacing) || 0, text = guess.value.toUpperCase();
  const width = t => ctx.measureText(t).width + ls * t.length;
  const box = guess.getBoundingClientRect(), host = guess.parentElement.getBoundingClientRect(), mid = box.left - host.left + box.width / 2;
  cursor.style.left = `${text ? mid + width(text) / 2 : mid - width(guess.placeholder.toUpperCase()) / 2}px`;
  cursor.style.width = `${Math.max(14, width('M'))}px`;
  cursor.style.top = `${box.top - host.top + box.height - 6}px`;
  cursor.classList.toggle('empty', !text);
}
guess.addEventListener('input', placeCursor);
new ResizeObserver(placeCursor).observe(document.body);
document.fonts && document.fonts.ready.then(placeCursor);

// Scanline overlays for the screens.
for (const el of document.querySelectorAll('#tab-darts .blk, #tab-darts .stage, header .plate, header .status')) { const d = document.createElement('div'); d.className = 'crt-lines'; d.setAttribute('aria-hidden', 'true'); el.appendChild(d); }

// ---- Settings: CRT effects, the sweep, a ping sound ----
const SETTINGS = { crt: true, sweep: true, sound: false };
function applySettings() {
  document.body.dataset.crt = SETTINGS.crt ? 'on' : 'off';
  document.body.dataset.sweep = SETTINGS.sweep ? 'on' : 'off';
  for (const k of Object.keys(SETTINGS)) $(`s-${k}`).checked = SETTINGS[k];
  try { localStorage.setItem('darts:settings', JSON.stringify(SETTINGS)); } catch {}
}
try { Object.assign(SETTINGS, JSON.parse(localStorage.getItem('darts:settings')) || {}); } catch {}
for (const k of Object.keys(SETTINGS)) $(`s-${k}`).addEventListener('change', e => { SETTINGS[k] = e.target.checked; applySettings(); });
applySettings();
function pingSound() {
  if (!SETTINGS.sound) return;
  try {
    const ac = pingSound.ac || (pingSound.ac = new (window.AudioContext || window.webkitAudioContext)());
    const o = ac.createOscillator(), g = ac.createGain(), t = ac.currentTime;
    o.type = 'sine'; o.frequency.setValueAtTime(1400, t); o.frequency.exponentialRampToValueAtTime(900, t + 0.5);
    g.gain.setValueAtTime(0.0001, t); g.gain.exponentialRampToValueAtTime(0.25, t + 0.02); g.gain.exponentialRampToValueAtTime(0.0001, t + 0.7);
    o.connect(g).connect(ac.destination); o.start(t); o.stop(t + 0.75);
  } catch {}
}

// ---- Look ----
function applyTheme(name) {
  theme = THEMES[name] || THEMES.graphite;
  document.body.dataset.theme = THEMES[name] ? name : 'graphite';
  document.body.dataset.family = 'console';
  render();
}

// ---- Persistence: today's game survives a refresh ----
const key = () => `sonar:${date}`;
function save() {
  if (practice) return;
  try { localStorage.setItem(key(), JSON.stringify({ phase, roundIdx, roundStart, rounds, bossHits })); } catch {}
}
function restore() {
  let saved; try { saved = JSON.parse(localStorage.getItem(key())); } catch {}
  if (!saved || saved.phase === 'idle') return;
  rounds = saved.rounds || []; roundIdx = saved.roundIdx || 0; roundStart = saved.roundStart || Date.now(); bossHits = saved.bossHits || [];
  phase = saved.phase;
  if (phase === 'over') { phase = 'between'; roundIdx = ROUNDS - 1; endGame(); return; }
  if (phase === 'between') { const r = rounds[roundIdx]; const next = roundIdx + 1 < ROUNDS ? `Press Enter for round ${roundIdx + 2}.` : 'Press Enter for the result.'; say(`${r && r.word ? `${r.word} · ${r.score} pts.` : r && r.kind === 'boss' ? `Boss: ${r.score} pts.` : 'Time up. 0 pts.'}  ${next}`); showInput(false); return; }
  if (phase === 'playing') { // the clock kept running while the page was away
    const kd = kind(roundIdx);
    if (kd === 'reverse') { showInput(false); say(`Where does "${reverseWord.word}" sit? Tap the scope.`); } else showInput(true);
    if (remaining() <= 0) timeOut();
  }
}

// ---- Wiring ----
function advance() { // Enter, or a tap on the terminal: start, submit, or move on
  if (phase === 'idle') startGame();
  else if (phase === 'playing' && kind(roundIdx) !== 'reverse') submitWord();
  else if (phase === 'between') nextRound();
}
$('d-form').addEventListener('submit', e => { e.preventDefault(); advance(); });
guess.addEventListener('keydown', e => { if (e.key === 'Enter') { e.preventDefault(); advance(); } });
document.addEventListener('keydown', e => { if (e.key === 'Enter' && e.target !== guess && !e.target.closest('button, details, label')) { e.preventDefault(); advance(); } });
$('d-message').addEventListener('click', advance);
$('d-stage').addEventListener('click', e => { if (phase === 'playing' && kind(roundIdx) === 'reverse') scopeTap(e); else if (phase === 'idle' || phase === 'between') advance(); });
$('d-again').addEventListener('click', again);
$('d-copy').addEventListener('click', () => navigator.clipboard.writeText($('d-share-text').textContent).then(() => { $('d-copy').textContent = 'Copied'; }));

window.sonarDebug = () => ({ axes, catOrder, targets, reverseWord, phase, roundIdx, rounds, lookup: (w, ci) => lookup(w, ci) });

// ---- Load the day ----
(async () => {
  try {
    arena = await fetch('puzzles/arena/arena.json').then(r => r.json());
    const now = new Date(), params = new URLSearchParams(location.search);
    date = params.get('day') || `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    dayNumber = Math.round((Date.parse(date) - Date.parse(arena.launch)) / 864e5) + 1;
    if (params.has('fresh')) { try { localStorage.removeItem(key()); } catch {} }
    setUpDay(mulberry32(fnv1a(`sonar:${date}`)));
    $('d-sub').textContent = `#${dayNumber} · ${now.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'long' })}`;
    applyTheme(params.get('theme') || 'graphite');
    say('Press Enter to start.'); showInput(false);
    restore();
    render();
  } catch (err) {
    $('d-sub').textContent = `Couldn't load today's game (${err.message}). Serve this folder over http.`;
  }
})();
})();
