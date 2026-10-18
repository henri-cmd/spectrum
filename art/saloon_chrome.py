"""UI chrome sprites: tiles, 9-slices, star, nail, skull, mug, bottle.
Run: .venv/bin/python art/chrome.py   (from the project folder)"""
import os, random
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets", "saloon")
os.makedirs(ASSETS, exist_ok=True)

PAL = {
    "K": "#15090a", "S": "#2a1710", "D": "#5a2f1a", "M": "#7a4426", "L": "#9b5a2e",
    "H": "#b8763a", "P": "#d9a066", "C": "#f3e2b4", "T": "#c9a46a", "R": "#c8322e",
    "r": "#8e1d1d", "k": "#e9a0a0", "p": "#e07070", "O": "#e8792b", "G": "#f2b544",
    "U": "#5a2a3a", "A": "#ffb347", "X": "#f0c050", "g": "#4f6b3a", "s": "#e0a885",
    "t": "#a3241f", "h": "#3b2418",
}
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
COL = {k: rgb(v) for k, v in PAL.items()}
PALETTE_RGB = {c[:3] for c in COL.values()}
BG = rgb("#7a4426")

def c(k): return COL[k] if isinstance(k, str) and k in COL else k

class Cv:
    """Pixel canvas. wrap=True makes every write wrap around (for seamless tiles)."""
    def __init__(self, w, h, fill=None, wrap=False):
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.w, self.h, self.wrap = w, h, wrap
        if fill: self.rect(0, 0, w - 1, h - 1, fill)
    def px(self, x, y, k):
        if self.wrap: x, y = x % self.w, y % self.h
        elif not (0 <= x < self.w and 0 <= y < self.h): return
        self.img.putpixel((x, y), (0, 0, 0, 0) if k is None else c(k))
    def get(self, x, y):
        if self.wrap: x, y = x % self.w, y % self.h
        return self.img.getpixel((x, y))
    def rect(self, x0, y0, x1, y1, k):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): self.px(x, y, k)
    def hline(self, x0, x1, y, k):
        for x in range(x0, x1 + 1): self.px(x, y, k)
    def vline(self, x, y0, y1, k):
        for y in range(y0, y1 + 1): self.px(x, y, k)
    def outline(self, x0, y0, x1, y1, k):
        self.hline(x0, x1, y0, k); self.hline(x0, x1, y1, k)
        self.vline(x0, y0, y1, k); self.vline(x1, y0, y1, k)
    def bevel(self, x0, y0, x1, y1, n, hi, lo):
        """n-px mitred bevel inside the box: hi on top/left, lo on bottom/right."""
        for i in range(n):
            self.hline(x0 + i, x1 - i, y0 + i, hi)
            self.vline(x0 + i, y0 + i, y1 - i, hi)
            self.hline(x0 + i, x1 - i, y1 - i, lo)
            self.vline(x1 - i, y0 + i, y1 - i, lo)
        # mitre: top-right and bottom-left corners belong to the shadow side
        for i in range(n):
            self.px(x1 - i, y0 + i, lo); self.px(x0 + i, y1 - i, lo)
    def art(self, x0, y0, rows, mirror=False):
        for dy, row in enumerate(rows):
            if mirror: row = row + row[::-1]
            for dx, ch in enumerate(row):
                if ch != ".": self.px(x0 + dx, y0 + dy, ch)
    def save(self, name):
        self.img.save(os.path.join(ASSETS, name))
        return self.img

# ---------------------------------------------------------------- seamless check
def seam_report(img, name):
    """The colour jump across the wrap seam must be no bigger than the biggest jump at any
    interior column/row boundary (a plank gap or board gap meeting its neighbour is normal)."""
    w, h = img.size
    px = img.load()
    def d(p, q): return sum(abs(p[i] - q[i]) for i in range(3))
    cols = [sum(d(px[x, y], px[x + 1, y]) for y in range(h)) / h for x in range(w - 1)]
    seam_h = sum(d(px[w - 1, y], px[0, y]) for y in range(h)) / h
    rows = [sum(d(px[x, y], px[x, y + 1]) for x in range(w)) / w for y in range(h - 1)]
    seam_v = sum(d(px[x, h - 1], px[x, 0]) for x in range(w)) / w
    ok = seam_h <= max(cols) and seam_v <= max(rows)
    print(f"seam {name}: LR {seam_h:.1f} (interior max {max(cols):.1f}), TB {seam_v:.1f} (interior max {max(rows):.1f}) -> {'OK' if ok else 'SEAM!'}")
    return ok

