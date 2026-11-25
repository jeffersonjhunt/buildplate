"""One Off Stax: five more backdrops (640x480, RGB444), for ten in all, one per job."""
import math
import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import ooe_mock640 as m

W, H = m.W, m.H
N, grad, mix, hx, starfield = m.N, m.grad, m.mix, m.hx, m.starfield
OUT = Path(sys.argv[1] if len(sys.argv) > 1 else "out640")


def bg_shipyard(seed=6):
    """Orbital shipyard: a hull being printed on a giant build plate above a glowing planet limb."""
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = grad([hx("#000000"), hx("#02040a"), hx("#060a18")], y / H * 0.8 + N(x / 200, y / 200, seed) * 0.2)
    starfield(img, rng, 500)
    # planet limb
    cx, cy, r = 320, 1180, 860
    for y in range(300, H):
        for x in range(W):
            d = math.hypot(x - cx, y - cy)
            if d < r:
                depth = (r - d) / 60
                c = grad([hx("#ff9a40"), hx("#a03010"), hx("#301008"), hx("#100404")], min(1, depth))
                n = N(x / 40, y / 12, seed + 2)
                px[x, y] = mix(c, hx("#000000"), 0.3 * n)
            elif d < r + 14:
                px[x, y] = mix(px[x, y], hx("#ff8030"), (1 - (d - r) / 14) * 0.7)
    d = ImageDraw.Draw(img)
    steel, dark, lamp = hx("#5a6070"), hx("#22262e"), hx("#ffc040")
    # the build plate
    d.polygon([(110, 300), (530, 300), (580, 330), (60, 330)], fill=hx("#3a3e48"), outline=hx("#8a92a4"))
    for gx in range(80, 570, 24):
        d.line([gx, 330, gx + (gx - 320) * 0.12, 300], fill=hx("#4a4e58"))
    # gantries with lattice
    for gx in (130, 510):
        d.rectangle([gx - 8, 80, gx + 8, 300], outline=steel)
        for yy in range(80, 300, 16):
            d.line([gx - 8, yy, gx + 8, yy + 16], fill=dark)
            d.line([gx + 8, yy, gx - 8, yy + 16], fill=dark)
        for yy in range(96, 300, 40):
            d.rectangle([gx - 2, yy, gx + 1, yy + 2], fill=lamp)
    d.rectangle([122, 74, 518, 90], outline=steel, fill=dark)
    for xx in range(126, 516, 16):
        d.line([xx, 74, xx + 16, 90], fill=steel)
    # print head and its beam
    hxp = 360
    d.rectangle([hxp - 18, 92, hxp + 18, 112], fill=hx("#8a92a4"), outline=hx("#c8d0e0"))
    d.line([hxp, 112, hxp, 196], fill=hx("#40e8ff"))
    d.line([hxp - 1, 112, hxp - 1, 196], fill=hx("#0a80a0"))
    # half-printed hull, layer lines
    for k, y in enumerate(range(296, 196, -4)):
        half = 150 - abs(k - 6) * 3 if k < 25 else 0
        if y < 200:
            break
        x0, x1 = 320 - half, 320 + half
        if k > 18:
            x1 = min(x1, hxp)
        d.line([x0, y, x1, y], fill=mix(hx("#8a8f9a"), hx("#40444e"), (k % 3) / 3))
        d.line([x0, y + 1, x1, y + 1], fill=hx("#2a2e36"))
    # sparks at the head
    for _ in range(40):
        a = rng.uniform(math.pi * 0.1, math.pi * 0.9)
        L = rng.uniform(4, 26)
        x2, y2 = hxp + math.cos(a) * L * (1 if rng.random() < 0.5 else -1), 198 + math.sin(a) * L * 0.6
        d.line([hxp, 198, x2, y2], fill=rng.choice([hx("#fff08a"), hx("#ffb000"), hx("#ffffff")]))
    return img


