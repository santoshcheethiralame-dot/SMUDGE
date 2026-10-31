"""HQ: the Inkwell. An overturned ink bottle lying in the book's gutter,
shown as a cut-away diorama and furnished with school supplies.

Walkable floor: y = 0, x in [-205, 200], z in [-14, 24].
"""
import numpy as np

from envrender import Obj, World, Light, gradient_sky
from src import sdf

(GLASS, GLASS_RIM, FLOOR, STAMP, STAMP_EDGE, MATCH, MATCH_PRINT, CORK, NOTE_Y, NOTE_B, NOTE_P,
 STRING, PIN, CLIP, THIMBLE, GLOW, COTTON, DOORLIGHT, STOPPER, PAGE, WOOD, HAT, HATBAND, PENCIL, GRAPHITE, GLASS_FRONT) = range(1, 27)
LEFT_END, NECK_START, MOUTH = -214.0, 162.0, 236.0

W, H = 480, 270
CENTRE = (0.0, 88.0)
BOTTLE_Y, BOTTLE_R = 92.0, 132.0

# where the interactive things are, in world x (for the game)
HOTSPOTS = {"bed": -156, "caseboard": -86, "cards": 22, "hatrack": 104, "door": 214}


def _hash(p, s=1.0):
    return np.abs(np.modf(np.sin(np.floor(p[:, 0] * s) * 12.99 + np.floor(p[:, 1] * s) * 78.23 + np.floor(p[:, 2] * s) * 37.7) * 43758.5)[0])


