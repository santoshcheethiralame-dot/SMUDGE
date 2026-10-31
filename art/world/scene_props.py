"""Standalone props on transparent backgrounds: the giant pen nib and the
Rubber Baron's eraser. build(which="nib"|"eraser")."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light
from src import sdf

PEN, GOLD, GOLD_DARK, RUBBER, SLEEVE, SLEEVE_PRINT, RUBBER_WORN = range(1, 8)

MATERIALS = {
    PEN: dict(ramp=["#030305", "#08080D", "#111118", "#1C1C26", "#2B2B38", "#3D3D4E"], gloss=40, spec="#C9D3E6", dither=0.15),
    GOLD: dict(ramp=["#3E2A06", "#664611", "#94681D", "#C08F2C", "#E5B848", "#FFE08A", "#FFF4C8"], gloss=22, spec="#FFFFFF", dither=0.15),
    GOLD_DARK: dict(ramp=["#1E1403", "#3A2808", "#5C3F0E", "#7E5714"]),
    RUBBER: dict(ramp=["#5A1F32", "#7E2D47", "#A2405F", "#C3587A", "#DD7896", "#F09CB4", "#FBC4D3"], dither=0.25),
    RUBBER_WORN: dict(ramp=["#4A2A33", "#64404A", "#7F5862", "#9A707A", "#B48A93", "#CBA4AC"], dither=0.3),
    SLEEVE: dict(ramp=["#0D1F45", "#163066", "#21458A", "#2E5CAD", "#4277CC", "#5F95E2"], dither=0.15),
    SLEEVE_PRINT: dict(ramp=["#BFC9DC", "#D7DFEC", "#EEF2F8", "#FFFFFF"]),
}


def _nib():
    # pen comes in from the upper right; nib tip at the origin
    axis = np.array([-0.62, -0.72, 0.31])
    axis /= np.linalg.norm(axis)
    up = np.cross(axis, [0, 0, 1.0])
    up /= np.linalg.norm(up)
    side = np.cross(axis, up)
    basis = np.stack([up, axis, side], 1)          # local x=up, y=axis(to tip), z=side

    def f(p):
        q = p @ basis                               # q[:,1] grows toward the tip
        y = q[:, 1]
        # barrel, section and gold ring
        barrel = sdf.cylinder_y(q - [0, -120, 0], 13.0, 70.0, 4.0)
        section = sdf.round_cone(q, (0, -52, 0), (0, -32, 0), 11.0, 9.0)
        ring = sdf.cylinder_y(q - [0, -50, 0], 13.8, 3.0, 1.0)
        # the nib: a tapering, slightly curved blade
        w = np.clip((0 - y) / 40.0, 0, 1)           # 0 at tip, 1 at the base
        half_w = 1.2 + 10.0 * w ** 0.8
        nib = np.maximum(np.abs(q[:, 0]) - half_w, np.abs(q[:, 2] - 1.5 * (1 - w)) - 1.8)
        nib = np.maximum(nib, np.maximum(y - 0.0, -40.0 - y))
        slit = np.maximum(np.abs(q[:, 0]) - 0.7, np.maximum(y - 0.5, -24.0 - y))
        hole = sdf.cylinder_y((q - [0, -24, 0]) @ sdf.rot_x(np.pi / 2), 2.6, 4.0, 0.3)
        nib = np.maximum(nib, -np.minimum(slit, hole))
        d = barrel
        mat = np.full(len(p), PEN)
        for dd, mm in ((section, PEN), (ring, GOLD), (nib, GOLD)):
            mat = np.where(dd < d, mm, mat)
            d = np.minimum(d, dd)
        return d, mat
    return [Obj(f, (-20, -20, -60), (160, 200, 60), "nib")], (210, 190), (58.0, 82.0)


def _eraser():
    tex = Image.new("L", (240, 60), 0)
    font = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", 30)
    ImageDraw.Draw(tex).text((22, 10), "BARON", font=font, fill=255)
    tex = np.array(tex) > 100

    def f(p):
        rub = sdf.box(p - [-30, 34, 0], (62, 34, 30), 7.0)
        slv = sdf.box(p - [52, 34, 0], (38, 36.5, 32.5), 2.0)
        mat = np.where(slv < rub, SLEEVE, RUBBER)
        d = np.minimum(rub, slv)
        # worn, rounded rubbing face at the bottom-left, smudged grey
        worn = (p[:, 1] < 6) | (p[:, 0] < -86)
        mat = np.where((mat == RUBBER) & worn, RUBBER_WORN, mat)
        # print on the front face of the sleeve
        front = (mat == SLEEVE) & (p[:, 2] > 31.5)
        u = np.clip((p[:, 0] - 14) * 3.0, 0, 239).astype(int)
        v = np.clip((52 - p[:, 1]) * 2.4, 0, 59).astype(int)
        mat = np.where(front & tex[v, u], SLEEVE_PRINT, mat)
        return d, mat
    return [Obj(f, (-100, -4, -40), (100, 80, 40), "eraser")], (240, 150), (0.0, 30.0)


def build(which="nib"):
    objs, (w, h), centre = _nib() if which == "nib" else _eraser()
    lights = [Light((-200, 260, 220), "#FFC46B", 1.1, 800),
              Light((220, 80, 120), "#6F8FD8", 0.4, 500, shadow=False)]
    return dict(world=World(objs), materials=MATERIALS, width=w, height=h, centre=centre,
                lights=lights, key=0.5, ambient=0.14, top=260.0, ss=2, steps=160)
