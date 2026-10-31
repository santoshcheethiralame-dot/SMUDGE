"""The casebook map: an open leather-bound book on a desk (face-on, 480x270), and one paper pop-up diorama per
chapter, seen from the usual 20-degree camera, to stand on its pages.

    build(which="book")      the backdrop; pages lie at game x 16..238 and 242..464, y 38..256
    build(which="pop3")      the pop-up for case 3, 48 x 44, its paper tab's front edge at the image's bottom centre

    python build_casebook.py renders them all into game/public/assets/map
"""
import numpy as np

from envrender import Obj, World, Light
from src import sdf
from scene_instruments import _faceon, _bench, _put

(DESK, LEATHER, PAGE, RULE, MARGIN, BRASS, RIBBON, RIBBON_G, STITCH, EDGE, COFFEE,
 PAPER, P_RED, P_BLUE, P_SKY, P_SAND, P_TERRA, P_GREEN, P_YELLOW, P_GREY, P_NAVY, LAMP, P_PINK, P_TEAL, P_WOOD) = range(1, 26)

MATERIALS = {
    DESK: dict(ramp=["#120A06", "#1E120A", "#2A1A0E", "#382414", "#47301B"],
               pattern=lambda p, n: 0.5 * np.sin(p[:, 1] * 0.6 + 3 * np.sin(p[:, 0] * 0.013 + p[:, 1] * 0.05)), pattern_gain=0.3),
    LEATHER: dict(ramp=["#1E0806", "#34100C", "#4E1A14", "#6A2A1E", "#86402C"], gloss=10, spec="#C88A6A", dither=0.3,
                  pattern=lambda p, n: 0.5 * np.sin(p[:, 0] * 1.7) * np.sin(p[:, 1] * 1.9), pattern_gain=0.12),
    PAGE: dict(ramp=["#A99B78", "#C9BC98", "#E3D8B8", "#F2E9CF", "#FBF5E4"], dither=0.25, expo=1.25),
    RULE: dict(ramp=["#7C93B4", "#94AACA", "#AFC2DD", "#C6D5EA"], expo=1.25),
    MARGIN: dict(ramp=["#9C4A4A", "#BC6262", "#D47676", "#E69494"], expo=1.25),
    BRASS: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848", "#FFE08A"], gloss=24, spec="#FFFFFF"),
    RIBBON: dict(ramp=["#3A0907", "#62110D", "#8E1A14", "#B8251C", "#DE3B2E"], gloss=12, spec="#FF9C8C"),
    RIBBON_G: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848"], gloss=12, spec="#FFF4C8"),
    STITCH: dict(ramp=["#8F8268", "#B3A584", "#CFC2A0"]),
    EDGE: dict(ramp=["#7A6E54", "#9C8F70", "#BCAE8C", "#D6CAA8"]),
    COFFEE: dict(ramp=["#8A6A44", "#A4835A", "#BC9C70", "#D2B488"], expo=1.25),
    PAPER: dict(ramp=["#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF", "#FFFBEF"], dither=0.15),
    P_RED: dict(ramp=["#5E100C", "#8E1A14", "#C9302A", "#EE5A4C", "#FF8A78"]),
    P_BLUE: dict(ramp=["#0F2E5C", "#1B4885", "#2C66AE", "#4A8AD0", "#7DB2EA"]),
    P_SKY: dict(ramp=["#3B5E8E", "#557AA9", "#6E95C2", "#88AFD9", "#A3C7EA"]),
    P_SAND: dict(ramp=["#80492E", "#A4623A", "#C47E4A", "#DE9C5E", "#EDB874"]),
    P_TERRA: dict(ramp=["#4A1F1E", "#6B2E26", "#8E4230", "#B0583A", "#CC7448", "#E0925E"]),
    P_GREEN: dict(ramp=["#16402A", "#215A3A", "#2E764C", "#409560", "#5AB276", "#7ED092"]),
    P_YELLOW: dict(ramp=["#7A5A12", "#B8891E", "#E6B43A", "#F8D66E", "#FFF0A8"]),
    P_GREY: dict(ramp=["#2C2830", "#433D48", "#5C5462", "#766C7C", "#928898", "#B0A8B4"]),
    P_NAVY: dict(ramp=["#0E1938", "#16264F", "#22305C", "#2E3F78", "#3E52A0"]),
    LAMP: dict(ramp=["#F2B44C", "#FFD27A", "#FFE9B0"], emissive=True),
    P_PINK: dict(ramp=["#5A2234", "#7E3448", "#A24A60", "#C2687C", "#DC8C9C"]),
    P_TEAL: dict(ramp=["#0B3B3A", "#14615E", "#1F8C86", "#3DB8AE", "#86E0D6"]),
    P_WOOD: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E", "#CF8A42"]),
}


