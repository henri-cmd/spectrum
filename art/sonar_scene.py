"""Submarine control-room background, 240x300, native pixels.
Run: .venv/bin/python art/sonar_scene.py   -> assets/sonar/scene-bg.png (+ art/preview-sonar-scene.png)
"""
import math, os, random
from PIL import Image

W, H = 240, 300
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

def h(s): s = s.lstrip('#'); return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), 255)
PAL = {k: h(v) for k, v in dict(
    black='0a0e12', sdarkest='121a22', sdark='1b2430', smid='2b3a4a', slight='3e5266',
    shi='5a7085', spale='8da2b5', pdarkest='0c2a1c', pdark='145c35', pmid='27a85e',
    plight='6cf29b', ppale='c8ffd9', amber='f0a030', amberl='ffd36b', amberd='9a5a12',
    red='d9342b', dred='7a1a14', brass='c9a247', brassd='7d5f24', rubber='1e1e22',
    skin='e0a885', skinsh='b07a5a', navy='22304a', navyl='34496b', white='f2f4f6').items()}
PALSET = set(PAL.values())

img = Image.new('RGBA', (W, H), PAL['sdark'])
P = img.load()

def px(x, y, c):
    if 0 <= x < W and 0 <= y < H: P[x, y] = PAL[c] if isinstance(c, str) else c
def get(x, y): return P[x, y]
def rect(x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): px(x, y, c)
def frame(x0, y0, x1, y1, c):
    for x in range(x0, x1 + 1): px(x, y0, c); px(x, y1, c)
    for y in range(y0, y1 + 1): px(x0, y, c); px(x1, y, c)
def box(x0, y0, x1, y1, fill, line='black'):
    rect(x0, y0, x1, y1, fill); frame(x0, y0, x1, y1, line)
def hline(x0, x1, y, c):
    for x in range(x0, x1 + 1): px(x, y, c)
def vline(x, y0, y1, c):
    for y in range(y0, y1 + 1): px(x, y, c)

def circ(cx2, cy2, rr, c, test=None):
    """Fill pixels whose centre lies within doubled-radius rr of doubled-centre (cx2, cy2).
    (2x+1-cx2)^2 + (2y+1-cy2)^2 <= rr^2   -- pure integer arithmetic."""
    r = rr // 2 + 2
    for y in range(cy2 // 2 - r, cy2 // 2 + r + 1):
        for x in range(cx2 // 2 - r, cx2 // 2 + r + 1):
            dx, dy = 2 * x + 1 - cx2, 2 * y + 1 - cy2
            if dx * dx + dy * dy <= rr * rr and (test is None or test(dx, dy)):
                px(x, y, c)
def ellipse(cx, cy, rx, ry, c):
    for y in range(cy - ry, cy + ry + 1):
        for x in range(cx - rx, cx + rx + 1):
            if ((x - cx) * ry) ** 2 + ((y - cy) * rx) ** 2 <= (rx * ry) ** 2: px(x, y, c)

# sprite-dict helpers (blit adds a 1px black outline)
def d_rect(d, x0, y0, x1, y1, c):
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1): d[(x, y)] = PAL[c]
def blit(d):
    for (x, y) in list(d):
        for ox, oy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + ox, y + oy) not in d: px(x + ox, y + oy, 'black')
    for (x, y), c in d.items(): px(x, y, c)

FONT = {   # 3x5 capitals (N is 4 wide so it cannot be mistaken for M)
    'A': ("010101111101101", 3), 'N': ("10011101101110011001", 4), 'O': ("111101101101111", 3),
    'R': ("110101110101101", 3), 'S': ("011100010001110", 3)}
