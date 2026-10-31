"""Case 1 props on transparent backgrounds: paper boats, the (fake) crown,
the lab's balance and the lab bench backdrop.  build(which=...)"""
import numpy as np

from envrender import Obj, World, Light, gradient_sky
from src import sdf

(PAPER, PAPER_LINE, GOLD, GEMR, METAL, LCD, PLASTIC, WOOD, WALL, GLASS, WATER, PRINT) = range(1, 13)

MATERIALS = {
    PAPER: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF", "#FFFBEF"],
                sub=(lambda p: np.abs(((p[:, 1] + 300) % 4.0) - 2.0) > 1.75, PAPER_LINE)),
    PAPER_LINE: dict(ramp=["#3F5E88", "#5577A6", "#6E92C2", "#88AAD8"]),
    GOLD: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848", "#FFE08A", "#FFF4C8"], gloss=26, spec="#FFFFFF"),
    GEMR: dict(ramp=["#4A0A08", "#8E1A14", "#C9302A", "#EE5A4C", "#FF9C8C"], gloss=40, spec="#FFFFFF"),
    METAL: dict(ramp=["#23272E", "#3F4650", "#68717D", "#9AA4AF", "#C7D0D8", "#E8EEF4"], gloss=24, spec="#FFFFFF"),
    LCD: dict(ramp=["#0B2A1A", "#14482B", "#1F7A44"], emissive=False),
    PLASTIC: dict(ramp=["#1C1C24", "#2C2C38", "#40404F", "#575769", "#707086"], gloss=16, spec="#C9CED6"),
    WOOD: dict(ramp=["#2A1608", "#47270F", "#683A18", "#8C5022", "#B06A2E", "#CF8A42"],
               pattern=lambda p, n: 0.5 * np.sin(p[:, 0] * 0.3 + 2 * np.sin(p[:, 2] * 0.1)), pattern_gain=0.14),
    WALL: dict(ramp=["#0E1424", "#151D33", "#1E2944", "#283656", "#33446A"],
               sub=(lambda p: np.abs(((p[:, 1] + 300) % 18.0) - 9.0) > 8.4, PRINT), dither=0.3),
    PRINT: dict(ramp=["#2B3E5E", "#3C5478", "#506B92", "#6683AB"]),
    GLASS: dict(ramp=["#1C3D63", "#2F6496", "#4F8FC6", "#86BDE6", "#C2E1F3"], gloss=40, spec="#FFFFFF"),
    WATER: dict(ramp=["#0F2E5C", "#1B4885", "#2C66AE", "#4A8AD0", "#7DB2EA"], gloss=30, spec="#E6F4FF"),
}


def _boat(scale):
    def f(p):
        q = p / scale
        hull = sdf.box(q - [0, 6, 0], (18, 6, 8), 0.8)
        hull = np.maximum(hull, np.abs(q[:, 0]) - 18 + (q[:, 1]) * 0.9)
        hull = np.maximum(hull, -(q[:, 1] - 3.0) - np.abs(q[:, 2]) * 0.0 - 3.0)
        sail = np.maximum(sdf.box(q - [0, 20, 0], (0.6, 12, 8), 0.3), np.abs(q[:, 2]) * 1.0 + (q[:, 1] - 32) * 0.65)
        sail = np.maximum(sail, 8 - q[:, 1])
        d = np.minimum(hull, sail) * scale
        return d, PAPER
    return [Obj(f, (-20 * scale, -1, -10 * scale), (20 * scale, 34 * scale, 10 * scale), "boat")]


def _crown():
    def f(p):
        band = np.maximum(np.abs(np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2) - 9.0) - 1.4, np.abs(p[:, 1] - 4.0) - 4.0)
        ang = np.arctan2(p[:, 2], p[:, 0])
        spike_h = 8.0 + 6.0 * np.clip(np.cos(ang * 5.0), 0, 1) ** 3
        spikes = np.maximum(np.abs(np.sqrt(p[:, 0] ** 2 + p[:, 2] ** 2) - 9.0) - 1.1, np.maximum(p[:, 1] - spike_h, 7.0 - p[:, 1]))
        d = np.minimum(band, spikes)
        mat = np.full(len(p), GOLD)
        for k in range(5):
            a = k * 2 * np.pi / 5
            gem = sdf.sphere(p, (10.4 * np.cos(a), 4.0, 10.4 * np.sin(a)), 1.7)
            tip = sdf.sphere(p, (9.0 * np.cos(a), 14.6, 9.0 * np.sin(a)), 1.6)
            mat = np.where(gem < d, GEMR, mat)
            d = np.minimum(d, gem)
            mat = np.where(tip < d, GOLD, mat)
            d = np.minimum(d, tip)
        return d, mat
    return [Obj(f, (-14, -1, -14), (14, 18, 14), "crown")]


def _balance():
    def f(p):
        base = sdf.box(p - [0, 6, 0], (22, 6, 14), 2.0)
        lcd = sdf.box(p - [0, 6, 14.2], (10, 3.2, 0.6), 0.3)
        pan = sdf.cylinder_y(p - [0, 13.0, -1], 16.0, 1.0, 0.8)
        btn = sdf.sphere(p, (15, 7, 13.6), 1.6)
        d, mat = base, np.full(len(p), PLASTIC)
        for dd, mm in ((lcd, LCD), (pan, METAL), (btn, GEMR)):
            mat = np.where(dd < d, mm, mat)
            d = np.minimum(d, dd)
        return d, mat
    return [Obj(f, (-24, -1, -16), (24, 16, 16), "balance")]


def _bench():
    """Lab backdrop: a bench top in front of a dark ruled wall, warm lamp from the left."""
    objs = [Obj(lambda p: (sdf.box(p - [0, -6, 20], (300, 6, 60), 1.0), WOOD), (-300, -12, -40), (300, 0.2, 80), "bench"),
            Obj(lambda p: (sdf.box(p - [0, 120, -46], (300, 140, 6)), WALL), (-300, -20, -52), (300, 260, -40), "wall")]
    return objs


def build(which="boat_s"):
    lights = [Light((-200, 260, 220), "#FFC46B", 1.1, 800), Light((220, 80, 120), "#6F8FD8", 0.4, 500, shadow=False)]
    if which.startswith("boat"):
        sc = {"boat_s": 0.9, "boat_m": 1.25, "boat_l": 1.7}[which]
        objs, w, h, c = _boat(sc), int(48 * sc) + 8, int(50 * sc) + 8, (0.0, 14.0 * sc)
    elif which == "crown":
        objs, w, h, c = _crown(), 40, 36, (0.0, 7.0)
    elif which == "balance":
        objs, w, h, c = _balance(), 64, 40, (0.0, 4.0)
    else:
        sky = gradient_sky(480, 270, "#05060F", "#141A33")
        return dict(world=World(_bench()), materials=MATERIALS, width=480, height=270, centre=(0.0, 92.0),
                    lights=[Light((-260, 260, 200), "#FFC46B", 1.4, 900)], key=0.3, ambient=0.1, top=270.0,
                    ss=2, steps=140, sky=sky)
    return dict(world=World(objs), materials=MATERIALS, width=w, height=h, centre=c,
                lights=lights, key=0.55, ambient=0.15, top=60.0, ss=2, steps=140)
