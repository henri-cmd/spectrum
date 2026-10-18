"""Sonar dartboard game: sonar operator sprite strip (6 frames), blip and ping icons.

Run from the project folder:  .venv/bin/python art/sonar_operator.py
Writes assets/sonar/operator.png, assets/sonar/blip.png, assets/sonar/ping.png,
art/preview-sonar-operator.png
"""
import math
import os
from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ASSETS = os.path.join(ROOT, "assets", "sonar")


def hx(s):
    s = s.lstrip("#")
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


OUT = hx("0a0e12")
ST_DKST = hx("121a22")
ST_DK = hx("1b2430")
ST_MID = hx("2b3a4a")
ST_LT = hx("3e5266")
ST_HI = hx("5a7085")
ST_PALE = hx("8da2b5")
PH_DKST = hx("0c2a1c")
PH_DK = hx("145c35")
PH_MID = hx("27a85e")
PH_LT = hx("6cf29b")
PH_PALE = hx("c8ffd9")
AMBER = hx("f0a030")
AMBER_LT = hx("ffd36b")
AMBER_DK = hx("9a5a12")
RUBBER = hx("1e1e22")
SKIN = hx("e0a885")
SKIN_SH = hx("b07a5a")
NAVY = hx("22304a")
NAVY_LT = hx("34496b")
WHITE = hx("f2f4f6")

PALETTE = {OUT, ST_DKST, ST_DK, ST_MID, ST_LT, ST_HI, ST_PALE, PH_DKST, PH_DK, PH_MID, PH_LT,
           PH_PALE, AMBER, AMBER_LT, AMBER_DK, hx("d9342b"), hx("7a1a14"), hx("c9a247"),
           hx("7d5f24"), RUBBER, SKIN, SKIN_SH, NAVY, NAVY_LT, WHITE}

