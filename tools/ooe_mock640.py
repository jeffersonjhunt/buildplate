"""OOE Build Plate: the mockups, and the design the game draws.

Screen type 7 (direct 640): 640x480, a $0RGB word a pixel (RGB444, 4,096 colours), double buffered. The layout
is a 40x30 grid of 16x16 cells. Everything is rounded to 12-bit colour; pictures get 4x4 ordered dither.
Blocks are an 8x8 design shown doubled (block_cells), since the falling piece is a sprite on the 320x240 grid.
"""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import ooe_mock as base  # glyphs, shapes, noise and dither helpers

OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "out640")
W, H = 640, 480
C = 16  # cell size in pixels


def q444(rgb):
    """RGB444: 4 bits a channel, 12-bit colour."""
    return tuple(min(255, int(round(v / 17.0)) * 17) for v in rgb)


def hx(h):
    h = h.lstrip("#")
    return q444(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))


def to444(img):
    """Quantize to RGB444 with 4x4 ordered dither (flat 12-bit colours pass unchanged)."""
    import numpy as np
    a = np.asarray(img.convert("RGB"), dtype=np.float32)
    bayer = (np.array(base.BAYER4, dtype=np.float32) + 0.5) / 16.0 - 0.5
    h, w = a.shape[:2]
    t = np.tile(bayer, (h // 4 + 1, w // 4 + 1))[:h, :w][..., None]
    q = np.clip(np.round(a / 17.0 + t * 0.94), 0, 15) * 17
    return Image.fromarray(q.astype(np.uint8), "RGB")


# brand colours, from the emulator site's stylesheet
BG0 = hx("#0b0a09")
PANEL = hx("#141311")
WELL = hx("#1c1512")
GRIDDOT = hx("#2c221d")
LINE = hx("#4a423b")
DIM = hx("#9a9590")
BONE = hx("#e8e4e0")
ORANGE = hx("#cc5500")
AMBER = hx("#ffb000")
RED = hx("#ff4a2a")
WHITE = hx("#ffffff")

PIECES = {
    "I": ("#8ff6ff", "#22c8dc", "#0a6f7c"),
    "O": ("#ffe680", "#ffb000", "#9a5c00"),
    "T": ("#e0a0ff", "#a848ee", "#4e1478"),
    "S": ("#a8ff98", "#44c844", "#14641a"),
    "Z": ("#ffa08a", "#ff4a2a", "#901a14"),
    "J": ("#a8c0ff", "#4a6cff", "#16248a"),
    "L": ("#ffa860", "#cc5500", "#6e2600"),
}
PIECES = {k: tuple(hx(c) for c in v) for k, v in PIECES.items()}
SHAPES = base.SHAPES
GLYPHS = base.GLYPHS


def mix(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


# ---------------------------------------------------------------- text: the 5x7 face at 2x, 16x16 cells
def text(img, x, y, s, col, scale=2, shadow=None):
    if shadow:
        text(img, x + scale // 2 + 1, y + scale // 2 + 1, s, shadow, scale)
    d = ImageDraw.Draw(img)
    for i, ch in enumerate(s):
        g = GLYPHS.get(ch, GLYPHS[" "])
        for gy, row in enumerate(g):
            for gx, bit in enumerate(row):
                if bit == "#":
                    X = x + i * 8 * scale + (gx + 1) * scale
                    Y = y + gy * scale
                    d.rectangle([X, Y, X + scale - 1, Y + scale - 1], fill=col)


def tw(s, scale=2):
    return len(s) * 8 * scale


def ooe_mark(img, x, y, h, col):
    d = ImageDraw.Draw(img)
    stroke = max(2, round(h / 7))
    ow = round(h * 0.86)
    gap = max(3, round(h * 0.18))
    r = max(2, round(h * 0.28))
    for k in range(2):
        x0 = x + k * (ow + gap)
        d.rounded_rectangle([x0, y, x0 + ow - 1, y + h - 1], radius=r, outline=col, width=stroke)
    bx = x + 2 * (ow + gap)
    for by in (y, y + (h - stroke) // 2, y + h - stroke):
        d.rounded_rectangle([bx, by, bx + ow - 1, by + stroke - 1], radius=stroke // 2, fill=col)
    return bx + ow - x


def mark_w(h):
    return ooe_mark(Image.new("RGB", (1, 1)), 0, 0, h, (0, 0, 0))


# ---------------------------------------------------------------- blocks, 16x16, direct colour
def block_cells(kind, ghost=False):
    """The 8x8 block design, one entry a sprite pixel: a colour, or None for transparent.

    Blocks are drawn at 8x8 and shown doubled (16x16 on screen), because the falling piece and
    its ghost are sprites, which the card shows on a 320x240 grid; locked blocks use the same
    8x8 art doubled, so a piece looks the same falling and locked. At most 5 colours a piece
    (light, upper face, lower face, dark, glint), in its own 16-colour sprite palette group."""
    lt, bs, dk = PIECES[kind]
    up, lo = mix(lt, bs, 0.55), mix(bs, dk, 0.2)
    g = [[None] * 8 for _ in range(8)]
    if ghost:
        for i in range(0, 8, 2):
            g[0][i] = g[7][i + 1] = g[i + 1][0] = g[i][7] = bs
        return g
    for j in range(8):
        for i in range(8):
            c = up if i + j < 7 else lo
            if i == 0 or j == 0:
                c = lt
            if i == 7 or j == 7:
                c = dk
            g[j][i] = c
    g[2][2] = WHITE
    g[2][3] = g[3][2] = lt
    return g


def block(img, x, y, kind, ghost=False):
    px = img.load()
    for j, row in enumerate(block_cells(kind, ghost)):
        for i, c in enumerate(row):
            if c is not None:
                for dy in (0, 1):
                    for dx in (0, 1):
                        px[x + 2 * i + dx, y + 2 * j + dy] = c


def well_cell(img, x, y, top=False):
    d = ImageDraw.Draw(img)
    d.rectangle([x, y, x + 15, y + 15], fill=PANEL if top else WELL)
    if not top:
        img.putpixel((x + 15, y + 15), GRIDDOT)


def panel(img, cx0, cy0, cx1, cy1, label=None, outline=LINE, fill=PANEL, labcol=ORANGE):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = cx0 * C, cy0 * C, cx1 * C + C - 1, cy1 * C + C - 1
    d.rounded_rectangle([x0 + 2, y0 + 2, x1 - 2, y1 - 2], radius=8, fill=fill)
    d.rounded_rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], radius=6, outline=outline, width=1)
    if label:
        lx = x0 + 16
        d.rectangle([lx - 4, y0, lx + tw(label) + 4, y0 + 13], fill=fill)
        text(img, lx, y0, label, labcol)


# ---------------------------------------------------------------- backdrops at 640x480
def dith(x, y):
    return base.dith(x, y)


def grad(stops, v):
    """Smooth multi-stop gradient (direct colour needs no dither, but we keep a hint of it)."""
    v = max(0.0, min(1.0, v))
    n = len(stops) - 1
    f = v * n
    i = min(int(f), n - 1)
    return mix(stops[i], stops[i + 1], f - i)


def starfield(img, rng, n):
    px = img.load()
    for _ in range(n):
        x, y = rng.randrange(W), rng.randrange(H)
        b = rng.random()
        c = mix((90, 90, 120), (255, 255, 255), b)
        px[x, y] = c
        if b > 0.93:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < W and 0 <= y + dy < H:
                    px[x + dx, y + dy] = mix(c, (0, 0, 0), 0.5)
            if b > 0.985:
                for k in range(2, 6):
                    for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
                        if 0 <= x + dx < W and 0 <= y + dy < H:
                            px[x + dx, y + dy] = mix(c, px[x + dx, y + dy], k / 6)


N = base.noise2


def bg_gas_giant(seed=1):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    sky = [hx("#03030a"), hx("#060820"), hx("#0c1238"), hx("#1a1440")]
    for y in range(H):
        for x in range(W):
            px[x, y] = grad(sky, y / H * 0.8 + N(x / 160, y / 160, seed) * 0.35)
    starfield(img, rng, 900)
    cx, cy, r = 470, 300, 196
    bands = [hx("#1a0a04"), hx("#4a1c08"), hx("#8a3a12"), hx("#c46a2c"), hx("#e8a060"), hx("#f6d0a0")]
    for y in range(max(0, cy - r), min(H, cy + r)):
        for x in range(max(0, cx - r), min(W, cx + r)):
            dx, dy = (x - cx) / r, (y - cy) / r
            d2 = dx * dx + dy * dy
            if d2 > 1:
                continue
            nz = math.sqrt(1 - d2)
            light = max(0.0, -dx * 0.7 - dy * 0.35 + nz * 0.6)
            band = 0.5 + 0.5 * math.sin(dy * 16 + 4 * N(x / 60, y / 14, seed + 3))
            storm = math.exp(-(((x - (cx - 60)) / 26) ** 2 + ((y - (cy + 50)) / 12) ** 2))
            v = light * (0.5 + 0.45 * band) + 0.25 * storm * light
            px[x, y] = grad(bands, v)
    for y in range(H):
        for x in range(W):
            dx, dy = (x - cx), (y - cy) * 3.1
            rr = math.sqrt(dx * dx + dy * dy)
            if 236 < rr < 320 and not (270 < rr < 278):
                behind = (y < cy) and ((x - cx) ** 2 + (y - cy) ** 2 < r * r)
                if behind:
                    continue
                v = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(rr * 0.45))
                shade = 0.35 if (y > cy and (x - cx) ** 2 / (r * r) + ((y - cy - 40) / r) ** 2 < 1 and x > cx - 40) else 1.0
                ringc = grad([hx("#3a2a1c"), hx("#8a6a48"), hx("#d8c098")], v * shade)
                a = 0.85
                px[x, y] = mix(px[x, y], ringc, a)
    mx, my, mr = 132, 92, 26
    for y in range(my - mr, my + mr):
        for x in range(mx - mr, mx + mr):
            dx, dy = (x - mx) / mr, (y - my) / mr
            if dx * dx + dy * dy <= 1:
                v = max(0, -dx * 0.6 - dy * 0.4 + math.sqrt(max(0, 1 - dx * dx - dy * dy)) * 0.6)
                v *= 0.85 + 0.15 * N(x / 6, y / 6, 9)
                px[x, y] = grad([hx("#101018"), hx("#5a5a68"), hx("#c8c8d0")], v)
    return img


def bg_grid_horizon(seed=2):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    hz = 300
    sky = [hx("#000000"), hx("#12041a"), hx("#2a0a30"), hx("#5a1430"), hx("#a02a20"), hx("#e05a10")]
    for y in range(hz):
        for x in range(W):
            px[x, y] = grad(sky, (y / hz) ** 1.5)
    starfield(img, rng, 400)
    sx, sy, sr = 320, 250, 96
    for y in range(sy - sr, hz):
        for x in range(sx - sr, sx + sr):
            dx, dy = x - sx, y - sy
            if dx * dx + dy * dy > sr * sr:
                continue
            gap = max(2, 14 - (y - sy) // 8)
            if y > sy - 10 and ((y - sy + 10) % gap) < max(1, (y - sy + 10) // 14):
                continue
            t = (y - (sy - sr)) / (2 * sr)
            px[x, y] = grad([hx("#fff08a"), hx("#ffb000"), hx("#ff6a00"), hx("#d02030")], t)
    for x in range(W):
        hgt = 36 + 44 * abs(math.sin(x * 0.0105 + 1.3)) * (0.6 + 0.4 * N(x / 46, 0, seed))
        hgt *= 1.0 if abs(x - 320) > 120 else 0.5
        top = int(hz - hgt)
        for y in range(top, hz):
            px[x, y] = mix(hx("#0a0208"), hx("#2a0818"), (y - top) / max(1, hgt))
        px[x, top] = hx("#ff6a00")
        if top + 1 < hz:
            px[x, top + 1] = hx("#a02a00")
    for y in range(hz, H):
        for x in range(W):
            px[x, y] = mix(hx("#100208"), hx("#000000"), (y - hz) / (H - hz))
    for k in range(1, 60):
        z = k * k * 0.32
        y = hz + int(z)
        if y >= H:
            break
        c = mix(hx("#ff6a00"), hx("#ff2080"), min(1, (y - hz) / 160))
        for x in range(W):
            px[x, y] = mix(px[x, y], c, 0.5 if y < hz + 10 else 1.0)
    for k in range(-30, 31):
        for y in range(hz, H):
            t = (y - hz) / (H - hz)
            x = int(320 + k * (10 + t * 120))
            if 0 <= x < W:
                c = mix(hx("#ff6a00"), hx("#ff2080"), min(1, (y - hz) / 160))
                px[x, y] = mix(px[x, y], c, 0.5 if y < hz + 10 else 1.0)
    return img


def bg_station(seed=3):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    neb = [hx("#000000"), hx("#02080e"), hx("#06202e"), hx("#183450"), hx("#40407a"), hx("#9a5a9a"), hx("#f0a0b0")]
    for y in range(H):
        for x in range(W):
            n = N(x / 150, y / 115, seed, 5)
            n2 = N(x / 50, y / 50, seed + 7, 3)
            v = max(0, (n - 0.4) * 2.3) * (0.7 + 0.5 * n2)
            px[x, y] = grad(neb, v)
    starfield(img, rng, 700)
    cx, cy = 184, 260
    hull, lit, win = hx("#3a3e4e"), hx("#9aa0b8"), hx("#ffc040")
    d = ImageDraw.Draw(img)
    for ang in (0, 60, 120):
        t = math.radians(ang)
        d.line([cx - 124 * math.cos(t), cy - 52 * math.sin(t), cx + 124 * math.cos(t), cy + 52 * math.sin(t)], fill=hull, width=3)
    for a in range(0, 7200):
        t = a / 7200 * 2 * math.pi
        front = math.sin(t) > 0
        for rr in range(124, 140):
            x = int(cx + rr * math.cos(t))
            y = int(cy + rr * 0.42 * math.sin(t))
            if 0 <= x < W and 0 <= y < H:
                shade = 0.5 + 0.5 * math.cos(t + 2.2)
                c = mix(hull, lit, shade * (1 if front else 0.4))
                if rr == 132 and (a // 60) % 3 == 0 and front:
                    c = win
                px[x, y] = c
    d.ellipse([cx - 18, cy - 12, cx + 18, cy + 12], fill=hx("#5a6070"), outline=lit)
    for i in range(5):
        d.point([cx - 8 + i * 4, cy], fill=win)
    sx, sy = 524, 108
    d.polygon([(sx, sy), (sx - 46, sy + 10), (sx - 40, sy), (sx - 46, sy - 10)], fill=hx("#a8acb8"))
    d.line([sx - 46, sy - 10, sx, sy], fill=hx("#e8ecf0"))
    for i in range(1, 140):
        a = 1 - i / 140
        for w in (-1, 0, 1):
            x, y = sx - 42 - i, sy + w
            px[x, y] = mix(px[x, y], hx("#40e8ff") if i < 30 else hx("#0a80a0"), a * (1 if w == 0 else 0.5))
    return img


def bg_moonbase(seed=4):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H), (0, 0, 0))
    px = img.load()
    starfield(img, rng, 700)
    ex, ey, er = 428, 140, 68
    for y in range(ey - er, ey + er):
        for x in range(ex - er, ex + er):
            dx, dy = (x - ex) / er, (y - ey) / er
            d2 = dx * dx + dy * dy
            if d2 > 1:
                continue
            light = max(0, dx * 0.7 - dy * 0.3 + math.sqrt(1 - d2) * 0.5)
            if light < 0.06:
                continue
            n = N(x / 28, y / 28, seed)
            cl = N(x / 16, y / 7, seed + 5)
            if cl > 0.6:
                c = grad([hx("#202430"), hx("#e8ecf4")], light)
            elif n > 0.55:
                c = grad([hx("#0a1a08"), hx("#3a7a30")], light)
            else:
                c = grad([hx("#020818"), hx("#1a4a9a")], light)
            px[x, y] = c
            if d2 > 0.9:  # atmosphere rim
                px[x, y] = mix(c, hx("#60a0ff"), (d2 - 0.9) * 6 * light)
    hz = 336
    for x in range(W):
        top = int(hz - 20 * N(x / 80, 0, seed) - 12 * N(x / 18, 3, seed))
        for y in range(top, H):
            depth = (y - top) / (H - top + 1)
            n = N(x / 36, y / 14, seed + 2, 4)
            v = 0.2 + 0.55 * n - 0.25 * depth
            px[x, y] = grad([hx("#0c0c0c"), hx("#3a3836"), hx("#7a766e"), hx("#b0aca0")], v)
        px[x, top] = hx("#c8c4b8")
    for _ in range(14):
        cx, cy = rng.randrange(W), rng.randrange(hz + 16, H)
        rx = rng.randrange(10, 44)
        for y in range(cy - rx // 3, cy + rx // 3 + 1):
            for x in range(cx - rx, cx + rx):
                if 0 <= x < W and 0 <= y < H:
                    dx, dy = (x - cx) / rx, (y - cy) / (rx / 3)
                    d2 = dx * dx + dy * dy
                    if d2 <= 1:
                        px[x, y] = mix(px[x, y], (0, 0, 0), 0.55 if dy < 0.1 else 0.3)
                    elif d2 <= 1.35 and dy > 0:
                        px[x, y] = mix(px[x, y], hx("#c8c4b8"), 0.5)
    d = ImageDraw.Draw(img)
    for bx, br in ((80, 36), (148, 22), (600, 28)):
        d.pieslice([bx - br, hz - br - 8, bx + br, hz + br - 8], 180, 360, fill=hx("#4a5060"), outline=hx("#a8b0c0"))
        d.arc([bx - br + 6, hz - br - 2, bx + br - 6, hz + br - 14], 200, 250, fill=hx("#d8e0f0"))
        for i in range(-br + 8, br - 6, 8):
            d.rectangle([bx + i, hz - 14, bx + i + 2, hz - 12], fill=hx("#ffc040"))
    d.line([112, hz - 12, 128, hz - 12], fill=hx("#a8b0c0"), width=3)
    d.line([192, hz - 4, 192, hz - 60], fill=hx("#a8b0c0"), width=2)
    d.line([180, hz - 52, 204, hz - 52], fill=hx("#a8b0c0"), width=2)
    d.ellipse([189, hz - 66, 195, hz - 60], fill=hx("#ff4a2a"))
    return img


def bg_derelict(seed=5):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = grad([hx("#000000"), hx("#100604"), hx("#24100a"), hx("#3a1c10")], N(x / 160, y / 160, seed, 4) * 0.95)
    starfield(img, rng, 600)
    rock = [hx("#0a0604"), hx("#2a1c12"), hx("#5a4030"), hx("#8a6a50"), hx("#c8a888")]
    for _ in range(30):
        ax, ay = rng.randrange(-20, W + 20), rng.randrange(-20, H + 20)
        ar = rng.choice([5, 7, 9, 12, 16, 22, 32, 44])
        sd = rng.randrange(1000)
        for y in range(ay - ar - 6, ay + ar + 6):
            for x in range(ax - ar - 6, ax + ar + 6):
                if not (0 <= x < W and 0 <= y < H):
                    continue
                dx, dy = (x - ax) / ar, (y - ay) / ar
                a = math.atan2(dy, dx)
                rr = 1 + 0.25 * (N(math.cos(a) * 2 + 5, math.sin(a) * 2 + 5, sd, 2) - 0.5) * 2
                d2 = math.sqrt(dx * dx + dy * dy)
                if d2 > rr:
                    continue
                nz = math.sqrt(max(0, 1 - (d2 / rr) ** 2))
                v = max(0, -dx * 0.6 - dy * 0.5 + nz * 0.5) * (0.7 + 0.4 * N(x / 6, y / 6, sd, 3))
                px[x, y] = grad(rock, v)
    d = ImageDraw.Draw(img)
    hx0, hy = 380, 372
    hull, dark, trim = hx("#4a4038"), hx("#1e1a16"), hx("#8a7c6a")
    d.polygon([(hx0 - 250, hy - 16), (hx0 + 140, hy - 28), (hx0 + 220, hy - 8), (hx0 + 140, hy + 20), (hx0 - 250, hy + 24)], fill=hull)
    d.line([hx0 - 250, hy - 16, hx0 + 140, hy - 28], fill=trim, width=2)
    for i in range(-230, 140, 28):
        d.rectangle([hx0 + i, hy - 12, hx0 + i + 18, hy + 10], outline=dark)
    d.rectangle([hx0 - 120, hy - 48, hx0 - 60, hy - 18], fill=hull, outline=trim)
    for i in range(-220, 132, 14):
        if rng.random() < 0.5:
            d.rectangle([hx0 + i, hy + 16, hx0 + i + 1, hy + 17], fill=hx("#ffc040"))
    d.ellipse([hx0 + 214, hy - 11, hx0 + 220, hy - 5], fill=hx("#ff4a2a"))
    for i in range(70):
        x, y = hx0 + 20 + i, hy - 6 + int(6 * math.sin(i * 0.35))
        d.line([x, y, x, y + 3], fill=(0, 0, 0))
        if rng.random() < 0.35:
            px[x, y + 4] = hx("#ff7a20")
    return img


BGS = {"gas-giant": bg_gas_giant, "grid-horizon": bg_grid_horizon, "orbital-station": bg_station,
       "moonbase": bg_moonbase, "derelict": bg_derelict}


def dim(img, f=0.75):
    return img.point(lambda v: int(v * f))


# ---------------------------------------------------------------- screens
NAME = "BUILD PLATE"


def header(img, hi="00184200"):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W - 1, 31], fill=PANEL)
    d.line([0, 31, W - 1, 31], fill=LINE)
    w = ooe_mark(img, 16, 8, 16, BONE)
    text(img, 16 + w + 10, 9, NAME, BONE)
    text(img, W - 16 - tw("HI " + hi), 9, "HI", DIM)
    text(img, W - 16 - tw(hi), 9, hi, AMBER)


def footer(img, s):
    d = ImageDraw.Draw(img)
    d.rectangle([0, 448, W - 1, H - 1], fill=PANEL)
    d.line([0, 448, W - 1, 448], fill=LINE)
    text(img, (W - tw(s)) // 2, 457, s, DIM)


def cells(img, ox, oy, kind, ghost=False):
    for (x, y) in SHAPES[kind]:
        block(img, ox + x * C, oy + y * C, kind, ghost)


def preview(img, cx, cy, kind):
    w = max(x for x, _ in SHAPES[kind]) + 1
    h = max(y for _, y in SHAPES[kind]) + 1
    cells(img, cx * C + (4 * C - w * C) // 2, cy * C + (2 * C - h * C) // 2, kind)


PF_X, PF_Y = 15, 6


def well(img, board, active=None, flash_rows=(), grey=False):
    panel(img, PF_X - 1, PF_Y - 2, PF_X + 10, PF_Y + 20)
    for c in range(10):
        well_cell(img, (PF_X + c) * C, (PF_Y - 1) * C, top=True)
    for r in range(20):
        for c in range(10):
            x, y = (PF_X + c) * C, (PF_Y + r) * C
            ch = board[r][c]
            if r in flash_rows:
                ImageDraw.Draw(img).rectangle([x, y, x + 15, y + 15], fill=WHITE)
            elif ch == ".":
                well_cell(img, x, y)
            else:
                block(img, x, y, ch)
                if grey:
                    for j in range(16):
                        for i in range(16):
                            p = img.getpixel((x + i, y + j))
                            g = int((p[0] * 0.3 + p[1] * 0.59 + p[2] * 0.11) * 0.55)
                            img.putpixel((x + i, y + j), (g, g, g))
    if active:
        kind, col, row, land = active
        cells(img, (PF_X + col) * C, (PF_Y + land) * C, kind, ghost=True)
        cells(img, (PF_X + col) * C, (PF_Y + row) * C, kind)


def left(img, hold="T", score="00041250", job="07", layers="063", action=None):
    panel(img, 2, 5, 12, 9, "HOLD")
    if hold:
        preview(img, 5, 6, hold)
    panel(img, 2, 11, 12, 22, "SHIFT")
    for i, (k, v, col) in enumerate((("OUTPUT", score, BONE), ("JOB", job, AMBER), ("LAYERS", layers, BONE))):
        text(img, 48, 208 + i * 56, k, DIM)
        text(img, 48, 228 + i * 56, v, col)
    if action:
        panel(img, 2, 24, 12, 26)
        for i, (s, col) in enumerate(action):
            text(img, 32 + (176 - tw(s)) // 2 - 8, 391 + i * 18, s, col)


def right(img, nxt=("I", "L", "S", "O", "J")):
    panel(img, 27, 5, 37, 21, "NEXT")
    for i, k in enumerate(nxt):
        preview(img, 30, 6 + i * 3, k)


def stamp(img, x, y, s, col=RED, angle=-4, scale=2):
    w = tw(s, scale) + 16
    st = Image.new("RGBA", (w + 8, 40), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rectangle([2, 2, w + 4, 35], outline=col + (255,), width=2)
    t = Image.new("RGB", (w + 8, 40), (0, 0, 0))
    text(t, 8, 12, s, col, scale)
    tm, sp = t.load(), st.load()
    rng = random.Random(7)
    for yy in range(40):
        for xx in range(w + 8):
            if tm[xx, yy] != (0, 0, 0):
                sp[xx, yy] = col + (255,)
            if sp[xx, yy][3]:
                ink = 0.55 + 0.45 * N(xx / 5, yy / 3, 11)
                if rng.random() > ink:
                    sp[xx, yy] = (0, 0, 0, 0)
                else:
                    sp[xx, yy] = col + (int(255 * min(1, ink + 0.2)),)
    st = st.rotate(angle, resample=Image.BICUBIC, expand=True)
    img.paste(st, (x, y), st)


BOARD = base.BOARD
GB = base.GAMEOVER_BOARD


def scr_title(bg):
    img = bg.copy()
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([96, 16, 543, 214], radius=10, fill=PANEL)
    d.rounded_rectangle([102, 22, 537, 208], radius=8, outline=LINE)
    mw = mark_w(48)
    ooe_mark(img, (W - mw) // 2, 34, 48, BONE)
    text(img, (W - tw("DIGITAL MANUFACTURING")) // 2, 94, "DIGITAL MANUFACTURING", DIM)
    text(img, (W - tw(NAME, 4)) // 2, 120, NAME, AMBER, scale=4, shadow=ORANGE)
    stamp(img, 330, 160, "STACK FAST")
    d.rounded_rectangle([176, 316, 463, 432], radius=8, fill=PANEL)
    d.rounded_rectangle([182, 322, 457, 426], radius=6, outline=LINE)
    for i, (s, sel) in enumerate((("START JOB", True), ("JOB 01", False), ("SETTINGS", False), ("QUIT", False))):
        y = 334 + i * 22
        text(img, 224, y, s, BONE if sel else DIM)
        if sel:
            text(img, 200, y, ">", AMBER)
    text(img, 224 + tw("JOB "), 356, "01", AMBER)
    text(img, 224 + tw("JOB 01 "), 356, "<>", LINE)
    footer(img, "HI SHIFT 00184200   (C) 2026 OOE")
    return img


def scr_play(bg, active=("T", 4, 3, 10), action=None, flash_rows=()):
    img = dim(bg)
    header(img)
    well(img, BOARD, active=active, flash_rows=flash_rows)
    left(img, action=action)
    right(img)
    footer(img, "ESC PAUSE   C HOLD   SPACE DROP")
    return img


def scr_pause(bg):
    img = dim(bg)
    header(img)
    well(img, ["." * 10] * 20)
    text(img, (W - tw("LINE HOLD")) // 2, 160, "LINE HOLD", AMBER)
    for i, (s, sel) in enumerate((("RESUME", True), ("RESTART", False), ("SETTINGS", False), ("QUIT", False))):
        y = 208 + i * 24
        text(img, PF_X * C + 24, y, s, BONE if sel else DIM)
        if sel:
            text(img, PF_X * C + 4, y, ">", AMBER)
    left(img, hold=None)
    right(img, nxt=())
    footer(img, "ESC RESUME   Q QUIT TO A>")
    return img


def scr_gameover(bg):
    img = dim(bg)
    header(img)
    well(img, GB, grey=True)
    left(img, hold="J", score="00184200", job="12", layers="117")
    right(img)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([212, 148, 427, 340], radius=10, fill=PANEL)
    d.rounded_rectangle([218, 154, 421, 334], radius=8, outline=RED, width=2)
    text(img, (W - tw("LINE STOP")) // 2, 170, "LINE STOP", RED)
    text(img, 236, 202, "OUTPUT", DIM)
    text(img, 236, 220, "00184200", AMBER)
    text(img, 236, 246, "JOB", DIM)
    text(img, 404 - tw("12"), 246, "12", BONE)
    text(img, 236, 266, "LAYERS", DIM)
    text(img, 404 - tw("117"), 266, "117", BONE)
    stamp(img, 206, 288, "NEW HI SHIFT", angle=3)
    footer(img, "R RESTART   Q QUIT TO A>")
    return img


def scr_settings(bg):
    img = dim(bg)
    header(img)
    panel(img, 5, 3, 34, 26, "SETTINGS")
    d = ImageDraw.Draw(img)
    rows = [("DAS", "10 FR"), ("ARR", "02 FR"), ("GHOST", "ON"), ("MUSIC", "ON"), ("MUSIC VOL", "#"),
            ("EFFECTS", "ON"), ("BACKDROPS", "RANDOM"), ("KEYS", "REMAP")]
    for i, (k, v) in enumerate(rows):
        y = 92 + i * 34
        sel = i == 0
        if sel:
            d.rounded_rectangle([112, y - 8, 527, y + 22], radius=4, fill=hx("#3a1a10"))
            text(img, 120, y, ">", AMBER)
        text(img, 144, y, k, BONE if sel else DIM)
        if v == "#":
            for j in range(10):
                d.rounded_rectangle([352 + j * 16, y, 363 + j * 16, y + 13], radius=2, fill=AMBER if j < 8 else LINE)
        else:
            text(img, 352, y, v, AMBER if sel else BONE)
        text(img, 496, y, ">", LINE)
    footer(img, "^v SELECT  <> CHANGE  ESC BACK")
    return img


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    bgs = {}
    for k, f in BGS.items():
        b = to444(f())
        bgs[k] = b
        b.save(OUT / f"bg-{k}.png")
        print("bg", k)
    screens = {
        "title": scr_title(bgs["grid-horizon"]),
        "play": scr_play(bgs["gas-giant"], action=[("T-SPIN", AMBER), ("DOUBLE", BONE)]),
        "play-clear": scr_play(bgs["orbital-station"], active=("I", 0, 0, 0), flash_rows=(17, 18),
                               action=[("QUAD", AMBER), ("B2B", ORANGE)]),
        "pause": scr_pause(bgs["moonbase"]),
        "gameover": scr_gameover(bgs["derelict"]),
        "settings": scr_settings(bgs["grid-horizon"]),
    }
    for k, s in screens.items():
        to444(s).save(OUT / f"screen-{k}.png")
        print("screen", k)
