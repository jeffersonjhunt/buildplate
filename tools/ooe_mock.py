"""Pixel-exact 320x240 mockups for the OOE falling-block game.

Everything is drawn on the OO-1's real logical grid: a 320x240 screen of 8x8 cells
(layer 1, 4-bit tiles), a 320x240 background of 16x16 8-bit tiles (layer 0), and
8x8 sprites. Colours are 12-bit (4 bits a channel) as the palette holds them.
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "out")
W, H = 320, 240


def c12(hexstr):
    """'#rgb' 12-bit colour -> 24-bit tuple."""
    h = hexstr.lstrip("#")
    return tuple(int(ch, 16) * 17 for ch in h)


def q12(rgb):
    return tuple(min(255, max(0, int(round(v / 17.0)) * 17)) for v in rgb)


# ---------------------------------------------------------------- brand palette (group 0)
INK = c12("#000")       # 0 transparent on layer 1; shown here as black
GROUND = c12("#111")    # panel fill (near the site's #0b0a09)
GROUND2 = c12("#211")   # playfield cell
GRID = c12("#322")      # playfield grid dot
LINE = c12("#544")      # frames (site --line #2c2924 lifted for the CRT)
DIM = c12("#876")       # labels, muted (site --dim/--muted)
BONE = c12("#edd")      # text (site --text #e8e4e0)
ORANGE = c12("#c50")    # accent (site --accent #cc5500)
AMBER = c12("#fb0")     # highlight (site --amber #ffb000)
RED = c12("#f42")       # alert / stamp (site --red #ff4a2a)
WHITE = c12("#fff")

# pieces: (light, base, dark), each in its own 16-colour group
PIECES = {
    "I": ("#7ff", "#2cd", "#078"),
    "O": ("#fe6", "#fb0", "#a60"),
    "T": ("#d8f", "#a4e", "#517"),
    "S": ("#9f8", "#4c4", "#160"),
    "Z": ("#f97", "#f42", "#912"),
    "J": ("#9bf", "#46f", "#128"),
    "L": ("#f94", "#c50", "#720"),
}
PIECES = {k: tuple(c12(x) for x in v) for k, v in PIECES.items()}

SHAPES = {  # spawn orientation, (x, y) with y down
    "I": [(0, 0), (1, 0), (2, 0), (3, 0)],
    "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
    "T": [(1, 0), (0, 1), (1, 1), (2, 1)],
    "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
    "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
    "J": [(0, 0), (0, 1), (1, 1), (2, 1)],
    "L": [(2, 0), (0, 1), (1, 1), (2, 1)],
}

# ---------------------------------------------------------------- 5x7 font in an 8x8 cell
# Monoline, squared with cut corners, after the OOE wordmark.
GLYPHS = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#..##", "#...#", "#...#", ".####"],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["..#..", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "J": ["....#", "....#", "....#", "....#", "....#", "#...#", ".###."],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "Q": [".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "X": ["#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    "Z": ["#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"],
    "0": [".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."],
    "1": ["..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
    "3": ["####.", "....#", "....#", ".###.", "....#", "....#", "####."],
    "4": ["#...#", "#...#", "#...#", "#####", "....#", "....#", "....#"],
    "5": ["#####", "#....", "#....", "####.", "....#", "....#", "####."],
    "6": [".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."],
    "7": ["#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."],
    "8": [".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."],
    "9": [".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."],
    ">": ["#....", ".#...", "..#..", "...#.", "..#..", ".#...", "#...."],
    "<": ["....#", "...#.", "..#..", ".#...", "..#..", "...#.", "....#"],
    "-": [".....", ".....", ".....", ".###.", ".....", ".....", "....."],
    ":": [".....", "..#..", ".....", ".....", ".....", "..#..", "....."],
    ".": [".....", ".....", ".....", ".....", ".....", ".....", "..#.."],
    "/": ["....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."],
    "!": ["..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."],
    "=": [".....", ".....", "#####", ".....", "#####", ".....", "....."],
    "'": ["..#..", "..#..", ".....", ".....", ".....", ".....", "....."],
    "(": ["...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."],
    ")": [".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."],
    "^": ["..#..", ".#.#.", "#...#", ".....", ".....", ".....", "....."],
    "v": [".....", ".....", ".....", ".....", "#...#", ".#.#.", "..#.."],
    " ": ["....."] * 7,
}


def text(img, x, y, s, col, scale=1, shadow=None, spacing=8):
    """Draw text on the 8x8 cell grid (x, y in pixels)."""
    px = img.load()
    for i, ch in enumerate(s):
        g = GLYPHS.get(ch, GLYPHS[" "])
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit != "#":
                    continue
                for sy in range(scale):
                    for sx in range(scale):
                        X = x + i * spacing * scale + (gx + 1) * scale + sx
                        Y = y + gy * scale + sy
                        if shadow and 0 <= X + scale < W and 0 <= Y + scale < H:
                            px[X + scale, Y + scale] = shadow
                        if 0 <= X < W and 0 <= Y < H:
                            px[X, Y] = col
    if shadow:  # redraw tops over shadows
        text(img, x, y, s, col, scale, None, spacing)


def text_w(s, scale=1, spacing=8):
    return len(s) * spacing * scale


def cell_text(img, cx, cy, s, col):
    text(img, cx * 8, cy * 8, s, col)


# ---------------------------------------------------------------- OOE mark
def ooe_mark(img, x, y, h, col):
    """The OOE icon: two rounded-square Os and the three bars, h pixels tall."""
    d = ImageDraw.Draw(img)
    stroke = max(1, round(h / 7))
    ow = round(h * 0.86)
    gap = max(2, round(h * 0.18))
    r = max(1, round(h * 0.28))
    for k in range(2):
        x0 = x + k * (ow + gap)
        d.rounded_rectangle([x0, y, x0 + ow - 1, y + h - 1], radius=r, outline=col, width=stroke)
    bx = x + 2 * (ow + gap)
    bw = round(h * 0.86)
    for k, by in enumerate((y, y + (h - stroke) // 2, y + h - stroke)):
        d.rounded_rectangle([bx, by, bx + bw - 1, by + stroke - 1], radius=stroke // 2, fill=col)
    return bx + bw - x


# ---------------------------------------------------------------- tiles
def block(img, x, y, kind, ghost=False):
    lt, base, dk = PIECES[kind]
    px = img.load()
    for j in range(8):
        for i in range(8):
            if ghost:
                edge = i in (0, 7) or j in (0, 7)
                if edge and (i + j) % 2 == 0:
                    px[x + i, y + j] = base
                continue
            if i == 7 or j == 7:
                c = dk
            elif i == 0 or j == 0:
                c = lt
            else:
                c = base
            if (i, j) in ((2, 2),):
                c = WHITE
            if (i, j) in ((3, 2), (2, 3)):
                c = lt
            px[x + i, y + j] = c


def field_cell(img, x, y, top=False):
    px = img.load()
    for j in range(8):
        for i in range(8):
            px[x + i, y + j] = GROUND2 if not top else GROUND
    px[x + 7, y + 7] = GRID


def frame(img, cx0, cy0, cx1, cy1, col=LINE, fill=GROUND, label=None, labcol=ORANGE, accent=True):
    """A rounded 1-px panel on cells (inclusive). Drawn from 8x8 frame tiles."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = cx0 * 8 + 3, cy0 * 8 + 3, cx1 * 8 + 4, cy1 * 8 + 4
    d.rectangle([cx0 * 8, cy0 * 8, cx1 * 8 + 7, cy1 * 8 + 7], fill=fill)
    d.rounded_rectangle([x0, y0, x1, y1], radius=3, outline=col, width=1)
    if accent:  # orange corner ticks, after the site's accent rule
        for (ax, ay, dx, dy) in ((x0, y0, 1, 1), (x1, y0, -1, 1), (x0, y1, 1, -1), (x1, y1, -1, -1)):
            pass
    if label:
        lx = cx0 * 8 + 8
        d.rectangle([lx - 1, y0 - 3, lx + text_w(label) + 1, y0 + 4], fill=fill)
        text(img, lx, y0 - 3, label, labcol)


