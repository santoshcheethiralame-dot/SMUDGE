"""Case 6, Ohmtown: Volta (battery seller), Ohmar (resistor maker), Glim (light-bulb lamp maker)."""
import numpy as np

from .. import sdf
from .. import palette as P
from ..palette import METAL, WHITE, INK, BAND, STEEL
from ..suspects import _Base, _legs, _put  # noqa: F401

COPPERTOP = P.register(["#5A2408", "#8A3C10", "#BC5C1C", "#E4843A", "#FCB06A"], specular="#FFE2C0")
GRAPHITE = P.register(["#0C0C12", "#18181F", "#26262F", "#383844", "#4E4E5C"], specular="#B8B8D0")
BOLT = P.register(["#7A5A12", "#B8891E", "#E6B43A", "#F8D66E", "#FFF0A8"])
TAN = P.register(["#5A4020", "#86622E", "#B08A48", "#D2AE6A", "#EED092"], specular="#FFF4D8")
BLACKB = P.register(["#08080A", "#121216", "#1E1E24", "#2C2C34", "#3C3C46"])
BULB = P.register(["#8A7A3A", "#BCA858", "#E6D47E", "#FAEEAA", "#FFFCE0"], specular="#FFFFFF")
FILAMENT = P.register(["#B8400E", "#F07018", "#FFA830", "#FFD860", "#FFF6C0"])


class Volta(_Base):
    """A battery: graphite below, a copper top with her face, a terminal on her head and a bolt on her front."""
    skin = COPPERTOP
    brow_hex = "#3A1404"
    shoulder = (9.0, 20.0, 0.0)
    front = 9.4

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.4, 5.0), np.full(len(q), INK)
        body = sdf.cylinder_y(q - [0, 19.0, 0], 9.2, 14.0, 2.2)
        d, mat = _put(d, mat, body, np.where(q[:, 1] > 17.5, COPPERTOP, GRAPHITE))
        ring = sdf.torus_y(q - [0, 17.5, 0], 9.3, 0.6)
        d, mat = _put(d, mat, ring, METAL)
        term = sdf.cylinder_y(q - [0, 34.6, 0], 3.2, 1.8, 0.6)
        d, mat = _put(d, mat, term, METAL)
        d, mat = _put(d, mat, sdf.cylinder_y(q - [0, 33.2, 0], 8.0, 0.4, 0.3), METAL)
        # a lightning bolt on the graphite, and a plus sign on her temple
        pts = [(1.8, 15.6), (-1.6, 10.6), (1.4, 10.0), (-1.8, 4.6)]
        bolt = np.full(len(q), 1e9)
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            bolt = np.minimum(bolt, sdf.capsule(q, (x0, y0, 9.2), (x1, y1, 9.2), 0.9))
        d, mat = _put(d, mat, bolt, BOLT)
        plus = np.minimum(sdf.box(q - [6.2, 29.5, 6.6], (1.6, 0.4, 0.4)), sdf.box(q - [6.2, 29.5, 6.6], (0.4, 1.6, 0.4)))
        d, mat = _put(d, mat, plus, BOLT)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != 1:
            return []
        # a red jump-lead clamp
        return [(sdf.box(q - (h + [0.8, 2.2, 1.0]), (1.0, 2.4, 0.9), 0.4), BAND),
                (sdf.capsule(q, h + [0.8, 4.4, 1.0], h + [1.6, 7.0, 1.4], 0.45), METAL)]

    def face_anchor(self):
        return self._anchor((0, 24.0, 0), (9.2, 9.0, 9.2), xs=(-3.2, 3.2)), 0.88


class Ohmar(_Base):
    """A resistor standing on end: a tan dog-bone body, colour bands for 20 ohms, a wire lead curling up top."""
    skin = TAN
    brow_hex = "#3A2408"
    shoulder = (6.6, 20.0, 0.0)
    front = 7.0

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 2.6, 6.0), np.full(len(q), INK)
        body = sdf.capsule(q, (0, 12.0, 0), (0, 30.0, 0), 6.4)
        ends = np.minimum(sdf.sphere(q, (0, 10.0, 0), 7.6), sdf.sphere(q, (0, 32.0, 0), 7.6))
        b = sdf.smin(body, ends, 2.5)
        # red, black, black, gold: twenty ohms. Two bands under the face, two over it
        y = q[:, 1]
        band = np.where(np.abs(y - 8.0) < 1.1, BAND, np.where(np.abs(y - 11.6) < 1.1, BLACKB,
                        np.where(np.abs(y - 33.6) < 1.1, BLACKB, np.where(np.abs(y - 36.4) < 0.9, BOLT, TAN))))
        d, mat = _put(d, mat, b, band)
        # the wire lead out of the top, curling over
        t = np.linspace(0, 1, 7)
        pts = [(2.4 * np.sin(k * 3.0), 39.0 + 6.0 * k, 2.4 * np.cos(k * 3.0) - 2.4) for k in t]
        for a, c in zip(pts[:-1], pts[1:]):
            d, mat = _put(d, mat, sdf.capsule(q, a, c, 0.55), STEEL)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        # a soldering iron
        return [(sdf.capsule(q, h + [0, -1.0, 0.6], h + [0.6, 4.6, 1.6], 0.9), BAND),
                (sdf.round_cone(q, h + [0.6, 4.6, 1.6], h + [1.0, 8.4, 2.4], 0.6, 0.15), METAL)]

    def face_anchor(self):
        return self._anchor((0, 22.0, 0), (7.0, 12.0, 7.0), xs=(-2.6, 2.6)), 0.84


class Glim(_Base):
    """A light bulb: a glowing glass globe for a head, a filament above the eyes, a threaded brass base."""
    skin = BULB
    brow_hex = "#5A4A10"
    shoulder = (5.2, 15.0, 0.0)
    front = 6.0

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 2.6, 5.0), np.full(len(q), INK)
        base = sdf.cylinder_y(q - [0, 11.0, 0], 5.6, 5.4, 0.8)
        thread = np.abs(((q[:, 1] + 0.3 * np.arctan2(q[:, 2], q[:, 0]) + 100) % 1.8) - 0.9) < 0.35
        d, mat = _put(d, mat, base, np.where(thread, STEEL, METAL))
        tip = sdf.sphere(q, (0, 5.2, 0), 2.6)
        d, mat = _put(d, mat, tip, BLACKB)
        neck = sdf.round_cone(q, (0, 16.4, 0), (0, 22.0, 0), 5.8, 8.4)
        globe = sdf.sphere(q, (0, 28.0, 0), 11.0)
        d, mat = _put(d, mat, sdf.smin(neck, globe, 3.0), BULB)
        # the filament, glowing, in the top of the globe
        pts = [(-5.0, 33.0), (-3.0, 36.0), (-1.0, 33.0), (1.0, 36.0), (3.0, 33.0), (5.0, 36.0)]
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
            d, mat = _put(d, mat, sdf.capsule(q, (x0, y0, 9.0), (x1, y1, 9.0 - 0.4 * abs(x1)), 0.5), FILAMENT)
        return self.arms(q, d, mat)

    def face_anchor(self):
        return self._anchor((0, 25.0, 0), (11.0, 11.0, 11.0), xs=(-3.4, 3.4), dy=0.0), 0.9


CHARS = {"volta": Volta, "ohmar": Ohmar, "glim": Glim}
VCENTRE = {"volta": 24.0, "ohmar": 25.0, "glim": 27.0}
