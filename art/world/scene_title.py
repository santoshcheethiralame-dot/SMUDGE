"""Title backdrop: a desk at night, a lamp, and an open textbook with a pop-up
city of living diagrams. 480x270, same camera as the sprites."""
import numpy as np

from envrender import Obj, World, Light
from src import sdf

(WALL, WALL_STRIPE, DESK, PAGE, PAGE_LINE, PAGE_MARGIN, COVER, PAGE_EDGE,
 CARD_MINT, CARD_PINK, CARD_YELLOW, CARD_SKY, GLASS, WATER, METAL, BRASS, BULB, WINDOW,
 INK, CORK, NOTE_Y, NOTE_P, NOTE_B, PIN, PEN_BODY, GOLD, RED, PRINT, CYAN_GLOW, FRAME, INK_GLASS) = range(1, 32)


def _hash(p):
    return np.modf(np.sin(p[:, 0] * 12.9898 + p[:, 1] * 78.233 + p[:, 2] * 37.719) * 43758.5453)[0] % 1.0


def _wood(p, n):
    g = np.sin(p[:, 0] * 0.09 + 2.2 * np.sin(p[:, 2] * 0.045) + 0.6 * np.sin(p[:, 0] * 0.31))
    return 0.55 * g + 0.25 * (_hash(np.floor(p / 3.0)) - 0.5)


def _speckle(p, n):
    return (_hash(np.floor(p * 0.9)) > 0.72) * 0.9 - 0.2


def _paper(p, n):
    return 0.25 * (_hash(np.floor(p * 0.7)) - 0.5)


