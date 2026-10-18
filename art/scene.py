"""Saloon interior background, 240x300, native pixels. Run: .venv/bin/python art/scene.py"""
import math, os, random
from PIL import Image

W, H = 240, 300
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def h(s): s = s.lstrip('#'); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)
PAL = {k: h(v) for k, v in dict(
    black='15090a', shadow='2a1710', wdark='5a2f1a', wmid='7a4426', wlight='9b5a2e',
    whi='b8763a', wpale='d9a066', cream='f3e2b4', tan='c9a46a', red='c8322e', dred='8e1d1d',
    pinkl='e9a0a0', pinkm='e07070', orange='e8792b', gold='f2b544', dusk='5a2a3a',
    glow='ffb347', gtext='f0c050', green='4f6b3a', skin='e0a885', shirt='a3241f', hat='3b2418').items()}
globals().update({'C_' + k: v for k, v in PAL.items()})

img = Image.new('RGBA', (W, H), PAL['shadow'])
P = img.load()

def px(x, y, c):
    if 0 <= x < W and 0 <= y < H: P[x, y] = c
def rect(x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): px(x, y, c)
def frame_rect(x0, y0, x1, y1, c):
    for x in range(x0, x1 + 1): px(x, y0, c); px(x, y1, c)
    for y in range(y0, y1 + 1): px(x0, y, c); px(x1, y, c)
def rr_dist(dx, dy): return int(math.sqrt(dx * dx + dy * dy) + 0.5)
def circle_fill(cx, cy, r, c):
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            if rr_dist(x - cx, y - cy) <= r: px(x, y, c)

# --- sprite dict helpers: pix = {(x,y): colour}; blit adds 1px black outline -----
def d_rect(d, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): d[(x, y)] = c
def blit(d, outline=True):
    if outline:
        for (x, y) in list(d):
            for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if (x + ox, y + oy) not in d: px(x + ox, y + oy, PAL['black'])
    for (x, y), c in d.items(): px(x, y, c)
def from_rows(rows, ox, oy, key, mirror=False):
    d = {}
    for j, row in enumerate(rows):
        row = row.ljust(max(len(r) for r in rows), '.')
        if mirror: row = row + row[::-1]
        for i, ch in enumerate(row):
            if ch in key: d[(ox + i, oy + j)] = PAL[key[ch]]
    return d

UP = {'shadow': 'wdark', 'wdark': 'wmid', 'wmid': 'wlight', 'wlight': 'whi', 'whi': 'wpale'}
DOWN = {v: k for k, v in UP.items()}
UPC = {PAL[k]: PAL[v] for k, v in UP.items()}
DOWNC = {PAL[k]: PAL[v] for k, v in DOWN.items()}
def remap(x, y, table):
    if 0 <= x < W and 0 <= y < H and P[x, y] in table: P[x, y] = table[P[x, y]]

# =============================== WALL ===========================================
rnd = random.Random(7)
PLANK = 9
for y in range(0, 216):
    idx = y // PLANK; r = y % PLANK
    base = PAL['wdark'] if idx % 2 == 0 else PAL['wmid']
    for x in range(W):
        P[x, y] = PAL['shadow'] if r == PLANK - 1 else base
    if r == 0:  # lit top edge of each plank
        for x in range(W): P[x, y] = PAL['wmid'] if idx % 2 == 0 else PAL['wlight']
    # butt joints
    off = (idx * 53) % 70
    for x in range(off, W, 70):
        if r < PLANK - 1: P[x, y] = PAL['shadow']
