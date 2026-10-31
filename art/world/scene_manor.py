"""Hollowmere Manor, the free-fall chapter, at midnight. 720x270, scrolls horizontally.

A gothic manor in a storm. Left to right: the dead yew; the main house with the armoury door (Sir Rivet) and the
gallery doors (Lady Varnish); the gramophone on its table; the crime scene: a white sheet over Old Tock inside a
chalk outline, out from the foot of the clock tower; the tower with its three balconies, each flying its owner's
banner (armoury low, gallery middle, clock room high, under the clock face); the washing line with the bedsheet the
household takes for the Tower Ghost; a few gravestones (Pendle waits by the tower stair).

build(glitch=True)   the law of falling is erased: raindrops hang in the air, the sheet on the line glows like a ghost
build(glitch=False)  after the case: the house lit up, the sheet just a sheet, the law sign whole
Walkable courtyard: y = 0, z in [0, 30]. Balcony floors at y = 36, 80, 144 (4.9 : 11.0 : 19.6 m, to scale).
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light, gradient_sky, moon, stars, BAYER4, hexrgb
from src import sdf

(COBBLE, COBBLE_D, STONE, STONE_D, SLATE, WINDOW, DARKWIN, CANDLE, WOOD, IRON, CHALK, SHEET, GHOST, BRASS, GILT,
 ARMOUR, BANNER_R, SIGN, SIGN_INK, YEW, GRAVE, VINYL, PUDDLE, OILG) = range(1, 25)

W, H = 720, 270
CENTRE = (0.0, 90.0)
HOTSPOTS = {"rivet": -250, "varnish": -110, "stage": 120, "pendle": 270}
TOWER_X, TOWER_Z, TOWER_HW = 150.0, -112.0, 24.0
FRONT = TOWER_Z + TOWER_HW                     # the tower's front face
BALCONIES = ((36.0, BANNER_R), (80.0, OILG), (144.0, BRASS))
BODY_X, BODY_Z = 150.0, FRONT + 45.0             # where he landed: 4.5 m out from the wall
GRAM_X, GRAM_Z = 40.0, -52.0


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _decal(text, font, w, h):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    b = d.textbbox((0, 0), text, font=font)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=font, fill=255)
    return np.array(im) > 100


LAW_TEX = _decal("h = ½gt²", _font("arialbd.ttf", 30), 120, 38)


def _tex(mask, p, x0, x1, ytop, ybot):
    hh, ww = mask.shape
    u = np.clip(((p[:, 0] - x0) / (x1 - x0) * (ww - 1)), 0, ww - 1).astype(int)
    v = np.clip(((ytop - p[:, 1]) / (ytop - ybot) * (hh - 1)), 0, hh - 1).astype(int)
    return mask[v, u]


def _put(d, mat, dd, mm):
    mat = np.where(dd < d, mm, mat)
    return np.minimum(d, dd), mat


def _arch(p, cx, cy, z, w, h, depth=0.7):
    """A gothic window or door: a box with a pointed top, centred at (cx, cy), half-width w, half-height h."""
    body = sdf.box(p - [cx, cy, z], (w, h, depth))
    top = sdf.box((p - [cx, cy + h, z]) @ sdf.rot_z(np.pi / 4), (w * 0.707, w * 0.707, depth))
    return np.minimum(body, top)


def _blocks(p, size=18.0, course=9.0):
    """Mortar lines of coursed stone on any vertical face. Big blocks: at 1 px a unit, small ones read as scanlines."""
    y = p[:, 1] + 300
    row = np.floor(y / course)
    u = p[:, 0] + p[:, 2] + (row % 2) * size / 2 + 600
    return (np.abs((y % course) - course / 2) > course / 2 - 0.45) | (np.abs((u % size) - size / 2) > size / 2 - 0.45)


def _block_tone(p, n, size=18.0, course=9.0):
    """A tone shift per stone (-0.5..0.5), so the wall reads as stones rather than stripes."""
    row = np.floor((p[:, 1] + 300) / course)
    col = np.floor((p[:, 0] + p[:, 2] + (row % 2) * size / 2 + 600) / size)
    return (np.sin(row * 12.9898 + col * 78.233) * 43758.5453) % 1.0 - 0.5


def _lantern(p, d, mat, x, y, z):
    """A wall lantern: candle glass in an iron cap and base, on a bracket back to the wall."""
    d, mat = _put(d, mat, sdf.box(p - [x, y, z], (1.6, 2.4, 1.6), 0.3), CANDLE)
    d, mat = _put(d, mat, sdf.box(p - [x, y + 3.0, z], (2.2, 0.6, 2.2), 0.2), IRON)
    d, mat = _put(d, mat, sdf.box(p - [x, y - 2.8, z], (1.9, 0.5, 1.9), 0.2), IRON)
    d, mat = _put(d, mat, sdf.box(p - [x, y + 4.0, z - 2.0], (0.4, 0.4, 2.4)), IRON)
    return d, mat


def _sky(glitch):
    """Storm sky: moon behind a band of cloud, stars above, a far hill and a ragged treeline at the horizon."""
    sky = gradient_sky(W, H, "#04050C", "#1C2140", glow=(590, 34, 190, "#343C66"))
    stars(sky, 80, seed=3, ymax=120)
    moon(sky, 590, 34, 11, hex_lit="#E4E8F6", hex_dark="#A2A8C2", halo="#46507E")
    yy, xx = np.mgrid[0:H, 0:W].astype(float)
    dith = BAYER4[yy.astype(int) % 4, xx.astype(int) % 4]
    # clouds: sums of sines, kept to a band, lit from behind where they cross the moon
    n = (np.sin(xx * 0.019 + np.sin(yy * 0.05) * 2.0) + 0.6 * np.sin(xx * 0.047 + yy * 0.09 + 1.3)
         + 0.8 * np.sin(xx * 0.011 - yy * 0.031) + 0.4 * np.sin(xx * 0.09 - yy * 0.21))
    band = np.exp(-((yy - 62) / 30) ** 2) + 0.5 * np.exp(-((yy - 118) / 16) ** 2)
    c = np.clip((n * 0.32 + 0.45) * band * 1.5 - 0.3, 0, 0.9)
    c4 = np.floor(c * 4 + dith * 0.9) / 4
    moonlit = np.clip(1 - np.hypot(xx - 590, (yy - 34) * 1.4) / 150, 0, 1)
    cloud = hexrgb("#1E2446") * (1 - moonlit[..., None]) + hexrgb("#5C68A2") * moonlit[..., None]
    edge = np.clip(c4 - np.floor((c + 0.12) * 4 + dith * 0.9) / 4 + 0.25, 0, 1) * moonlit
    col = sky[..., :3] * (1 - c4[..., None]) + cloud * c4[..., None] + hexrgb("#7A86B8") * 0.4 * edge[..., None]
    sky[..., :3] = np.clip(col, 0, 255).astype(np.uint8)
    # far hill, then the near treeline: flat silhouettes for depth behind the wall and the tower
    # (the courtyard wall's top is at about y 128 on screen, so they have to rise above it to be seen)
    hill = 104 + 9 * np.sin(xx[0] * 0.012 + 0.6) + 5 * np.sin(xx[0] * 0.041)
    trees = 124 - 3 * np.sin(xx[0] * 0.05) - 9 * np.abs(np.sin(xx[0] * 0.21)) * (np.sin(xx[0] * 0.013) > -0.3)
    for x in range(W):
        sky[int(hill[x]):, x, :3] = hexrgb("#11152C")
        sky[int(trees[x]):, x, :3] = hexrgb("#0A0C1A")
    return sky


def _mist(img, dep, mat):
    """Low ground mist: a dithered cool veil that thickens toward the bottom of the frame."""
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    a = np.clip((yy - h * 0.62) / (h * 0.3), 0, 1) * 0.2 * (0.75 + 0.25 * np.sin(xx * 0.027 + yy * 0.08))
    a = np.floor(a * 10 + BAYER4[yy % 4, xx % 4]) / 10
    img[..., :3] = np.clip(img[..., :3] * (1 - a[..., None]) + hexrgb("#4A5684") * a[..., None], 0, 255).astype(np.uint8)
    return img


def materials(glitch):
    lit = DARKWIN if glitch else WINDOW
    return lit, {
        COBBLE: dict(ramp=["#16161E", "#1E1E28", "#282834", "#323242", "#3E3E50"],
                     pattern=lambda p, n: np.sin(p[:, 0] * 0.9) * np.sin(p[:, 2] * 1.1), pattern_gain=0.08,
                     sub=(lambda p: (np.abs(((p[:, 0] + 0.5 * np.floor((p[:, 2] + 300) / 3.2) * 3 + 600) % 3.6) - 1.8) > 1.5)
                          | (np.abs(((p[:, 2] + 600) % 3.2) - 1.6) > 1.35), COBBLE_D)),
        COBBLE_D: dict(ramp=["#08080C", "#0E0E14", "#14141C"]),
        PUDDLE: dict(ramp=["#141C34", "#1E2A4A", "#2C3C64", "#44587E"], gloss=60, spec="#C8D8FF"),
        STONE: dict(ramp=["#1A1B26", "#262836", "#343646", "#444758", "#56596E", "#6C7088"],
                    pattern=_block_tone, pattern_gain=0.22, dither=0.12, sub=(lambda p: _blocks(p), STONE_D)),
        STONE_D: dict(ramp=["#101119", "#161822", "#1E202C"], dither=0.1),
        SLATE: dict(ramp=["#0C0E16", "#141824", "#1C2232", "#262E42"], gloss=30, spec="#8090B0"),
        WINDOW: dict(ramp=["#E89A3C", "#F8C060", "#FFE2A0"], emissive=True),
        DARKWIN: dict(ramp=["#080A14", "#0E1224", "#161C36", "#222A4A"], gloss=40, spec="#7080B0"),
        CANDLE: dict(ramp=["#B86A20", "#E09A3A", "#F8C870"], emissive=True),
        WOOD: dict(ramp=["#140A04", "#22120A", "#341C10", "#4A2A18", "#623A22"]),
        IRON: dict(ramp=["#05060A", "#0C0E14", "#16191F", "#22262E"], gloss=20, spec="#9098A8"),
        CHALK: dict(ramp=["#B8BCC8", "#D8DCE6", "#F2F4FA"]),
        SHEET: dict(ramp=["#5A6070", "#8890A0", "#B4BAC8", "#D8DCE6", "#F2F4FA"]),
        GHOST: dict(ramp=["#6A9AFF", "#A8C8FF", "#E8F2FF"], emissive=True),
        BRASS: dict(ramp=["#4A2E08", "#7A5012", "#AC7A22", "#D8A63E", "#F6D070"], gloss=24, spec="#FFF4C8"),
        GILT: dict(ramp=["#5A3A0A", "#8A6014", "#BC8C26", "#E2B84A", "#FADC82"], gloss=24, spec="#FFF6D0"),
        ARMOUR: dict(ramp=["#2A3038", "#46505C", "#6A7684", "#98A4B2", "#C8D2DC"], gloss=30, spec="#FFFFFF"),
        BANNER_R: dict(ramp=["#3A0907", "#62110D", "#8E1A14", "#B8251C", "#DE3B2E"]),
        SIGN: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8"]),
        SIGN_INK: dict(ramp=["#07090F", "#0E121D", "#161C2C"]),
        YEW: dict(ramp=["#06080A", "#0C1012", "#12181A", "#1A2224"]),
        GRAVE: dict(ramp=["#1C1E24", "#282A32", "#363842", "#464854"]),
        OILG: dict(ramp=["#0A1A14", "#143024", "#1E4634", "#2A5E46", "#3A7A5C"]),
        VINYL: dict(ramp=["#050507", "#0C0C10", "#16161C"], gloss=50, spec="#C0C0D0"),
    }


def build(glitch=True):
    lit, mats = materials(glitch)
    objs = []

    def ground(p):
        x, z = p[:, 0], p[:, 2]
        # a rough figure in chalk round the sheet: body, head, an arm flung out
        bx, bz = x - BODY_X, z - BODY_Z
        body = np.abs(np.hypot(bx / 22.0, bz / 11.0) - 1.0) < 0.14
        head = np.abs(np.hypot(bx + 27.0, bz + 1.0) - 5.4) < 1.2
        arm = (np.abs(bz - 9.0 - 0.3 * (bx - 8.0)) < 1.2) & (bx > 8.0) & (bx < 30.0)
        chalk = body | head | arm
        puddle = (np.hypot((x + 40) / 22, (z + 14) / 6) < 1) | (np.hypot((x - 250) / 18, (z - 8) / 5) < 1)
        return p[:, 1], np.where(chalk, CHALK, np.where(puddle, PUDDLE, COBBLE))
    objs.append(Obj(ground, (-400, -2, -340), (400, 0.2, 260), "ground"))

    # the main house: coursed stone, a steep slate roof, pointed windows; armoury door left, gallery doors right
    def house(p):
        x0, z0 = -160.0, -150.0
        d = sdf.box(p - [x0, 52, z0], (190, 52, 34), 0.6)
        mat = np.full(len(p), STONE)
        roof = np.maximum(np.abs(p[:, 2] - z0) * 1.25 + (p[:, 1] - 150), np.maximum(104 - p[:, 1], np.abs(p[:, 0] - x0) - 192))
        d, mat = _put(d, mat, roof * 0.7, SLATE)
        for gx in (-300.0, -160.0, -30.0):
            gable = np.maximum(np.abs(p[:, 0] - gx) * 1.1 + (p[:, 1] - 150), np.maximum(100 - p[:, 1], np.abs(p[:, 2] - z0 - 30) - 6))
            d, mat = _put(d, mat, gable * 0.7, STONE)
            d, mat = _put(d, mat, _arch(p, gx, 116, z0 + 36.4, 4.0, 6.0), lit)
            for cx in (gx - 2.0, gx + 2.0):
                d, mat = _put(d, mat, sdf.box(p - [cx, 156, z0 + 4], (1.6, 10, 1.6)), STONE)
        for wx in (-330.0, -290.0, -205.0, -175.0, -60.0, -20.0):
            # a few rooms still lit by candle on the stormy night; all of them once the law is back
            pane = CANDLE if glitch and wx in (-290.0, -175.0, -20.0) else lit
            mull = (np.abs(p[:, 0] - wx) < 0.45) | (np.abs(p[:, 1] - 64) < 0.45)
            d, mat = _put(d, mat, _arch(p, wx, 66, z0 + 34.4, 5.0, 9.0), np.where(mull, IRON, pane))
            d, mat = _put(d, mat, sdf.box(p - [wx, 56, z0 + 35.6], (6.4, 0.9, 1.6)), STONE)
        # the armoury: a studded door in a dressed-stone surround, crossed swords behind a shield, a lantern
        d, mat = _put(d, mat, _arch(p, -250, 17, z0 + 34.3, 11.5, 17.5), STONE)
        studs = (np.abs(((p[:, 0] + 600) % 4.0) - 2.0) < 0.7) & (np.abs(((p[:, 1] + 600) % 6.0) - 3.0) < 0.7)
        d, mat = _put(d, mat, _arch(p, -250, 16, z0 + 34.8, 9.0, 16.0), np.where(studs, IRON, WOOD))
        for s in (-1, 1):
            d, mat = _put(d, mat, sdf.capsule(p, (-250 - 10 * s, 34, z0 + 34.9), (-250 + 10 * s, 58, z0 + 34.9), 0.7), ARMOUR)
        shield = np.maximum(sdf.ellipsoid(p, (-250, 46, z0 + 35.6), (6.0, 7.5, 1.4)), 40.0 - p[:, 1] - 0.6 * np.abs(p[:, 0] + 250))
        d, mat = _put(d, mat, shield, np.where(np.abs(p[:, 0] + 250) < 1.0, ARMOUR, BANNER_R))
        d, mat = _lantern(p, d, mat, -234, 28, z0 + 38.0)
        # the gallery: glazed double doors with leaded panes, in a slim gilt surround, lanterns either side
        d, mat = _put(d, mat, _arch(p, -110, 20, z0 + 34.6, 12.0, 20.0, 0.9), GILT)
        lead = (np.abs(((p[:, 0] + 600) % 3.0) - 1.5) < 0.4) | (np.abs(((p[:, 1] + 600) % 5.0) - 2.5) < 0.4)
        for sx in (-5.8, 5.8):
            d, mat = _put(d, mat, _arch(p, -110 + sx, 19, z0 + 35.4, 4.8, 17.0), np.where(lead, IRON, CANDLE if glitch else WINDOW))
        for lx in (-127.0, -93.0):
            d, mat = _lantern(p, d, mat, lx, 32, z0 + 38.0)
        return d, mat
    objs.append(Obj(house, (-355, -1, -178), (36, 168, -108), "house"))

    # the clock tower: three balconies, each flying its owner's banner, and the clock under a slate spire
    def tower(p):
        x0, z0, hw = TOWER_X, TOWER_Z, TOWER_HW
        d = sdf.box(p - [x0, 97, z0], (hw, 97, hw), 0.6)
        mat = np.full(len(p), STONE)
        spire = np.maximum(np.maximum(np.abs(p[:, 0] - x0), np.abs(p[:, 2] - z0)) * 2.2 + (p[:, 1] - 248), 194 - p[:, 1])
        d, mat = _put(d, mat, spire * 0.4, SLATE)
        face = sdf.cylinder_y((p - [x0, 178, FRONT + 0.6]) @ sdf.rot_x(np.pi / 2), 10.0, 0.8, 0.4)
        a = np.arctan2(p[:, 1] - 178, p[:, 0] - x0)
        r = np.hypot(p[:, 0] - x0, p[:, 1] - 178)
        marks = (np.abs(((a * 12 / (2 * np.pi)) + 100) % 1.0 - 0.5) > 0.4) & (r > 7.4)
        # both hands straight up: midnight
        hands = (np.abs(p[:, 0] - x0) < 0.7) & (p[:, 1] > 178) & (p[:, 1] < 187.5)
        d, mat = _put(d, mat, face, np.where(marks | hands, SIGN_INK, SIGN))
        d, mat = _put(d, mat, sdf.torus_y((p - [x0, 178, FRONT + 0.8]) @ sdf.rot_x(np.pi / 2), 10.4, 0.9), BRASS)
        for hb, colour in BALCONIES:
            d, mat = _put(d, mat, _arch(p, x0, hb + 9, FRONT + 0.2, 5.0, 8.0), CANDLE)
            slab = sdf.box(p - [x0, hb, FRONT + 6], (13, 1.4, 6), 0.4)
            d, mat = _put(d, mat, slab, STONE)
            rail = sdf.box(p - [x0, hb + 8, FRONT + 11.4], (13, 0.6, 0.6))
            for k in range(-6, 7, 2):
                rail = np.minimum(rail, sdf.box(p - [x0 + 2.0 * k, hb + 4.4, FRONT + 11.4], (0.35, 3.6, 0.35)))
            for sx in (-1, 1):
                rail = np.minimum(rail, sdf.box(p - [x0 + sx * 13, hb + 4.4, FRONT + 6], (0.35, 3.6, 5.6)))
            d, mat = _put(d, mat, rail, IRON)
            banner = sdf.box(p - [x0, hb - 8.5, FRONT + 11.8], (5.0, 7.0, 0.4), 0.2)
            notch = (p[:, 1] < hb - 12.5) & (np.abs(p[:, 0] - x0) < 2.4 - (hb - 15.5 - p[:, 1]) * 0.8)
            d, mat = _put(d, mat, np.where(notch, 1e9, banner), colour)
        door = _arch(p, x0 + 15, 13, FRONT + 0.4, 5.0, 13.0)
        d, mat = _put(d, mat, door, WOOD)
        return d, mat
    objs.append(Obj(tower, (120, -1, -140), (180, 238, -74), "tower"))

    # the crime scene: a white sheet over Old Tock, inside the chalk
    def scene(p):
        lump = sdf.smin(sdf.ellipsoid(p, (BODY_X + 2, 0.0, BODY_Z), (15.0, 5.6, 6.4)),
                        sdf.ellipsoid(p, (BODY_X - 15, 0.0, BODY_Z - 0.6), (4.8, 5.0, 4.8)), 2.0)
        drape = sdf.ellipsoid(p, (BODY_X, 0.0, BODY_Z), (20.0, 1.4, 9.4))
        return sdf.smin(lump, drape, 1.6), SHEET
    objs.append(Obj(scene, (BODY_X - 26, -1, BODY_Z - 12), (BODY_X + 26, 8, BODY_Z + 12), "scene"))

    # the ghost-hunter's gramophone on a little table
    def gramophone(p):
        x0, z0 = GRAM_X, GRAM_Z
        d, mat = sdf.box(p - [x0, 12, z0], (8, 0.8, 6), 0.3), np.full(len(p), WOOD)
        for sx in (-6.5, 6.5):
            for sz in (-4.5, 4.5):
                d, mat = _put(d, mat, sdf.capsule(p, (x0 + sx, 0, z0 + sz), (x0 + sx, 12, z0 + sz), 0.6), WOOD)
        d, mat = _put(d, mat, sdf.box(p - [x0, 15, z0], (5.4, 2.4, 4.4), 0.4), WOOD)
        d, mat = _put(d, mat, sdf.cylinder_y(p - [x0, 17.8, z0], 4.6, 0.3, 0.1), VINYL)
        arm = sdf.capsule(p, (x0 + 3.6, 18.4, z0 - 3.0), (x0 + 3.8, 26.0, z0 - 2.4), 0.5)
        d, mat = _put(d, mat, arm, BRASS)
        horn = sdf.round_cone(p, (x0 + 3.8, 26.0, z0 - 2.4), (x0 - 4.0, 34.0, z0 + 3.0), 0.6, 7.0)
        mouth = sdf.sphere(p, (x0 - 4.6, 34.6, z0 + 3.6), 5.6)
        d, mat = _put(d, mat, np.maximum(horn, -mouth), BRASS)
        return d, mat
    objs.append(Obj(gramophone, (GRAM_X - 14, -1, GRAM_Z - 10), (GRAM_X + 10, 44, GRAM_Z + 12), "gramophone"))

    # the washing line, and the bedsheet the household takes for the Tower Ghost
    def line(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), WOOD)
        for px in (222.0, 322.0):
            d, mat = _put(d, mat, sdf.box(p - [px, 22, -70], (1.2, 22, 1.2)), WOOD)
        t = np.clip((p[:, 0] - 222) / 100, 0, 1)
        rope = np.maximum(np.hypot(p[:, 1] - (42 - 6 * 4 * t * (1 - t)), p[:, 2] + 70) - 0.4, np.maximum(222 - p[:, 0], p[:, 0] - 322))
        d, mat = _put(d, mat, rope, IRON)
        sx = p[:, 0] - 272
        hang = 42 - 6 * 4 * ((sx + 50) / 100) * (1 - (sx + 50) / 100) - 1
        billow = 2.4 * np.sin(sx * 0.35) * np.clip((hang - p[:, 1]) / 20, 0, 1)
        sheet = sdf.box(np.stack([sx, p[:, 1] - (hang - 13), p[:, 2] + 70 - billow], 1), (15, 13, 0.5), 0.3) * 0.8
        if glitch:
            eyes = (np.hypot(sx + 4, p[:, 1] - (hang - 9)) < 1.8) | (np.hypot(sx - 4, p[:, 1] - (hang - 9)) < 1.8)
            d, mat = _put(d, mat, sheet, np.where(eyes, IRON, GHOST))
        else:
            d, mat = _put(d, mat, sheet, SHEET)
            for k in (-10.0, 0.0, 10.0):
                tk = (k + 50) / 100
                d, mat = _put(d, mat, sdf.box(p - [272 + k, 41.2 - 24 * tk * (1 - tk), -70], (0.6, 1.6, 0.8)), WOOD)
        return d, mat
    objs.append(Obj(line, (218, -1, -80), (326, 46, -60), "line"))

    def wall(p):
        d = sdf.box(p - [205, 14, -160], (175, 14, 4), 0.4)
        mat = np.full(len(p), STONE)
        bars = (np.abs(((p[:, 0] + 600) % 6.0) - 3.0) < 0.5) & (p[:, 1] < 46)
        rail = np.maximum(sdf.box(p - [205, 37, -160], (175, 9, 0.6)), np.where(bars, -1.0, 1.0))
        rail = np.minimum(rail, sdf.box(p - [205, 44, -160], (175, 0.7, 0.7)))
        d, mat = _put(d, mat, rail, IRON)
        return d, mat
    objs.append(Obj(wall, (28, -1, -166), (382, 48, -154), "wall"))

    # the dead yew on the left, gravestones on the right
    def yard(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), YEW)
        rng = np.random.default_rng(4)
        trunk = sdf.round_cone(p, (-342, 0, -96), (-338, 70, -96), 6.0, 2.4)
        d = np.minimum(d, trunk)
        for _ in range(9):
            a = np.array([-338 + rng.uniform(-3, 3), rng.uniform(34, 66), -96.0])
            for k in range(3):
                b = a + [rng.uniform(-14, 14), rng.uniform(4, 12), rng.uniform(-3, 3)]
                d = np.minimum(d, sdf.capsule(p, a, b, 1.6 - 0.4 * k))
                a = b
        for gx, gz, tilt in ((300.0, -100.0, 0.12), (334.0, -92.0, -0.1), (356.0, -110.0, 0.05)):
            q = (p - [gx, 0, gz]) @ sdf.rot_z(tilt)
            stone = np.minimum(sdf.box(q - [0, 7, 0], (5.0, 7.0, 1.6), 0.6), sdf.cylinder_y((q - [0, 14, 0]) @ sdf.rot_x(np.pi / 2), 5.0, 1.6, 0.5))
            d, mat = _put(d, mat, stone, GRAVE)
        return d, mat
    objs.append(Obj(yard, (-372, -1, -124), (366, 92, -80), "yard"))

    # the law sign by the gramophone
    def lawsign(p):
        x0, z0 = -10.0, -46.0
        post = sdf.capsule(p, (x0, 0, z0), (x0, 24, z0), 0.9)
        bd = sdf.box(p - [x0, 32, z0], (30, 10, 0.9), 0.4)
        ink = (p[:, 2] > z0 + 0.7) & _tex(LAW_TEX, p, x0 - 28, x0 + 28, 41, 23)
        d, mat = post, np.full(len(p), IRON)
        rub = p[:, 0] > x0 - 4 + 3 * np.sin(p[:, 1])
        d, mat = _put(d, mat, bd, np.where(ink, np.where(rub & glitch, GHOST, SIGN_INK), SIGN))
        return d, mat
    objs.append(Obj(lawsign, (-42, -1, -50), (22, 44, -42), "lawsign"))

    if glitch:
        # raindrops that have stopped falling, hanging in the air
        def rain(p):
            d = np.full(len(p), 1e9)
            rng = np.random.default_rng(23)
            for _ in range(60):
                c = np.array([rng.uniform(-360, 360), rng.uniform(16, 200), rng.uniform(-90, 10)])
                d = np.minimum(d, sdf.capsule(p, c, c + [0.8, 5.0, 0], 0.55))
            return d, GHOST
        objs.append(Obj(rain, (-362, 14, -92), (364, 206, 12), "rain"))

    sky = _sky(glitch)
    lights = [Light((380, 260, 200), "#9AAAE0", 1.1, 1000)]
    for hb, _ in BALCONIES:
        lights.append(Light((TOWER_X, hb + 9, FRONT + 10), "#F8B860", 0.35, 30, shadow=False))
    for lx, ly in ((-234, 28), (-127, 32), (-93, 32)):          # the door lanterns
        lights.append(Light((lx, ly, -150 + 46), "#F8B060", 0.55, 48, shadow=False))
    if not glitch:
        lights += [Light((-160, 70, -100), "#FFC870", 0.7, 160, shadow=False)]
    else:
        lights += [Light((272, 30, -60), "#8AB0FF", 0.6, 70, shadow=False)]
    return dict(world=World(objs), materials=mats, width=W, height=H, centre=CENTRE,
                lights=lights, key=0.7, ambient=0.2, top=240.0, ss=2, steps=180, sky=sky, post=_mist,
                bloom=[(WINDOW, "#FFC861", 9, 0.5), (CANDLE, "#F8B860", 8, 0.6), (GHOST, "#A8C8FF", 8, 0.55)])
