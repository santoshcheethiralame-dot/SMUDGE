"""Watt Works, the Work-and-power chapter, a smoky dusk. 720x270, scrolls horizontally.

An industrial clock town of brick, iron and cogs, by a canal. Left to right: Cog's workshop under the railway
arches; the clock tower with its open crate-lift shaft, the crime scene; Hoist's dockyard crane over the canal;
Dynamo's generator shed humming with coils.

build(glitch=True)   work and power are erased: crates drift up off the ground and hang in the air, the crane's
                     load floats above its hook, the clock face is blank where the escapement drove it
build(glitch=False)  after the case: crates on the ground, the clock's hands back and lit
Walkable towpath: y = 0, z in [0, 30].
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light, gradient_sky
from src import sdf

(PATH, PATH_D, BRICK, BRICK_D, IRON, RUST, BRASS, WINDOW, LAMP, CLOCK, SIGN, SIGN_INK, CANAL, WOOD, HAZARD, COIL,
 SPARK, SMOKE, FAR, GHOST, CRATE, STONE) = range(1, 23)

W, H = 720, 270
CENTRE = (0.0, 90.0)
HOTSPOTS = {"cog": -260, "stage": -90, "hoist": 110, "dynamo": 250}
TOWER = (-90.0, -112.0)


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _decal(text, font, w, h):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    b = d.textbbox((0, 0), text, font=font)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=font, fill=255)
    return np.array(im) > 100


LAW_TEX = _decal("P = W / t", _font("arialbd.ttf", 30), 180, 36)


def _tex(mask, p, x0, x1, ytop, ybot):
    hh, ww = mask.shape
    u = np.clip(((p[:, 0] - x0) / (x1 - x0) * (ww - 1)), 0, ww - 1).astype(int)
    v = np.clip(((ytop - p[:, 1]) / (ytop - ybot) * (hh - 1)), 0, hh - 1).astype(int)
    return mask[v, u]


def _put(d, mat, dd, mm):
    mat = np.where(dd < d, mm, mat)
    return np.minimum(d, dd), mat


def _gear(p, c, r, t, axis_z=True):
    q = p - c
    rr = np.hypot(q[:, 0], q[:, 1])
    a = np.arctan2(q[:, 1], q[:, 0])
    teeth = r + 1.6 * np.clip(np.cos(a * max(8, int(r))) * 3.0, -1, 1)
    return np.maximum(np.maximum(rr - teeth, np.abs(q[:, 2]) - t), r * 0.35 - rr) * 0.8


def materials():
    return {
        PATH: dict(ramp=["#3A322C", "#4E443C", "#64584E", "#7C6E62", "#968676", "#B0A08C"], warm_tint=0.5,
                   pattern=lambda p, n: 0.4 * np.sin(p[:, 0] * 0.8) * np.sin(p[:, 2] * 0.9), pattern_gain=0.08,
                   sub=(lambda p: (p[:, 1] < 0.5) & ((np.abs(((p[:, 0] + 3.0 * (np.floor((p[:, 2] + 600) / 6.0) % 2) + 600) % 12.0) - 6.0) > 5.75)
                                                      | (np.abs(((p[:, 2] + 600) % 6.0) - 3.0) > 2.82)), PATH_D)),
        PATH_D: dict(ramp=["#141010", "#1E1816", "#28201C"]),
        BRICK: dict(ramp=["#2A1214", "#42191C", "#5E2426", "#7C3230", "#9A443C", "#B45A4C"], warm_tint=0.5,
                    sub=(lambda p: (np.abs(((p[:, 1] + 300) % 4.0) - 2.0) > 1.65) | (np.abs(((p[:, 0] + p[:, 2] + 2.0 * (np.floor((p[:, 1] + 300) / 4.0) % 2) + 300) % 8.0) - 4.0) > 3.6), BRICK_D)),
        BRICK_D: dict(ramp=["#10080A", "#1A0E10", "#24121A"]),
        IRON: dict(ramp=["#0A0C10", "#15191F", "#222831", "#323A46", "#47515F", "#626E7F"], gloss=20, spec="#C8D4E2"),
        RUST: dict(ramp=["#2A1210", "#46201A", "#663024", "#864432", "#A65C44"]),
        BRASS: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848", "#FFE08A"], gloss=24, spec="#FFFFFF"),
        WINDOW: dict(ramp=["#F2B44C", "#FFD27A", "#FFE9B0"], emissive=True),
        LAMP: dict(ramp=["#FFD860", "#FFF0A8", "#FFFCE0"], emissive=True),
        CLOCK: dict(ramp=["#D8D2C2", "#F2EEE2", "#FFFFFF"], emissive=True),
        SIGN: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF"]),
        SIGN_INK: dict(ramp=["#07090F", "#0E121D", "#161C2C"]),
        CANAL: dict(ramp=["#0A1218", "#101C24", "#182834", "#223646", "#2E485A"], gloss=30, spec="#C8D8E8",
                    pattern=lambda p, n: 0.6 * np.sin(p[:, 0] * 0.3 + np.sin(p[:, 2] * 0.4) * 2.0), pattern_gain=0.12),
        WOOD: dict(ramp=["#1E1006", "#2E1A0D", "#462814", "#61381C", "#7E4A25"],
                   pattern=lambda p, n: 0.45 * np.sin(p[:, 1] * 1.3 + p[:, 0] * 0.2), pattern_gain=0.12),
        HAZARD: dict(ramp=["#7A5A08", "#B8880E", "#E6B820", "#F8DA4A"]),
        COIL: dict(ramp=["#4A1C0A", "#7A3214", "#AC5022", "#D87434", "#F6A060"], gloss=26, spec="#FFEAD0"),
        SPARK: dict(ramp=["#6A9AFF", "#B8D4FF", "#FFFFFF"], emissive=True),
        SMOKE: dict(ramp=["#3A3440", "#4C4654", "#605A68", "#76707E"], dither=0.4),
        FAR: dict(ramp=["#2A2232", "#362C40", "#44384E", "#52465E"], dither=0.3),
        GHOST: dict(ramp=["#4A3E7A", "#62549A", "#7E70B8", "#9C8ED0"], emissive=True),
        CRATE: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E", "#CF8A42"],
                    pattern=lambda p, n: 0.45 * np.sin(p[:, 0] * 0.9 + p[:, 1] * 0.4), pattern_gain=0.12),
        STONE: dict(ramp=["#2C2830", "#433D48", "#5C5462", "#766C7C", "#928898"]),
    }


def build(glitch=True):
    objs = []

    def ground(p):
        canal = (p[:, 2] < -36) & (p[:, 2] > -76) & (p[:, 0] > 40) & (p[:, 0] < 220)
        return np.where(canal, p[:, 1] + 4.0, p[:, 1]), np.where(canal, CANAL, PATH)
    objs.append(Obj(ground, (-400, -6, -340), (400, 0.2, 260), "ground"))
    objs.append(Obj(lambda p: (np.maximum(sdf.box(p - [130, -2, -56], (92, 2.4, 21)), -sdf.box(p - [130, -2, -56], (90, 6, 20))), STONE),
                    (36, -6, -79), (224, 1, -33), "canalwall"))

    # a row of lit warehouses behind everything, gears bolted to their gables
    def warehouses(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), BRICK)
        for k, x in enumerate(range(-360, 380, 52)):
            h = 44 + 16 * ((k * 37) % 5) / 4
            body = sdf.box(p - [x, h / 2, -170], (24, h / 2, 14), 0.6)
            d, mat = _put(d, mat, body, BRICK)
            gable = np.maximum(np.abs(p[:, 0] - x) * 0.7 + (p[:, 1] - h - 12), np.maximum(h - p[:, 1], np.abs(p[:, 2] + 170) - 15)) * 0.8
            d, mat = _put(d, mat, gable, IRON)
            for wy in np.arange(10, h - 6, 12):
                for wx in (-14.0, -5.0, 5.0, 14.0):
                    lit = ((k * 7 + int(wy) * 3 + int(wx)) % 3) != 0
                    d, mat = _put(d, mat, sdf.box(p - [x + wx, wy, -155.6], (2.6, 3.6, 0.6), 0.2), WINDOW if lit else BRICK_D)
            d, mat = _put(d, mat, _gear(p, np.array([x, h + 4.0, -154.0]), 4.0, 0.8), BRASS)
        return d, mat
    objs.append(Obj(warehouses, (-390, -1, -186), (390, 82, -150), "warehouses"))

    # far factory skyline: sawtooth roofs and chimneys with smoke
    def far(p):
        cell = np.round(p[:, 0] / 30.0)
        hh = 30 + 18 * (np.abs(np.sin(cell * 3.3)) )
        q = p - np.stack([cell * 30.0, np.zeros(len(p)), np.full(len(p), -270.0)], 1)
        saw = np.maximum.reduce([np.abs(q[:, 0]) - 14.5, np.abs(q[:, 2]) - 10, -q[:, 1], q[:, 1] - hh - 6 * ((q[:, 0] + 15) % 10) / 10])
        chim = np.maximum(np.hypot(q[:, 0] - 6, q[:, 2]) - 2.6, np.maximum(-q[:, 1], q[:, 1] - hh - 28 * (np.abs(np.sin(cell * 7.1)) > 0.5)))
        d, mat = np.minimum(saw, chim), np.full(len(p), FAR)
        return d, mat
    objs.append(Obj(far, (-420, -1, -285), (420, 90, -255), "far"))

    def smoke(p):
        d = np.full(len(p), 1e9)
        rng = np.random.default_rng(23)
        for _ in range(9):
            x, y = rng.uniform(-360, 360), rng.uniform(80, 110)
            d = sdf.smin(d, sdf.ellipsoid(p, (x, y, -268), (rng.uniform(14, 28), rng.uniform(5, 9), 8)), 4.0)
        return d, SMOKE
    objs.append(Obj(smoke, (-400, 70, -280), (400, 125, -255), "smoke"))

    # Cog's workshop under the railway arches
    def arches(p):
        x0, z0 = -262.0, -100.0
        viaduct = sdf.box(p - [x0, 26, z0], (70, 26, 12), 0.8)
        arch = np.full(len(p), 1e9)
        for ax in (-46.0, 0.0, 46.0):
            arch = np.minimum(arch, np.maximum(np.hypot(p[:, 0] - x0 - ax, p[:, 1] - 22) - 16, -p[:, 1] - 1))
            arch = np.minimum(arch, sdf.box(p - [x0 + ax, 11, z0], (16, 11, 20)))
        d, mat = np.maximum(viaduct, -arch), np.full(len(p), BRICK)
        rail = sdf.box(p - [x0, 53, z0], (72, 1.4, 13), 0.4)
        d, mat = _put(d, mat, rail, IRON)
        # the shopfront filling the middle arch: glass, a clock in the window, a big brass gear sign
        front = sdf.box(p - [x0, 14, z0 + 4], (15, 14, 0.8), 0.4)
        d, mat = _put(d, mat, front, WOOD)
        win = sdf.box(p - [x0 - 5, 16, z0 + 5], (7, 7, 0.6), 0.4)
        d, mat = _put(d, mat, win, WINDOW)
        d, mat = _put(d, mat, sdf.box(p - [x0 + 9, 9, z0 + 5], (3.6, 9, 0.6), 0.4), WOOD)
        g = _gear(p, np.array([x0, 33.0, z0 + 6]), 6.0, 1.2)
        d, mat = _put(d, mat, g, BRASS)
        for ax in (-46.0, 46.0):
            d, mat = _put(d, mat, sdf.box(p - [x0 + ax, 14, z0 + 2], (14, 14, 0.8), 0.4), BRICK_D)
        return d, mat
    objs.append(Obj(arches, (-336, -1, -114), (-188, 56, -86), "arches"))

    # the clock tower and its open lift shaft
    tx, tz = TOWER

    def tower(p):
        body = sdf.box(p - [tx, 60, tz], (16, 60, 14), 0.8)
        d, mat = body, np.full(len(p), BRICK)
        top = sdf.box(p - [tx, 126, tz], (19, 6, 17), 0.8)
        d, mat = _put(d, mat, top, STONE)
        roof = np.maximum(np.maximum(np.abs(p[:, 0] - tx), np.abs(p[:, 2] - tz)) * 1.6 + (p[:, 1] - 160), 132 - p[:, 1]) * 0.5
        d, mat = _put(d, mat, roof, IRON)
        cq = p - [tx, 108, tz + 14.6]
        face = sdf.cylinder_y(cq @ sdf.rot_x(np.pi / 2), 11.0, 0.8, 0.3)
        rr, aa = np.hypot(cq[:, 0], cq[:, 1]), np.arctan2(cq[:, 0], cq[:, 1])
        ticks = (rr > 8.6) & (rr < 10.4) & (np.abs(((aa * 6 / np.pi) % 1.0) - 0.5) > 0.4)
        if glitch:
            hands = np.zeros(len(p), bool)
        else:
            hands = ((np.abs(cq[:, 0] * np.cos(2.6) - cq[:, 1] * np.sin(2.6)) < 0.8) & (cq[:, 0] * np.sin(2.6) + cq[:, 1] * np.cos(2.6) > -0.5) & (rr < 6.0)) \
                | ((np.abs(cq[:, 0]) < 0.7) & (cq[:, 1] > -0.5) & (rr < 8.4))
        d, mat = _put(d, mat, face, np.where(ticks | hands, SIGN_INK, CLOCK))
        d, mat = _put(d, mat, sdf.torus_y(cq @ sdf.rot_x(np.pi / 2), 11.2, 0.9), BRASS)
        # the lift shaft bolted to the front: two iron rails, cross-braces, the cage at the bottom
        sx, sz = tx + 26, tz + 10
        for dx in (-7.0, 7.0):
            d, mat = _put(d, mat, sdf.box(p - [sx + dx, 60, sz], (1.0, 60, 1.0), 0.2), IRON)
        for y in range(10, 118, 14):
            d, mat = _put(d, mat, sdf.capsule(p, (sx - 7, y, sz), (sx + 7, y + 12, sz), 0.5), IRON)
        d, mat = _put(d, mat, sdf.box(p - [sx, 121, sz - 2], (9, 2, 4), 0.4), IRON)
        d, mat = _put(d, mat, sdf.cylinder_y((p - [sx, 125, sz - 2]) @ sdf.rot_x(np.pi / 2), 3.4, 1.2, 0.4), BRASS)
        cage_y = 2.0
        cage = np.maximum(sdf.box(p - [sx, cage_y + 7, sz], (6.4, 7, 5.6), 0.4), -sdf.box(p - [sx, cage_y + 7, sz], (5.6, 6.2, 6.4)))
        d, mat = _put(d, mat, cage, HAZARD)
        d, mat = _put(d, mat, sdf.box(p - [sx, cage_y + 0.6, sz], (6.2, 0.6, 5.4), 0.2), IRON)
        crate = sdf.box(p - [sx, cage_y + 5.4, sz], (4.0, 4.0, 4.0), 0.5)
        d, mat = _put(d, mat, crate, CRATE)
        d, mat = _put(d, mat, sdf.capsule(p, (sx, cage_y + 14, sz), (sx, 119, sz), 0.35), IRON)
        door = sdf.box(p - [tx - 4, 11, tz + 14.2], (6, 11, 0.6), 1.0)
        d, mat = _put(d, mat, door, WOOD)
        for wy in (40.0, 70.0):
            d, mat = _put(d, mat, sdf.box(p - [tx - 4, wy, tz + 14.2], (3, 6, 0.6), 0.4), WINDOW)
        return d, mat
    objs.append(Obj(tower, (tx - 22, -1, tz - 20), (tx + 38, 164, tz + 20), "tower"))

    # Hoist's dockyard crane over the canal
    def crane(p):
        cx, cz = 130.0, -84.0
        d, mat = np.full(len(p), 1e9), np.full(len(p), HAZARD)
        for sx in (-1, 1):
            for sz in (-1, 1):
                d, mat = _put(d, mat, sdf.capsule(p, (cx + sx * 8, 0, cz + sz * 6), (cx + sx * 3, 70, cz + sz * 3), 1.0), HAZARD)
        for y in range(8, 70, 10):
            w = 8 - 5 * y / 70
            d, mat = _put(d, mat, sdf.capsule(p, (cx - w, y, cz + 6 - 3 * y / 70), (cx + w, y + 8, cz + 6 - 3 * y / 70), 0.5), HAZARD)
        cab = sdf.box(p - [cx, 74, cz], (7, 5, 6), 0.6)
        d, mat = _put(d, mat, cab, HAZARD)
        d, mat = _put(d, mat, sdf.box(p - [cx + 3, 75, cz + 6.2], (2.6, 2.4, 0.4), 0.3), WINDOW)
        jib = sdf.capsule(p, (cx - 30, 80, cz), (cx + 60, 80, cz), 1.4)
        d, mat = _put(d, mat, jib, HAZARD)
        d, mat = _put(d, mat, sdf.capsule(p, (cx, 92, cz), (cx + 58, 80.5, cz), 0.5), IRON)
        d, mat = _put(d, mat, sdf.capsule(p, (cx, 92, cz), (cx - 28, 80.5, cz), 0.5), IRON)
        d, mat = _put(d, mat, sdf.box(p - [cx - 26, 76, cz], (5, 4, 4), 0.4), STONE)
        hx = cx + 50
        hook_y = 34.0
        d, mat = _put(d, mat, sdf.capsule(p, (hx, 79, cz), (hx, hook_y + 3, cz), 0.35), IRON)
        hq = (p - [hx, hook_y, cz]) @ sdf.rot_x(np.pi / 2)
        d, mat = _put(d, mat, np.maximum(sdf.torus_y(hq, 2.4, 0.8), -(p[:, 0] - hx + 1.0)), IRON)
        load_y = hook_y - 10 + (14 if glitch else 0)
        load = sdf.box(p - [hx, load_y, cz], (6, 5, 5), 0.5)
        d, mat = _put(d, mat, load, CRATE)
        if not glitch:
            for sx in (-1, 1):
                d, mat = _put(d, mat, sdf.capsule(p, (hx, hook_y - 2, cz), (hx + sx * 5, load_y + 5, cz), 0.3), IRON)
        return d, mat
    objs.append(Obj(crane, (90, -1, -96), (196, 96, -72), "crane"))

    # Dynamo's generator shed with its coils and a spark gap
    def shed(p):
        x0, z0 = 262.0, -92.0
        body = sdf.box(p - [x0, 18, z0], (22, 18, 12), 0.8)
        d, mat = body, np.full(len(p), BRICK)
        roof = np.maximum(np.abs(p[:, 0] - x0) * 0.5 + (p[:, 1] - 46), np.maximum(36 - p[:, 1], np.abs(p[:, 2] - z0) - 15)) * 0.85
        d, mat = _put(d, mat, roof, IRON)
        for cy in (6.0, 14.0, 22.0):
            coil = sdf.torus_y((p - [x0 - 30, cy, z0 + 6]) @ sdf.rot_z(np.pi / 2), 4.6, 1.6)
            d, mat = _put(d, mat, coil, COIL)
        d, mat = _put(d, mat, sdf.capsule(p, (x0 - 30, 0, z0 + 6), (x0 - 30, 30, z0 + 6), 1.2), IRON)
        for sx in (-1, 1):
            d, mat = _put(d, mat, sdf.capsule(p, (x0 + 26 + sx * 4, 0, z0 + 8), (x0 + 26 + sx * 4, 26, z0 + 8), 0.8), IRON)
            d, mat = _put(d, mat, sdf.sphere(p, (x0 + 26 + sx * 4, 27, z0 + 8), 1.8), BRASS)
        pts = [(x0 + 22, 27, z0 + 8), (x0 + 24, 29, z0 + 8), (x0 + 26, 26, z0 + 8), (x0 + 28, 28.6, z0 + 8), (x0 + 30, 27, z0 + 8)]
        for a, b in zip(pts[:-1], pts[1:]):
            d, mat = _put(d, mat, sdf.capsule(p, a, b, 0.5), SPARK)
        win = sdf.box(p - [x0 + 6, 16, z0 + 12.2], (6, 6, 0.6), 0.6)
        d, mat = _put(d, mat, win, WINDOW)
        door = sdf.box(p - [x0 - 10, 10, z0 + 12.2], (5, 10, 0.6), 0.6)
        d, mat = _put(d, mat, door, IRON)
        return d, mat
    objs.append(Obj(shed, (226, -1, -108), (300, 52, -78), "shed"))

    # crates along the towpath: on the ground, or drifting up while the law is gone
    def crates(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), CRATE)
        for k, (x, z) in enumerate(((-170.0, -40.0), (-160.0, -44.0), (30.0, -36.0), (200.0, -30.0), (330.0, -40.0))):
            y = 4.0 + (10.0 + 7.0 * (k % 3) if glitch else 0.0)
            c = sdf.box((p - [x, y, z]) @ sdf.rot_y(0.3 * k) @ (sdf.rot_z(0.25 * (k % 2)) if glitch else np.eye(3)), (4.0, 4.0, 4.0), 0.5)
            d, mat = _put(d, mat, c, np.where(np.abs(np.abs(p[:, 1] - y) - 3.4) < 0.6, RUST, CRATE))
        return d, mat
    objs.append(Obj(crates, (-180, -1, -54), (340, 32, -24), "crates"))

    # the law sign and gas lamps on the towpath
    def dressing(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), IRON)
        x0, z0 = -6.0, -30.0
        d, mat = _put(d, mat, sdf.capsule(p, (x0, 0, z0), (x0, 22, z0), 0.9), IRON)
        bd = sdf.box(p - [x0, 30, z0], (26, 8, 0.9), 0.4)
        ink = (p[:, 2] > z0 + 0.7) & _tex(LAW_TEX, p, x0 - 24, x0 + 24, 37, 23)
        rub = p[:, 0] > x0 + 3 + 3 * np.sin(p[:, 1])
        d, mat = _put(d, mat, bd, np.where(ink, np.where(rub & glitch, GHOST, SIGN_INK), SIGN))
        for lx in (-320.0, -200.0, 60.0, 340.0):
            d, mat = _put(d, mat, sdf.capsule(p, (lx, 0, -8.0), (lx, 26, -8.0), 0.8), IRON)
            d, mat = _put(d, mat, sdf.box(p - [lx, 28.6, -8.0], (1.8, 2.4, 1.8), 0.4), LAMP)
        return d, mat
    objs.append(Obj(dressing, (-326, -1, -34), (346, 40, -4), "dressing"))

    sky = gradient_sky(W, H, "#2E2240", "#E8946A", glow=(360, 230, 360, "#FFC090"))
    lights = [Light((-300, 220, 240), "#FFC890", 1.0, 1100),
              Light((262.0 + 26, 28, -80), "#8AB4FF", 0.8, 60, shadow=False),
              *[Light((x, 28.0, -4.0), "#FFD27A", 0.4, 50, shadow=False) for x in (-320.0, -200.0, 60.0, 340.0)]]
    return dict(world=World(objs), materials=materials(), width=W, height=H, centre=CENTRE,
                lights=lights, key=0.62, ambient=0.22, top=170.0, ss=2, steps=170, sky=sky,
                bloom=[(WINDOW, "#FFC861", 8, 0.45), (LAMP, "#FFE680", 8, 0.5), (SPARK, "#B8D4FF", 8, 0.6),
                       (CLOCK, "#FFF4D8", 10, 0.4), (GHOST, "#7E70B8", 6, 0.35)])
