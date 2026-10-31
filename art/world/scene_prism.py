"""Prism Port, the Refraction chapter, at blue hour. 720x270, scrolls horizontally.

A harbour town built round light. Left to right: Frost's ice house on the quay with its ice sculptures; the
lighthouse on its rock, the crime scene, whose diamond lens was swapped; the great Prism on the headland
across the water, throwing a rainbow; Pane's glassworks and its glowing chimney; Geo's grotto under the cliff.

build(glitch=True)   refraction is erased: the beam kinks and wanders, the rainbow comes out in the wrong order,
                     the lighthouse lens sits dull
build(glitch=False)  after the case: the diamond lens blazes, the beam runs true, the rainbow is in order
Walkable quay: y = 0, z in [0, 30]. The harbour water lies behind it.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light, gradient_sky, stars
from src import sdf

(QUAY, QUAY_D, WATER, WATER_L, ROCK, ICE, ICE_D, BRICK, ROOF, WOOD, WINDOW, GLOW, LAMP, WHITE, RED, GLASS, SAPPH,
 BEAM, R1, R2, R3, R4, R5, R6, GHOST, SIGN, SIGN_INK, METAL, CLIFF, FAR, GRASS) = range(1, 32)

W, H = 720, 270
CENTRE = (0.0, 90.0)
HOTSPOTS = {"frost": -260, "stage": -90, "pane": 110, "geo": 250}
LH = (-90.0, -128.0)          # x, z of the lighthouse
LAMP_Y = 104.0
WL = -6.0                     # harbour water level


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _decal(text, font, w, h):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    b = d.textbbox((0, 0), text, font=font)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=font, fill=255)
    return np.array(im) > 100


GLASS_TEX = _decal("GLASS", _font("arialbd.ttf", 18), 72, 22)
LAW_TEX = _decal("n = sin i / sin r", _font("arialbd.ttf", 22), 176, 30)


def _tex(mask, p, x0, x1, ytop, ybot):
    hh, ww = mask.shape
    u = np.clip(((p[:, 0] - x0) / (x1 - x0) * (ww - 1)), 0, ww - 1).astype(int)
    v = np.clip(((ytop - p[:, 1]) / (ytop - ybot) * (hh - 1)), 0, hh - 1).astype(int)
    return mask[v, u]


def _put(d, mat, dd, mm):
    mat = np.where(dd < d, mm, mat)
    return np.minimum(d, dd), mat


RAINBOW = [R1, R2, R3, R4, R5, R6]


def materials():
    return {
        QUAY: dict(ramp=["#1A1C24", "#262833", "#343744", "#444858", "#565B6E", "#6A7088", "#808AA2"],
                   pattern=lambda p, n: np.sin(np.floor((p[:, 0] + 3.0 * (np.floor((p[:, 2] + 600) / 6.0) % 2) + 600) / 10.0) * 7.3
                                               + np.floor((p[:, 2] + 600) / 6.0) * 3.1), pattern_gain=0.12,
                   sub=(lambda p: (p[:, 1] < 0.5) & ((np.abs(((p[:, 0] + 3.0 * (np.floor((p[:, 2] + 600) / 6.0) % 2) + 600) % 10.0) - 5.0) > 4.55)
                                                       | (np.abs(((p[:, 2] + 600) % 6.0) - 3.0) > 2.65)), QUAY_D)),
        QUAY_D: dict(ramp=["#0E0F18", "#161824", "#1E2030"]),
        WATER: dict(ramp=["#0A1432", "#102048", "#182E62", "#22407E", "#2E549C", "#3E6CB8"], gloss=30, spec="#E6F0FF", dither=0.35,
                    pattern=lambda p, n: 0.7 * np.sin(p[:, 0] * 0.11 + np.sin(p[:, 2] * 0.13) * 2.0), pattern_gain=0.12,
                    sub=(lambda p: np.abs(((p[:, 2] + 300) % 11.0) - 5.5) > 5.1, WATER_L)),
        WATER_L: dict(ramp=["#3A4E86", "#5068A2", "#6A84BE", "#88A2D8"], gloss=20, spec="#FFFFFF"),
        ROCK: dict(ramp=["#16141E", "#201E2C", "#2C2A3C", "#3A374E", "#4A4662"],
                   pattern=lambda p, n: 0.5 * (np.abs(np.sin(p[:, 0] * 0.9) * np.sin(p[:, 1] * 0.8)) - 0.5), pattern_gain=0.2),
        ICE: dict(ramp=["#2E6A8E", "#4E94B8", "#7EBEDC", "#B4E0F2", "#E6F8FF"], gloss=36, spec="#FFFFFF"),
        ICE_D: dict(ramp=["#1E4A66", "#2E6A8E", "#4E94B8"]),
        BRICK: dict(ramp=["#2A1214", "#42191C", "#5E2426", "#7C3230", "#9A443C", "#B45A4C"],
                    sub=(lambda p: (np.abs(((p[:, 1] + 300) % 4.0) - 2.0) > 1.65) | (np.abs(((p[:, 0] + p[:, 2] + 2.0 * (np.floor((p[:, 1] + 300) / 4.0) % 2) + 300) % 8.0) - 4.0) > 3.6), ROOF)),
        ROOF: dict(ramp=["#140C14", "#20141E", "#2E1C2A", "#3C2636"]),
        WOOD: dict(ramp=["#1E1006", "#2E1A0D", "#462814", "#61381C", "#7E4A25"], pattern=lambda p, n: 0.45 * np.sin(p[:, 1] * 1.3 + p[:, 0] * 0.2), pattern_gain=0.12),
        WINDOW: dict(ramp=["#F2B44C", "#FFD27A", "#FFE9B0"], emissive=True),
        GLOW: dict(ramp=["#F07018", "#FFA830", "#FFD860"], emissive=True),
        LAMP: dict(ramp=["#BFE6FF", "#E8F6FF", "#FFFFFF"], emissive=True),
        WHITE: dict(ramp=["#3A3F50", "#5C6276", "#868CA2", "#B4B8C8", "#DCDFE8"]),
        RED: dict(ramp=["#3A0907", "#62110D", "#8E1A14", "#B8251C", "#DE3B2E"]),
        GLASS: dict(ramp=["#1C3D63", "#2F6496", "#4F8FC6", "#86BDE6", "#C2E1F3"], gloss=40, spec="#FFFFFF"),
        SAPPH: dict(ramp=["#2450C4", "#4A7EEA", "#8AB4FF"], emissive=True),
        BEAM: dict(ramp=["#8AB4E8", "#BCD8F8", "#E8F4FF"], emissive=True),
        R1: dict(ramp=["#E0261B", "#FF5A4A"], emissive=True), R2: dict(ramp=["#F07018", "#FFA050"], emissive=True),
        R3: dict(ramp=["#F2C621", "#FFE070"], emissive=True), R4: dict(ramp=["#2FA84F", "#60D07C"], emissive=True),
        R5: dict(ramp=["#2B7BC0", "#58A4E8"], emissive=True), R6: dict(ramp=["#5B2E8C", "#8A5ABE"], emissive=True),
        GHOST: dict(ramp=["#4A3E7A", "#62549A", "#7E70B8", "#9C8ED0"], emissive=True),
        SIGN: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8"]),
        SIGN_INK: dict(ramp=["#07090F", "#0E121D", "#161C2C"]),
        METAL: dict(ramp=["#0A0C10", "#15191F", "#222831", "#323A46", "#47515F", "#626E7F"], gloss=24, spec="#C8D4E2"),
        CLIFF: dict(ramp=["#2A2234", "#3A3048", "#4C405E", "#5E5274", "#72668C", "#887CA2"],
                    pattern=lambda p, n: 0.9 * (np.abs(((p[:, 1] + 400) % 9.0) - 4.5) > 3.9) - 0.4, pattern_gain=0.16),
        FAR: dict(ramp=["#1E2240", "#28305A", "#343E70", "#424E86"], dither=0.3),
        GRASS: dict(ramp=["#0C1A14", "#11261C", "#183426", "#204432"]),
    }


def build(glitch=True):
    objs = []

    def ground(p):
        quay = p[:, 2] > -36
        return np.where(quay, p[:, 1], p[:, 1] + 30.0), QUAY
    objs.append(Obj(lambda p: (p[:, 1], QUAY), (-400, -2, -38), (400, 0.2, 260), "quay"))
    objs.append(Obj(lambda p: (np.maximum(p[:, 1] - WL, -p[:, 2] - 340), WATER), (-400, WL - 2, -340), (400, WL + 0.2, -36), "water"))
    # the quay wall dropping to the water
    objs.append(Obj(lambda p: (np.maximum(sdf.box(p - [0, (WL - 2) / 2, -38.0], (400, (2 - WL) / 2 + 1, 2.0)), -1e9), QUAY),
                    (-400, WL - 4, -41), (400, 1.5, -35), "wall"))

    # the far shore: a dark headland with the great Prism on it
    def far(p):
        hill = np.maximum((p[:, 1] - (18 + 14 * np.sin(p[:, 0] * 0.012 + 0.6) + 6 * np.sin(p[:, 0] * 0.05))) * 0.7, np.abs(p[:, 2] + 300) - 30)
        d, mat = hill, np.full(len(p), FAR)
        q = p - [120.0, 30.0, -290.0]
        tri = np.maximum.reduce([np.abs(q[:, 2]) - 10.0, q[:, 1] * 0.5 + np.abs(q[:, 0]) * 0.866 - 22.0, -q[:, 1] - 6.0])
        d, mat = _put(d, mat, tri, GLASS)
        return d, mat
    objs.append(Obj(far, (-420, WL - 1, -335), (420, 80, -265), "far"))

    # the rainbow fanning out of the Prism across the evening sky
    def rainbow(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), R1)
        cx, cy, cz = 120.0, 40.0, -292.0
        order = [R1, R2, R3, R4, R5, R6] if not glitch else [R4, R1, R6, R3, R2, R5]
        a = np.arctan2(p[:, 1] - cy, p[:, 0] - cx)
        rr = np.hypot(p[:, 0] - cx, p[:, 1] - cy)
        for k, m in enumerate(order):
            ang = 0.25 + 0.075 * k + (0.06 * np.sin(rr * 0.12 + k) if glitch else 0.0)
            band = np.maximum.reduce([np.abs(a - ang) * rr - 2.4, 30.0 - rr, rr - 220.0, np.abs(p[:, 2] - cz) - 0.5])
            d, mat = _put(d, mat, band, m)
        return d, mat
    objs.append(Obj(rainbow, (100, 30, -300), (380, 200, -284), "rainbow"))

    # the lighthouse on its rock; the lens room on top
    lx, lz = LH

    def lighthouse(p):
        rock = sdf.ellipsoid(p, (lx, WL - 4, lz), (48, 20, 30)) + 1.4 * np.sin(p[:, 0] * 0.3) * np.sin(p[:, 2] * 0.4)
        d, mat = rock, np.full(len(p), ROCK)
        body = sdf.round_cone(p, (lx, 0, lz), (lx, 86, lz), 15.0, 10.0)
        stripes = (np.floor((p[:, 1] + 300) / 14.0) % 2) == 0
        d, mat = _put(d, mat, body, np.where(stripes, WHITE, RED))
        gallery = sdf.cylinder_y(p - [lx, 90, lz], 14.0, 1.4, 0.4)
        d, mat = _put(d, mat, gallery, METAL)
        rail = np.maximum(np.abs(np.hypot(p[:, 0] - lx, p[:, 2] - lz) - 13.4) - 0.4, np.abs(p[:, 1] - 95) - 3.6)
        rail = np.maximum(rail, -(np.abs(((np.arctan2(p[:, 2] - lz, p[:, 0] - lx) * 10) % 1.0) - 0.5) - 0.38) * 6)
        d, mat = _put(d, mat, rail, METAL)
        room = sdf.cylinder_y(p - [lx, 104, lz], 9.0, 8.0, 0.6)
        frames = np.abs(((np.arctan2(p[:, 2] - lz, p[:, 0] - lx) * 8 / (2 * np.pi)) % 1.0) - 0.5) > 0.42
        d, mat = _put(d, mat, room, np.where(frames, METAL, GLASS))
        lens = sdf.sphere(p, (lx, LAMP_Y, lz + 2), 5.6)
        d, mat = _put(d, mat, lens, GHOST if glitch else LAMP)
        roof = np.maximum(np.hypot(p[:, 0] - lx, p[:, 2] - lz) - (11.0 - 0.9 * (p[:, 1] - 112)), np.maximum(112 - p[:, 1], p[:, 1] - 124)) * 0.7
        d, mat = _put(d, mat, roof, RED)
        d, mat = _put(d, mat, sdf.sphere(p, (lx, 125.5, lz), 1.6), METAL)
        door = sdf.box(p - [lx, 8, lz + 14.6], (4.4, 8, 0.8), 0.8)
        d, mat = _put(d, mat, door, WOOD)
        for wy in (34.0, 60.0):
            d, mat = _put(d, mat, sdf.box(p - [lx, wy, lz + 13.6 - (wy - 34) * 0.06], (2.2, 3.6, 0.6), 0.4), WINDOW)
        return d, mat
    objs.append(Obj(lighthouse, (lx - 52, WL - 25, lz - 34), (lx + 52, 128, lz + 34), "lighthouse"))

    # the beam: true and straight once the law is back; kinked and wandering while it's gone
    def beam(p):
        o = np.array([lx - 6.0, LAMP_Y, lz + 2])
        d = np.full(len(p), 1e9)
        if not glitch:
            q = p - o
            t = np.clip(-q[:, 0] / 260.0, 0, 1)
            width = 1.0 + 3.6 * t
            dd = np.maximum.reduce([np.hypot(q[:, 1] - (-0.06 * -q[:, 0]) * 0 - 0.05 * -q[:, 0], q[:, 2]) - width, q[:, 0], -q[:, 0] - 260])
            return dd * 0.7, BEAM
        pts = [o, o + [-40, 14, 0], o + [-70, -6, 4], o + [-115, 22, 0], o + [-150, 2, -4], o + [-200, 30, 0]]
        for a, b in zip(pts[:-1], pts[1:]):
            d = np.minimum(d, sdf.capsule(p, a, b, 1.6))
        return d, GHOST
    objs.append(Obj(beam, (lx - 270, LAMP_Y - 30, lz - 20), (lx, LAMP_Y + 40, lz + 20), "beam"))

    # Frost's ice house and its sculptures
    def icehouse(p):
        x0, z0 = -262.0, -88.0
        body = sdf.box(p - [x0, 20, z0], (30, 20, 13), 1.2)
        bricks = (np.abs(((p[:, 1] + 300) % 6.0) - 3.0) > 2.6) | (np.abs(((p[:, 0] + 3.0 * (np.floor((p[:, 1] + 300) / 6.0) % 2) + 300) % 10.0) - 5.0) > 4.6)
        d, mat = body, np.where(bricks, ICE_D, ICE)
        roof = np.maximum(sdf.ellipsoid(p, (x0, 40, z0), (32.0, 12.0, 15.0)), 40 - p[:, 1])
        d, mat = _put(d, mat, roof, WHITE)
        door = sdf.box(p - [x0 + 12, 11, z0 + 13.4], (6, 11, 0.8), 1.0)
        d, mat = _put(d, mat, door, ICE_D)
        win = sdf.box(p - [x0 - 14, 22, z0 + 13.4], (6, 5, 0.6), 0.8)
        d, mat = _put(d, mat, win, WINDOW)
        # an ice swan on a plinth and an ice obelisk out front
        sx, sz = x0 - 36.0, -54.0
        d, mat = _put(d, mat, sdf.box(p - [sx, 3, sz], (6, 3, 5), 0.6), QUAY)
        swan = np.minimum(sdf.ellipsoid(p, (sx, 9.5, sz), (5.0, 3.2, 3.0)), sdf.capsule(p, (sx + 3.0, 10.0, sz), (sx + 4.4, 17.0, sz), 1.0))
        swan = np.minimum(swan, sdf.ellipsoid(p, (sx + 5.4, 17.4, sz), (1.8, 1.2, 1.0)))
        d, mat = _put(d, mat, swan, ICE)
        ob = np.maximum(np.maximum(np.abs(p[:, 0] - x0 - 40), np.abs(p[:, 2] + 56)) - (3.4 - 0.1 * p[:, 1]), np.abs(p[:, 1] - 12) - 12)
        d, mat = _put(d, mat, ob * 0.8, ICE)
        return d, mat
    objs.append(Obj(icehouse, (-306, -1, -104), (-214, 54, -48), "icehouse"))

    # Pane's glassworks: brick, a tall chimney glowing at the top, the furnace mouth, bottles in the window
    def glassworks(p):
        x0, z0 = 112.0, -96.0
        body = sdf.box(p - [x0, 22, z0], (32, 22, 13), 0.8)
        d, mat = body, np.full(len(p), BRICK)
        roof = np.maximum(np.abs(p[:, 0] - x0) * 0.5 + (p[:, 1] - 56), np.maximum(44 - p[:, 1], np.abs(p[:, 2] - z0) - 15)) * 0.85
        d, mat = _put(d, mat, roof, ROOF)
        chim = sdf.round_cone(p, (x0 + 20, 40, z0 - 4), (x0 + 20, 96, z0 - 4), 6.0, 4.0)
        d, mat = _put(d, mat, chim, BRICK)
        d, mat = _put(d, mat, sdf.cylinder_y(p - [x0 + 20, 97, z0 - 4], 4.4, 1.2, 0.4), GLOW)
        mouth = sdf.box(p - [x0 - 14, 10, z0 + 13.4], (8, 10, 0.8), 3.0)
        d, mat = _put(d, mat, mouth, GLOW)
        win = sdf.box(p - [x0 + 14, 22, z0 + 13.4], (10, 7, 0.6), 0.6)
        d, mat = _put(d, mat, win, WINDOW)
        for k, m in enumerate((R5, R3, R4, R1)):
            bx = x0 + 6.5 + 5.0 * k
            bottle = np.minimum(sdf.cylinder_y(p - [bx, 18.5, z0 + 14.2], 1.7, 3.0, 0.6), sdf.capsule(p, (bx, 21.5, z0 + 14.2), (bx, 24.5, z0 + 14.2), 0.6))
            d, mat = _put(d, mat, bottle, m)
        sign = sdf.box(p - [x0, 38, z0 + 13.6], (18, 5.5, 0.8), 0.4)
        d, mat = _put(d, mat, sign, np.where(_tex(GLASS_TEX, p, x0 - 17, x0 + 17, 42.5, 33.5) & (p[:, 2] > z0 + 14.2), SIGN_INK, SIGN))
        return d, mat
    objs.append(Obj(glassworks, (76, -1, -114), (150, 100, -80), "glassworks"))

    # Geo's grotto: a cliff on the right with a cave mouth full of glowing sapphire
    def grotto(p):
        cliff = sdf.box(p - [312, 36, -132], (70, 36, 30), 6.0)
        cliff += 2.4 * np.sin(p[:, 1] * 0.3 + p[:, 0] * 0.07) * np.sin(p[:, 2] * 0.25)
        top = p[:, 1] - (58 + 12 * np.sin(p[:, 0] * 0.05 + 1.0))
        cliff = np.maximum(cliff, top * 0.7)
        cliff = np.maximum(cliff, ((236 - p[:, 0]) + 0.5 * p[:, 1]) * 0.8)
        cave = sdf.ellipsoid(p, (266.0, 12.0, -102.0), (17.0, 20.0, 22.0))
        d, mat = np.maximum(cliff, -cave), np.full(len(p), CLIFF)
        rng = np.random.default_rng(9)
        for _ in range(9):
            b = np.array([rng.uniform(254, 278), rng.uniform(0, 4), rng.uniform(-110, -98)])
            tip = b + [rng.uniform(-3, 3), rng.uniform(7, 15), rng.uniform(-1, 2)]
            d, mat = _put(d, mat, sdf.round_cone(p, b, tip, 2.0, 0.4), SAPPH)
        lamp = sdf.sphere(p, (290.0, 26.0, -84.0), 1.8)
        d, mat = _put(d, mat, lamp, WINDOW)
        d, mat = _put(d, mat, sdf.capsule(p, (290.0, 0, -84.0), (290.0, 24.0, -84.0), 0.6), METAL)
        return d, mat
    objs.append(Obj(grotto, (215, -1, -184), (400, 110, -82), "grotto"))

    # the law board on the quay
    def board(p):
        x0, z0 = 0.0, -60.0
        d, mat = np.full(len(p), 1e9), np.full(len(p), WOOD)
        for x in (x0 - 40, x0 + 40):
            d, mat = _put(d, mat, sdf.box(p - [x, 14, z0 - 1], (1.4, 14, 1.4), 0.4), WOOD)
        bd = sdf.box(p - [x0, 36, z0], (48, 12, 1.0), 0.5)
        ink = (p[:, 2] > z0 + 0.8) & _tex(LAW_TEX, p, x0 - 46, x0 + 46, 46, 26)
        rub = p[:, 0] > x0 - 6 + 4 * np.sin(p[:, 1] * 0.8)
        d, mat = _put(d, mat, bd, np.where(ink, np.where(rub & glitch, GHOST, SIGN_INK), SIGN))
        return d, mat
    objs.append(Obj(board, (-52, -1, -64), (52, 50, -56), "board"))

    # the quay's edge: a chain railing, lamps, and cargo waiting by the glassworks
    LAMPS = (-185.0, 36.0, 196.0)

    def dressing(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), METAL)
        for x in range(-360, 380, 30):
            d, mat = _put(d, mat, sdf.cylinder_y(p - [x, 5, -33.0], 1.4, 5.0, 0.5), METAL)
        for x in range(-360, 350, 30):
            t = (p[:, 0] - x) / 30.0
            sag = 8.0 - 3.0 * 4 * np.clip(t, 0, 1) * (1 - np.clip(t, 0, 1))
            chain = np.maximum(np.hypot(p[:, 1] - sag, p[:, 2] + 33.0) - 0.45, np.maximum(x - p[:, 0], p[:, 0] - x - 30))
            d, mat = _put(d, mat, chain, METAL)
        for x in LAMPS:
            d, mat = _put(d, mat, sdf.capsule(p, (x, 0, -28.0), (x, 30.0, -28.0), 1.0), METAL)
            d, mat = _put(d, mat, sdf.sphere(p, (x, 32.0, -28.0), 2.6), WINDOW)
            d, mat = _put(d, mat, sdf.cylinder_y(p - [x, 35.4, -28.0], 3.0, 0.6, 0.3), METAL)
        for cx, cy, cz in ((150.0, 4.0, -24.0), (160.0, 4.0, -24.0), (155.0, 12.0, -24.0)):
            crate = sdf.box(p - [cx, cy, cz], (4.0, 4.0, 4.0), 0.4)
            d, mat = _put(d, mat, crate, np.where(np.abs(np.abs(p[:, 0] - cx) - 3.4) < 0.6, ROOF, WOOD))
        coil = sdf.torus_y(p - [-120.0, 1.4, -26.0], 4.4, 1.4)
        d, mat = _put(d, mat, coil, SIGN)
        for bx in (-60.0, -52.0):
            barrel = sdf.cylinder_y(p - [bx, 5.0, -24.0], 3.4 - 0.02 * (p[:, 1] - 5.0) ** 2, 5.0, 0.6)
            d, mat = _put(d, mat, barrel, np.where(np.abs(np.abs(p[:, 1] - 5.0) - 3.0) < 0.6, METAL, WOOD))
        return d, mat
    objs.append(Obj(dressing, (-362, -1, -36), (362, 40, -18), "dressing"))

    # mooring posts in the shallows by the quay
    def posts(p):
        d = np.full(len(p), 1e9)
        for x in (-180.0, -40.0, 40.0, 180.0):
            d = np.minimum(d, sdf.cylinder_y(p - [x, WL + 4, -46.0], 2.2, 10.0, 0.6))
        return d, WOOD
    objs.append(Obj(posts, (-186, WL - 8, -50), (186, 16, -42), "posts"))

    sky = gradient_sky(W, H, "#120E2E", "#4A3A78", glow=(420, 150, 360, "#8A5A9E"))
    stars(sky, 110, seed=21, ymax=90)
    lights = [Light((-300, 240, 220), "#B8C8FF", 1.0, 1000),
              Light((lx, LAMP_Y, lz + 14), "#E8F4FF", 0.9 if not glitch else 0.3, 160, shadow=False),
              Light((112.0 - 14, 12, -80), "#FFA040", 0.8, 70, shadow=False),
              Light((266.0, 14, -84), "#6A9AFF", 1.0, 70, shadow=False),
              *[Light((x, 32.0, -22.0), "#FFD27A", 0.5, 50, shadow=False) for x in (-185.0, 36.0, 196.0)]]
    return dict(world=World(objs), materials=materials(), width=W, height=H, centre=CENTRE,
                lights=lights, key=0.55, ambient=0.18, top=150.0, ss=2, steps=170, sky=sky,
                bloom=[(WINDOW, "#FFC861", 8, 0.45), (GLOW, "#FF8A30", 10, 0.55), (LAMP, "#E8F4FF", 18, 0.7),
                       (BEAM, "#BCD8F8", 10, 0.4), (SAPPH, "#4A7EEA", 8, 0.5), (GHOST, "#7E70B8", 8, 0.4)])