def bg_ice_aurora(seed=7):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = grad([hx("#000208"), hx("#020a18"), hx("#06142a")], y / 320)
    starfield(img, rng, 600)
    # aurora curtains
    for y in range(20, 260):
        for x in range(W):
            base = 120 + 50 * math.sin(x / 90 + 1.1) + 30 * math.sin(x / 37)
            dy = y - base
            if -110 < dy < 40:
                flick = 0.5 + 0.5 * math.sin(x / 3.1 + N(x / 30, 0, seed) * 9)
                fall = math.exp(-((dy + 30) / 50) ** 2) * (0.35 + 0.65 * flick)
                col = grad([hx("#20ff90"), hx("#40ffc0"), hx("#a060ff")], max(0, min(1, (-dy) / 110)))
                px[x, y] = mix(px[x, y], col, min(0.85, fall))
    # icy mountains
    for x in range(W):
        top = int(300 - 70 * abs(math.sin(x / 120 + 0.5)) * (0.6 + 0.4 * N(x / 50, 1, seed)) - 30 * N(x / 15, 4, seed))
        for y in range(top, 372):
            v = 0.85 - (y - top) / 160 + 0.25 * N(x / 10, y / 10, seed + 3)
            ridge = 0.12 * math.sin((x - y * 0.6) / 9 + N(x / 30, y / 30, seed) * 4)
            px[x, y] = grad([hx("#0a1424"), hx("#3a5070"), hx("#a8c0d8"), hx("#e8f4ff")], v + ridge)
    # frozen lake reflecting the sky
    for y in range(372, H):
        for x in range(W):
            sy = 372 - (y - 372) * 2
            src = px[x, max(0, min(H - 1, sy))]
            px[x, y] = mix(src, hx("#081828"), 0.55 + 0.1 * math.sin(y * 0.9))
    d = ImageDraw.Draw(img)
    d.rectangle([470, 356, 520, 372], fill=hx("#2a3444"), outline=hx("#8aa0b8"))
    for i in range(474, 518, 8):
        d.rectangle([i, 362, i + 3, 365], fill=hx("#ffc040"))
    d.line([500, 356, 500, 330], fill=hx("#8aa0b8"))
    d.point([500, 329], fill=hx("#ff4a2a"))
    return img


def bg_twin_suns(seed=8):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = grad([hx("#1a0a2a"), hx("#6a2040"), hx("#d06030"), hx("#ffc070")], (y / 300) ** 1.3)
    for sx, sy, sr, c in ((420, 230, 34, hx("#fff4c0")), (500, 262, 18, hx("#ffd890"))):
        for y in range(sy - sr * 3, sy + sr * 3):
            for x in range(sx - sr * 3, sx + sr * 3):
                if 0 <= x < W and 0 <= y < H:
                    dd = math.hypot(x - sx, y - sy)
                    if dd < sr:
                        px[x, y] = c
                    elif dd < sr * 3:
                        px[x, y] = mix(px[x, y], c, 0.5 * (1 - (dd - sr) / (sr * 2)) ** 2)
    # faint ringed planet high in the sky
    pcx, pcy, pr = 150, 90, 46
    for y in range(pcy - 60, pcy + 60):
        for x in range(pcx - 110, pcx + 110):
            dx, dy = x - pcx, y - pcy
            if dx * dx + dy * dy < pr * pr:
                px[x, y] = mix(px[x, y], hx("#e0b0c0"), 0.35 + 0.2 * math.sin(dy / 6))
            rr = math.hypot(dx, dy * 3.5)
            if 62 < rr < 98 and not (dy < 0 and dx * dx + dy * dy < pr * pr):
                px[x, y] = mix(px[x, y], hx("#f0d0d0"), 0.3)
    # dunes, back to front
    for layer, (hgt, c0, c1) in enumerate(((300, "#7a3a28", "#c06a40"), (340, "#5a2a1c", "#a85a34"), (390, "#3a1a10", "#80401e"))):
        for x in range(W):
            top = int(hgt - 30 * math.sin(x / (90 - layer * 15) + layer * 2) - 20 * N(x / 60, layer, seed))
            for y in range(top, H):
                lit = 0.5 + 0.5 * math.sin(x / (90 - layer * 15) + layer * 2 + 1.2)
                px[x, y] = grad([hx(c0), hx(c1)], lit * (1 - (y - top) / 200))
    d = ImageDraw.Draw(img)
    for bx, bh in ((90, 120), (120, 80), (560, 150)):  # rock spires
        d.polygon([(bx - 14, 360), (bx - 6, 360 - bh), (bx + 4, 360 - bh + 10), (bx + 16, 360)], fill=hx("#2a120a"))
    return img


