"""Lab instruments and props, rendered at the size the game draws them (1 px = 1 world px).

Two kinds of prop:
  * bench props (balance, crate, dice, weights, rack) sit in the world, seen from the usual 20-degree camera;
  * face-on instruments (phone, dial meter, thermometer, protractor, glassware) are modelled in screen space:
    x right, y up, z toward the viewer, in the same game pixels the instrument code uses, so dynamic parts
    (needles, mercury, ticks) drawn by Phaser land exactly on them.

    python build_instruments.py            renders every prop into game/public/assets/lab
"""
import numpy as np

from envrender import Obj, World, Light
from src import sdf
from src.render import RIGHT, UP, RAY

(BODY, LCD, METAL, GOLD, RED, BLUE, RUBBER, GLASS, BAKELITE, FACE, ENAMEL, WOOD, WOOD_DARK, PAPER, IVORY, INKDOT,
 ACRYLIC, MERC, LENS, PHONE, NAVY, GEMR) = range(1, 23)

MATERIALS = {
    BODY: dict(ramp=["#3B3F4A", "#6A6F7C", "#9DA2AE", "#C9CDD5", "#E6E8EC", "#F7F8FA"], gloss=18, spec="#FFFFFF", dither=0.12),
    LCD: dict(ramp=["#06170E", "#0B2A1A", "#123A24"], dither=0.0),
    METAL: dict(ramp=["#23272E", "#3F4650", "#68717D", "#9AA4AF", "#C7D0D8", "#E8EEF4"], gloss=24, spec="#FFFFFF", dither=0.15),
    GOLD: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848", "#FFE08A", "#FFF4C8"], gloss=26, spec="#FFFFFF", dither=0.15),
    RED: dict(ramp=["#4A0A08", "#8E1A14", "#C9302A", "#EE5A4C", "#FF9C8C"], gloss=30, spec="#FFFFFF"),
    BLUE: dict(ramp=["#0D1F45", "#163066", "#21458A", "#2E5CAD", "#4277CC", "#5F95E2"], gloss=30, spec="#FFFFFF"),
    RUBBER: dict(ramp=["#0A0A0E", "#16161C", "#24242C", "#34343E"]),
    GLASS: dict(ramp=["#2F6496", "#4F8FC6", "#86BDE6", "#C2E1F3", "#EAF6FF"], gloss=40, spec="#FFFFFF", dither=0.1),
    BAKELITE: dict(ramp=["#140B06", "#24150C", "#3A2414", "#53361F", "#6E4A2C"], gloss=22, spec="#E8D2B8", dither=0.15),
    FACE: dict(ramp=["#CBBE9A", "#E3D8B8", "#F2E9CF", "#FBF5E4"], dither=0.0, expo=1.6),
    ENAMEL: dict(ramp=["#B9AE90", "#D6CCAE", "#EDE5CC", "#FAF5E6"], dither=0.0, expo=1.5),
    WOOD: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E", "#CF8A42"],
               pattern=lambda p, n: 0.5 * np.sin(p[:, 0] * 0.9 + 3 * np.sin(p[:, 1] * 0.21 + p[:, 2] * 0.13)), pattern_gain=0.22),
    WOOD_DARK: dict(ramp=["#1A0D04", "#2A1608", "#47270F", "#683A18", "#8C5022"]),
    PAPER: dict(ramp=["#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF", "#FFFBEF"], dither=0.0, expo=1.3),
    IVORY: dict(ramp=["#7F786A", "#ABA493", "#D2CCBC", "#EDE9DF", "#FFFFFF"], gloss=20, spec="#FFFFFF", dither=0.1),
    INKDOT: dict(ramp=["#05060F", "#0E1938", "#1A2E5C"]),
    ACRYLIC: dict(ramp=["#3E7C8C", "#62A6B4", "#8CCAD3", "#B6E4E8", "#E2F7F8"], gloss=34, spec="#FFFFFF", dither=0.1),
    MERC: dict(ramp=["#4A0A08", "#8E1A14", "#C9302A", "#EE5A4C", "#FF9C8C"], gloss=40, spec="#FFFFFF"),
    LENS: dict(ramp=["#05060F", "#0E1938", "#1C3D63", "#2F6496"], gloss=50, spec="#BFE0FF"),
    PHONE: dict(ramp=["#07080D", "#0E1018", "#171A26", "#222636", "#2E3448"], gloss=20, spec="#9AA6C8", dither=0.1),
    NAVY: dict(ramp=["#05060F", "#0E1938", "#16264F", "#22305C", "#2E3F78"]),
    GEMR: dict(ramp=["#4A0A08", "#8E1A14", "#C9302A", "#EE5A4C", "#FF9C8C"], gloss=40, spec="#FFFFFF"),
}

