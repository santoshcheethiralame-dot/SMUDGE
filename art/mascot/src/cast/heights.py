"""Case 4, Lumen Heights: Lumen (street-lamp lamplighter), Vane (weathervane forecaster), Sola (sunflower gossip)."""
import numpy as np

from .. import sdf
from .. import palette as P
from ..palette import METAL, WHITE, INK, PAPER, BAND, NAVY
from ..suspects import _Base, _legs, _put  # noqa: F401

IRON = P.register(["#0A1210", "#132220", "#1E3430", "#2C4A44", "#3E625A"], specular="#9FD8C8")
LAMPGLASS = P.register(["#7A5210", "#B8801E", "#E6B03A", "#F8D670", "#FFF0B0"], specular="#FFFFFF")
VERDI = P.register(["#123A34", "#1E5A4E", "#2E7E6A", "#4AA48A", "#7CCCB0"], specular="#E0FFF4")
COPPER = P.register(["#4A1E0C", "#7A3416", "#AA5424", "#D47A3C", "#F0A062"], specular="#FFE2C8")
PETAL = P.register(["#7A5208", "#B8800E", "#E8B420", "#F8D44A", "#FFEC96"], specular="#FFFBE0")
SEED = P.register(["#3A2210", "#5A3618", "#7A4C24", "#9A6432", "#B87E44"], specular="#F0D8B0")
LEAF = P.register(["#0E2A14", "#17421F", "#22602C", "#30823C", "#48A452"], specular="#D8FFD0")
TERRA = P.register(["#4A1A0E", "#76301A", "#A04828", "#C4663A", "#E08A56"], specular="#FFD8C0")
FLAME = P.register(["#B8400E", "#F07018", "#FFA830", "#FFD860", "#FFF6C0"])


class Lumen(_Base):
    """A cast-iron street lamp: fluted post for a body, a glowing glass lantern for a head, a lighting pole in hand."""
    skin = LAMPGLASS
    brow_hex = "#5A3A08"
    shoulder = (2.4, 21.0, 0.0)
    front = 3.0

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 2.4, 5.0), np.full(len(q), INK)
        plinth = sdf.round_cone(q, (0, 5.0, 0), (0, 9.0, 0), 5.2, 3.2)
        d, mat = _put(d, mat, plinth, IRON)
        post = sdf.cylinder_y(q - [0, 16.5, 0], 2.6, 8.0, 0.4)
        ang = np.arctan2(q[:, 2], q[:, 0])
        d, mat = _put(d, mat, post, np.where(np.cos(ang * 8) > 0.6, INK, IRON))
        for y in (9.6, 24.4):
            d, mat = _put(d, mat, sdf.torus_y(q - [0, y, 0], 2.9, 0.8), METAL)
        # the lantern: a glass box in an iron frame, with a pyramid roof and a finial
        glass = sdf.box(q - [0, 32.5, 0], (6.6, 7.4, 6.6), 1.4)
        d, mat = _put(d, mat, glass, LAMPGLASS)
        for sx in (-1, 1):
            for sz in (-1, 1):
                bar = sdf.capsule(q, (sx * 6.6, 25.4, sz * 6.6), (sx * 6.6, 40.0, sz * 6.6), 0.7)
                d, mat = _put(d, mat, bar, IRON)
        tray = sdf.cylinder_y(q - [0, 25.2, 0], 7.6, 0.8, 0.4)
        d, mat = _put(d, mat, tray, IRON)
        roof = np.maximum(np.maximum(np.abs(q[:, 0]), np.abs(q[:, 2])) * 1.25 + (q[:, 1] - 48.0), 40.0 - q[:, 1]) * 0.62
        d, mat = _put(d, mat, roof, IRON)
        d, mat = _put(d, mat, sdf.sphere(q, (0, 48.6, 0), 1.4), METAL)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != 1:
            return []
        top = h + [1.6, 12.0, 1.0]
        return [(sdf.capsule(q, h + [-0.4, -4.0, 0], top, 0.55), METAL),
                (sdf.ellipsoid(q, top + [0, 1.6, 0], (1.0, 1.8, 1.0)), FLAME)]

    def face_anchor(self):
        return self._anchor((0, 32.0, 0), (6.6, 7.4, 6.8), xs=(-2.6, 2.6)), 0.8