# ---------------------------------------------------------------- tiles
def wall_tile():
    rnd = random.Random(7)
    cv = Cv(48, 48, "D", wrap=True)
    joins = [20, 41, 9, 30]                       # staggered plank end joins
    for p in range(4):
        y0 = p * 12
        cv.hline(0, 47, y0 + 11, "S")             # shadow gap under plank
        cv.hline(0, 47, y0, "M")                  # top edge catches the lamp
        # mid-wood variation streaks
        for _ in range(6):
            x, y, n = rnd.randrange(48), y0 + rnd.randrange(2, 10), rnd.randrange(5, 14)
            cv.hline(x, x + n - 1, y, "M")
        # plank end join (shadow line + lit edge on its right)
        j = joins[p]
        cv.vline(j, y0, y0 + 10, "S")
        cv.vline(j + 1, y0 + 1, y0 + 10, "M")
    # grain dashes (wood highlight), 3-6 px
    for (x, y, n) in [(4, 5, 5), (27, 7, 4), (14, 18, 6), (36, 21, 3), (3, 31, 5), (22, 42, 4), (38, 34, 4)]:
        cv.hline(x, x + n - 1, y, "H")
    # knots
    for (x, y) in [(33, 15), (15, 38)]:
        cv.rect(x - 1, y - 1, x + 2, y + 1, "M")
        cv.hline(x, x + 1, y, "S")
        cv.px(x - 1, y - 1, "D"); cv.px(x + 2, y + 1, "D")
    cv.save("wall-tile.png")
    return cv.img

def floor_tile():
    rnd = random.Random(11)
    cv = Cv(48, 48, "M", wrap=True)
    for b in range(6):                             # 6 boards, 8px pitch (7px board + 1px gap)
        x0 = b * 8
        cv.vline(x0 + 7, 0, 47, "D")               # gap
        cv.vline(x0, 0, 47, "L")                   # lit left edge
        for _ in range(5):                         # lighter grain streaks
            x, y, n = x0 + rnd.randrange(2, 6), rnd.randrange(48), rnd.randrange(3, 8)
            cv.vline(x, y, y + n - 1, "L")
        for _ in range(3):                         # darker flecks
            cv.px(x0 + rnd.randrange(2, 7), rnd.randrange(48), "D")
        # staggered joins: dark line with a lit lip below
        for jy in ([(b * 17 + 5) % 48, (b * 17 + 29) % 48]):
            cv.hline(x0, x0 + 6, jy, "D")
            cv.hline(x0 + 1, x0 + 6, jy + 1, "L")
    cv.save("floor-tile.png")
    return cv.img

# ---------------------------------------------------------------- 9-slices
def nail3(cv, x, y):
    cv.rect(x, y, x + 2, y + 2, "C")
    cv.px(x + 2, y + 2, "S")

def sign_9slice():
    cv = Cv(36, 36)
    cv.outline(0, 0, 35, 35, "K")
    cv.bevel(1, 1, 34, 34, 2, "H", "D")
    cv.rect(3, 3, 32, 32, "M")
    # faint horizontal grain on the top/bottom bands only (centre stays plain)
    for (x0, x1, y) in [(5, 29, 5), (8, 33, 9), (3, 24, 27), (9, 31, 31), (11, 22, 7), (13, 26, 29)]:
        cv.hline(x0, x1, y, "L")
    for (x, y) in [(4, 4), (29, 4), (4, 29), (29, 29)]:
        nail3(cv, x, y)
    cv.save("sign-9slice.png")
    return cv.img

