"""The Case 2 lab backdrops, drawn blank so the game can draw each case's own numbers live.

build(mode="track")  step 1, the braking test (480x270): bench, a strip of Braking Bend's asphalt and the
                     speed gate reading 10.0 m/s. The game animates the cart and its skid.
build(mode="plate")  step 2, the skid plate (480x270): the evidence photo pinned to the lab wall, with the
                     white brake line, a 0-25 m scale and D/R/M tags. The game draws the three skids to scale.
build(mode="cart")   the toy cart alone on a transparent canvas.

Plate geometry for the game: skids start at world x = PLATE_START, PX_PER_M units per metre, on the
photo's face at z = -55, rows at world y = ROWS[sid]. Camera centre (0, 100).
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light, gradient_sky
from src import sdf

(WALL, RULE, BENCH, ASPHALT, SKID, PAINT, SCREEN, METAL, RED, CART, WHEEL, TAG, TAG_INK, PIN, DUST, FRAME,
 CORK) = range(1, 18)
W, H = 480, 270
CENTRE = (0.0, 100.0)
PX_PER_M = 15.0       # skid plate scale: 15 world units per metre, 25 m across
PLATE_START = -183.0
ROWS = {"dash": 180.0, "rolla": 138.0, "mu": 94.0}


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _decal(text, font, w, h):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    b = d.textbbox((0, 0), text, font=font)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=font, fill=255)
    return np.array(im) > 100


def _tex(mask, p, x0, x1, ytop, ybot):
    hh, ww = mask.shape
    u = np.clip(((p[:, 0] - x0) / (x1 - x0) * (ww - 1)), 0, ww - 1).astype(int)
    v = np.clip(((ytop - p[:, 1]) / (ytop - ybot) * (hh - 1)), 0, hh - 1).astype(int)
    inside = (p[:, 0] >= x0) & (p[:, 0] <= x1) & (p[:, 1] <= ytop) & (p[:, 1] >= ybot)
    return mask[v, u] & inside


def _put(d, mat, dd, mm):
    mat = np.where(dd < d, mm, mat)
    return np.minimum(d, dd), mat


LCD_TEX = _decal("10.0", _font("consolab.ttf", 22), 56, 24)
MS_TEX = _decal("m/s", _font("arialbd.ttf", 14), 30, 16)
GATE_TEX = _decal("SPEED GATE", _font("arialbd.ttf", 13), 90, 16)
NUM_TEX = {k: _decal(str(k), _font("arialbd.ttf", 14), 18, 16) for k in range(0, 25, 2)}
LBL_TEX = {k: _decal(k, _font("arialbd.ttf", 15), 18, 18) for k in "DRM"}
TITLE_TEX = _decal("EVIDENCE 2-B   BRAKING BEND   SKIDS   (metres)", _font("arialbd.ttf", 13), 330, 16)


def materials():
    return {
        WALL: dict(ramp=["#3F3A2E", "#5A5342", "#776E58", "#958A70", "#B0A587", "#C9BE9F", "#DCD2B4"],
                   sub=(lambda p: np.abs(((p[:, 1] + 300) % 12.0) - 6.0) > 5.45, RULE), dither=0.3),
        RULE: dict(ramp=["#2B3E5E", "#3C5478", "#506B92", "#6683AB"]),
        CORK: dict(ramp=["#3A2614", "#5A3A1E", "#7A5028", "#9A6834", "#B8824A"],
                   pattern=lambda p, n: np.sin(p[:, 0] * 2.3) * np.sin(p[:, 1] * 2.9), pattern_gain=0.25),
        BENCH: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E", "#CF8A42", "#E2A45C"],
                    pattern=lambda p, n: 0.45 * np.sin(p[:, 0] * 0.35 + 2.0 * np.sin(p[:, 2] * 0.2)), pattern_gain=0.14),
        ASPHALT: dict(ramp=["#2A2430", "#3A3342", "#4A4254", "#5A5166", "#6B6178", "#7E7388"],
                      pattern=lambda p, n: 0.6 * np.sin(p[:, 0] * 1.9 + p[:, 1] * 0.7) * np.sin(p[:, 1] * 1.7 + p[:, 2]), pattern_gain=0.14),
        SKID: dict(ramp=["#050407", "#0B0910", "#120F17", "#1A1620"]),
        PAINT: dict(ramp=["#8E8A86", "#B8B4AE", "#DCD8D0", "#F4F0E6"]),
        SCREEN: dict(ramp=["#3DBB6A", "#9CF5B5"], emissive=True),
        METAL: dict(ramp=["#0A0C10", "#15191F", "#222831", "#323A46", "#47515F", "#626E7F"], gloss=24, spec="#C8D4E2"),
        RED: dict(ramp=["#3A0907", "#62110D", "#8E1A14", "#B8251C", "#DE3B2E", "#F26654"]),
        CART: dict(ramp=["#1B4885", "#2C66AE", "#4A8AD0", "#7DB2EA"], gloss=18, spec="#FFFFFF"),
        WHEEL: dict(ramp=["#0B0C10", "#17191F", "#262931", "#383C47"]),
        TAG: dict(ramp=["#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF"]),
        TAG_INK: dict(ramp=["#07090F", "#0E121D", "#161C2C", "#20283C"]),
        PIN: dict(ramp=["#5E100C", "#8E1A14", "#C9302A", "#EE5A4C", "#FF8A78"], gloss=30, spec="#FFFFFF"),
        DUST: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0"]),
        FRAME: dict(ramp=["#8E8A86", "#B8B4AE", "#DCD8D0", "#F4F0E6", "#FFFFFF"]),
    }


def _plate():
    objs = []
    objs.append(Obj(lambda p: (p[:, 2] + 60.0, WALL), (-300, -10, -62), (300, 330, -59), "wall"))
    objs.append(Obj(lambda p: (sdf.box(p - [0, 6, 0], (260, 8, 60), 0.8), BENCH), (-262, -3, -62), (262, 15, 62), "bench"))
    # the photo: white border, asphalt print, three skids from the brake line, metre scale
    x0, x1, y0, y1 = -205.0, 205.0, 60.0, 210.0

    def photo(p):
        frame = sdf.box(p - [0, (y0 + y1) / 2, -56], ((x1 - x0) / 2 + 8, (y1 - y0) / 2 + 14, 1.0), 0.3)
        mat = np.full(len(p), FRAME)
        on = (p[:, 0] > x0) & (p[:, 0] < x1) & (p[:, 1] > y0) & (p[:, 1] < y1) & (p[:, 2] > -55.5)
        mat = np.where(on, ASPHALT, mat)
        start = PLATE_START
        mat = np.where(on & (np.abs(p[:, 0] - (start - 4)) < 3.0), PAINT, mat)
        # metre scale along the bottom border
        scale_band = (p[:, 1] > y0 - 13) & (p[:, 1] < y0 - 1) & (p[:, 2] > -55.5)
        m = (p[:, 0] - start) / PX_PER_M
        tick = scale_band & (m > -0.05) & (m < 25.05) & (np.abs(((m + 100) % 1.0) - 0.5) > 0.44) & (p[:, 1] > y0 - 5 - 4 * (np.abs(((m + 100) % 2.0) - 1.0) > 0.94))
        mat = np.where(tick, TAG_INK, mat)
        for k, tex in NUM_TEX.items():
            cx = start + k * PX_PER_M
            mat = np.where(scale_band & _tex(tex, p, cx - 5, cx + 5, y0 - 4, y0 - 13), TAG_INK, mat)
        title = (p[:, 1] > y1 + 1) & (p[:, 2] > -55.5)
        mat = np.where(title & _tex(TITLE_TEX, p, -132, 132, y1 + 12, y1 + 2), TAG_INK, mat)
        return frame, mat
    objs.append(Obj(photo, (x0 - 10, y0 - 16, -58), (x1 + 10, y1 + 16, -54), "photo"))

    # paper tags with tread letters, pinned at the left end of each skid
    def tags(p):
        d = np.full(len(p), 1e9)
        mat = np.full(len(p), TAG)
        for k, yy in (("D", ROWS["dash"] - 3.5), ("R", ROWS["rolla"]), ("M", ROWS["mu"])):
            tag = sdf.box(p - [x0 - 18, yy, -53.5], (8, 8, 0.6), 0.3)
            d, mat = _put(d, mat, tag, np.where((p[:, 2] > -53.2) & _tex(LBL_TEX[k], p, x0 - 24, x0 - 12, yy + 6, yy - 6), TAG_INK, TAG))
            d, mat = _put(d, mat, sdf.sphere(p, (x0 - 18, yy + 7, -52.0), 1.8), PIN)
        return d, mat
    objs.append(Obj(tags, (x0 - 30, y0 + 20, -56), (x0 - 4, y0 + 130, -49), "tags"))
    lights = [Light((-200, 260, 160), "#FFD9A0", 1.2, 900), Light((240, 120, 140), "#9FB8FF", 0.35, 600, shadow=False)]
    return objs, lights


def _track():
    objs = []
    objs.append(Obj(lambda p: (p[:, 2] + 70.0, WALL), (-300, -10, -72), (300, 330, -69), "wall"))
    objs.append(Obj(lambda p: (sdf.box(p - [0, 26, 0], (260, 8, 60), 0.8), BENCH), (-262, 17, -62), (262, 35, 62), "bench"))

    def track(p):
        strip = sdf.box(p - [20, 34.6, -6], (220, 0.8, 20), 0.3)
        mat = np.full(len(p), ASPHALT)
        mat = np.where(np.abs(p[:, 0] + 120) < 2.5, PAINT, mat)
        return strip, mat
    objs.append(Obj(track, (-202, 33, -27), (242, 36, 15), "track"))

    def gate(p):
        d = np.full(len(p), 1e9)
        mat = np.full(len(p), METAL)
        for z in (-28.0, 16.0):
            d, mat = _put(d, mat, sdf.box(p - [-120, 58, z], (2.2, 24, 2.2), 0.5), METAL)
        beam = sdf.box(p - [-120, 84, -6], (3, 4, 25), 0.6)
        d, mat = _put(d, mat, beam, RED)
        box = sdf.box(p - [-120, 102, -20], (30, 16, 3), 1.0)
        d, mat = _put(d, mat, box, METAL)
        lcd = (np.abs(p[:, 0] + 124) < 22) & (np.abs(p[:, 1] - 104) < 9) & (p[:, 2] > -17.2)
        dig = lcd & _tex(LCD_TEX, p, -144, -106, 112, 96)
        unit = (p[:, 2] > -17.2) & _tex(MS_TEX, p, -106, -94, 103, 95)
        title = (p[:, 2] > -17.2) & _tex(GATE_TEX, p, -144, -96, 117.5, 113)
        mat = np.where(lcd, np.where(dig, SCREEN, WHEEL), mat)
        mat = np.where(unit | title, PAINT, mat)
        return d, mat
    objs.append(Obj(gate, (-152, 33, -32), (-88, 120, 20), "gate"))

    lights = [Light((-220, 260, 180), "#FFD9A0", 1.2, 900), Light((240, 140, 140), "#9FB8FF", 0.35, 600, shadow=False)]
    return objs, lights


def _cart():
    """The toy cart, centred on its own canvas, wheels resting on y = 35.4 (the test road's surface)."""
    def cart(p):
        body = sdf.box(p - [0, 44, -6], (12, 5, 9), 1.4)
        d, mat = body, np.full(len(p), CART)
        for x in (-9, 9):
            for z in (-15.5, 3.5):
                w = sdf.cylinder_y((p - [x, 39.4, z]) @ sdf.rot_x(np.pi / 2), 3.6, 1.2, 0.4)
                d, mat = _put(d, mat, w, WHEEL)
        flag = np.maximum(np.abs(p[:, 2] + 6) - 0.4, np.maximum(np.abs(p[:, 0] + 6) - 5, np.abs(p[:, 1] - 60) - 3.2))
        mast = sdf.capsule(p, (-11, 49, -6), (-11, 64, -6), 0.6)
        d, mat = _put(d, mat, mast, METAL)
        d, mat = _put(d, mat, flag, RED)
        return d, mat
    lights = [Light((-220, 260, 180), "#FFD9A0", 1.2, 900), Light((240, 140, 140), "#9FB8FF", 0.35, 600, shadow=False)]
    return [Obj(cart, (-16, 34, -22), (16, 66, 12), "cart")], lights


CART_W, CART_H = 48, 40
CART_CENTRE = (0.0, 47.0)


def build(mode="plate"):
    if mode == "cart":
        objs, lights = _cart()
        return dict(world=World(objs), materials=materials(), width=CART_W, height=CART_H, centre=CART_CENTRE,
                    lights=lights, key=0.5, ambient=0.16, top=80.0, ss=2, steps=120, sky=None)
    objs, lights = _plate() if mode == "plate" else _track()
    sky = gradient_sky(W, H, "#0A0F24", "#22305C")
    return dict(world=World(objs), materials=materials(), width=W, height=H, centre=CENTRE,
                lights=lights, key=0.5, ambient=0.16, top=260.0, ss=2, steps=150, sky=sky,
                bloom=[(SCREEN, "#9CF5B5", 6, 0.5)])
