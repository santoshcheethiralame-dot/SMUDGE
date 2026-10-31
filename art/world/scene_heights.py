"""Lumen Heights, the Heights-and-distances chapter, late on a golden afternoon. 720x270, scrolls horizontally.

A hill town of tall things and long shadows. Left to right: Ladder Lane with Lumen's street lamps and a ladder
up a narrow townhouse; the plaza, where the sundial's Golden Gnomon is missing, under the town hall clock; the
law billboard; Vane's Weathercock Spire; the Gazette kiosk; Sola's Sunflower Mill in its field.

build(glitch=True)   the law is erased: shadows fall toward the sun, lost shadows drift over the plaza,
                     the billboard's tan rubbed out, the gnomon gone
build(glitch=False)  after the case: the gnomon back on the dial, shadows where they belong
Walkable ground: y = 0, z in [0, 30]. The sun is low on the right, so real shadows run left.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light, gradient_sky, stars  # noqa: F401
from src import sdf

(PAVE, PAVE_D, GRASS, STONE, STONE_D, ROOF, WOOD, IRON, LAMP, WINDOW, GOLD, BRONZE, SIGN, SIGN_INK, ERASE, GHOST,
 SHADE, COPPER, VERDI, PETAL, SEEDH, LEAF, WHITE, CLOCK, FAR, HILL, SUN, RED, PAPER) = range(1, 30)

W, H = 720, 270
CENTRE = (0.0, 90.0)
HOTSPOTS = {"lumen": -260, "stage": -90, "vane": 110, "sola": 250}
DIAL = (-90.0, -38.0)
SUNPOS = np.array([520.0, 150.0, 60.0])


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _decal(text, font, w, h):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    b = d.textbbox((0, 0), text, font=font)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=font, fill=255)
    return np.array(im) > 100


LAW_TEX = _decal("tan\u03b8 = h/s", _font("arialbd.ttf", 30), 168, 40)
GAZ_TEX = _decal("GAZETTE", _font("arialbd.ttf", 18), 84, 22)


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
    return {
        PAVE: dict(ramp=["#4A3A30", "#6A5444", "#8C705A", "#AE8E72", "#CCAC8A", "#E4C8A2", "#F4DEB8"], warm_tint=0.6,
                   pattern=lambda p, n: 0.4 * np.sin(p[:, 0] * 0.9) * np.sin(p[:, 2] * 1.1), pattern_gain=0.1,
                   sub=(lambda p: (p[:, 1] < 0.5) & ((np.abs(((p[:, 0] + 3.0 * (np.floor((p[:, 2] + 600) / 5.0) % 2) + 600) % 7.0) - 3.5) > 3.15)
                                                       | (np.abs(((p[:, 2] + 600) % 5.0) - 2.5) > 2.2)), PAVE_D)),
        PAVE_D: dict(ramp=["#2E241E", "#40322A", "#544236", "#6A5444"]),
        GRASS: dict(ramp=["#1E3418", "#2C4A20", "#3E642A", "#567E34", "#729A40", "#90B44E"], warm_tint=0.6,
                    pattern=lambda p, n: 0.7 * np.sin(p[:, 0] * 1.9 + p[:, 2] * 1.3), pattern_gain=0.12),
        STONE: dict(ramp=["#3A2E2E", "#56443E", "#74604E", "#94785E", "#B49472", "#D0B088", "#E8CCA4"], warm_tint=0.55,
                    pattern=lambda p, n: 0.6 * ((np.abs(((p[:, 1] + 300) % 7.0) - 3.5) > 3.0) | (np.abs(((p[:, 0] + p[:, 2] + 300) % 11.0) - 5.5) > 5.0)), pattern_gain=0.16),
        STONE_D: dict(ramp=["#241C1E", "#382C2C", "#4E3E3A", "#66524A"]),
        ROOF: dict(ramp=["#2A0E0C", "#461612", "#68221A", "#8C3022", "#B04430", "#CC6040"], warm_tint=0.5,
                   pattern=lambda p, n: 0.7 * (np.abs(((p[:, 1] + 300) % 3.0) - 1.5) > 1.1), pattern_gain=0.14),
        WOOD: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E", "#CF8A42"],
                   pattern=lambda p, n: 0.45 * np.sin(p[:, 1] * 1.3 + p[:, 0] * 0.2), pattern_gain=0.12),
        IRON: dict(ramp=["#0A1210", "#132220", "#1E3430", "#2C4A44", "#3E625A"], gloss=14, spec="#9FD8C8"),
        LAMP: dict(ramp=["#F2B44C", "#FFD27A", "#FFE9B0"], emissive=True),
        WINDOW: dict(ramp=["#1A2440", "#24345A", "#34507E", "#4A6CA0", "#7096C4"], gloss=40, spec="#FFF4D8"),
        GOLD: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848", "#FFE08A", "#FFF4C8"], gloss=26, spec="#FFFFFF"),
        BRONZE: dict(ramp=["#2A1A0A", "#46301A", "#6A4A2A", "#8E6A3E", "#B08A52"], gloss=18, spec="#FFE8C0"),
        SIGN: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF"]),
        SIGN_INK: dict(ramp=["#07090F", "#0E121D", "#161C2C", "#20283C"]),
        ERASE: dict(ramp=["#8C5A6A", "#B07A8A", "#D29EAC", "#EBC0C8"]),
        GHOST: dict(ramp=["#2A2048", "#3A2E62", "#4C3E7E", "#62549A"], emissive=True),
        SHADE: dict(ramp=["#1E1830", "#28203E", "#32284C"], emissive=True),
        COPPER: dict(ramp=["#4A1E0C", "#7A3416", "#AA5424", "#D47A3C", "#F0A062"], gloss=20, spec="#FFE2C8"),
        VERDI: dict(ramp=["#123A34", "#1E5A4E", "#2E7E6A", "#4AA48A", "#7CCCB0"], gloss=14, spec="#E0FFF4"),
        PETAL: dict(ramp=["#7A5208", "#B8800E", "#E8B420", "#F8D44A", "#FFEC96"]),
        SEEDH: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022"]),
        LEAF: dict(ramp=["#0E2A14", "#17421F", "#22602C", "#30823C", "#48A452"]),
        WHITE: dict(ramp=["#6A6458", "#8E887A", "#B4AE9E", "#D8D2C2", "#F2EEE2"], warm_tint=0.5),
        CLOCK: dict(ramp=["#B4AE9E", "#D8D2C2", "#F2EEE2", "#FFFFFF"]),
        FAR: dict(ramp=["#6A6478", "#7C7488", "#908698", "#A498A6", "#B8AAB2", "#CCBEBE"], dither=0.3, warm_tint=0.35),
        HILL: dict(ramp=["#3A4A3A", "#4A5E44", "#5E7450", "#748A5C", "#8EA06A"], dither=0.3, warm_tint=0.5),
        SUN: dict(ramp=["#FFB050", "#FFD07A", "#FFF0C0"], emissive=True),
        RED: dict(ramp=["#3A0907", "#62110D", "#8E1A14", "#B8251C", "#DE3B2E", "#F26654"]),
        PAPER: dict(ramp=["#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF"]),
    }


def build(glitch=True):
    objs = []

    def ground(p):
        plaza = np.hypot(p[:, 0] - DIAL[0], (p[:, 2] - DIAL[1]) * 1.2) < 66
        road = (p[:, 2] > -14) & (p[:, 2] < 44)
        paths = (np.abs(p[:, 0] - HOTSPOTS["lumen"]) < 12) | (np.abs(p[:, 0] - 110.0) < 10) | (np.abs(p[:, 0] - 268.0) < 8)
        paths &= (p[:, 2] > -110) & (p[:, 2] < 0)
        mat = np.where(plaza | road | paths, PAVE, GRASS)
        ring = plaza & ~road & (np.abs(np.hypot(p[:, 0] - DIAL[0], p[:, 2] - DIAL[1]) % 12.0 - 6.0) > 5.4)
        mat = np.where(ring, PAVE_D, mat)
        kerb = (np.abs(p[:, 2] + 14.5) < 1.2) | (np.abs(p[:, 2] - 44.5) < 1.2)
        mat = np.where(kerb & ~plaza, STONE, mat)
        return p[:, 1], mat
    objs.append(Obj(ground, (-400, -2, -340), (400, 0.2, 260), "ground"))

    # far hills and the old town stacked up them, warm in the low sun
    def far(p):
        hill = p[:, 1] - (30 + 22 * np.sin(p[:, 0] * 0.011 + 1.2) + 9 * np.sin(p[:, 0] * 0.037))
        hill = np.maximum(hill * 0.7, np.abs(p[:, 2] + 300) - 30)
        cell = np.round(p[:, 0] / 18.0)
        hgt = 30 + 22 * np.sin(cell * 0.2 + 1.2) + 9 * np.sin(cell * 0.66) - 2 + 14 * _hash(cell) ** 1.6
        hgt = np.where(_hash(cell, 78.233) < 0.3, -40.0, hgt)
        hw = 5.0 + 3.0 * _hash(cell, 3.7)
        q = p - np.stack([cell * 18.0 + 3.0 * (_hash(cell, 9.1) - 0.5), np.zeros(len(p)), np.full(len(p), -262.0)], 1)
        tw = np.maximum.reduce([np.abs(q[:, 0]) - hw, np.abs(q[:, 2]) - 6, q[:, 1] - hgt, -q[:, 1]])
        cap = np.maximum(np.abs(q[:, 0]) * 1.3 + (q[:, 1] - hgt - hw * 1.2), np.maximum(hgt - q[:, 1], np.abs(q[:, 2]) - 7)) * 0.6
        d, mat = hill, np.full(len(p), HILL)
        d, mat = _put(d, mat, tw, FAR)
        d, mat = _put(d, mat, cap, ROOF)
        win = (np.abs(((q[:, 1] + 300) % 8.0) - 4.0) < 1.2) & (np.abs(q[:, 0]) < 2.0) & (q[:, 2] > 5.5) & (q[:, 1] < hgt - 4)
        mat = np.where(win & (mat == FAR), STONE_D, mat)
        return d, mat
    objs.append(Obj(far, (-420, -1, -335), (420, 120, -250), "far"))
    objs.append(Obj(lambda p: (sdf.sphere(p, (300, 78, -340), 26.0), SUN), (270, 50, -370), (330, 106, -310), "sun"))

    # Ladder Lane: a tall narrow townhouse, a ladder up its front, Lumen's lamps along the kerb
    def lane(p):
        x0 = -275.0
        d, mat = np.full(len(p), 1e9), np.full(len(p), STONE)
        for bx, w, h, z in ((x0, 17, 92, -112), (x0 - 40, 14, 66, -118), (x0 + 42, 15, 74, -116)):
            body = sdf.box(p - [bx, h / 2, z], (w, h / 2, 12), 0.8)
            roof = np.maximum(np.abs(p[:, 0] - bx) * 1.1 + (p[:, 1] - h - 16), np.maximum(h - p[:, 1], np.abs(p[:, 2] - z) - 13)) * 0.66
            d, mat = _put(d, mat, body, STONE)
            d, mat = _put(d, mat, roof, ROOF)
            for wy in np.arange(14, h - 8, 16):
                for wx in (-w * 0.45, w * 0.45):
                    win = sdf.box(p - [bx + wx, wy, z + 12.2], (2.8, 4.4, 0.6), 0.3)
                    d, mat = _put(d, mat, win, WINDOW)
        # the ladder up the tall one
        lq = (p - [x0 + 4, 0, -98.0]) @ sdf.rot_z(-0.16)
        for sx in (-4.0, 4.0):
            d, mat = _put(d, mat, sdf.capsule(lq, (sx, 0, 0), (sx, 70, 0), 0.8), WOOD)
        rung = np.maximum(np.abs(lq[:, 0]) - 4.0, np.maximum(np.abs(((lq[:, 1] + 300) % 6.0) - 3.0) - 0.5, np.abs(lq[:, 2]) - 0.6))
        d, mat = _put(d, mat, np.maximum(rung, np.maximum(-lq[:, 1], lq[:, 1] - 70)), WOOD)
        # street lamps
        for lx in (-320.0, -262.0, -204.0):
            post = np.minimum(sdf.capsule(p, (lx, 0, -62.0), (lx, 30, -62.0), 1.2), sdf.cylinder_y(p - [lx, 2.0, -62.0], 3.0, 2.0, 0.5))
            head = sdf.box(p - [lx, 34.0, -62.0], (3.0, 3.6, 3.0), 0.6)
            cap = np.maximum(np.maximum(np.abs(p[:, 0] - lx), np.abs(p[:, 2] + 62)) * 1.3 + (p[:, 1] - 42.5), 37.5 - p[:, 1]) * 0.6
            d, mat = _put(d, mat, post, IRON)
            d, mat = _put(d, mat, head, LAMP)
            d, mat = _put(d, mat, cap, IRON)
        sign = sdf.box(p - [-233.0, 24.0, -61.0], (11.0, 3.0, 0.6), 0.3)
        d, mat = _put(d, mat, sign, np.where(np.abs(p[:, 1] - 24.0) < 0.6, WHITE, SIGN_INK))
        d, mat = _put(d, mat, sdf.capsule(p, (-233.0, 0, -62.0), (-233.0, 21.0, -62.0), 0.7), IRON)
        return d, mat
    objs.append(Obj(lane, (-345, -1, -132), (-180, 118, -56), "lane"))

    # the plaza: the sundial on its pedestal; the town hall and its clock behind
    dx, dz = DIAL

    def plaza(p):
        ped = sdf.cylinder_y(p - [dx, 5.0, dz], 5.4, 5.0, 0.8)
        foot = sdf.cylinder_y(p - [dx, 1.0, dz], 8.0, 1.0, 0.5)
        dial = sdf.cylinder_y(p - [dx, 11.0, dz], 15.0, 1.2, 0.6)
        d, mat = np.minimum(ped, foot), np.full(len(p), STONE)
        r = np.hypot(p[:, 0] - dx, p[:, 2] - dz)
        a = np.arctan2(p[:, 2] - dz, p[:, 0] - dx)
        marks = (r > 10.5) & (r < 14.0) & (np.abs(((a * 12 / (2 * np.pi)) % 1.0) - 0.5) > 0.42)
        d, mat = _put(d, mat, dial, np.where(marks, BRONZE, np.where(r > 14.2, BRONZE, WHITE)))
        if not glitch:
            gq = p - [dx, 12.2, dz]
            gnomon = np.maximum.reduce([np.abs(gq[:, 2]) - 0.7, -gq[:, 1], gq[:, 1] - (gq[:, 0] + 9.0) * 0.9, gq[:, 0] - 9.0, -gq[:, 0] - 9.0])
            d, mat = _put(d, mat, gnomon, GOLD)
        else:
            slot = sdf.box(p - [dx, 12.3, dz], (9.0, 0.3, 0.9))
            d, mat = _put(d, mat, slot, STONE_D)
        # the town hall: a broad front, a clock tower with its face to the plaza
        hx, hz = -50.0, -150.0
        hall = sdf.box(p - [hx, 26, hz], (48, 26, 14), 1.0)
        cols = np.abs(((p[:, 0] - hx + 600) % 12.0) - 6.0) < 1.6
        d, mat = _put(d, mat, hall, np.where(cols & (p[:, 2] > hz + 13.5) & (p[:, 1] < 46), WHITE, STONE))
        pedi = np.maximum(np.abs(p[:, 0] - hx) * 0.45 + (p[:, 1] - 66), np.maximum(52 - p[:, 1], np.abs(p[:, 2] - hz) - 15)) * 0.8
        d, mat = _put(d, mat, pedi, ROOF)
        tower = sdf.box(p - [hx, 82, hz - 2], (11, 30, 11), 0.8)
        d, mat = _put(d, mat, tower, STONE)
        spire = np.maximum(np.maximum(np.abs(p[:, 0] - hx), np.abs(p[:, 2] - hz + 2)) * 2.2 + (p[:, 1] - 136), 112 - p[:, 1]) * 0.42
        d, mat = _put(d, mat, spire, ROOF)
        cq = p - [hx, 92, hz + 9.6]
        face = sdf.cylinder_y(cq @ sdf.rot_x(np.pi / 2), 8.4, 0.8, 0.3)
        rr, aa = np.hypot(cq[:, 0], cq[:, 1]), np.arctan2(cq[:, 0], cq[:, 1])
        ticks = (rr > 6.6) & (rr < 8.0) & (np.abs(((aa * 6 / np.pi) % 1.0) - 0.5) > 0.4)
        hour = (np.abs(cq[:, 0] * np.cos(2.1) - cq[:, 1] * np.sin(2.1)) < 0.7) & (cq[:, 0] * np.sin(2.1) + cq[:, 1] * np.cos(2.1) > -0.5) & (rr < 4.6)
        minute = (np.abs(cq[:, 0]) < 0.6) & (cq[:, 1] > -0.5) & (rr < 6.6)
        d, mat = _put(d, mat, face, np.where(ticks | hour | minute, SIGN_INK, CLOCK))
        d, mat = _put(d, mat, sdf.torus_y(cq @ sdf.rot_x(np.pi / 2), 8.6, 0.8), GOLD)
        for wx in (-30.0, -16.0, 16.0, 30.0):
            d, mat = _put(d, mat, sdf.box(p - [hx + wx, 30, hz + 14.2], (3.0, 7.0, 0.6), 0.4), WINDOW)
        door = sdf.box(p - [hx, 10, hz + 14.2], (6.0, 10.0, 0.6), 0.6)
        d, mat = _put(d, mat, door, WOOD)
        return d, mat
    objs.append(Obj(plaza, (-125, -1, -170), (10, 140, -20), "plaza"))

    # the law billboard by the plaza
    def billboard(p):
        x0, z0 = 32.0, -96.0
        d, mat = np.full(len(p), 1e9), np.full(len(p), WOOD)
        for x in (x0 - 32, x0 + 32):
            d, mat = _put(d, mat, sdf.box(p - [x, 20, z0 - 1], (1.6, 20, 1.6), 0.4), WOOD)
        board = sdf.box(p - [x0, 44, z0], (40, 11, 1.2), 0.5)
        ink = (p[:, 2] > z0 + 1.0) & _tex(LAW_TEX, p, x0 - 38, x0 + 38, 53, 35)
        rub = (p[:, 0] < x0 - 8 + 4 * np.sin(p[:, 1] * 0.8))
        face = np.where(ink, np.where(rub & glitch, ERASE, SIGN_INK), SIGN)
        if glitch:
            face = np.where((~ink) & rub & (((p[:, 0] * 3 + p[:, 1] * 5).astype(int) % 7) == 0), ERASE, face)
        d, mat = _put(d, mat, board, face)
        return d, mat
    objs.append(Obj(billboard, (-12, -1, -100), (76, 58, -90), "billboard"))

    # Vane's Weathercock Spire
    def spire(p):
        sx, sz = 110.0, -120.0
        base = sdf.box(p - [sx, 20, sz], (14, 20, 14), 0.8)
        shaft = np.maximum(np.maximum(np.abs(p[:, 0] - sx), np.abs(p[:, 2] - sz)) - (9.0 - 0.04 * (p[:, 1] - 40)), np.abs(p[:, 1] - 69) - 29)
        d, mat = np.minimum(base, shaft), np.full(len(p), STONE)
        bands = np.abs(((p[:, 1] + 300) % 13.0) - 6.5) > 5.8
        mat = np.where(bands & (p[:, 1] > 40), STONE_D, mat)
        cone = np.maximum(np.maximum(np.abs(p[:, 0] - sx), np.abs(p[:, 2] - sz)) * 1.6 + (p[:, 1] - 124), 96 - p[:, 1]) * 0.5
        d, mat = _put(d, mat, cone, VERDI)
        d, mat = _put(d, mat, sdf.capsule(p, (sx, 122, sz), (sx, 133, sz), 0.6), COPPER)
        for a, b in (((sx - 7, 126, sz), (sx + 7, 126, sz)), ((sx, 126, sz - 7), (sx, 126, sz + 7))):
            d, mat = _put(d, mat, sdf.capsule(p, a, b, 0.45), COPPER)
        # the cockerel itself
        body = sdf.ellipsoid(p, (sx, 135.0, sz), (4.6, 3.0, 1.0))
        tail = np.maximum(sdf.ellipsoid(p, (sx - 4.4, 137.0, sz), (2.6, 4.0, 0.8)), -(p[:, 0] - sx + 2.0))
        head = sdf.sphere(p, (sx + 4.0, 138.0, sz), 1.6)
        comb = sdf.sphere(p, (sx + 4.0, 140.0, sz), 1.0)
        d, mat = _put(d, mat, np.minimum(np.minimum(body, tail), head), COPPER)
        d, mat = _put(d, mat, comb, RED)
        win = sdf.box(p - [sx, 66, sz + 8.0], (2.4, 9, 0.6), 0.4)
        d, mat = _put(d, mat, win, WINDOW)
        door = sdf.box(p - [sx, 9, sz + 14.2], (5.0, 9.0, 0.6), 0.6)
        d, mat = _put(d, mat, door, WOOD)
        return d, mat
    objs.append(Obj(spire, (90, -1, -140), (130, 144, -100), "spire"))

    # the Gazette kiosk
    def kiosk(p):
        kx, kz = 182.0, -66.0
        body = sdf.box(p - [kx, 9, kz], (11, 9, 7), 0.6)
        roof = np.maximum(sdf.box(p - [kx, 21, kz], (14, 2.6, 10), 0.6), -1e9)
        stripe = np.abs(((p[:, 0] - kx + 600) % 6.0) - 3.0) > 1.5
        d, mat = body, np.full(len(p), VERDI)
        d, mat = _put(d, mat, roof, np.where(stripe, RED, WHITE))
        sign = sdf.box(p - [kx, 16.0, kz + 7.4], (10.0, 2.6, 0.5), 0.3)
        d, mat = _put(d, mat, sign, np.where(_tex(GAZ_TEX, p, kx - 10, kx + 10, 18.6, 13.4) & (p[:, 2] > kz + 7.6), SIGN_INK, SIGN))
        for k in range(4):
            pq = sdf.box(p - [kx - 7.0 + 4.6 * k, 7.5, kz + 7.6], (1.8, 2.6, 0.3), 0.1)
            d, mat = _put(d, mat, pq, PAPER)
        return d, mat
    objs.append(Obj(kiosk, (166, -1, -78), (198, 26, -56), "kiosk"))

    # Sola's Sunflower Mill and its field
    def mill(p):
        mx, mz = 268.0, -122.0
        tower = sdf.round_cone(p, (mx, 0, mz), (mx, 52, mz), 15.0, 10.0)
        d, mat = tower, np.full(len(p), WHITE)
        cap = sdf.ellipsoid(p, (mx, 54, mz), (12.0, 9.0, 12.0))
        d, mat = _put(d, mat, cap, ROOF)
        hub = np.array([mx, 50.0, mz + 13.0])
        d, mat = _put(d, mat, sdf.sphere(p, hub, 4.0), SEEDH)
        hq = p - hub
        for k in range(4):
            bq = hq @ sdf.rot_z(-(0.35 + k * np.pi / 2))
            arm = sdf.box(bq - [14.0, 0, 0.6], (14.0, 0.8, 0.6), 0.3)
            blade = sdf.ellipsoid(bq, (17.0, 2.6, 0.0), (11.0, 4.2, 0.9))
            d, mat = _put(d, mat, arm, WOOD)
            d, mat = _put(d, mat, blade, PETAL)
        d, mat = _put(d, mat, sdf.box(p - [mx, 12, mz + 14.4], (4.4, 12, 0.6), 0.6), WOOD)
        for wy in (28.0, 40.0):
            d, mat = _put(d, mat, sdf.box(p - [mx, wy, mz + 12.6 - (wy - 28) * 0.1], (2.4, 3.2, 0.6), 0.3), WINDOW)
        return d, mat
    objs.append(Obj(mill, (234, -1, -140), (302, 76, -100), "mill"))

    def field(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), LEAF)
        rng = np.random.default_rng(5)
        for _ in range(16):
            fx, fz, h = rng.uniform(205, 340), rng.uniform(-94, -40), rng.uniform(10, 18)
            d, mat = _put(d, mat, sdf.capsule(p, (fx, 0, fz), (fx, h, fz), 0.7), LEAF)
            head = sdf.cylinder_y((p - [fx, h + 1.5, fz + 0.6]) @ sdf.rot_x(np.pi / 2 - 0.3), 3.6, 0.6, 0.3)
            r = np.hypot(p[:, 0] - fx, p[:, 1] - h - 1.5)
            d, mat = _put(d, mat, head, np.where(r < 1.8, SEEDH, PETAL))
        return d, mat
    objs.append(Obj(field, (198, -1, -100), (346, 24, -34), "field"))

    if glitch:
        # shadows that fall toward the sun, and lost shadows drifting over the plaza
        def wrong(p):
            d, mat = np.full(len(p), 1e9), np.full(len(p), SHADE)
            for x, z, ln, w in ((-262.0, -62.0, 34.0, 2.0), (-204.0, -62.0, 34.0, 2.0), (dx, dz, 26.0, 5.0), (110.0, -105.0, 60.0, 7.0),
                                (182.0, -58.0, 22.0, 9.0)):
                t = np.clip((p[:, 0] - x) / ln, 0, 1)
                strip = np.maximum.reduce([np.abs(p[:, 2] - z - 4.0) - w * (1 - 0.6 * t), x - p[:, 0], p[:, 0] - x - ln, np.abs(p[:, 1] - 0.15) - 0.1])
                d, mat = _put(d, mat, strip, SHADE)
            for x, y, z in ((-150.0, 10.0, -24.0), (-30.0, 18.0, -52.0), (60.0, 8.0, -30.0)):
                body = sdf.round_cone(p, (x, y, z), (x, y + 10.0, z), 4.2, 2.6)
                head = sdf.sphere(p, (x, y + 15.0, z), 3.2)
                ghost = np.maximum(np.minimum(body, head), np.abs(p[:, 2] - z) - 0.5)
                d, mat = _put(d, mat, ghost, GHOST)
            return d, mat
        objs.append(Obj(wrong, (-275, -1, -120), (260, 46, 0), "wrong"))

    sky = gradient_sky(W, H, "#5E8CC8", "#FFD8A2", glow=(600, 40, 340, "#FFE6B8"))
    lights = [Light(SUNPOS, "#FFC27A", 1.2, 1400),
              Light((-260.0, 34.0, -54.0), "#FFD27A", 0.4, 60, shadow=False),
              Light((-300, 200, 160), "#8EA8E0", 0.35, 900, shadow=False)]
    return dict(world=World(objs), materials=materials(), width=W, height=H, centre=CENTRE,
                lights=lights, key=0.5, ambient=0.16, top=150.0, ss=2, steps=170, sky=sky,
                bloom=[(LAMP, "#FFC861", 8, 0.45), (SUN, "#FFC070", 22, 0.6), (GHOST, "#7A6AC0", 6, 0.3)])