def panel_9slice():
    cv = Cv(36, 36)
    cv.outline(0, 0, 35, 35, "K")
    cv.rect(1, 1, 34, 34, "M")
    cv.rect(3, 3, 32, 32, "S")
    cv.hline(3, 32, 3, "H"); cv.vline(3, 3, 32, "H")      # inner highlight, top/left
    cv.save("panel-9slice.png")
    return cv.img

def button_9slice(active=False):
    cv = Cv(24, 24)
    cv.outline(0, 0, 23, 23, "K")
    cv.rect(1, 1, 22, 22, "X")
    cv.rect(3, 3, 20, 20, "X" if active else "S")
    if active:
        cv.hline(3, 20, 3, "r"); cv.vline(3, 3, 20, "r")  # dark-red inner shadow, top/left (pressed in)
    else:
        cv.hline(3, 20, 3, "A"); cv.vline(3, 3, 20, "A")  # lamp-glow highlight inside the border
    cv.save("button-active-9slice.png" if active else "button-9slice.png")
    return cv.img

def input_9slice():
    cv = Cv(24, 24)
    cv.outline(0, 0, 23, 23, "K")
    cv.hline(1, 22, 1, "D"); cv.vline(1, 1, 22, "D")       # inner shadow top/left
    cv.hline(2, 22, 22, "L"); cv.vline(22, 2, 22, "L")     # inner highlight bottom/right
    cv.rect(2, 2, 21, 21, "S")
    cv.save("input-9slice.png")
    return cv.img

# ---------------------------------------------------------------- small sprites
def star():
    cv = Cv(11, 11)
    cv.art(0, 0, [
        ".....K.....",
        "....KXK....",
        "....KXK....",
        "KKKKKXXKKKK"[:11],
        "KAAXXXXXXXK",
        ".KAXXXXXGK.",
        "..KXXXXXK..",
        "..KXXXXGK..",
        ".KXXKKKXGK.",
        ".KXK...KGK.",
        "KKK.....KKK",
    ])
    cv.save("star.png")
    return cv.img

def nail():
    cv = Cv(5, 5)
    cv.art(0, 0, [".CCC.", "CCCCT", "CCSCT", "CCTTT", ".TTT."])
    cv.save("nail.png")
    return cv.img

def skull():
    cv = Cv(24, 20)
    half = [
        "............",  # 0
        "KK..........",  # 1
        "KCK.........",  # 2
        "KCK....KKKKK",  # 3
        "KTK...KCCCCC",  # 4
        "KTKKKKCCCCCC",  # 5
        "KTTTTTCCCCCC",  # 6
        "KTTTTTCCCCCC",  # 7
        "KKKKKKKCSSCC",  # 8
        "......KCSSCC",  # 9
        "......KCSSCC",  # 10
        ".......KCSCC",  # 11
        ".......KCCCC",  # 12
        "........KCCC",  # 13
        "........KCSS",  # 14
        "........KCSS",  # 15
        "........KCCC",  # 16
        "........KTTT",  # 17
        "........KKKK",  # 18
        "............",  # 19
    ]
    cv.art(0, 0, half, mirror=True)
    # light from upper left: cream pixels backed by outline to the right/below become tan on the right half
    base = cv.img.copy(); px = base.load()
    for y in range(19):
        for x in range(8, 24):
            if px[x, y] == COL["C"] and (px[x + 1, y] == COL["K"] if x < 23 else False):
                cv.px(x, y, "T")
    for x in range(8, 24):                         # underside shade
        for y in range(19):
            if px[x, y] == COL["C"] and px[x, y + 1] == COL["K"]: cv.px(x, y, "T")
    cv.save("skull-small.png")
    return cv.img