def text(s, x0, y, c):
    x = x0
    for ch in s:
        g, w = FONT[ch]
        for j in range(5 * w):
            if g[j] == '1': px(x + j % w, y + j // w, c)
        x += w + 1
rnd = random.Random(11)
SCX, SCY = 120, 128          # sonar scope centre
def sdist(x, y):             # integer-rounded distance to scope centre
    return int(math.sqrt((x - SCX) ** 2 + (y - SCY) ** 2) + 0.5)

UP = {PAL['sdarkest']: PAL['sdark'], PAL['sdark']: PAL['smid'], PAL['smid']: PAL['slight']}

# =============================== BULKHEAD (rows 0..215) ==========================
PWID, PHGT = 40, 28
plate_mid = {}
for r in range(0, 8):
    for k in range(-1, 7):
        plate_mid[(r, k)] = rnd.random() < 0.28
for y in range(0, 216):
    r = y // PHGT; ry = y % PHGT
    off = 0 if r % 2 == 0 else 20
    for x in range(W):
        k = (x - off) // PWID; rx = (x - off) % PWID
        mid = plate_mid[(r, k)]
        base = PAL['smid'] if mid else PAL['sdark']
        hi = PAL['slight'] if mid else PAL['smid']
        c = base
        if ry == 0 or rx == 0: c = PAL['black']
        elif ry == 1: c = hi
        elif ry == 2:  # shadow row below seam: cold green near scope glow
            c = PAL['pdarkest'] if sdist(x, y) <= 100 else PAL['sdarkest']
            if mid: c = PAL['sdark'] if sdist(x, y) > 100 else PAL['pdarkest']
        P[x, y] = c
# rivets
for r in range(0, 8):
    off = 0 if r % 2 == 0 else 20
    for k in range(-1, 7):
        x0 = off + k * PWID; y0 = r * PHGT
        for (rx, ry) in ((4, 5), (34, 5), (4, 22), (34, 22)):
            x, y = x0 + rx, y0 + ry
            if not (0 <= x < W - 3 and 0 <= y < 213): continue
            sh = 'pdarkest' if sdist(x, y) <= 100 else 'sdarkest'
            for (a, b) in ((2, 0), (2, 1), (2, 2), (0, 2), (1, 2)): px(x + a, y + b, sh)
            rect(x, y, x + 1, y + 1, 'shi')
# weld scratches
for _ in range(34):
    x = rnd.randrange(2, W - 8); y = rnd.randrange(30, 212)
    if y % PHGT in (0, 1, 2) or (y % PHGT) > 24: continue
    for i in range(rnd.randrange(3, 7)):
        if P[x + i, y] in (PAL['sdark'], PAL['smid']): P[x + i, y] = PAL['smid'] if P[x + i, y] == PAL['sdark'] else PAL['slight']
# instrument glow: plates near the scope step one shade lighter
for y in range(28, 216):
    for x in range(W):
        d = sdist(x, y)
        if 80 < d <= 96 and P[x, y] in UP and P[x, y] != PAL['smid']: P[x, y] = UP[P[x, y]]
# red alarm lamp tint (dark red halo, dithered at its rim)
AX, AY = 226, 60
for y in range(AY - 17, AY + 18):
    for x in range(AX - 17, AX + 18):
        d = int(math.sqrt((x - AX) ** 2 + (y - AY) ** 2) + 0.5)
        if not (0 <= x < W and 28 <= y < 216): continue
        if P[x, y] in (PAL['sdark'], PAL['sdarkest']):
            if d <= 9: P[x, y] = PAL['dred'] if (x + y) % 2 == 0 else P[x, y]
            elif d <= 15 and (x % 2 == 0 and y % 2 == 0): P[x, y] = PAL['dred']

# =============================== DECK (rows 216..299) ============================
hline(0, W - 1, 215, 'black')
hline(0, W - 1, 216, 'slight')
hline(0, W - 1, 217, 'sdarkest')
for y in range(218, H):
    for x in range(W):
        pr = (y - 218) // 20; off = 0 if pr % 2 == 0 else 24
        pk = (x - off) // 48; ry = (y - 218) % 20; rx = (x - off) % 48
        P[x, y] = PAL['smid'] if (pr + pk) % 2 == 0 else PAL['sdark']
        if ry == 0 or rx == 0: P[x, y] = PAL['black']
# diamond-plate tread
def lit_patch(x, y):
    dx, dy = x - 120, y - 216
    return (dx * 1.0 / 40) ** 2 + (dy * 1.0 / 46) ** 2 <= 1.0
for y in range(218, H):
    for x in range(W):
        if P[x, y] == PAL['black']: continue
        cx, cy = x // 8, (y - 218) // 8
        lx, ly = x % 8, (y - 218) % 8
        diag = (lx == ly) if (cx + cy) % 2 == 0 else (lx + ly == 7)
        on = diag and 1 <= lx <= 6
        lit = lit_patch(x, y)
        if lit: # one step lighter plates
            if P[x, y] == PAL['sdark']: P[x, y] = PAL['smid']
            elif P[x, y] == PAL['smid']: P[x, y] = PAL['slight']
        if on: P[x, y] = PAL['pdarkest'] if lit else PAL['sdarkest']
        elif lit and diag is False and ((lx + 1 == ly) if (cx + cy) % 2 == 0 else (lx + ly == 6)) and 1 <= lx <= 5:
            P[x, y] = PAL['pdark']   # phosphor tint on the tread highlights
# dark band along bulkhead foot
# (row 217 shadow already drawn)

# =============================== TOP PIPES =======================================
def pipe(y0, y1, c_body, c_hi, c_dark):
    hline(0, W - 1, y0, 'black'); hline(0, W - 1, y1, 'black')
    for y in range(y0 + 1, y1): hline(0, W - 1, y, c_body)
    hline(0, W - 1, y0 + 1, c_hi)
    hline(0, W - 1, y1 - 1, c_dark)
pipe(6, 14, 'smid', 'shi', 'sdark')
hline(0, W - 1, 13, 'sdark'); hline(0, W - 1, 12, 'sdark') if False else None
pipe(20, 26, 'smid', 'shi', 'sdark')
hline(0, W - 1, 15, 'sdarkest'); hline(0, W - 1, 27, 'sdarkest')
# red-painted section on upper pipe
for y in range(7, 14): hline(143, 196, y, 'red')
hline(143, 196, 12, 'dred'); hline(143, 196, 13, 'dred')
for gx in range(147, 194, 9): hline(gx, gx + 2, 7, 'white')
for gx in range(150, 194, 11): hline(gx, gx + 1, 8, 'white')
# rubber-tape bands on the red section
for bx in (160, 178):
    vline(bx, 7, 13, 'dred'); vline(bx + 1, 7, 13, 'dred')
# flanges every 60 px
for fx in (20, 80, 140, 200):
    for (a, b) in ((4, 16), (18, 28)):
        rect(fx - 3, a, fx + 2, b, 'slight'); frame(fx - 3, a, fx + 2, b, 'black')
        vline(fx - 2, a + 1, b - 1, 'spale'); vline(fx + 1, a + 1, b - 1, 'smid')
        px(fx - 1, a + 2, 'shi'); px(fx - 1, b - 2, 'shi')
        px(fx, a + 2, 'sdarkest'); px(fx, b - 2, 'sdarkest')
# brass valve wheel hanging from the lower pipe at x 52
rect(51, 27, 52, 30, 'brassd'); vline(50, 27, 30, 'black'); vline(53, 27, 30, 'black')
rect(49, 27, 54, 27, 'smid'); hline(49, 54, 28, 'black')
for j in range(10):
    for i in range(10):
        dx, dy = 2 * i - 9, 2 * j - 9
        d2 = dx * dx + dy * dy
        x, y = 47 + i, 29 + j
        if d2 > 100 or (d2 > 90 and False): continue
        if d2 > 68: c = 'black'
        elif abs(dx) <= 1 and abs(dy) <= 1: c = 'amberd'
        elif abs(dx) <= 1 or abs(dy) <= 1: c = 'brass'
        elif d2 > 36: c = 'brassd' if dx + dy > 5 else 'brass'
        else: c = 'sdarkest'
        px(x, y, c)
px(47, 33, 'black'); px(56, 33, 'black') if False else None

# =============================== SONAR SCOPE =====================================
# drop shadow (down-right 2px)
for y in range(SCY - 84, SCY + 86):
    for x in range(SCX - 84, SCX + 86):
        if 28 <= y < 216 and sdist(x - 2, y - 2) <= 80 and sdist(x, y) > 80:
            if P[x, y] in (PAL['sdark'], PAL['smid'], PAL['slight'], PAL['sdarkest'], PAL['pdarkest'], PAL['black']):
                P[x, y] = PAL['sdarkest'] if P[x, y] != PAL['black'] else PAL['black']
for y in range(SCY - 81, SCY + 82):
    for x in range(SCX - 81, SCX + 82):
        d = sdist(x, y)
        if d > 80: continue
        dx, dy = x - SCX, y - SCY
        t = (dx + dy) / (1.4142 * max(d, 1))
        if d == 80: c = 'black'
        elif d > 70:
            if t < -0.35: c = 'slight'
            else: c = 'smid'
            if d == 79 and t < -0.15: c = 'shi'
            if d == 71 and t > 0.1: c = 'sdark'
            if d == 79 and t > 0.55: c = 'sdark'
        elif d == 70: c = 'pdark'
        else: c = 'sdarkest'
        px(x, y, c)
# bezel segment seams (12 radial)
for k in range(12):
    a = math.radians(k * 30 + 15)
    for rr in range(72, 79):
        x = SCX + int(round(rr * math.cos(a))); y = SCY + int(round(rr * math.sin(a)))
        px(x, y, 'sdark' if (x - SCX) + (y - SCY) > 0 else 'smid')
# six brass screw heads (3x3) at radius 75
for k in range(6):
    a = math.radians(-90 + k * 60)
    sx = SCX + int(round(75 * math.cos(a))); sy = SCY + int(round(75 * math.sin(a)))
    rect(sx - 1, sy - 1, sx + 1, sy + 1, 'brass')
    px(sx + 1, sy + 1, 'brassd'); px(sx, sy, 'brassd'); px(sx - 1, sy - 1, 'amberl')
    px(sx + 2, sy, 'sdarkest'); px(sx, sy + 2, 'sdarkest'); px(sx + 2, sy + 1, 'sdarkest'); px(sx + 1, sy + 2, 'sdarkest')

# =============================== LEFT BULKHEAD ===================================
# pressure gauge at (36,64), 24px across
GX2, GY2 = 72, 128
circ(GX2 + 2, GY2 + 2, 24, 'sdarkest')       # soft shadow
circ(GX2, GY2, 24, 'black')
circ(GX2, GY2, 22, 'brass')
circ(GX2, GY2, 19, 'brassd', test=lambda dx, dy: dx + dy > 6)   # rim shading, lower-right
circ(GX2, GY2, 18, 'brassd')
circ(GX2, GY2, 16, 'white')
circ(GX2, GY2, 15, 'red', test=lambda dx, dy: dx > 0 and dy < 0 and dx * dx + dy * dy >= 121)
for a in range(0, 360, 30):
    if 0 <= a <= 90: continue
    x = 36 + int(round(7 * math.sin(math.radians(a)))) ; y = 64 - int(round(7 * math.cos(math.radians(a))))
    px(x - (1 if math.sin(math.radians(a)) < 0 else 0), y - (1 if math.cos(math.radians(a)) > 0 else 0) if False else y, 'slight')
for t in range(0, 8):
    nx = 36 + int(round(t * 0.866)); ny = 63 - int(round(t * 0.5))
    px(nx, ny, 'black')
rect(35, 63, 36, 64, 'black'); px(35, 63, 'brassd')
# toggle bank: three switches, amber lamps (two lit)
for i, lit in enumerate((True, True, False)):
    x0 = 17 + i * 9
    box(x0, 92, x0 + 7, 104, 'sdark')
    hline(x0 + 1, x0 + 6, 93, 'smid')
    # lamp
    rect(x0 + 2, 94, x0 + 5, 95, 'amber' if lit else 'amberd')
    if lit: px(x0 + 2, 94, 'amberl'); px(x0 + 3, 94, 'amberl')
    frame(x0 + 1, 93, x0 + 6, 96, 'black') if False else None
    # lever
    rect(x0 + 3, 98, x0 + 4, 102, 'sdarkest')
    if i != 1: rect(x0 + 3, 98, x0 + 4, 100, 'spale'); px(x0 + 3, 98, 'white')
    else: rect(x0 + 3, 100, x0 + 4, 102, 'spale'); px(x0 + 3, 100, 'white')
    px(x0 + 1, 105, 'sdarkest'); px(x0 + 2, 105, 'sdarkest')
# depth gauge x 8..20, y 110..170
box(8, 110, 20, 170, 'sdark')
hline(9, 19, 111, 'smid'); vline(9, 111, 168, 'smid')
box(11, 114, 17, 166, 'pdarkest')
rect(12, 138, 16, 165, 'pmid'); hline(12, 16, 138, 'plight'); vline(12, 139, 165, 'plight')
for ty in range(116, 166, 6):
    hline(9, 10, ty, 'spale'); hline(18, 19, ty, 'spale')
rect(9, 167, 19, 169, 'brassd'); hline(10, 18, 168, 'brass')
px(10, 112, 'brass'); px(18, 112, 'brass')

# =============================== RIGHT BULKHEAD ==================================
# periscope column x 206..220 from top pipes to y 170
rect(206, 29, 220, 170, 'slight'); frame(206, 29, 220, 170, 'black')
vline(207, 30, 169, 'spale'); vline(208, 30, 169, 'shi')
vline(219, 30, 169, 'smid'); vline(218, 30, 169, 'smid')
for (a, b) in ((29, 33), (112, 114), (164, 170)):
    rect(204, a, 222, b, 'smid'); frame(204, a, 222, b, 'black'); hline(205, 221, a + 1, 'shi')
# eyepiece box and folded handles
rect(203, 129, 225, 149, 'smid'); frame(203, 129, 225, 149, 'black')
hline(204, 224, 130, 'shi'); vline(204, 131, 148, 'slight'); hline(204, 224, 148, 'sdark')
rect(198, 137, 202, 144, 'rubber'); frame(198, 137, 202, 144, 'black'); px(199, 138, 'sdark'); px(199, 139, 'sdark')
rect(209, 134, 219, 143, 'sdark'); frame(209, 134, 219, 143, 'black')
rect(211, 136, 217, 141, 'pdarkest'); px(212, 137, 'pdark')
for hx in (202, 222):
    rect(hx, 123, hx + 1, 128, 'spale'); vline(hx - 1, 123, 128, 'black'); vline(hx + 2, 123, 128, 'black')
    vline(hx, 123, 128, 'spale'); vline(hx + 1, 123, 128, 'shi')
    rect(hx - 1, 118, hx + 2, 122, 'rubber'); frame(hx - 1, 118, hx + 2, 122, 'black'); px(hx, 119, 'sdark')
    rect(hx - 1, 129, hx + 2, 129, 'black')

# SONAR nameplate (moved above the scope: x 168..200, y 32..44)
NX0, NY0, NX1, NY1 = 168, 32, 200, 44
rect(NX0 + 1, NY0 + 1, NX1 + 2, NY1 + 2, 'sdarkest')
box(NX0, NY0, NX1, NY1, 'brass')
hline(NX0 + 1, NX1 - 1, NY0 + 1, 'amberl'); hline(NX0 + 1, NX1 - 1, NY1 - 1, 'brassd'); vline(NX1 - 1, NY0 + 1, NY1 - 1, 'brassd')
text("SONAR", NX0 + 6, NY0 + 4, 'black')
for (x, y) in ((NX0 + 2, NY0 + 2), (NX1 - 2, NY0 + 2), (NX0 + 2, NY1 - 2), (NX1 - 2, NY1 - 2)): px(x, y, 'brassd')
# red alarm lamp in a steel cage at (226, 60)
rect(222, 66, 230, 68, 'smid'); frame(222, 66, 230, 68, 'black'); hline(223, 229, 66, 'shi')
rect(223, 53, 229, 54, 'smid'); frame(223, 53, 229, 54, 'black'); hline(224, 228, 53, 'shi')
for y in range(55, 66):
    for x in range(221, 232):
        dx, dy = x - AX, y - 60
        if dx * dx + dy * dy <= 21:
            c = 'red'
            if dx + dy >= 3: c = 'dred'
            px(x, y, c)
px(224, 57, 'white'); px(224, 58, 'white'); px(225, 56, 'white')
for bx in (224, 228): vline(bx, 55, 65, 'sdark')
hline(222, 230, 60, 'sdark')
vline(221, 56, 64, 'black'); vline(231, 56, 64, 'black')

# =============================== CONSOLE + CREW ==================================
# crew member (drawn before the desk so the desk hides his lower body)
d = {}
# torso (navy, shoulders)
for y in range(164, 181):
    if y == 164: x0, x1 = 25, 40
    elif y == 165: x0, x1 = 22, 42
    else: x0, x1 = 21, 43
    for x in range(x0, x1 + 1): d[(x, y)] = PAL['navy']
for x in range(24, 41): d[(x, 165)] = PAL['navyl']
for y in range(166, 181): d[(42, y)] = PAL['navyl']; d[(43, y)] = PAL['navyl']
for y in range(168, 181): d[(24, y)] = PAL['navyl']
for x in range(28, 36): d[(x, 164)] = PAL['skinsh']
for (x, y) in ((30, 166), (31, 167), (32, 168), (33, 167), (34, 166)): d[(x, y)] = PAL['navyl']
for y in (171, 175, 179): d[(36, y)] = PAL['brassd']
# neck + head
for x in range(30, 35): d[(x, 163)] = PAL['skinsh']
for y in range(151, 163):
    x0, x1 = 26, 37
    if y in (151, 162): x0, x1 = 27, 36
    for x in range(x0, x1 + 1): d[(x, y)] = PAL['skin']
for y in range(158, 163):
    for x in range(26, 28): d[(x, y)] = PAL['skinsh']
for x in range(28, 37): d[(x, 162)] = PAL['skinsh']
d[(38, 156)] = PAL['skin']; d[(38, 157)] = PAL['skin']
d[(36, 154)] = PAL['black']; d[(35, 152)] = PAL['skinsh']; d[(36, 152)] = PAL['skinsh']; d[(37, 155)] = PAL['skin']
d[(35, 160)] = PAL['skinsh']; d[(36, 160)] = PAL['skinsh']
# cap
for y in range(144, 151):
    x0, x1 = 26, 37
    if y == 144: x0, x1 = 28, 35
    for x in range(x0, x1 + 1): d[(x, y)] = PAL['navy']
for x in range(29, 35): d[(x, 145)] = PAL['navyl']
for x in range(26, 38): d[(x, 149)] = PAL['navyl']
for x in range(30, 42): d[(x, 150)] = PAL['navy']
for x in range(32, 41): d[(x, 150)] = PAL['navyl'] if False else PAL['navy']
rect_b = {(x, y): PAL['brass'] for x in (34, 35) for y in (146, 147)}
d.update(rect_b); d[(35, 147)] = PAL['brassd']
# headphones: band over the cap, cup on the ear
for y in range(145, 154): d[(30, y)] = PAL['rubber']
for y in range(154, 159):
    for x in range(29, 32): d[(x, y)] = PAL['rubber']
d[(29, 155)] = PAL['sdark']; d[(29, 156)] = PAL['sdark']; d[(29, 154)] = PAL['sdark']
blit(d)
# console desk x 0..72, y 180..215
rect(73, 182, 74, 216, 'sdarkest'); rect(2, 216, 74, 217, 'sdarkest')
box(0, 180, 72, 215, 'smid')
hline(1, 71, 181, 'shi'); hline(1, 71, 182, 'slight'); vline(1, 181, 214, 'slight')
hline(1, 71, 214, 'sdark'); vline(71, 183, 213, 'sdark')
box(3, 185, 69, 193, 'sdark'); hline(4, 68, 186, 'sdarkest')
for i in range(9):
    bx = 6 + i * 7
    lit = i in (0, 1, 3, 4, 7)
    rect(bx, 188, bx + 3, 191, 'amber' if lit else 'amberd'); frame(bx - 1, 187, bx + 4, 192, 'black')
    if lit: px(bx, 188, 'amberl'); px(bx + 1, 188, 'amberl')
box(3, 197, 34, 212, 'sdark'); box(38, 197, 69, 212, 'sdark')
hline(4, 33, 198, 'smid'); hline(39, 68, 198, 'smid')
hline(14, 23, 203, 'spale'); hline(49, 58, 203, 'spale'); hline(14, 23, 204, 'sdarkest'); hline(49, 58, 204, 'sdarkest')
for (x, y) in ((5, 199), (32, 199), (40, 199), (67, 199), (5, 210), (32, 210), (40, 210), (67, 210)): px(x, y, 'shi')
# green CRT on the desk top
rect(46, 164, 69, 179, 'slight'); frame(46, 164, 69, 179, 'black')
hline(47, 68, 165, 'shi'); vline(47, 165, 178, 'shi'); hline(47, 68, 178, 'smid'); vline(68, 166, 178, 'smid')
box(50, 167, 65, 176, 'pdarkest', 'black')
for gx in range(52, 65, 3):
    for gy in (169, 172, 175): px(gx, gy, 'pdark')
wave = [172, 172, 171, 169, 168, 170, 173, 175, 174, 172, 172, 171, 170, 172]
for i, wy in enumerate(wave): px(51 + i, wy, 'pmid')
for i in range(len(wave) - 1):
    a, b = wave[i], wave[i + 1]
    for yy in range(min(a, b), max(a, b) + 1): px(51 + i if abs(a - 172) > abs(b - 172) else 52 + i, yy, 'pmid')
px(55, 168, 'plight'); px(52, 168, 'pdark')
px(67, 168, 'red'); px(67, 171, 'amberl'); px(67, 174, 'amberd')
rect(48, 179, 51, 179, 'black'); rect(64, 179, 67, 179, 'black')
# faint green spill from the CRT onto the desk top
hline(50, 65, 181, 'pdark')

# =============================== RIGHT, LOWER ====================================
# locker x 176..204, y 196..236
ellipse(190, 238, 16, 2, 'sdarkest')
rect(205, 198, 206, 238, 'sdarkest')
box(176, 196, 204, 236, 'smid')
hline(177, 203, 197, 'shi'); vline(177, 198, 235, 'slight'); vline(203, 198, 235, 'sdark'); hline(177, 203, 235, 'sdark')
box(180, 200, 200, 214, 'sdarkest')
for gy in range(202, 214, 2): hline(181, 199, gy, 'smid')
hline(181, 199, 201, 'sdark')
hline(177, 203, 217, 'black'); hline(177, 203, 218, 'shi')
rect(196, 224, 199, 229, 'brass'); frame(196, 224, 199, 229, 'black'); px(197, 225, 'amberl')
rect(180, 222, 183, 233, 'sdark'); frame(180, 222, 183, 233, 'black') if False else None
for (x, y) in ((179, 220), (201, 220), (179, 233), (201, 233)): rect(x, y, x + 1, y + 1, 'shi')
# bolted-down stool x 212..238, y 200..240
ellipse(226, 238, 13, 2, 'sdarkest')
ellipse(225, 235, 12, 4, 'black'); ellipse(225, 235, 11, 3, 'smid'); ellipse(225, 234, 9, 2, 'slight')
rect(222, 211, 228, 233, 'smid'); vline(221, 211, 233, 'black'); vline(229, 211, 233, 'black')
vline(223, 211, 233, 'slight'); vline(227, 211, 233, 'sdark')
for (x, y) in ((215, 234), (234, 234), (219, 237), (230, 237)): rect(x, y, x + 1, y + 1, 'spale'); px(x + 2, y + 1, 'sdarkest')
ellipse(225, 208, 13, 5, 'black'); ellipse(225, 208, 12, 4, 'sdark')
ellipse(225, 205, 13, 5, 'black'); ellipse(225, 205, 12, 4, 'smid'); ellipse(225, 204, 10, 3, 'slight')
for x in range(217, 224): px(x, 202, 'shi')
for x in range(216, 218): px(x, 203, 'shi')

# mug at (184, 262)
ellipse(185, 268, 7, 2, 'sdarkest')
box(179, 256, 189, 267, 'white')
rect(180, 260, 188, 263, 'navy'); hline(180, 188, 260, 'navyl')
vline(188, 257, 259, 'spale'); vline(188, 264, 266, 'spale'); hline(180, 188, 266, 'spale')
rect(180, 257, 188, 257, 'rubber')   # dark coffee at the rim
rect(190, 259, 193, 265, 'black'); rect(190, 260, 192, 264, 'white'); rect(191, 261, 191, 263, 'black')
px(190, 259, 'black'); px(190, 265, 'black')
px(181, 258, 'white')
# clipboard at (224, 250)
rect(218, 245, 232, 261, 'sdarkest')
box(217, 243, 230, 258, 'brassd')
box(219, 246, 228, 256, 'white')
for ly in (248, 250, 252, 254): hline(220, 227 if ly != 254 else 224, ly, 'slight')
hline(220, 223, 248, 'spale')
rect(221, 241, 226, 244, 'spale'); frame(221, 241, 226, 244, 'black'); hline(222, 225, 242, 'white')
px(225, 255, 'red') if False else None

# ping console stand under the operator's button (dome at (86,234) is drawn by the page)
ellipse(89, 264, 15, 2, 'sdarkest')                      # floor shadow
rect(101, 238, 102, 262, 'sdarkest')
box(80, 242, 96, 259, 'smid')                            # column
vline(81, 243, 258, 'slight'); vline(95, 243, 258, 'sdark'); hline(81, 95, 258, 'sdark')
box(78, 258, 98, 262, 'slight'); hline(79, 97, 259, 'spale')   # base flange on the deck
for (x, y) in ((79, 261), (97, 261)): px(x, y, 'sdarkest')
box(76, 236, 100, 242, 'smid')                           # top plate
hline(77, 99, 237, 'shi'); hline(77, 99, 241, 'sdark')
px(78, 239, 'shi'); px(98, 239, 'shi')
for x, c in ((90, 'amber'), (93, 'amberl'), (96, 'amberd')): px(x, 239, c)
rect(83, 247, 92, 250, 'sdarkest'); frame(83, 247, 92, 250, 'black'); hline(84, 91, 248, 'pdarkest')
px(85, 248, 'pdark'); px(89, 248, 'pmid')
# rubber-black cable: from the plate side down to the deck, then curling out
vline(99, 242, 261, 'rubber'); vline(100, 243, 262, 'black')
for x in range(100, 106): px(x, 263, 'rubber'); px(x, 264, 'black')
px(106, 262, 'rubber'); px(106, 261, 'black')

# =============================== SAVE ============================================
bad = [(x, y) for y in range(H) for x in range(W) if P[x, y] not in PALSET or P[x, y][3] != 255]
assert not bad, bad[:5]
os.makedirs(os.path.join(ROOT, 'assets', 'sonar'), exist_ok=True)
img.save(os.path.join(ROOT, 'assets', 'sonar', 'scene-bg.png'))
img.resize((W * 3, H * 3), Image.NEAREST).save(os.path.join(HERE, 'preview-sonar-scene.png'))
print('saved', len(set(P[x, y] for y in range(H) for x in range(W))), 'colours used')