LIFT = 100.0                    # face-on props float here so no ray is cut off below the ground plane
FWD = -RAY                      # toward the viewer
COS, SIN = UP[1], FWD[1]


def _put(d, mat, dd, mm):
    mat = np.where(dd < d, mm, mat)
    return np.minimum(d, dd), mat


def _screen(p):
    """World points -> screen-space (x right, y up, z toward the viewer) around the prop's centre."""
    p = p - [0, LIFT, 0]
    return np.stack([p @ RIGHT, p @ UP, p @ FWD], 1)


def _faceon(fn, w, h, depth=30.0):
    """A face-on prop of w x h game pixels, modelled by fn(q) in screen space centred on the image."""
    corners = np.array([[sx * (w / 2 + 4), sy * (h / 2 + 4), sz * depth] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    world = corners[:, :1] * RIGHT + corners[:, 1:2] * UP + corners[:, 2:3] * FWD + [0, LIFT, 0]
    obj = Obj(lambda p: fn(_screen(p)), world.min(0), world.max(0), "prop")
    return dict(objs=[obj], width=w, height=h, centre=(0.0, LIFT * COS), top=world[:, 1].max() + 2)


def _bench(objs, w, h, centre):
    return dict(objs=objs, width=w, height=h, centre=centre, top=80.0)


# ------------------------------------------------------------------ face-on instruments

def _d_shape(q, r, cut):
    """A D: a disc of radius r around the origin, kept above y = -cut."""
    return np.maximum(np.hypot(q[:, 0], q[:, 1]) - r, -cut - q[:, 1])


def phone():
    """The storm-video phone, landscape. Image at game (12, 76), 282 x 174; screen hole 262 x 150 at (22, 92)."""
    W, H = 282, 174

    def f(q):
        frame = sdf.box(q, (W / 2, H / 2, 3.5), 9.0)
        face = sdf.box(q - [0, 0, 0.8], (W / 2 - 1.6, H / 2 - 1.6, 3.5), 7.5)
        hole = sdf.box(q - [0, -4.0, 0], (131.0, 75.0, 12.0), 2.0)
        d, mat = np.maximum(frame, -hole), np.full(len(q), METAL)
        d, mat = _put(d, mat, np.maximum(face, -hole), PHONE)
        # glass edge round the screen, front camera, speaker slot, volume buttons on the top edge
        lip = np.maximum(sdf.box(q - [0, -4.0, 3.6], (132.5, 76.5, 0.6), 2.5), -hole)
        d, mat = _put(d, mat, lip, NAVY)
        d, mat = _put(d, mat, sdf.sphere(q, (-136.0, 0.0, 4.2), 1.9), LENS)
        d, mat = _put(d, mat, sdf.capsule(q, (136.0, -14.0, 4.0), (136.0, 14.0, 4.0), 0.9), RUBBER)
        for x0, x1 in ((48.0, 64.0), (70.0, 86.0)):
            d, mat = _put(d, mat, sdf.capsule(q, (x0, H / 2 + 0.2, 0), (x1, H / 2 + 0.2, 0), 1.4), METAL)
        return d, mat
    return _faceon(f, W, H)


def dial():
    """Analogue meter housing. Image at game (50, 112), 192 x 118; needle pivot at game (146, 208)."""
    W, H = 192, 118
    P = np.array([0.0, -37.0, 0.0])                         # the pivot, in image-centred screen space

    def f(q):
        case = sdf.box(q - [0, 0, -4.0], (W / 2 - 1, H / 2 - 1, 5.0), 9.0)
        d, mat = case, np.full(len(q), BAKELITE)
        r = q - P
        bezel = np.maximum(np.maximum(_d_shape(r, 86.0, 14.0), -_d_shape(r, 81.5, 9.5)), np.abs(q[:, 2] - 1.6) - 1.4)
        d, mat = _put(d, mat, bezel, METAL)
        face = np.maximum(_d_shape(r, 81.5, 9.5), np.abs(q[:, 2] - 0.6) - 0.6)
        d, mat = _put(d, mat, face, FACE)
        # mirror strip under the scale, a red danger arc at the top end, four screws, two terminals
        for x, y in ((-84.0, 50.0), (84.0, 50.0), (-84.0, -50.0), (84.0, -50.0)):
            d, mat = _put(d, mat, sdf.ellipsoid(q, (x, y, 1.6), (3.0, 3.0, 1.4)), METAL)
        for x, m in ((-64.0, RED), (64.0, INKDOT)):
            post = sdf.cylinder_y((q - [x, -50.0, 2.0]) @ sdf.rot_x(np.pi / 2), 5.0, 2.4, 1.2)
            d, mat = _put(d, mat, post, m)
            d, mat = _put(d, mat, sdf.sphere(q, (x, -50.0, 5.4), 1.8), METAL)
        plate = sdf.box(q - [0, -50.0, 1.2], (26.0, 5.0, 0.6), 1.0)
        d, mat = _put(d, mat, plate, GOLD)
        return d, mat
    return _faceon(f, W, H)


def hub():
    """The brass boss that covers a needle's pivot."""
    def f(q):
        return np.minimum(sdf.ellipsoid(q, (0, 0, 0), (5.0, 5.0, 3.0)), sdf.sphere(q, (0, 0, 2.6), 1.2)), GOLD
    return _faceon(f, 14, 14)


def knob():
    """The red drag knob on a protractor arm."""
    def f(q):
        d, mat = sdf.ellipsoid(q, (0, 0, 0), (5.6, 5.6, 3.6)), np.full(len(q), RED)
        return _put(d, mat, sdf.torus_y((q - [0, 0, 1.6]) @ sdf.rot_x(np.pi / 2), 4.4, 0.7), GOLD)
    return _faceon(f, 16, 16)


def thermo():
    """Thermometer on an enamel plate. Image at game (122, 92), 64 x 146; tube at game x 136, bulb at y 223."""
    W, H = 64, 146

    def f(q):
        plate = sdf.box(q - [0, 0, -4.0], (W / 2 - 1, H / 2 - 1, 2.0), 5.0)
        d, mat = plate, np.full(len(q), ENAMEL)
        rim = np.maximum(sdf.box(q - [0, 0, -3.0], (W / 2 - 1, H / 2 - 1, 1.6), 5.0), -sdf.box(q, (W / 2 - 4, H / 2 - 4, 9.0), 3.0))
        d, mat = _put(d, mat, rim, GOLD)
        for x, y in ((-24.0, 66.0), (24.0, 66.0), (-24.0, -66.0), (24.0, -66.0)):
            d, mat = _put(d, mat, sdf.ellipsoid(q, (x, y, -1.6), (2.4, 2.4, 1.2)), METAL)
        tube = sdf.capsule(q, (-18.0, -52.0, 0.5), (-18.0, 58.0, 0.5), 5.0)
        d, mat = _put(d, mat, tube, GLASS)
        bore = sdf.capsule(q, (-18.0, -52.0, 3.0), (-18.0, 55.0, 3.0), 2.2)
        d, mat = _put(d, mat, np.maximum(bore, tube - 0.2) - 0.05, ENAMEL)
        d, mat = _put(d, mat, sdf.sphere(q, (-18.0, -58.0, 0.5), 8.0), MERC)
        cap = sdf.cylinder_y(q - [-18.0, 61.0, 0.5], 5.6, 2.6, 1.0)
        d, mat = _put(d, mat, cap, GOLD)
        return d, mat
    return _faceon(f, W, H)


def protractor(R):
    """A quarter protractor, vertex at the image's bottom-right: the ring from R-13 to R+3 and two edge strips."""
    S = R + 10

    def f(q):
        v = q - [S / 2 - 5.0, -(S / 2 - 5.0), 0]               # vertex-centred
        rr = np.hypot(v[:, 0], v[:, 1])
        ring = np.maximum(np.maximum(rr - (R + 3.0), (R - 13.0) - rr), np.maximum(v[:, 0], -v[:, 1]))
        along_x = np.maximum.reduce([np.abs(v[:, 1]) - 3.0, v[:, 0] - 3.0, -v[:, 0] - (R + 3.0)])
        along_y = np.maximum.reduce([np.abs(v[:, 0]) - 3.0, -v[:, 1] - 3.0, v[:, 1] - (R + 3.0)])
        shape = np.minimum(ring, np.minimum(along_x, along_y))
        d, mat = np.maximum(shape, np.abs(v[:, 2]) - 1.4) - 0.4, np.full(len(q), ACRYLIC)
        return _put(d, mat, sdf.torus_y((v - [0, 0, 1.6]) @ sdf.rot_x(np.pi / 2), 2.2, 0.7), GOLD)
    return _faceon(f, S, S)


def tube():
    """A test tube: rim lip, rounded bottom. Drawn over its Phaser liquid at 55% alpha. 16 x 58."""
    def f(q):
        shell = np.maximum(sdf.capsule(q, (0, -21.0, 0), (0, 30.0, 0), 6.6), -sdf.capsule(q, (0, -21.0, 0), (0, 34.0, 0), 5.4))
        shell = np.maximum(shell, q[:, 1] - 26.0)
        lip = sdf.torus_y(q - [0, 26.0, 0], 6.8, 1.1)
        return np.minimum(shell, lip), GLASS
    return _faceon(f, 16, 58)


def dropper():
    """A glass pipette with a red rubber bulb, tip at the bottom. 12 x 40."""
    def f(q):
        glass = sdf.round_cone(q, (0, -17.0, 0), (0, 6.0, 0), 0.8, 2.6)
        bulb = sdf.capsule(q, (0, 10.0, 0), (0, 15.0, 0), 4.2)
        collar = sdf.cylinder_y(q - [0, 7.0, 0], 3.4, 1.2, 0.5)
        d, mat = glass, np.full(len(q), GLASS)
        d, mat = _put(d, mat, bulb, RED)
        return _put(d, mat, collar, RED)
    return _faceon(f, 12, 40)


def cylinder():
    """Case 1's measuring cylinder: glass walls, a foot and a spout. Image at game (176, 52), 60 x 192."""
    W, H = 60, 192

    def f(q):
        # walls: inner width 46 (game x 183..229), top at game y 64, bottom at 236
        outer = sdf.box(q - [0, 4.0, 0], (25.0, 84.0, 6.0), 4.0)
        inner = sdf.box(q - [0, 12.0, 2.0], (23.0, 84.0, 4.0), 2.0)
        walls = np.maximum(outer, -inner)
        foot = sdf.box(q - [0, -84.0, -1.0], (29.0, 3.0, 6.0), 2.0)
        spout = sdf.capsule(q, (21.0, 86.0, 1.0), (28.0, 89.0, 1.0), 1.6)
        d, mat = walls, np.full(len(q), GLASS)
        d, mat = _put(d, mat, foot, NAVY)
        return _put(d, mat, spout, GLASS)
    return _faceon(f, W, H)


# ------------------------------------------------------------------ bench props

def balance():
    """A top-loading lab balance: enamel body, steel pan, LCD on the front, two buttons, a level bubble."""
    def f(p):
        body = sdf.box(p - [0, 9.5, 0], (58.0, 9.5, 28.0), 4.0)
        d, mat = body, np.full(len(p), BODY)
        stripe = (p[:, 1] < 4.2) & (p[:, 1] > 1.6)
        mat = np.where(stripe & (mat == BODY), NAVY, mat)
        lcd = sdf.box(p - [-6.0, 9.5, 28.0], (24.0, 5.6, 0.8), 1.0)
        bezel = sdf.box(p - [-6.0, 9.5, 27.6], (26.5, 7.6, 0.8), 1.6)
        d, mat = _put(d, mat, bezel, PHONE)
        d, mat = _put(d, mat, lcd, LCD)
        for x, m in ((32.0, RED), (44.0, BLUE)):
            d, mat = _put(d, mat, sdf.cylinder_y((p - [x, 9.5, 28.0]) @ sdf.rot_x(np.pi / 2), 3.6, 1.6, 0.9), m)
        post = sdf.cylinder_y(p - [0, 20.0, 0], 4.0, 2.0, 0.5)
        pan = sdf.cylinder_y(p - [0, 23.0, 0], 32.0, 1.0, 0.8)
        lip = sdf.torus_y(p - [0, 24.0, 0], 31.2, 1.0)
        d, mat = _put(d, mat, post, METAL)
        d, mat = _put(d, mat, np.minimum(pan, lip), METAL)
        bubble = sdf.ellipsoid(p, (-48.0, 19.0, 20.0), (3.6, 1.6, 3.6))
        d, mat = _put(d, mat, bubble, GLASS)
        for x in (-52.0, 52.0):
            for z in (-22.0, 22.0):
                d, mat = _put(d, mat, sdf.cylinder_y(p - [x, 0.0, z], 3.0, 1.2, 0.4), RUBBER)
        return d, mat
    return _bench([Obj(f, (-64, -2, -34), (64, 28, 34), "balance")], 132, 58, (0.0, 13.0))


def crate():
    """A wooden sample crate with corner battens and a paper label on the front."""
    def f(p):
        box = sdf.box(p - [0, 12.0, 0], (17.0, 12.0, 12.0), 1.0)
        d, mat = box, np.full(len(p), WOOD)
        groove = (np.abs(((p[:, 1] + 100) % 6.0) - 3.0) > 2.55) & (np.abs(p[:, 1] - 12.0) < 11.0)
        mat = np.where(groove, WOOD_DARK, mat)
        for sx in (-1, 1):
            for sz in (-1, 1):
                bat = sdf.box(p - [sx * 16.0, 12.0, sz * 11.0], (1.8, 12.2, 1.8), 0.5)
                d, mat = _put(d, mat, bat, WOOD_DARK)
        label = sdf.box(p - [0, 12.0, 12.2], (12.5, 6.0, 0.4), 0.4)
        d, mat = _put(d, mat, label, PAPER)
        for x in (-11.0, 11.0):
            d, mat = _put(d, mat, sdf.sphere(p, (x, 16.8, 12.6), 0.8), METAL)
        return d, mat
    return _bench([Obj(f, (-20, -1, -15), (20, 26, 15), "crate")], 40, 38, (0.0, 9.0))


def tub():
    """A little wooden tub of water, for weighing water on the balance."""
    def f(p):
        shell = np.maximum(sdf.cylinder_y(p - [0, 8.0, 0], 13.0 - 0.12 * (p[:, 1] - 8.0), 8.0, 1.0), -sdf.cylinder_y(p - [0, 11.0, 0], 11.4, 8.0, 0.4))
        staves = np.abs(((np.arctan2(p[:, 2], p[:, 0]) * 12 / np.pi) % 1.0) - 0.5) > 0.42
        hoops = np.abs(np.abs(p[:, 1] - 8.0) - 4.6) < 0.8
        d, mat = shell, np.where(hoops, METAL, np.where(staves, WOOD_DARK, WOOD))
        water = sdf.cylinder_y(p - [0, 13.0, 0], 11.6, 0.4, 0.2)
        return _put(d, mat, water, BLUE)
    return _bench([Obj(f, (-15, -1, -15), (15, 18, 15), "tub")], 40, 34, (0.0, 7.0))


def ingot():
    """A plain grey metal block, scuffed, for weighing on the balance."""
    def f(p):
        d = sdf.box(p - [0, 7.0, 0], (12.0, 7.0, 8.0), 1.2)
        scuff = np.sin(p[:, 0] * 1.7 + p[:, 2] * 0.9) * np.sin(p[:, 1] * 2.1) > 0.75
        return d, np.where(scuff, BODY, METAL)
    return _bench([Obj(f, (-14, -1, -10), (14, 16, 10), "ingot")], 36, 30, (0.0, 6.0))


PIPS = {1: [(0, 0)], 2: [(-1, 1), (1, -1)], 3: [(-1, 1), (0, 0), (1, -1)], 4: [(-1, 1), (1, 1), (-1, -1), (1, -1)],
        5: [(-1, 1), (1, 1), (0, 0), (-1, -1), (1, -1)], 6: [(-1, 1), (1, 1), (-1, 0), (1, 0), (-1, -1), (1, -1)]}


def die(v):
    """An ivory die showing v on its front face, with the top and right faces in view."""
    top, right = {1: (2, 3), 2: (3, 1), 3: (1, 2), 4: (1, 5), 5: (1, 3), 6: (2, 4)}[v]
    rot = sdf.rot_y(0.42)

    def f(p):
        q = (p - [0, 11.0, 0]) @ rot
        d, mat = sdf.box(q, (10.0, 10.0, 10.0), 2.6), np.full(len(p), IVORY)
        pips = np.full(len(p), 1e9)
        for n, (ax, sgn) in ((v, (2, 1)), (top, (1, 1)), (right, (0, 1))):
            for a, b in PIPS[n]:
                c = np.zeros(3)
                c[ax] = 10.3 * sgn
                u, w = [i for i in range(3) if i != ax]
                c[u], c[w] = a * 5.0, b * 5.0
                pips = np.minimum(pips, sdf.sphere(q, c, 2.1))
        d = np.maximum(d, -pips)
        mat = np.where(pips < 0.5, INKDOT, mat)
        return d, mat
    return _bench([Obj(f, (-16, -1, -16), (16, 26, 16), "die")], 36, 38, (0.0, 9.0))


def weights():
    """A wooden case of brass calibration weights with a pair of tweezers."""
    def f(p):
        case = sdf.box(p - [0, 3.0, 0], (30.0, 3.0, 14.0), 1.5)
        d, mat = case, np.full(len(p), WOOD)
        for x, r, h in ((-20.0, 5.6, 9.0), (-8.0, 4.6, 7.4), (2.0, 3.8, 6.0), (10.0, 3.0, 4.8), (17.0, 2.4, 3.8), (23.0, 2.0, 3.0)):
            body = sdf.cylinder_y(p - [x, 6.0 + h / 2, 0], r, h / 2, 0.6)
            neck = sdf.cylinder_y(p - [x, 6.0 + h + 0.8, 0], r * 0.45, 0.8, 0.3)
            knob = sdf.sphere(p, (x, 6.0 + h + 2.2, 0), r * 0.55)
            d, mat = _put(d, mat, np.minimum(np.minimum(body, neck), knob), GOLD)
        tw = sdf.capsule(p, (-24.0, 6.6, 9.0), (20.0, 6.6, 11.0), 0.7)
        return _put(d, mat, tw, METAL)
    return _bench([Obj(f, (-32, -1, -16), (32, 24, 16), "weights")], 70, 34, (0.0, 6.0))


def crown2x():
    """Case 1's crown at twice the old size, so the lab can draw it at 1:1."""
    def f(p):
        p = p / 2.0
        band = np.maximum(np.abs(np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2) - 9.0) - 1.4, np.abs(p[:, 1] - 4.0) - 4.0)
        ang = np.arctan2(p[:, 2], p[:, 0])
        spike_h = 8.0 + 6.0 * np.clip(np.cos(ang * 5.0), 0, 1) ** 3
        spikes = np.maximum(np.abs(np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2) - 9.0) - 1.1, np.maximum(p[:, 1] - spike_h, 7.0 - p[:, 1]))
        d, mat = np.minimum(band, spikes), np.full(len(p), GOLD)
        rims = np.maximum(np.abs(np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2) - 9.0) - 1.7, np.minimum(np.abs(p[:, 1] - 0.6), np.abs(p[:, 1] - 7.6)) - 0.6)
        d, mat = _put(d, mat, rims, GOLD)
        for k in range(5):
            a = k * 2 * np.pi / 5
            d, mat = _put(d, mat, sdf.sphere(p, (10.4 * np.cos(a), 4.0, 10.4 * np.sin(a)), 1.7), GEMR)
            d, mat = _put(d, mat, sdf.sphere(p, (9.0 * np.cos(a), 14.6, 9.0 * np.sin(a)), 1.6), GOLD)
            b = a + np.pi / 5
            d, mat = _put(d, mat, sdf.sphere(p, (10.6 * np.cos(b), 4.0, 10.6 * np.sin(b)), 0.9), BLUE)
        return d * 2.0, mat
    return _bench([Obj(f, (-30, -2, -30), (30, 36, 30), "crown")], 80, 72, (0.0, 12.0))


PROPS = {
    "phone": phone, "dial": dial, "hub": hub, "knob": knob, "thermo": thermo,
    "protractor46": lambda: protractor(46),
    "tube": tube, "dropper": dropper, "cylinder": cylinder,
    "balance": balance, "crate": crate, "tub": tub, "ingot": ingot, "crown": crown2x,
    **{f"die{v}": (lambda v=v: die(v)) for v in range(1, 7)},
}


def build(which="balance"):
    s = PROPS[which]()
    lights = [Light((-200, 260, 220), "#FFC46B", 0.7, 900), Light((240, 120, 160), "#6F8FD8", 0.3, 600, shadow=False)]
    return dict(world=World(s["objs"]), materials=MATERIALS, width=s["width"], height=s["height"], centre=s["centre"],
                lights=lights, key=0.5, ambient=0.1, top=s["top"], ss=2, steps=160)
