"""Motion Mesa, Chapter 8, at dusk. 720x270, scrolls horizontally.

The whole district is graph paper: the desert floor is ruled, the mesas are
plotted, the road down Slope Hill is a velocity-time graph. The Rubber Baron
erased the equations of motion, so friction flickers: things slide and won't stop,
and every equation sign in town has been rubbed out.

Left to right: Mu's friction lab and Dash's courier post up on Slope Hill, the road
down to Braking Bend (the crime scene: three skids and the toppled Trophy Tower),
Rolla's bakery, the Derby gate.

build(glitch=True)   the law is erased: pebbles slide up the hill, afterimages, the billboard rubbed out
build(glitch=False)  after the case
Walkable ground: y = 0, z in [0, 30]. The skids at Braking Bend start at the brake line, x = -46.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light, gradient_sky, stars, hexrgb, BAYER4
from src import sdf

(SAND, GRID, MESA, FAR, ASPHALT, LINE_Y, PAINT, SKID, CURB, WOOD, POSTB, TRIM, SIGN, SIGN_INK, BAKERY, AWN_R,
 AWN_W, WINDOW, CACTUS, GOLD, CUBE_R, CUBE_Y, CUBE_B, STONE, METAL, ERASE, GHOST, FLAG_K, FLAG_W, RED, PINE,
 HAT_Y, DIAL, SUN, BAND, SCRUB, TANK) = range(1, 38)

W, H = 720, 270
CENTRE = (0.0, 90.0)
HOTSPOTS = {"mu": -290, "dash": -170, "bend": 20, "rolla": 190, "gate": 300}
SLOPE = 80.0 / 300.0          # Slope Hill rises 80 over 300: gradient 4/15


def hill_y(x):
    return np.clip((-60.0 - x) * SLOPE, 0, None)


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _decal(text, font, w, h):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    b = d.textbbox((0, 0), text, font=font)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=font, fill=255)
    return np.array(im) > 100


POST_TEX = _decal("POST", _font("arialbd.ttf", 19), 72, 24)
PIES_TEX = _decal("PIES", _font("arialbd.ttf", 19), 72, 24)
DERBY_TEX = _decal("GRAND DERBY", _font("arialbd.ttf", 17), 150, 24)
MU_TEX = _decal("\u03bc LAB", _font("arialbd.ttf", 19), 72, 24)
LIMIT_TEX = _decal("9", _font("arialbd.ttf", 34), 40, 40)
EQ_TEX = _decal("v\u00b2 = u\u00b2 + 2as", _font("georgiab.ttf", 22), 160, 36)


def _tex(mask, p, x0, x1, ytop, ybot):
    hh, ww = mask.shape
    u = np.clip(((p[:, 0] - x0) / (x1 - x0) * (ww - 1)), 0, ww - 1).astype(int)
    v = np.clip(((ytop - p[:, 1]) / (ytop - ybot) * (hh - 1)), 0, hh - 1).astype(int)
    return mask[v, u]


def _put(d, mat, dd, mm):
    mat = np.where(dd < d, mm, mat)
    return np.minimum(d, dd), mat


def _grid_lines(p, step=12.0, w=0.55):
    gx = np.abs(((p[:, 0] + 600) % step) - step / 2) > step / 2 - w
    gz = np.abs(((p[:, 2] + 600) % step) - step / 2) > step / 2 - w
    return gx | gz


def materials():
    return {
        SAND: dict(ramp=["#3A1F17", "#5C3222", "#80492E", "#A4623A", "#C47E4A", "#DE9C5E", "#EDB874"],
                   pattern=lambda p, n: 0.6 * np.sin(p[:, 0] * 0.31 + np.sin(p[:, 2] * 0.21) * 2.4), pattern_gain=0.08,
                   warm_tint=0.5, sub=(lambda p: _grid_lines(p) & (p[:, 1] < 0.6), GRID)),
        GRID: dict(ramp=["#2B2A44", "#3B3B5E", "#4C4F78", "#5E6590", "#7280A8"]),
        MESA: dict(ramp=["#2E1416", "#4A1F1E", "#6B2E26", "#8E4230", "#B0583A", "#CC7448", "#E0925E"],
                   pattern=lambda p, n: 0.9 * (np.abs(((p[:, 1] + 400) % 9.0) - 4.5) > 3.9) - 0.4, pattern_gain=0.16,
                   sub=(lambda p: np.abs(((p[:, 1] + 1.6 * np.sin(p[:, 0] * 0.11 + p[:, 2] * 0.07) + 400) % 14.0) - 7.0) > 5.6, BAND)),
        FAR: dict(ramp=["#3A2440", "#4E2F4E", "#66405C", "#7E5468", "#986C74", "#B08680"], dither=0.3,
                  sub=(lambda p: (np.abs(((p[:, 0] + 600) % 30.0) - 15.0) > 14.2) | (np.abs(((p[:, 1] + 600) % 30.0) - 15.0) > 14.2), GRID)),
        ASPHALT: dict(ramp=["#2A2430", "#3A3342", "#4A4254", "#5A5166", "#6B6178", "#7E7388"],
                      pattern=lambda p, n: 0.5 * np.sin(p[:, 0] * 1.7) * np.sin(p[:, 2] * 1.3), pattern_gain=0.1),
        LINE_Y: dict(ramp=["#7A5A12", "#B8891E", "#E6B43A", "#F8D66E"]),
        PAINT: dict(ramp=["#8E8A86", "#B8B4AE", "#DCD8D0", "#F4F0E6"]),
        SKID: dict(ramp=["#050407", "#0B0910", "#120F17", "#1A1620"]),
        CURB: dict(ramp=["#3A3238", "#544A50", "#70646A", "#8E8086", "#AC9EA2"]),
        WOOD: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E", "#CF8A42"],
                   pattern=lambda p, n: 0.45 * np.sin(p[:, 0] * 0.4 + 2.0 * np.sin(p[:, 1] * 0.2)), pattern_gain=0.14),
        PINE: dict(ramp=["#5A3A18", "#8C5E2C", "#BC8A4A", "#DDB173", "#F2D29C"]),
        POSTB: dict(ramp=["#16304E", "#204569", "#2D5D88", "#3F78A7", "#5795C4", "#76B2DC"]),
        TRIM: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848"], gloss=24, spec="#FFFBE6"),
        SIGN: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF"]),
        SIGN_INK: dict(ramp=["#07090F", "#0E121D", "#161C2C", "#20283C"]),
        BAKERY: dict(ramp=["#3A1622", "#5A2234", "#7E3448", "#A24A60", "#C2687C", "#DC8C9C"]),
        AWN_R: dict(ramp=["#5E100C", "#8E1A14", "#C9302A", "#EE5A4C"]),
        AWN_W: dict(ramp=["#8E8A86", "#B8B4AE", "#DCD8D0", "#F4F0E6"]),
        WINDOW: dict(ramp=["#F2B44C", "#FFD27A", "#FFE9B0"], emissive=True),
        CACTUS: dict(ramp=["#0E2A1C", "#16402A", "#215A3A", "#2E764C", "#409560", "#5AB276"]),
        GOLD: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848", "#FFE08A"], gloss=22, spec="#FFFFFF"),
        CUBE_R: dict(ramp=["#5E100C", "#8E1A14", "#C9302A", "#EE5A4C", "#FF8A78"]),
        CUBE_Y: dict(ramp=["#6B5A1C", "#B9A33B", "#EDDB72", "#F8EC98"]),
        CUBE_B: dict(ramp=["#1B4885", "#2C66AE", "#4A8AD0", "#7DB2EA"]),
        STONE: dict(ramp=["#2C2830", "#433D48", "#5C5462", "#766C7C", "#928898"]),
        METAL: dict(ramp=["#0A0C10", "#15191F", "#222831", "#323A46", "#47515F", "#626E7F"], gloss=24, spec="#C8D4E2"),
        ERASE: dict(ramp=["#8C5A6A", "#B07A8A", "#D29EAC", "#EBC0C8"]),
        GHOST: dict(ramp=["#4A3E7A", "#62549A", "#7E70B8", "#9C8ED0", "#BCB0E6"], emissive=True),
        FLAG_K: dict(ramp=["#07090F", "#0E121D", "#161C2C"]),
        FLAG_W: dict(ramp=["#B8B4AE", "#DCD8D0", "#F4F0E6"]),
        RED: dict(ramp=["#3A0907", "#62110D", "#8E1A14", "#B8251C", "#DE3B2E", "#F26654"]),
        HAT_Y: dict(ramp=["#5C3C06", "#A26A0A", "#E09B12", "#F8C23A", "#FFE38A"], gloss=20, spec="#FFFFFF"),
        DIAL: dict(ramp=["#B8B4AE", "#DCD8D0", "#F4F0E6", "#FFFFFF"]),
        SUN: dict(ramp=["#FF9A52", "#FFC070", "#FFE2A0"], emissive=True),
        BAND: dict(ramp=["#4A2A22", "#6E4232", "#94603F", "#B87E50", "#D69C66", "#ECBC84"]),
        SCRUB: dict(ramp=["#1A1A10", "#2C2C18", "#424224", "#5A5A30", "#76723E"]),
        TANK: dict(ramp=["#2A2430", "#3E3A4A", "#56546A", "#6E7088", "#8C90A8"], gloss=16, spec="#E8E0FF"),
    }


def build(glitch=True):
    objs = []

    # desert floor: ruled like graph paper
    objs.append(Obj(lambda p: (p[:, 1], SAND), (-400, -2, -330), (400, 0.2, 260), "ground"))

    # far mesas, plotted on the horizon
    def far(p):
        d = np.full(len(p), 1e9)
        for x, w, h, z in ((-330, 70, 46, -300), (-190, 50, 34, -290), (-40, 90, 58, -310), (140, 60, 40, -295),
                           (300, 90, 52, -305)):
            m = sdf.box(p - [x, h / 2, z], (w, h / 2, 18), 1.0)
            m = np.maximum(m, (np.abs(p[:, 0] - x) * 0.35 + p[:, 1]) - (h + w * 0.35 - 6))
            m = np.maximum(m, p[:, 1] - h + 3.0 * (np.sin(p[:, 0] * 0.13 + x) > 0.6))
            d = np.minimum(d, m)
        return d, FAR
    objs.append(Obj(far, (-430, -1, -330), (400, 62, -270), "far"))
    objs.append(Obj(lambda p: (sdf.sphere(p, (250, 40, -330), 34.0), SUN), (214, 4, -366), (286, 76, -294), "sun"))

    # two near mesas, terracotta strata
    def mesas(p):
        d = np.full(len(p), 1e9)
        for x, w, h, z in ((30, 80, 62, -200), (260, 64, 48, -210)):
            m = sdf.box(p - [x, h / 2, z], (w + 0.42 * h, h / 2, 26), 1.4)
            side = np.abs(p[:, 0] - x) - (w - 2) - 0.42 * (h - p[:, 1])
            side += 2.2 * np.sin(p[:, 1] * 0.45 + x) + 1.4 * np.sin(p[:, 1] * 1.3 + p[:, 2] * 0.2)
            side -= 2.5 * (np.abs(((p[:, 1] + 400) % 14.0) - 7.0) < 1.6)
            m = np.maximum(m, side * 0.8)
            talus = sdf.ellipsoid(p, (x, 0.0, z + 8), (w + 0.42 * h + 22, 14.0, 34.0))
            d = np.minimum(d, sdf.smin(m, talus, 6.0))
        return d, MESA
    objs.append(Obj(mesas, (-80, -1, -240), (340, 66, -170), "mesas"))

    # Slope Hill: a wedge rising to the left, the road running down its face
    def hill(p):
        top = p[:, 1] - hill_y(p[:, 0])
        body = np.maximum.reduce([top * 0.96, -p[:, 1], p[:, 0] + 60.0 - 0.0 * p[:, 1], -p[:, 0] - 420,
                                  -p[:, 2] - 140, p[:, 2] + 14])
        on_road = (p[:, 2] > -78) & (p[:, 2] < -22) & (top > -0.8)
        mat = np.where(on_road, ASPHALT, MESA)
        centre = on_road & (np.abs(p[:, 2] + 50) < 0.9) & (((p[:, 0] + 600) % 14) < 8)
        mat = np.where(centre, LINE_Y, mat)
        ticks = on_road & (np.abs(np.abs(p[:, 2] + 50) - 26.0) < 1.1) & (((p[:, 0] + 600) % 10) < 1.2)
        mat = np.where(ticks, PAINT, mat)
        return body, mat
    objs.append(Obj(hill, (-420, -1, -141), (-58, 96, -13), "hill"))

    # the flat road from the foot of the hill to the Derby gate
    def road(p):
        slab = sdf.box(p - [160, -0.3, -50], (220, 0.7, 28), 0.3)
        mat = np.full(len(p), ASPHALT)
        mat = np.where((np.abs(p[:, 2] + 50) < 0.9) & (((p[:, 0] + 600) % 14) < 8) & ((p[:, 0] < -52) | (p[:, 0] > 64)), LINE_Y, mat)
        ticks = (np.abs(np.abs(p[:, 2] + 50) - 26.0) < 1.1) & (((p[:, 0] + 600) % 10) < 1.2)
        finish = (p[:, 0] > 312) & (p[:, 0] < 324) & ((np.floor((p[:, 0] + 600) / 4) + np.floor((p[:, 2] + 600) / 4)) % 2 == 0)
        mat = np.where(finish, PAINT, mat)
        mat = np.where(ticks, PAINT, mat)
        brake = (p[:, 0] > -52) & (p[:, 0] < -46)
        mat = np.where(brake, PAINT, mat)
        # three skids, one per suspect, starting at the brake line
        dash = (p[:, 0] > -46) & (p[:, 0] < -4) & ((np.abs(p[:, 2] + 67.0) < 0.7) | (np.abs(p[:, 2] + 62.5) < 0.7))
        chev = np.abs(((p[:, 0] + np.abs(p[:, 2] + 44.0) * 1.2 + 600) % 5.0) - 2.5) < 1.3
        rolla = (p[:, 0] > -46) & (p[:, 0] < 8) & (np.abs(p[:, 2] + 44.0) < 3.6) & chev
        smear = 0.5 + 0.5 * np.sin(p[:, 0] * 0.9 + p[:, 2] * 2.1)
        mu = (p[:, 0] > -46) & (p[:, 0] < 58) & (np.abs(p[:, 2] + 30.0) < 5.0 - 2.0 * ((p[:, 0] + 46) / 104.0)) & (smear > 0.25)
        mat = np.where(dash | rolla | mu, SKID, mat)
        curb = sdf.box(p - [160, 0.6, -22.5], (220, 1.2, 1.4), 0.4)
        d, mat = _put(slab, mat, curb, CURB)
        return d, mat
    objs.append(Obj(road, (-62, -2, -80), (382, 2.5, -20), "road"))

    # Mu's friction lab on the hilltop: a shed, and a test ramp with a block on it
    def mulab(p):
        x0, y0 = -290.0, float(hill_y(np.array([-290.0]))[0])
        shed = sdf.box(p - [x0, y0 + 22, -112], (26, 22, 12), 1.0)
        roof = np.maximum(sdf.box(p - [x0, y0 + 48, -112], (31, 5, 16), 1.0), p[:, 1] - (y0 + 50) + 0.0 * p[:, 0])
        sign = sdf.box(p - [x0 - 4, y0 + 33, -99.4], (19, 6.5, 0.8), 0.4)
        door = sdf.box(p - [x0 + 18, y0 + 12, -99.6], (6, 12, 0.6), 0.5)
        d, mat = shed, np.full(len(p), PINE)
        for dd, mm in ((roof, HAT_Y), (sign, SIGN), (door, WOOD)):
            d, mat = _put(d, mat, dd, mm)
        mat = np.where((mat == SIGN) & (p[:, 2] > -99.0) & _tex(MU_TEX, p, x0 - 23, x0 + 15, y0 + 39, y0 + 27), SIGN_INK, mat)
        # the inclined-plane rig: a wooden ramp with a little block resting on it
        rq = p - [x0 + 46, y0 - 12, -112]
        ramp = np.maximum.reduce([rq[:, 1] - (14 - 0.5 * (rq[:, 0] + 14)), -rq[:, 1], np.abs(rq[:, 0]) - 14, np.abs(rq[:, 2]) - 5])
        bq = (rq - [-4, 18.5, 0]) @ sdf.rot_z(np.arctan(0.5))
        block = sdf.box(bq, (3.2, 2.4, 3.2), 0.4)
        d, mat = _put(d, mat, ramp * 0.8, WOOD)
        d, mat = _put(d, mat, block, PINE)
        return d, mat
    objs.append(Obj(mulab, (-325, 30, -130), (-225, 122, -94), "mulab"))

    # Dash's courier post: a blue box of a building with an arrow weathervane
    def post(p):
        x0, y0 = -170.0, float(hill_y(np.array([-150.0]))[0]) - 1
        body = sdf.box(p - [x0, y0 + 20, -112], (24, 20, 11), 1.0)
        roof = np.maximum(sdf.box(p - [x0, y0 + 42, -112], (29, 4, 15), 1.0), 0)
        sign = sdf.box(p - [x0, y0 + 30, -100.4], (18, 6.5, 0.8), 0.4)
        win = sdf.box(p - [x0 - 12, y0 + 14, -100.6], (6, 6, 0.6), 0.5)
        slot = sdf.box(p - [x0 + 12, y0 + 15, -100.6], (5, 1.2, 0.6), 0.3)
        mast = sdf.capsule(p, (x0, y0 + 46, -112), (x0, y0 + 62, -112), 0.7)
        shaft = sdf.capsule(p, (x0 - 9, y0 + 60, -112), (x0 + 7, y0 + 60, -112), 0.8)
        tipq = p - [x0 + 9, y0 + 60, -112]
        tip = np.maximum(np.abs(tipq[:, 2]) - 0.8, np.abs(tipq[:, 1]) * 1.4 + tipq[:, 0] - 4.0)
        tip = np.maximum(tip, -tipq[:, 0] - 3.0)
        d, mat = body, np.full(len(p), POSTB)
        for dd, mm in ((roof, RED), (sign, SIGN), (win, WINDOW), (slot, METAL), (mast, METAL), (shaft, RED), (tip, RED)):
            d, mat = _put(d, mat, dd, mm)
        mat = np.where((mat == SIGN) & (p[:, 2] > -100.0) & _tex(POST_TEX, p, x0 - 18, x0 + 18, y0 + 36, y0 + 24), SIGN_INK, mat)
        return d, mat
    objs.append(Obj(post, (-200, 18, -127), (-140, 92, -97), "post"))

    # Rolla's bakery: pink walls, striped awning, warm windows
    def bakery(p):
        x0 = 190.0
        body = sdf.box(p - [x0, 30, -100], (40, 30, 14), 1.2)
        roof = np.maximum(sdf.box(p - [x0, 66, -100], (46, 8, 18), 1.2), (np.abs(p[:, 0] - x0) * 0.45 + p[:, 1]) - 82)
        aw = p - [x0, 46, -82]
        awning = np.maximum.reduce([np.abs(aw[:, 0]) - 38, np.abs(aw[:, 1] + aw[:, 2] * 0.55) - 0.9, aw[:, 2] - 8, -aw[:, 2] - 2])
        stripe = np.abs(((p[:, 0] - x0 + 600) % 10.0) - 5.0) > 2.5
        win1 = sdf.box(p - [x0 - 20, 26, -85.6], (12, 12, 0.6), 0.5)
        win2 = sdf.box(p - [x0 + 18, 22, -85.6], (8, 22, 0.6), 0.5)
        sign = sdf.box(p - [x0, 58, -81.6], (19, 6.5, 0.8), 0.4)
        chim = sdf.box(p - [x0 + 26, 80, -102], (4, 10, 4), 0.6)
        d, mat = body, np.full(len(p), BAKERY)
        for dd, mm in ((roof, AWN_R), (win1, WINDOW), (win2, WINDOW), (sign, SIGN), (chim, STONE)):
            d, mat = _put(d, mat, dd, mm)
        d, mat = _put(d, mat, awning * 0.8, np.where(stripe, AWN_R, AWN_W))
        mat = np.where((mat == SIGN) & (p[:, 2] > -81.0) & _tex(PIES_TEX, p, x0 - 18, x0 + 18, 64, 52), SIGN_INK, mat)
        return d, mat
    objs.append(Obj(bakery, (140, -1, -120), (240, 92, -72), "bakery"))

    # the Derby gate over the road: two posts and a chequered banner
    def gate(p):
        x0 = 318.0
        d = np.full(len(p), 1e9)
        mat = np.full(len(p), STONE)
        for x in (x0 - 40, x0 + 40):
            d, mat = _put(d, mat, sdf.box(p - [x, 32, -92], (3, 32, 3), 0.6), STONE)
        ban = sdf.box(p - [x0, 60, -92], (40, 9, 1.2), 0.4)
        chk = ((np.floor((p[:, 0] + 600) / 4) + np.floor((p[:, 1] + 600) / 4)) % 2) == 0
        inner = (np.abs(p[:, 0] - x0) < 36) & (np.abs(p[:, 1] - 60) < 6)
        face = np.where(inner, SIGN, np.where(chk, FLAG_K, FLAG_W))
        face = np.where(inner & (p[:, 2] > -91.0) & _tex(DERBY_TEX, p, x0 - 36, x0 + 36, 66, 54), SIGN_INK, face)
        d, mat = _put(d, mat, ban, face)
        for k, x in enumerate(range(int(x0) - 36, int(x0) + 40, 9)):
            flag = np.maximum(np.abs(p[:, 2] + 91.5) - 0.4,
                              np.maximum(np.abs(p[:, 0] - x) * 1.2 + (49 - p[:, 1]) * 0.6 - 4.0, p[:, 1] - 49))
            d, mat = _put(d, mat, flag, (RED, CUBE_Y, CUBE_B)[k % 3])
        return d, mat
    objs.append(Obj(gate, (272, -1, -98), (364, 72, -86), "gate"))

    # Braking Bend: the speed-limit sign and the toppled Trophy Tower
    def bend(p):
        d = np.full(len(p), 1e9)
        mat = np.full(len(p), METAL)
        pole = sdf.capsule(p, (-80, 0, -16), (-80, 30, -16), 0.8)
        disc = sdf.cylinder_y((p - [-80, 36, -15]) @ sdf.rot_x(np.pi / 2), 7.5, 0.7, 0.3)
        d, mat = _put(d, mat, pole, METAL)
        rr = np.hypot(p[:, 0] + 80, p[:, 1] - 36)
        face = np.where(rr > 5.6, RED, PAINT)
        face = np.where((rr <= 5.6) & (p[:, 2] > -14.6) & _tex(LIMIT_TEX, p, -85, -75, 41, 31), SIGN_INK, face)
        d, mat = _put(d, mat, disc, face)
        # plinth, cracked, and the tower's unit cubes scattered across the verge and the road
        plinth = sdf.box(p - [80, 5, -14], (9, 5, 6), 0.6)
        crack = np.abs(p[:, 0] - 80 - 2.0 * np.sin(p[:, 1])) < 0.35
        d, mat = _put(d, mat, plinth, np.where(crack, SKID, STONE))
        rng = np.random.default_rng(7)
        cols = (CUBE_R, CUBE_Y, CUBE_B)
        for i, (x, z) in enumerate([(72, -9), (90, -6), (99, -12), (64, -26), (108, -30), (86, -34), (118, -8), (56, -14), (95, -44)]):
            a = rng.uniform(0, 1.2)
            cq = (p - [x, 3.6, z]) @ sdf.rot_y(a)
            d, mat = _put(d, mat, sdf.box(cq, (3.6, 3.6, 3.6), 0.5), cols[i % 3])
        stack = sdf.box(p - [80, 14.2, -14], (3.6, 3.6, 3.6), 0.5)
        d, mat = _put(d, mat, stack, CUBE_R)
        # the Golden Odometer trophy on its side
        tq = (p - [100, 4.2, -18]) @ sdf.rot_z(np.pi / 2 - 0.2)
        cup = sdf.round_cone(tq, (0, -4, 0), (0, 4, 0), 2.0, 4.6)
        cup = np.maximum(cup, -sdf.cylinder_y(tq - [0, 5.5, 0], 3.6, 2.0, 0.2))
        dial = sdf.cylinder_y((p - [100.5, 4.4, -13.8]) @ sdf.rot_x(np.pi / 2), 2.2, 0.4, 0.2)
        d, mat = _put(d, mat, cup, GOLD)
        d, mat = _put(d, mat, dial, DIAL)
        return d, mat
    objs.append(Obj(bend, (-90, -1, -50), (126, 46, -2), "bend"))

    # the equation billboard, rubbed out by the Eraser Gang
    def billboard(p):
        x0 = 60.0
        d = np.full(len(p), 1e9)
        mat = np.full(len(p), WOOD)
        for x in (x0 - 34, x0 + 34):
            d, mat = _put(d, mat, sdf.box(p - [x, 22, -128], (1.6, 22, 1.6), 0.4), WOOD)
        board = sdf.box(p - [x0, 46, -127], (42, 11, 1.2), 0.5)
        ink = (p[:, 2] > -126.0) & _tex(EQ_TEX, p, x0 - 40, x0 + 40, 55, 37)
        rub = (p[:, 0] > x0 - 6 + 4 * np.sin(p[:, 1] * 0.7)) & (p[:, 0] < x0 + 26 + 3 * np.sin(p[:, 1] * 0.9))
        face = np.where(ink, np.where(rub & glitch, ERASE, SIGN_INK), SIGN)
        if glitch:
            face = np.where((~ink) & rub & (((p[:, 0] * 3 + p[:, 1] * 5).astype(int) % 7) == 0), ERASE, face)
        d, mat = _put(d, mat, board, face)
        return d, mat
    objs.append(Obj(billboard, (14, -1, -132), (106, 58, -122), "billboard"))

    # tally-mark cacti
    def cacti(p):
        d = np.full(len(p), 1e9)
        for x0, z0 in ((-20, -90), (130, -70), (240, -12), (-130, -12)):
            for k in range(4):
                d = np.minimum(d, sdf.capsule(p, (x0 - 4.5 + 3 * k, 0, z0), (x0 - 4.5 + 3 * k, 13, z0), 1.0))
            d = np.minimum(d, sdf.capsule(p, (x0 - 7, 3, z0 + 1.5), (x0 + 6, 11, z0 + 1.5), 0.9))
        return d, CACTUS
    objs.append(Obj(cacti, (-140, -1, -95), (250, 15, -6), "cacti"))

    if glitch:
        # friction flickers: a tumbleweed and a crate sliding with no reason to stop, trailing afterimages
        def ghosts(p):
            d = np.full(len(p), 1e9)
            mat = np.full(len(p), GHOST)
            for x0, z0 in ((-210, -58), (-160, -40)):
                for k in range(4):
                    xk = x0 + 7.0 * k
                    st = sdf.sphere(p, (xk, float(hill_y(np.array([xk]))[0]) + 1.8, z0), 2.0 - 0.3 * k)
                    d, mat = _put(d, mat, st, STONE if k == 0 else GHOST)
            for k, a in enumerate((0, 1, 2, 3)):
                x = 150 - 9 * k
                ball = np.abs(sdf.sphere(p, (x, 5.2, -6), 5.0 - 0.6 * k)) - 0.5
                weave = np.abs(np.sin(p[:, 0] * 1.4) * np.sin(p[:, 1] * 1.6) * np.sin(p[:, 2] * 1.5)) < 0.35
                ball = np.where(weave, ball, ball + 0.6)
                d, mat = _put(d, mat, ball, WOOD if k == 0 else GHOST)
                crate = sdf.box(p - [-118 + 8 * k, 4, -6], (4, 4, 4), 0.4)
                d, mat = _put(d, mat, crate, PINE if k == 0 else GHOST)
            return d, mat
        objs.append(Obj(ghosts, (-215, -1, -62), (157, 50, 0), "ghosts"))

    # a natural arch between the mesas, and a balanced hoodoo by the foot of the hill
    def rocks(p):
        aq = (p - [150.0, 0.0, -238.0]) @ sdf.rot_x(np.pi / 2)
        arch = np.maximum(sdf.torus_y(aq, 26.0, 7.0 + 1.2 * np.sin(p[:, 0] * 0.5)), -p[:, 1])
        legs = np.minimum(sdf.ellipsoid(p, (124.0, 4.0, -238.0), (12.0, 12.0, 10.0)), sdf.ellipsoid(p, (176.0, 4.0, -238.0), (12.0, 12.0, 10.0)))
        stem = sdf.round_cone(p, (-48.0, 0.0, -150.0), (-48.0, 26.0, -150.0), 6.0, 2.4)
        cap = sdf.ellipsoid(p, (-48.0, 31.0, -150.0), (9.0, 5.0, 8.0))
        return np.minimum(np.minimum(arch, legs), np.minimum(stem, cap)), MESA
    objs.append(Obj(rocks, (-60, -1, -252), (210, 46, -140), "rocks"))

    # a water tower behind the billboard and telegraph poles strung along the back of the road
    POLES = (-40.0, 70.0, 180.0, 290.0)

    def town(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), WOOD)
        tx, tz = 112.0, -165.0
        for sx in (-1, 1):
            for sz in (-1, 1):
                leg = sdf.capsule(p, (tx + sx * 11, 0, tz + sz * 8), (tx + sx * 7, 44, tz + sz * 5), 1.0)
                d, mat = _put(d, mat, leg, WOOD)
        tank = sdf.cylinder_y(p - [tx, 54.0, tz], 13.0, 10.0, 1.0)
        hoops = np.abs(np.abs(p[:, 1] - 54.0) - 6.0) < 0.8
        d, mat = _put(d, mat, tank, np.where(hoops, METAL, TANK))
        roof = np.maximum(np.hypot(p[:, 0] - tx, p[:, 2] - tz) - (14.5 - 1.1 * (p[:, 1] - 64.0)), np.maximum(64.0 - p[:, 1], p[:, 1] - 77.0)) * 0.7
        d, mat = _put(d, mat, roof, RED)
        for x in POLES:
            d, mat = _put(d, mat, sdf.capsule(p, (x, 0, -86.0), (x, 40.0, -86.0), 0.9), WOOD)
            d, mat = _put(d, mat, sdf.capsule(p, (x - 6, 37.0, -86.0), (x + 6, 37.0, -86.0), 0.7), WOOD)
        for a, b in zip(POLES[:-1], POLES[1:]):
            for off in (-5.0, 5.0):
                t = np.clip((p[:, 0] - a - off) / (b - a), 0, 1)
                sag = 37.6 - 7.0 * 4 * t * (1 - t)
                wire = np.hypot(p[:, 1] - sag, p[:, 2] + 86.0) - 0.45
                wire = np.maximum(wire, np.maximum(a + off - p[:, 0], p[:, 0] - b - off))
                d, mat = _put(d, mat, wire, SIGN_INK)
        return d, mat
    objs.append(Obj(town, (-50, -1, -180), (300, 80, -80), "town"))

    # scrub and stones scattered in the foreground, clear of the walking strip
    def scrub(p):
        cell = np.round(p[:, 0] / 34.0)
        hsh = np.abs(np.sin(cell * 91.7) * 4373.1) % 1.0
        cx = cell * 34.0 + (hsh - 0.5) * 16.0
        cz = 44.0 + 12.0 * hsh
        q = p - np.stack([cx, np.zeros_like(cx), cz], 1)
        bush = np.sqrt((q[:, 0] / 6.0) ** 2 + (q[:, 1] / 4.0) ** 2 + (q[:, 2] / 5.0) ** 2) * 4.0 - 4.0
        bush += 0.9 * np.sin(q[:, 0] * 2.1) * np.sin(q[:, 1] * 2.7) * np.sin(q[:, 2] * 1.9)
        stone = sdf.ellipsoid(q, (9.0, 0.5, 3.0), (3.2, 2.0, 2.6))
        big = hsh > 0.45
        d = np.where(big, np.minimum(bush * 0.6, stone), stone)
        mat = np.where(big & (bush * 0.6 < stone), SCRUB, STONE)
        return d, mat
    objs.append(Obj(scrub, (-400, -1, 36), (400, 6, 62), "scrub"))

    sky = gradient_sky(W, H, "#1B1236", "#E07A4A", glow=(610, 190, 320, "#FFB070"))
    stars(sky, 90, seed=11, ymax=70)
    # long dusk clouds, lit from below by the setting sun
    yy, xx = np.mgrid[0:H, 0:W]
    for cx, cy, rx, ry in ((120, 52, 90, 6), (300, 38, 70, 5), (470, 66, 110, 7), (640, 44, 60, 4)):
        g = 1 - np.hypot((xx - cx) / rx, (yy - cy) / ry)
        g += 0.25 * np.sin(xx * 0.09 + cy)
        band = np.clip(np.floor(np.clip(g, 0, 1) * 3 + BAYER4[yy % 4, xx % 4] * 0.9) / 3, 0, 1)[..., None]
        lit = np.where((yy > cy)[..., None], hexrgb("#F2A27A"), hexrgb("#8A5A7E"))
        sky[:, :, :3] = np.clip(sky[:, :, :3] * (1 - 0.7 * band) + lit * 0.7 * band, 0, 255)
    lights = [Light((300, 200, 220), "#FFB070", 1.5, 1000),
              Light((190, 30, -80), "#FFD27A", 0.6, 120, ignore=("bakery",)),
              Light((-300, 160, 120), "#8E7AD8", 0.45, 800, shadow=False)]
    return dict(world=World(objs), materials=materials(), width=W, height=H, centre=CENTRE,
                lights=lights, key=0.45, ambient=0.13, top=150.0, ss=2, steps=170, sky=sky,
                bloom=[(WINDOW, "#FFC861", 10, 0.5), (GHOST, "#9C8ED0", 6, 0.35), (SUN, "#FFB070", 22, 0.6)])