# ---------------------------------------------------------------- dithering helpers
BAYER4 = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def dith(x, y):
    return (BAYER4[y & 3][x & 3] + 0.5) / 16.0


def lerp(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


def ramp_pick(ramp, v, x, y):
    """Pick from a list of 12-bit colours by v in 0..1 with ordered dither."""
    n = len(ramp) - 1
    f = max(0.0, min(1.0, v)) * n
    i = int(f)
    if i >= n:
        return ramp[n]
    return ramp[i + 1] if (f - i) > dith(x, y) else ramp[i]


def hexes(*xs):
    return [c12(x) for x in xs]


def stars(img, rng, n, cols, avoid=None):
    px = img.load()
    for _ in range(n):
        x, y = rng.randrange(W), rng.randrange(H)
        if avoid and avoid(x, y):
            continue
        c = rng.choice(cols)
        px[x, y] = c
        if rng.random() < 0.06 and 0 < x < W - 1 and 0 < y < H - 1:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                px[x + dx, y + dy] = cols[0]


def noise2(x, y, seed, oct=4):
    """Cheap value noise."""
    def h(ix, iy):
        n = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
        n = (n ^ (n >> 13)) * 1274126177 & 0xFFFFFFFF
        return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0

    def vn(x, y):
        ix, iy = int(math.floor(x)), int(math.floor(y))
        fx, fy = x - ix, y - iy
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a, b = h(ix, iy), h(ix + 1, iy)
        c, d = h(ix, iy + 1), h(ix + 1, iy + 1)
        return (a + (b - a) * fx) + ((c + (d - c) * fx) - (a + (b - a) * fx)) * fy

    s, amp, tot = 0.0, 1.0, 0.0
    for o in range(oct):
        s += vn(x * (2 ** o), y * (2 ** o)) * amp
        tot += amp
        amp *= 0.5
    return s / tot


# ---------------------------------------------------------------- backgrounds (layer 0)
def bg_gas_giant(seed=1):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H), c12("#001"))
    px = img.load()
    sky = hexes("#001", "#002", "#012", "#113")
    for y in range(H):
        for x in range(W):
            px[x, y] = ramp_pick(sky, (y / H) * 0.9 + noise2(x / 60, y / 60, seed) * 0.3, x, y)
    stars(img, rng, 260, hexes("#99b", "#ccd", "#fff", "#668"))
    cx, cy, r = 236, 150, 96
    bands = hexes("#310", "#520", "#831", "#a52", "#c74", "#da7", "#eb8")
    for y in range(max(0, cy - r), min(H, cy + r)):
        for x in range(max(0, cx - r), min(W, cx + r)):
            dx, dy = (x - cx) / r, (y - cy) / r
            d2 = dx * dx + dy * dy
            if d2 > 1:
                continue
            nz = math.sqrt(1 - d2)
            light = max(0.0, (-dx * 0.75 - dy * 0.35 + nz * 0.55))
            band = 0.5 + 0.5 * math.sin(dy * 13 + 3 * noise2(x / 30, y / 9, seed + 3))
            v = light * (0.55 + 0.45 * band)
            px[x, y] = ramp_pick(bands, v, x, y)
    # ring
    ring = hexes("#653", "#975", "#cb8")
    for y in range(H):
        for x in range(W):
            dx, dy = (x - cx), (y - cy) * 3.2
            rr = math.sqrt(dx * dx + dy * dy)
            if 118 < rr < 160:
                behind = (y < cy) and ((x - cx) ** 2 + (y - cy) ** 2 < r * r)
                if behind:
                    continue
                gapband = 134 < rr < 138
                if gapband:
                    continue
                v = 0.3 + 0.7 * (0.5 + 0.5 * math.sin(rr * 0.9))
                if dith(x, y) < 0.8:
                    px[x, y] = ramp_pick(ring, v * (0.5 if x > cx + 40 else 1.0), x, y)
    # moon
    mx, my, mr = 70, 46, 12
    moon = hexes("#223", "#556", "#99a", "#ccc")
    for y in range(my - mr, my + mr):
        for x in range(mx - mr, mx + mr):
            dx, dy = (x - mx) / mr, (y - my) / mr
            if dx * dx + dy * dy <= 1:
                v = max(0, -dx * 0.6 - dy * 0.4 + math.sqrt(max(0, 1 - dx * dx - dy * dy)) * 0.6)
                px[x, y] = ramp_pick(moon, v * (0.85 + 0.15 * noise2(x / 4, y / 4, 9)), x, y)
    return img


