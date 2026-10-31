"""Case 5, Prism Port: Frost (ice-cube sculptor), Pane (glass-jar glassblower), Geo (geode gem cutter)."""
import numpy as np

from .. import sdf
from .. import palette as P
from ..palette import METAL, WHITE, INK, BAND, WOOD, NAVY
from ..suspects import _Base, _legs, _put  # noqa: F401

ICE = P.register(["#2E6A8E", "#4E94B8", "#7EBEDC", "#B4E0F2", "#E6F8FF"], specular="#FFFFFF")
SCARF = P.register(["#16264F", "#1F3A7A", "#2E56A8", "#4A7ED0", "#7AA8EC"], specular="#D8E8FF")
JAR = P.register(["#2A5E54", "#468C7C", "#6EB8A4", "#A2DCCA", "#D8F6EC"], specular="#FFFFFF")
CORK = P.register(["#4A2E14", "#6E4620", "#966232", "#BC8448", "#DCA868"], specular="#FFE8C8")
GLOW = P.register(["#B8400E", "#F07018", "#FFA830", "#FFD860", "#FFF6C0"])
MARBLE = P.register(["#4A0F3A", "#7A1A60", "#B02C8A", "#DB58B4", "#F59AD8"], specular="#FFFFFF")
ROCK = P.register(["#2A2630", "#3E3A46", "#58525E", "#746C7A", "#948A98"], specular="#D8D0E0")
SAPPH = P.register(["#0A1A5A", "#14308E", "#2450C4", "#4A7EEA", "#8AB4FF"], specular="#FFFFFF")


class Frost(_Base):
    """An ice cube with a knitted scarf, a cap of snow, icicles along the bottom edge and a chisel in hand."""
    skin = ICE
    brow_hex = "#1E4C6A"
    shoulder = (10.6, 15.0, 0.0)
    front = 10.0

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.4, 4.0), np.full(len(q), INK)
        cube = sdf.box(q - [0, 14.0, 0], (10.6, 10.6, 9.6), 2.4)
        # frost cracks inside the ice
        crack = (np.abs(np.sin(q[:, 0] * 0.7 + q[:, 1] * 0.45) * np.sin(q[:, 1] * 0.6 - q[:, 2] * 0.5)) < 0.06) & (q[:, 2] < 8.0)
        d, mat = _put(d, mat, cube, np.where(crack, WHITE, ICE))
        snow = np.maximum(sdf.ellipsoid(q, (0, 25.0, 0), (11.4, 3.4, 10.4)), 23.6 - q[:, 1])
        d, mat = _put(d, mat, snow, WHITE)
        for x in (-7.0, -2.0, 4.0, 8.0):
            ic = sdf.round_cone(q, (x, 3.4, 9.4), (x, 3.4 - (2.4 + abs(x) * 0.25), 9.4), 1.1, 0.25)
            d, mat = _put(d, mat, ic, ICE)
        # the scarf round the top, a tail hanging down one side
        scarf = np.maximum(sdf.box(q - [0, 21.0, 0], (11.6, 1.8, 10.6), 2.4), -sdf.box(q - [0, 21.0, 0], (9.4, 4.0, 8.4), 1.0))
        stripe = np.abs(((q[:, 0] + q[:, 2] + 60) % 4.0) - 2.0) < 0.7
        d, mat = _put(d, mat, scarf, np.where(stripe, WHITE, SCARF))
        tail = sdf.box((q - [7.0, 15.0, 10.4]) @ sdf.rot_z(0.12), (1.8, 5.0, 0.6), 0.4)
        d, mat = _put(d, mat, tail, SCARF)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != 1:
            return []
        return [(sdf.capsule(q, h + [0, -2.0, 0.5], h + [0.4, 3.6, 1.6], 0.7), WOOD),
                (sdf.box(q - (h + [0.6, 5.6, 2.0]), (0.9, 1.8, 0.35), 0.2), METAL)]

    def face_anchor(self):
        return self._anchor((0, 13.0, 0), (10.6, 10.6, 9.8), xs=(-3.4, 3.4)), 0.9


