"""Buoyant Bay: a harbour on Chapter 9, festival day. A pier runs across the
screen; behind it the bay, the lighthouse, Karat's shop, the festival stage
(the crime scene) and Bob's mooring. 720x270, scrolls horizontally.

build(flooded=True)  the density law is gone: the bay has risen to the deck
build(flooded=False) after the case: water back where it belongs
Walkable deck: y = 0, x in [-340, 340], z in [10, 24].
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light, gradient_sky, stars, moon
from src import sdf

(DECK, DECK_GAP, POST, WATER, WATER_LINE, ROCK, GLASS, GLASSWATER, METAL, RED, WINDOW, SHOP, SHOP_TRIM,
 SIGN, SIGN_INK, CURTAIN, STAGE, CUSHION, GOLD, FLAG_R, FLAG_Y, FLAG_B, ROPE, PAGE_WALL, PRINT, BOATP,
 TOWN, ROOF, HULL, SAIL) = range(1, 31)

W, H = 720, 270
CENTRE = (0.0, 90.0)
HOTSPOTS = {"cyl": -228, "karat": -92, "stage": 60, "bob": 214, "exit": -330}
LAMPS = (-180.0, -20.0, 140.0, 300.0)
FS = 1.8                       # scale of the floating barrels, buoy and anvil


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _decal(text, font, w, h):
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    b = d.textbbox((0, 0), text, font=font)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=font, fill=255)
    return np.array(im) > 100


SIGN_TEX = _decal("GEMS", _font("arialbd.ttf", 30), 120, 40)
BANNER_TEX = _decal("FESTIVAL", _font("arialbd.ttf", 30), 200, 40)
LAW_TEX = {True: _decal("DENSITY   =   ?  ?  ?", _font("georgiab.ttf", 34), 600, 44),
           False: _decal("DENSITY   ρ  =  m / V", _font("georgiab.ttf", 34), 600, 44)}


def _wood(p, n):
    g = np.sin(p[:, 0] * 0.4 + 2.0 * np.sin(p[:, 2] * 0.15))
    return 0.45 * g


def materials(flooded):
    return {
        DECK: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E", "#CF8A42", "#E2A45C"],
                   pattern=_wood, pattern_gain=0.14, warm_tint=0.4,
                   sub=(lambda p: (np.abs(((p[:, 2] + 300) % 7.0) - 3.5) > 3.05) & (p[:, 1] > -0.5), DECK_GAP)),
        DECK_GAP: dict(ramp=["#120903", "#1E1006", "#2A1608", "#3A1F0C"]),
        POST: dict(ramp=["#1E1006", "#2E1A0D", "#462814", "#61381C", "#7E4A25"],
                   pattern=lambda p, n: -0.9 * (p[:, 1] < (-2 if flooded else -12)), pattern_gain=0.2),
        WATER: dict(ramp=["#081A33", "#0D2648", "#143561", "#1C477E", "#285C9C", "#3873B6", "#4F8DCB"],
                    gloss=26, spec="#DDF0FF", dither=0.35,
                    pattern=lambda p, n: 0.7 * np.sin(p[:, 0] * 0.09 + np.sin(p[:, 2] * 0.12) * 2.0), pattern_gain=0.12,
                    sub=(lambda p: np.abs(((p[:, 2] + 300) % 13.0) - 6.5) > 6.0, WATER_LINE)),
        WATER_LINE: dict(ramp=["#3B5E8E", "#557AA9", "#6E95C2", "#88AFD9", "#A3C7EA"], gloss=20, spec="#FFFFFF"),
        ROCK: dict(ramp=["#1C1C24", "#2C2C38", "#40404F", "#575769", "#707086"],
                   pattern=lambda p, n: 0.5 * (np.abs(np.sin(p[:, 0] * 1.3) * np.sin(p[:, 1] * 1.1)) - 0.5), pattern_gain=0.2),
        GLASS: dict(ramp=["#1C3D63", "#2F6496", "#4F8FC6", "#86BDE6", "#C2E1F3"], gloss=40, spec="#FFFFFF"),
        GLASSWATER: dict(ramp=["#0F2E5C", "#1B4885", "#2C66AE", "#4A8AD0", "#7DB2EA"], gloss=30, spec="#E6F4FF"),
        METAL: dict(ramp=["#0A0C10", "#15191F", "#222831", "#323A46", "#47515F", "#626E7F"], gloss=24, spec="#C8D4E2"),
        RED: dict(ramp=["#3A0907", "#62110D", "#8E1A14", "#B8251C", "#DE3B2E", "#F26654"]),
        WINDOW: dict(ramp=["#F2B44C", "#FFD27A", "#FFE9B0"], emissive=True),
        SHOP: dict(ramp=["#16304E", "#204569", "#2D5D88", "#3F78A7", "#5795C4", "#76B2DC", "#9DCDEE"]),
        SHOP_TRIM: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848"], gloss=24, spec="#FFFBE6"),
        SIGN: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF"]),
        SIGN_INK: dict(ramp=["#07090F", "#0E121D", "#161C2C", "#20283C"]),
        CURTAIN: dict(ramp=["#2A0507", "#4A0A0E", "#6E1218", "#931D24", "#B52B31", "#D1453F"],
                      pattern=lambda p, n: 0.8 * np.sin(p[:, 0] * 0.9), pattern_gain=0.22),
        STAGE: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E", "#CF8A42"], pattern=_wood, pattern_gain=0.1),
        CUSHION: dict(ramp=["#2B0F3D", "#43195C", "#5E257D", "#7C369F", "#9B4FC0", "#B871DC"]),
        GOLD: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848", "#FFE08A"], gloss=22, spec="#FFFFFF"),
        FLAG_R: dict(ramp=["#5E100C", "#8E1A14", "#C9302A", "#EE5A4C"]),
        FLAG_Y: dict(ramp=["#6B5A1C", "#B9A33B", "#EDDB72", "#F8EC98"]),
        FLAG_B: dict(ramp=["#1B4885", "#2C66AE", "#4A8AD0", "#7DB2EA"]),
        ROPE: dict(ramp=["#3A2614", "#55391E", "#73502B", "#946B3B"]),
        PAGE_WALL: dict(ramp=["#3F3A2E", "#5A5342", "#776E58", "#958A70", "#B0A587", "#C9BE9F"],
                        sub=(lambda p: np.abs(((p[:, 1] + 300) % 16.0) - 8.0) > 7.2, PRINT), dither=0.3),
        PRINT: dict(ramp=["#2B3E5E", "#3C5478", "#506B92", "#6683AB"]),
        BOATP: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF"]),
        TOWN: dict(ramp=["#141A33", "#1E2747", "#2A355C", "#384672", "#475888"], dither=0.3),
        ROOF: dict(ramp=["#200B12", "#34121C", "#4C1A28", "#662436", "#813046"]),
        HULL: dict(ramp=["#0E1938", "#16264F", "#22305C", "#2E3F78", "#3E52A0"]),
        SAIL: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8"]),
    }


def build(flooded=True):
    wl = -3.0 if flooded else -14.0                      # water level
    objs = []

    # the bay: water everywhere below the deck, out to the page curl
    objs.append(Obj(lambda p: (p[:, 1] - wl, WATER), (-500, wl - 2, -260), (500, wl + 0.2, 200), "water"))
    # the next page curls up far behind the bay, like distant cliffs with print on them
    def far_page(p):
        dy, dz = p[:, 1] - 70.0, p[:, 2] + 250.0
        r = np.sqrt(dy * dy + dz * dz)
        d = np.maximum(np.abs(r - 70.0) - 2.0, np.maximum(p[:, 2] + 250.0, -p[:, 1] + wl))
        # the law that belongs on this page, printed big; with the law gone it is only question marks
        u = np.clip(p[:, 0] + 300.0, 0, 599).astype(int)
        v = np.clip((60.0 - p[:, 1]) / 44.0 * 43, 0, 43).astype(int)
        text = (np.abs(p[:, 0]) < 300) & (p[:, 1] > 16) & (p[:, 1] < 60) & LAW_TEX[flooded][v, u]
        return d, np.where(text, PRINT, PAGE_WALL)
    objs.append(Obj(far_page, (-500, wl - 1, -330), (500, 80, -245), "farpage"))

    # pier deck and posts
    def deck(p):
        top = sdf.box(p - [0, -2.0, 18.0], (360, 2.0, 16.0), 0.4)
        d, mat = top, np.full(len(p), DECK)
        for x in range(-340, 360, 40):
            for z in (5.0, 31.0):
                post = sdf.cylinder_y(p - [x, -12.0, z], 2.6, 12.5, 0.8)
                mat = np.where(post < d, POST, mat)
                d = np.minimum(d, post)
        rail = sdf.capsule(p, (-360, 8.0, 3.0), (360, 8.0, 3.0), 0.9)
        mat = np.where(rail < d, ROPE, mat)
        d = np.minimum(d, rail)
        for x in range(-340, 360, 80):
            bol = sdf.cylinder_y(p - [x, 4.0, 3.0], 1.8, 4.5, 0.6)
            mat = np.where(bol < d, POST, mat)
            d = np.minimum(d, bol)
        return d, mat
    objs.append(Obj(deck, (-362, -26, 1), (362, 12, 35), "deck"))

    # lighthouse on a rock, back left (Cyl's workplace)
    def lighthouse(p):
        rock = sdf.ellipsoid(p, (-250, wl - 6, -120), (70, 24, 40))
        q = p - [-250, 90, -120]
        body = sdf.cylinder_y(q, 20.0, 80.0, 1.6)
        mat = np.where(p[:, 1] < 80, GLASSWATER, GLASS)
        marks = (np.abs(((p[:, 1] + 100) % 16.0) - 8.0) > 7.0) & (p[:, 0] < -250) & (p[:, 1] > 20) & (p[:, 1] < 165)
        mat = np.where(marks, METAL, mat)
        lamp = sdf.cylinder_y(p - [-250, 177, -120], 15.0, 8.0, 0.6)
        roof = np.maximum(np.sqrt((p[:, 0] + 250) ** 2 + (p[:, 2] + 120) ** 2) - (21.0 - 0.95 * (p[:, 1] - 185)),
                          np.maximum(185 - p[:, 1], p[:, 1] - 206)) * 0.72
        d = np.minimum(rock, body)
        mat = np.where(rock < body, ROCK, mat)
        for dd, mm in ((lamp, WINDOW), (roof, RED)):
            mat = np.where(dd < d, mm, mat)
            d = np.minimum(d, dd)
        return d, mat
    objs.append(Obj(lighthouse, (-322, wl - 30, -162), (-178, 210, -78), "lighthouse"))

    # Karat & Co.: a little gem-blue shop on the pier
    def shop(p):
        body = sdf.box(p - [-92, 44, -14], (50, 44, 12), 1.2)
        roof = np.maximum(sdf.box(p - [-92, 96, -14], (58, 10, 18), 1.2), (np.abs(p[:, 0] + 92) * 0.5 + p[:, 1]) - 118)
        trim = np.maximum(sdf.box(p - [-92, 87, -14], (51, 2, 13), 0.5), 0)
        win = sdf.box(p - [-112, 36, -1.4], (16, 16, 0.8), 0.6)
        door = sdf.box(p - [-68, 26, -1.4], (10, 26, 0.8), 0.6)
        sign = sdf.box(p - [-92, 72, -0.6], (32, 9, 0.8), 0.4)
        d, mat = body, np.full(len(p), SHOP)
        for dd, mm in ((roof, SHOP_TRIM), (trim, SHOP_TRIM), (win, WINDOW), (door, RED), (sign, SIGN)):
            mat = np.where(dd < d, mm, mat)
            d = np.minimum(d, dd)
        u = np.clip(((p[:, 0] + 92 + 32) / 64.0 * 119), 0, 119).astype(int)
        v = np.clip(((81.0 - p[:, 1]) / 18.0 * 39), 0, 39).astype(int)
        mat = np.where((mat == SIGN) & (p[:, 2] > -0.2) & SIGN_TEX[v, u], SIGN_INK, mat)
        return d, mat
    objs.append(Obj(shop, (-152, -1, -34), (-32, 130, 2), "shop"))

    # the festival stage: curtain, banner, and the cushion where the crown sits
    def stage(p):
        floor_ = sdf.box(p - [60, 5, -10], (62, 5, 14), 0.8)
        back = sdf.box(p - [60, 56, -23], (62, 52, 2), 0.6)
        curtain_l = sdf.box(p - [12, 54, -18], (14, 50, 2.6), 1.6)
        curtain_r = sdf.box(p - [108, 54, -18], (14, 50, 2.6), 1.6)
        banner = sdf.box(p - [60, 98, -19.5], (40, 9, 0.8), 0.4)
        ped = sdf.cylinder_y(p - [60, 18, -8], 5.0, 8.0, 0.6)
        cush = sdf.ellipsoid(p, (60, 27.5, -8), (10.0, 3.2, 7.0))
        d, mat = floor_, np.full(len(p), STAGE)
        for dd, mm in ((back, CURTAIN), (curtain_l, CURTAIN), (curtain_r, CURTAIN), (banner, SIGN), (ped, SHOP_TRIM), (cush, CUSHION)):
            mat = np.where(dd < d, mm, mat)
            d = np.minimum(d, dd)
        u = np.clip(((p[:, 0] - 60 + 40) / 80.0 * 199), 0, 199).astype(int)
        v = np.clip(((107.0 - p[:, 1]) / 18.0 * 39), 0, 39).astype(int)
        mat = np.where((mat == SIGN) & (p[:, 2] > -19.0) & BANNER_TEX[v, u], RED, mat)
        return d, mat
    objs.append(Obj(stage, (-4, -1, -28), (124, 110, 6), "stage"))

    # bunting across the top of the pier
    def bunting(p):
        d = np.full(len(p), 1e9)
        mat = np.full(len(p), ROPE)
        rope = sdf.capsule(p, (-360, 132, -30), (360, 132, -30), 0.5)
        sag = 132 - 6 * np.cos(np.pi * ((p[:, 0] + 360) % 120) / 120 - np.pi / 2) ** 2
        rope = sdf.capsule(p, (-360, 132, -30), (360, 132, -30), 0.5) + np.abs(p[:, 1] - sag) * 0.0
        d = rope
        for i, x in enumerate(range(-350, 360, 16)):
            y = 132 - 6 * np.sin(np.pi * ((x + 360) % 120) / 120)
            tri = np.maximum(np.abs(p[:, 2] + 30) - 0.4,
                             np.maximum(np.abs(p[:, 0] - x) * 1.4 + (y - p[:, 1]) * 0.7 - 5.0, p[:, 1] - y))
            m = (FLAG_R, FLAG_Y, FLAG_B)[i % 3]
            mat = np.where(tri < d, m, mat)
            d = np.minimum(d, tri)
        return d, mat
    objs.append(Obj(bunting, (-362, 118, -32), (362, 134, -28), "bunting"))

    # Bob's mooring: a cleat and a coil of rope, back right; his boat is a sprite
    def mooring(p):
        coil = sdf.torus_y(p - [214, 1.5, -8], 6.0, 1.6)
        cleat = sdf.box(p - [232, 2.0, -8], (4, 2, 1.5), 0.6)
        d = np.minimum(coil, cleat)
        return d, np.where(coil < cleat, ROPE, METAL)
    objs.append(Obj(mooring, (200, -1, -18), (240, 6, 2), "mooring"))

    # the far shore: tall narrow houses along the foot of the next page, windows lit for the festival
    def town(p):
        cell = np.round(p[:, 0] / 24.0)
        hsh = np.abs(np.sin(cell * 12.9898) * 43758.5453) % 1.0
        h = 16.0 + 28.0 * hsh
        q = p - np.stack([cell * 24.0, np.full(len(p), wl + 2.0), np.full(len(p), -205.0)], 1)
        zero = np.zeros_like(h)
        b = np.abs(q - np.stack([zero, h / 2, zero], 1)) - np.stack([zero + 10.0, h / 2, zero + 8.0], 1)
        body = np.linalg.norm(np.maximum(b, 0), axis=1) + np.minimum(b.max(1), 0)
        roof = np.maximum(np.abs(q[:, 0]) * 0.9 + (q[:, 1] - h) - 9.0, np.maximum(h - q[:, 1], np.abs(q[:, 2]) - 9.0)) * 0.7
        quay = sdf.box(p - [0, wl + 1.0, -205.0], (400.0, 1.6, 11.0), 0.5)
        d = np.minimum(np.minimum(body, roof), quay)
        mat = np.where(roof < body, ROOF, TOWN)
        mat = np.where(quay <= np.minimum(body, roof), ROCK, mat)
        lit = np.abs(np.sin(cell * 7.1 + np.floor(q[:, 1] / 8.0) * 3.7 + np.floor((q[:, 0] + 50) / 6.0) * 1.3) * 911.0) % 1.0 > 0.45
        win = (q[:, 2] > 7.4) & (np.abs(((q[:, 0] + 50) % 6.0) - 3.0) < 1.3) & ((q[:, 1] % 8.0) > 3.0) & ((q[:, 1] % 8.0) < 6.6)
        win &= (q[:, 1] > 4) & (q[:, 1] < h - 2) & (np.abs(q[:, 0]) < 8.5) & lit
        return d, np.where(win & (mat == TOWN), WINDOW, mat)
    objs.append(Obj(town, (-400, wl - 1, -217), (400, wl + 56, -193), "town"))

    # boats riding at anchor in the bay, lanterns on their mastheads
    def boats(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), HULL)
        for bx, bz, sc in ((-20.0, -130.0, 1.5), (190.0, -165.0, 1.2), (330.0, -110.0, 1.6)):
            q = (p - [bx, wl, bz]) / sc
            hull = np.maximum(sdf.ellipsoid(q, (0, 2.0, 0), (17.0, 6.0, 5.5)), q[:, 1] - 4.0)
            hm = np.where((q[:, 1] > 1.0) & (q[:, 1] < 2.4), RED, HULL)
            cabin = sdf.box(q - [-4.0, 6.0, 0], (5.0, 2.4, 3.4), 0.8)
            mast = sdf.capsule(q, (2.0, 4.0, 0), (2.0, 34.0, 0), 0.55)
            boom = sdf.capsule(q, (2.0, 9.0, 0), (15.0, 8.0, 0), 1.7)
            lamp = sdf.sphere(q, (2.0, 35.5, 0), 1.3)
            for dd, mm in ((hull * sc, hm), (cabin * sc, SAIL), (mast * sc, METAL), (boom * sc, SAIL), (lamp * sc, WINDOW)):
                mat = np.where(dd < d, mm, mat)
                d = np.minimum(d, dd)
        return d, mat
    objs.append(Obj(boats, (-50, wl - 8, -180), (365, 62, -95), "boats"))

    # what floats and what sinks: with the law gone an anvil bobs on the water and a barrel goes under
    def floaters(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), POST)

        def barrel(x, z, sink):
            q = ((p - [x, wl, z]) / FS - [0, 1.5 - sink, 0]) @ sdf.rot_z(np.pi / 2)
            b = sdf.cylinder_y(q, 4.4 - 0.5 * (np.abs(q[:, 1]) / 6.0) ** 2, 6.0, 1.0)
            return b * FS, np.where(np.abs(np.abs(q[:, 1]) - 3.6) < 0.7, METAL, POST)

        def buoy(x, z, sink, tilt):
            q = ((p - [x, wl, z]) / FS - [0, 0.8 - sink, 0]) @ sdf.rot_x(tilt)
            ring = sdf.torus_y(q, 5.2, 1.7)
            stripe = (np.floor((np.arctan2(q[:, 2], q[:, 0]) + np.pi) / (np.pi / 4)) % 2) == 0
            return ring * FS, np.where(stripe, RED, SIGN)

        def anvil(x, z):
            q = (p - [x, wl, z]) / FS - [0, 0.6, 0]
            body = sdf.box(q - [0, 5.0, 0], (7.0, 2.4, 3.0), 0.5)
            waist = sdf.box(q - [0, 2.0, 0], (3.6, 1.6, 2.4), 0.3)
            foot = sdf.box(q - [0, 0.4, 0], (6.0, 0.8, 3.2), 0.3)
            horn = sdf.round_cone(q, (7.0, 5.6, 0), (14.0, 6.4, 0), 2.0, 0.4)
            return np.minimum(np.minimum(body, waist), np.minimum(foot, horn)) * FS, METAL

        if flooded:
            parts = [anvil(-165.0, -95.0), buoy(150.0, -90.0, 1.6, 0.5), barrel(280.0, -80.0, 6.4)]
        else:
            parts = [barrel(-165.0, -95.0, 0.0), buoy(150.0, -90.0, 0.0, 0.0), barrel(280.0, -80.0, 0.0)]
        for dd, mm in parts:
            mat = np.where(dd < d, mm, mat)
            d = np.minimum(d, dd)
        return d, mat
    objs.append(Obj(floaters, (-195, wl - 20, -125), (320, wl + 22, -55), "floaters"))

    # lamp posts along the back of the pier, and cargo waiting by the shop and the stage
    def dressing(p):
        d, mat = np.full(len(p), 1e9), np.full(len(p), METAL)
        for x in LAMPS:
            post = np.minimum(sdf.capsule(p, (x, 0, 3.0), (x, 46.0, 3.0), 1.1), sdf.cylinder_y(p - [x, 1.0, 3.0], 2.4, 1.2, 0.4))
            cap = sdf.box(p - [x, 54.0, 3.0], (3.6, 1.4, 3.6), 0.5)
            lan = sdf.box(p - [x, 50.0, 3.0], (2.6, 3.2, 2.6), 0.6)
            for dd, mm in ((post, METAL), (cap, METAL), (lan, WINDOW)):
                mat = np.where(dd < d, mm, mat)
                d = np.minimum(d, dd)
        for cx, cy, cz in ((-160.0, 5.0, 7.0), (-149.0, 5.0, 7.0), (-155.0, 15.0, 7.0)):
            crate = sdf.box(p - [cx, cy, cz], (5.0, 5.0, 4.0), 0.5)
            mat = np.where(crate < d, np.where(np.abs(np.abs(p[:, 0] - cx) - 4.4) < 0.7, DECK_GAP, STAGE), mat)
            d = np.minimum(d, crate)
        for bx in (158.0, 166.0):
            b = sdf.cylinder_y(p - [bx, 5.5, 7.0], 3.6 - 0.02 * (p[:, 1] - 5.5) ** 2, 5.5, 0.6)
            mat = np.where(b < d, np.where(np.abs(np.abs(p[:, 1] - 5.5) - 3.4) < 0.6, METAL, POST), mat)
            d = np.minimum(d, b)
        return d, mat
    objs.append(Obj(dressing, (-186, -1, -2), (306, 58, 12), "dressing"))

    sky = gradient_sky(W, H, "#0A0F24", "#3A4A78", glow=(140, 30, 320, "#7A5A3A"))
    stars(sky, 150, seed=3, ymax=110)
    moon(sky, 590, 36, 12)
    lights = [Light((-300, 260, 200), "#FFC877", 1.4, 900),
              *[Light((x, 50.0, 8.0), "#FFC877", 0.55, 70, shadow=False) for x in LAMPS],
              Light((-250, 177, -100), "#FFD27A", 0.6, 140, ignore=("lighthouse",)),
              Light((300, 160, 120), "#7FA8E8", 0.4, 700, shadow=False)]
    return dict(world=World(objs), materials=materials(flooded), width=W, height=H, centre=CENTRE,
                lights=lights, key=0.4, ambient=0.12, top=215.0, ss=2, steps=170, sky=sky,
                bloom=[(WINDOW, "#FFC861", 12, 0.55)])