# ------------------------------------------------------------------ the book

def book():
    W, H = 480, 270

    def f(q):
        gx, gy = q[:, 0] + W / 2, H / 2 - q[:, 1]                  # game pixels
        desk = q[:, 2] + 12.0
        d, mat = desk, np.full(len(q), DESK)
        cover = sdf.box(q - [0, -(147.0 - H / 2), -8.0], (232.0, 115.0, 3.0), 6.0)
        d, mat = _put(d, mat, cover, LEATHER)
        # each page block bulges toward the reader and dips into the gutter
        for x0, x1 in ((16.0, 238.0), (242.0, 464.0)):
            t = np.clip((gx - x0) / (x1 - x0), 0, 1)
            gutter = 1 - t if x0 > 200 else t                       # 1 at the gutter edge
            surf = 3.5 + 2.6 * np.sin(np.pi * np.clip(t, 0, 1)) ** 0.6 - 4.5 * np.clip(gutter - 0.9, 0, 1) * 10
            block = np.maximum.reduce([q[:, 2] - surf, -q[:, 2] - 5.0, x0 - gx, gx - x1, 38.0 - gy, gy - 256.0]) * 0.8
            # the page edges: a stack of thin lines along the outer and bottom edges
            pm = np.where((gy > 253.5) & (((gx + 600) % 3.0) < 1.0), EDGE, PAGE)
            ruled = (np.abs(((gy - 58.0 + 600) % 12.0) - 0.0) < 0.9) & (gy > 50) & (gy < 250) & (gx > x0 + 3) & (gx < x1 - 3)
            pm = np.where(ruled & (pm == PAGE), RULE, pm)
            pm = np.where((np.abs(gx - (x0 + 20.5)) < 0.7) & (gy > 40) & (pm != EDGE), MARGIN, pm)
            d, mat = _put(d, mat, block, pm)
        # a coffee ring on the right page, stitching down the gutter
        ring = np.abs(np.hypot(gx - 436.0, gy - 232.0) - 11.0) < 1.0
        mat = np.where(ring & (mat == PAGE) & (np.sin(np.arctan2(gy - 232, gx - 436) * 3) > -0.6), COFFEE, mat)
        stitch = (np.abs(gx - 240.0) < 2.0) & (((gy + 600) % 8.0) < 4.0) & (gy > 40) & (gy < 254)
        d, mat = _put(d, mat, np.where(stitch, np.maximum.reduce([np.abs(gx - 240.0) - 0.8, q[:, 2] - 1.0, -q[:, 2] - 4.0]), 1e9), STITCH)
        # brass corners on the cover
        for cx, cy, sx, sy in ((8.0, 32.0, 1, 1), (472.0, 32.0, -1, 1), (8.0, 262.0, 1, -1), (472.0, 262.0, -1, -1)):
            u, v = (gx - cx) * sx, (gy - cy) * sy
            corner = np.maximum.reduce([u + v - 22.0, -u - 1.0, -v - 1.0, np.abs(q[:, 2] + 4.0) - 1.4]) * 0.7
            d, mat = _put(d, mat, corner, BRASS)
        # two ribbon bookmarks out of the gutter, over the bottom edge and onto the desk
        for k, (m, off) in enumerate(((RIBBON, -4.0), (RIBBON_G, 5.0))):
            wob = off + np.clip(gy - 240.0, 0, None) * (0.5 if k else -0.4)
            rib = np.maximum.reduce([np.abs(gx - 240.0 - wob) - 2.6, 238.0 - gy, gy - (272.0 - 6 * k),
                                     np.abs(q[:, 2] - (np.where(gy < 256, 6.5, -2.0) + 0.0)) - 0.7]) * 0.7
            notch = (gy > 266.0 - 6 * k) & (np.abs(gx - 240.0 - wob) < (gy - (266.0 - 6 * k)))
            d, mat = _put(d, mat, np.where(notch, 1e9, rib), m)
        return d, mat
    return _faceon(f, W, H, depth=20.0)


# ------------------------------------------------------------------ the pop-ups

def _tab(p):
    """The folded paper tab every pop-up stands on."""
    return sdf.box(p - [0, 0.6, 0], (20.0, 0.6, 9.0), 0.4), PAPER


def _scene(parts):
    def f(p):
        d, mat = _tab(p)
        mat = np.full(len(p), PAPER)
        for dd, mm in parts(p):
            d, mat = _put(d, mat, dd, mm)
        return d, mat
    return f