def bg_grid_horizon(seed=2):
    """The mid-80s one: striped sun, wire mountains, perspective grid, in OOE oranges."""
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H), c12("#000"))
    px = img.load()
    hz = 150
    sky = hexes("#000", "#101", "#202", "#312", "#512", "#731")
    for y in range(hz):
        for x in range(W):
            px[x, y] = ramp_pick(sky, (y / hz) ** 1.6, x, y)
    stars(img, rng, 120, hexes("#a87", "#dcb", "#fff"), avoid=lambda x, y: y > hz - 40)
    # sun
    sx, sy, sr = 160, 108, 52
    sun = hexes("#c30", "#e50", "#f80", "#fb0", "#fe6")
    for y in range(sy - sr, hz):
        for x in range(sx - sr, sx + sr):
            dx, dy = x - sx, y - sy
            if dx * dx + dy * dy > sr * sr:
                continue
            t = (y - (sy - sr)) / (2 * sr)
            stripe = y > sy - 6 and ((y - sy) // 2) % max(2, 8 - (y - sy) // 6) == 0
            if stripe:
                continue
            px[x, y] = ramp_pick(list(reversed(sun)), t * 1.1, x, y)
    # mountains
    mcol, medge = c12("#100"), c12("#c50")
    for x in range(W):
        hgt = 18 + 22 * abs(math.sin(x * 0.021 + 1.3)) * (0.6 + 0.4 * noise2(x / 23, 0, seed))
        hgt *= 1.0 if abs(x - 160) > 60 else 0.55
        top = int(hz - hgt)
        for y in range(top, hz):
            px[x, y] = mcol
        px[x, top] = medge
    # ground + grid
    gnd = hexes("#000", "#100", "#201")
    for y in range(hz, H):
        for x in range(W):
            px[x, y] = ramp_pick(gnd, (y - hz) / (H - hz), x, y)
    gcol, gfar = c12("#f60"), c12("#830")
    for k in range(1, 40):
        z = k * k * 0.35
        y = hz + int(z)
        if y >= H:
            break
        c = gfar if y < hz + 12 else gcol
        for x in range(W):
            if y < hz + 6 and (x + y) % 2:
                continue
            px[x, y] = c
    for k in range(-20, 21):
        for y in range(hz, H):
            t = (y - hz) / (H - hz)
            x = int(160 + k * (6 + t * 70))
            if 0 <= x < W:
                px[x, y] = gfar if y < hz + 12 else gcol
    return img


def bg_station(seed=3):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    neb = hexes("#000", "#011", "#022", "#123", "#235", "#448", "#86a")
    for y in range(H):
        for x in range(W):
            n = noise2(x / 70, y / 55, seed, 5)
            n2 = noise2(x / 25, y / 25, seed + 7, 3)
            v = max(0, (n - 0.42) * 2.4) * (0.7 + 0.5 * n2)
            px[x, y] = ramp_pick(neb, v, x, y)
    stars(img, rng, 220, hexes("#8ab", "#cde", "#fff"))
    # ring station, seen at an angle
    cx, cy = 92, 128
    hull, lit, win = c12("#334"), c12("#778"), c12("#fb0")
    for a in range(0, 3600):
        t = a / 3600 * 2 * math.pi
        for rr in range(62, 70):
            x = int(cx + rr * math.cos(t))
            y = int(cy + rr * 0.42 * math.sin(t))
            if 0 <= x < W and 0 <= y < H:
                front = math.sin(t) > 0
                c = lit if (rr in (62, 63) and front) else hull
                if rr == 66 and (a // 45) % 3 == 0 and front:
                    c = win
                px[x, y] = c
    d = ImageDraw.Draw(img)
    for ang in (0, 60, 120):
        t = math.radians(ang)
        d.line([cx, cy, cx + 62 * math.cos(t), cy + 26 * math.sin(t)], fill=hull)
        d.line([cx, cy, cx - 62 * math.cos(t), cy - 26 * math.sin(t)], fill=hull)
    d.ellipse([cx - 9, cy - 6, cx + 9, cy + 6], fill=c12("#556"), outline=lit)
    for i in range(4):
        px[cx - 4 + i * 3, cy] = win
    # ship with engine trail
    sx, sy = 262, 54
    d.polygon([(sx, sy), (sx - 22, sy + 5), (sx - 22, sy - 5)], fill=c12("#99a"))
    d.line([sx - 22, sy - 5, sx, sy], fill=c12("#ccd"))
    for i in range(1, 60):
        if dith(sx - 22 - i, sy) < 1 - i / 60:
            px[sx - 22 - i, sy] = c12("#2cd") if i < 20 else c12("#078")
    return img


def bg_moonbase(seed=4):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = c12("#000")
    stars(img, rng, 200, hexes("#778", "#bbc", "#fff"))
    # earthrise
    ex, ey, er = 214, 70, 34
    sea, land, cloud = hexes("#013", "#025", "#148"), hexes("#141", "#363"), c12("#ccd")
    for y in range(ey - er, ey + er):
        for x in range(ex - er, ex + er):
            dx, dy = (x - ex) / er, (y - ey) / er
            d2 = dx * dx + dy * dy
            if d2 > 1:
                continue
            light = max(0, dx * 0.7 - dy * 0.3 + math.sqrt(1 - d2) * 0.5)
            if light < 0.12:
                continue
            n = noise2(x / 14, y / 14, seed)
            cl = noise2(x / 8, y / 4, seed + 5)
            if cl > 0.62 and light > 0.3:
                px[x, y] = cloud
            elif n > 0.55:
                px[x, y] = ramp_pick(land, light, x, y)
            else:
                px[x, y] = ramp_pick(sea, light, x, y)
    # ground
    hz = 168
    reg = hexes("#111", "#222", "#333", "#444", "#665", "#887")
    for x in range(W):
        top = int(hz - 10 * noise2(x / 40, 0, seed) - 6 * noise2(x / 9, 3, seed))
        for y in range(top, H):
            depth = (y - top) / (H - top + 1)
            n = noise2(x / 18, y / 7, seed + 2, 4)
            v = 0.25 + 0.5 * n - 0.25 * depth
            px[x, y] = ramp_pick(reg, v, x, y)
        px[x, top] = reg[-1]
    # craters
    for _ in range(9):
        cx, cy = rng.randrange(W), rng.randrange(hz + 8, H)
        rx = rng.randrange(6, 22)
        for y in range(cy - rx // 3, cy + rx // 3 + 1):
            for x in range(cx - rx, cx + rx):
                if 0 <= x < W and 0 <= y < H:
                    dx, dy = (x - cx) / rx, (y - cy) / (rx / 3)
                    d2 = dx * dx + dy * dy
                    if d2 <= 1:
                        px[x, y] = reg[1] if dy < 0.2 else reg[0]
                    elif d2 <= 1.3 and dy > 0:
                        px[x, y] = reg[4]
    # domes with lights
    d = ImageDraw.Draw(img)
    for bx, br in ((40, 18), (74, 11), (300, 14)):
        d.pieslice([bx - br, hz - br - 4, bx + br, hz + br - 4], 180, 360, fill=c12("#556"), outline=c12("#99a"))
        for i in range(-br + 4, br - 3, 4):
            px[bx + i, hz - 7] = c12("#fb0")
    d.line([56, hz - 6, 64, hz - 6], fill=c12("#99a"))
    # antenna mast + red beacon
    d.line([96, hz - 2, 96, hz - 30], fill=c12("#99a"))
    d.line([90, hz - 26, 102, hz - 26], fill=c12("#99a"))
    px[96, hz - 31] = c12("#f42")
    return img


def bg_derelict(seed=5):
    """Asteroid field with a derelict freighter: browns + amber running lights."""
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    sky = hexes("#000", "#100", "#110", "#211")
    for y in range(H):
        for x in range(W):
            px[x, y] = ramp_pick(sky, noise2(x / 80, y / 80, seed, 4) * 0.9, x, y)
    stars(img, rng, 180, hexes("#987", "#cba", "#fff"))
    rock = hexes("#110", "#221", "#332", "#543", "#765", "#987")
    for _ in range(26):
        ax, ay = rng.randrange(-10, W + 10), rng.randrange(-10, H + 10)
        ar = rng.choice([3, 4, 5, 6, 8, 11, 16, 22])
        sd = rng.randrange(1000)
        for y in range(ay - ar - 3, ay + ar + 3):
            for x in range(ax - ar - 3, ax + ar + 3):
                if not (0 <= x < W and 0 <= y < H):
                    continue
                dx, dy = (x - ax) / ar, (y - ay) / ar
                a = math.atan2(dy, dx)
                rr = 1 + 0.22 * (noise2(math.cos(a) * 2 + 5, math.sin(a) * 2 + 5, sd, 2) - 0.5) * 2
                d2 = math.sqrt(dx * dx + dy * dy)
                if d2 > rr:
                    continue
                nz = math.sqrt(max(0, 1 - (d2 / rr) ** 2))
                v = max(0, -dx * 0.6 - dy * 0.5 + nz * 0.5) * (0.75 + 0.35 * noise2(x / 3, y / 3, sd, 2))
                px[x, y] = ramp_pick(rock, v, x, y)
    # freighter
    d = ImageDraw.Draw(img)
    hx, hy = 190, 186
    hullc, dark, trim = c12("#443"), c12("#221"), c12("#776")
    d.polygon([(hx - 120, hy - 8), (hx + 70, hy - 14), (hx + 110, hy - 4), (hx + 70, hy + 10), (hx - 120, hy + 12)], fill=hullc)
    d.line([hx - 120, hy - 8, hx + 70, hy - 14], fill=trim)
    for i in range(-110, 70, 14):
        d.rectangle([hx + i, hy - 6, hx + i + 9, hy + 5], outline=dark)
    d.rectangle([hx - 60, hy - 24, hx - 30, hy - 9], fill=hullc, outline=trim)
    for i in range(-104, 66, 9):
        if rng.random() < 0.5:
            px[hx + i, hy + 8] = c12("#fb0")
    px[hx + 108, hy - 4] = c12("#f42")
    # gash
    for i in range(30):
        x, y = hx + 10 + i, hy - 4 + int(3 * math.sin(i * 0.7))
        px[x, y] = c12("#000")
        if rng.random() < 0.3:
            px[x, y + 1] = c12("#c50")
    return img


BGS = {
    "gas-giant": bg_gas_giant,
    "grid-horizon": bg_grid_horizon,
    "orbital-station": bg_station,
    "moonbase": bg_moonbase,
    "derelict": bg_derelict,
}


def quantize_bg(img, ncol=96):
    """12-bit colour, at most ncol colours: the background's palette entries 128..255."""
    q = img.point(lambda v: int(round(v / 17.0)) * 17)
    p = q.quantize(colors=ncol, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    out = p.convert("RGB").point(lambda v: int(round(v / 17.0)) * 17)
    return out


def dim_for_play(img, factor=0.8):
    return img.point(lambda v: int(round(v * factor / 17.0)) * 17)


def tile_stats(img, size=16):
    tiles = set()
    for ty in range(0, H, size):
        for tx in range(0, W, size):
            tiles.add(img.crop((tx, ty, tx + size, ty + size)).tobytes())
    return len(tiles), len(set(img.get_flattened_data()))


# ---------------------------------------------------------------- screens
NAME = "INFILL"  # working title; see the names board


def header(img, name=NAME, hi="00184200"):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, 15], fill=GROUND)
    d.line([0, 15, W - 1, 15], fill=LINE)
    w = ooe_mark(img, 8, 4, 8, BONE)
    text(img, 8 + w + 4, 4, name, BONE)
    text(img, W - 8 - text_w("HI " + hi), 4, "HI", DIM)
    text(img, W - 8 - text_w(hi), 4, hi, AMBER)


def footer(img, s, col=DIM):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 224, W - 1, H - 1], fill=GROUND)
    d.line([0, 224, W - 1, 224], fill=LINE)
    text(img, (W - text_w(s)) // 2, 228, s, col)


def draw_piece_cells(img, ox, oy, kind, ghost=False):
    for (x, y) in SHAPES[kind]:
        block(img, ox + x * 8, oy + y * 8, kind, ghost)


def preview(img, cx, cy, kind):
    """A piece in a 4x2-cell preview slot, centred."""
    w = max(x for x, _ in SHAPES[kind]) + 1
    h = max(y for _, y in SHAPES[kind]) + 1
    ox = cx * 8 + (32 - w * 8) // 2
    oy = cy * 8 + (16 - h * 8) // 2
    draw_piece_cells(img, ox, oy, kind)


BOARD = [  # 20 rows top->bottom, 10 cols; '.' empty
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "..........",
    "......O O.".replace(" ", "O"),
    "......OO..",
    "L.....JJJ.",
    "LZZ...SSJ.",
    "LLZZ.SS.TT",
    "IIII.OOTTT",
    "JZZL.OOSST",
    "JJZZLLLSS.",
    "JTTTLOOIII",
]
BOARD = [r if len(r) == 10 else r[:10] for r in BOARD]
BOARD[11] = ".........."  # tidy
BOARD[12] = ".........."

PF_X, PF_Y = 15, 6  # playfield's top-left cell; 10x20


def playfield(img, board=BOARD, active=None, ghost=True, flash_rows=()):
    frame(img, PF_X - 1, PF_Y - 2, PF_X + 10, PF_Y + 20, fill=GROUND, accent=False)
    for r in range(20):
        for c in range(10):
            x, y = (PF_X + c) * 8, (PF_Y + r) * 8
            ch = board[r][c]
            if r in flash_rows:
                ImageDraw.Draw(img).rectangle([x, y, x + 7, y + 7], fill=WHITE)
            elif ch == ".":
                field_cell(img, x, y)
            else:
                block(img, x, y, ch)
    # the sliver of the hidden rows
    for c in range(10):
        field_cell(img, (PF_X + c) * 8, (PF_Y - 1) * 8, top=True)
    if active:
        kind, col, row, land = active
        if ghost:
            draw_piece_cells(img, (PF_X + col) * 8, (PF_Y + land) * 8, kind, ghost=True)
        draw_piece_cells(img, (PF_X + col) * 8, (PF_Y + row) * 8, kind)


def left_panel(img, hold="T", score="00041250", job="07", layers="063", held_used=False, action=None):
    frame(img, 2, 5, 12, 9, label="HOLD")
    if hold:
        preview(img, 5, 6, hold)
        if held_used:  # dim it
            for y in range(48, 72):
                for x in range(24, 96):
                    if (x + y) % 2 == 0:
                        img.putpixel((x, y), GROUND)
    frame(img, 2, 11, 12, 22, label="SHIFT")
    text(img, 24, 104, "OUTPUT", DIM)
    text(img, 24, 114, score, BONE)
    text(img, 24, 132, "JOB", DIM)
    text(img, 24, 142, job, AMBER)
    text(img, 24, 160, "LAYERS", DIM)
    text(img, 24, 170, layers, BONE)
    if action:
        frame(img, 2, 24, 12, 26)
        for i, (s, col) in enumerate(action):
            text(img, 20 + (88 - text_w(s)) // 2 - 4, 197 + i * 10, s, col)


def right_panel(img, nxt=("I", "L", "S", "O", "J")):
    frame(img, 27, 5, 37, 21, label="NEXT")
    for i, k in enumerate(nxt):
        preview(img, 30, 6 + i * 3, k)


def compose(bg, dim=True):
    img = (dim_for_play(bg) if dim else bg).copy()
    return img


def stamp(img, x, y, s, col=RED, angle=-4):
    """A rubber-stamp imprint, as the boot splash's VINTAGE FAST."""
    w = text_w(s) + 8
    st = Image.new("RGBA", (w + 6, 20), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rectangle([1, 1, w + 3, 17], outline=col + (255,))
    t = Image.new("RGB", (w + 6, 20), (0, 0, 0))
    text(t, 4, 6, s, col)
    tm = t.load()
    sp = st.load()
    rng = random.Random(7)
    for yy in range(20):
        for xx in range(w + 6):
            if tm[xx, yy] != (0, 0, 0):
                sp[xx, yy] = col + (255,)
            if sp[xx, yy][3] and rng.random() < 0.12:  # thin ink
                sp[xx, yy] = (0, 0, 0, 0)
    st = st.rotate(angle, resample=Image.NEAREST, expand=True)
    img.paste(st, (x, y), st)


def scr_title(bg, name=NAME, tag="LAYER FAST"):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    # title plate
    d.rectangle([40, 22, 279, 124], fill=GROUND)
    d.rounded_rectangle([43, 25, 276, 121], radius=4, outline=LINE)
    mw = ooe_mark(Image.new("RGB", (1, 1)), 0, 0, 30, BONE)
    ooe_mark(img, (W - mw) // 2, 34, 30, BONE)
    text(img, (W - text_w("DIGITAL MANUFACTURING")) // 2, 70, "DIGITAL MANUFACTURING", DIM)
    text(img, (W - text_w(name, 2)) // 2, 84, name, AMBER, scale=2, shadow=ORANGE)
    stamp(img, 168, 100, tag)
    # menu
    d.rectangle([88, 160, 231, 214], fill=GROUND)
    d.rounded_rectangle([91, 163, 228, 211], radius=3, outline=LINE)
    items = [("START JOB", True), ("JOB 01", False), ("SETTINGS", False), ("QUIT", False)]
    for i, (s, sel) in enumerate(items):
        y = 168 + i * 10
        if sel:
            text(img, 100, y, ">", AMBER)
            text(img, 112, y, s, BONE)
        else:
            text(img, 112, y, s, DIM)
    text(img, 112 + text_w("JOB "), 178, "01", AMBER)
    text(img, 112 + text_w("JOB 01 "), 178, "<>", LINE)
    footer(img, "HI SHIFT 00184200   (C) 2026 OOE")
    return img


def scr_play(bg, active=("T", 4, 3, 10), action=None, flash_rows=(), hold_used=False):
    img = compose(bg)
    header(img)
    playfield(img, active=active, flash_rows=flash_rows)
    left_panel(img, action=action, held_used=hold_used)
    right_panel(img)
    footer(img, "ESC PAUSE   C HOLD   SPACE DROP")
    return img


def scr_pause(bg):
    img = compose(bg)
    header(img)
    frame(img, PF_X - 1, PF_Y - 2, PF_X + 10, PF_Y + 20, fill=GROUND, accent=False)
    for r in range(-1, 20):
        for c in range(10):
            field_cell(img, (PF_X + c) * 8, (PF_Y + r) * 8, top=(r < 0))
    text(img, (W - text_w("LINE HOLD")) // 2, 80, "LINE HOLD", AMBER)
    items = [("RESUME", True), ("RESTART", False), ("SETTINGS", False), ("QUIT", False)]
    for i, (s, sel) in enumerate(items):
        y = 104 + i * 12
        x = PF_X * 8 + 12
        text(img, x, y, s, BONE if sel else DIM)
        if sel:
            text(img, x - 10, y, ">", AMBER)
    left_panel(img, hold=None)
    right_panel(img, nxt=())
    footer(img, "ESC RESUME   Q QUIT TO A>")
    return img


GAMEOVER_BOARD = [
    "..JJ......",
    "..J.ZZ....",
    "..JIIIIL..",
    "TTTSSZLL..",
    ".TSSLZZL.O",
    "IIIILLLLOO",
] + [
    "".join(random.Random(i).choice("IOTSZJL") if random.Random(i * 7 + c).random() < 0.82 else "." for c in range(10))
    for i in range(14)
]


def scr_gameover(bg):
    img = compose(bg, dim=True)
    header(img)
    gb = ["".join("." if ch == "." else ch for ch in row) for row in GAMEOVER_BOARD]
    playfield(img, board=gb, active=None)
    # grey the stack
    for y in range(PF_Y * 8, (PF_Y + 20) * 8):
        for x in range(PF_X * 8, (PF_X + 10) * 8):
            p = img.getpixel((x, y))
            if p not in (GROUND2, GRID):
                g = q12(((p[0] + p[1] + p[2]) // 3,) * 3)
                img.putpixel((x, y), q12((g[0] // 2, g[1] // 2, g[2] // 2)))
    left_panel(img, hold="J", score="00184200", job="12", layers="117")
    right_panel(img)
    d = ImageDraw.Draw(img)
    d.rectangle([72, 76, 247, 172], fill=GROUND)
    d.rounded_rectangle([75, 79, 244, 169], radius=3, outline=RED)
    text(img, (W - text_w("LINE STOP")) // 2, 88, "LINE STOP", RED)
    rows = [("OUTPUT", "00184200", AMBER), ("JOB", "12", BONE), ("LAYERS", "117", BONE)]
    for i, (k, v, col) in enumerate(rows):
        text(img, 88, 106 + i * 12, k, DIM)
        text(img, 232 - text_w(v), 106 + i * 12, v, col)
    stamp(img, 104, 144, "NEW HI SHIFT", col=RED, angle=3)
    footer(img, "R RESTART   Q QUIT TO A>")
    return img


def scr_settings(bg):
    img = compose(bg)
    header(img)
    d = ImageDraw.Draw(img)
    frame(img, 5, 3, 34, 26, label="SETTINGS")
    rows = [
        ("DAS", "10 FR", "<>"),
        ("ARR", "02 FR", "<>"),
        ("GHOST", "ON", "<>"),
        ("MUSIC", "ON", "<>"),
        ("MUSIC VOL", "########", ""),
        ("EFFECTS", "ON", "<>"),
        ("BACKDROPS", "RANDOM", "<>"),
        ("KEYS", "REMAP", ">"),
    ]
    for i, (k, v, arrows) in enumerate(rows):
        y = 44 + i * 16
        sel = i == 0
        if sel:
            d.rectangle([56, y - 3, 263, y + 9], fill=c12("#311"))
            text(img, 60, y, ">", AMBER)
        text(img, 72, y, k, BONE if sel else DIM)
        if v.startswith("#"):
            for j in range(10):
                col = AMBER if j < 8 else LINE
                d.rectangle([176 + j * 8, y, 181 + j * 8, y + 6], fill=col)
        else:
            text(img, 176, y, v, AMBER if sel else BONE)
        if arrows:
            text(img, 248, y, arrows[-1], LINE)
    footer(img, "^v SELECT  <> CHANGE  ESC BACK")
    return img


def scr_backdrops(bgs):
    """Contact sheet: each backdrop as it looks behind play (dimmed), 2x2 + 1."""
    sheet = Image.new("RGB", (W * 3 + 16, H * 2 + 8), (0, 0, 0))
    for i, (k, b) in enumerate(bgs.items()):
        img = scr_play(b, active=("T", 4, 3, 10))
        sheet.paste(img, ((i % 3) * (W + 8), (i // 3) * (H + 8)))
    return sheet


NAMES = [
    ("INFILL", "LAYER FAST", "3D printing's fill between walls: you fill the gaps"),
    ("QUADFAB", "FOUR-CELL FAB", "four-cell parts, fabricated"),
    ("TOOLPATH", "CUT FAST", "the route a machine takes; you plan each drop"),
    ("BUILD PLATE", "STACK FAST", "where every print starts and stacks"),
    ("ZERO DEFECT", "QC FAST", "a full line ships; a gap is a defect"),
    ("OOEBLOX", "VINTAGE FAST", "the plain one, OOE inside the name"),
]


def names_board():
    """Each candidate as its title plate."""
    tile_w, tile_h = 300, 96
    sheet = Image.new("RGB", (tile_w * 2 + 8, tile_h * 3 + 16), (0, 0, 0))
    globals_W = W
    for i, (name, tag, _) in enumerate(NAMES):
        t = Image.new("RGB", (W, H), GROUND)
        mw = ooe_mark(Image.new("RGB", (1, 1)), 0, 0, 16, BONE)
        ooe_mark(t, (W - mw) // 2, 66, 16, BONE)
        text(t, (W - text_w("DIGITAL MANUFACTURING")) // 2, 86, "DIGITAL MANUFACTURING", DIM)
        text(t, (W - text_w(name, 2)) // 2, 100, name, AMBER, scale=2, shadow=ORANGE)
        stamp(t, 170, 118, tag)
        crop = t.crop(((W - tile_w) // 2, 60, (W + tile_w) // 2, 60 + tile_h))
        sheet.paste(crop, ((i % 2) * (tile_w + 8), (i // 2) * (tile_h + 8)))
    return sheet


def up(img, k=2):
    return img.resize((img.width * k, img.height * k), Image.NEAREST)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    bgs = {k: quantize_bg(f()) for k, f in BGS.items()}
    for k, b in bgs.items():
        b.save(OUT / f"bg-{k}.png")
        up(b).save(OUT / f"bg-{k}@2x.png")
        nt, nc = tile_stats(b)
        print(f"bg {k}: {nt} distinct 16x16 tiles of 300, {nc} colours")
    main_bg = bgs["gas-giant"]
    screens = {
        "title": scr_title(bgs["grid-horizon"]),
        "play": scr_play(main_bg, action=[("T-SPIN", AMBER), ("DOUBLE", BONE)]),
        "play-clear": scr_play(bgs["orbital-station"], active=("I", 0, 0, 0), flash_rows=(17, 18),
                               action=[("QUAD", AMBER), ("B2B", ORANGE)]),
        "pause": scr_pause(bgs["moonbase"]),
        "gameover": scr_gameover(bgs["derelict"]),
        "settings": scr_settings(bgs["grid-horizon"]),
    }
    for k, s in screens.items():
        s.save(OUT / f"screen-{k}.png")
        up(s).save(OUT / f"screen-{k}@2x.png")
        print(f"screen {k}: {len(set(s.get_flattened_data()))} colours")
    up(scr_backdrops(bgs)).save(OUT / "backdrops@2x.png")
    up(names_board()).save(OUT / "names@2x.png")