MATERIALS = {
    GLASS: dict(ramp=["#050C14", "#0A1622", "#102233", "#173044", "#203F57", "#2C516D", "#3D6886"],
                pattern=lambda p, n: 0.5 * np.sin(p[:, 1] * 0.05 + p[:, 0] * 0.012) - 0.6 * (p[:, 1] < 26),
                pattern_gain=0.16, gloss=18, spec="#BFE4FF", dither=0.3),
    GLASS_FRONT: dict(ramp=["#0D2233", "#163447", "#21485F", "#2E5E79", "#3E7695", "#5592B2", "#77B2CF"],
                      gloss=10, spec="#FFFFFF", dither=0.3),
    GLASS_RIM: dict(ramp=["#1C3A52", "#2C5574", "#417595", "#5B96B5", "#7FB6D2", "#A9D3E8"], gloss=12, spec="#FFFFFF"),
    FLOOR: dict(ramp=["#020309", "#050915", "#0A1124", "#111B35", "#1A2849", "#253860"],
                pattern=lambda p, n: 0.6 * np.sin(np.hypot(p[:, 0] + 30, (p[:, 2] - 5) * 3.0) * 0.12),
                pattern_gain=0.14, gloss=30, spec="#7FA8E8", dither=0.3),
    STAMP: dict(ramp=["#5A1F1A", "#7E2E25", "#A54335", "#C65F4B", "#DE8467", "#EFAA8A"],
                sub=(lambda p: (np.abs(p[:, 0] + 30) > 50) | (np.abs(p[:, 2] - 5) > 13), STAMP_EDGE)),
    STAMP_EDGE: dict(ramp=["#7A6E58", "#A39577", "#C8BA98", "#E2D6B6", "#F2EAD2"]),
    MATCH: dict(ramp=["#3E0B08", "#621410", "#8A1F17", "#B02D21", "#CF4433", "#E86A52"]),
    MATCH_PRINT: dict(ramp=["#6B5A1C", "#93802A", "#B9A33B", "#D8C352", "#EDDB72"]),
    CORK: dict(ramp=["#3A2614", "#55391E", "#73502B", "#946B3B", "#B2874E", "#C9A066"],
               pattern=lambda p, n: (_hash(p, 0.9) > 0.72) * 0.9 - 0.2, pattern_gain=0.2),
    NOTE_Y: dict(ramp=["#6B5A1C", "#93802A", "#B9A33B", "#D8C352", "#EDDB72", "#F8EC98"]),
    NOTE_B: dict(ramp=["#25486A", "#33638E", "#4580B0", "#5E9DCC", "#7DB8E2", "#A2D0F0"]),
    NOTE_P: dict(ramp=["#6A2D3E", "#8F4058", "#B45874", "#D17594", "#E696B0", "#F4B8CB"]),
    STRING: dict(ramp=["#4A0A08", "#8E1A14", "#C9302A", "#EE5A4C"]),
    PIN: dict(ramp=["#4A0A08", "#8E1A14", "#C9302A", "#EE5A4C"], gloss=20, spec="#FFD0C6"),
    CLIP: dict(ramp=["#2A3038", "#46505C", "#6A7684", "#95A1AE", "#C2CCD6", "#E8EEF4"], gloss=26, spec="#FFFFFF"),
    THIMBLE: dict(ramp=["#23272E", "#3F4650", "#68717D", "#9AA4AF", "#C7D0D8"], gloss=24, spec="#FFFFFF",
                  pattern=lambda p, n: 0.6 * ((np.floor(p[:, 1] * 0.9) % 2) * (np.floor(np.arctan2(p[:, 2], p[:, 0] - 44) * 9) % 2) - 0.5),
                  pattern_gain=0.15),
    GLOW: dict(ramp=["#6FD6FF", "#B8EEFF", "#FFFFFF"], emissive=True),
    COTTON: dict(ramp=["#6E7488", "#9298AB", "#B6BCCC", "#D4D9E5", "#ECEFF6", "#FFFFFF"],
                 pattern=lambda p, n: 0.5 * (_hash(p, 0.6) - 0.5), pattern_gain=0.15),
    DOORLIGHT: dict(ramp=["#E8B060", "#F6CF8A", "#FFEBC2"], emissive=True,
                    pattern=lambda p, n: (np.sin(p[:, 1] * 0.25) > 0.3).astype(float)),
    STOPPER: dict(ramp=["#3A2614", "#55391E", "#73502B", "#946B3B", "#B2874E", "#C9A066"],
                  pattern=lambda p, n: (_hash(p, 0.8) > 0.7) * 0.8 - 0.2, pattern_gain=0.2),
    PAGE: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF"]),
    WOOD: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E", "#CF8A42"],
               pattern=lambda p, n: 0.5 * np.sin(p[:, 0] * 0.6 + 2 * np.sin(p[:, 1] * 0.2)), pattern_gain=0.12),
    HAT: dict(ramp=["#170D06", "#2E1B0E", "#4A2D17", "#6A4223", "#8C5A31"]),
    HATBAND: dict(ramp=["#4A0A08", "#8E1A14", "#C9302A", "#EE5A4C"]),
    PENCIL: dict(ramp=["#5E4410", "#8C661A", "#B98A25", "#E0AF35", "#F5CC56"]),
    GRAPHITE: dict(ramp=["#16181C", "#26292F", "#3A3E46", "#53585F"], gloss=20, spec="#C9CED6"),
}