def mug():
    cv = Cv(20, 26)
    # body
    cv.rect(1, 7, 14, 25, "K")
    cv.rect(2, 8, 13, 24, "T")                     # tan glass walls
    cv.rect(4, 8, 11, 22, "G")                     # sunset-gold beer
    cv.vline(11, 8, 22, "O")                       # shaded right edge of the beer
    cv.vline(4, 10, 20, "A")                       # lamp-lit left edge of the beer
    cv.vline(2, 9, 19, "P"); cv.vline(2, 22, 23, "P")  # pale glass highlights
    cv.vline(3, 10, 14, "C")
    cv.vline(13, 9, 23, "L")                       # shaded wall
    cv.hline(2, 13, 23, "L"); cv.hline(2, 13, 24, "L")  # thick base
    cv.hline(2, 13, 23, "T"); cv.hline(3, 13, 24, "L")
    # foam, overflowing the rim (wider than the glass) with drips
    cv.art(0, 0, [
        "....KKK..KKK.......",
        "...KCCCKKCCCK......",
        "..KCCCCCCCCCCK.....",
        ".KCCCCCCCCCCCCK....",
        ".KCCCCCCCCCCCCCK...",
        "KCCCCCCCCCCCCCCK...",
        "KCCCCCCCCCCCCCTK...",
        "KCCCCCCCCCCCCTTK...",
    ])
    cv.vline(15, 4, 6, "K")
    cv.rect(2, 8, 3, 8, "C"); cv.px(2, 9, "C"); cv.px(2, 10, "C"); cv.px(3, 9, "T")
    cv.rect(12, 8, 13, 8, "T"); cv.px(13, 9, "T"); cv.px(13, 10, "L")
    # handle
    cv.art(15, 10, [
        "KKKK.",
        "TTTTK",
        "KKKTK",
        "..KTK",
        "..KTK",
        "..KTK",
        "..KTK",
        "..KTK",
        "..KTK",
        "KKKTK",
        "TTTTK",
        "KKKK.",
    ])
    cv.save("mug.png")
    return cv.img

def bottle():
    cv = Cv(12, 30)
    # cap
    cv.rect(3, 0, 8, 2, "K"); cv.rect(4, 1, 7, 1, "S"); cv.px(4, 1, "L"); cv.px(5, 1, "D")
    # neck
    cv.rect(3, 3, 8, 11, "K"); cv.rect(4, 3, 7, 11, "D")
    cv.vline(4, 3, 11, "M"); cv.vline(7, 3, 11, "S")
    # shoulders
    cv.rect(2, 12, 9, 12, "K"); cv.rect(3, 12, 8, 12, "D"); cv.px(3, 12, "M")
    cv.rect(1, 13, 10, 13, "K"); cv.rect(2, 13, 9, 13, "D"); cv.px(2, 13, "M")
    # body
    cv.rect(0, 14, 11, 29, "K"); cv.rect(1, 14, 10, 28, "D")
    cv.vline(1, 14, 28, "M"); cv.vline(10, 14, 28, "S")
    cv.hline(1, 10, 28, "S"); cv.px(1, 28, "D")
    # glass glints
    cv.vline(2, 14, 15, "L"); cv.vline(2, 26, 27, "L")
    # label
    cv.rect(1, 17, 10, 25, "C")
    cv.hline(1, 10, 25, "T"); cv.vline(10, 17, 25, "T")
    cv.hline(3, 8, 19, "r"); cv.hline(3, 8, 20, "R")
    cv.hline(3, 8, 22, "T"); cv.hline(4, 7, 23, "T")
    cv.save("bottle.png")
    return cv.img

# ---------------------------------------------------------------- preview
def nine_slice(img, s, tw, th):
    w, h = img.size
    out = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    def piece(box, size, pos):
        out.paste(img.crop(box).resize(size, Image.NEAREST), pos)
    piece((0, 0, s, s), (s, s), (0, 0))
    piece((w - s, 0, w, s), (s, s), (tw - s, 0))
    piece((0, h - s, s, h), (s, s), (0, th - s))
    piece((w - s, h - s, w, h), (s, s), (tw - s, th - s))
    piece((s, 0, w - s, s), (tw - 2 * s, s), (s, 0))
    piece((s, h - s, w - s, h), (tw - 2 * s, s), (s, th - s))
    piece((0, s, s, h - s), (s, th - 2 * s), (0, s))
    piece((w - s, s, w, h - s), (s, th - 2 * s), (tw - s, s))
    piece((s, s, w - s, h - s), (tw - 2 * s, th - 2 * s), (s, s))
    return out

