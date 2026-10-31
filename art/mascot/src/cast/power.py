"""Case 9, Watt Works: Cog (brass-gear clockmaker), Hoist (iron pulley-block crane operator), Dynamo (motor mechanic)."""
import numpy as np

from .. import sdf
from .. import palette as P
from ..palette import METAL, WHITE, INK, BAND, STEEL
from ..suspects import _Base, _legs, _put  # noqa: F401

BRASS = P.register(["#4A3008", "#7A5214", "#AA7A22", "#D4A43C", "#F2CC6A"], specular="#FFF4D0")
IRONB = P.register(["#14161C", "#22262E", "#343A44", "#4A525E", "#646E7C"], specular="#C8D4E2")
HAZARD = P.register(["#7A5A08", "#B8880E", "#E6B820", "#F8DA4A", "#FFF0A0"])
COIL = P.register(["#4A1C0A", "#7A3214", "#AC5022", "#D87434", "#F6A060"], specular="#FFEAD0")
MOTOR = P.register(["#0E2A3A", "#164058", "#205A7A", "#2E789E", "#4A9AC0"], specular="#D8F0FF")
SPARK = P.register(["#6A9AFF", "#8AB4FF", "#B8D4FF", "#E0ECFF", "#FFFFFF"])


class Cog(_Base):
    """A brass gear standing on edge: twelve teeth, a hub for a face, an eyepiece on a chain."""
    billboard = True
    skin = BRASS
    brow_hex = "#3A2404"
    shoulder = (11.0, 17.0, 0.0)
    front = 3.6

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.0, 5.0), np.full(len(q), INK)
        c = np.array([0, 18.0, 0])
        r = np.hypot(q[:, 0] - c[0], q[:, 1] - c[1])
        a = np.arctan2(q[:, 1] - c[1], q[:, 0] - c[0])
        teeth = 12.4 + 2.2 * np.clip(np.cos(a * 12) * 3.0, -1, 1)
        gear = np.maximum(r - teeth, np.abs(q[:, 2]) - 2.6) * 0.8
        spokes = np.abs(((a * 6 / np.pi) % 1.0) - 0.5) < 0.18
        holes = (r > 8.4) & (r < 10.6) & ~spokes
        gear = np.maximum(gear, np.where(holes, 2.8 - np.abs(q[:, 2]), -1e9))
        d, mat = _put(d, mat, gear, BRASS)
        hub = sdf.cylinder_y((q - [0, 18.0, 1.6]) @ sdf.rot_x(np.pi / 2), 7.6, 1.6, 0.8)
        d, mat = _put(d, mat, hub, BRASS)
        # eyepiece on a little chain at the rim
        lens = sdf.cylinder_y((q - [8.2, 26.4, 3.6]) @ sdf.rot_x(np.pi / 2), 2.0, 1.0, 0.4)
        d, mat = _put(d, mat, lens, INK)
        d, mat = _put(d, mat, sdf.cylinder_y((q - [8.2, 26.4, 4.7]) @ sdf.rot_x(np.pi / 2), 1.4, 0.2), WHITE)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != 1:
            return []
        # a tiny screwdriver
        return [(sdf.capsule(q, h + [0, -0.6, 0.6], h + [0.4, 2.6, 1.2], 0.7), BAND),
                (sdf.capsule(q, h + [0.4, 2.6, 1.2], h + [0.8, 6.4, 1.8], 0.3), STEEL)]

    def face_anchor(self):
        return self._anchor((0, 18.0, 3.2), (7.6, 7.6, 1.0), xs=(-2.8, 2.8)), 0.82


