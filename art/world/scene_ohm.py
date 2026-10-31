"""Ohmtown, the Electricity chapter, on festival night. 720x270, scrolls horizontally.

A town wired like a circuit board: copper traces run down the street between solder pads, the power station
hums on the hill with its pylons, and every building is a component. Left to right: Volta's Battery Barn; the
Grand Light Board, the crime scene, with its festival marquee; Ohmar's Resistor Works; Glim's domed Lamp Shop.

build(glitch=True)   Ohm's law is erased: blackout, every bulb dead, sparks frozen in mid-air over the board
build(glitch=False)  after the case: the marquee and the string lights blaze, windows lit up and down the street
Walkable street: y = 0, z in [0, 30].
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light, gradient_sky, stars, moon
from src import sdf

(STREET, TRACE, PAD, BRICK, BRICK_D, GRAPH, COPPER, METAL, WINDOW, DARKWIN, LAMP, BULB_OFF, BOARD, SIGN, SIGN_INK,
 GHOST, TAN, RBAND, KBAND, GBAND, GLASS, CONCRETE, HILL, WIRE, WOOD, RED) = range(1, 27)

W, H = 720, 270
CENTRE = (0.0, 90.0)
HOTSPOTS = {"volta": -260, "stage": -90, "ohmar": 110, "glim": 250}
BOARD_X, BOARD_Z = -90.0, -64.0


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _decal(text, font, w, h):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    b = d.textbbox((0, 0), text, font=font)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=font, fill=255)
    return np.array(im) > 100


LAW_TEX = _decal("V = IR", _font("arialbd.ttf", 34), 112, 38)
FEST_TEX = _decal("FESTIVAL", _font("arialbd.ttf", 18), 120, 22)


def _tex(mask, p, x0, x1, ytop, ybot):
    hh, ww = mask.shape
    u = np.clip(((p[:, 0] - x0) / (x1 - x0) * (ww - 1)), 0, ww - 1).astype(int)
    v = np.clip(((ytop - p[:, 1]) / (ytop - ybot) * (hh - 1)), 0, hh - 1).astype(int)
    return mask[v, u]


def _put(d, mat, dd, mm):
    mat = np.where(dd < d, mm, mat)
    return np.minimum(d, dd), mat


def _traces(p):
    """Copper traces: two long runs along the street, and a branch up to each building."""
    x, z = p[:, 0], p[:, 2]
    runs = (np.abs(z + 12.0) < 0.8) | (np.abs(z - 38.0) < 0.8)
    branch = np.zeros(len(p), bool)
    for bx in (-262.0, -90.0, 110.0, 254.0):
        branch |= (np.abs(x - bx - 6.0) < 0.8) & (z < -12.0) & (z > -80.0)
        branch |= (np.abs(x - bx + 6.0) < 0.8) & (z < -12.0) & (z > -80.0)
    vias = (np.hypot(((x + 600) % 23.0) - 11.5, ((z + 600) % 23.0) - 11.5) < 0.9) & (z < -16)
    return runs | branch | vias


def materials(glitch):
    lit = WINDOW if not glitch else DARKWIN
    return lit, {
        STREET: dict(ramp=["#0E1A14", "#14261C", "#1C3426", "#264432", "#30543E", "#3C664A"],
                     pattern=lambda p, n: 0.4 * np.sin(p[:, 0] * 0.6) * np.sin(p[:, 2] * 0.7), pattern_gain=0.06,
                     sub=(lambda p: (p[:, 1] < 0.5) & _traces(p), TRACE)),
        TRACE: dict(ramp=["#5A3410", "#8A5418", "#B87A2A", "#DCA048"], gloss=20, spec="#FFE8B0"),
        PAD: dict(ramp=["#7A7A86", "#A4A4B0", "#C8C8D4", "#E6E6F0"], gloss=30, spec="#FFFFFF"),
        BRICK: dict(ramp=["#24121A", "#381A24", "#4E2430", "#66303C", "#7E3E48"],
                    sub=(lambda p: (np.abs(((p[:, 1] + 300) % 4.0) - 2.0) > 1.65) | (np.abs(((p[:, 0] + p[:, 2] + 2.0 * (np.floor((p[:, 1] + 300) / 4.0) % 2) + 300) % 8.0) - 4.0) > 3.6), BRICK_D)),
        BRICK_D: dict(ramp=["#10080C", "#1A0E14", "#24121A"]),
        GRAPH: dict(ramp=["#0A0A10", "#14141C", "#1E1E28", "#2A2A36", "#383846"], gloss=16, spec="#A0A0C0"),
        COPPER: dict(ramp=["#5A2408", "#8A3C10", "#BC5C1C", "#E4843A", "#FCB06A"], gloss=24, spec="#FFE2C0"),
        METAL: dict(ramp=["#0A0C10", "#15191F", "#222831", "#323A46", "#47515F", "#626E7F"], gloss=24, spec="#C8D4E2"),
        WINDOW: dict(ramp=["#F2B44C", "#FFD27A", "#FFE9B0"], emissive=True),
        DARKWIN: dict(ramp=["#0A0E1C", "#121830", "#1C2444", "#283258"], gloss=40, spec="#8090C0"),
        LAMP: dict(ramp=["#FFD860", "#FFF0A8", "#FFFCE0"], emissive=True),
        BULB_OFF: dict(ramp=["#2A2A30", "#3E3E46", "#55555E", "#6E6E78"], gloss=40, spec="#C0C0D0"),
        BOARD: dict(ramp=["#0A1028", "#101A3A", "#18244C", "#22305E", "#2E3E72"]),
        SIGN: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8"]),
        SIGN_INK: dict(ramp=["#07090F", "#0E121D", "#161C2C"]),
        GHOST: dict(ramp=["#6A9AFF", "#A8C8FF", "#E8F2FF"], emissive=True),
        TAN: dict(ramp=["#5A4020", "#86622E", "#B08A48", "#D2AE6A", "#EED092"]),
        RBAND: dict(ramp=["#5E100C", "#8E1A14", "#C9302A", "#EE5A4C"]),
        KBAND: dict(ramp=["#08080A", "#121216", "#1E1E24", "#2C2C34"]),
        GBAND: dict(ramp=["#7A5A12", "#B8891E", "#E6B43A", "#F8D66E"]),
        GLASS: dict(ramp=["#1C3D63", "#2F6496", "#4F8FC6", "#86BDE6", "#C2E1F3"], gloss=40, spec="#FFFFFF"),
        CONCRETE: dict(ramp=["#1C1E28", "#282A36", "#363846", "#464858", "#585A6C"]),
        HILL: dict(ramp=["#0A1410", "#0E1C16", "#14261C", "#1A3024"], dither=0.3),
        WIRE: dict(ramp=["#05060A", "#0A0C12", "#12141C"]),
        WOOD: dict(ramp=["#1E1006", "#2E1A0D", "#462814", "#61381C", "#7E4A25"]),
        RED: dict(ramp=["#3A0907", "#62110D", "#8E1A14", "#B8251C", "#DE3B2E"]),
    }


def build(glitch=True):
    lit, mats = materials(glitch)
    objs = []

    def ground(p):
        pad = np.zeros(len(p), bool)
        for bx in (-262.0, -90.0, 110.0, 254.0):
            for sx in (-6.0, 6.0):
                r = np.hypot(p[:, 0] - bx - sx, p[:, 2] + 12.0)
                pad |= (r < 2.8) & (r > 1.1)
        return p[:, 1], np.where(pad, PAD, STREET)
    objs.append(Obj(ground, (-400, -2, -340), (400, 0.2, 260), "ground"))

    # the hill behind, the power station and its pylons
    def hill(p):
        h = np.maximum((p[:, 1] - (20 + 16 * np.sin(p[:, 0] * 0.01 + 1.0) + 7 * np.sin(p[:, 0] * 0.043))) * 0.7, np.abs(p[:, 2] + 290) - 40)
        d, mat = h, np.full(len(p), HILL)
        cx, cz = 40.0, -250.0
        tower = np.maximum(np.hypot(p[:, 0] - cx, p[:, 2] - cz) - (18 - 0.18 * p[:, 1] + 0.0028 * p[:, 1] ** 2), np.abs(p[:, 1] - 40) - 40)
        d, mat = _put(d, mat, tower * 0.8, CONCRETE)
        hall = sdf.box(p - [cx + 50, 24, cz + 6], (26, 24, 14), 1.0)
        d, mat = _put(d, mat, hall, CONCRETE)
        for wx in (-14.0, 0.0, 14.0):
            d, mat = _put(d, mat, sdf.box(p - [cx + 50 + wx, 30, cz + 20.4], (3, 5, 0.6), 0.4), lit)
        stacks = np.minimum(sdf.cylinder_y(p - [cx + 64, 60, cz], 3.4, 16, 0.4), sdf.cylinder_y(p - [cx + 72, 56, cz], 3.0, 12, 0.4))
        d, mat = _put(d, mat, stacks, RED)
        return d, mat
    objs.append(Obj(hill, (-420, -1, -335), (420, 85, -245), "hill"))

    PYLONS = (-300.0, -150.0, 150.0, 300.0)

    def pylons(p):
        d = np.full(len(p), 1e9)
        for x in PYLONS:
            z = -200.0
            for sx in (-1, 1):
                d = np.minimum(d, sdf.capsule(p, (x + sx * 7, 0, z), (x + sx * 1.5, 62, z), 0.8))
            for y, w in ((20.0, 5.6), (36.0, 4.0), (52.0, 9.0), (60.0, 6.0)):
                d = np.minimum(d, sdf.capsule(p, (x - w, y, z), (x + w, y, z), 0.6))
            for y0, y1 in ((0.0, 20.0), (20.0, 36.0), (36.0, 52.0)):
                w0, w1 = 7 - 5.5 * y0 / 62, 7 - 5.5 * y1 / 62
                d = np.minimum(d, sdf.capsule(p, (x - w0, y0, z), (x + w1, y1, z), 0.4))
        for a, b in zip(PYLONS[:-1], PYLONS[1:]):
            for yy in (52.0, 60.0):
                t = np.clip((p[:, 0] - a) / (b - a), 0, 1)
                wire = np.maximum(np.hypot(p[:, 1] - (yy - 9 * 4 * t * (1 - t)), p[:, 2] + 200) - 0.5, np.maximum(a - p[:, 0], p[:, 0] - b))
                d = np.minimum(d, wire)
        return d, METAL
    objs.append(Obj(pylons, (-312, -1, -206), (312, 66, -194), "pylons"))

    # Volta's Battery Barn: a giant standing cell with a copper dome
    def barn(p):
        x0, z0 = -262.0, -104.0
        body = sdf.cylinder_y(p - [x0, 26, z0], 26.0, 26.0, 2.0)
        d, mat = body, np.where(p[:, 1] > 36, COPPER, GRAPH)
        dome = np.maximum(sdf.ellipsoid(p, (x0, 52, z0), (26.0, 12.0, 26.0)), 52 - p[:, 1])
        d, mat = _put(d, mat, dome, COPPER)
        term = sdf.cylinder_y(p - [x0, 66, z0], 7.0, 4.0, 1.0)
        d, mat = _put(d, mat, term, METAL)
        plus = np.minimum(sdf.box(p - [x0, 44, z0 + 25.4], (6, 1.6, 1.0)), sdf.box(p - [x0, 44, z0 + 25.4], (1.6, 6, 1.0)))
        d, mat = _put(d, mat, plus, GBAND)
        door = sdf.box(p - [x0, 10, z0 + 25.4], (6, 10, 1.0), 1.0)
        d, mat = _put(d, mat, door, METAL)
        for wx in (-16.0, 16.0):
            d, mat = _put(d, mat, sdf.box(p - [x0 + wx, 22, z0 + 20.2 + abs(wx) * 0.0], (4, 5, 1.0), 0.5), lit)
        return d, mat
    objs.append(Obj(barn, (-292, -1, -134), (-232, 72, -76), "barn"))

    # the Grand Light Board: a marquee of bulbs on a navy board, dials, and the slot that took the wrong part
    def board(p):
        x0, z0 = BOARD_X, BOARD_Z
        d, mat = np.full(len(p), 1e9), np.full(len(p), METAL)
        for x in (x0 - 34, x0 + 34):
            d, mat = _put(d, mat, sdf.box(p - [x, 14, z0 - 2], (1.6, 14, 1.6), 0.4), METAL)
        panel = sdf.box(p - [x0, 40, z0], (38, 16, 2.0), 0.8)
        d, mat = _put(d, mat, panel, BOARD)
        sign = sdf.box(p - [x0, 66, z0], (30, 6, 1.2), 0.5)
        d, mat = _put(d, mat, sign, np.where(_tex(FEST_TEX, p, x0 - 28, x0 + 28, 70.5, 61.5) & (p[:, 2] > z0 + 1.0), RBAND, SIGN))
        for k in range(15):
            bx = x0 - 35 + 5.0 * k
            for by in (55.0, 25.0):
                d, mat = _put(d, mat, sdf.sphere(p, (bx, by, z0 + 2.2), 1.7), LAMP if not glitch else BULB_OFF)
        for k, dx in enumerate((-22.0, -8.0, 8.0)):
            dial = sdf.cylinder_y((p - [x0 + dx, 42, z0 + 2.2]) @ sdf.rot_x(np.pi / 2), 5.0, 0.4, 0.3)
            rr = np.hypot(p[:, 0] - x0 - dx, p[:, 1] - 42)
            needle = (np.abs((p[:, 0] - x0 - dx) * np.cos(0.6 + k) - (p[:, 1] - 42) * np.sin(0.6 + k)) < 0.5) & (rr < 4.2)
            d, mat = _put(d, mat, dial, np.where(needle, RBAND, SIGN))
        slot = sdf.box(p - [x0 + 22, 40, z0 + 2.0], (8.0, 3.0, 0.8), 0.4)
        d, mat = _put(d, mat, slot, KBAND)
        part = sdf.capsule(p, (x0 + 16.5, 40, z0 + 2.8), (x0 + 27.5, 40, z0 + 2.8), 1.4)
        y = p[:, 0] - x0
        d, mat = _put(d, mat, part, np.where(np.abs(y - 19.5) < 0.6, RBAND, np.where(np.abs(y - 22) < 0.6, KBAND, TAN)))
        # the string lights from the board out over the street
        for a, b in (((x0 - 34, 70.0, z0), (-262.0, 74.0, -84.0)), ((x0 + 34, 70.0, z0), (110.0, 66.0, -84.0))):
            a, b = np.array(a), np.array(b)
            t = np.clip(((p - a) @ (b - a)) / ((b - a) @ (b - a)), 0, 1)
            sag = a + (b - a) * t[:, None] - np.array([0, 10.0, 0]) * (4 * t * (1 - t))[:, None]
            wire = np.linalg.norm(p - sag, axis=1) - 0.4
            d, mat = _put(d, mat, wire, WIRE)
            for k in range(1, 12):
                tk = k / 12
                c = a + (b - a) * tk - np.array([0, 10.0 * 4 * tk * (1 - tk) + 1.6, 0])
                d, mat = _put(d, mat, sdf.sphere(p, c, 1.2), LAMP if not glitch else BULB_OFF)
        return d, mat
    objs.append(Obj(board, (-270, -1, -90), (120, 78, -55), "board"))

    # Ohmar's Resistor Works: brick, a smokestack, a giant resistor on the roof
    def works(p):
        x0, z0 = 110.0, -104.0
        body = sdf.box(p - [x0, 22, z0], (34, 22, 14), 0.8)
        d, mat = body, np.full(len(p), BRICK)
        saw = np.maximum(np.abs(((p[:, 0] - x0 + 600) % 17.0) - 8.5) * 0.9 + (p[:, 1] - 52), np.maximum(44 - p[:, 1], np.maximum(np.abs(p[:, 0] - x0) - 34, np.abs(p[:, 2] - z0) - 15)))
        d, mat = _put(d, mat, saw * 0.8, CONCRETE)
        stack = sdf.round_cone(p, (x0 - 24, 40, z0 - 4), (x0 - 24, 84, z0 - 4), 5.0, 3.6)
        d, mat = _put(d, mat, stack, BRICK)
        rq = p - [x0 + 8, 60, z0 - 2]
        res = sdf.smin(sdf.capsule(rq, (-14, 0, 0), (14, 0, 0), 5.0), np.minimum(sdf.sphere(rq, (-15, 0, 0), 6.4), sdf.sphere(rq, (15, 0, 0), 6.4)), 2.0)
        bx = rq[:, 0]
        band = np.where(np.abs(bx + 10) < 1.4, RBAND, np.where(np.abs(bx + 5) < 1.4, KBAND, np.where(np.abs(bx) < 1.4, KBAND, np.where(np.abs(bx - 9) < 1.2, GBAND, TAN))))
        d, mat = _put(d, mat, res, band)
        for sx in (-1, 1):
            d, mat = _put(d, mat, sdf.capsule(rq, (sx * 20, 0, 0), (sx * 24, -12, 0), 0.8), METAL)
        for wx in (-20.0, -6.0, 8.0, 22.0):
            d, mat = _put(d, mat, sdf.box(p - [x0 + wx, 24, z0 + 14.2], (4, 6, 0.6), 0.4), lit)
        door = sdf.box(p - [x0 + 14, 9, z0 + 14.2], (7, 9, 0.6), 0.6)
        d, mat = _put(d, mat, door, WOOD)
        return d, mat
    objs.append(Obj(works, (72, -1, -122), (148, 90, -86), "works"))

    # Glim's Lamp Shop under its glass dome
    def lampshop(p):
        x0, z0 = 254.0, -102.0
        body = sdf.cylinder_y(p - [x0, 18, z0], 24.0, 18.0, 1.0)
        d, mat = body, np.full(len(p), BRICK)
        dome = np.maximum(sdf.sphere(p, (x0, 36, z0), 24.0), 36 - p[:, 1])
        ribs = np.abs(((np.arctan2(p[:, 2] - z0, p[:, 0] - x0) * 10 / (2 * np.pi)) % 1.0) - 0.5) > 0.44
        d, mat = _put(d, mat, dome, np.where(ribs, METAL, lit if not glitch else GLASS))
        finial = sdf.round_cone(p, (x0, 60, z0), (x0, 68, z0), 2.4, 0.8)
        d, mat = _put(d, mat, finial, COPPER)
        win = sdf.box(p - [x0 - 12, 18, z0 + 22.4], (6, 7, 0.8), 1.0)
        d, mat = _put(d, mat, win, lit)
        door = sdf.box(p - [x0 + 10, 10, z0 + 22.6], (5.4, 10, 0.8), 1.0)
        d, mat = _put(d, mat, door, WOOD)
        return d, mat
    objs.append(Obj(lampshop, (228, -1, -128), (280, 70, -76), "lampshop"))

    # the law sign at the street corner
    def lawsign(p):
        x0, z0 = 10.0, -48.0
        post = sdf.capsule(p, (x0, 0, z0), (x0, 24, z0), 0.9)
        bd = sdf.box(p - [x0, 32, z0], (28, 10, 0.9), 0.4)
        ink = (p[:, 2] > z0 + 0.7) & _tex(LAW_TEX, p, x0 - 26, x0 + 26, 41, 23)
        d, mat = post, np.full(len(p), METAL)
        rub = p[:, 0] > x0 + 2 + 3 * np.sin(p[:, 1])
        d, mat = _put(d, mat, bd, np.where(ink, np.where(rub & glitch, GHOST, SIGN_INK), SIGN))
        return d, mat
    objs.append(Obj(lawsign, (-14, -1, -52), (34, 40, -44), "lawsign"))

    if glitch:
        # sparks frozen in the air over the board and along the wires
        def sparks(p):
            d = np.full(len(p), 1e9)
            rng = np.random.default_rng(13)
            for _ in range(7):
                c = np.array([rng.uniform(-180, 60), rng.uniform(30, 80), rng.uniform(-70, -40)])
                a = c
                for k in range(4):
                    b = a + [rng.uniform(-6, 6), rng.uniform(-7, -3), rng.uniform(-2, 2)]
                    d = np.minimum(d, sdf.capsule(p, a, b, 0.6))
                    a = b
            return d, GHOST
        objs.append(Obj(sparks, (-200, 0, -80), (80, 90, -30), "sparks"))

    sky = gradient_sky(W, H, "#06081A", "#1E2448", glow=(330, 200, 260, "#2E3A6A"))
    stars(sky, 160, seed=31, ymax=120)
    moon(sky, 640, 30, 10)
    lights = [Light((-300, 240, 220), "#9AB0E8", 0.9, 1000)]
    if not glitch:
        lights += [Light((BOARD_X, 50, BOARD_Z + 16), "#FFD860", 1.0, 110, shadow=False),
                   Light((254.0, 40, -78), "#FFE6A0", 0.6, 80, shadow=False)]
    else:
        lights += [Light((BOARD_X, 50, BOARD_Z + 16), "#8AB0FF", 0.5, 70, shadow=False)]
    return dict(world=World(objs), materials=mats, width=W, height=H, centre=CENTRE,
                lights=lights, key=0.5, ambient=0.15, top=150.0, ss=2, steps=170, sky=sky,
                bloom=[(WINDOW, "#FFC861", 8, 0.45), (LAMP, "#FFE680", 8, 0.55), (GHOST, "#A8C8FF", 8, 0.5)])