def pop(num):
    def bay(p):
        light = sdf.cylinder_y(p - [-8.0, 14.0, -2.0], 4.2 - 0.06 * (p[:, 1] - 14.0), 13.0, 0.5)
        stripes = np.abs(((p[:, 1] + 100) % 7.0) - 3.5) < 1.6
        yield light, np.where(stripes, P_RED, PAPER)
        yield sdf.cylinder_y(p - [-8.0, 29.0, -2.0], 3.4, 2.0, 0.4), LAMP
        yield np.maximum(sdf.ellipsoid(p, (-8.0, 31.5, -2.0), (4.6, 4.0, 4.6)), 31.0 - p[:, 1]), P_RED
        wave = np.maximum.reduce([np.abs(p[:, 2] - 4.0) - 0.6, np.abs(p[:, 0]) - 19.0, p[:, 1] - (3.5 + 1.6 * np.sin(p[:, 0] * 0.5)), 1.0 - p[:, 1]])
        yield wave, P_BLUE
        hull = np.maximum(sdf.box(p - [9.0, 5.0, 1.0], (6.0, 2.0, 2.0), 0.3), np.abs(p[:, 0] - 9.0) - 6.0 + (p[:, 1] - 3.0) * 0.8)
        yield hull, PAPER
        yield np.maximum.reduce([np.abs(p[:, 2] - 1.0) - 0.3, p[:, 0] - 9.5, 4.0 - p[:, 0] + (p[:, 1] - 7.0) * 0.4, 7.0 - p[:, 1], p[:, 1] - 16.0]), PAPER

    def mesa(p):
        butte = sdf.box(p - [-3.0, 9.0, -3.0], (12.0, 9.0, 5.0), 1.0)
        butte = np.maximum(butte, (np.abs(p[:, 0] + 3.0) - 12.0 + 0.3 * (p[:, 1] - 18.0)) * 0.9)
        yield butte, np.where(np.abs(((p[:, 1] + 100) % 6.0) - 3.0) < 0.9, P_SAND, P_TERRA)
        yield sdf.box(p - [3.0, 1.4, 5.0], (16.0, 0.4, 2.6), 0.2), P_GREY
        shaft = sdf.capsule(p, (10.0, 4.0, 5.5), (10.0, 18.0, 5.5), 1.0)
        head = np.maximum.reduce([np.abs(p[:, 2] - 5.5) - 0.8, np.abs(p[:, 0] - 10.0) * 1.1 + (p[:, 1] - 24.0), 17.0 - p[:, 1]])
        yield np.minimum(shaft, head), P_RED

    def valley(p):
        for sx in (-1, 1):
            cliff = np.maximum(sdf.box(p - [sx * 13.0, 11.0, -3.0], (6.0, 11.0, 5.0), 1.0), (sx * p[:, 0] - 13.0 + 0.25 * (p[:, 1] - 22.0)))
            yield cliff, P_GREEN
        tower = sdf.box(p - [0, 12.0, 1.0], (3.6, 12.0, 3.0), 0.5)
        yield tower, PAPER
        yield np.maximum(sdf.box(p - [0, 27.0, 1.0], (5.0, 3.0, 4.0), 0.5), (np.abs(p[:, 0]) + p[:, 1]) - 31.0), P_RED
        yield sdf.round_cone(p, (0, 21.0, 4.2), (0, 17.0, 4.2), 1.0, 2.4), P_YELLOW
        for r in (6.0, 9.0):
            arc = np.maximum(np.abs(np.hypot(p[:, 0], p[:, 1] - 19.0) - r) - 0.5, np.maximum(np.abs(p[:, 2] - 4.5) - 0.3, -np.abs(p[:, 0]) + 3.0))
            yield np.maximum(arc, p[:, 1] - 26.0), P_SKY

    def heights(p):
        yield sdf.box(p - [-6.0, 14.0, -2.0], (3.4, 14.0, 3.4), 0.4), P_GREY
        yield sdf.sphere(p, (-6.0, 30.0, -2.0), 3.0), LAMP
        yield sdf.box(p - [6.0, 1.3, 2.0], (12.0, 0.25, 3.0), 0.1), P_NAVY
        yield sdf.box(p - [12.0, 6.0, -3.0], (3.0, 6.0, 3.0), 0.4), PAPER
        yield np.maximum(sdf.cylinder_y((p - [14.0, 22.0, -6.0]) @ sdf.rot_x(np.pi / 2), 4.0, 0.4, 0.2), -1e9), P_YELLOW

    def prism(p):
        tri = np.maximum.reduce([np.abs(p[:, 2]) - 4.0, p[:, 1] * 0.5 + np.abs(p[:, 0] + 6.0) * 0.866 - 9.0, 0.5 - p[:, 1]])
        yield tri, P_SKY
        for k, m in enumerate((P_RED, P_YELLOW, P_GREEN, P_BLUE)):
            a = -0.15 + 0.13 * k
            r = (p - [-2.0, 8.0, 0]) @ sdf.rot_z(a)
            yield np.maximum.reduce([np.abs(r[:, 1]) - 0.9, -r[:, 0], r[:, 0] - 20.0, np.abs(r[:, 2]) - 0.3]), m

    def ohm(p):
        for sx in (-1, 1):
            yield sdf.capsule(p, (sx * 6.0, 0, -2.0), (sx * 1.5, 28.0, -2.0), 0.7), P_GREY
        for y, w in ((10.0, 4.5), (18.0, 3.2), (24.0, 7.0)):
            yield sdf.capsule(p, (-w, y, -2.0), (w, y, -2.0), 0.6), P_GREY
        bolt = np.maximum(np.abs(p[:, 2] - 4.0) - 0.4, np.abs(p[:, 0] - 10.0 - (np.where(p[:, 1] > 9, 1, -1)) * 1.5 + (p[:, 1] - 9.0) * 0.3) - 1.6)
        yield np.maximum(bolt, np.abs(p[:, 1] - 9.0) - 7.0), P_YELLOW
        yield sdf.box(p - [-12.0, 4.0, 3.0], (4.0, 4.0, 3.0), 0.3), PAPER
        yield sdf.box(p - [-12.0, 5.0, 6.1], (1.2, 1.2, 0.2)), LAMP

    def kelvin(p):
        yield sdf.ellipsoid(p, (0, 1.4, 1.0), (15.0, 2.0, 7.0)), P_TEAL
        yield sdf.capsule(p, (12.0, 2.0, -3.0), (12.0, 22.0, -3.0), 1.6), PAPER
        yield sdf.sphere(p, (12.0, 3.0, -3.0), 2.6), P_RED
        yield sdf.capsule(p, (12.0, 3.0, -1.3), (12.0, 14.0, -1.3), 0.6), P_RED
        for x, y, r in ((-6.0, 7.0, 2.6), (-3.0, 11.0, 3.0), (-7.0, 15.0, 2.4), (-2.0, 18.0, 2.0)):
            yield sdf.sphere(p, (x, y, 0.0), r), PAPER

    def acid(p):
        flask = sdf.round_cone(p, (0, 6.0, 0), (0, 15.0, 0), 8.0, 2.0)
        neck = sdf.cylinder_y(p - [0, 20.0, 0], 2.0, 5.0, 0.4)
        glass = np.maximum(np.minimum(flask, neck), -np.minimum(sdf.round_cone(p, (0, 6.0, 0), (0, 15.0, 0), 7.0, 1.2), sdf.cylinder_y(p - [0, 22.0, 0], 1.2, 6.0)))
        yield glass, P_SKY
        yield np.maximum(sdf.round_cone(p, (0, 6.0, 0), (0, 15.0, 0), 7.0, 1.2), p[:, 1] - 8.5), P_GREEN
        for x, y in ((-2.0, 13.0), (1.5, 17.0), (-0.5, 26.0), (1.0, 30.0)):
            yield sdf.sphere(p, (x, y, 1.0), 1.0), P_GREEN

    def watt(p):
        yield sdf.box(p - [-10.0, 14.0, -2.0], (1.6, 14.0, 1.6), 0.3), P_YELLOW
        yield sdf.box(p - [0, 27.0, -2.0], (13.0, 1.4, 1.4), 0.3), P_YELLOW
        yield sdf.capsule(p, (11.0, 26.0, -2.0), (11.0, 13.0, -2.0), 0.3), P_GREY
        yield sdf.box(p - [11.0, 9.0, -2.0], (4.0, 4.0, 4.0), 0.4), P_WOOD
        g = np.hypot(p[:, 0] + 10.0, p[:, 1] - 6.0)
        teeth = np.maximum(g - 6.0 - 1.2 * (np.sin(np.arctan2(p[:, 1] - 6.0, p[:, 0] + 10.0) * 8) > 0), np.abs(p[:, 2] - 2.5) - 0.8)
        yield np.maximum(teeth, 2.0 - g), P_GREY

    parts = {1: bay, 2: mesa, 3: valley, 4: heights, 5: prism, 6: ohm, 7: kelvin, 8: acid, 9: watt}[num]
    return _bench([Obj(_scene(parts), (-24, -1, -12), (24, 36, 12), f"pop{num}")], 48, 44, (0.0, 13.0))


PROPS = {"book": book, **{f"pop{n}": (lambda n=n: pop(n)) for n in range(1, 10)}}


def build(which="book"):
    s = PROPS[which]()
    lights = [Light((-200, 260, 220), "#FFC46B", 0.8, 900), Light((240, 120, 160), "#6F8FD8", 0.25, 600, shadow=False)]
    return dict(world=World(s["objs"]), materials=MATERIALS, width=s["width"], height=s["height"], centre=s["centre"],
                lights=lights, key=0.5, ambient=0.12, top=s["top"], ss=2, steps=160)