def tile2x2(img):
    w, h = img.size
    t = Image.new("RGBA", (w * 2, h * 2))
    for i in range(2):
        for j in range(2): t.paste(img, (i * w, j * h))
    return t

def preview(a):
    Z = 3
    BGC = BG
    def new(w, h): return Image.new("RGBA", (w, h), BGC)
    tiles = new(760, 340); d = ImageDraw.Draw(tiles)
    def put(sheet, im, x, y, label=None, z=Z):
        sheet.alpha_composite(im.resize((im.width * z, im.height * z), Image.NEAREST), (x, y))
        if label: ImageDraw.Draw(sheet).text((x, y - 11), label, fill=COL["C"])
    put(tiles, a["wall"], 10, 20, "wall-tile 48x48")
    put(tiles, tile2x2(a["wall"]), 170, 20, "wall 2x2 tiled", z=2)
    put(tiles, a["floor"], 10, 190, "floor-tile 48x48")
    put(tiles, tile2x2(a["floor"]), 170, 190, "floor 2x2 tiled", z=2)
    # sprites in the right column
    x = 400
    put(tiles, a["star"], x, 20, "star"); x += 11 * Z + 20
    put(tiles, a["nail"], x, 20, "nail"); x += 5 * Z + 20
    put(tiles, a["skull"], x, 20, "skull"); x += 24 * Z + 20
    put(tiles, a["mug"], x, 20, "mug"); x += 20 * Z + 20
    put(tiles, a["bottle"], x, 20, "bottle")
    # 9-slice area
    nine = new(760, 790)
    names = [("sign", 12), ("panel", 12), ("button", 8), ("button_a", 8), ("input", 8)]
    x = 10
    for n, s in names:
        put(nine, a[n], x, 20, n + " raw")
        x += a[n].width * Z + 14
    x, y = 10, 150
    for n, s in names:
        st = nine_slice(a[n], s, 120, 60)
        put(nine, st, x, y, n + " stretched 120x60", z=Z)
        x += 120 * Z + 12
        if x + 120 * Z > 760: x, y = 10, y + 60 * Z + 20
    sheet = new(760, tiles.height + nine.height)
    sheet.paste(tiles, (0, 0)); sheet.paste(nine, (0, tiles.height))
    sheet.save(os.path.join(HERE, "preview-saloon-chrome.png"))

def palette_check(files):
    ok = True
    for f in files:
        im = Image.open(os.path.join(ASSETS, f)).convert("RGBA")
        bad = {p[:3] for p in im.getdata() if p[3] and p[:3] not in PALETTE_RGB}
        alphas = {p[3] for p in im.getdata()}
        if bad or not alphas <= {0, 255}:
            ok = False; print("PALETTE FAIL", f, bad, alphas)
        else:
            print(f"{f:26s} {im.size[0]:>2}x{im.size[1]:<2} palette OK")
    return ok

if __name__ == "__main__":
    a = {
        "wall": wall_tile(), "floor": floor_tile(), "sign": sign_9slice(), "panel": panel_9slice(),
        "button": button_9slice(), "button_a": button_9slice(True), "input": input_9slice(),
        "star": star(), "nail": nail(), "skull": skull(), "mug": mug(), "bottle": bottle(),
    }
    seam_report(a["wall"], "wall"); seam_report(a["floor"], "floor")
    preview(a)
    files = ["wall-tile.png", "floor-tile.png", "sign-9slice.png", "panel-9slice.png", "button-9slice.png",
             "button-active-9slice.png", "input-9slice.png", "star.png", "nail.png", "skull-small.png",
             "mug.png", "bottle.png"]
    palette_check(files)
