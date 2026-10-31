"""Case 8, Acid Alley: Citrine (lemon cordial seller), Bicarb (baking-soda baker), Sudsy (soap-flake laundress)."""
import numpy as np

from .. import sdf
from .. import palette as P
from ..palette import METAL, WHITE, INK, BAND, WOOD
from ..suspects import _Base, _legs, _put  # noqa: F401

LEMON = P.register(["#7A5A08", "#B8880E", "#E6B820", "#F8DA4A", "#FFF0A0"], specular="#FFFCE0")
STRAW = P.register(["#6A4A18", "#9C7228", "#C89A40", "#E4C068", "#F6DE9A"])
CORDIAL = P.register(["#8A6A08", "#C89A10", "#F2C62A", "#FCE070", "#FFF4B8"], specular="#FFFFFF")
TIN = P.register(["#6A2C10", "#A0461A", "#D06A2A", "#F09048", "#FFBA78"], specular="#FFE6D0")
RIBBON = P.register(["#0E2A14", "#17421F", "#22602C", "#30823C", "#48A452"])
MITT = P.register(["#4A0A20", "#7A1434", "#B0244E", "#DA4672", "#F47AA0"])
SOAP = P.register(["#7A2A4A", "#B04672", "#D86C98", "#F29ABC", "#FFC8DE"], specular="#FFFFFF")
BUBBLE = P.register(["#6A8AB8", "#9AB8DC", "#C8DEF2", "#EAF4FF", "#FFFFFF"], specular="#FFFFFF")


class Citrine(_Base):
    """A lemon with pointed ends, a dimpled rind, a straw hat with a green band, and a glass of cordial."""
    skin = LEMON
    brow_hex = "#5A4004"
    shoulder = (9.6, 15.0, 0.0)
    front = 10.0

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.0, 5.0), np.full(len(q), INK)
        body = sdf.ellipsoid(q, (0, 16.0, 0), (10.4, 11.4, 10.0))
        nubs = np.minimum(sdf.round_cone(q, (0, 26.0, 0), (0, 29.4, 0), 2.6, 0.8), sdf.round_cone(q, (0, 6.0, 0), (0, 3.4, 0), 2.6, 0.9))
        rind = body + 0.18 * (np.sin(q[:, 0] * 3.1) * np.sin(q[:, 1] * 2.9) * np.sin(q[:, 2] * 3.3) > 0.3)
        d, mat = _put(d, mat, sdf.smin(rind, nubs, 1.6), LEMON)
        # the straw hat, tipped back
        hq = (q - [0, 27.0, -1.0]) @ sdf.rot_x(-0.25)
        brim = sdf.ellipsoid(hq, (0, 0, 0), (12.4, 0.8, 11.6))
        crown = sdf.cylinder_y(hq - [0, 2.6, 0], 5.6, 2.6, 1.4)
        d, mat = _put(d, mat, np.minimum(brim, crown), STRAW)
        band = np.maximum(sdf.cylinder_y(hq - [0, 1.6, 0], 5.8, 0.8, 0.3), -sdf.cylinder_y(hq - [0, 1.6, 0], 5.0, 2.0))
        d, mat = _put(d, mat, band, RIBBON)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        glass = np.maximum(sdf.cylinder_y(q - (h + [0.6, 3.0, 2.0]), 1.8, 2.6, 0.3), -sdf.cylinder_y(q - (h + [0.6, 4.6, 2.0]), 1.4, 2.0))
        drink = sdf.cylinder_y(q - (h + [0.6, 2.6, 2.0]), 1.5, 1.6, 0.2)
        straw = sdf.capsule(q, h + [1.0, 3.0, 2.0], h + [1.8, 7.0, 2.4], 0.3)
        return [(glass, BUBBLE), (drink, CORDIAL), (straw, BAND)]

    def face_anchor(self):
        return self._anchor((0, 15.0, 0), (10.4, 11.4, 10.0), xs=(-3.4, 3.4)), 0.88