def build(layer="room"):
    if layer == "front":
        return _front()
    objs = []

    # --- the bottle: back half of a glass cylinder lying along x, cut away at the front ---
    def bottle(p):
        dy, dz = p[:, 1] - BOTTLE_Y, p[:, 2] - 4.0
        r = np.sqrt(dy * dy + dz * dz)
        shell = np.abs(r - BOTTLE_R) - 4.0
        shell = np.maximum(shell, p[:, 2] + 30.0)                   # keep only the back half
        shell = np.maximum(shell, -p[:, 1] - 2.0)                   # nothing below the floor
        shell = np.maximum(shell, np.maximum(LEFT_END - p[:, 0], p[:, 0] - NECK_START - 2))
        # left end: the thick bottom of the bottle
        cap = np.maximum(np.abs(p[:, 0] - LEFT_END) - 7.0, r - BOTTLE_R - 4.0)
        cap = np.maximum(cap, p[:, 2] + 10.0)
        # rim highlight band where the cut-away edge is
        rim = np.maximum(np.abs(r - BOTTLE_R) - 5.0, np.abs(p[:, 2] + 30.0) - 1.6)
        rim = np.maximum(rim, np.maximum(-p[:, 1] - 2.0, np.maximum(LEFT_END - p[:, 0], p[:, 0] - NECK_START - 2)))
        d = np.minimum.reduce([shell, cap, rim])
        mat = np.where(rim <= np.minimum(shell, cap) + 0.01, GLASS_RIM, GLASS)
        return d, mat
    objs.append(Obj(bottle, (LEFT_END - 10, -4, -140), (NECK_START + 4, 230, 12), "bottle"))

    # --- the neck on the right, opening onto the night page: the door ---
    def neck(p):
        dz = p[:, 2] + 6.0
        cone_r = np.interp(p[:, 0], [NECK_START, 205, MOUTH + 10], [BOTTLE_R, 54, 54])
        dy = p[:, 1] - np.interp(p[:, 0], [NECK_START, 205, MOUTH + 10], [BOTTLE_Y, 56, 56])
        r = np.sqrt(dy * dy + dz * dz)
        shell = np.maximum(np.abs(r - cone_r) - 4.0, np.maximum(NECK_START - p[:, 0], p[:, 0] - MOUTH))
        shell = np.maximum(shell, p[:, 2] + 18.0)
        shell = np.maximum(shell, -p[:, 1] - 2.0)
        light = np.maximum(r - (cone_r - 4.5), np.abs(p[:, 0] - MOUTH + 3.0) - 2.0)
        light = np.maximum(light, p[:, 2] + 18.0)
        d = np.minimum(shell, light)
        mat = np.where(light < shell, DOORLIGHT, GLASS)
        return d, mat
    objs.append(Obj(neck, (NECK_START - 4, -4, -140), (MOUTH + 4, 230, 0), "neck"))

    # floor: a layer of dried ink, with a postage-stamp rug
    objs.append(Obj(lambda p: (np.maximum(sdf.box(p - [0, -3, 0], (250, 3, 70)), 0), FLOOR), (-252, -6, -72), (252, 0.2, 72), "floor"))
    objs.append(Obj(lambda p: (sdf.box(p - [-30, 0.4, 5], (54, 0.4, 16), 0.2), STAMP), (-86, -0.2, -13), (26, 1.0, 23), "rug"))

    # --- bed: a matchbox with a cotton-ball pillow ---
    def bed(p):
        box = sdf.box(p - [-160, 7, -6], (28, 7, 15), 0.8)
        label = sdf.box(p - [-160, 7, 9.4], (18, 4.5, 0.5), 0.2)
        mat = np.where(label < box, MATCH_PRINT, MATCH)
        d = np.minimum(box, label)
        pillow = sdf.ellipsoid(p, (-180, 17.5, -6), (9, 5.5, 10))
        blanket = sdf.box(p - [-150, 15, -6], (19, 1.8, 14), 1.2)
        mat = np.where(pillow < d, COTTON, mat)
        d = np.minimum(d, pillow)
        mat = np.where(blanket < d, NOTE_B, mat)
        return np.minimum(d, blanket), mat
    objs.append(Obj(bed, (-190, -1, -23), (-130, 25, 11), "bed"))

    # --- case board: a corkboard leaning on the glass, red string waiting for a case ---
    def caseboard(p):
        q = (p - [-86, 46, -36]) @ sdf.rot_x(-0.12)
        board = sdf.box(q, (34, 44, 2.2), 0.6)
        frame = np.maximum(sdf.box(q, (37, 47, 3.0), 0.8), -sdf.box(q - [0, 0, 1.2], (33, 43, 3.0)))
        d = np.minimum(board, frame)
        mat = np.where(frame < board, WOOD, CORK)
        notes = [((-104, 74), 0.1, NOTE_Y), ((-70, 70), -0.12, NOTE_P), ((-88, 36), 0.04, NOTE_B)]
        for (x, y), ang, m in notes:
            nq = (p - [x, y, -32.0]) @ sdf.rot_x(-0.12) @ sdf.rot_z(ang)
            n_ = sdf.box(nq, (9, 8, 0.4), 0.2)
            mat = np.where(n_ < d, m, mat)
            d = np.minimum(d, n_)
            pin = sdf.sphere(p, (x, y + 6, -30.6), 1.8)
            mat = np.where(pin < d, PIN, mat)
            d = np.minimum(d, pin)
        s1 = sdf.capsule(p, (-104, 80, -30.8), (-70, 76, -30.8), 0.6)
        s2 = sdf.capsule(p, (-70, 76, -30.8), (-88, 42, -31.4), 0.6)
        st = np.minimum(s1, s2)
        mat = np.where(st < d, STRING, mat)
        return np.minimum(d, st), mat
    objs.append(Obj(caseboard, (-126, -1, -46), (-46, 96, -26), "caseboard"))

    # --- formula-card wall: five empty paper-clip frames on the glass ---
    def cards(p):
        d = np.full(len(p), 1e9)
        mat = np.full(len(p), CLIP)
        for k, x in enumerate((-12, 5, 22, 39, 56)):
            outer = sdf.box(p - [x, 62, -40], (7, 10, 0.8), 0.6)
            inner = sdf.box(p - [x, 62, -40], (5.2, 8.2, 2.0))
            frame = np.maximum(outer, -inner)
            back = sdf.box(p - [x, 62, -40.8], (5.2, 8.2, 0.3))
            mat = np.where(frame < d, CLIP, mat)
            d = np.minimum(d, frame)
            mat = np.where(back < d, PAGE, mat)
            d = np.minimum(d, back)
        # a strip of masking-tape shelf below
        shelf = sdf.box(p - [22, 47, -38], (44, 1.2, 4), 0.5)
        mat = np.where(shelf < d, WOOD, mat)
        return np.minimum(d, shelf), mat
    objs.append(Obj(cards, (-24, 44, -44), (68, 74, -33), "cards"))

    # --- desk: a pencil-sharpener-shavings-free pencil stub table with a thimble lamp ---
    def desk(p):
        top = sdf.box(p - [44, 20, -8], (24, 2.2, 12), 0.8)
        legs = None
        for lx in (24, 64):
            for lz in (-17, 1):
                leg = sdf.cylinder_y(p - [lx, 9, lz], 1.8, 9.5, 0.5)
                legs = leg if legs is None else np.minimum(legs, leg)
        d = np.minimum(top, legs)
        mat = np.where(top < legs, PENCIL, GRAPHITE)
        thimble = sdf.round_cone(p, (34, 22, -10), (34, 34, -10), 6.5, 5.2)
        thimble = np.maximum(thimble, -sdf.sphere(p, (34, 37, -10), 4.2))
        mat = np.where(thimble < d, THIMBLE, mat)
        d = np.minimum(d, thimble)
        glow = sdf.sphere(p, (34, 34.5, -10), 4.0)
        mat = np.where(glow < d, GLOW, mat)
        d = np.minimum(d, glow)
        book = sdf.box((p - [54, 23.4, -6]) @ sdf.rot_y(0.3), (8, 1.2, 6), 0.3)
        mat = np.where(book < d, NOTE_Y, mat)
        return np.minimum(d, book), mat
    objs.append(Obj(desk, (18, -1, -24), (72, 40, 8), "desk"))

    # --- hat rack: a push-pin stand with Smudge's spare fedora ---
    def hatrack(p):
        pole = sdf.cylinder_y(p - [104, 22, -14], 1.4, 22, 0.4)
        base = sdf.cylinder_y(p - [104, 1.5, -14], 8, 1.5, 0.8)
        head = sdf.sphere(p, (104, 46, -14), 5.0)
        d = np.minimum.reduce([pole, base])
        mat = np.full(len(p), CLIP)
        mat = np.where(head < d, PIN, mat)
        d = np.minimum(d, head)
        q = (p - [104, 44, -14]) @ sdf.rot_z(0.25)
        brim = sdf.ellip_cylinder_y(q - [0, -1, 0], 10.0, 9.0, 0.5, 0.4)
        crown = sdf.ellip_cylinder_y(q - [0, 2.5, 0], 6.0, 5.4, 3.0, 1.8)
        band = sdf.ellip_cylinder_y(q - [0, 0.6, 0], 6.2, 5.6, 0.9, 0.3)
        hat = np.minimum(brim, crown)
        mat = np.where(hat < d, HAT, mat)
        d = np.minimum(d, hat)
        mat = np.where(band < d, HATBAND, mat)
        return np.minimum(d, band), mat
    objs.append(Obj(hatrack, (90, -1, -26), (118, 56, -2), "hatrack"))

    # --- cork stopper lying by the door, and a stack of stamp-books on the left ---
    objs.append(Obj(lambda p: (sdf.cylinder_y((p - [150, 12, -22]) @ sdf.rot_z(np.pi / 2 - 0.1), 12, 15, 2.5), STOPPER),
                    (132, -1, -36), (170, 26, -8), "stopper"))

    def books(p):
        d = np.full(len(p), 1e9)
        mat = np.full(len(p), NOTE_P)
        for k, (h, m, ang) in enumerate(((6, NOTE_P, 0.0), (5, NOTE_B, 0.12), (5, NOTE_Y, -0.08), (4, MATCH, 0.05))):
            y = 3 + sum((6, 5, 5, 4)[:k]) * 1.0 + h / 2 - 3
            b = sdf.box((p - [-198, y + 3, -26]) @ sdf.rot_y(ang), (10, h / 2, 8), 0.6)
            mat = np.where(b < d, m, mat)
            d = np.minimum(d, b)
        return d, mat
    objs.append(Obj(books, (-212, -1, -40), (-184, 26, -12), "books"))

    sky = gradient_sky(W, H, "#03040B", "#0B1022")
    lights = [Light((MOUTH - 6, 56, -6), "#FFC877", 1.8, 470, ignore=("neck",)),
              Light((34, 36, -4), "#7FD8FF", 0.95, 120, ignore=("desk",)),
              Light((-60, 190, 120), "#6F8FD8", 0.25, 500, shadow=False)]
    return dict(world=World(objs), materials=MATERIALS, width=W, height=H, centre=CENTRE,
                lights=lights, key=0.12, ambient=0.07, top=232.0, ss=2, steps=170, sky=sky,
                bloom=[(GLOW, "#7FD8FF", 26, 0.7), (DOORLIGHT, "#FFC877", 30, 0.6)])


