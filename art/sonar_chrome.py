"""Sonar UI chrome sprites: tiles, 9-slices, sub, rivet, anchor, mug, headphones.
Run: .venv/bin/python art/sonar_chrome.py   (from the project folder)
Palette: art/PALETTE-SONAR.md  (flat fills, 1px outlines, no anti-aliasing)."""
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(HERE, "..", "assets", "sonar")
os.makedirs(ASSETS, exist_ok=True)

PAL = {
    "K": "#0a0e12",                                   # outline black
    "d": "#121a22", "D": "#1b2430", "M": "#2b3a4a",   # steel darkest / dark / mid
    "L": "#3e5266", "H": "#5a7085", "P": "#8da2b5",   # steel light / highlight / pale
    "0": "#0c2a1c", "1": "#145c35", "2": "#27a85e",   # phosphor darkest / dark / mid
    "3": "#6cf29b", "4": "#c8ffd9",                   # phosphor light / pale
    "A": "#f0a030", "Y": "#ffd36b", "E": "#9a5a12",   # amber / light / dark
    "r": "#d9342b", "x": "#7a1a14",                   # alarm red / dark red
    "B": "#c9a247", "b": "#7d5f24",                   # brass / dark
    "R": "#1e1e22", "s": "#e0a885", "t": "#b07a5a",   # rubber black / skin / skin shade
    "N": "#22304a", "n": "#34496b", "W": "#f2f4f6",   # navy / navy light / white
}
def rgb(h): h = h.lstrip("#"); return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), 255)
COL = {k: rgb(v) for k, v in PAL.items()}
PALETTE_RGB = {c[:3] for c in COL.values()}
BG = rgb(PAL["M"])
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
    def ring(self, x0, y0, x1, y1, n, k):
        for i in range(n): self.outline(x0 + i, y0 + i, x1 - i, y1 - i, k)
    def bevel(self, x0, y0, x1, y1, n, hi, lo):
        """n-px mitred bevel inside the box: hi on top/left, lo on bottom/right."""
        for i in range(n):
            self.hline(x0 + i, x1 - i, y0 + i, hi); self.vline(x0 + i, y0 + i, y1 - i, hi)
            self.hline(x0 + i, x1 - i, y1 - i, lo); self.vline(x1 - i, y0 + i, y1 - i, lo)
        for i in range(n):   # mitre: top-right and bottom-left corners belong to the shadow side
            self.px(x1 - i, y0 + i, lo); self.px(x0 + i, y1 - i, lo)
    def art(self, x0, y0, rows, mirror=False):
        for dy, row in enumerate(rows):
            if mirror: row = row + row[::-1]
            for dx, ch in enumerate(row):
                if ch not in ". ": self.px(x0 + dx, y0 + dy, ch)
    def save(self, name):
        self.img.save(os.path.join(ASSETS, name))
        return self.img

def auto_outline(cv, k="K", diag=False):
    """Put an outline pixel on every transparent pixel touching a drawn pixel."""
    src = cv.img.copy(); p = src.load()
    nb = [(1, 0), (-1, 0), (0, 1), (0, -1)] + ([(1, 1), (-1, -1), (1, -1), (-1, 1)] if diag else [])
    for y in range(cv.h):
        for x in range(cv.w):
            if p[x, y][3] == 0 and any(0 <= x + dx < cv.w and 0 <= y + dy < cv.h and p[x + dx, y + dy][3]
                                       for dx, dy in nb):
                cv.px(x, y, k)