def bg_neon_city(seed=9):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    for y in range(H):
        for x in range(W):
            px[x, y] = grad([hx("#05020c"), hx("#180830"), hx("#401050"), hx("#802060")], (y / 360) ** 1.4)
    starfield(img, rng, 150)
    d = ImageDraw.Draw(img)
    neon = [hx("#ff2a8a"), hx("#40e8ff"), hx("#ffb000"), hx("#a060ff")]
    for layer in range(3):
        x = -20
        while x < W:
            bw = rng.randrange(30, 80)
            bh = rng.randrange(80, 220) + layer * 40
            top = 400 - bh + layer * 30
            body = mix(hx("#0a0614"), hx("#1a1028"), layer / 3)
            d.rectangle([x, top, x + bw, H], fill=body)
            for wy in range(top + 6, H, 8):
                for wx in range(x + 4, x + bw - 4, 6):
                    if rng.random() < 0.22 + 0.1 * layer:
                        d.rectangle([wx, wy, wx + 2, wy + 3], fill=rng.choice([hx("#ffc860"), hx("#80d0ff"), hx("#ffe0a0")]) if layer == 2 else hx("#3a2a50"))
            if layer == 2 and rng.random() < 0.6:  # vertical neon sign, no words
                c = rng.choice(neon)
                sx = x + bw // 2
                d.rectangle([sx - 4, top + 14, sx + 4, top + 60], outline=c)
                for k in range(top + 20, top + 56, 9):
                    d.rectangle([sx - 1, k, sx + 1, k + 4], fill=c)
            x += bw + rng.randrange(-6, 10)
    # flying traffic streaks
    for _ in range(6):
        y = rng.randrange(150, 300)
        x0 = rng.randrange(0, W - 120)
        c = rng.choice([hx("#ff4a2a"), hx("#ffffff")])
        for i in range(rng.randrange(40, 120)):
            px[x0 + i, y] = mix(px[x0 + i, y], c, i / 120)
    # wet street glow
    for y in range(440, H):
        for x in range(W):
            px[x, y] = mix(px[x, y], hx("#ff2a8a") if (x // 40) % 3 == 0 else hx("#40e8ff"), 0.15)
    return img


def bg_black_hole(seed=10):
    rng = random.Random(seed)
    img = Image.new("RGB", (W, H))
    px = img.load()
    cx, cy, rs = 320, 230, 46
    for y in range(H):
        for x in range(W):
            px[x, y] = grad([hx("#000000"), hx("#08040e"), hx("#140a1a")], N(x / 120, y / 120, seed) * 0.8)
    # lensed stars: push stars away from the hole
    for _ in range(900):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        dx, dy = x - cx, y - cy
        dd = math.hypot(dx, dy) + 1e-3
        k = 1 + (rs * 2.2) ** 2 / (dd * dd)
        X, Y = int(cx + dx * k), int(cy + dy * k)
        if 0 <= X < W and 0 <= Y < H:
            b = rng.random()
            px[X, Y] = mix(hx("#605870"), hx("#ffffff"), b)
    disk = [hx("#200400"), hx("#802000"), hx("#e06010"), hx("#ffb040"), hx("#fff4d0")]
    for y in range(H):
        for x in range(W):
            dx, dy = x - cx, y - cy
            # thin tilted disk in front
            ex = dx / 250
            ey = dy / 34
            e = math.hypot(ex, ey)
            r = math.hypot(dx, dy)
            # the far side of the disk, lensed up over the top as an arc
            arc = abs(r - rs * 1.75) < 10 and dy < 6
            if 0.32 < e < 1.0 and not (r < rs * 1.02):
                heat = (1 - e) / 0.68
                swirl = 0.5 + 0.5 * math.sin(math.atan2(ey, ex) * 7 + e * 25)
                dop = 0.7 + 0.3 * (-dx / 250)  # the approaching side is brighter
                v = heat * (0.6 + 0.4 * swirl) * dop
                px[x, y] = mix(px[x, y], grad(disk, v), min(1, 0.4 + heat))
            elif arc:
                v = (1 - abs(r - rs * 1.75) / 10) * (0.55 + 0.25 * math.sin(math.atan2(dy, dx) * 9))
                px[x, y] = mix(px[x, y], grad(disk, v), 0.9)
            if r < rs:
                px[x, y] = (0, 0, 0)
            elif r < rs + 3:
                px[x, y] = mix(px[x, y], hx("#ffd890"), 0.6)
    return img


NEW = {"shipyard": bg_shipyard, "ice-aurora": bg_ice_aurora, "twin-suns": bg_twin_suns,
       "neon-city": bg_neon_city, "black-hole": bg_black_hole}

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for k, f in NEW.items():
        m.to444(f()).save(OUT / f"bg-{k}.png")
        print("bg", k)
