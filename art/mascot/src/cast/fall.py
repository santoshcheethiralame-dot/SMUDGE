"""Case 10, Hollowmere Manor: Sir Rivet (suit of armour), Lady Varnish (walking portrait), Pendle (clock pendulum)."""
import numpy as np

from .. import sdf
from .. import palette as P
from ..palette import INK, BAND, STEEL
from ..suspects import _Base, _legs, _put  # noqa: F401

ARMOUR = P.register(["#2A3038", "#46505C", "#6A7684", "#98A4B2", "#C8D2DC"], specular="#FFFFFF")
RIVETS = P.register(["#4A3410", "#7A5A1C", "#A8802E", "#D2A84A", "#F2D27A"], specular="#FFF2C0")
GILT = P.register(["#5A3A0A", "#8A6014", "#BC8C26", "#E2B84A", "#FADC82"], specular="#FFF6D0")
OIL = P.register(["#0A1A14", "#122A20", "#1C3C2E", "#28503E", "#366650"])
PAINTSKIN = P.register(["#7A4A3A", "#A8705A", "#CC9478", "#E8B898", "#F8D8BC"], specular="#FFF0E0")
GOWN = P.register(["#2A0614", "#460C22", "#681434", "#8E2048", "#B6345E"])
BRASS = P.register(["#4A2E08", "#7A5012", "#AC7A22", "#D8A63E", "#F6D070"], specular="#FFF4C8")
WAX = P.register(["#A8A090", "#C8C0AE", "#E2DCCA", "#F2EEE0", "#FFFCF4"])
FLAME = P.register(["#B8400E", "#F07018", "#FFA830", "#FFD860", "#FFF6C0"])


class Rivet(_Base):
    """A suit of armour: a riveted breastplate, a round helm with his face on the front, a red plume, and a candle
    held up against the dark he is secretly scared of."""
    skin = ARMOUR
    brow_hex = "#1A1E24"
    shoulder = (8.6, 19.0, 0.0)
    front = 6.4

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.2, 6.0), np.full(len(q), ARMOUR)
        chest = sdf.box(q - [0, 15.0, 0], (7.0, 8.0, 5.0), 2.4)
        d, mat = _put(d, mat, chest, ARMOUR)
        belt = sdf.box(q - [0, 8.6, 0], (7.4, 1.2, 5.4), 0.6)
        d, mat = _put(d, mat, belt, RIVETS)
        for x, y in ((-4.6, 19.0), (4.6, 19.0), (-4.6, 12.0), (4.6, 12.0), (0.0, 16.0)):
            d, mat = _put(d, mat, sdf.sphere(q, (x, y, 5.2), 0.8), RIVETS)
        for s in (-1, 1):
            pauldron = sdf.ellipsoid(q, (s * 7.6, 21.0, 0), (3.4, 2.6, 3.8))
            d, mat = _put(d, mat, pauldron, ARMOUR)
        helm = sdf.smin(sdf.cylinder_y(q - [0, 28.0, 0], 7.4, 5.4, 2.0), sdf.sphere(q, (0, 32.0, 0), 7.0), 2.0)
        d, mat = _put(d, mat, helm, ARMOUR)
        ridge = sdf.box(q - [0, 34.0, 0], (0.8, 4.2, 6.8), 0.6)
        d, mat = _put(d, mat, ridge, RIVETS)
        # the plume, sweeping back off the crest
        pts = [(0, 38.0, 1.0), (0, 41.5, -1.0), (0, 43.0, -4.5), (0, 41.0, -8.0), (0, 37.5, -9.5)]
        for k, (a, c) in enumerate(zip(pts[:-1], pts[1:])):
            d, mat = _put(d, mat, sdf.capsule(q, a, c, 2.2 - 0.35 * k), BAND)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != 1:
            return []
        return [(sdf.cylinder_y(q - (h + [0, 3.6, 0.6]), 1.1, 2.6, 0.3), WAX),
                (sdf.ellipsoid(q, h + [0, 7.6, 0.6], (0.9, 1.6, 0.9)), FLAME)]

    def face_anchor(self):
        return self._anchor((0, 28.0, 0), (7.4, 6.0, 7.4), xs=(-2.8, 2.8)), 0.82


