"""Acid Alley, the Acids-and-bases chapter, a bright afternoon. 720x270, scrolls horizontally.

A narrow market alley of tall painted houses, washing strung between them. Left to right: Citrine's cordial
stand under a striped awning; the little square with the Mayor's fountain and its koi, the crime scene;
Bicarb's bakery; Sudsy's laundry with sheets on the line.

build(glitch=True)   acids and bases are erased: the fountain runs a sickly orange, soap bubbles drift out of the
                     lemon crates, the pH sign is rubbed out
build(glitch=False)  after the case: the fountain glows neutral green again, the koi are gold, the sign is whole
Walkable cobbles: y = 0, z in [0, 30].
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light, gradient_sky
from src import sdf

(COBBLE, COBBLE_D, PLASTER1, PLASTER2, PLASTER3, PLASTER4, ROOF, WOOD, WINDOW, SHUTTER, AWN_Y, AWN_W, LEMON, STONE,
 WATER_G, WATER_O, KOI, SIGN, SIGN_INK, BRICK, SHEET1, SHEET2, SHEET3, ROPE, BUBBLE, FLOWER, LEAF, GHOST, METAL, FAR) = range(1, 31)

W, H = 720, 270
CENTRE = (0.0, 90.0)
HOTSPOTS = {"citrine": -260, "stage": -90, "bicarb": 110, "sudsy": 250}
FOUNT = (-90.0, -50.0)


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _decal(text, font, w, h):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    b = d.textbbox((0, 0), text, font=font)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=font, fill=255)
    return np.array(im) > 100


LAW_TEX = _decal("pH 7 = neutral", _font("arialbd.ttf", 30), 236, 36)
BREAD_TEX = _decal("BREAD", _font("arialbd.ttf", 20), 80, 24)
SOAP_TEX = _decal("LAUNDRY", _font("arialbd.ttf", 18), 104, 24)


def _tex(mask, p, x0, x1, ytop, ybot):
    hh, ww = mask.shape
    u = np.clip(((p[:, 0] - x0) / (x1 - x0) * (ww - 1)), 0, ww - 1).astype(int)
    v = np.clip(((ytop - p[:, 1]) / (ytop - ybot) * (hh - 1)), 0, hh - 1).astype(int)
    return mask[v, u]


def _put(d, mat, dd, mm):
    mat = np.where(dd < d, mm, mat)
    return np.minimum(d, dd), mat


def _hash(c, k=12.9898):
    return np.abs(np.sin(c * k) * 43758.5453) % 1.0


def materials():
    plaster = lambda ramp: dict(ramp=ramp, warm_tint=0.5, pattern=lambda p, n: 0.4 * np.sin(p[:, 0] * 0.7) * np.sin(p[:, 1] * 0.9), pattern_gain=0.06)
    return {
        COBBLE: dict(ramp=["#3A2E2A", "#54443C", "#6E5A4E", "#8A7262", "#A68C78", "#C2A890"], warm_tint=0.5,
                     pattern=lambda p, n: np.sin(np.floor((p[:, 0] + 2.5 * (np.floor((p[:, 2] + 600) / 5.0) % 2) + 600) / 5.0) * 7.3
                                                + np.floor((p[:, 2] + 600) / 5.0) * 3.1), pattern_gain=0.1,
                     sub=(lambda p: (p[:, 1] < 0.5) & ((np.abs(((p[:, 0] + 2.5 * (np.floor((p[:, 2] + 600) / 5.0) % 2) + 600) % 5.0) - 2.5) > 2.28)
                                                        | (np.abs(((p[:, 2] + 600) % 5.0) - 2.5) > 2.28)), COBBLE_D)),
        COBBLE_D: dict(ramp=["#1A1412", "#261E1A", "#342822"]),
        PLASTER1: plaster(["#5A3A2E", "#84553E", "#AE7650", "#D49A6A", "#ECBC8A"]),
        PLASTER2: plaster(["#2E4A4A", "#3E6664", "#548A84", "#70ACA2", "#94CCC0"]),
        PLASTER3: plaster(["#5A4A1E", "#86702C", "#B09A40", "#D6C060", "#EEDC8A"]),
        PLASTER4: plaster(["#5A2E44", "#844260", "#AE5C80", "#D47AA0", "#EC9EBE"]),
        ROOF: dict(ramp=["#2A100C", "#461A14", "#66261C", "#8A3426", "#AE4632"],
                   pattern=lambda p, n: 0.7 * (np.abs(((p[:, 1] + 300) % 3.0) - 1.5) > 1.1), pattern_gain=0.14),
        WOOD: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E"],
                   pattern=lambda p, n: 0.45 * np.sin(p[:, 1] * 1.3 + p[:, 0] * 0.2), pattern_gain=0.12),
        WINDOW: dict(ramp=["#1A2440", "#24345A", "#34507E", "#4A6CA0", "#7096C4"], gloss=40, spec="#FFF4D8"),
        SHUTTER: dict(ramp=["#14301E", "#1E4A2C", "#2A6640", "#3A8456"]),
        AWN_Y: dict(ramp=["#7A5A08", "#B8880E", "#E6B820", "#F8DA4A"]),
        AWN_W: dict(ramp=["#8E8A86", "#B8B4AE", "#DCD8D0", "#F4F0E6"]),
        LEMON: dict(ramp=["#7A5A08", "#B8880E", "#E6B820", "#F8DA4A", "#FFF0A0"], gloss=20, spec="#FFFCE0"),
        STONE: dict(ramp=["#3E3A40", "#58525A", "#746C76", "#928A94", "#B2AAB4", "#D0C8D2"], warm_tint=0.4),
        WATER_G: dict(ramp=["#0E3A20", "#16582E", "#22783E", "#349A52", "#4EBC6A"], gloss=30, spec="#E6FFF0", emissive=False,
                      pattern=lambda p, n: 0.6 * np.sin(p[:, 0] * 0.5 + np.sin(p[:, 2] * 0.6) * 2.0), pattern_gain=0.14),
        WATER_O: dict(ramp=["#4A1E08", "#7A3410", "#B0541C", "#DA7A2E", "#F4A04A"], gloss=30, spec="#FFF0E0",
                      pattern=lambda p, n: 0.6 * np.sin(p[:, 0] * 0.5 + np.sin(p[:, 2] * 0.6) * 2.0), pattern_gain=0.14),
        KOI: dict(ramp=["#8A4A08", "#C87010", "#F09A20", "#FFC860"]),
        SIGN: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF"]),
        SIGN_INK: dict(ramp=["#07090F", "#0E121D", "#161C2C", "#20283C"]),
        BRICK: dict(ramp=["#3A1A12", "#56281C", "#763828", "#964A34", "#B46044"],
                    pattern=lambda p, n: 0.7 * (np.abs(((p[:, 1] + 300) % 4.0) - 2.0) > 1.6), pattern_gain=0.2),
        SHEET1: dict(ramp=["#8E8A86", "#B8B4AE", "#DCD8D0", "#F4F0E6"]),
        SHEET2: dict(ramp=["#2E4A7A", "#3E64A0", "#5682C4", "#78A4E0"]),
        SHEET3: dict(ramp=["#7A2A4A", "#B04672", "#D86C98", "#F29ABC"]),
        ROPE: dict(ramp=["#3A2614", "#55391E", "#73502B"]),
        BUBBLE: dict(ramp=["#9AB8DC", "#C8DEF2", "#EAF4FF", "#FFFFFF"], gloss=50, spec="#FFFFFF"),
        FLOWER: dict(ramp=["#8E1A14", "#C9302A", "#EE5A4C", "#FF8A78"]),
        LEAF: dict(ramp=["#17421F", "#22602C", "#30823C", "#48A452"]),
        GHOST: dict(ramp=["#4A3E7A", "#62549A", "#7E70B8", "#9C8ED0"], emissive=True),
        METAL: dict(ramp=["#0A0C10", "#15191F", "#222831", "#323A46", "#47515F", "#626E7F"], gloss=24, spec="#C8D4E2"),
        FAR: dict(ramp=["#7A8AAE", "#8E9CBE", "#A2B0CE", "#B8C4DC"], dither=0.3),
    }


PLASTERS = (PLASTER1, PLASTER2, PLASTER3, PLASTER4)


def build(glitch=True):
    objs = []
    objs.append(Obj(lambda p: (p[:, 1], COBBLE), (-400, -2, -340), (400, 0.2, 260), "ground"))

    # the far rooftops and a clock tower, hazy
    def far(p):
        cell = np.round(p[:, 0] / 22.0)
        h = 40 + 30 * _hash(cell)
        q = p - np.stack([cell * 22.0, np.zeros(len(p)), np.full(len(p), -280.0)], 1)
        body = np.maximum.reduce([np.abs(q[:, 0]) - 10.0, np.abs(q[:, 2]) - 8.0, q[:, 1] - h, -q[:, 1]])
        roof = np.maximum(np.abs(q[:, 0]) * 0.9 + (q[:, 1] - h - 8), np.maximum(h - q[:, 1], np.abs(q[:, 2]) - 9)) * 0.7
        tower = np.maximum(sdf.box(p - [60, 45, -285], (8, 45, 8), 0.5), -1e9)
        spire = np.maximum(np.maximum(np.abs(p[:, 0] - 60), np.abs(p[:, 2] + 285)) * 1.8 + (p[:, 1] - 106), 90 - p[:, 1]) * 0.5
        return np.minimum.reduce([body, roof, tower, spire]), FAR
    objs.append(Obj(far, (-420, -1, -300), (420, 110, -260), "far"))

    # the Mayor's hall behind the fountain: a pale front, a balcony, a flag
    def hall(p):
        x0, z0 = FOUNT[0], -150.0
        body = sdf.box(p - [x0, 32, z0], (34, 32, 14), 0.8)
        d, mat = body, np.full(len(p), STONE)
        pedi = np.maximum(np.abs(p[:, 0] - x0) * 0.5 + (p[:, 1] - 80), np.maximum(64 - p[:, 1], np.abs(p[:, 2] - z0) - 15)) * 0.85
        d, mat = _put(d, mat, pedi, ROOF)
        for wx in (-22.0, -8.0, 8.0, 22.0):
            for wy in (22.0, 46.0):
                d, mat = _put(d, mat, sdf.box(p - [x0 + wx, wy, z0 + 14.2], (3.4, 6.0, 0.6), 0.4), WINDOW)
        bal = sdf.box(p - [x0, 38, z0 + 17], (12, 1.0, 3.4), 0.4)
        rail = np.maximum(sdf.box(p - [x0, 41, z0 + 20], (12, 2.6, 0.4), 0.2), -(np.abs(((p[:, 0] + 600) % 2.0) - 1.0) - 0.6) * 4)
        d, mat = _put(d, mat, np.minimum(bal, rail), METAL)
        door = sdf.box(p - [x0, 11, z0 + 14.2], (6, 11, 0.6), 1.0)
        d, mat = _put(d, mat, door, WOOD)
        d, mat = _put(d, mat, sdf.capsule(p, (x0, 80, z0), (x0, 98, z0), 0.5), METAL)
        flag = np.maximum.reduce([np.abs(p[:, 2] - z0) - 0.4, x0 - p[:, 0], p[:, 0] - x0 - 10, np.abs(p[:, 1] - 94) - 3.4])
        d, mat = _put(d, mat, flag, SHEET2)
        return d, mat
    objs.append(Obj(hall, (FOUNT[0] - 40, -1, -168), (FOUNT[0] + 40, 100, -130), "hall"))

    # the terrace of tall painted houses along the back of the alley
    def terrace(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), PLASTER1)
        xs = np.arange(-380, 400, 34.0)
        for k, x in enumerate(xs):
            if abs(x - FOUNT[0]) < 40:
                continue
            h = 62 + 24 * _hash(x)
            pm = PLASTERS[k % 4]
            body = sdf.box(p - [x, h / 2, -128], (16.5, h / 2, 14), 0.6)
            d, mat = _put(d, mat, body, pm)
            roof = np.maximum(np.abs(p[:, 0] - x) * 0.8 + (p[:, 1] - h - 12), np.maximum(h - p[:, 1], np.abs(p[:, 2] + 128) - 15)) * 0.75
            d, mat = _put(d, mat, roof, ROOF)
            for wy in np.arange(28, h - 6, 16):
                for wx in (-7.0, 7.0):
                    win = sdf.box(p - [x + wx, wy, -113.6], (3.0, 4.4, 0.6), 0.3)
                    d, mat = _put(d, mat, win, WINDOW)
                    for sx in (-1, 1):
                        d, mat = _put(d, mat, sdf.box(p - [x + wx + sx * 4.2, wy, -113.4], (1.0, 4.4, 0.6), 0.2), SHUTTER)
                    box = sdf.box(p - [x + wx, wy - 5.4, -112.6], (3.4, 0.9, 1.4), 0.3)
                    d, mat = _put(d, mat, box, WOOD)
                    for fx in (-2.0, 0.0, 2.0):
                        d, mat = _put(d, mat, sdf.sphere(p, (x + wx + fx, wy - 4.2, -112.2), 0.9), FLOWER if (k + int(wy)) % 2 else LEAF)
        return d, mat
    objs.append(Obj(terrace, (-400, -1, -145), (400, 110, -110), "terrace"))

    # Citrine's cordial stand
    def stand(p):
        x0, z0 = -262.0, -78.0
        d, mat = np.full(len(p), 1e9), np.full(len(p), WOOD)
        counter = sdf.box(p - [x0, 7, z0], (20, 7, 6), 0.5)
        d, mat = _put(d, mat, counter, WOOD)
        for x in (x0 - 19, x0 + 19):
            d, mat = _put(d, mat, sdf.box(p - [x, 20, z0 - 4], (1.0, 20, 1.0), 0.3), WOOD)
        aw = p - [x0, 38, z0 + 2]
        awning = np.maximum.reduce([np.abs(aw[:, 0]) - 23, np.abs(aw[:, 1] + aw[:, 2] * 0.5) - 0.8, aw[:, 2] - 9, -aw[:, 2] - 6])
        stripe = np.abs(((p[:, 0] - x0 + 600) % 8.0) - 4.0) > 2.0
        d, mat = _put(d, mat, awning * 0.8, np.where(stripe, AWN_Y, AWN_W))
        for k in range(3):
            jar = sdf.cylinder_y(p - [x0 - 10 + 10 * k, 17, z0 + 2], 2.6, 3.0, 0.8)
            d, mat = _put(d, mat, jar, LEMON)
        crate = sdf.box(p - [x0 + 28, 4, z0 + 8], (6, 4, 5), 0.4)
        d, mat = _put(d, mat, crate, WOOD)
        rng = np.random.default_rng(3)
        for _ in range(7):
            c = (x0 + 28 + rng.uniform(-4.5, 4.5), 8.6 + rng.uniform(0, 1.4), z0 + 8 + rng.uniform(-3.5, 3.5))
            d, mat = _put(d, mat, sdf.ellipsoid(p, c, (1.8, 1.5, 1.5)), LEMON)
        sign = sdf.ellipsoid(p, (x0, 46, z0 - 2), (9.0, 6.4, 1.6))
        d, mat = _put(d, mat, sign, LEMON)
        if glitch:
            for k in range(5):
                d, mat = _put(d, mat, sdf.sphere(p, (x0 + 26 + 3 * np.sin(k), 14 + 5 * k, z0 + 8), 1.6 - 0.15 * k), BUBBLE)
        return d, mat
    objs.append(Obj(stand, (-288, -1, -86), (-226, 56, -64), "stand"))

    # the Mayor's fountain in its little square
    fx, fz = FOUNT

    def fountain(p):
        r = np.hypot(p[:, 0] - fx, (p[:, 2] - fz) * 1.0)
        basin = np.maximum(np.abs(r - 22.0) - 2.0, np.abs(p[:, 1] - 4.0) - 4.0)
        d, mat = basin, np.full(len(p), STONE)
        water = np.maximum(r - 20.4, np.abs(p[:, 1] - 6.2) - 0.4)
        d, mat = _put(d, mat, water, WATER_O if glitch else WATER_G)
        col = sdf.cylinder_y(p - [fx, 14, fz], 3.0, 12.0, 0.6)
        tier = sdf.cylinder_y(p - [fx, 18, fz], 9.0, 1.2, 0.8)
        tier2 = sdf.cylinder_y(p - [fx, 28, fz], 5.0, 1.0, 0.6)
        d, mat = _put(d, mat, np.minimum(np.minimum(col, tier), tier2), STONE)
        bowl_w = np.maximum(sdf.cylinder_y(p - [fx, 19.0, fz], 8.0, 0.4, 0.2), -1e9)
        d, mat = _put(d, mat, bowl_w, WATER_O if glitch else WATER_G)
        # a statue on top: a flask pouring
        flask = sdf.round_cone(p, (fx, 31, fz), (fx, 38, fz), 4.0, 1.4)
        neck = sdf.cylinder_y(p - [fx, 40, fz], 1.4, 2.0, 0.3)
        d, mat = _put(d, mat, np.minimum(flask, neck), METAL)
        for a in np.linspace(0, 2 * np.pi, 6, endpoint=False):
            jet = sdf.capsule(p, (fx + 2 * np.cos(a), 29.5, fz + 2 * np.sin(a)), (fx + 7 * np.cos(a), 20.5, fz + 7 * np.sin(a)), 0.5)
            d, mat = _put(d, mat, jet, WATER_O if glitch else WATER_G)
        # koi in the basin
        for k, a in enumerate((0.5, 2.3, 4.0, 5.4)):
            c = np.array([fx + 15 * np.cos(a), 6.6, fz + 15 * np.sin(a)])
            kq = (p - c) @ sdf.rot_y(a + np.pi / 2)
            koi = np.minimum(sdf.ellipsoid(kq, (0, 0, 0), (2.6, 0.7, 1.0)), sdf.ellipsoid(kq, (-2.8, 0, 0), (1.2, 0.5, 1.2)))
            d, mat = _put(d, mat, koi, KOI)
        return d, mat
    objs.append(Obj(fountain, (fx - 26, -1, fz - 26), (fx + 26, 44, fz + 26), "fountain"))

    # Bicarb's bakery
    def bakery(p):
        x0, z0 = 112.0, -84.0
        body = sdf.box(p - [x0, 22, z0], (24, 22, 12), 0.8)
        d, mat = body, np.full(len(p), BRICK)
        roof = np.maximum(np.abs(p[:, 0] - x0) * 0.6 + (p[:, 1] - 56), np.maximum(44 - p[:, 1], np.abs(p[:, 2] - z0) - 15)) * 0.8
        d, mat = _put(d, mat, roof, ROOF)
        chim = sdf.box(p - [x0 + 14, 56, z0 - 4], (3, 10, 3), 0.4)
        d, mat = _put(d, mat, chim, BRICK)
        win = sdf.box(p - [x0 - 9, 15, z0 + 12.2], (9, 8, 0.6), 0.6)
        d, mat = _put(d, mat, win, WINDOW)
        for k in range(3):
            loaf = sdf.ellipsoid(p, (x0 - 14 + 5 * k, 9.4, z0 + 13.2), (2.2, 1.4, 1.4))
            d, mat = _put(d, mat, loaf, PLASTER1)
        door = sdf.box(p - [x0 + 12, 10, z0 + 12.2], (5, 10, 0.6), 0.6)
        d, mat = _put(d, mat, door, WOOD)
        sign = sdf.box(p - [x0, 34, z0 + 12.6], (16, 5, 0.6), 0.3)
        d, mat = _put(d, mat, sign, np.where(_tex(BREAD_TEX, p, x0 - 15, x0 + 15, 38.5, 29.5) & (p[:, 2] > z0 + 13), SIGN_INK, SIGN))
        return d, mat
    objs.append(Obj(bakery, (84, -1, -100), (140, 68, -70), "bakery"))

    # Sudsy's laundry, and sheets strung across to the next house
    def laundry(p):
        x0, z0 = 256.0, -84.0
        body = sdf.box(p - [x0, 20, z0], (22, 20, 12), 0.8)
        d, mat = body, np.full(len(p), PLASTER2)
        roof = np.maximum(np.abs(p[:, 0] - x0) * 0.6 + (p[:, 1] - 52), np.maximum(40 - p[:, 1], np.abs(p[:, 2] - z0) - 15)) * 0.8
        d, mat = _put(d, mat, roof, ROOF)
        win = sdf.box(p - [x0 + 8, 16, z0 + 12.2], (7, 7, 0.6), 0.6)
        d, mat = _put(d, mat, win, WINDOW)
        door = sdf.box(p - [x0 - 10, 10, z0 + 12.2], (5, 10, 0.6), 0.6)
        d, mat = _put(d, mat, door, WOOD)
        sign = sdf.box(p - [x0, 32, z0 + 12.6], (21, 6, 0.6), 0.3)
        d, mat = _put(d, mat, sign, np.where(_tex(SOAP_TEX, p, x0 - 20, x0 + 20, 37.5, 26.5) & (p[:, 2] > z0 + 13), SIGN_INK, SIGN))
        a, b = np.array([x0 - 22, 44.0, z0 + 12]), np.array([x0 - 96, 50.0, z0 + 12])
        t = np.clip(((p - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
        sag = a + (b - a) * t[:, None] - np.array([0, 5.0, 0]) * (4 * t * (1 - t))[:, None]
        d, mat = _put(d, mat, np.linalg.norm(p - sag, axis=1) - 0.35, ROPE)
        for k, m in enumerate((SHEET1, SHEET2, SHEET3, SHEET1)):
            tk = 0.15 + 0.22 * k
            c = a + (b - a) * tk - np.array([0, 5.0 * 4 * tk * (1 - tk), 0])
            sheet = sdf.box(p - (c - [0, 6.0, 0]), (6.0, 6.0, 0.3), 0.2)
            d, mat = _put(d, mat, sheet, m)
        for k in range(6):
            d, mat = _put(d, mat, sdf.sphere(p, (x0 + 18 + 2 * np.sin(k * 1.7), 6 + 6 * k, z0 + 14), 1.8 - 0.2 * k), BUBBLE)
        return d, mat
    objs.append(Obj(laundry, (150, -1, -100), (282, 64, -68), "laundry"))

    # the pH sign at the edge of the square
    def phsign(p):
        x0, z0 = 10.0, -40.0
        d, mat = sdf.capsule(p, (x0, 0, z0), (x0, 22, z0), 0.9), np.full(len(p), METAL)
        bd = sdf.box(p - [x0, 31, z0], (40, 10, 0.9), 0.4)
        ink = (p[:, 2] > z0 + 0.7) & _tex(LAW_TEX, p, x0 - 38, x0 + 38, 40, 22)
        rub = p[:, 0] > x0 + 2 + 3 * np.sin(p[:, 1])
        d, mat = _put(d, mat, bd, np.where(ink, np.where(rub & glitch, GHOST, SIGN_INK), SIGN))
        return d, mat
    objs.append(Obj(phsign, (-32, -1, -44), (52, 44, -36), "phsign"))

    sky = gradient_sky(W, H, "#4C86C8", "#F4D6A8", glow=(140, 50, 300, "#FFF0C8"))
    lights = [Light((-320, 220, 240), "#FFE0B0", 1.2, 1100),
              Light((300, 160, 160), "#A8C8F0", 0.4, 800, shadow=False)]
    return dict(world=World(objs), materials=materials(), width=W, height=H, centre=CENTRE,
                lights=lights, key=0.55, ambient=0.18, top=150.0, ss=2, steps=170, sky=sky,
                bloom=[(GHOST, "#7E70B8", 6, 0.35)])