class Hoist(_Base):
    """An iron pulley block: a sheave in its cheeks up top, the chain running over it, hazard stripes, a crane hook."""
    skin = IRONB
    brow_hex = "#06070A"
    shoulder = (10.6, 15.0, 0.0)
    front = 7.0

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.6, 5.0), np.full(len(q), INK)
        block = sdf.box(q - [0, 15.0, 0], (10.4, 10.0, 6.6), 2.2)
        stripe = (np.abs(((q[:, 0] + q[:, 1] + 60) % 4.0) - 2.0) < 1.0) & (q[:, 1] < 8.0)
        d, mat = _put(d, mat, block, np.where(stripe, HAZARD, IRONB))
        for sx in (-1, 1):
            cheek = sdf.box(q - [sx * 4.4, 28.0, 0], (0.9, 5.4, 5.2), 0.6)
            d, mat = _put(d, mat, cheek, IRONB)
        sheave = sdf.cylinder_y((q - [0, 29.0, 0]) @ sdf.rot_z(np.pi / 2), 4.6, 2.6, 0.6)
        d, mat = _put(d, mat, sheave, STEEL)
        d, mat = _put(d, mat, sdf.cylinder_y((q - [0, 29.0, 0]) @ sdf.rot_z(np.pi / 2), 1.2, 5.6, 0.3), METAL)
        for k in range(4):
            for sz in (-1, 1):
                link = sdf.torus_y((q - [0, 34.0 + 3.0 * k, sz * 4.4]) @ sdf.rot_z(np.pi / 2) @ sdf.rot_x((k % 2) * np.pi / 2), 1.3, 0.5)
                d, mat = _put(d, mat, link, STEEL)
        for sx in (-1, 1):
            for sy in (-1, 1):
                d, mat = _put(d, mat, sdf.sphere(q, (sx * 7.6, 15.0 + sy * 7.0, 6.8), 1.0), METAL)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        hq = (q - (h + [0.6, -3.4, 1.4])) @ sdf.rot_x(np.pi / 2)
        hook = np.maximum(sdf.torus_y(hq, 2.6, 0.9), -(q[:, 0] - h[0] - 0.6 + 2.0))
        shank = sdf.capsule(q, h + [2.6, -3.4, 1.4], h + [0.6, 1.2, 1.4], 0.9)
        return [(np.minimum(hook, shank), HAZARD)]

    def face_anchor(self):
        return self._anchor((0, 16.0, 0), (10.4, 10.0, 7.0), xs=(-3.2, 3.2)), 0.88


class Dynamo(_Base):
    """An electric motor: a blue can wound with copper coil, a caged fan on top, a terminal box and a spark."""
    skin = MOTOR
    brow_hex = "#06141E"
    shoulder = (9.6, 15.0, 0.0)
    front = 9.6

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.2, 4.0), np.full(len(q), INK)
        can = sdf.cylinder_y(q - [0, 15.0, 0], 9.4, 11.0, 2.0)
        fins = (np.abs(((np.arctan2(q[:, 2], q[:, 0]) * 16 / np.pi) % 1.0) - 0.5) < 0.12) & (q[:, 2] < 4.0)
        d, mat = _put(d, mat, can, np.where(fins, IRONB, MOTOR))
        for y in (5.6, 24.4):
            d, mat = _put(d, mat, sdf.torus_y(q - [0, y, 0], 9.6, 1.1), COIL)
        cage = np.maximum(np.abs(sdf.sphere(q, (0, 27.0, 0), 7.4)) - 0.3, 26.0 - q[:, 1])
        bars = (np.abs(((np.arctan2(q[:, 2], q[:, 0]) * 8 / np.pi) % 1.0) - 0.5) > 0.38) | (np.abs(((q[:, 1] + 60) % 2.6) - 1.3) > 1.0)
        cage = np.where(bars, cage, cage + 0.6)
        d, mat = _put(d, mat, cage, STEEL)
        for k in range(3):
            bq = (q - [0, 29.6, 0]) @ sdf.rot_y(k * 2.094)
            blade = sdf.ellipsoid(bq, (3.0, 0, 0), (3.0, 0.4, 1.4))
            d, mat = _put(d, mat, blade, BAND)
        tbox = sdf.box(q - [9.8, 12.0, 1.0], (2.0, 3.0, 2.6), 0.6)
        d, mat = _put(d, mat, tbox, IRONB)
        pts = [(-3.0, 34.0, 1.0), (-0.8, 36.4, 1.0), (-2.2, 37.4, 1.0), (0.4, 40.0, 1.0)]
        for a, b in zip(pts[:-1], pts[1:]):
            d, mat = _put(d, mat, sdf.capsule(q, a, b, 0.5), SPARK)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != 1:
            return []
        # an oil can
        body = sdf.cylinder_y(q - (h + [0.6, 2.0, 1.6]), 1.8, 1.6, 0.5)
        spout = sdf.round_cone(q, h + [0.6, 3.6, 1.6], h + [2.6, 7.6, 2.2], 0.7, 0.2)
        return [(np.minimum(body, spout), BAND)]

    def face_anchor(self):
        return self._anchor((0, 16.0, 0), (9.4, 11.0, 9.4), xs=(-3.2, 3.2)), 0.88


CHARS = {"cog": Cog, "hoist": Hoist, "dynamo": Dynamo}
VCENTRE = {"cog": 20.0, "hoist": 20.0, "dynamo": 20.0}