def _front():
    """Foreground: the front half of the bottle, with a broken-out hole we look through."""
    def front(p):
        dy, dz = p[:, 1] - BOTTLE_Y, p[:, 2] - 4.0
        r = np.sqrt(dy * dy + dz * dz)
        shell = np.abs(r - BOTTLE_R) - 3.0
        shell = np.maximum(shell, -(p[:, 2] - 60.0))
        shell = np.maximum(shell, np.maximum(LEFT_END - p[:, 0], p[:, 0] - NECK_START))
        ang = np.arctan2(p[:, 1] - 96.0, p[:, 0] + 20.0)
        jag = 1.0 + 0.05 * np.sin(ang * 9.0) + 0.03 * np.sin(ang * 23.0 + 1.3)
        hole = ((p[:, 0] + 20.0) / (196.0 * jag)) ** 2 + ((p[:, 1] - 96.0) / (128.0 * jag)) ** 2 - 1.0
        shell = np.maximum(shell, -hole * 20.0)
        return shell, GLASS_FRONT
    objs = [Obj(front, (LEFT_END - 4, -40, 50), (NECK_START + 4, 230, 150), "front")]
    lights = [Light((MOUTH, 56, 40), "#FFC877", 1.2, 470, shadow=False),
              Light((-60, 190, 160), "#6F8FD8", 0.4, 500, shadow=False)]
    return dict(world=World(objs), materials=MATERIALS, width=W, height=H, centre=CENTRE,
                lights=lights, key=0.35, ambient=0.1, top=232.0, ss=2, steps=120)