MATERIALS = {
    WALL: dict(ramp=["#07091A", "#0C1028", "#121836", "#1A2246", "#232E58", "#2E3B6C"],
               sub=(lambda p: (np.floor((p[:, 0] + 400) / 13) % 2) == 0, WALL_STRIPE), dither=0.3),
    WALL_STRIPE: dict(ramp=["#080B1E", "#0E132E", "#151C3D", "#1E274F", "#283462", "#334376"], dither=0.3),
    DESK: dict(ramp=["#1A0F07", "#2E1A0D", "#462814", "#61381C", "#7E4A25", "#9C5E30", "#BC7840"],
               pattern=_wood, pattern_gain=0.16, warm_tint=0.35),
    PAGE: dict(ramp=["#6E6450", "#968970", "#BBAD8C", "#D7CAA6", "#EADFC0", "#F7EED7", "#FFF9EA"],
               pattern=_paper, pattern_gain=0.1,
               sub=(lambda p: (np.abs(((p[:, 2] + 300) % 9.0) - 4.5) > 3.9) & (p[:, 1] > 2.5), PAGE_LINE),
               warm_tint=0.3),
    PAGE_LINE: dict(ramp=["#4B6E9C", "#6B90BF", "#89ACD8", "#A5C4EA", "#BCD6F4", "#CFE3FA"], warm_tint=0.2),
    PAGE_MARGIN: dict(ramp=["#8E3B3B", "#B25555", "#CF7373", "#E39393", "#F0AFAF", "#F8C8C8"]),
    COVER: dict(ramp=["#1E0504", "#3A0C09", "#5A140F", "#7D1E16", "#A02A1F", "#C23A2B"], gloss=30, spec="#F2A08C"),
    PAGE_EDGE: dict(ramp=["#5E5442", "#857860", "#A99A7C", "#C7B998", "#DCCFAE", "#ECE1C2"],
                    pattern=lambda p, n: 0.5 * np.sign(np.sin(p[:, 1] * 3.3)), pattern_gain=0.12),
    CARD_MINT: dict(ramp=["#183B30", "#245644", "#33725A", "#4A9073", "#69AE8F", "#8FCCAD", "#B7E6CC"], pattern=_paper),
    CARD_PINK: dict(ramp=["#4A1B2C", "#6B2840", "#8E3A57", "#B35172", "#D16F90", "#E893AE", "#F7BCCF"], pattern=_paper),
    CARD_YELLOW: dict(ramp=["#4C3510", "#6E4D17", "#93681F", "#B9872B", "#D9A73F", "#EDC461", "#FAE08E"], pattern=_paper),
    CARD_SKY: dict(ramp=["#16304E", "#204569", "#2D5D88", "#3F78A7", "#5795C4", "#76B2DC", "#9DCDEE"], pattern=_paper),
    GLASS: dict(ramp=["#1C3550", "#29506F", "#3A6C8F", "#5089AD", "#6DA6C8", "#93C3DF", "#C2E1F3"], gloss=40, spec="#FFFFFF"),
    WATER: dict(ramp=["#0D2340", "#143259", "#1D4473", "#29588E", "#386EA8", "#4C86C0"], gloss=30, spec="#DDF1FF"),
    METAL: dict(ramp=["#0A0C10", "#15191F", "#222831", "#323A46", "#47515F", "#626E7F"], gloss=24, spec="#C8D4E2"),
    BRASS: dict(ramp=["#2E2008", "#4D360E", "#725116", "#9A6F21", "#C29233", "#E2B652"], gloss=28, spec="#FFF2C2"),
    BULB: dict(ramp=["#FFE9A8", "#FFF6D6", "#FFFFFF"], emissive=True),
    WINDOW: dict(ramp=["#F2B44C", "#FFD27A", "#FFE9B0"], emissive=True,
                 pattern=lambda p, n: (_hash(np.floor(p * 0.5)) > 0.5).astype(float)),
    INK: dict(ramp=["#02030C", "#060A1C", "#0D1631", "#16264B", "#22396B", "#33508C"], gloss=14, spec="#BFD6FF"),
    INK_GLASS: dict(ramp=["#04060F", "#0A1024", "#121D3C", "#1C2D57", "#2A4277", "#3E5C9C"], gloss=30, spec="#DDE8FF"),
    CORK: dict(ramp=["#3A2614", "#55391E", "#73502B", "#946B3B", "#B2874E", "#C9A066"], pattern=_speckle, pattern_gain=0.2),
    NOTE_Y: dict(ramp=["#6B5A1C", "#93802A", "#B9A33B", "#D8C352", "#EDDB72", "#F8EC98"]),
    NOTE_P: dict(ramp=["#6A2D3E", "#8F4058", "#B45874", "#D17594", "#E696B0", "#F4B8CB"]),
    NOTE_B: dict(ramp=["#25486A", "#33638E", "#4580B0", "#5E9DCC", "#7DB8E2", "#A2D0F0"]),
    PIN: dict(ramp=["#4A0A08", "#8E1A14", "#C9302A", "#EE5A4C"], gloss=20, spec="#FFD0C6"),
    PEN_BODY: dict(ramp=["#030305", "#09090D", "#121219", "#1D1D27", "#2C2C3A"], gloss=50, spec="#B9C3D6"),
    GOLD: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848", "#FFE08A"], gloss=30, spec="#FFFBE6"),
    RED: dict(ramp=["#3A0907", "#62110D", "#8E1A14", "#B8251C", "#DE3B2E", "#F26654"], gloss=20, spec="#FFD0C6"),
    PRINT: dict(ramp=["#0A0D18", "#141A2C", "#1F2740", "#2A3554"]),
    CYAN_GLOW: dict(ramp=["#7DF9FF", "#C8FDFF", "#FFFFFF"], emissive=True),
    FRAME: dict(ramp=["#140B05", "#24140A", "#3A2112", "#523019", "#6B4022"]),
}

W, H = 480, 270
CENTRE = (0.0, 100.0)


def _page_block(sign):
    """One half of the open book: pages bulge up near the middle of each half."""
    x0, x1 = (2.0, 158.0) if sign > 0 else (-158.0, -2.0)
    zc, zh = 15.0, 40.0

    def f(p):
        s = np.clip((sign * p[:, 0] - 2.0) / 156.0, 0, 1)
        top = 3.4 + 5.2 * np.sqrt(s) * (1 - 0.75 * s)
        d_top = (p[:, 1] - top) * 0.8
        d_x = np.maximum(x0 - p[:, 0], p[:, 0] - x1)
        d_z = np.abs(p[:, 2] - zc) - zh
        d = np.maximum.reduce([d_top, d_x, d_z, 0.2 - p[:, 1]])
        side = np.maximum(d_x, d_z) > d_top - 0.05
        mat = np.where(side, PAGE_EDGE, PAGE)
        # margin rules near the outer edge of each page
        mx = sign * p[:, 0]
        mat = np.where(~side & (np.abs(mx - 142.0) < 0.9), PAGE_MARGIN, mat)
        return d, mat
    return Obj(f, (x0 - 1, 0, zc - zh - 1), (x1 + 1, 10, zc + zh + 1), "pages")