class Varnish(_Base):
    """An oil portrait who walks: a gilt frame on legs, a painted lady in it whose face is her face, a burgundy
    gown painted below."""
    skin = PAINTSKIN
    brow_hex = "#2A1008"
    shoulder = (11.2, 18.0, 0.0)
    front = 2.6

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.4, 6.0), np.full(len(q), INK)
        frame = sdf.box(q - [0, 25.0, 0], (11.0, 15.0, 1.6), 0.8)
        d, mat = _put(d, mat, frame, GILT)
        for x in (-11.0, 11.0):
            for y in (10.0, 40.0):
                d, mat = _put(d, mat, sdf.sphere(q, (x, y, 0.6), 2.0), GILT)
        crest = sdf.ellipsoid(q, (0, 41.0, 0.4), (4.0, 2.6, 1.6))
        d, mat = _put(d, mat, crest, GILT)
        # the canvas, painted: a dark green ground, her face in an oval, black hair piled up, the gown below
        canvas = sdf.box(q - [0, 25.0, 1.4], (8.6, 12.6, 0.4), 0.2)
        x, y = q[:, 0], q[:, 1]
        face = ((x / 4.6) ** 2 + ((y - 27.0) / 5.4) ** 2) < 1
        hair = (((x / 5.4) ** 2 + ((y - 29.5) / 6.2) ** 2) < 1) | ((x ** 2 + (y - 35.6) ** 2) < 3.0 ** 2)
        gown = (y < 20.5) & (np.abs(x) < 4.0 + (20.5 - y) * 0.8)
        pearls = (np.abs(y - 20.9 + 0.08 * x * x) < 0.7) & (np.abs(x) < 3.6) & (((x + 100) % 1.6) < 1.0)
        paint = np.where(face, PAINTSKIN, np.where(hair, INK, np.where(pearls, WAX, np.where(gown, GOWN, OIL))))
        d, mat = _put(d, mat, canvas, paint)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        # a folded fan
        return [(sdf.round_cone(q, h + [0, 0.6, 0.6], h + [-0.8, 6.0, 1.2], 0.5, 1.4), GOWN)]

    def face_anchor(self):
        # a flat canvas: a huge, shallow ellipsoid puts the eyes on the paint, facing out
        return self._anchor((0, 27.0, -30.0), (40.0, 40.0, 31.8), xs=(-2.0, 2.0)), 0.7


class Pendle(_Base):
    """The tower clock's pendulum: a brass rod, and a big round bob that is his face, ticking side to side."""
    skin = BRASS
    brow_hex = "#3A2206"
    shoulder = (9.6, 15.0, 0.0)
    front = 3.0

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 2.6, 6.0), np.full(len(q), INK)
        bob = sdf.cylinder_y((q - [0, 16.0, 0]) @ sdf.rot_x(np.pi / 2), 10.0, 1.8, 1.0)
        d, mat = _put(d, mat, bob, BRASS)
        rim = sdf.torus_y((q - [0, 16.0, 0]) @ sdf.rot_x(np.pi / 2), 10.0, 0.9)
        d, mat = _put(d, mat, rim, RIVETS)
        rod = sdf.box(q - [0, 35.0, 0], (1.1, 9.0, 0.9), 0.4)
        d, mat = _put(d, mat, rod, RIVETS)
        pivot = sdf.cylinder_y((q - [0, 45.0, 0]) @ sdf.rot_x(np.pi / 2), 2.4, 1.2, 0.5)
        d, mat = _put(d, mat, pivot, STEEL)
        # twelve tick marks round the bob, like the clock face he swings under
        a = np.arctan2(q[:, 1] - 16.0, q[:, 0])
        r = np.hypot(q[:, 0], q[:, 1] - 16.0)
        tick = (np.abs(((a * 12 / (2 * np.pi)) + 100) % 1.0 - 0.5) > 0.42) & (r > 7.6) & (r < 9.0) & (q[:, 2] > 2.2)
        mat = np.where(tick & (np.abs(d - bob) < 0.3), INK, mat)
        return self.arms(q, d, mat)

    def face_anchor(self):
        return self._anchor((0, 16.0, -60.0), (40.0, 40.0, 62.9), xs=(-3.0, 3.0)), 0.9


CHARS = {"rivet": Rivet, "varnish": Varnish, "pendle": Pendle}
VCENTRE = {"rivet": 27.0, "varnish": 27.0, "pendle": 18.0}