class Bicarb(_Base):
    """A round tin of baking soda: orange label with bubbles, a lid with a puff of flour, oven-mitt hands, a whisk."""
    skin = TIN
    brow_hex = "#3A1404"
    shoulder = (9.4, 16.0, 0.0)
    front = 9.4
    glove = MITT

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.2, 4.0), np.full(len(q), INK)
        tin = sdf.cylinder_y(q - [0, 15.0, 0], 9.4, 11.0, 1.4)
        bub = (np.sin(q[:, 0] * 1.6) * np.sin(q[:, 1] * 1.4 + 1.0) > 0.88) & (q[:, 1] < 9.0)
        d, mat = _put(d, mat, tin, np.where(bub, WHITE, TIN))
        for y in (4.6, 25.4):
            d, mat = _put(d, mat, sdf.torus_y(q - [0, y, 0], 9.4, 0.8), METAL)
        lid = sdf.cylinder_y(q - [0, 27.0, 0], 9.0, 1.0, 0.6)
        d, mat = _put(d, mat, lid, METAL)
        for x, y, z, r in ((-2.5, 29.4, 1.0, 2.6), (2.4, 29.8, -1.0, 2.2), (0.0, 31.6, 0.4, 1.8)):
            d, mat = _put(d, mat, sdf.sphere(q, (x, y, z), r), WHITE)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != 1:
            return []
        loops = np.full(len(q), 1e9)
        for a in (0.0, 1.05, 2.1):
            lq = (q - (h + [0.6, 7.0, 1.6])) @ sdf.rot_y(a) @ sdf.rot_x(np.pi / 2)
            loops = np.minimum(loops, np.maximum(sdf.torus_y(lq * [1, 1, 0.6], 2.0, 0.25), -1e9))
        return [(sdf.capsule(q, h + [0, -1.0, 0.4], h + [0.6, 4.0, 1.6], 0.6), WOOD), (loops, METAL)]

    def face_anchor(self):
        return self._anchor((0, 17.0, 0), (9.4, 11.0, 9.4), xs=(-3.2, 3.2)), 0.88


class Sudsy(_Base):
    """A pink bar of soap standing on end, bubbles foaming off her top, a scrubbing brush in hand."""
    skin = SOAP
    brow_hex = "#5A1A34"
    shoulder = (9.0, 16.0, 0.0)
    front = 6.4

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.0, 4.0), np.full(len(q), INK)
        bar = sdf.box(q - [0, 15.0, 0], (9.0, 11.0, 6.0), 4.0)
        groove = np.maximum(np.abs(sdf.box(q - [0, 15.0, 5.4], (6.6, 8.6, 1.0), 3.0)) - 0.35, -q[:, 2] + 4.6)
        d, mat = _put(d, mat, np.maximum(bar, -groove), SOAP)
        for x, y, z, r in ((-4.0, 27.4, 1.0, 3.0), (1.2, 28.6, -0.6, 3.6), (5.4, 27.0, 1.2, 2.4), (-0.6, 32.6, 0.6, 2.2), (3.0, 34.6, -0.4, 1.4)):
            d, mat = _put(d, mat, sdf.sphere(q, (x, y, z), r), BUBBLE)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        brush = sdf.box(q - (h + [0.4, 2.6, 1.6]), (3.0, 1.4, 1.6), 0.6)
        bristles = sdf.box(q - (h + [0.4, 1.0, 1.6]), (2.6, 0.6, 1.3), 0.2)
        return [(brush, WOOD), (bristles, WHITE)]

    def face_anchor(self):
        return self._anchor((0, 15.0, 0), (9.0, 11.0, 6.4), xs=(-2.8, 2.8)), 0.86


CHARS = {"citrine": Citrine, "bicarb": Bicarb, "sudsy": Sudsy}
VCENTRE = {"citrine": 18.0, "bicarb": 19.0, "sudsy": 19.0}