class Vane(_Base):
    """A verdigris copper ball on a compass cross, with a weathervane arrow spinning on its head."""
    skin = VERDI
    brow_hex = "#0E2E28"
    shoulder = (9.4, 18.0, 0.0)
    front = 10.0

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.0, 8.0), np.full(len(q), INK)
        body = sdf.sphere(q, (0, 17.0, 0), 10.0)
        d, mat = _put(d, mat, body, VERDI)
        # the compass cross through the waist, a letter plate on each arm
        for a, b in (((-15.0, 9.5, 0), (15.0, 9.5, 0)), ((0, 9.5, -15.0), (0, 9.5, 15.0))):
            d, mat = _put(d, mat, sdf.capsule(q, a, b, 0.7), COPPER)
        for c in ((15.6, 9.5, 0), (-15.6, 9.5, 0), (0, 9.5, 15.6), (0, 9.5, -15.6)):
            plate = sdf.box(q - c, (1.5, 1.7, 1.5), 0.4)
            d, mat = _put(d, mat, plate, METAL)
        d, mat = _put(d, mat, sdf.torus_y(q - [0, 9.5, 0], 8.0, 0.7), COPPER)
        # spindle, ball and the arrow, tipped to point
        d, mat = _put(d, mat, sdf.capsule(q, (0, 26.0, 0), (0, 38.0, 0), 0.7), COPPER)
        d, mat = _put(d, mat, sdf.sphere(q, (0, 28.4, 0), 1.6), METAL)
        shaft = sdf.capsule(q, (-9.0, 36.0, 0), (8.0, 36.0, 0), 0.7)
        head = np.maximum.reduce([np.abs(q[:, 2]) - 0.6, (q[:, 0] - 13.0) + np.abs(q[:, 1] - 36.0) * 1.6, 7.0 - q[:, 0]])
        tail = np.maximum.reduce([np.abs(q[:, 2]) - 0.5, -q[:, 0] - 13.0, q[:, 0] + 6.0, np.abs(q[:, 1] - 36.0) - 1.0 - 0.45 * (-q[:, 0] - 6.0)])
        d, mat = _put(d, mat, shaft, COPPER)
        d, mat = _put(d, mat, head, COPPER)
        d, mat = _put(d, mat, tail, COPPER)
        # a rooster's comb on top of the ball, for a weathercock
        for k, x in enumerate((-2.2, 0.0, 2.2)):
            d, mat = _put(d, mat, sdf.sphere(q, (x, 26.4 + (1.2 if k == 1 else 0.4), -1.0), 1.6), BAND)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        # a little wind sock on a stick
        return [(sdf.capsule(q, h + [0, -1.0, 0], h + [0, 8.0, 0], 0.4), METAL),
                (sdf.round_cone(q, h + [0.4, 7.0, 0], h + [6.0, 6.0, 0], 1.6, 0.8),
                 np.where((np.floor((q[:, 0] - h[0]) / 1.6) % 2) == 0, BAND, WHITE))]

    def face_anchor(self):
        return self._anchor((0, 17.0, 0), (10.0, 10.0, 10.0), xs=(-3.4, 3.4), dy=2.0), 0.9


class Sola(_Base):
    """A sunflower in a terracotta pot; the seed head is her face, and she carries the Gazette."""
    billboard = True
    skin = SEED
    brow_hex = "#120804"
    shoulder = (1.8, 21.0, 0.0)
    front = 3.0

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.0, 3.0), np.full(len(q), INK)
        pot = sdf.round_cone(q, (0, 3.0, 0), (0, 11.0, 0), 5.0, 6.8)
        rim = sdf.torus_y(q - [0, 12.0, 0], 6.6, 1.3)
        d, mat = _put(d, mat, sdf.smin(pot, rim, 0.8), TERRA)
        soil = sdf.cylinder_y(q - [0, 12.4, 0], 5.8, 0.4, 0.2)
        d, mat = _put(d, mat, soil, SEED)
        stem = sdf.capsule(q, (0, 12.0, 0), (0, 26.0, -0.6), 1.6)
        d, mat = _put(d, mat, stem, LEAF)
        for sx in (-1, 1):
            lq = (q - [sx * 5.0, 17.5, 0]) @ sdf.rot_z(sx * 0.5)
            d, mat = _put(d, mat, sdf.ellipsoid(lq, (0, 0, 0), (4.4, 1.8, 1.0)), LEAF)
        # the head: a ring of petals round the seed disc
        c = np.array([0, 33.0, 0])
        r = q - c
        disc = sdf.ellipsoid(q, c + [0, 0, 0.6], (7.2, 7.2, 2.6))
        ang = np.arctan2(r[:, 1], r[:, 0])
        k = np.round(ang / (2 * np.pi / 14)) * (2 * np.pi / 14)
        u = r[:, 0] * np.cos(k) + r[:, 1] * np.sin(k)
        v = -r[:, 0] * np.sin(k) + r[:, 1] * np.cos(k)
        petal = np.sqrt(((u - 9.6) / 4.2) ** 2 + (v / 1.9) ** 2 + (r[:, 2] / 0.9) ** 2) * 1.6 - 1.6
        back = np.sqrt(((u - 8.6) / 3.8) ** 2 + ((np.abs(v) - 1.6) / 1.8) ** 2 + ((r[:, 2] + 1.2) / 0.8) ** 2) * 1.4 - 1.4
        d, mat = _put(d, mat, np.minimum(petal, back) * 0.8, PETAL)
        seeds = (np.sin(r[:, 0] * 2.6) * np.sin(r[:, 1] * 2.6) > 0.55) & (np.hypot(r[:, 0], r[:, 1]) > 5.6)
        d, mat = _put(d, mat, disc, np.where(seeds, INK, SEED))
        # a bow on the stem, for a columnist
        for sx in (-1, 1):
            d, mat = _put(d, mat, sdf.ellipsoid(q, (sx * 1.8, 24.4, 1.4), (1.8, 1.2, 0.8)), BAND)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        paper = sdf.box(q - (h + [0.8, 3.2, 2.0]), (3.0, 4.0, 0.4), 0.2)
        lines = (np.abs(((q[:, 1] - h[1]) % 1.4) - 0.7) < 0.22) & (np.abs(q[:, 0] - h[0] - 0.8) < 2.2)
        return [(paper, np.where(lines, NAVY, PAPER))]

    def face_anchor(self):
        return self._anchor((0, 33.0, 0.6), (7.2, 7.2, 2.6), xs=(-2.6, 2.6)), 0.8


CHARS = {"lumen": Lumen, "vane": Vane, "sola": Sola}
VCENTRE = {"lumen": 33.0, "vane": 21.0, "sola": 31.0}
