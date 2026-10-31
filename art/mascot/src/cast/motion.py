"""Case 2, Motion Mesa: Dash (vector-arrow courier), Rolla (wheel baker), Mu (friction-block slope inspector)."""
import numpy as np

from .. import sdf
from ..palette import BAND, METAL, STEEL, WHITE, INK, COAT, BELT, PAPER, WOOD, HAT, DASH, FLETCH, RUBBER, PIE, PINE, HARDHAT, SKATE
from ..suspects import _Base, _legs, _mask, _put  # noqa: F401

MU_TEX = _mask("μ", 44, 48, 48)


class Dash(_Base):
    """An upright vector arrow: the arrowhead is his head, fletching at his hips, skates for feet."""
    billboard = True
    skin = DASH
    brow_hex = "#4A0C06"
    shoulder = (2.4, 21.5, 0.0)
    front = 3.6

    def eval(self, q):
        q = self._local(q)
        shaft = sdf.capsule(q, (0, 8.0, 0), (0, 31.0, 0), 2.7)
        # arrowhead: a square pyramid (Chebyshev radius) with the base notched into four barbs
        r = np.abs(q[:, 0])
        y = q[:, 1]
        edge = (r * 23.0 + 13.5 * (y - 48.0)) / np.hypot(23.0, 13.5)          # slanted sides, apex at y=48
        notch = -(y - 33.0 + r * 0.62) * 0.85                                    # chevron cut: the barbs hang below
        flat = np.maximum.reduce([edge, notch, 23.0 - y])
        head = np.maximum(flat, np.abs(q[:, 2]) - 3.6 + 0.6 * np.clip(flat + 2.0, 0, 2.0)) - 0.5   # bevelled slab
        d, mat = np.minimum(shaft, head), np.full(len(q), DASH)
        # fletching: two feather wings flaring out at the hips, one at the back
        for side in (-1, 1):
            x = q[:, 0] * side
            wing = np.maximum.reduce([np.abs(q[:, 2] + 1.2) - 0.55, 2.2 - x, x - 9.0,
                                      (y - (18.5 - 0.55 * (x - 2.2))) * 0.85, ((9.5 - 0.55 * (x - 2.2)) - y) * 0.85]) - 0.25
            d, mat = _put(d, mat, wing, FLETCH)
        back = np.maximum.reduce([np.abs(q[:, 0]) - 0.55, -q[:, 2] - 8.0, q[:, 2] + 2.0,
                                  y - (18.5 + 0.4 * (q[:, 2] + 2.0)), (9.5 + 0.4 * (q[:, 2] + 2.0)) - y]) - 0.25
        d, mat = _put(d, mat, back, FLETCH)
        # legs and roller skates
        for side in (-1, 1):
            leg = sdf.capsule(q, (side * 2.4, 9.0, 0), (side * 3.0, 3.6, 0.4), 1.4)
            boot = sdf.box(q - [side * 3.0, 2.6, 0.9], (1.9, 1.4, 3.4), 1.0)
            d, mat = _put(d, mat, leg, INK)
            d, mat = _put(d, mat, boot, SKATE)
            for z in (-1.6, 3.2):
                wheel = sdf.capsule(q, (side * 3.0 - 1.1, 0.9, z), (side * 3.0 + 1.1, 0.9, z), 0.9)
                d, mat = _put(d, mat, wheel, METAL)
        # courier satchel on a strap
        bag = sdf.box(q - [6.6, 15.5, 1.6], (2.4, 3.2, 2.4), 0.8)
        strap = sdf.capsule(q, (6.0, 18.5, 2.0), (-3.6, 26.0, 3.6), 0.5)
        flap = sdf.box(q - [6.6, 17.6, 2.4], (2.5, 1.2, 2.0), 0.5)
        d, mat = _put(d, mat, bag, COAT)
        d, mat = _put(d, mat, flap, BELT)
        d, mat = _put(d, mat, strap, BELT)
        # racing goggles pushed up on the arrowhead, and a speed stripe down the shaft
        band = np.maximum(np.abs(y - 42.6) - 0.7, np.abs(q[:, 2]) - 4.3)
        d, mat = _put(d, mat, np.maximum(band, edge - 0.6), INK)
        for side in (-1, 1):
            lens = sdf.cylinder_y((q - [side * 2.6, 42.6, 3.9]) @ sdf.rot_x(np.pi / 2), 1.8, 0.7, 0.3)
            d, mat = _put(d, mat, lens, METAL)
        stripe = (np.abs(q[:, 0]) < 0.8) & (q[:, 2] > 1.5) & (y > 9.0) & (y < 22.0)
        mat = np.where(stripe & (mat == DASH), WHITE, mat)
        return self.arms(q, d, mat)

    def face_anchor(self):
        return self._anchor((0, 37.0, 0.0), (7.0, 6.0, 3.6), xs=(-3.0, 3.0)), 0.85


