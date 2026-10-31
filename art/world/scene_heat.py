"""Kelvin Springs, the Heat chapter, a snowy evening. 720x270, scrolls horizontally.

A hot-spring town in the mountains. A boardwalk runs over the snow past steaming pools. Left to right: Al's
Steam Kitchen; the bathhouse, the crime scene, with its iron safe and the cooling tub where the block was
found; Ferris's boiler house and its pipes; Brewster's Copper Kettle tea house.

build(glitch=True)   heat is erased: the steam hangs frozen solid over the pools, the ice lock lies in a puddle
build(glitch=False)  after the case: soft steam rises, lanterns glow, the safe is shut and locked again
Walkable boardwalk: y = 0, z in [0, 30].
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light, gradient_sky, stars
from src import sdf

(SNOW, PLANK, PLANK_D, WOOD, WOOD_D, ROOF, ROOFSNOW, STONE, POOL, STEAM, FROZEN, WINDOW, LANTERN, IRON, ICE, COPPER,
 ALU, PINE, MOUNT, MOUNTSNOW, SIGN, SIGN_INK, RED, PUDDLE, BRICK, GHOST) = range(1, 27)

W, H = 720, 270
CENTRE = (0.0, 90.0)
HOTSPOTS = {"al": -260, "stage": -90, "ferris": 110, "brewster": 250}


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _decal(text, font, w, h):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    b = d.textbbox((0, 0), text, font=font)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=font, fill=255)
    return np.array(im) > 100


LAW_TEX = _decal("Q = mc\u0394T", _font("arialbd.ttf", 27), 128, 40)
BATH_TEX = _decal("BATHS", _font("arialbd.ttf", 20), 80, 24)
TEA_TEX = _decal("TEA", _font("arialbd.ttf", 20), 56, 24)


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
        SNOW: dict(ramp=["#4A5470", "#6A7694", "#8E9AB6", "#B4BED6", "#D8E0F0", "#F2F6FF"], dither=0.25,
                   pattern=lambda p, n: 0.5 * np.sin(p[:, 0] * 0.13 + np.sin(p[:, 2] * 0.11) * 2.0), pattern_gain=0.08),
        PLANK: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E", "#CF8A42"],
                    pattern=lambda p, n: 0.45 * np.sin(p[:, 0] * 0.5 + 2.0 * np.sin(p[:, 2] * 0.3)), pattern_gain=0.14,
                    sub=(lambda p: (p[:, 1] < 0.6) & (np.abs(((p[:, 0] + 600) % 6.0) - 3.0) > 2.65), PLANK_D)),
        PLANK_D: dict(ramp=["#120903", "#1E1006", "#2A1608"]),
        WOOD: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E"],
                   pattern=lambda p, n: 0.45 * np.sin(p[:, 1] * 1.3 + p[:, 0] * 0.2), pattern_gain=0.12),
        WOOD_D: dict(ramp=["#140A04", "#24130A", "#3A2010", "#522E18"]),
        ROOF: dict(ramp=["#1A1420", "#28202E", "#382C40", "#4A3A54"]),
        ROOFSNOW: dict(ramp=["#8E9AB6", "#B4BED6", "#D8E0F0", "#F2F6FF"]),
        STONE: dict(ramp=["#2C2830", "#433D48", "#5C5462", "#766C7C", "#928898"]),
        POOL: dict(ramp=["#0E3A40", "#14545A", "#1E7076", "#2E8E92", "#46ACAE"], gloss=30, spec="#E6FFFF",
                   pattern=lambda p, n: 0.6 * np.sin(p[:, 0] * 0.4 + np.sin(p[:, 2] * 0.5) * 2.0), pattern_gain=0.12),
        STEAM: dict(ramp=["#8A94AC", "#A8B2C8", "#C6CEE0", "#E2E8F4"], dither=0.4),
        FROZEN: dict(ramp=["#6A9AC8", "#8EB8E0", "#B8D8F2", "#E0F2FF"], gloss=40, spec="#FFFFFF"),
        WINDOW: dict(ramp=["#F2B44C", "#FFD27A", "#FFE9B0"], emissive=True),
        LANTERN: dict(ramp=["#E04020", "#FF7040", "#FFA070"], emissive=True),
        IRON: dict(ramp=["#0A0C10", "#15191F", "#222831", "#323A46", "#47515F", "#626E7F"], gloss=24, spec="#C8D4E2"),
        ICE: dict(ramp=["#4E94B8", "#7EBEDC", "#B4E0F2", "#E6F8FF"], gloss=40, spec="#FFFFFF"),
        COPPER: dict(ramp=["#4A1C0A", "#7A3214", "#AC5022", "#D87434", "#F6A060"], gloss=26, spec="#FFEAD0"),
        ALU: dict(ramp=["#3E4652", "#66707E", "#949EAC", "#C4CCD6", "#EEF2F8"], gloss=26, spec="#FFFFFF"),
        PINE: dict(ramp=["#0A1A14", "#10261C", "#183426", "#204432"]),
        MOUNT: dict(ramp=["#2A2840", "#38365A", "#4A4672", "#5E5A8C"], dither=0.3),
        MOUNTSNOW: dict(ramp=["#8A90B8", "#AAB0D0", "#CCD2E8", "#ECEFFC"], dither=0.3),
        SIGN: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8"]),
        SIGN_INK: dict(ramp=["#07090F", "#0E121D", "#161C2C"]),
        RED: dict(ramp=["#3A0907", "#62110D", "#8E1A14", "#B8251C", "#DE3B2E"]),
        PUDDLE: dict(ramp=["#2E5A80", "#4A7AA0", "#7AA6C8"], gloss=50, spec="#FFFFFF"),
        BRICK: dict(ramp=["#2A1214", "#42191C", "#5E2426", "#7C3230", "#9A443C"],
                    pattern=lambda p, n: 0.7 * (np.abs(((p[:, 1] + 300) % 4.0) - 2.0) > 1.6), pattern_gain=0.2),
        GHOST: dict(ramp=["#4A3E7A", "#62549A", "#7E70B8", "#9C8ED0"], emissive=True),
    }


def build(glitch=True):
    objs = []

    def ground(p):
        walk = (p[:, 2] > -2) & (p[:, 2] < 32)
        return p[:, 1], np.where(walk, PLANK, SNOW)
    objs.append(Obj(ground, (-400, -2, -340), (400, 0.2, 260), "ground"))
    objs.append(Obj(lambda p: (np.maximum(sdf.box(p - [0, 0.4, -1.0], (400, 0.6, 0.8)), -1e9), WOOD_D), (-400, -1, -2.5), (400, 1.5, 0.5), "edge"))

    # snowy peaks and a pine forest on the slopes
    def far(p):
        ridge = 26 + 52 * (1 - np.abs(np.sin(p[:, 0] * 0.011 + 0.4))) ** 2.2 + 12 * (1 - np.abs(np.sin(p[:, 0] * 0.034 + 1.1))) ** 2
        m = np.maximum((p[:, 1] - ridge) * 0.6, np.abs(p[:, 2] + 310) - 30)
        cap = p[:, 1] > 52 + 5 * np.sin(p[:, 0] * 0.21) + 3 * np.sin(p[:, 0] * 0.53)
        d, mat = m, np.where(cap, MOUNTSNOW, MOUNT)
        return d, mat
    objs.append(Obj(far, (-420, -1, -345), (420, 90, -275), "far"))

    def pines(p):
        d = np.full(len(p), 1e9)
        rng = np.random.default_rng(17)
        mat = np.full(len(p), PINE)
        for _ in range(26):
            x, z, h = rng.uniform(-380, 380), rng.uniform(-240, -160), rng.uniform(16, 30)
            if abs(x + 90) < 60 and z > -200:
                continue
            cone = np.maximum(np.hypot(p[:, 0] - x, p[:, 2] - z) - (h * 0.32) * (1 - (p[:, 1]) / h), np.maximum(-p[:, 1] + 3, p[:, 1] - h)) * 0.8
            d, mat = _put(d, mat, cone, np.where(((p[:, 1] + 300) % 6.0) > 4.6, ROOFSNOW, PINE))
            d, mat = _put(d, mat, sdf.capsule(p, (x, 0, z), (x, 4, z), 1.2), WOOD_D)
        return d, mat
    objs.append(Obj(pines, (-400, -1, -250), (400, 32, -150), "pines"))

    # the hot pools on the terrace behind the bathhouse, steam over them
    POOLS = ((-170.0, -130.0, 26.0), (-20.0, -140.0, 30.0), (190.0, -150.0, 24.0))

    def pools(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), STONE)
        for x, z, r in POOLS:
            rim = np.maximum(np.abs(np.hypot((p[:, 0] - x) / 1.6, p[:, 2] - z) - r * 0.6) - 2.6, np.abs(p[:, 1] - 1.2) - 1.2)
            water = np.maximum(np.hypot((p[:, 0] - x) / 1.6, p[:, 2] - z) - r * 0.6, np.abs(p[:, 1] - 1.0) - 0.4)
            d, mat = _put(d, mat, rim, STONE)
            d, mat = _put(d, mat, water, POOL)
            rng = np.random.default_rng(int(x) + 500)
            for k in range(5):
                c = (x + rng.uniform(-r, r), 8 + 6 * k + rng.uniform(-2, 2), z + rng.uniform(-4, 4))
                if glitch:
                    blob = sdf.box(p - c, (5.0 - 0.5 * k, 3.0, 3.0), 1.6)
                    d, mat = _put(d, mat, blob, FROZEN)
                else:
                    d, mat = _put(d, mat, sdf.ellipsoid(p, c, (8.0 - k, 3.6, 4.0)), STEAM)
        return d, mat
    objs.append(Obj(pools, (-230, -1, -175), (240, 46, -110), "pools"))

    # Al's Steam Kitchen
    def kitchen(p):
        x0, z0 = -264.0, -86.0
        body = sdf.box(p - [x0, 16, z0], (24, 16, 12), 0.8)
        d, mat = body, np.full(len(p), WOOD)
        roof = np.maximum(np.abs(p[:, 0] - x0) * 0.6 + (p[:, 1] - 46), np.maximum(32 - p[:, 1], np.abs(p[:, 2] - z0) - 15)) * 0.8
        d, mat = _put(d, mat, roof, np.where(p[:, 1] > 40 - 0.6 * np.abs(p[:, 0] - x0) * 0, ROOFSNOW, ROOF))
        counter = sdf.box(p - [x0, 9, z0 + 13], (20, 1.4, 2.4), 0.4)
        d, mat = _put(d, mat, counter, WOOD_D)
        hatch = sdf.box(p - [x0, 18, z0 + 12.2], (16, 6, 0.6), 0.6)
        d, mat = _put(d, mat, hatch, WINDOW)
        for k, dx in enumerate((-10.0, 0.0, 10.0)):
            pot = sdf.cylinder_y(p - [x0 + dx, 12.6, z0 + 13], 3.2, 2.2, 0.6)
            d, mat = _put(d, mat, pot, ALU)
        chim = sdf.cylinder_y(p - [x0 + 14, 44, z0 - 4], 2.6, 10.0, 0.4)
        d, mat = _put(d, mat, chim, IRON)
        for k in range(4):
            c = (x0 + 14 + 2 * np.sin(k), 58 + 6 * k, z0 - 4)
            d, mat = _put(d, mat, sdf.sphere(p, c, 3.0 - 0.3 * k) if not glitch else sdf.box(p - c, (2.4, 2.4, 2.4), 0.8), FROZEN if glitch else STEAM)
        return d, mat
    objs.append(Obj(kitchen, (-292, -1, -104), (-236, 84, -70), "kitchen"))

    # the bathhouse; in front, the iron safe and the cooling tub
    def bathhouse(p):
        x0, z0 = -86.0, -108.0
        body = sdf.box(p - [x0, 22, z0], (42, 22, 16), 0.8)
        d, mat = body, np.full(len(p), WOOD)
        posts = np.abs(((p[:, 0] - x0 + 600) % 14.0) - 7.0) < 1.2
        mat = np.where(posts & (p[:, 2] > z0 + 15.5), WOOD_D, mat)
        roof = np.maximum((np.abs(p[:, 0] - x0) * 0.35 + (p[:, 1] - 62)) - 0.004 * (p[:, 0] - x0) ** 2 * 0, np.maximum(44 - p[:, 1], np.abs(p[:, 2] - z0) - 22))
        roof = np.maximum(roof, np.abs(p[:, 0] - x0) - 50)
        d, mat = _put(d, mat, roof * 0.8, np.where(p[:, 1] > 54, ROOFSNOW, ROOF))
        sign = sdf.box(p - [x0, 37, z0 + 16.6], (21, 6.5, 0.6), 0.3)
        d, mat = _put(d, mat, sign, np.where(_tex(BATH_TEX, p, x0 - 20, x0 + 20, 43, 31) & (p[:, 2] > z0 + 17), SIGN_INK, SIGN))
        for wx in (-30.0, -16.0, 16.0, 30.0):
            d, mat = _put(d, mat, sdf.box(p - [x0 + wx, 22, z0 + 16.2], (4, 6, 0.6), 0.4), WINDOW)
        door = sdf.box(p - [x0, 11, z0 + 16.2], (7, 11, 0.6), 0.6)
        d, mat = _put(d, mat, door, WOOD_D)
        for lx in (x0 - 22, x0 + 22):
            lan = sdf.ellipsoid(p, (lx, 34, z0 + 18), (2.4, 3.2, 2.4))
            d, mat = _put(d, mat, lan, LANTERN)
        # the safe, and its ice lock: whole when restored, a puddle while heat is erased
        sx, sz = x0 - 22.0, -52.0
        safe = sdf.box(p - [sx, 8, sz], (8, 8, 7), 0.8)
        d, mat = _put(d, mat, safe, IRON)
        wheel = sdf.torus_y((p - [sx, 9, sz + 7.4]) @ sdf.rot_x(np.pi / 2), 2.6, 0.6)
        d, mat = _put(d, mat, wheel, COPPER)
        if glitch:
            pud = sdf.ellipsoid(p, (sx + 6, 0.1, sz + 10), (7.0, 0.4, 4.0))
            d, mat = _put(d, mat, pud, PUDDLE)
            door = sdf.box((p - [sx + 9.4, 8, sz + 10.0]) @ sdf.rot_y(-0.9), (0.6, 7.4, 6.6), 0.3)
            d, mat = _put(d, mat, door, IRON)
        else:
            lock = sdf.box(p - [sx + 4.4, 9, sz + 7.6], (2.0, 3.0, 1.0), 0.6)
            d, mat = _put(d, mat, lock, ICE)
        # the cooling tub with the block in it
        tx, tz = x0 + 26.0, -50.0
        tub = np.maximum(sdf.cylinder_y(p - [tx, 6, tz], 9.0, 6.0, 0.6), -sdf.cylinder_y(p - [tx, 9, tz], 8.0, 6.0, 0.2))
        staves = np.abs(((np.arctan2(p[:, 2] - tz, p[:, 0] - tx) * 14 / np.pi) % 1.0) - 0.5) > 0.44
        hoops = np.abs(np.abs(p[:, 1] - 6.0) - 3.6) < 0.7
        d, mat = _put(d, mat, tub, np.where(hoops, IRON, np.where(staves, WOOD_D, WOOD)))
        water = sdf.cylinder_y(p - [tx, 10.2, tz], 8.0, 0.3, 0.1)
        d, mat = _put(d, mat, water, POOL)
        return d, mat
    objs.append(Obj(bathhouse, (-140, -1, -132), (-30, 72, -38), "bathhouse"))

    # Ferris's boiler house: brick, a tall stack, pipes running out to the pools
    def boiler(p):
        x0, z0 = 112.0, -102.0
        body = sdf.box(p - [x0, 18, z0], (24, 18, 12), 0.8)
        d, mat = body, np.full(len(p), BRICK)
        roof = np.maximum(sdf.box(p - [x0, 38, z0], (27, 2.4, 15), 0.8), -1e9)
        d, mat = _put(d, mat, roof, ROOFSNOW)
        stack = sdf.round_cone(p, (x0 - 14, 36, z0 - 4), (x0 - 14, 80, z0 - 4), 5.0, 3.4)
        d, mat = _put(d, mat, stack, BRICK)
        for k in range(3):
            c = (x0 - 14 + 3 * np.sin(k * 1.3), 86 + 7 * k, z0 - 4)
            d, mat = _put(d, mat, sdf.box(p - c, (3, 3, 3), 1.0) if glitch else sdf.sphere(p, c, 3.8 - 0.4 * k), FROZEN if glitch else STEAM)
        for y in (10.0, 16.0):
            pipe = sdf.capsule(p, (x0 + 24, y, z0 + 4), (x0 + 60, y, z0 + 4), 1.4)
            d, mat = _put(d, mat, pipe, COPPER)
        gauge = sdf.cylinder_y((p - [x0 + 8, 22, z0 + 12.4]) @ sdf.rot_x(np.pi / 2), 3.2, 0.6, 0.3)
        d, mat = _put(d, mat, gauge, SIGN)
        door = sdf.box(p - [x0 - 6, 10, z0 + 12.2], (6, 10, 0.6), 0.6)
        d, mat = _put(d, mat, door, IRON)
        win = sdf.box(p - [x0 + 10, 12, z0 + 12.2], (4, 4, 0.6), 0.6)
        d, mat = _put(d, mat, win, WINDOW)
        return d, mat
    objs.append(Obj(boiler, (84, -1, -118), (176, 110, -88), "boiler"))

    # Brewster's Copper Kettle tea house, with a giant kettle for a sign
    def teahouse(p):
        x0, z0 = 254.0, -98.0
        body = sdf.box(p - [x0, 16, z0], (22, 16, 12), 0.8)
        d, mat = body, np.full(len(p), WOOD)
        roof = np.maximum(np.abs(p[:, 0] - x0) * 0.7 + (p[:, 1] - 46), np.maximum(32 - p[:, 1], np.abs(p[:, 2] - z0) - 15)) * 0.8
        d, mat = _put(d, mat, roof, np.where(p[:, 1] > 38, ROOFSNOW, ROOF))
        k = sdf.ellipsoid(p, (x0, 52, z0 + 2), (8.0, 7.0, 7.0))
        spout = sdf.round_cone(p, (x0 + 6, 50, z0 + 4), (x0 + 12, 56, z0 + 6), 2.0, 1.0)
        handle = np.maximum(sdf.torus_y((p - [x0, 58, z0 + 2]) @ sdf.rot_x(np.pi / 2), 5.0, 0.8), 58 - p[:, 1])
        d, mat = _put(d, mat, np.minimum(np.minimum(k, spout), handle), COPPER)
        sign = sdf.box(p - [x0, 26, z0 + 12.6], (13, 5.6, 0.6), 0.3)
        d, mat = _put(d, mat, sign, np.where(_tex(TEA_TEX, p, x0 - 12, x0 + 12, 31, 21) & (p[:, 2] > z0 + 13), SIGN_INK, SIGN))
        for wx in (-12.0, 12.0):
            d, mat = _put(d, mat, sdf.box(p - [x0 + wx, 15, z0 + 12.2], (5, 5, 0.6), 0.6), WINDOW)
        door = sdf.box(p - [x0, 9, z0 + 12.2], (4.4, 9, 0.6), 0.6)
        d, mat = _put(d, mat, door, RED)
        return d, mat
    objs.append(Obj(teahouse, (228, -1, -116), (282, 66, -82), "teahouse"))

    # the law sign and lantern posts along the boardwalk
    def dressing(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), WOOD_D)
        x0, z0 = 14.0, -34.0
        d, mat = _put(d, mat, sdf.box(p - [x0, 14, z0 - 1], (1.2, 14, 1.2), 0.3), WOOD_D)
        bd = sdf.box(p - [x0, 30, z0], (26, 9, 0.9), 0.4)
        ink = (p[:, 2] > z0 + 0.7) & _tex(LAW_TEX, p, x0 - 24, x0 + 24, 38, 22)
        rub = p[:, 0] > x0 + 4 + 3 * np.sin(p[:, 1])
        d, mat = _put(d, mat, bd, np.where(ink, np.where(rub & glitch, GHOST, SIGN_INK), SIGN))
        for lx in (-180.0, 40.0, 180.0, 330.0):
            d, mat = _put(d, mat, sdf.capsule(p, (lx, 0, -6.0), (lx, 22, -6.0), 0.8), WOOD_D)
            d, mat = _put(d, mat, sdf.ellipsoid(p, (lx, 24.6, -6.0), (2.2, 3.0, 2.2)), LANTERN)
        return d, mat
    objs.append(Obj(dressing, (-186, -1, -40), (336, 42, -2), "dressing"))

    sky = gradient_sky(W, H, "#1A1438", "#C88AA8", glow=(500, 200, 320, "#F0B8A8"))
    stars(sky, 70, seed=41, ymax=70)
    lights = [Light((-300, 240, 220), "#C8C0F0", 1.0, 1000),
              Light((-86.0, 20, -80), "#FFB070", 0.8, 90, shadow=False),
              Light((-264.0, 18, -66), "#FFC070", 0.6, 60, shadow=False),
              Light((254.0, 16, -78), "#FFC070", 0.6, 60, shadow=False)]
    return dict(world=World(objs), materials=materials(), width=W, height=H, centre=CENTRE,
                lights=lights, key=0.55, ambient=0.18, top=150.0, ss=2, steps=170, sky=sky,
                bloom=[(WINDOW, "#FFC861", 8, 0.45), (LANTERN, "#FF7040", 8, 0.5), (GHOST, "#7E70B8", 6, 0.35)])