FW, FH = 96, 110
NFRAMES = 6
BUTTON = (86, 44)


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

    def px(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.im.putpixel((x, y), color)

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

    def m_ring(self, cx, cy, a, b, a2, b2):
        return self.minus(self.m_ellipse(cx, cy, a, b), self.m_ellipse(cx, cy, a2, b2))

    def m_pts(self, pts):
        m = self.mask()
        d = ImageDraw.Draw(m)
        for p in pts:
            d.point(p, fill=255)
        return m

    def m_stamp_line(self, p0, p1, r=2):
        """Thick limb: rounded (2r+1) square stamp walked along a Bresenham line."""
        m = self.mask()
        d = ImageDraw.Draw(m)
        for (x, y) in bresenham(p0[0], p0[1], p1[0], p1[1]):
            for oy in range(-r, r + 1):
                for ox in range(-r, r + 1):
                    if abs(ox) == r and abs(oy) == r and r >= 2:
                        continue
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

    def edge_tl(self, m):
        """Pixels of m with no neighbour up-left (lit edge)."""
        return self.minus(m, self.shift(m, 1, 1))

    def edge_right(self, m):
        return self.minus(m, self.shift(m, -1, 0))

    def edge_bottom(self, m):
        return self.minus(m, self.shift(m, 0, -1))

    def outline_of(self, m):
        return self.minus(self.dilate(m), m)


def mask_pixels(m):
    w, h = m.size
    d = m.load()
    return [(x, y) for y in range(h) for x in range(w) if d[x, y]]


# ---------------------------------------------------------------- body
HC = 30        # head centre x
HEAD_Y = 50    # head centre y


def draw_torso(cv):
    """Navy shoulders, cut off by the bottom edge; returns the torso mask."""
    torso = cv.m_poly([(0, 112), (0, 92), (3, 90), (12, 85), (20, 81), (24, 79),
                       (36, 79), (40, 81), (50, 84), (60, 86), (66, 87), (70, 89),
                       (72, 92), (72, 112)])
    cv.paint(cv.dilate(torso), OUT)
    cv.paint(torso, NAVY)
    # uniform-light highlights: a soft ridge along the top of each shoulder, seams and folds
    ridge = cv.minus(torso, cv.shift(torso, 0, 2))
    cv.paint(cv.inter(ridge, cv.m_rect(0, 0, 66, FH)), NAVY_LT)
    # shadow below the head / nape
    shadow = cv.inter(cv.m_ellipse(HC, 82, 14, 5), torso)
    cv.paint(shadow, ST_DK)
    # back seam and shoulder-blade folds
    cv.paint(cv.m_pts(bresenham(HC, 88, HC, 109)), ST_DK)
    cv.paint(cv.m_pts(bresenham(12, 96, 15, 108)), NAVY_LT)
    cv.paint(cv.m_pts(bresenham(48, 95, 45, 108)), ST_DK)
    cv.paint(cv.m_pts(bresenham(58, 94, 56, 103)), ST_DK)
    cv.paint(cv.m_pts(bresenham(5, 98, 8, 107)), NAVY_LT)
    # right edge of the torso in shadow, away from the scope
    cv.paint(cv.inter(cv.minus(torso, cv.shift(torso, -2, 0)), cv.m_rect(0, 92, FW, FH)), ST_DK)
    # cold phosphor rim on the upper-left edge of the shoulders
    rim = cv.inter(cv.edge_tl(torso), cv.m_rect(0, 0, 62, FH))
    cv.paint(rim, PH_DK)
    cv.paint(cv.inter(rim, cv.m_rect(0, 0, 38, 95)), PH_MID)
    cv.paint(cv.inter(rim, cv.m_rect(0, 0, 16, 95)), PH_LT)
    return torso


def draw_collar(cv):
    """Collar around the neck base with a 1px white edge on top."""
    collar = cv.m_poly([(20, 80), (22, 75), (38, 75), (40, 80), (36, 82), (24, 82)])
    cv.paint(cv.dilate(collar), OUT)
    cv.paint(collar, NAVY_LT)
    cv.paint(cv.m_rect(24, 80, 36, 82), NAVY)
    # white edge along the top of the collar
    top = cv.minus(collar, cv.shift(collar, 0, 1))
    cv.paint(top, WHITE)
    cv.paint(cv.m_pts([(21, 77), (21, 78), (39, 77), (39, 78)]), WHITE)
    # phosphor light touches the left end of the collar edge
    cv.paint(cv.m_pts([(22, 75), (23, 75)]), PH_PALE)


def draw_head(cv, dy):
    """Back of the head, headphones. dy = vertical offset of the head (tilt)."""
    cy = HEAD_Y + dy
    # neck (fixed in place, drawn by caller); here: hair + headphones
    hair = cv.m_ellipse(HC, cy - 2, 15.5, 17.5)
    # nape narrows toward the neck
    nape = cv.m_poly([(HC - 9, cy + 10), (HC + 9, cy + 10), (HC + 7, cy + 14), (HC - 7, cy + 14)])
    hair = cv.union(hair, nape)

    # headband: ring over the top of the head
    band = cv.minus(cv.m_ellipse(HC, cy - 2, 18.5, 20.5), cv.m_ellipse(HC, cy - 2, 15.5, 17.5))
    band = cv.inter(band, cv.m_rect(0, 0, FW, cy + 6))
    # cups
    lc = (HC - 18, cy + 1)
    rc = (HC + 18, cy + 1)
    cupL = cv.m_ellipse(lc[0], lc[1], 6.4, 7.4)
    cupR = cv.m_ellipse(rc[0], rc[1], 6.4, 7.4)
    # silhouette -> outline
    sil = cv.union(hair, band, cupL, cupR)
    cv.paint(cv.dilate(sil), OUT)
    # hair
    cv.paint(hair, ST_DKST)
    for (x, y) in [(22, 44), (25, 40), (28, 37), (31, 42), (35, 38), (38, 44), (24, 52), (33, 49),
                   (27, 58), (36, 56), (30, 62), (20, 56), (40, 52), (29, 47), (34, 60)]:
        cv.paint(cv.inter(cv.m_pts([(x, y + dy)]), hair), RUBBER)
    # hairline at the nape
    cv.paint(cv.inter(cv.m_rect(0, cy + 12, FW, cy + 20), hair), RUBBER)
    # scope light grazes the upper-left of the hair
    inner = cv.minus(cv.minus(hair, cv.shift(hair, 2, 2)), cv.edge_tl(hair))
    cv.paint(cv.inter(inner, cv.m_rect(0, 0, 34, cy)), ST_DK)
    # band
    cv.paint(band, RUBBER)
    # band specular: 1px steel highlight down the middle of the band
    mid = cv.minus(cv.m_ellipse(HC, cy - 2, 17.0, 19.0), cv.m_ellipse(HC, cy - 2, 16.0, 18.0))
    mid = cv.inter(mid, cv.inter(band, cv.m_rect(0, 0, FW, cy + 4)))
    cv.paint(mid, ST_LT)
    cv.paint(cv.inter(mid, cv.m_rect(0, 0, 36, cy - 8)), ST_HI)
    # yoke where the band meets each cup
    # cups: rubber body, steel highlight rim, inner disc
    for (c, cup, right) in ((lc, cupL, False), (rc, cupR, True)):
        cv.paint(cup, RUBBER)
        inner = cv.m_ellipse(c[0], c[1], 4.4, 5.4)
        cv.paint(inner, ST_DK)
        inner2 = cv.m_ellipse(c[0], c[1], 2.4, 3.4)
        cv.paint(inner2, ST_MID)
        # steel-highlight rim on the cup edge (ring, lit side only)
        ring = cv.minus(cup, cv.m_ellipse(c[0], c[1], 5.2, 6.2))
        cv.paint(ring, ST_HI)
        cv.paint(cv.inter(ring, cv.m_rect(0, cy + 6, FW, FH)), ST_LT)
        # inner highlight on the cup surface
        cv.paint(cv.m_pts([(c[0] - 1, c[1] - 2), (c[0] - 1, c[1] - 1)]), ST_HI)
    # amber light indicator on the right cup
    ax, ay = rc[0] + 1, rc[1] + 1
    cv.paint(cv.m_rect(ax - 1, ay - 1, ax, ay), AMBER_LT)
    cv.paint(cv.m_pts([(ax + 1, ay), (ax + 1, ay + 1), (ax - 1, ay + 1), (ax, ay + 1)]), AMBER_DK)
    cv.paint(cv.m_pts([(ax, ay)]), AMBER)
    cv.paint(cv.m_pts([(ax - 1, ay - 1)]), AMBER_LT)
    # cold phosphor rim light on the upper-left edge of head and cup
    rim = cv.inter(cv.edge_tl(sil), cv.m_rect(0, 0, 46, cy + 12))
    cv.paint(rim, PH_DK)
    cv.paint(cv.inter(rim, cv.m_rect(0, 0, FW, cy + 8)), PH_MID)
    cv.paint(cv.inter(rim, cv.m_rect(0, 0, 24, cy - 6)), PH_LT)
    return sil


def draw_neck(cv):
    neck = cv.m_rect(HC - 5, 63, HC + 5, 78)
    cv.paint(cv.dilate(neck), OUT)
    cv.paint(neck, SKIN_SH)
    cv.paint(cv.m_rect(HC - 5, 63, HC + 5, 66), ST_DK)  # shadow under hair
    cv.paint(cv.m_rect(HC - 5, 67, HC - 5, 74), SKIN)   # a sliver of scope light on the left side


# ---------------------------------------------------------------- arm
def norm(v):
    l = math.hypot(*v) or 1.0
    return (v[0] / l, v[1] / l)


def draw_button(cv, state, pressed=False):
    """state: 'off' (amber dark dome), 'lit' (amber light), 'amber' (amber)."""
    bx, by = BUTTON
    dy = 1 if pressed else 0
    base = cv.m_rect(bx - 7, by, bx + 6, by + 2)
    rows = [(4, 37), (8, 38), (10, 39), (12, 40), (12, 41), (12, 42)]
    dome = cv.mask()
    d = ImageDraw.Draw(dome)
    for w, y in rows:
        x0 = bx - 6 + (12 - w) // 2
        d.rectangle([x0, y + dy, x0 + w - 1, y + dy], fill=255)
    sep = cv.m_rect(bx - 7, by - 1 + dy, bx + 6, by - 1 + dy) if not pressed else cv.m_rect(bx - 7, by, bx + 6, by)
    whole = cv.union(base, dome, sep)
    cv.paint(cv.dilate(whole), OUT)
    cv.paint(base, AMBER_DK)
    cv.paint(cv.m_rect(bx - 7, by + 2, bx + 6, by + 2), ST_MID)
    cv.paint(sep, OUT)
    if state == "lit":
        main, hi, lo = AMBER_LT, AMBER_LT, AMBER
    elif state == "amber":
        main, hi, lo = AMBER, AMBER_LT, AMBER_DK
    else:
        main, hi, lo = AMBER_DK, AMBER_DK, AMBER_DK
    cv.paint(dome, main)
    if state != "off":
        cv.paint(cv.edge_bottom(dome), lo)
        cv.paint(cv.edge_right(dome), lo)
        cv.paint(cv.m_pts([(bx - 4, 40 + dy), (bx - 3, 39 + dy), (bx - 4, 39 + dy), (bx - 2, 38 + dy)]), hi if state == "amber" else WHITE if False else hi)
    else:
        cv.paint(cv.m_pts([(bx - 4, 40 + dy), (bx - 4, 41 + dy)]), ST_LT)


def hand_masks(cv, W, d, style, T=None, fl=0):
    """Skin hand starting at wrist W, forward direction d (unit). Returns (skin mask, creases mask)."""
    px, py = -d[1], d[0]  # perpendicular
    palm_end = (W[0] + d[0] * 1.0, W[1] + d[1] * 1.0)
    palm = cv.m_stamp_line(W, palm_end, 2)
    crease = cv.mask()
    if style == "relaxed":
        # fingers curl down/forward off the palm: a block of four short fingers
        base = (round(W[0] + d[0] * 3), round(W[1] + d[1] * 3))
        fm = cv.m_stamp_line(base, (base[0] + d[0] * 2, base[1] + d[1] * 2), 2)
        fm = cv.union(fm, cv.m_stamp_line((base[0] + 1, base[1] + 1), (base[0] + 1 + d[0] * 2, base[1] + 1 + d[1] * 2), 2))
        thumb = cv.m_pts([(round(W[0] - px * 3), round(W[1] - py * 3)),
                          (round(W[0] - px * 3 + d[0]), round(W[1] - py * 3 + d[1]))])
        skin = cv.union(palm, fm, thumb)
        # finger separations
        cr = []
        for k in (-1, 0, 1):
            cr.append((round(base[0] + d[0] * 2 + px * k * 1.2), round(base[1] + d[1] * 2 + py * k * 1.2)))
        crease = cv.m_pts(cr)
        return skin, crease
    # pointing: fist + index finger of length fl toward T
    fist = cv.m_stamp_line(W, (W[0] + d[0] * 2, W[1] + d[1] * 2), 2)
    thumb = cv.m_stamp_line((W[0] - px * 3 + d[0], W[1] - py * 3 + d[1]),
                            (W[0] - px * 3 + d[0] * 3, W[1] - py * 3 + d[1] * 3), 1)
    fe = (W[0] + d[0] * 2, W[1] + d[1] * 2)
    # finger: 2px wide, goes to the tip T (or fl px further)
    fpts = bresenham(fe[0] + d[0] * 1, fe[1] + d[1] * 1, T[0], T[1])
    fm = cv.m_pts(fpts)
    fm = cv.union(fm, cv.shift(fm, 1, 0))
    # knuckle crease
    ky = (round(W[0] + d[0] * 2 + px * 2), round(W[1] + d[1] * 2 + py * 2))
    crease = cv.m_pts([(round(W[0] + d[0] * 3 + px * k), round(W[1] + d[1] * 3 + py * k)) for k in (-2, -1, 0, 1, 2)][:0])
    skin = cv.union(fist, thumb, fm)
    return skin, crease


def draw_arm(cv, S, E, W, style, T, torso, dy_hand=0):
    """Sleeve S->E->W (5px thick, navy) then skin hand from W."""
    sleeve = cv.union(cv.m_stamp_line(S, E, 2), cv.m_stamp_line(E, W, 2))
    if style == "point":
        d = norm((T[0] - W[0], T[1] - W[1]))
    else:
        d = norm((W[0] - E[0], W[1] - E[1]))
    skin, crease = hand_masks(cv, W, d, style, T)
    skin = cv.minus(skin, cv.m_rect(0, 0, 0, 0))
    # silhouette outline: black outside the torso, steel darkest over it
    sil = cv.union(sleeve, skin)
    ring = cv.outline_of(sil)
    cv.paint(cv.minus(ring, torso), OUT)
    cv.paint(cv.inter(ring, torso), ST_DKST)
    cv.paint(sleeve, NAVY)
    # sleeve shading: uniform light on the upper-left edge, amber dark on the lower-right
    cv.paint(cv.minus(cv.edge_tl(sleeve), skin), NAVY_LT)
    cv.paint(cv.minus(cv.inter(cv.edge_right(sleeve), cv.m_rect(0, 0, FW, FH)), skin), ST_DK)
    # warm lamp light on the right side of the sleeve (outer, only the part beyond the torso)
    lamp = cv.minus(cv.minus(cv.edge_right(sleeve), torso), skin)
    cv.paint(cv.inter(lamp, cv.m_rect(0, 0, FW, W[1] + 1)), AMBER_DK)
    # cuff: uniform light band across the sleeve end, white edge
    cuff = cv.m_stamp_line((round(W[0] - d[0] * 1), round(W[1] - d[1] * 1)),
                           (round(W[0] - d[0] * 1), round(W[1] - d[1] * 1)), 2)
    cuff = cv.inter(cuff, sleeve)
    cv.paint(cuff, NAVY_LT)
    # hand
    cv.paint(skin, SKIN)
    cv.paint(cv.edge_bottom(skin), SKIN_SH)
    cv.paint(cv.minus(skin, cv.shift(skin, 0, 1)), SKIN)  # keep top edge light
    cv.paint(crease, SKIN_SH)
    # warm amber on the right side of the hand (console lamps)
    cv.paint(cv.edge_right(skin), AMBER)
    # shade where hand meets the sleeve
    return sil, d


# ---------------------------------------------------------------- frames
S = (64, 91)
# E elbow, W wrist, T fingertip, style, head dy, button (None/off/lit/amber), pressed
FRAMES = [
    dict(E=(68, 102), W=(83, 100), style="relaxed", T=None, dy=0, btn="off"),                       # 0 idle
    dict(E=(75, 88), W=(85, 71), style="point", T=(87, 63), dy=0, btn="off"),                       # 1 reach
    dict(E=(80, 70), W=(84, 54), style="point", T=(86, 44), dy=-1, btn="lit"),                      # 2 press
    dict(E=(80, 71), W=(84, 55), style="point", T=(86, 45), dy=-1, btn="lit", pressed=True, glint=True),  # 3 held
    dict(E=(79, 74), W=(83, 59), style="point", T=(85, 49), dy=0, btn="amber"),                     # 4 release
    dict(E=(71, 96), W=(85, 86), style="relaxed", T=None, dy=0, btn="off"),                         # 5 return
]


def make_frame(f):
    cv = Canvas(FW, FH)
    torso = draw_torso(cv)
    draw_neck(cv)
    draw_collar(cv)
    draw_head(cv, f["dy"])
    if f.get("btn"):
        draw_button(cv, f["btn"], f.get("pressed", False))
    sil, d = draw_arm(cv, S, f["E"], f["W"], f["style"], f["T"], torso)
    if f.get("glint"):
        cv.px(f["T"][0], f["T"][1], PH_PALE)
    return cv.im


# ---------------------------------------------------------------- blip / ping
def make_blip():
    cv = Canvas(12, 12)
    # outer ring, phosphor mid, gaps at the diagonals
    for y in range(12):
        for x in range(12):
            dx, dy = x - 5.5, y - 5.5
            dist = math.hypot(dx, dy)
            if 4.4 <= dist <= 5.4 and abs(abs(dx) - abs(dy)) > 1.2:
                cv.px(x, y, PH_MID)
    # inner ring, phosphor light: rounded square around the core
    for y in range(3, 9):
        for x in range(3, 9):
            dx, dy = abs(x - 5.5), abs(y - 5.5)
            if max(dx, dy) == 2.5 and not (dx == 2.5 and dy == 2.5):
                cv.px(x, y, PH_LT)
    # core
    for (x, y) in [(5, 5), (6, 5), (5, 6), (6, 6)]:
        cv.px(x, y, PH_PALE)
    return cv.im


def make_ping():
    cv = Canvas(16, 16)
    cx, cy = 2.0, 13.0
    for r, col in ((4.6, PH_LT), (8.0, PH_MID), (11.4, PH_DK)):
        for y in range(16):
            for x in range(16):
                dx, dy = x - cx, cy - y
                if dx < 1 or dy < 1:
                    continue
                ang = math.degrees(math.atan2(dy, dx))
                if ang < 4 or ang > 86:
                    continue
                if abs(math.hypot(dx, dy) - r) <= 0.62:
                    cv.px(x, y, col)
    for (x, y) in [(1, 13), (2, 13), (1, 14), (2, 14)]:
        cv.px(x, y, PH_PALE)
    return cv.im


# ---------------------------------------------------------------- output
def palette_check(ims):
    bad = {}
    for name, im in ims.items():
        for p in im.get_flattened_data():
            if p[3] == 0:
                continue
            if p[3] != 255 or p not in PALETTE:
                bad[(name, p)] = bad.get((name, p), 0) + 1
    return bad


def main():
    os.makedirs(ASSETS, exist_ok=True)
    frames = [make_frame(f) for f in FRAMES]
    strip = Image.new("RGBA", (FW * NFRAMES, FH), (0, 0, 0, 0))
    for i, fr in enumerate(frames):
        strip.paste(fr, (i * FW, 0))
    strip.save(os.path.join(ASSETS, "operator.png"))
    blip = make_blip()
    ping = make_ping()
    blip.save(os.path.join(ASSETS, "blip.png"))
    ping.save(os.path.join(ASSETS, "ping.png"))

    S3, S6 = 3, 6
    pw = FW * NFRAMES * S3 + 20 + 12 * S6 + 20 + 16 * S6 + 20
    ph = FH * S3 + 20
    pv = Image.new("RGBA", (pw, ph), ST_MID)
    pv.alpha_composite(strip.resize((strip.width * S3, strip.height * S3), Image.NEAREST), (0, 10))
    x = FW * NFRAMES * S3 + 20
    pv.alpha_composite(blip.resize((12 * S6, 12 * S6), Image.NEAREST), (x, 10))
    x += 12 * S6 + 20
    pv.alpha_composite(ping.resize((16 * S6, 16 * S6), Image.NEAREST), (x, 10))
    pv.convert("RGB").save(os.path.join(HERE, "preview-sonar-operator.png"))

    bad = palette_check({"strip": strip, "blip": blip, "ping": ping})
    print("palette violations:", bad if bad else "none")
    print("sizes: strip", strip.size, "blip", blip.size, "ping", ping.size)
    print("button position:", BUTTON)
    for i, f in enumerate(FRAMES):
        print("frame", i, "fingertip", f["T"] if f["T"] else "n/a (relaxed hand, wrist %s)" % (f["W"],),
              "button", f["btn"], "pressed" if f.get("pressed") else "")


if __name__ == "__main__":
    main()