class Rolla(_Base):
    """A cheerful wheel with a pie-crust hub and a baker's toque. Always faces you."""
    billboard = True
    skin = PIE
    brow_hex = "#5A3410"
    shoulder = (15.5, 17.0, 0.0)
    front = 5.0
    glove = BAND

    def eval(self, q):
        q = self._local(q)
        wq = (q - [0, 17.0, 0]) @ sdf.rot_x(np.pi / 2)
        tyre = sdf.torus_y(wq, 13.0, 4.2)
        d, mat = tyre, np.where(np.hypot(q[:, 0], q[:, 1] - 17.0) > 11.5, RUBBER, STEEL)   # rubber tyre, steel rim
        hub = sdf.ellipsoid(q, (0, 17.0, 0.4), (10.8, 10.8, 3.6))
        d, mat = _put(d, mat, hub, PIE)
        for k in range(8):
            a = k * np.pi / 4
            bolt = sdf.sphere(q, (9.6 * np.cos(a), 17.0 + 9.6 * np.sin(a), 1.6), 0.9)
            d, mat = _put(d, mat, bolt, METAL)
        band = sdf.cylinder_y(q - [0, 35.4, 0], 6.4, 2.4, 0.6)
        puff = sdf.ellipsoid(q, (0, 41.0, 0), (8.6, 5.2, 7.2))
        puff = np.minimum(puff, sdf.ellipsoid(q, (-4.6, 40.0, 0.5), (4.2, 4.2, 4.2)))
        puff = np.minimum(puff, sdf.ellipsoid(q, (4.6, 40.0, 0.5), (4.2, 4.2, 4.2)))
        d, mat = _put(d, mat, sdf.smin(band, puff, 1.5), WHITE)
        # crimped crust round the hub, sugar glaze dots and a rolling pin in hand
        ang = np.arctan2(q[:, 1] - 17.0, q[:, 0])
        rr = np.hypot(q[:, 0], q[:, 1] - 17.0)
        crimp = (rr > 8.6) & (rr < 10.6) & (np.sin(ang * 14) > 0.2) & (q[:, 2] > 1.0)
        mat = np.where(crimp & (mat == PIE), WOOD, mat)
        for x, y in ((-3.5, 21.5), (3.8, 21.0), (-5.0, 15.0), (5.2, 13.5), (0.0, 11.0)):
            d, mat = _put(d, mat, sdf.sphere(q, (x, y, 3.7), 0.55), WHITE)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        pin = sdf.capsule(q, h + [-1.0, -0.5, 1.5], h + [6.0, 1.5, 3.0], 1.3)
        knobs = np.minimum(sdf.capsule(q, h + [-1.0, -0.5, 1.5], h + [-3.2, -1.1, 1.0], 0.6),
                           sdf.capsule(q, h + [6.0, 1.5, 3.0], h + [8.2, 2.1, 3.5], 0.6))
        return [(pin, PINE), (knobs, WOOD)]

    def face_anchor(self):
        return self._anchor((0, 17.0, 0), (10.8, 10.8, 4.0), xs=(-3.4, 3.4), dy=1.5), 0.9


class Mu(_Base):
    """A wooden block with a mu carved into it, a yellow hard hat and a clipboard."""
    skin = PINE
    brow_hex = "#3F2410"
    shoulder = (12.5, 18.0, 0.0)
    front = 10.0

    def eval(self, q):
        q = self._local(q)
        block = sdf.box(q - [0, 12.5, 0], (12.0, 12.0, 10.0), 1.8)
        grain = np.sin(q[:, 1] * 1.25 + 1.6 * np.sin(q[:, 0] * 0.22 + q[:, 2] * 0.15)) > 0.72
        grain &= ~((q[:, 2] > 7.0) & (np.abs(q[:, 0]) < 9.5) & (q[:, 1] > 14.5) & (q[:, 1] < 24.5))   # keep the face clean
        d, mat = block, np.where(grain, WOOD, PINE)
        u = np.clip(((q[:, 0] + 9.0) / 18.0 * 47), 0, 47).astype(int)
        v = np.clip(((15.0 - q[:, 1]) / 16.0 * 47), 0, 47).astype(int)
        carve = (q[:, 2] > 9.0) & (np.abs(q[:, 0]) < 9.0) & (q[:, 1] > -1.0) & (q[:, 1] < 15.0) & MU_TEX[v, u]
        mat = np.where(carve, HAT, mat)
        dome = np.maximum(sdf.ellipsoid(q, (0, 25.0, 0), (8.8, 6.2, 8.0)), 25.0 - q[:, 1])
        brim = sdf.ellip_cylinder_y(q - [0, 25.2, 0.8], 11.2, 10.4, 0.7, 0.5)
        ridge = np.maximum(sdf.box(q - [0, 28.0, 0], (1.2, 3.4, 8.2), 0.6), 25.0 - q[:, 1])
        d, mat = _put(d, mat, sdf.smin(dome, brim, 0.8), HARDHAT)
        d, mat = _put(d, mat, np.maximum(ridge, sdf.ellipsoid(q, (0, 25.0, 0), (9.6, 7.0, 8.8))), HARDHAT)
        # a pencil behind the hard-hat brim, a tape measure on the hip
        d, mat = _put(d, mat, sdf.capsule(q, (-7.5, 24.2, 6.5), (-11.5, 23.4, 3.0), 0.55), HARDHAT)
        tape = sdf.cylinder_y((q - [-12.6, 6.0, 2.0]) @ sdf.rot_z(np.pi / 2), 2.4, 1.0, 0.5)
        d, mat = _put(d, mat, tape, BAND)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        board = sdf.box(q - (h + [0.0, 1.5, 2.2]), (3.6, 4.8, 0.5), 0.3)
        clip = sdf.box(q - (h + [0.0, 6.0, 2.4]), (1.6, 0.8, 0.6), 0.3)
        lines = (np.abs(((q[:, 1] - h[1]) % 1.6) - 0.8) < 0.25) & (np.abs(q[:, 0] - h[0]) < 2.6)
        return [(board, np.where(lines, STEEL, PAPER)), (clip, METAL)]

    def face_anchor(self):
        return self._anchor((0, 19.5, 0), (17.0, 14.0, 10.0), xs=(-4.0, 4.0)), 0.9


CHARS = {"dash": Dash, "rolla": Rolla, "mu": Mu}
VCENTRE = {"dash": 33.0, "rolla": 22.0, "mu": 17.0}
