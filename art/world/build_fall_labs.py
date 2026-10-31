"""Case 10's lab art, drawn flat (front-on, no camera pitch) so the game can do real physics on it.

    python build_fall_labs.py

Writes to out/fall/: lab_tower.png and lab_gramophone.png (480x270), sack.png (16x16), sheet_ghost.png (two
32x32 frames: the ghost, then the plain sheet), and fall_layout.json, the pixel geometry LabFall needs:
ground line, pixels per metre, each balcony's floor, the chalk outline, the waveform strip.
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "out", "fall")
W, H = 480, 270
PX_PER_M = 10.0
GROUND = 250
WALL_X = 230                         # the tower's front face; the courtyard runs off to the right
TOWER_L = 150
BALCONIES = {"rivet": 4.9, "varnish": 11.0, "pendle": 19.6}
BANNER = {"rivet": "#B8251C", "varnish": "#2A5E46", "pendle": "#D8A63E"}
OUTLINE_M = 4.5                      # demo seed: 3 m/s x 1.5 s

INK, NIGHT, NIGHT2 = "#07090F", "#05060E", "#1A1A2E"
STONE, STONE_L, STONE_D = "#383846", "#484858", "#1C1C26"
COBBLE, COBBLE_D = "#282834", "#14141C"
PAPER, PAPER_D, RULE = "#E3D8B8", "#B3A584", "#8F8268"
WOOD, WOOD_L, WOOD_D = "#4A2A18", "#623A22", "#22120A"
BRASS, BRASS_L, BRASS_D = "#AC7A22", "#F6D070", "#4A2E08"
CANDLE, SHEET, SHEET_D, GHOST = "#F8C870", "#D8DCE6", "#8890A0", "#A8C8FF"


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def sky(w, h, top, bottom):
    """A vertical gradient in six dithered bands, like the rendered districts."""
    a, b = np.array(_rgb(top), float), np.array(_rgb(bottom), float)
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    t = np.linspace(0, 1, h)[:, None] * 5 + bayer[np.arange(h) % 4][:, np.arange(w) % 4] - 0.5
    t = np.clip(np.round(t), 0, 5) / 5
    img = (a + (b - a) * t[..., None]).astype(np.uint8)
    return Image.fromarray(np.dstack([img, np.full((h, w), 255, np.uint8)]), "RGBA")


def y_of(m):
    return round(GROUND - m * PX_PER_M)


BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def light(im, cx, cy, rx, ry, col, k, mix=False):
    """A soft elliptical pool of light (added) or haze (mixed toward col), quantised in dithered steps."""
    a = np.asarray(im).astype(float)
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    f = np.clip(1 - np.hypot((xx - cx) / rx, (yy - cy) / ry), 0, 1) ** 2 * k
    f = (np.floor(f * 6 + BAYER[yy % 4, xx % 4]) / 6)[..., None]
    c = np.array(_rgb(col), float)
    a[..., :3] = a[..., :3] * (1 - f) + c * f if mix else a[..., :3] + c * f
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")


def shade(hexcol, k):
    return tuple(int(min(255, v * k)) for v in _rgb(hexcol))


def lab_tower():
    rng = np.random.default_rng(5)
    im = sky(W, H, "#04050C", "#1C1E36")
    # moon, clouds catching its light, a far ridge and the manor's dark roofline behind the courtyard
    im = light(im, 409, 29, 70, 60, "#2A3458", 0.9)
    for cx, cy, rx, ry in ((330, 46, 110, 9), (440, 70, 90, 7), (90, 30, 120, 8), (250, 96, 140, 6)):
        im = light(im, cx, cy, rx, ry, "#3A4468", 0.85, mix=True)
    d = ImageDraw.Draw(im)
    for _ in range(70):
        x, y = rng.integers(0, W), rng.integers(0, 140)
        d.point((x, y), fill="#C9D8FF" if rng.random() < 0.4 else "#5A6A9A")
    d.ellipse((400, 20, 418, 38), fill="#E4E6F2")
    d.ellipse((404, 25, 409, 30), fill="#A8AEC6")
    d.ellipse((411, 30, 414, 33), fill="#B8BED4")
    d.polygon([(0, 214), (60, 200), (130, 206), (240, 196), (330, 204), (420, 194), (480, 202), (480, GROUND), (0, GROUND)],
              fill="#10121E")
    for x0, x1, top in ((270, 330, 214), (330, 400, 208), (400, 480, 216)):
        d.rectangle((x0, top, x1, GROUND), fill="#0B0C16")
        d.polygon([(x0 - 4, top), (x1 + 4, top), ((x0 + x1) / 2, top - 14)], fill="#0B0C16")
        for wx in range(x0 + 8, x1 - 6, 16):
            if rng.random() < 0.45:
                d.rectangle((wx, top + 10, wx + 3, top + 15), fill="#C08A40")
    # the tower: coursed stone, each block its own tone, lit from the moon on the right
    tones = ["#2A2A36", "#30303E", "#383846", "#40404E", "#4A4A5A"]
    for row, y in enumerate(range(20, GROUND, 6)):
        for x in range(TOWER_L - (5 if row % 2 else 0), WALL_X, 10):
            t = int(np.clip(rng.integers(0, 3) + (x - TOWER_L) / (WALL_X - TOWER_L) * 2.2, 0, 4))
            d.rectangle((max(x, TOWER_L), y, min(x + 9, WALL_X - 1), y + 5), fill=tones[t])
            d.line((max(x, TOWER_L), y, min(x + 8, WALL_X - 1), y), fill=shade(tones[t], 1.18))
        d.line((TOWER_L, y + 5, WALL_X, y + 5), fill="#16161E")
    d.line((WALL_X - 1, 20, WALL_X - 1, GROUND), fill="#7A8098")
    d.line((TOWER_L, 20, TOWER_L, GROUND), fill="#121218", width=2)
    for y in (70, 110, 170, 226):                          # arrow slits
        d.rectangle((TOWER_L + 18, y, TOWER_L + 20, y + 9), fill="#08080E")
    for _ in range(40):                                    # ivy at the foot
        x, y = TOWER_L + rng.integers(-4, 40), GROUND - rng.integers(0, 50) * rng.random()
        d.ellipse((x, y, x + 4, y + 3), fill="#1E3426" if rng.random() < 0.6 else "#2C4A34")
    # slate roof with a ridge highlight, a cornice, and the clock in a brass ring with hour ticks
    mx = (TOWER_L + WALL_X) / 2
    d.polygon([(TOWER_L - 6, 20), (WALL_X + 6, 20), (mx, -30)], fill="#1C2232")
    for k in range(1, 8):
        y = 20 - k * 6
        hw = (WALL_X - TOWER_L + 12) / 2 * (1 - k * 6 / 50)
        d.line((mx - hw, y, mx + hw, y), fill="#283048")
    d.line((mx, -30, WALL_X + 6, 20), fill="#4A5470")
    d.rectangle((TOWER_L - 6, 19, WALL_X + 6, 22), fill="#4A4A5A", outline="#16161E")
    cx, cy = int(mx), 36
    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=BRASS_D)
    d.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), fill=BRASS)
    d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill="#F2E6C0")
    for k in range(12):
        an = k * np.pi / 6
        d.point((cx + round(7.5 * np.sin(an)), cy - round(7.5 * np.cos(an))), fill=INK)
    d.line((cx, cy, cx, cy - 7), fill=INK, width=2)
    d.line((cx, cy, cx + 4, cy + 1), fill=INK)
    # the balconies: a lit arched door, a stone slab on a corbel, an iron rail, the owner's banner with folds
    floors = {}
    for sid, m in BALCONIES.items():
        y = y_of(m)
        floors[sid] = {"metres": m, "x": WALL_X + 18, "y": y}
        d.rectangle((WALL_X - 16, y - 24, WALL_X - 1, y), fill="#5A5A6C")
        d.polygon([(WALL_X - 16, y - 24), (WALL_X - 1, y - 24), (WALL_X - 8, y - 31)], fill="#5A5A6C")
        d.rectangle((WALL_X - 14, y - 22, WALL_X - 3, y - 1), fill=CANDLE)
        d.polygon([(WALL_X - 14, y - 22), (WALL_X - 3, y - 22), (WALL_X - 8, y - 28)], fill=CANDLE)
        d.rectangle((WALL_X - 12, y - 20, WALL_X - 5, y - 1), fill="#FFE2A0")
        d.line((WALL_X - 9, y - 26, WALL_X - 9, y - 1), fill="#9A6428")
        d.line((WALL_X - 14, y - 12, WALL_X - 3, y - 12), fill="#9A6428")
        d.polygon([(WALL_X, y + 3), (WALL_X + 8, y + 3), (WALL_X, y + 10)], fill="#30303E")
        d.rectangle((WALL_X, y, WALL_X + 30, y + 3), fill="#5A5A6C", outline="#1C1C26")
        d.line((WALL_X, y, WALL_X + 30, y), fill="#8A90A8")
        d.line((WALL_X + 30, y - 10, WALL_X + 30, y), fill="#2A2E38", width=2)
        d.line((WALL_X, y - 10, WALL_X + 30, y - 10), fill="#3A4050", width=2)
        d.line((WALL_X, y - 11, WALL_X + 30, y - 11), fill="#8A90A8")
        for x in range(WALL_X + 4, WALL_X + 30, 5):
            d.line((x, y - 10, x, y), fill="#2A2E38")
        b = BANNER[sid]
        d.rectangle((WALL_X + 8, y + 4, WALL_X + 20, y + 18), fill=b)
        d.line((WALL_X + 11, y + 5, WALL_X + 11, y + 15), fill=shade(b, 0.65))
        d.line((WALL_X + 17, y + 5, WALL_X + 17, y + 15), fill=shade(b, 1.3))
        d.line((WALL_X + 8, y + 4, WALL_X + 20, y + 4), fill=BRASS_L)
        d.polygon([(WALL_X + 8, y + 18), (WALL_X + 20, y + 18), (WALL_X + 14, y + 13)], fill="#30303E")
    for m in BALCONIES.values():
        im = light(im, WALL_X - 8, y_of(m) - 12, 30, 26, "#7A4A14", 0.7)
    im = light(im, mx, 36, 26, 26, "#5A4A20", 0.6)
    d = ImageDraw.Draw(im)
    # wet cobbles, a puddle holding the moon, the chalk outline 4.5 m out, a ground ruler in metres
    d.rectangle((0, GROUND, W, H), fill="#14141C")
    for r, y in enumerate(range(GROUND + 1, H, 4)):
        for x in range(-(r % 2) * 4, W, 8):
            d.ellipse((x, y, x + 7, y + 3), fill=["#22222E", "#282834", "#2E2E3C"][rng.integers(0, 3)])
            d.line((x + 2, y, x + 4, y), fill="#3E4052")
    d.ellipse((380, GROUND + 3, 452, GROUND + 9), fill="#1A2034")
    d.line((404, GROUND + 5, 418, GROUND + 5), fill="#9AA4C8")
    d.rectangle((WALL_X - 2, GROUND + 5, WALL_X + 222, GROUND + 20), fill="#101018")
    ox = round(WALL_X + OUTLINE_M * PX_PER_M)
    d.ellipse((ox - 16, GROUND - 1, ox + 16, GROUND + 5), outline="#F2F4FA")
    d.ellipse((ox - 24, GROUND, ox - 16, GROUND + 4), outline="#F2F4FA")
    small = _font("arialbd.ttf", 8)
    for k in range(0, 23):
        x = WALL_X + k * PX_PER_M
        d.line((x, GROUND + 6, x, GROUND + (11 if k % 5 == 0 else 8)), fill=PAPER_D)
        if k % 5 == 0:
            d.text((x - 3, GROUND + 11), f"{k}", font=small, fill=PAPER)
    d.line((WALL_X, GROUND + 6, WALL_X + 220, GROUND + 6), fill=PAPER_D)
    # the metre strip: a surveyor's pole up the wall, banded red every other metre, numbered every five
    sx = TOWER_L - 22
    d.rectangle((sx - 1, y_of(21) - 1, sx + 11, GROUND), fill="#1C140C")
    d.rectangle((sx, y_of(21), sx + 10, GROUND), fill=PAPER, outline=RULE)
    for k in range(0, 21, 2):
        d.rectangle((sx + 7, y_of(k + 1) + 1, sx + 9, y_of(k) - 1), fill="#B8251C")
    for k in range(0, 22):
        y = y_of(k)
        d.line((sx, y, sx + (10 if k % 5 == 0 else 5), y), fill=INK)
        if k % 5 == 0:
            d.text((sx - 14, y - 5), f"{k}", font=small, fill=PAPER)
    d.text((sx - 6, y_of(21) - 12), "m", font=small, fill=PAPER)
    im.save(os.path.join(OUT, "lab_tower.png"))
    return {"ground_y": GROUND, "px_per_m": PX_PER_M, "wall_x": WALL_X, "balconies": floors,
            "outline": {"x": ox, "y": GROUND + 2, "metres": OUTLINE_M}, "drop_from_x": WALL_X + 18}


def lab_gramophone():
    rng = np.random.default_rng(9)
    im = sky(W, H, "#0C0806", "#2A1A12")
    # damask wallpaper: a diamond lattice with a dot at every crossing
    a = np.asarray(im).copy()
    wall = a[:196]
    yy, xx = np.mgrid[0:196, 0:W]
    lat = ((xx + yy) % 14 == 0) | ((xx - yy) % 14 == 0)
    wall[lat, :3] = (wall[lat, :3] * 1.45).clip(0, 255).astype(np.uint8)
    wall[((xx + yy) % 14 == 7) & ((xx - yy) % 14 == 7), :3] = _rgb("#5A3E1E")
    im = Image.fromarray(a, "RGBA")
    d = ImageDraw.Draw(im)
    d.line((0, 104, W, 104), fill=WOOD_L, width=2)
    d.line((0, 106, W, 106), fill=WOOD_D)
    # a tall window, moonlight and rain beyond it
    wx0, wy0, wx1, wy1 = 376, 6, 452, 96
    d.rectangle((wx0 - 4, wy0 - 4, wx1 + 4, wy1 + 6), fill=WOOD_D)
    im.paste(sky(wx1 - wx0, wy1 - wy0, "#0A0E22", "#2A3456"), (wx0, wy0))
    d = ImageDraw.Draw(im)
    d.ellipse((424, 18, 438, 32), fill="#E4E6F2")
    for _ in range(26):
        x, y = rng.integers(wx0, wx1), rng.integers(wy0, wy1 - 6)
        d.line((x, y, x - 1, y + 5), fill="#4A5C88")
    d.rectangle((wx0, (wy0 + wy1) // 2 - 1, wx1, (wy0 + wy1) // 2), fill=WOOD_D)
    d.rectangle(((wx0 + wx1) // 2 - 1, wy0, (wx0 + wx1) // 2, wy1), fill=WOOD_D)
    d.rectangle((wx0 - 6, wy1 + 4, wx1 + 6, wy1 + 8), fill=WOOD_L, outline=WOOD_D)
    # a small gilt-framed landscape
    d.rectangle((296, 30, 344, 72), fill=BRASS, outline=BRASS_D)
    d.rectangle((300, 34, 340, 68), fill="#1A2234")
    d.polygon([(300, 60), (314, 50), (326, 56), (340, 46), (340, 68), (300, 68)], fill="#0E141E")
    d.point((330, 40), fill="#D8DCEC")
    # the hanging lamp: cord, a green glass shade, a brass rim
    d.line((240, 0, 240, 14), fill="#1A1008", width=2)
    d.polygon([(226, 14), (254, 14), (272, 34), (208, 34)], fill="#2E5A44")
    d.line((226, 14, 254, 14), fill="#4A8A68")
    d.line((208, 34, 272, 34), fill=BRASS_L, width=2)
    d.ellipse((234, 33, 246, 39), fill="#FFF0C0")
    # the desk: planks, each its own tone, with grain
    for i, y in enumerate(range(196, H, 9)):
        d.rectangle((0, y, W, y + 8), fill=shade(WOOD, [1.0, 0.86, 1.1, 0.94][i % 4]))
        d.line((0, y + 8, W, y + 8), fill=WOOD_D)
        for _ in range(14):
            x = rng.integers(0, W)
            d.line((x, y + rng.integers(2, 7), x + rng.integers(8, 30), y + rng.integers(2, 7)), fill=shade(WOOD, 0.75))
    d.line((0, 196, W, 196), fill=WOOD_L, width=2)
    # the gramophone: a panelled cabinet, a crank, a record with grooves and a red label, the tonearm
    d.rectangle((20, 150, 96, 196), fill=WOOD_L, outline=WOOD_D)
    d.rectangle((26, 160, 90, 190), fill=WOOD, outline=WOOD_D)
    d.line((26, 160, 90, 160), fill="#8A5A34")
    d.line((26, 160, 26, 190), fill="#8A5A34")
    for x in (20, 92):
        d.rectangle((x, 192, x + 4, 197), fill=BRASS)
    d.line((14, 172, 20, 172), fill=BRASS, width=2)
    d.line((14, 172, 12, 182), fill=BRASS, width=2)
    d.ellipse((9, 181, 15, 186), fill=WOOD_D)
    d.rectangle((18, 148, 98, 152), fill=WOOD_L, outline=WOOD_D)
    d.ellipse((24, 140, 92, 156), fill="#0C0C10", outline="#26262E")
    for r in (28, 22, 16):
        d.ellipse((58 - r, 148 - r * 0.24, 58 + r, 148 + r * 0.24), outline="#1C1C24")
    d.ellipse((51, 146, 65, 150), fill="#B8251C")
    d.point((58, 148), fill=BRASS_L)
    d.line((70, 145, 84, 146), fill="#2A2A30")
    d.line((84, 146, 96, 104), fill=BRASS, width=3)
    d.line((85, 144, 96, 106), fill=BRASS_L)
    # the horn: a flared cone built out of rings, banded like brass petals
    n = 16
    for i in range(n + 1):
        t = i / n
        x, y = 98 + (159 - 98) * t, 106 + (58 - 106) * t
        rx, ry = 3 + 16 * t ** 2.2, 3 + 21 * t ** 2.2
        d.ellipse((x - rx, y - ry, x + rx, y + ry), fill=[BRASS, "#C89838", BRASS, "#8E6418"][i % 4])
    d.ellipse((140, 34, 178, 82), fill=BRASS_L, outline=BRASS_D)
    d.ellipse((143, 38, 175, 78), fill=BRASS)
    d.ellipse((149, 46, 169, 70), fill=BRASS_D)
    d.ellipse((154, 52, 164, 64), fill="#1E1204")
    d.arc((142, 36, 176, 80), 200, 260, fill="#FFF0B0", width=2)
    # the paper strip, pinned at both ends with brass clips, casting a shadow on the wall
    x0, x1, y0, y1 = 112, 468, 112, 188
    d.rectangle((x0 + 2, y0 + 2, x1 + 5, y1 + 5), fill="#0C0806")
    d.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), fill=PAPER_D)
    d.rectangle((x0, y0, x1, y1), fill=PAPER)
    for cx in (x0, x1):
        d.rectangle((cx - 3, y0 - 6, cx + 3, y0 + 6), fill=BRASS, outline=BRASS_D)
        d.rectangle((cx - 3, y1 - 6, cx + 3, y1 + 6), fill=BRASS, outline=BRASS_D)
    mid = (y0 + y1) // 2
    d.line((x0, mid, x1, mid), fill=RULE)
    small = _font("arialbd.ttf", 8)
    per_s = (x1 - x0) / 6.0
    for k in range(0, 61):
        x = round(x0 + k * per_s / 10)
        d.line((x, y1 - (6 if k % 10 == 0 else 3 if k % 5 == 0 else 1), x, y1), fill=RULE)
        if k % 10 == 0:
            d.text((x - 2, y1 + 3), f"{k // 10}", font=small, fill=PAPER)
    d.text((x1 + 6, y1 + 3), "s", font=small, fill=PAPER)
    # lamp light pooling over the desk and strip, a cool spill from the window
    im = light(im, 240, 60, 230, 170, "#3A2610", 0.75)
    im = light(im, 240, 36, 40, 18, "#6A5020", 0.8)
    im = light(im, 414, 60, 70, 80, "#18203A", 0.6)
    im.save(os.path.join(OUT, "lab_gramophone.png"))
    return {"strip": {"x0": x0, "x1": x1, "y0": y0, "y1": y1, "mid": mid, "seconds": 6.0, "px_per_s": per_s}}


def sprites():
    # a flour sack, tied at the neck
    s = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    d.ellipse((2, 5, 13, 15), fill="#C8B48A", outline="#5A4020")
    d.polygon([(5, 6), (10, 6), (9, 2), (6, 2)], fill="#C8B48A", outline="#5A4020")
    d.line((5, 5, 10, 5), fill="#5A4020")
    d.point([(6, 10), (9, 11), (7, 12)], fill="#86622E")
    s.save(os.path.join(OUT, "sack.png"))
    # the bedsheet: as the ghost (glowing, two holes for eyes), then just a sheet with pegs
    g = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    for f, (fill, edge) in enumerate(((GHOST, "#6A9AFF"), (SHEET, SHEET_D))):
        ox = f * 32
        d.line((ox, 2, ox + 31, 2), fill=WOOD_D)
        pts = [(ox + 4, 3), (ox + 28, 3), (ox + 29, 26), (ox + 25, 29), (ox + 21, 26), (ox + 16, 30), (ox + 11, 26),
               (ox + 7, 29), (ox + 3, 26)]
        d.polygon(pts, fill=fill, outline=edge)
        if f == 0:
            d.ellipse((ox + 10, 10, ox + 13, 14), fill=INK)
            d.ellipse((ox + 19, 10, ox + 22, 14), fill=INK)
        else:
            for px in (7, 16, 25):
                d.rectangle((ox + px, 1, ox + px + 1, 5), fill=WOOD_L)
    g.save(os.path.join(OUT, "sheet_ghost.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    import scene_manor as M
    district = {"width": M.W, "cu": M.CENTRE[0], "cv": M.CENTRE[1], "hotspots": M.HOTSPOTS,
                "clues": {"sheet": [M.BODY_X, 4, M.BODY_Z], "gramophone": [M.GRAM_X, 30, M.GRAM_Z],
                          "tower": [M.TOWER_X, 100, M.FRONT], "ghost": [272, 30, -70]},
                "balconies": {sid: [M.TOWER_X, hb, M.FRONT + 6] for sid, (hb, _) in zip(BALCONIES, M.BALCONIES)}}
    layout = {"district": district, "tower": lab_tower(), "gramophone": lab_gramophone(), "g": 9.8}
    sprites()
    with open(os.path.join(OUT, "fall_layout.json"), "w") as f:
        json.dump(layout, f, indent=1)
    print("ok", OUT)
