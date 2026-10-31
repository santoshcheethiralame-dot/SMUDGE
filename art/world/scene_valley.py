"""Echo Valley, the Sound chapter, on a stormy night. 720x270, scrolls horizontally.

A canyon whose cliffs are organ pipes. On a hill at the back, the bell tower: the Silver Tuning Fork's
stand on top is empty. Along the front: Reverb's radio shack and its mast, Thump's bandstand, Coil's post
office with its pillar box.

build(glitch=True)   the law of sound is erased: sound-wave rings and music notes hang frozen in the air
build(glitch=False)  after the case: the storm clears and the moon comes out
Walkable ground: y = 0, z in [0, 30].
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light, gradient_sky
from src import sdf

(GROUND, COBBLE, GRASS, ROCK, PIPE, STONE, ROOF_R, WOOD, WHITE, BRASS, BELL, WINDOW, SIGN, SIGN_INK, RED, GHOST,
 CLOUD, MOSS, PUDDLE, LAMP, GREEN) = range(1, 22)

W, H = 720, 270
CENTRE = (0.0, 90.0)
HOTSPOTS = {"reverb": -260, "stage": -90, "thump": 110, "coil": 250}
TOWER = (-90.0, -150.0)        # x, z of the bell tower on its hill


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _decal(text, font, w, h):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    b = d.textbbox((0, 0), text, font=font)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=font, fill=255)
    return np.array(im) > 100


RADIO_TEX = _decal("RADIO", _font("arialbd.ttf", 19), 76, 24)
POST_TEX = _decal("POST", _font("arialbd.ttf", 19), 72, 24)


def _tex(mask, p, x0, x1, ytop, ybot):
    hh, ww = mask.shape
    u = np.clip(((p[:, 0] - x0) / (x1 - x0) * (ww - 1)), 0, ww - 1).astype(int)
    v = np.clip(((ytop - p[:, 1]) / (ytop - ybot) * (hh - 1)), 0, hh - 1).astype(int)
    return mask[v, u]


def _put(d, mat, dd, mm):
    mat = np.where(dd < d, mm, mat)
    return np.minimum(d, dd), mat


def materials():
    return {
        GROUND: dict(ramp=["#171B28", "#212738", "#2C344A", "#3A445E", "#4B5674", "#5E6A8A"], pattern=lambda p, n: 0.5 * np.sin(p[:, 0] * 0.4) * np.sin(p[:, 2] * 0.5), pattern_gain=0.08,
                     sub=(lambda p: (p[:, 2] > -2) & (p[:, 2] < 32) & ((np.abs(((p[:, 0] + 600) % 7.0) - 3.5) > 3.1) | (np.abs(((p[:, 2] + 600) % 5.0) - 2.5) > 2.1)), COBBLE)),
        COBBLE: dict(ramp=["#0E1018", "#151924", "#1E2332"]),
        GRASS: dict(ramp=["#0C1A14", "#11261C", "#183426", "#204432", "#2C5842"], pattern=lambda p, n: 0.7 * np.sin(p[:, 0] * 1.7 + p[:, 2] * 0.9), pattern_gain=0.12),
        ROCK: dict(ramp=["#14121E", "#1E1B2C", "#29253C", "#36304E", "#453D62", "#574D78"],
                   pattern=lambda p, n: 0.9 * (np.abs(((p[:, 1] + 400) % 11.0) - 5.5) > 4.8) - 0.4, pattern_gain=0.14),
        PIPE: dict(ramp=["#1C1A2C", "#2A2742", "#3A3658", "#4C4770", "#625B8C", "#7A72A6"], gloss=10, spec="#B8B0E0",
                   pattern=lambda p, n: 0.6 * (np.abs(((p[:, 1] + 400) % 14.0) - 7.0) > 6.3), pattern_gain=0.2),
        STONE: dict(ramp=["#1E1E2A", "#2C2C3C", "#3C3C50", "#4E4E66", "#62627E", "#7A7A96"],
                    pattern=lambda p, n: 0.6 * ((np.abs(((p[:, 1] + 300) % 6.0) - 3.0) > 2.6) | (np.abs(((p[:, 0] + p[:, 2] + 300) % 9.0) - 4.5) > 4.1)), pattern_gain=0.22),
        ROOF_R: dict(ramp=["#2A0808", "#4A0E0E", "#6E1616", "#952222", "#B83434"]),
        WOOD: dict(ramp=["#1E1006", "#2E1A0D", "#462814", "#61381C", "#7E4A25"], pattern=lambda p, n: 0.45 * np.sin(p[:, 1] * 1.3 + p[:, 0] * 0.2), pattern_gain=0.12),
        WHITE: dict(ramp=["#3A3F50", "#5C6276", "#868CA2", "#B4B8C8", "#DCDFE8"]),
        BRASS: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848"], gloss=24, spec="#FFFBE6"),
        BELL: dict(ramp=["#2E2008", "#4E3610", "#7A561C", "#A87C2C", "#D4A848"], gloss=30, spec="#FFFFFF"),
        WINDOW: dict(ramp=["#F2B44C", "#FFD27A", "#FFE9B0"], emissive=True),
        SIGN: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8"]),
        SIGN_INK: dict(ramp=["#07090F", "#0E121D", "#161C2C"]),
        RED: dict(ramp=["#3A0907", "#62110D", "#8E1A14", "#B8251C", "#DE3B2E"]),
        GHOST: dict(ramp=["#4A3E7A", "#62549A", "#7E70B8", "#9C8ED0", "#BCB0E6"], emissive=True),
        CLOUD: dict(ramp=["#0E1122", "#151A30", "#1E2440", "#283052", "#343E66"], dither=0.35),
        MOSS: dict(ramp=["#0E2216", "#16321F", "#20442B"]),
        PUDDLE: dict(ramp=["#0A0F24", "#121A3A", "#1C2852", "#2C3C70"], gloss=40, spec="#C8D8FF"),
        LAMP: dict(ramp=["#FF3A2A", "#FF8070"], emissive=True),
        GREEN: dict(ramp=["#0C2A1C", "#124030", "#1A5A44", "#247456"]),
    }


def build(glitch=True):
    objs = []
    objs.append(Obj(lambda p: (p[:, 1], GROUND), (-400, -2, -340), (400, 0.2, 260), "ground"))

    # storm clouds banked over the far rim
    def clouds(p):
        d = np.full(len(p), 1e9)
        rng = np.random.default_rng(3)
        for _ in range(16 if glitch else 9):
            c = (rng.uniform(-380, 380), rng.uniform(96, 132), rng.uniform(-340, -300))
            d = sdf.smin(d, sdf.ellipsoid(p, c, (rng.uniform(40, 80), rng.uniform(12, 22), 20)), 8.0)
        return d, CLOUD
    objs.append(Obj(clouds, (-470, 70, -345), (470, 160, -275), "clouds"))

    # the Organ Cliffs: canyon walls made of pipes
    def cliffs(p):
        d = np.full(len(p), 1e9)
        rng = np.random.default_rng(11)
        for side, (x0, x1) in ((-1, (-400, -140)), (1, (60, 400))):
            for x in np.arange(x0, x1, 15.0):
                h = 34 + 46 * np.abs(np.sin(x * 0.031)) + rng.uniform(0, 14) + (0 if side < 0 else 6)
                z = -250 + rng.uniform(-10, 10)
                pipe = sdf.cylinder_y(p - [x, h / 2, z], 7.2, h / 2, 1.5)
                mouth = sdf.box(p - [x, h * 0.25, z + 7.0], (3.2, 2.0, 1.6), 0.5)
                d = np.minimum(d, np.maximum(pipe, -mouth))
        base = sdf.box(p - [0, 10, -255], (420, 12, 22), 3.0)
        return np.minimum(d, base), PIPE
    objs.append(Obj(cliffs, (-420, -1, -280), (420, 110, -225), "cliffs"))

    # the hill and the bell tower; the tuning fork's stand on top is empty
    tx, tz = TOWER

    def tower(p):
        hill = sdf.ellipsoid(p, (tx, -18, tz), (120, 58, 62))
        d, mat = hill, np.full(len(p), GRASS)
        body = sdf.box(p - [tx, 62, tz], (11, 24, 11), 0.8)
        belfry = sdf.box(p - [tx, 96, tz], (12, 10, 12), 0.8)
        arch = np.minimum(sdf.box(p - [tx, 95, tz], (6.5, 7.5, 14), 1.2), sdf.box(p - [tx, 95, tz], (14, 7.5, 6.5), 1.2))
        belfry = np.maximum(belfry, -arch)
        roof = np.maximum(np.maximum(np.abs(p[:, 0] - tx), np.abs(p[:, 2] - tz)) * 1.4 + (p[:, 1] - 120), 106 - p[:, 1]) * 0.6
        for dd, mm in ((body, STONE), (belfry, STONE), (roof, ROOF_R)):
            d, mat = _put(d, mat, dd, mm)
        bell = sdf.round_cone(p, (tx, 99, tz), (tx, 91, tz), 2.6, 5.4)
        bell = np.maximum(bell, -sdf.cylinder_y(p - [tx, 90.4, tz], 4.4, 1.6, 0.2))
        d, mat = _put(d, mat, bell, BELL)
        rod = sdf.capsule(p, (tx, 120, tz), (tx, 140, tz), 0.6)
        stand = sdf.cylinder_y(p - [tx, 126, tz + 2], 3.4, 1.2, 0.4)
        d, mat = _put(d, mat, rod, BRASS)
        d, mat = _put(d, mat, stand, STONE)
        win = sdf.box(p - [tx, 66, tz + 11.2], (3, 6, 0.6), 0.4)
        d, mat = _put(d, mat, win, WINDOW)
        return d, mat
    objs.append(Obj(tower, (tx - 125, -20, tz - 65), (tx + 125, 142, tz + 65), "tower"))

    if True:
        # law erased: only the fork's outline hums where it stood. Restored: the Silver Tuning Fork is back.
        def fork_ghost(p):
            d = np.full(len(p), 1e9)
            for x in (-2.6, 2.6):
                d = np.minimum(d, sdf.capsule(p, (tx + x, 128, tz + 2), (tx + x, 140, tz + 2), 0.5))
            d = np.minimum(d, sdf.capsule(p, (tx - 2.6, 128, tz + 2), (tx + 2.6, 128, tz + 2), 0.5))
            return d, (GHOST if glitch else WHITE)
        objs.append(Obj(fork_ghost, (tx - 4, 126, tz), (tx + 4, 142, tz + 4), "forkghost"))

    # Reverb's radio shack and mast
    def radio(p):
        x0, z0 = -260.0, -82.0
        body = sdf.box(p - [x0, 16, z0], (26, 16, 12), 1.0)
        roof = np.maximum(sdf.box(p - [x0, 34, z0], (30, 3, 16), 0.8), 0)
        sign = sdf.box(p - [x0, 26, z0 + 12.6], (20, 6.5, 0.6), 0.4)
        win = sdf.box(p - [x0 - 12, 13, z0 + 12.4], (6, 6, 0.6), 0.4)
        door = sdf.box(p - [x0 + 12, 11, z0 + 12.4], (5, 11, 0.6), 0.4)
        d, mat = body, np.full(len(p), WOOD)
        for dd, mm in ((roof, STONE), (sign, SIGN), (win, WINDOW), (door, RED)):
            d, mat = _put(d, mat, dd, mm)
        mat = np.where((mat == SIGN) & (p[:, 2] > z0 + 12.8) & _tex(RADIO_TEX, p, x0 - 19, x0 + 19, 32, 20), SIGN_INK, mat)
        mx = x0 + 34
        for k in range(4):
            y0, y1 = 2 + 26 * k, 28 + 26 * k
            w0, w1 = 8 - 1.8 * k, 8 - 1.8 * (k + 1)
            for sx in (-1, 1):
                d, mat = _put(d, mat, sdf.capsule(p, (mx + sx * w0, y0, z0), (mx + sx * w1, y1, z0), 0.7), STONE)
            d, mat = _put(d, mat, sdf.capsule(p, (mx - w0, y0, z0), (mx + w1, y1, z0), 0.45), STONE)
        tip = sdf.sphere(p, (mx, 108, z0), 2.0)
        d, mat = _put(d, mat, tip, LAMP)
        return d, mat
    objs.append(Obj(radio, (-292, -1, -98), (-214, 112, -68), "radio"))

    # Thump's bandstand: an octagonal gazebo, red roof, white posts
    def bandstand(p):
        x0, z0 = 110.0, -78.0
        base = sdf.cylinder_y(p - [x0, 3, z0], 30, 3, 0.8)
        d, mat = base, np.full(len(p), STONE)
        for k in range(8):
            a = k * np.pi / 4 + np.pi / 8
            post = sdf.capsule(p, (x0 + 26 * np.cos(a), 6, z0 + 26 * np.sin(a)), (x0 + 26 * np.cos(a), 34, z0 + 26 * np.sin(a)), 1.4)
            d, mat = _put(d, mat, post, WHITE)
        r = np.hypot(p[:, 0] - x0, p[:, 2] - z0)
        roof = np.maximum(r * 0.55 + (p[:, 1] - 52), 33 - p[:, 1]) * 0.85
        stripe = (np.abs(((np.arctan2(p[:, 2] - z0, p[:, 0] - x0) + 7) % (np.pi / 4)) - np.pi / 8) < np.pi / 16)
        d, mat = _put(d, mat, roof, np.where(stripe, WHITE, ROOF_R))
        flag = sdf.capsule(p, (x0, 52, z0), (x0, 62, z0), 0.5)
        d, mat = _put(d, mat, flag, BRASS)
        return d, mat
    objs.append(Obj(bandstand, (78, -1, -110), (142, 64, -46), "bandstand"))

    # Coil's post office and its pillar box
    def post(p):
        x0, z0 = 250.0, -86.0
        body = sdf.box(p - [x0, 22, z0], (30, 22, 13), 1.2)
        roof = np.maximum(sdf.box(p - [x0, 50, z0], (35, 7, 17), 1.0), (np.abs(p[:, 0] - x0) * 0.42 + p[:, 1]) - 62)
        sign = sdf.box(p - [x0, 36, z0 + 13.6], (19, 6.5, 0.6), 0.4)
        win = sdf.box(p - [x0 - 15, 18, z0 + 13.4], (7, 8, 0.6), 0.4)
        door = sdf.box(p - [x0 + 13, 13, z0 + 13.4], (6, 13, 0.6), 0.4)
        d, mat = body, np.full(len(p), STONE)
        for dd, mm in ((roof, GREEN), (sign, SIGN), (win, WINDOW), (door, GREEN)):
            d, mat = _put(d, mat, dd, mm)
        mat = np.where((mat == SIGN) & (p[:, 2] > z0 + 13.8) & _tex(POST_TEX, p, x0 - 18, x0 + 18, 42, 30), SIGN_INK, mat)
        box = sdf.cylinder_y(p - [x0 - 42, 9, z0 + 30], 4.2, 9, 0.8)
        cap = sdf.ellipsoid(p, (x0 - 42, 18.5, z0 + 30), (4.8, 2.6, 4.8))
        slot = sdf.box(p - [x0 - 42, 13, z0 + 34.2], (2.4, 0.5, 0.6), 0.2)
        d, mat = _put(d, mat, box, RED)
        d, mat = _put(d, mat, cap, RED)
        d, mat = _put(d, mat, slot, SIGN_INK)
        return d, mat
    objs.append(Obj(post, (204, -1, -103), (288, 66, -52), "post"))

    # puddles on the path and lamp posts
    def street(p):
        d = np.full(len(p), 1e9)
        mat = np.full(len(p), PUDDLE)
        for x, z, rx, rz in ((-170, 14, 16, 4), (20, 22, 22, 5), (190, 10, 14, 3.5), (330, 20, 18, 4)):
            pud = np.maximum(sdf.ellipsoid(p, (x, 0.0, z), (rx, 0.35, rz)), -p[:, 1])
            d, mat = _put(d, mat, pud, PUDDLE)
        for x in (-200, -20, 180):
            pole = sdf.capsule(p, (x, 0, -12), (x, 30, -12), 0.8)
            head = sdf.sphere(p, (x, 32, -12), 2.4)
            d, mat = _put(d, mat, pole, STONE)
            d, mat = _put(d, mat, head, WINDOW)
        return d, mat
    objs.append(Obj(street, (-212, -1, -15), (350, 36, 26), "street"))

    if glitch:
        # sound has nowhere to go: rings and notes frozen in the air
        def frozen(p):
            d = np.full(len(p), 1e9)
            for (cx, cy, cz), rs in (((tx, 95, tz + 14), (14, 22, 30)), ((110, 40, -60), (16, 24)), ((-260, 60, -66), (10, 17))):
                for r in rs:
                    ring = sdf.torus_y((p - [cx, cy, cz]) @ sdf.rot_x(np.pi / 2), r, 0.55)
                    ring = np.maximum(ring, -(p[:, 1] - cy + r * 0.15))      # arcs, not full circles
                    d = np.minimum(d, ring)
            for x, y, z in ((60, 62, -40), (150, 70, -30), (-40, 80, -60), (220, 58, -40)):
                note = np.minimum(sdf.ellipsoid(p, (x, y, z), (2.6, 2.0, 1.0)), sdf.capsule(p, (x + 2.2, y, z), (x + 2.2, y + 9, z), 0.5))
                d = np.minimum(d, note)
            return d, GHOST
        objs.append(Obj(frozen, (-280, 30, -185), (240, 130, -26), "frozen"))

    if glitch:
        sky = gradient_sky(W, H, "#0A0D24", "#3A4472", glow=(200, 40, 240, "#6A6AA8"))
    else:
        sky = gradient_sky(W, H, "#0A1030", "#3A4A78", glow=(520, 40, 200, "#C8D2F0"))
    lights = [Light((-300, 260, 200), "#B4C2FF", 1.35, 900),
              Light((-260, 108, -70), "#FF5040", 0.4, 90, shadow=False),
              Light((110, 30, -60), "#FFD27A", 0.35, 120, shadow=False),
              Light((300, 160, 120), "#8E7AD8", 0.35, 700, shadow=False)]
    return dict(world=World(objs), materials=materials(), width=W, height=H, centre=CENTRE,
                lights=lights, key=0.5, ambient=0.17, top=210.0, ss=2, steps=170, sky=sky,
                bloom=[(WINDOW, "#FFC861", 10, 0.5), (GHOST, "#9C8ED0", 7, 0.4), (LAMP, "#FF5040", 8, 0.6)])