# grain dashes
for idx in range(216 // PLANK):
    for _ in range(4):
        gx = rnd.randrange(2, W - 10); gy = idx * PLANK + rnd.randrange(2, 7)
        ln = rnd.randrange(3, 8)
        c = PAL['wmid'] if idx % 2 == 0 else (PAL['whi'] if rnd.random() < 0.3 else PAL['wlight'])
        for x in range(gx, gx + ln):
            if P[x, gy] in (PAL['wdark'], PAL['wmid']): P[x, gy] = c
# lamp halo (two concentric glow steps, lighter wood colours)
LX, LY = 36, 60
for y in range(0, 216):
    for x in range(W):
        d = rr_dist(x - LX, y - LY)
        if d <= 36: remap(x, y, UPC)
        if d <= 20: remap(x, y, UPC)

# =============================== LEFT WALL ======================================
# shelf with bottles
rect(3, 82, 41, 84, PAL['wlight']); frame_rect(3, 82, 41, 84, PAL['black'])
rect(4, 82, 40, 82, PAL['whi'])
rect(6, 85, 7, 87, PAL['wdark']); rect(37, 85, 38, 87, PAL['wdark'])
bottle_rows = ["..xx..", "..xx..", "..xx..", ".gggg.", "gggggg", "gggggg", "gggggg", "gggggg", "gggggg", "gggggg"]
for i, col in enumerate(('green', 'gold', 'green', 'gold')):
    d = {}
    ox = 5 + i * 9
    for j, row in enumerate(bottle_rows):
        for k, ch in enumerate(row):
            if ch == 'x': d[(ox + k, 72 + j)] = PAL['hat'] if i % 2 == 0 else PAL['wdark']
            elif ch == 'g': d[(ox + k, 72 + j)] = PAL[col]
    d[(ox + 1, 77)] = PAL['cream']; d[(ox + 1, 78)] = PAL['cream']
    if col == 'gold': d[(ox + 4, 80)] = PAL['orange']; d[(ox + 4, 79)] = PAL['orange']; d[(ox + 5, 80)] = PAL['orange']
    else: d[(ox + 4, 80)] = PAL['hat']; d[(ox + 5, 80)] = PAL['hat']; d[(ox + 5, 79)] = PAL['hat']
    blit(d)

# oil lamp
LAMP_X = 36
rect(6, 36, 9, 52, PAL['hat']); frame_rect(5, 35, 10, 53, PAL['black']); px(7, 38, PAL['wlight']); px(7, 50, PAL['wlight'])
rect(10, 42, 36, 43, PAL['hat']); frame_rect(10, 41, 37, 44, PAL['black']); rect(10, 42, 36, 42, PAL['wdark'])
rect(11, 42, 36, 42, PAL['wmid'])
for k in range(8): px(10 + k, 51 - k, PAL['black']); px(11 + k, 51 - k, PAL['hat'])
d = {}
for k in range(5): d[(LAMP_X, 45 + k)] = PAL['hat'] if k % 2 == 0 else PAL['wmid']
d[(LAMP_X, 44)] = PAL['hat']
d_rect(d, 33, 50, 39, 51, PAL['hat']); d_rect(d, 34, 49, 38, 49, PAL['wmid'])
for y in range(52, 67):
    for x in range(30, 43):
        dx = x - LAMP_X; dy = y - 59
        if dx * dx * 64 + dy * dy * 25 <= 25 * 64 + 200:
            d[(x, y)] = PAL['glow']
d[(33, 54)] = d[(33, 55)] = PAL['cream']
for y in range(55, 64):
    wdt = 1 if y in (55, 63) else (2 if y in (56, 62) else 3)
    for x in range(LAMP_X - wdt + 1 if wdt > 1 else LAMP_X, LAMP_X + (wdt if wdt > 1 else 1)): d[(x, y)] = PAL['gold']
for y in range(57, 61): d[(LAMP_X, y)] = PAL['cream']
d_rect(d, 32, 67, 40, 68, PAL['hat']); d_rect(d, 33, 69, 39, 69, PAL['hat'])
blit(d)

# longhorn skull
SK_KEY = {'o': 'black', 'c': 'cream', 't': 'tan', 'd': 'shadow', 'h': 'wpale'}
sk_rows = [
 "oo............",
 "oco...........",
 "otco....ooooo.",
 "otco...occcccc",
 "otco..occcccct",
 "otcco.occcccct",
 ".otccoocccccct",
 ".otcctoccdddct",
 "..otttoccdddct",
 "...ooootcdddct",
 "......otcccctt",
 "......ottcdcdt",
 ".......ootcdtt",
 ".........oottt",
 "...........ooo",
]
sk = from_rows(sk_rows, 56, 33, SK_KEY, mirror=True)
for (x, y) in list(sk):
    if sk[(x, y)] == PAL['black']:
        pass
for k, v in sk.items(): px(k[0], k[1], v)
# nose bridge + forehead centre shading
px(70, 37, PAL['tan']); px(69, 37, PAL['tan']); px(70, 36, PAL['cream'])
# drop shadow of skull on wall (one step down), under-right
for (x, y) in sk:
    if (x + 1, y + 1) not in sk: remap(x + 1, y + 1, DOWNC)
for k, v in sk.items(): px(k[0], k[1], v)

# poster
PX0, PY0, PX1, PY1 = 5, 94, 38, 140
rect(PX0 + 1, PY0 + 1, PX1 + 2, PY1 + 2, PAL['shadow'])  # drop shadow right/below
rect(PX0, PY0, PX1, PY1, PAL['tan']); frame_rect(PX0, PY0, PX1, PY1, PAL['black'])
frame_rect(PX0 + 1, PY0 + 1, PX1 - 1, PY1 - 1, PAL['cream'])
frame_rect(PX0 + 2, PY0 + 2, PX1 - 2, PY1 - 2, PAL['cream'])
FONT = {
 'A': "010101111101101", 'C': "011100100100011", 'D': "110101101101110", 'G': "011100101101011",
 'I': "111010010010111", 'K': "101101110101101", 'M': "101111111101101", 'N': "111101101101101",
 'O': "111101101101111", 'P': "111101111100100", 'R': "110101110101101", 'S': "011100010001110",
 'Y': "101101010010010"}
def text(s, cx, y, c):
    wdt = len(s) * 4 - 1; x0 = cx - wdt // 2
    for i, ch in enumerate(s):
        g = FONT[ch]
        for j in range(15):
            if g[j] == '1': px(x0 + i * 4 + j % 3, y + j // 3, c)
cxp = (PX0 + PX1) // 2
ink = PAL['hat']
text("GOOD", cxp, PY0 + 6, ink); text("DRINKS", cxp, PY0 + 13, PAL['dred'])
for k in range(-5, 6): px(cxp + k, PY0 + 21, ink if k % 2 == 0 else PAL['wlight'])
px(cxp, PY0 + 20, ink); px(cxp, PY0 + 22, ink)
text("GOOD", cxp, PY0 + 26, ink); text("COMPANY", cxp, PY0 + 33, PAL['dred'])
for (x, y) in ((PX0 + 1, PY0 + 1), (PX1 - 1, PY0 + 1), (PX0 + 1, PY1 - 1), (PX1 - 1, PY1 - 1)):
    px(x, y, PAL['black'])
px(PX0 + 1, PY0 + 1, PAL['red']); px(PX1 - 1, PY0 + 1, PAL['red'])

# =============================== RIGHT WALL: WINDOW =============================
WX0, WY0, WX1, WY1 = 205, 80, 236, 165
rect(WX0 + 1, WY0 + 1, WX1 + 2, WY1 + 2, PAL['shadow'])
rect(WX0, WY0, WX1, WY1, PAL['wpale']); frame_rect(WX0, WY0, WX1, WY1, PAL['black'])
IX0, IY0, IX1, IY1 = WX0 + 4, WY0 + 4, WX1 - 4, WY1 - 6
bands = [(IY0, 'gold'), (IY0 + 17, 'orange'), (IY0 + 34, 'dred'), (IY0 + 52, 'dusk')]
for y in range(IY0, IY1 + 1):
    col = None
    for by, bc in bands:
        if y >= by: col = bc
    rect(IX0, y, IX1, y, PAL[col])
# sun
SUNX, SUNY = 216, IY0 + 36
for y in range(SUNY - 8, SUNY + 9):
    for x in range(SUNX - 8, SUNX + 9):
        if rr_dist(x - SUNX, y - SUNY) <= 6 and IX0 <= x <= IX1 and y < IY0 + 48:
            px(x, y, PAL['gold'])
# mesas (flat dusk purple silhouettes, stepped sides)
def mesa(x0, x1, top, base=IY0 + 52):
    for x in range(x0, x1 + 1):
        t = top
        if x in (x0, x1): t = top + 3
        elif x in (x0 + 1, x1 - 1): t = top + 1
        rect(x, t, x, base, PAL['dusk'])
mesa(IX0, IX0 + 9, IY0 + 46)
mesa(224, IX1, IY0 + 40)
rect(IX0, IY0 + 52, IX1, IY1, PAL['dusk'])
# frame inner bevel + muntins
frame_rect(IX0 - 1, IY0 - 1, IX1 + 1, IY1 + 1, PAL['black'])
rect(IX0 - 1, IY1 + 2, IX1 + 1, IY1 + 2, PAL['wmid'])
px(IX0 - 1, IY0 - 1, PAL['black'])
rect(IX0, IY0 + 15, IX1, IY0 + 16, PAL['wpale']); rect(IX0, IY0 + 14, IX1, IY0 + 14, PAL['black']); rect(IX0, IY0 + 17, IX1, IY0 + 17, PAL['black'])
# frame shading (light upper-left): lit top/left, shaded bottom/right
rect(WX0 + 1, WY0 + 1, WX1 - 1, WY0 + 1, PAL['cream'])
rect(WX0 + 1, WY0 + 1, WX0 + 1, WY1 - 1, PAL['cream'])
rect(WX1 - 1, WY0 + 2, WX1 - 1, WY1 - 1, PAL['whi'])
# sill
rect(WX0 - 2, WY1 - 4, WX1 + 2, WY1 - 2, PAL['wpale']); frame_rect(WX0 - 2, WY1 - 4, WX1 + 2, WY1 - 2, PAL['black'])
rect(WX0 - 1, WY1 - 3, WX1 + 1, WY1 - 3, PAL['cream'])
rect(WX0 - 1, WY1 - 2, WX1 + 1, WY1 - 2, PAL['whi'])
rect(WX0 - 1, WY1 - 1, WX1 + 1, WY1 - 1, PAL['wdark'])
# rider on horse (silhouette)
rider_rows = [
 "......xx.....",
 ".....xxxx....",
 "......xx...xx",
 ".....xxxx.xx.",
 "..xxxxxxxxxx.",
 ".xxxxxxxxxxx.",
 "xxxxxxxxxxx..",
 "xxxxxxxxxxxx.",
 ".x.xx...xx.x.",
 ".x.x....x..x.",
]
rd = from_rows(rider_rows, 212, IY1 - 9, {'x': 'black'})
for k, v in rd.items(): px(k[0], k[1], v)
# hat and arm tweak


# =============================== FLOOR ==========================================
for y in range(216, H):
    u = y - 216
    for x in range(W):
        s = x + u
        b = s // 14
        c = PAL['wmid'] if b % 2 == 0 else PAL['wlight']
        if s % 14 == 0: c = PAL['wdark']
        # staggered butt joints along the boards
        if (u + b * 13) % 31 == 0 and s % 14 in (3, 4, 5, 6): c = PAL['wdark']
        P[x, y] = c
# grain flecks
for _ in range(60):
    gx = rnd.randrange(0, W - 5); gy = rnd.randrange(220, H)
    for k in range(3):
        if P[gx + k, gy] == PAL['wlight']: P[gx + k, gy] = PAL['whi']
        elif P[gx + k, gy] == PAL['wmid']: P[gx + k, gy] = PAL['wlight']
rect(0, 216, W - 1, 216, PAL['shadow']); rect(0, 217, W - 1, 217, PAL['wdark']); rect(0, 218, W - 1, 218, PAL['wmid'])
# lamp-lit patch
def in_ell(x, y, cx, cy, rx, ry): return ((x - cx) * (x - cx) * ry * ry + (y - cy) * (y - cy) * rx * rx) <= rx * rx * ry * ry
for y in range(219, H):
    for x in range(W):
        if in_ell(x, y, 120, 262, 42, 34): remap(x, y, UPC)
        if in_ell(x, y, 120, 262, 24, 19): remap(x, y, UPC)

# =============================== DARTBOARD FRAME ================================
BX, BY, RO, RI = 120, 128, 80, 70
# soft shadow (2px darker offset down-right): step existing colours down
for y in range(BY - RO - 2, BY + RO + 4):
    for x in range(BX - RO - 2, BX + RO + 4):
        if rr_dist(x - BX - 2, y - BY - 2) <= RO: remap(x, y, DOWNC)
for y in range(BY - RO, BY + RO + 1):
    for x in range(BX - RO, BX + RO + 1):
        dx, dy = x - BX, y - BY
        r = rr_dist(dx, dy)
        if r > RO: continue
        lit = (dx + dy) < 0
        if r == RO: c = PAL['black']
        elif r > RI + 1:
            c = PAL['wmid'] if lit else PAL['wdark']
            if r == RO - 1: c = PAL['wlight'] if lit else PAL['hat']
        elif r == RI + 1: c = PAL['whi']
        else: c = PAL['shadow']
        if RI + 1 < r < RO - 1:
            for k in range(12):
                th = math.radians(15 + 30 * k)
                if dx * math.cos(th) + dy * math.sin(th) > 0 and abs(dx * math.sin(th) - dy * math.cos(th)) < 0.5:
                    c = PAL['wdark'] if lit else PAL['shadow']
        P[x, y] = c

# =============================== BAR + BARTENDER ================================
BCX = 32
bt = {}
d_rect(bt, BCX - 5, 144, BCX + 4, 150, PAL['hat'])             # crown
d_rect(bt, BCX - 5, 147, BCX + 4, 147, PAL['wdark'])           # hat band
d_rect(bt, BCX - 9, 151, BCX + 8, 152, PAL['hat'])             # brim
d_rect(bt, BCX - 5, 153, BCX + 4, 161, PAL['skin'])            # face
d_rect(bt, BCX - 6, 156, BCX - 6, 158, PAL['skin']); d_rect(bt, BCX + 5, 156, BCX + 5, 158, PAL['skin'])  # ears
for (x, y) in ((BCX - 3, 155), (BCX + 2, 155)): bt[(x, y)] = PAL['black']
d_rect(bt, BCX - 1, 156, BCX, 157, PAL['wpale'])                # nose
d_rect(bt, BCX - 5, 158, BCX + 4, 163, PAL['shadow'])           # beard
d_rect(bt, BCX - 6, 157, BCX - 5, 160, PAL['shadow']); d_rect(bt, BCX + 4, 157, BCX + 5, 160, PAL['shadow'])
d_rect(bt, BCX - 2, 159, BCX + 1, 159, PAL['skin'])             # mouth gap
d_rect(bt, BCX - 1, 160, BCX, 160, PAL['dred'])
d_rect(bt, BCX - 12, 164, BCX + 11, 179, PAL['cream'])          # shirt
d_rect(bt, BCX - 13, 166, BCX - 13, 179, PAL['cream']); d_rect(bt, BCX + 12, 166, BCX + 12, 179, PAL['tan'])
d_rect(bt, BCX + 9, 164, BCX + 11, 179, PAL['tan'])             # shaded right side
d_rect(bt, BCX - 8, 164, BCX - 3, 179, PAL['hat']); d_rect(bt, BCX + 2, 164, BCX + 7, 179, PAL['hat'])  # waistcoat
d_rect(bt, BCX - 2, 164, BCX + 1, 179, PAL['cream'])           # shirt V gap
for k in range(3): bt[(BCX - 2 + k, 164 + k)] = PAL['tan']; bt[(BCX + 1 - k, 164 + k)] = PAL['tan']
bt[(BCX - 5, 170)] = PAL['gtext']; bt[(BCX - 5, 175)] = PAL['gtext']; bt[(BCX + 4, 170)] = PAL['gtext']; bt[(BCX + 4, 175)] = PAL['gtext']
# arms resting on bar
d_rect(bt, BCX - 24, 176, BCX - 13, 179, PAL['cream']); d_rect(bt, BCX - 27, 177, BCX - 25, 179, PAL['skin'])
d_rect(bt, BCX + 12, 176, BCX + 23, 179, PAL['tan']); d_rect(bt, BCX + 24, 177, BCX + 26, 179, PAL['skin'])
d_rect(bt, BCX - 24, 176, BCX - 14, 176, PAL['cream'])
for (x, y) in ((BCX - 12, 164), (BCX - 11, 164), (BCX + 11, 164), (BCX + 10, 164), (BCX - 12, 165), (BCX + 11, 165)): bt.pop((x, y), None)
blit(bt)
# counter
CX0, CX1, CY0, CY1 = 0, 72, 180, 215
rect(CX0, CY0, CX1, CY1, PAL['wlight'])
rect(CX0, CY0 + 1, CX1, CY0 + 2, PAL['whi'])        # lit top edge
rect(CX0, CY0 + 3, CX1, CY0 + 3, PAL['wmid'])
rect(CX0, CY0 + 4, CX1, CY0 + 4, PAL['wdark'])      # under-lip shadow
for px0 in (3, 27, 51):                              # raised panels
    frame_rect(px0, 188, px0 + 18, 208, PAL['wdark'])
    frame_rect(px0 + 1, 189, px0 + 17, 207, PAL['wmid'])
    rect(px0 + 2, 190, px0 + 16, 206, PAL['wlight'])
    rect(px0 + 2, 190, px0 + 16, 190, PAL['whi']); rect(px0 + 2, 190, px0 + 2, 206, PAL['whi'])
rect(CX0, 210 + 3, CX1, CY1, PAL['wdark']); rect(CX0, 212, CX1, 212, PAL['wmid'])
frame_rect(CX0 - 1, CY0, CX1, CY1, PAL['black'])
rect(CX1 - 1, CY0 + 1, CX1 - 1, CY1 - 1, PAL['wmid'])
# bottle & glass on the bar
bgl = {}
d_rect(bgl, 8, 174, 12, 179, PAL['glow']); d_rect(bgl, 9, 172, 11, 173, PAL['glow']); bgl[(8, 174)] = PAL['cream']
blit(bgl)
for k in range(5): px(8 + k, 177, PAL['gold'])
# bar top shadow onto floor
for x in range(0, 78): remap(x, 217, DOWNC)

# =============================== FLOOR OBJECTS ==================================
def floor_shadow(cx, cy, rx, ry):
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if in_ell(x, y, cx, cy, rx, ry) and y >= 219: remap(x, y, DOWNC)
# barrel
floor_shadow(193, 236, 18, 4)
bar = {}
BCXb = 190
for y in range(196, 237):
    u = y - 216; hw = 14 - (u * u) // 130
    for x in range(BCXb - hw, BCXb + hw + 1):
        band = (x - (BCXb - hw)) // 6
        c = PAL['wmid']
        if x - (BCXb - hw) < 3: c = PAL['wlight']
        if x >= BCXb + hw - 4: c = PAL['wdark']
        if (x - (BCXb - hw)) % 6 == 5 and c == PAL['wmid']: c = PAL['wdark']
        if y <= 198: c = PAL['wlight'] if y < 198 else PAL['wdark']
        bar[(x, y)] = c
for hy in (203, 228):
    for y in (hy, hy + 1, hy + 2):
        u = y - 216; hw = 14 - (u * u) // 130
        for x in range(BCXb - hw, BCXb + hw + 1):
            bar[(x, y)] = PAL['dred'] if y < hy + 2 else PAL['black']
        bar[(BCXb - hw + 1, hy)] = PAL['red']; bar[(BCXb - hw + 2, hy)] = PAL['red']
for x in range(BCXb - 11, BCXb + 12): bar[(x, 197)] = PAL['wpale'] if x < BCXb - 4 else PAL['whi']
blit(bar)
# chair
floor_shadow(225, 240, 15, 3)
ch = {}
def post(x0, x1, y0, y1):
    d_rect(ch, x0, y0, x1, y1, PAL['wmid'])
    d_rect(ch, x0, y0, x0, y1, PAL['wlight']); d_rect(ch, x1, y0, x1, y1, PAL['wdark'])
post(213, 216, 186, 240); post(234, 237, 186, 240)
for sy in (190, 198, 206):
    d_rect(ch, 217, sy, 233, sy + 3, PAL['wmid'])
    d_rect(ch, 217, sy, 233, sy, PAL['wlight']); d_rect(ch, 217, sy + 3, 233, sy + 3, PAL['wdark'])
d_rect(ch, 212, 186, 238, 188, PAL['wlight']); d_rect(ch, 212, 186, 238, 186, PAL['whi']); d_rect(ch, 212, 188, 238, 188, PAL['wmid'])
d_rect(ch, 211, 214, 239, 221, PAL['wlight']); d_rect(ch, 211, 214, 239, 214, PAL['whi']); d_rect(ch, 211, 221, 239, 221, PAL['wdark'])
d_rect(ch, 214, 222, 236, 224, PAL['wmid'])
d_rect(ch, 217, 225, 233, 226, PAL['wdark'])  # stretcher shadow under seat
d_rect(ch, 217, 234, 233, 235, PAL['wmid']);  d_rect(ch, 217, 234, 233, 234, PAL['wlight'])
blit(ch)
# mug
floor_shadow(186, 270, 11, 2)
mug = {}
d_rect(mug, 178, 256, 189, 269, PAL['tan'])
d_rect(mug, 178, 256, 179, 269, PAL['cream']); d_rect(mug, 188, 256, 189, 269, PAL['whi']); d_rect(mug, 178, 269, 189, 269, PAL['whi'])
d_rect(mug, 178, 259, 189, 259, PAL['whi']); d_rect(mug, 178, 266, 189, 266, PAL['whi'])
d_rect(mug, 179, 259, 179, 259, PAL['cream'])
d_rect(mug, 177, 253, 190, 255, PAL['cream']); d_rect(mug, 179, 251, 182, 252, PAL['cream']); d_rect(mug, 185, 250, 188, 252, PAL['cream'])
d_rect(mug, 177, 255, 190, 255, PAL['tan']); d_rect(mug, 183, 252, 184, 252, PAL['cream'])
d_rect(mug, 190, 258, 193, 259, PAL['tan']); d_rect(mug, 192, 260, 193, 263, PAL['tan']); d_rect(mug, 190, 264, 193, 265, PAL['tan'])
d_rect(mug, 192, 260, 193, 263, PAL['whi']); d_rect(mug, 190, 258, 193, 258, PAL['cream'])
blit(mug)
# brown bottle
floor_shadow(225, 260, 7, 2)
bo = {}
d_rect(bo, 223, 241, 224, 241, PAL['tan'])
d_rect(bo, 223, 242, 224, 247, PAL['wdark']); d_rect(bo, 222, 248, 225, 248, PAL['wdark'])
d_rect(bo, 220, 249, 227, 259, PAL['wdark'])
d_rect(bo, 220, 252, 227, 256, PAL['cream']); d_rect(bo, 220, 255, 227, 256, PAL['tan'])
d_rect(bo, 222, 253, 225, 253, PAL['dred'])
d_rect(bo, 221, 249, 221, 251, PAL['whi']); d_rect(bo, 221, 257, 221, 258, PAL['wmid'])
d_rect(bo, 223, 242, 223, 247, PAL['wmid'])
blit(bo)

# =============================== SAVE ===========================================
def save():
    os.makedirs(os.path.join(ROOT, 'assets'), exist_ok=True)
    img.save(os.path.join(ROOT, 'assets', 'scene-bg.png'))
    img.resize((W * 3, H * 3), Image.NEAREST).save(os.path.join(HERE, 'preview-scene.png'))
    pal = set(PAL.values())
    bad = {P[x, y] for y in range(H) for x in range(W) if P[x, y] not in pal or P[x, y][3] != 255}
    print('saved', img.size, 'colours used:', len({P[x, y] for y in range(H) for x in range(W)}), 'off-palette:', bad or 'none')
save()