# ---------------------------------------------------------------- seamless check
def seam_report(img, name):
    """Colour jump across the wrap seam must be no bigger than the biggest interior jump."""
    w, h = img.size
    px = img.load()
    def d(p, q): return sum(abs(p[i] - q[i]) for i in range(3))
    cols = [sum(d(px[x, y], px[x + 1, y]) for y in range(h)) / h for x in range(w - 1)]
    seam_h = sum(d(px[w - 1, y], px[0, y]) for y in range(h)) / h
    rows = [sum(d(px[x, y], px[x, y + 1]) for x in range(w)) / w for y in range(h - 1)]
    seam_v = sum(d(px[x, h - 1], px[x, 0]) for x in range(w)) / w
    # tiling the tile 2x2 and re-cutting a window straddling the seams must match the tile itself
    t = tile2x2(img)
    ok_shift = all(t.getpixel((x + w // 2, y + h // 2)) == img.getpixel(((x + w // 2) % w, (y + h // 2) % h))
                   for x in range(w) for y in range(h))
    ok = seam_h <= max(cols) and seam_v <= max(rows) and ok_shift
    print(f"seam {name}: LR {seam_h:.1f} (interior max {max(cols):.1f}), TB {seam_v:.1f} "
          f"(interior max {max(rows):.1f}), periodic {ok_shift} -> {'OK' if ok else 'SEAM!'}")
    return ok

# ---------------------------------------------------------------- tiles
def rivet(cv, x, y):
    """2x2 steel-highlight rivet with a 1px steel-darkest shadow to the bottom-right."""
    cv.rect(x, y, x + 1, y + 1, "H")
    cv.px(x + 2, y + 1, "d"); cv.px(x + 2, y + 2, "d"); cv.px(x + 1, y + 2, "d")

def wall_tile():
    cv = Cv(48, 48, "D", wrap=True)
    seams = [(11, 38), (35, 14)]           # (horizontal seam row, x of the vertical seam in the band below it)
    for sy, vx in seams:
        cv.hline(0, 47, sy, "K")           # horizontal seam
        cv.hline(0, 47, sy + 1, "M")       # lit lip under it
        cv.vline(vx, sy + 1, sy + 23, "K") # vertical seam, staggered per band
        cv.vline(vx + 1, sy + 2, sy + 23, "M")
    for sy, vx in seams:
        for k in range(5):                 # rivets along the horizontal seams (top and bottom of the plate)
            rx = vx + 3 + 10 * k
            rivet(cv, rx, sy + 3)
            rivet(cv, rx, sy + 19)
        rivet(cv, vx + 3, sy + 11)         # and mid-height either side of the vertical seam
        rivet(cv, vx + 43, sy + 11)
    for (x, y, n) in [(22, 18, 5), (6, 30, 4), (28, 40, 6), (4, 3, 3), (40, 9, 3), (34, 29, 2), (24, 6, 3), (44, 19, 2)]:
        cv.hline(x, x + n - 1, y, "M")     # scuffs
    cv.px(30, 18, "M"); cv.px(9, 31, "M"); cv.px(33, 41, "M"); cv.px(20, 44, "M")
    cv.save("wall-tile.png")
    return cv.img

def floor_tile():
    cv = Cv(48, 48, "D", wrap=True)
    dia = ["..M..", ".MMM.", "MMMMM", ".MMM.", "..M.."]
    for j in range(8):                     # 6px row pitch, 8px column pitch, odd rows shifted by half
        for i in range(6):
            x0 = i * 8 + (4 if j % 2 else 0)
            y0 = j * 6
            cv.art(x0, y0, dia)
            cv.px(x0 + 1, y0 + 1, "H")     # lit top-left
            cv.px(x0 + 3, y0 + 3, "d")     # shadow bottom-right
    cv.save("floor-tile.png")
    return cv.img

# ---------------------------------------------------------------- 9-slices
def brass_rivet3(cv, x, y):
    cv.rect(x, y, x + 2, y + 2, "B")
    cv.px(x + 2, y + 2, "b")

def sign_9slice():
    cv = Cv(36, 36)
    cv.outline(0, 0, 35, 35, "K")
    cv.bevel(1, 1, 34, 34, 2, "H", "d")
    cv.rect(3, 3, 32, 32, "M")
    for (x, y) in [(4, 4), (29, 4), (4, 29), (29, 29)]:
        brass_rivet3(cv, x, y)
    cv.save("sign-9slice.png")
    return cv.img

def panel_9slice():
    cv = Cv(36, 36)
    cv.outline(0, 0, 35, 35, "K")
    cv.rect(1, 1, 34, 34, "M")             # 2px steel-mid frame
    cv.rect(3, 3, 32, 32, "d")
    cv.hline(3, 32, 3, "H"); cv.vline(3, 3, 32, "H")      # inner highlight, top/left
    cv.ring(4, 4, 31, 31, 1, "1")                          # phosphor-dark screen glow all the way round
    cv.save("panel-9slice.png")
    return cv.img

def button_9slice(active=False):
    cv = Cv(24, 24)
    cv.outline(0, 0, 23, 23, "K")
    cv.rect(1, 1, 22, 22, "A")             # 2px amber border
    cv.rect(3, 3, 20, 20, "Y" if active else "d")
    if active:
        cv.hline(3, 20, 3, "E"); cv.vline(3, 3, 20, "E")  # amber-dark inner shadow (pressed in)
    else:
        cv.hline(3, 20, 3, "Y"); cv.vline(3, 3, 20, "Y")  # amber-light highlight inside the border
    cv.save("button-active-9slice.png" if active else "button-9slice.png")
    return cv.img

def input_9slice():
    cv = Cv(24, 24)
    cv.outline(0, 0, 23, 23, "K")
    cv.ring(1, 1, 22, 22, 1, "D")          # steel-dark bezel
    cv.ring(2, 2, 21, 21, 1, "1")          # phosphor-dark ring
    cv.rect(3, 3, 20, 20, "0")             # phosphor-darkest screen
    cv.save("input-9slice.png")
    return cv.img

# ---------------------------------------------------------------- small sprites
def star():
    """Little submarine (keeps the star filename)."""
    cv = Cv(11, 11)
    m = {(5, 1), (6, 1), (5, 2), (5, 3)}                   # periscope
    rows = {4: range(4, 7), 5: range(4, 7), 6: range(2, 9), 7: range(1, 10),
            8: range(1, 10), 9: range(2, 9)}
    for y, xs in rows.items():
        for x in xs: m.add((x, y))
    m |= {(1, 5), (1, 6)}                                  # stern fin
    for (x, y) in m: cv.px(x, y, "P")
    auto_outline(cv)
    for x in range(2, 9): cv.px(x, 9, "H")                 # shaded belly
    cv.px(5, 7, "3")                                       # porthole
    cv.save("star.png")
    return cv.img

def nail():
    cv = Cv(5, 5)
    cv.art(0, 0, [".BBB.", "BBBBB", "BBBBB", "BBBbB", ".BBB."])
    cv.save("nail.png")
    return cv.img

def skull():
    """Small brass anchor (keeps the skull-small filename)."""
    cv = Cv(24, 20)
    m = set()
    cx, cy = 11.5, 3.6
    for y in range(0, 7):
        for x in range(24):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if 1.5 <= d <= 3.3: m.add((x, y))                           # ring
    for y in range(6, 17): m |= {(11, y), (12, y)}                      # shaft
    for x in range(7, 17): m |= {(x, 8), (x, 9)}                        # stock
    for y in range(7, 11): m |= {(6, y), (17, y)}                       # stock end caps
    ax, ay = 11.5, 10.5
    for y in range(13, 19):
        for x in range(24):
            d = ((x - ax) ** 2 + (y - ay) ** 2) ** 0.5
            if 5.9 <= d <= 7.9: m.add((x, y))                           # curved arms
    for (x, y) in [(4, 11), (3, 12), (4, 12), (5, 12), (3, 13), (4, 13)]:   # fluke points
        m.add((x, y)); m.add((23 - x, y))
    for (x, y) in m: cv.px(x, y, "B")
    auto_outline(cv)
    base = cv.img.copy(); p = base.load()
    for y in range(20):                                                 # shadow side: right and bottom edges
        for x in range(24):
            if p[x, y] == COL["B"]:
                r = p[x + 1, y] if x < 23 else (0, 0, 0, 0)
                b_ = p[x, y + 1] if y < 19 else (0, 0, 0, 0)
                if r == COL["K"] or b_ == COL["K"]: cv.px(x, y, "b")
    cv.save("skull-small.png")
    return cv.img

def mug():
    """Enamel mug: white body, navy rim and band, steam."""
    cv = Cv(20, 26)
    cv.rect(0, 6, 13, 25, "K")
    cv.rect(1, 7, 12, 24, "W")
    cv.rect(1, 7, 12, 8, "N")                      # rim
    cv.rect(1, 14, 12, 17, "N")                    # band
    cv.vline(12, 9, 13, "P"); cv.vline(12, 18, 23, "P"); cv.hline(1, 12, 24, "P")   # shade side
    cv.px(12, 24, "P")
    cv.hline(1, 12, 9, "P")                        # shadow under the rim
    cv.art(14, 9, [
        "KKKKK.",
        "WWWWWK",
        "PPPWWK",
        "KKKWWK",
        "..KWPK",
        "..KWPK",
        "..KWPK",
        "..KWPK",
        "..KWPK",
        "..KWPK",
        "KKKWWK",
        "PPPWWK",
        "WWWWWK",
        "KKKKK.",
    ])
    cv.px(7, 1, "4"); cv.px(8, 3, "4"); cv.px(6, 4, "4")   # steam
    cv.save("mug.png")
    return cv.img

def bottle():
    """Headphones on a brass hook (keeps the bottle filename)."""
    cv = Cv(12, 30)
    m = set()
    cx, cy = 5.5, 11.5
    for y in range(6, 13):
        for x in range(12):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if 2.6 <= d <= 4.9 and y <= 11: m.add((x, y))               # headband arch
    for y in range(12, 21): m |= {(1, y), (2, y), (9, y), (10, y)}      # band ends
    for (x, y) in m: cv.px(x, y, "R")
    auto_outline(cv)
    base = cv.img.copy(); p = base.load()
    for y in range(1, 12):                                               # lit top edge of the arch
        for x in range(1, 6):
            if p[x, y] == COL["R"] and p[x, y - 1] == COL["K"]: cv.px(x, y, "L")
    for x0 in (0, 7):                                                    # ear cups
        cv.outline(x0, 21, x0 + 4, 29, "K")
        cv.rect(x0 + 1, 22, x0 + 3, 28, "R")
        cv.ring(x0 + 1, 22, x0 + 3, 28, 1, "H")
        cv.px(x0 + 2, 24, "L"); cv.px(x0 + 2, 25, "L")                   # cushion glint
    cv.art(0, 0, [                                                       # brass hook
        "....KKKK....",
        "...KBBBbK...",
        "...KBKKbK...",
        "...KBKKbK...",
        "....KBbK....",
        "....KBbK....",
        "...KBBBbK...",
    ])
    cv.save("bottle.png")
    return cv.img

# ---------------------------------------------------------------- preview
def nine_slice(img, s, tw, th):
    w, h = img.size
    out = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    def piece(box, size, pos): out.paste(img.crop(box).resize(size, Image.NEAREST), pos)
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
    def new(w, h): return Image.new("RGBA", (w, h), BG)
    W_ = 780
    tiles = new(W_, 470)
    def put(sheet, im, x, y, label=None, z=Z):
        sheet.alpha_composite(im.resize((im.width * z, im.height * z), Image.NEAREST), (x, y))
        if label: ImageDraw.Draw(sheet).text((x, y - 11), label, fill=COL["P"])
    put(tiles, a["wall"], 10, 20, "wall-tile 48x48")
    put(tiles, tile2x2(a["wall"]), 170, 20, "wall 2x2 tiled", z=2)
    put(tiles, a["floor"], 10, 250, "floor-tile 48x48")
    put(tiles, tile2x2(a["floor"]), 170, 250, "floor 2x2 tiled", z=2)
    x = 400
    put(tiles, a["star"], x, 20, "sub (star)"); x += 11 * Z + 24
    put(tiles, a["nail"], x, 20, "rivet"); x += 5 * Z + 24
    put(tiles, a["skull"], x, 20, "anchor"); x += 24 * Z + 24
    put(tiles, a["mug"], x, 20, "mug"); x += 20 * Z + 24
    put(tiles, a["bottle"], x, 20, "phones")
    nine = new(W_, 790)
    names = [("sign", 12), ("panel", 12), ("button", 8), ("button_a", 8), ("input", 8)]
    x = 10
    for n, s in names:
        put(nine, a[n], x, 20, n + " raw"); x += a[n].width * Z + 14
    x, y = 10, 150
    for n, s in names:
        put(nine, nine_slice(a[n], s, 120, 60), x, y, n + " stretched 120x60", z=Z)
        x += 120 * Z + 12
        if x + 120 * Z > W_: x, y = 10, y + 60 * Z + 20
    sheet = new(W_, tiles.height + nine.height)
    sheet.paste(tiles, (0, 0)); sheet.paste(nine, (0, tiles.height))
    sheet.save(os.path.join(HERE, "preview-sonar-chrome.png"))

FILES = ["wall-tile.png", "floor-tile.png", "sign-9slice.png", "panel-9slice.png", "button-9slice.png",
         "button-active-9slice.png", "input-9slice.png", "star.png", "nail.png", "skull-small.png",
         "mug.png", "bottle.png"]

def palette_check(files):
    ok = True
    for f in files:
        im = Image.open(os.path.join(ASSETS, f)).convert("RGBA")
        pix = [im.getpixel((x, y)) for y in range(im.height) for x in range(im.width)]
        bad = {p[:3] for p in pix if p[3] and p[:3] not in PALETTE_RGB}
        alphas = {p[3] for p in pix}
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
    palette_check(FILES)
