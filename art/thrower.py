"""Saloon dartboard game: cowboy thrower sprite strip + dart sprites.

Run from the project folder:  .venv/bin/python art/thrower.py
Writes assets/thrower.png, assets/dart.png, assets/dart-stuck.png, art/preview-thrower.png
"""
import math
import os
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets")


def hx(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


OUT = hx("15090a")
SHADOW = hx("2a1710")
WOOD_D = hx("5a2f1a")
WOOD_M = hx("7a4426")
WOOD_L = hx("9b5a2e")
WOOD_H = hx("b8763a")
CREAM = hx("f3e2b4")
TAN = hx("c9a46a")
RED = hx("c8322e")
DRED = hx("8e1d1d")
SKIN = hx("e0a885")
SHIRT = hx("a3241f")
HAT = hx("3b2418")
SHAFT = hx("15090a")  # dart shaft (allowed exception)

FW, FH = 96, 110
NFRAMES = 6


# ---------------------------------------------------------------- helpers
def bresenham(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pts


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def mask(self):
        return Image.new("L", (self.w, self.h), 0)

    def paint(self, m, color):
        self.im.paste(color, mask=m)

    # -- mask builders
    def m_rect(self, x0, y0, x1, y1):
        m = self.mask()
        ImageDraw.Draw(m).rectangle([x0, y0, x1, y1], fill=255)
        return m

    def m_poly(self, pts):
        m = self.mask()
        ImageDraw.Draw(m).polygon([(float(x), float(y)) for x, y in pts], fill=255)
        return m

    def m_ellipse(self, cx, cy, a, b):
        m = self.mask()
        d = ImageDraw.Draw(m)
        for y in range(self.h):
            for x in range(self.w):
                if ((x - cx) / a) ** 2 + ((y - cy) / b) ** 2 <= 1.0:
                    d.point((x, y), fill=255)
        return m

    def m_line(self, pts):
        m = self.mask()
        d = ImageDraw.Draw(m)
        for p in pts:
            d.point(p, fill=255)
        return m

    def m_stamp_line(self, p0, p1, r=2):
        """Thick limb: rounded (r*2+1) square stamp walked along a Bresenham line."""
        m = self.mask()
        d = ImageDraw.Draw(m)
        for (x, y) in bresenham(p0[0], p0[1], p1[0], p1[1]):
            for oy in range(-r, r + 1):
                for ox in range(-r, r + 1):
                    if abs(ox) == r and abs(oy) == r and r >= 2:
                        continue  # clip corners -> rounded
                    d.point((x + ox, y + oy), fill=255)
        return m

    # -- mask ops
    @staticmethod
    def union(*ms):
        out = ms[0]
        for m in ms[1:]:
            out = ImageChops.lighter(out, m)
        return out

    @staticmethod
    def inter(a, b):
        return ImageChops.darker(a, b)

    @staticmethod
    def minus(a, b):
        return ImageChops.subtract(a, b)

    @staticmethod
    def dilate(m):
        return m.filter(ImageFilter.MaxFilter(3))

    @staticmethod
    def shift(m, dx, dy):
        out = Image.new("L", m.size, 0)
        out.paste(m, (dx, dy))
        return out

    # -- compound painters
    def shape(self, m, base, hi=None, lo=None, outline=True, out_mask=None):
        if outline:
            self.paint(out_mask if out_mask is not None else self.dilate(m), OUT)
        self.paint(m, base)
        if hi is not None:
            self.paint(self.minus(m, self.shift(m, 1, 1)), hi)   # top-left edge
        if lo is not None:
            self.paint(self.minus(m, self.shift(m, -1, -1)), lo)  # bottom-right edge


# ---------------------------------------------------------------- dart
def unit(angle_deg):
    a = math.radians(angle_deg)
    return math.cos(a), -math.sin(a)  # y down


def draw_dart(cv, tail, angle, length, fin_len=5.5, fin_span=4.2, tip_px=3):
    """Side-view dart; tail=(x,y) float, angle in degrees (0=right, 90=up)."""
    dx, dy = unit(angle)
    px, py = -dy, dx  # perpendicular
    tx, ty = tail
    tip = (tx + dx * length, ty + dy * length)

    def P(a, b):
        return (tx + dx * a + px * b, ty + dy * a + py * b)

    # two fins, one each side of the shaft
    finA = cv.m_poly([P(fin_len, 0), P(0, 0), P(-1.5, fin_span), P(fin_len - 2.0, fin_span)])
    finB = cv.m_poly([P(fin_len, 0), P(0, 0), P(-1.5, -fin_span), P(fin_len - 2.0, -fin_span)])
    # figure which fin is upper-left (lit)
    lit, dark = (finA, finB) if (px + py) < 0 else (finB, finA)
    both = cv.union(finA, finB)
    cv.paint(cv.dilate(both), OUT)
    cv.paint(dark, DRED)
    cv.paint(lit, RED)
    # shaft
    shaft = bresenham(tx, ty, tip[0], tip[1])
    cv.paint(cv.m_line(shaft), SHAFT)
    # tip: last 3 px cream with outline
    tipm = cv.m_line(shaft[-tip_px:])
    cv.paint(cv.dilate(tipm), OUT)
    cv.paint(tipm, CREAM)
    return tip


# ---------------------------------------------------------------- body
def body_head(cv, dx):
    """Shirt, neck, hair, ear, hat. dx = lean in px."""
    # ---- shirt (back view, cut at the bottom edge)
    shirt = cv.m_poly([(-4 + dx, 112), (-4 + dx, 80), (4 + dx, 71), (22 + dx, 65), (28 + dx, 62),
                       (38 + dx, 62), (44 + dx, 65), (66 + dx, 67), (88 + dx, 71),
                       (100 + dx, 80), (100 + dx, 112)])
    # neck
    neck = cv.m_rect(28 + dx, 54, 38 + dx, 66)
    cv.shape(shirt, SHIRT, hi=RED, lo=None)
    # shade right part of the back (light from upper left)
    cv.paint(cv.minus(shirt, cv.m_rect(0, 0, 89 + dx, FH)), DRED)
    for yy in range(70, FH):
        for xx in (87, 88):
            if (xx + yy) % 2 == 0:
                cv.paint(cv.inter(cv.m_line([(xx + dx, yy)]), shirt), DRED)
    # shoulder-blade fold + centre seam
    cv.paint(cv.m_line(bresenham(33 + dx, 74, 33 + dx, 109)), DRED)
    cv.paint(cv.m_line(bresenham(14 + dx, 80, 20 + dx, 92)), DRED)
    cv.paint(cv.m_line(bresenham(52 + dx, 80, 47 + dx, 94)), DRED)
    cv.paint(cv.m_line(bresenham(14 + dx, 66, 26 + dx, 63)), RED)
    # neck over shirt
    cv.shape(neck, SKIN, lo=TAN)
    cv.paint(cv.m_rect(28 + dx, 54, 38 + dx, 58), TAN)  # shadow under the hair
    # collar
    collar = cv.m_poly([(26 + dx, 61), (40 + dx, 61), (38 + dx, 66), (28 + dx, 66)])
    cv.shape(collar, SHIRT, hi=RED, lo=DRED)

    # ---- ear (right side of head, lit less)
    ear = cv.m_rect(46 + dx, 50, 49 + dx, 55)
    cv.shape(ear, SKIN, lo=TAN)
    # ---- hair
    hair = cv.m_ellipse(33 + dx, 50, 14.5, 9.5)
    hair = cv.union(hair, cv.m_rect(23 + dx, 52, 43 + dx, 58))
    cv.shape(hair, WOOD_D, hi=None, lo=SHADOW)
    cv.paint(cv.inter(hair, cv.m_rect(41 + dx, 0, 60 + dx, 70)), SHADOW)   # shadow side
    cv.paint(cv.inter(hair, cv.m_rect(0, 56, 100, 70)), SHADOW)           # nape in shadow
    for (x, y) in [(26, 52), (27, 54), (29, 51), (31, 53), (34, 52), (37, 54)]:
        cv.paint(cv.m_line([(x + dx, y)]), SHADOW if x > 32 else WOOD_M)

    # ---- hat brim (wide, 60px)
    brim = cv.m_ellipse(33 + dx, 42, 30.4, 7.4)
    cv.shape(brim, HAT, hi=WOOD_D, lo=SHADOW)
    # brim underside shadow cast on hair is the outline; add highlight on left brim top
    cv.paint(cv.inter(brim, cv.m_rect(0, 0, 15 + dx, FH)), WOOD_D)
    cv.paint(cv.inter(brim, cv.m_rect(0, 0, 8 + dx, FH)), HAT)
    cv.paint(cv.inter(brim, cv.m_rect(54 + dx, 0, FW, FH)), SHADOW)

    # ---- crown with a dent
    crown = cv.m_poly([(17 + dx, 43), (18 + dx, 26), (19 + dx, 19), (23 + dx, 14), (29 + dx, 14),
                       (31 + dx, 17), (35 + dx, 17), (37 + dx, 14), (43 + dx, 14), (47 + dx, 19),
                       (48 + dx, 26), (49 + dx, 43)])
    cv.shape(crown, HAT, hi=WOOD_D, lo=SHADOW)
    cv.paint(cv.inter(crown, cv.m_rect(0, 0, 23 + dx, FH)), WOOD_D)      # lit left
    cv.paint(cv.inter(crown, cv.m_rect(0, 0, 20 + dx, FH)), WOOD_L)      # brightest strip
    cv.paint(cv.inter(crown, cv.m_rect(0, 0, 18 + dx, FH)), WOOD_D)
    cv.paint(cv.inter(crown, cv.m_rect(41 + dx, 0, FW, FH)), SHADOW)     # shadow right
    # dent crease running down the crown
    cv.paint(cv.m_line(bresenham(33 + dx, 18, 33 + dx, 29)), SHADOW)
    cv.paint(cv.m_line(bresenham(31 + dx, 17, 32 + dx, 21)), SHADOW)
    cv.paint(cv.m_line(bresenham(36 + dx, 17, 35 + dx, 21)), SHADOW)
    # hat band: 1px wood highlight
    band = cv.inter(cv.m_rect(0, 36, FW, 36), cv.minus(crown, cv.minus(cv.dilate(crown), crown)))
    cv.paint(band, WOOD_H)
    cv.paint(cv.inter(band, cv.m_rect(40 + dx, 0, FW, FH)), WOOD_L)
    # brim shadow line under the crown (crown base)
    cv.paint(cv.inter(cv.m_rect(0, 43, FW, 43), crown), SHADOW)


# ---------------------------------------------------------------- arm
def rot(v, deg):
    a = math.radians(deg)
    return (v[0] * math.cos(a) - v[1] * math.sin(a), v[0] * math.sin(a) + v[1] * math.cos(a))


def norm(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


def draw_arm(cv, S, E, H, hand, body_mask):
    """Sleeve S->E (shirt red), forearm E->H (skin), hand styles: fist/open/relaxed."""
    sleeve = cv.m_stamp_line(S, E, 2)
    d = norm((H[0] - E[0], H[1] - E[1]))
    f0 = (E[0] + d[0] * 3, E[1] + d[1] * 3)
    fore = cv.m_stamp_line(f0, H, 2)
    # hand
    if hand == "fist":
        hand_m = cv.m_stamp_line((H[0], H[1]), (H[0] + d[0] * 2, H[1] + d[1] * 2), 2)
        fingers = None
    elif hand == "open":
        palm = cv.m_stamp_line((H[0], H[1]), (H[0] + d[0] * 1, H[1] + d[1] * 1), 2)
        fm = cv.mask()
        base = (H[0] + d[0] * 2, H[1] + d[1] * 2)
        for ang, ln in [(-70, 4), (-36, 6), (-8, 8), (20, 7), (48, 5)]:
            v = rot(d, ang)
            fm = cv.union(fm, cv.m_line(bresenham(base[0], base[1], base[0] + v[0] * ln, base[1] + v[1] * ln)))
        hand_m = cv.union(palm, fm)
        fingers = fm
    else:  # relaxed, fingers drooping and slightly curled
        palm = cv.m_stamp_line((H[0], H[1]), (H[0] + d[0] * 1, H[1] + d[1] * 1), 2)
        fm = cv.mask()
        base = (H[0] + d[0] * 2, H[1] + d[1] * 2)
        for ang, ln in [(30, 3), (52, 4), (74, 4), (96, 3)]:
            v = rot(d, ang)
            fm = cv.union(fm, cv.m_line(bresenham(base[0], base[1], base[0] + v[0] * ln, base[1] + v[1] * ln)))
        hand_m = cv.union(palm, fm)
        fingers = fm
    skin = cv.union(fore, hand_m)

    # sleeve: outline only where it leaves the torso
    cv.shape(sleeve, SHIRT, hi=RED, lo=DRED, out_mask=cv.minus(cv.dilate(sleeve), body_mask))
    cv.shape(skin, SKIN, lo=TAN)
    if fingers is not None:
        cv.paint(fingers, SKIN)
    # cuff line where skin meets sleeve
    return skin, d


def draw_grip(cv, H, d, dart_angle):
    """Thumb + finger pinch over the dart shaft."""
    pinch = cv.m_stamp_line((H[0] - 1, H[1] - 1), (H[0] + 1, H[1] + 1), 1)
    cv.shape(pinch, SKIN, lo=TAN)
    cv.paint(cv.m_line([(round(H[0] + d[0] * 2), round(H[1] + d[1] * 2))]), TAN)


# ---------------------------------------------------------------- frames
SHOULDER = (80, 72)
# lean, elbow, hand, hand-style, dart angle (None=no dart)
FRAMES = [
    dict(lean=0,  E=(85, 85), H=(73, 54), hand="fist",    dart=62),   # 0 idle
    dict(lean=0,  E=(85, 82), H=(69, 52), hand="fist",    dart=22),   # 1 aim
    dict(lean=-1, E=(87, 74), H=(63, 50), hand="fist",    dart=30),   # 2 cocked
    dict(lean=1,  E=(81, 56), H=(87, 39), hand="open",    dart=None), # 3 release
    dict(lean=1,  E=(81, 60), H=(89, 47), hand="open",    dart=None), # 4 follow-through
    dict(lean=0,  E=(85, 84), H=(82, 68), hand="relaxed", dart=None), # 5 recover
]


def make_frame(f):
    cv = Canvas(FW, FH)
    dx = f["lean"]
    body_head(cv, dx)
    # torso mask for sleeve outline suppression
    torso = cv.m_poly([(-4 + dx, 112), (-4 + dx, 80), (4 + dx, 71), (22 + dx, 65), (28 + dx, 62),
                       (38 + dx, 62), (44 + dx, 65), (66 + dx, 67), (88 + dx, 71),
                       (100 + dx, 80), (100 + dx, 112)])
    S = (SHOULDER[0] + dx, SHOULDER[1])
    E, H = f["E"], f["H"]
    skin, d = draw_arm(cv, S, E, H, f["hand"], torso)
    if f["dart"] is not None:
        ux, uy = unit(f["dart"])
        tail = (H[0] - ux * 8, H[1] - uy * 8)
        draw_dart(cv, tail, f["dart"], 26, fin_len=4.5, fin_span=3.0, tip_px=5)
        draw_grip(cv, H, d, f["dart"])
    return cv.im


# ---------------------------------------------------------------- dart sprites
def make_dart():
    cv = Canvas(16, 16)
    draw_dart(cv, (3.5, 12.0), 45, 13.5, fin_len=4.5, fin_span=2.6)
    return cv.im


def make_dart_stuck():
    cv = Canvas(12, 12)
    cx = cy = 5  # 9x9 cross occupies 1..9
    cross = cv.mask()
    d = ImageDraw.Draw(cross)
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if abs(dx) <= 1 or abs(dy) <= 1:
                d.point((cx + dx, cy + dy), fill=255)
    cv.paint(cv.shift(cv.dilate(cross), 1, 1), SHADOW)   # 1px drop shadow down-right
    cv.paint(cv.dilate(cross), OUT)
    cv.paint(cross, DRED)
    lit = cv.mask()
    d = ImageDraw.Draw(lit)
    for dy in range(-4, 5):
        for dx in range(-4, 5):
            if (abs(dx) <= 1 or abs(dy) <= 1) and dx + dy <= 0 and not (dx == 1 and dy == -1 and False):
                d.point((cx + dx, cy + dy), fill=255)
    cv.paint(lit, RED)
    # fin creases: dark-red lines between the four fins
    for (x, y) in [(cx - 1, cy - 1), (cx + 1, cy - 1), (cx - 1, cy + 1), (cx + 1, cy + 1)]:
        cv.paint(cv.m_line([(x, y)]), DRED if (x + y) % 2 else RED)
    cv.paint(cv.m_line([(cx, cy)]), OUT)  # centre dot
    return cv.im


# ---------------------------------------------------------------- output
def palette_check(ims):
    allowed = {OUT, SHADOW, WOOD_D, WOOD_M, WOOD_L, WOOD_H, CREAM, TAN, RED, DRED, SKIN, SHIRT, HAT, SHAFT}
    bad = {}
    for name, im in ims.items():
        for p in im.get_flattened_data() if hasattr(im,'get_flattened_data') else im.getdata():
            if p[3] == 0:
                continue
            if p[3] != 255 or p not in allowed:
                bad[(name, p)] = bad.get((name, p), 0) + 1
    return bad


def main():
    os.makedirs(ASSETS, exist_ok=True)
    frames = [make_frame(f) for f in FRAMES]
    strip = Image.new("RGBA", (FW * NFRAMES, FH), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * FW, 0))
    strip.save(os.path.join(ASSETS, "thrower.png"))
    dart = make_dart()
    stuck = make_dart_stuck()
    dart.save(os.path.join(ASSETS, "dart.png"))
    stuck.save(os.path.join(ASSETS, "dart-stuck.png"))

    # preview
    S3, S6 = 3, 6
    pw = FW * NFRAMES * S3 + 20 + 16 * S6 + 20 + 12 * S6 + 20
    ph = FH * S3 + 20
    pv = Image.new("RGBA", (pw, ph), hx("7a4426"))
    pv.alpha_composite(strip.resize((strip.width * S3, strip.height * S3), Image.NEAREST), (0, 10))
    x = FW * NFRAMES * S3 + 20
    pv.alpha_composite(dart.resize((16 * S6, 16 * S6), Image.NEAREST), (x, 10))
    x += 16 * S6 + 20
    pv.alpha_composite(stuck.resize((12 * S6, 12 * S6), Image.NEAREST), (x, 10))
    pv.convert("RGB").save(os.path.join(HERE, "preview-thrower.png"))

    bad = palette_check({"strip": strip, "dart": dart, "stuck": stuck})
    print("palette violations:", bad if bad else "none")
    print("strip", strip.size, "dart", dart.size, "stuck", stuck.size)
    for i, f in enumerate(FRAMES):
        print("frame", i, "hand", (f["H"]), "lean", f["lean"], "elbow", f["E"])


if __name__ == "__main__":
    main()