class Pane(_Base):
    """A glass jar with marbles glowing in the bottom, a cork for a hat and a blowpipe with a hot gather."""
    skin = JAR
    brow_hex = "#1A4A40"
    shoulder = (8.6, 18.0, 0.0)
    front = 9.0

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.0, 4.0), np.full(len(q), INK)
        body = sdf.cylinder_y(q - [0, 15.0, 0], 8.8, 11.0, 3.0)
        neck = sdf.cylinder_y(q - [0, 28.0, 0], 6.0, 2.4, 0.8)
        lip = sdf.torus_y(q - [0, 30.4, 0], 6.2, 0.9)
        d, mat = _put(d, mat, sdf.smin(body, neck, 2.0), JAR)
        d, mat = _put(d, mat, lip, JAR)
        for x, y, z, r, m in ((-4.0, 6.6, -2.0, 2.6, MARBLE), (2.6, 6.4, -3.0, 2.4, SAPPH), (0.0, 6.0, 2.0, 2.0, GLOW)):
            d, mat = _put(d, mat, sdf.sphere(q, (x, y, z), r), m)
        cork = sdf.cylinder_y(q - [0, 34.6, 0], 5.6 - 0.12 * (q[:, 1] - 34.6), 3.6, 0.8)
        dots = np.sin(q[:, 0] * 3.1) * np.sin(q[:, 1] * 2.7) * np.sin(q[:, 2] * 2.9) > 0.5
        d, mat = _put(d, mat, cork, np.where(dots, WOOD, CORK))
        # a label band round the belly, below the face
        band = np.maximum(sdf.cylinder_y(q - [0, 7.6, 0], 9.0, 1.4, 0.4), -sdf.cylinder_y(q - [0, 7.6, 0], 8.4, 3.0))
        d, mat = _put(d, mat, band, BAND)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != 1:
            return []
        tip = h + [3.0, 11.0, 2.0]
        return [(sdf.capsule(q, h + [-0.6, -3.0, -0.4], tip, 0.6), METAL), (sdf.sphere(q, tip + [0.3, 1.4, 0.2], 1.9), GLOW)]

    def face_anchor(self):
        return self._anchor((0, 17.0, 0), (8.8, 11.0, 8.8), xs=(-3.0, 3.0), dy=0.0), 0.88


class Geo(_Base):
    """A grey geode, cracked open on top into a crown of sapphire crystals, holding a jeweller's loupe."""
    skin = ROCK
    brow_hex = "#1A1820"
    shoulder = (10.4, 16.0, 0.0)
    front = 10.0

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.4, 5.0), np.full(len(q), INK)
        lumpy = 0.7 * np.sin(q[:, 0] * 0.9) * np.sin(q[:, 1] * 0.8 + 1.0) * np.sin(q[:, 2] * 0.85)
        rock = sdf.ellipsoid(q, (0, 15.0, 0), (11.4, 12.0, 10.4)) + lumpy
        cut = 24.0 - q[:, 1] + 1.4 * np.sin(q[:, 0] * 0.8) + 0.9 * np.sin(q[:, 2] * 1.1)
        shell = np.maximum(rock, -cut)
        speck = np.sin(q[:, 0] * 2.3) * np.sin(q[:, 1] * 2.1) * np.sin(q[:, 2] * 1.9) > 0.7
        d, mat = _put(d, mat, shell, np.where(speck, INK, ROCK))
        inner = sdf.ellipsoid(q, (0, 22.0, 0), (9.4, 4.0, 8.4))
        d, mat = _put(d, mat, inner, WHITE)
        for k in range(9):
            a = k * 2.4
            r = 2.0 + 4.6 * ((k * 0.37) % 1.0)
            base = np.array([r * np.cos(a), 22.4, r * np.sin(a) * 0.9])
            tip = base + [0.9 * np.cos(a), 5.4 + 2.6 * ((k * 0.61) % 1.0), 0.8 * np.sin(a)]
            crystal = sdf.round_cone(q, base, tip, 1.5, 0.25)
            d, mat = _put(d, mat, crystal, SAPPH)
        # a canvas apron strap and a pocket
        apron = np.maximum(sdf.box(q - [0, 6.0, 6.0], (7.0, 4.0, 8.0), 1.0), rock - 0.5)
        d, mat = _put(d, mat, apron, NAVY)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        return [(sdf.cylinder_y((q - (h + [0.4, 2.4, 1.6])) @ sdf.rot_x(np.pi / 2), 1.5, 1.3, 0.4), INK),
                (sdf.cylinder_y((q - (h + [0.4, 2.4, 2.9])) @ sdf.rot_x(np.pi / 2), 1.1, 0.2), SAPPH)]

    def face_anchor(self):
        return self._anchor((0, 15.0, 0), (11.4, 12.0, 10.4), xs=(-3.4, 3.4), dy=0.0), 0.9


CHARS = {"frost": Frost, "pane": Pane, "geo": Geo}
VCENTRE = {"frost": 17.0, "pane": 20.0, "geo": 19.0}
