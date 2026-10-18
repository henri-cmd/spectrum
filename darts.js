// Darts — the second game, on the Darts tab. Reuses today's Spectrum puzzle data: two of its four
// spectrums become the board's axes, and a target is set at a random point on the board.
// Everything lives in one closure so nothing collides with game.js.
(() => {
const DARTS = 5;
const SHARDS = 256;
const FIT_THRESHOLD = 25;    // same leniency as Spectrum
const TARGET_RADIUS = 0.75;  // targets stay inside this radius so a real word can always get close
const BULL = 0.1;            // a dart within this distance is a bullseye
const C = 300, R = 215;      // board centre and the screen length of one unit
const GRID = 0.25;           // matrix spacing, in units

// ---- Scoring: the one place to change the rule ----
// A dart scores by its distance from the target: 100 inside the bull, then falling to 0 one unit away.
// The game's score is the best dart.
function scoreDart(d) {
  if (d <= BULL) return 100;
  return Math.max(0, Math.min(99, Math.round(100 * (1 - d))));
}
const scoreGame = throws => throws.length ? Math.max(...throws.map(t => t.score)) : 0;

// ---- State ----
let puzzle;               // today's Spectrum puzzle: {id, category, spectrums, date, number}
let axes = [0, 1];        // which of the puzzle's spectrums run left→right and bottom→top
let target = { x: 0, y: 0 };
let throws = [];          // {word, x, y, d, score}
let started = false, over = false, practice = false;
const shardCache = new Map();

const $ = id => document.getElementById(id);
const svg = $('d-board');
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const normalise = s => s.trim().toLowerCase().replace(/[^a-z\s-]/g, '').replace(/[\s-]+/g, ' ').trim();
const sx = x => C + x * R, sy = y => C - y * R;   // units → screen

// ---- Seeded random: everyone gets the same target on the same day ----
function fnv1a(s) {
  let h = 0x811c9dc5;
  for (const b of new TextEncoder().encode(s)) h = Math.imul(h ^ b, 0x01000193) >>> 0;
  return h;
}
function mulberry32(a) {
  return () => {
    a = (a + 0x6D2B79F5) >>> 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
// Picks the two axes and a target uniformly inside the target disc.
function setUp(rand) {
  const a = Math.floor(rand() * 4), b = (a + 1 + Math.floor(rand() * 3)) % 4;
  axes = [a, b];
  const ang = rand() * 2 * Math.PI, r = Math.sqrt(rand()) * TARGET_RADIUS;
  target = { x: Math.round(100 * r * Math.cos(ang)) / 100, y: Math.round(100 * r * Math.sin(ang)) / 100 };
}

// ---- Word lookup (same shard files as Spectrum) ----
async function shard(word) {
  const key = (fnv1a(word) % SHARDS).toString(16).padStart(2, '0');
  if (!shardCache.has(key)) shardCache.set(key, fetch(`puzzles/${puzzle.id}/w/${key}.json`).then(r => r.ok ? r.json() : {}));
  return shardCache.get(key);
}
async function lookup(word) {
  const parts = word.split(' ');
  const entries = await Promise.all(parts.map(async p => (await shard(p))[p]));
  if (entries.some(e => !e)) return null;
  const at = i => entries.reduce((s, e) => s + e[i], 0) / entries.length / 100;
  return { x: at(axes[0]), y: at(axes[1]), fit: Math.min(...entries.map(e => e[4])) };
}

// ---- Board ----
function render() {
  if (!puzzle) return;
  const [X, Y] = axes.map(i => puzzle.spectrums[i]);
  let s = `<defs><clipPath id="d-clip"><circle cx="${C}" cy="${C}" r="${R}"/></clipPath></defs>`;
  s += `<circle cx="${C}" cy="${C}" r="${R}" fill="#fafafa" stroke="#111" stroke-width="1.5"/>`;
  // The matrix: grid lines every GRID units, clipped to the board; the two axes through the centre are darker.
  s += '<g clip-path="url(#d-clip)">';
  for (let v = -1; v <= 1.001; v += GRID) {
    const main = Math.abs(v) < 1e-9, col = main ? '#999' : '#e2e2e2';
    s += `<line x1="${sx(v)}" y1="${sy(-1)}" x2="${sx(v)}" y2="${sy(1)}" stroke="${col}" stroke-width="1"/>`;
    s += `<line x1="${sx(-1)}" y1="${sy(v)}" x2="${sx(1)}" y2="${sy(v)}" stroke="${col}" stroke-width="1"/>`;
  }
  s += `<circle cx="${C}" cy="${C}" r="${R * 0.5}" fill="none" stroke="#ccc" stroke-width="1" stroke-dasharray="3 4"/>`;
  s += '</g>';
  // Axis end words.
  s += `<text class="axis" x="${sx(-1) - 10}" y="${C + 5}" text-anchor="end">${esc(X.low)}</text>`;
  s += `<text class="axis" x="${sx(1) + 10}" y="${C + 5}" text-anchor="start">${esc(X.high)}</text>`;
  s += `<text class="axis" x="${C}" y="${sy(1) - 12}" text-anchor="middle">${esc(Y.high)}</text>`;
  s += `<text class="axis" x="${C}" y="${sy(-1) + 22}" text-anchor="middle">${esc(Y.low)}</text>`;
  if (!started) { svg.innerHTML = s; return; }
  // Target: a crosshair with the bull drawn to scale.
  const tx = sx(target.x), ty = sy(target.y);
  s += `<circle cx="${tx}" cy="${ty}" r="${BULL * R}" fill="#c00" fill-opacity="0.15" stroke="#c00" stroke-width="1.5"/>`;
  s += `<line x1="${tx - 16}" y1="${ty}" x2="${tx + 16}" y2="${ty}" stroke="#c00" stroke-width="1.5"/>`;
  s += `<line x1="${tx}" y1="${ty - 16}" x2="${tx}" y2="${ty + 16}" stroke="#c00" stroke-width="1.5"/>`;
  s += `<circle cx="${tx}" cy="${ty}" r="2.5" fill="#c00"/>`;
  // Darts: the newest is filled and tied to the target with a dashed line.
  const labels = [];
  throws.forEach((t, k) => {
    const x = sx(t.x), y = sy(t.y), last = k === throws.length - 1;
    if (last && !over) s += `<line x1="${x}" y1="${y}" x2="${tx}" y2="${ty}" stroke="#999" stroke-width="1" stroke-dasharray="2 3"/>`;
    s += `<circle cx="${x}" cy="${y}" r="5" fill="${last ? '#111' : '#fff'}" stroke="#111" stroke-width="1.7"/>`;
    labels.push({ x, y, word: t.word, n: k + 1 });
  });
  // Words beside their darts: to the right unless near the right edge; pushed down when they'd overlap.
  for (const l of labels) {
    const right = l.x < C + R * 0.55, w = (l.word.length + 2) * 7.5;
    l.tx = right ? l.x + 10 : l.x - 10; l.anchor = right ? 'start' : 'end'; l.ty = l.y + 4;
    l.x0 = right ? l.tx : l.tx - w; l.x1 = l.x0 + w;
  }
  for (let pass = 0; pass < 4; pass++) for (let a = 0; a < labels.length; a++) for (let b = a + 1; b < labels.length; b++) {
    const A = labels[a], B = labels[b];
    if (A.x0 < B.x1 && B.x0 < A.x1 && Math.abs(A.ty - B.ty) < 15) B.ty = A.ty + 15;
  }
  for (const l of labels) s += `<text class="tag" x="${l.tx}" y="${l.ty}" text-anchor="${l.anchor}">${esc(l.word)}</text>`;
  svg.innerHTML = s;
  $('d-legend').textContent = `✚ target   ○ dart   ● latest dart${practice ? '   · practice target' : ''}`;
}

// ---- Readout ----
function hint(t) {
  if (t.d <= BULL) return 'bullseye!';
  const parts = [];
  axes.forEach((i, k) => {
    const gap = (k === 0 ? t.x - target.x : t.y - target.y);
    if (Math.abs(gap) < 0.12) return;
    const sp = puzzle.spectrums[i];
    parts.push(`${Math.abs(gap) > 0.6 ? 'much ' : ''}more ${sp[gap > 0 ? 'low' : 'high']}`);
  });
  const off = Math.hypot(t.x, t.y) > 1 ? 'off the board — ' : '';
  return off + (parts.length ? `needs ${parts.join(', ')}` : 'so close');
}
function renderReadout() {
  $('d-readout').innerHTML = throws.map((t, k) =>
    `<li><span class="n">${k + 1}</span><span class="w">${esc(t.word)}</span><span class="s">${t.score}</span><span class="hint">${hint(t)}</span></li>`).join('');
}

// ---- Game flow ----
function msg(text, colour = '#a00') { $('d-message').textContent = text; $('d-message').style.color = colour; }

function start() {
  started = true;
  $('d-start').hidden = true;
  $('d-form').hidden = false;
  render();
  $('d-guess').focus();
  save();
}

async function submitThrow(e) {
  e.preventDefault();
  if (over) return;
  const word = normalise($('d-guess').value);
  if (!word) return;
  if (throws.some(t => t.word === word)) return msg(`You already threw "${word}".`);
  $('d-submit').disabled = true;
  const entry = await lookup(word);
  $('d-submit').disabled = false;
  if (!entry) return msg(`"${word}" isn't a word I know.`);
  if (entry.fit < FIT_THRESHOLD) return msg(`"${word}" doesn't look like ${puzzle.category.toLowerCase()} to me — try another word.`);
  $('d-guess').value = '';
  msg('');
  addThrow(word, entry);
  save();
}

function addThrow(word, entry) {
  const d = Math.hypot(entry.x - target.x, entry.y - target.y);
  throws.push({ word, x: entry.x, y: entry.y, d, score: scoreDart(d) });
  renderReadout();
  render();
  if (d <= BULL || throws.length === DARTS) return endGame();
  if (throws.length === DARTS - 1) msg('Last dart.', '#111');
}

function endGame() {
  over = true;
  $('d-form').hidden = true;
  msg('');
  const best = throws.reduce((a, b) => b.score > a.score ? b : a);
  const bull = best.d <= BULL;
  const total = throws.reduce((s, t) => s + t.score, 0);
  $('d-result').textContent = bull
    ? `Bullseye with "${best.word}" on dart ${throws.indexOf(best) + 1}! Score ${best.score}.`
    : `Best dart "${best.word}", ${best.score}. Total ${total} over ${throws.length}.`;
  $('d-share-text').textContent = `Darts #${puzzle.number} ${bull ? '🎯' : '🏹'} ${best.score} · ${throws.map(t => t.score).join(' ')}`;
  $('d-share').hidden = false;
  render();
}

// A fresh, unseeded target on the same board for another go. Practice games aren't saved.
function again() {
  practice = true; over = false; throws = [];
  const keep = axes;
  setUp(Math.random);
  axes = keep;
  $('d-readout').innerHTML = ''; $('d-result').textContent = ''; $('d-share').hidden = true;
  $('d-form').hidden = false;
  render();
  $('d-guess').focus();
}

// ---- Persistence ----
const key = () => `darts:${puzzle.id}:${puzzle.date}`;
function save() {
  if (practice) return;
  try { localStorage.setItem(key(), JSON.stringify({ started, words: throws.map(t => t.word) })); } catch {}
}
async function restore() {
  let saved;
  try { saved = JSON.parse(localStorage.getItem(key())); } catch {}
  if (!saved || !saved.started) return;
  start();
  for (const w of saved.words) {
    if (over) break;
    const entry = await lookup(w);
    if (entry) addThrow(w, entry);
  }
  save();
}

// ---- Wiring ----
$('d-go').addEventListener('click', start);
$('d-form').addEventListener('submit', submitThrow);
$('d-again').addEventListener('click', again);
$('d-copy').addEventListener('click', () => navigator.clipboard.writeText($('d-share-text').textContent).then(() => { $('d-copy').textContent = 'Copied'; }));

// ---- Load today's puzzle (same schedule as Spectrum) ----
(async () => {
  try {
    const index = await fetch('puzzles/index.json').then(r => r.json());
    const now = new Date();
    const date = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`;
    const params = new URLSearchParams(location.search);
    const id = params.get('puzzle') || index.days[date];
    if (!id) throw new Error(`no puzzle scheduled for ${date} — run build.py`);
    if (params.has('fresh')) { try { localStorage.removeItem(`darts:${id}:${date}`); } catch {} }
    puzzle = await fetch(`puzzles/${id}/puzzle.json`).then(r => r.json());
    puzzle.date = date;
    puzzle.number = Math.round((Date.parse(date) - Date.parse(index.launch)) / 864e5) + 1;
    setUp(mulberry32(fnv1a(`darts:${id}:${date}`)));
    $('d-sub').textContent = `#${puzzle.number} · ${now.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })} · ${puzzle.category}`;
    render();
    $('d-go').disabled = false;
    await restore();
  } catch (err) {
    $('d-sub').textContent = `Couldn't load today's board (${err.message}). Serve this folder over http.`;
  }
})();
})();