def build():
    objs = []
    objs.append(Obj(lambda p: (sdf.box(p - [0, -10, 25], (420, 10, 75)), DESK), (-420, -20, -50), (420, 0.1, 100), "desk"))
    objs.append(Obj(lambda p: (sdf.box(p - [0, 160, -56], (420, 200, 6)), WALL), (-420, -40, -62), (420, 360, -50), "wall"))
    # skirting board where wall meets desk
    objs.append(Obj(lambda p: (sdf.box(p - [0, 3, -49], (420, 3, 1.5), 0.5), FRAME), (-420, 0, -51), (420, 6, -47), "skirting"))

    # the book
    objs.append(Obj(lambda p: (sdf.box(p - [0, 1.4, 15], (166, 1.4, 43.5), 0.8), COVER), (-167, 0, -29), (167, 3, 59), "cover"))
    objs.append(_page_block(1))
    objs.append(_page_block(-1))

    # --- pop-up city ---
    # measuring-cylinder lighthouse
    def lighthouse(p):
        q = p - [-118, 50, 18]
        body = sdf.cylinder_y(q, 11.0, 45.0, 1.0)
        mat = np.where(p[:, 1] < 44, WATER, GLASS)
        marks = (np.abs(((p[:, 1] + 100) % 10.0) - 5.0) > 4.3) & (p[:, 0] < -118) & (p[:, 2] > 18) & (p[:, 1] > 12) & (p[:, 1] < 90)
        mat = np.where(marks, PRINT, mat)
        lamp = sdf.cylinder_y(p - [-118, 101, 18], 8.5, 5.5, 0.5)
        cage = sdf.cylinder_y(p - [-118, 101, 18], 9.5, 6.5, 0.5)
        cage = np.maximum(cage, -sdf.box(p - [-118, 101, 18], (20, 4.5, 3.2)))
        cage = np.maximum(cage, -sdf.box(p - [-118, 101, 18], (3.2, 4.5, 20)))
        base = sdf.cylinder_y(p - [-118, 95, 18], 13.0, 1.4, 0.6)
        rq = p - [-118, 107.5, 18]
        roof = np.maximum(np.sqrt(rq[:, 0] ** 2 + rq[:, 2] ** 2) - (12.5 - 0.85 * rq[:, 1]), np.maximum(-rq[:, 1], rq[:, 1] - 15.0))
        roof = roof * 0.75
        d = body
        for dd, mm in ((lamp, WINDOW), (cage, METAL), (base, METAL), (roof, RED)):
            mat = np.where(dd < d, mm, mat)
            d = np.minimum(d, dd)
        return d, mat
    objs.append(Obj(lighthouse, (-132, 4, 4), (-104, 124, 32), "lighthouse"))

    # prism tower (equilateral triangular prism)
    def prism(p):
        q = p - [-58, 36, 24]
        h = (62.0, 10.0)
        qa = np.abs(q)
        d = np.maximum(qa[:, 2] - h[1], np.maximum(qa[:, 0] * 0.866025 + q[:, 1] * 0.5, -q[:, 1]) - h[0] * 0.5)
        win = sdf.box(p - [-58, 38, 34.3], (5, 8, 0.8), 0.6)
        mat = np.where(win < d, WINDOW, CARD_PINK)
        return np.minimum(d, win), mat
    objs.append(Obj(prism, (-95, 4, 13), (-21, 100, 36), "prism"))

    # resistor house
    def resistor(p):
        body = sdf.box(p - [32, 44, 22], (24, 39, 15), 1.5)
        d, mat = body, np.full(len(p), CARD_YELLOW)
        for y, m in ((70, RED), (58, PRINT), (46, RED), (34, GOLD)):
            band = np.maximum(sdf.box(p - [32, y, 22], (24.8, 3.2, 15.8), 1.5), body - 0.8)
            mat = np.where(band < d, m, mat)
            d = np.minimum(d, band)
        for wx in (22, 42):
            for wy in (18,):
                win = sdf.box(p - [wx, wy, 37.3], (4, 5.5, 0.8), 0.5)
                mat = np.where(win < d, WINDOW, mat)
                d = np.minimum(d, win)
        door = sdf.box(p - [32, 11, 37.3], (4.5, 7, 0.8), 0.5)
        mat = np.where(door < d, FRAME, mat)
        d = np.minimum(d, door)
        ant = sdf.capsule(p, (40, 83, 22), (40, 98, 22), 0.9)
        tip = sdf.sphere(p, (40, 100, 22), 2.6)
        mat = np.where(ant < d, METAL, mat)
        d = np.minimum(d, ant)
        mat = np.where(tip < d, CYAN_GLOW, mat)
        return np.minimum(d, tip), mat
    objs.append(Obj(resistor, (6, 4, 5), (58, 104, 39), "resistor"))

    # clock tower
    def clock(p):
        body = sdf.box(p - [108, 46, 20], (19, 41, 15), 1.5)
        dome = sdf.ellipsoid(p, (108, 88, 20), (17, 13, 13))
        dome = np.maximum(dome, 87 - p[:, 1])
        d = np.minimum(body, dome)
        mat = np.where(dome <= body, CARD_SKY, CARD_MINT)
        face = sdf.cylinder_y((p - [108, 64, 35.4]) @ sdf.rot_x(np.pi / 2), 11.5, 0.7, 0.5)
        mat = np.where(face < d, PAGE, mat)
        d = np.minimum(d, face)
        hands = np.minimum(sdf.capsule(p, (108, 64, 36.4), (108, 72, 36.4), 0.9),
                           sdf.capsule(p, (108, 64, 36.4), (113.5, 61, 36.4), 0.9))
        mat = np.where(hands < d, PRINT, mat)
        d = np.minimum(d, hands)
        for wx in (100, 116):
            for wy in (22, 40):
                win = sdf.box(p - [wx, wy, 35.3], (3.6, 5.0, 0.8), 0.5)
                mat = np.where(win < d, WINDOW, mat)
                d = np.minimum(d, win)
        flag = sdf.capsule(p, (108, 100, 20), (108, 112, 20), 0.7)
        cloth = sdf.box(p - [113, 109, 20], (5, 3, 0.5), 0.3)
        mat = np.where(flag < d, METAL, mat)
        d = np.minimum(d, flag)
        mat = np.where(cloth < d, RED, mat)
        return np.minimum(d, cloth), mat
    objs.append(Obj(clock, (88, 4, 4), (126, 114, 37), "clock"))

    # little paper boat on the right page
    def boat(p):
        q = p - [148, 9, 42]
        hull = sdf.box(q, (12, 4.5, 5), 0.6)
        hull = np.maximum(hull, (np.abs(q[:, 0]) - 12 + (q[:, 1] + 4.5) * 0.9))
        sail = np.maximum(sdf.box(q - [0, 10, 0], (0.5, 8, 6), 0.2), np.abs(q[:, 0]) * 1.3 + q[:, 1] - 16)
        d = np.minimum(hull, sail)
        return d, np.where(sail < hull, PAGE, CARD_SKY)
    objs.append(Obj(boat, (134, 4, 35), (162, 28, 49), "boat"))

    # --- desk lamp on the left ---
    def lamp(p):
        base = sdf.cylinder_y(p - [-210, 2.2, 12], 22, 2.2, 1.5)
        neck = sdf.cylinder_y(p - [-210, 6, 12], 5, 3, 1)
        arm1 = sdf.capsule(p, (-210, 6, 12), (-206, 122, 2), 2.6)
        joint = sdf.sphere(p, (-206, 122, 2), 4.5)
        arm2 = sdf.capsule(p, (-206, 122, 2), (-176, 168, 8), 2.4)
        hq = p - [-160, 150, 8]
        axis = np.array([0.62, -0.55, 0.56])
        axis /= np.linalg.norm(axis)
        shade_ = sdf.round_cone(p, (-176, 168, 8), (-176, 168, 8) + axis * 26, 7.0, 21.0)
        inner = sdf.round_cone(p, (-176, 168, 8) + axis * 3, (-176, 168, 8) + axis * 30, 5.5, 20.0)
        shade_ = np.maximum(shade_, -inner)
        d = base
        mat = np.full(len(p), METAL)
        for dd, mm in ((neck, BRASS), (arm1, METAL), (joint, BRASS), (arm2, METAL), (shade_, METAL)):
            mat = np.where(dd < d, mm, mat)
            d = np.minimum(d, dd)
        bulb = sdf.sphere(p, (-176, 168, 8) + axis * 20, 9.0)
        mat = np.where(bulb < d, BULB, mat)
        return np.minimum(d, bulb), mat
    objs.append(Obj(lamp, (-236, 0, -15), (-120, 175, 40), "lamp"))

    # --- tipped ink bottle and spill on the right ---
    def bottle(p):
        q = (p - [188, 12, 58]) @ sdf.rot_z(np.pi / 2) @ sdf.rot_x(0.35)
        body = sdf.cylinder_y(q, 12.0, 15.0, 3.0)
        neck = sdf.cylinder_y(q - [0, -18, 0], 5.5, 4.0, 1.0)
        d = np.minimum(body, neck)
        mat = np.where(body < neck, INK_GLASS, METAL)
        spill = sdf.ellipsoid(p, (150, 0.0, 66), (42, 1.6, 16))
        spill2 = sdf.ellipsoid(p, (118, 0.0, 74), (14, 1.2, 7))
        sp = sdf.smin(spill, spill2, 6.0)
        mat = np.where(sp < d, INK, mat)
        return np.minimum(d, sp), mat
    objs.append(Obj(bottle, (100, -2, 40), (210, 30, 90), "bottle"))

    # --- fountain pen across the front ---
    def pen(p):
        a, b = np.array([20.0, 3.2, 92.0]), np.array([210.0, 3.2, 80.0])
        body = sdf.capsule(p, a + (b - a) * 0.12, b, 3.2)
        band = np.maximum(sdf.capsule(p, a + (b - a) * 0.12, b, 3.6),
                          np.abs(((p - a) @ ((b - a) / np.linalg.norm(b - a))) - 70) - 3.0)
        nib = sdf.round_cone(p, a + (b - a) * 0.12, a, 2.9, 0.4)
        clip = sdf.capsule(p, a + (b - a) * 0.72 + [0, 3.4, 0], a + (b - a) * 0.95 + [0, 3.4, 0], 0.8)
        d = body
        mat = np.full(len(p), PEN_BODY)
        for dd, mm in ((band, GOLD), (nib, GOLD), (clip, GOLD)):
            mat = np.where(dd < d, mm, mat)
            d = np.minimum(d, dd)
        return d, mat
    objs.append(Obj(pen, (15, 0, 74), (215, 8, 98), "pen"))

    # --- corkboard with notes on the wall ---
    def board(p):
        frame = sdf.box(p - [178, 176, -49], (64, 42, 2.5), 0.8)
        cork = sdf.box(p - [178, 176, -47.4], (59, 37, 1.5), 0.3)
        d = frame
        mat = np.full(len(p), FRAME)
        mat = np.where(cork < d, CORK, mat)
        d = np.minimum(d, cork)
        notes = [((150, 192), 0.12, NOTE_Y), ((196, 196), -0.08, NOTE_P), ((172, 160), 0.05, NOTE_B), ((214, 160), -0.15, NOTE_Y)]
        for (x, y), ang, m in notes:
            n_ = sdf.box((p - [x, y, -45.6]) @ sdf.rot_z(ang), (13, 11, 0.4), 0.2)
            mat = np.where(n_ < d, m, mat)
            d = np.minimum(d, n_)
            pin = sdf.sphere(p, (x, y + 8, -44.4), 2.0)
            mat = np.where(pin < d, PIN, mat)
            d = np.minimum(d, pin)
        string = np.minimum(sdf.capsule(p, (150, 200, -44.6), (196, 204, -44.6), 0.55),
                            sdf.capsule(p, (196, 204, -44.6), (172, 168, -44.6), 0.55))
        mat = np.where(string < d, RED, mat)
        return np.minimum(d, string), mat
    objs.append(Obj(board, (112, 132, -52), (244, 220, -42), "board"))

    lights = [Light((-150, 140, 32), "#FFC46B", 2.3, 360, ignore=("lamp",)),
              Light((40, 101, 24), "#7DF9FF", 0.5, 45, shadow=False),
              Light((-118, 101, 30), "#FFD27A", 0.5, 60, shadow=False)]
    return dict(world=World(objs), materials=MATERIALS, width=W, height=H, centre=CENTRE,
                lights=lights, key=0.16, ambient=0.05, top=240.0, ss=2, steps=160,
                bloom=[(BULB, "#FFD98A", 34, 0.75), (WINDOW, "#FFC861", 10, 0.55), (CYAN_GLOW, "#7DF9FF", 12, 0.6)])
