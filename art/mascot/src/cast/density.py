"""Case 1, Buoyant Bay: Karat (diamond jeweller), Cyl (measuring-cylinder harbour master), Bob (buoy)."""
import numpy as np

from .. import sdf
from ..palette import GEM, GLASS, WATER, NAVY, METAL, BAND, WHITE, INK, STEEL, PAPER, WOOD
from ..suspects import _Base, _legs, _mask, _put  # noqa: F401


class Karat(_Base):
    """A brilliant-cut diamond on tiny legs, with a gold monocle."""
    skin = GEM
    brow_hex = "#1E4C63"
    shoulder = (10.0, 22.0, 0.5)
    front = 10.0

    def eval(self, q):
        q = self._local(q)
        c = np.array([0, 24.0, 0])
        lq = (q - c) @ sdf.rot_y(0.39)
        ang = np.arctan2(lq[:, 2], lq[:, 0])
        k = np.round(ang / (np.pi / 4)) * (np.pi / 4)
        rad = lq[:, 0] * np.cos(k) + lq[:, 2] * np.sin(k)
        crown = np.maximum(rad - 11.5, np.maximum(lq[:, 1] - 6.0, -lq[:, 1]))
        crown = np.maximum(crown, (rad * 0.55 + lq[:, 1]) - 9.6)
        pav = np.maximum(rad - 11.5 * np.clip((lq[:, 1] + 13.0) / 13.0, 0, 1), np.maximum(lq[:, 1], -lq[:, 1] - 13.0))
        gem = np.minimum(crown, pav) * 0.8
        d, mat = gem, np.full(len(q), GEM)
        legs = _legs(q, 2.6, 13.0)
        mat = np.where(legs < d, INK, mat)
        d = np.minimum(d, legs)
        mono = sdf.torus_y((q - [3.2, 27.0, 8.6]) @ sdf.rot_x(np.pi / 2), 2.6, 0.55)
        chain = sdf.capsule(q, (5.6, 26.0, 8.0), (8.5, 19.0, 6.0), 0.35)
        m2 = np.minimum(mono, chain)
        mat = np.where(m2 < d, METAL, mat)
        d = np.minimum(d, m2)
        # a gold collet round the girdle, with four claws gripping the crown
        d, mat = _put(d, mat, sdf.torus_y(q - [0, 24.0, 0], 11.3, 0.75), METAL)
        for k in range(4):
            a = np.pi / 4 + k * np.pi / 2
            claw = sdf.capsule(q, (11.0 * np.cos(a), 23.6, 11.0 * np.sin(a)), (8.6 * np.cos(a), 28.6, 8.6 * np.sin(a)), 0.7)
            d, mat = _put(d, mat, claw, METAL)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        # a jeweller's loupe: a little brass barrel
        return [(sdf.capsule(q, h + [0.4, 1.6, 0.6], h + [0.4, 4.4, 1.6], 1.2), METAL)]

    def face_anchor(self):
        return self._anchor((0, 26.0, 0), (11.5, 8.0, 10.4), xs=(-3.2, 3.2)), 0.85


class Cyl(_Base):
    """A measuring cylinder with water inside and a harbour master's cap."""
    skin = GLASS
    brow_hex = "#1C3D63"
    shoulder = (8.0, 27.0, 0.0)
    front = 8.0

    def eval(self, q):
        q = self._local(q)
        tube = sdf.cylinder_y(q - [0, 23.0, 0], 8.0, 17.0, 1.2)
        inner = sdf.cylinder_y(q - [0, 25.0, 0], 6.8, 17.0, 0.8)
        glass = np.maximum(tube, -inner)
        water = sdf.cylinder_y(q - [0, 14.5, 0], 6.9, 8.5, 0.6)
        base = sdf.cylinder_y(q - [0, 3.0, 0], 10.5, 1.5, 0.8)
        spout = sdf.capsule(q, (6.8, 40.0, 0), (10.0, 41.0, 0), 1.0)
        d, mat = glass, np.full(len(q), GLASS)
        for dd, mm in ((water, WATER), (base, GLASS), (spout, GLASS)):
            mat = np.where(dd < d, mm, mat)
            d = np.minimum(d, dd)
        for y in (8, 12, 16, 20, 24):
            mark = sdf.box(q - [-4.2, y, 7.9], (2.0 if y % 8 == 0 else 1.2, 0.35, 0.4))
            mat = np.where(mark < d, WHITE, mat)
            d = np.minimum(d, mark)
        cq = q - [0, 42.5, 0]
        cap = sdf.ellip_cylinder_y(cq, 8.6, 8.6, 2.4, 1.6)
        peak = np.maximum(sdf.ellip_cylinder_y(cq - [0, -1.8, 4.5], 8.0, 6.0, 0.5, 0.3), -cq[:, 2] + 2.0)
        badge = sdf.sphere(q, (0, 43.0, 8.4), 1.5)
        mat = np.where(cap < d, NAVY, mat)
        d = np.minimum(d, cap)
        mat = np.where(peak < d, NAVY, mat)
        d = np.minimum(d, peak)
        mat = np.where(badge < d, METAL, mat)
        d = np.minimum(d, badge)
        # bubbles rising through the water, a lanyard and whistle, a rope fender round the base
        for x, y, z, r in ((-2.5, 9.0, 3.0, 0.9), (1.8, 13.0, 4.0, 0.7), (-0.6, 17.5, 4.6, 0.6), (3.0, 20.0, 3.4, 0.5)):
            d, mat = _put(d, mat, sdf.sphere(q, (x, y, z), r), WHITE)
        lan = sdf.torus_y((q - [0, 28.0, 1.2]) @ sdf.rot_x(0.35), 7.9, 0.35)
        d, mat = _put(d, mat, np.maximum(lan, -q[:, 2] + 2.0), BAND)
        d, mat = _put(d, mat, sdf.capsule(q, (0, 24.2, 8.9), (1.8, 23.6, 9.4), 0.8), METAL)
        rope = sdf.torus_y(q - [0, 4.6, 0], 9.6, 1.1)
        d, mat = _put(d, mat, rope, np.where(np.sin(np.arctan2(q[:, 2], q[:, 0]) * 18 + q[:, 1] * 3) > 0, PAPER, WOOD))
        return self.arms(q, d, mat)

    def face_anchor(self):
        return self._anchor((0, 33.0, 0), (8.0, 10.0, 8.0), xs=(-2.6, 2.6)), 0.85


class Bob(_Base):
    """A red-and-white buoy with a brass bell on a little mast."""
    skin = WHITE
    brow_hex = "#6F7584"
    shoulder = (11.0, 17.0, 0.0)
    front = 11.5
    glove = NAVY

    def eval(self, q):
        q = self._local(q)
        body = sdf.ellipsoid(q, (0, 15.0, 0), (11.5, 12.5, 11.5))
        stripe = (np.floor((q[:, 1] - 3.0) / 6.0) % 2 == 0) & (np.abs(q[:, 1] - 21.0) > 3.4)
        mat = np.where(stripe, BAND, WHITE)
        d = body
        mast = sdf.capsule(q, (0, 26, 0), (0, 34, 0), 0.9)
        cage = np.maximum(np.abs(sdf.sphere(q, (0, 37.5, 0), 4.2)) - 0.5, np.abs(q[:, 1] - 37.0) - 3.0)
        bell = sdf.round_cone(q, (0, 39.0, 0), (0, 34.0, 0), 1.6, 3.4)
        bell = np.maximum(bell, -sdf.cylinder_y(q - [0, 33.0, 0], 2.6, 1.2, 0.2))
        for dd, mm in ((mast, STEEL), (cage, STEEL), (bell, METAL)):
            mat = np.where(dd < d, mm, mat)
            d = np.minimum(d, dd)
        # a pennant on the mast, a bolted collar and a mooring chain trailing from the base
        flag = np.maximum.reduce([np.abs(q[:, 2]) - 0.35, -q[:, 0] + 0.6, q[:, 0] - 6.5,
                                  np.abs(q[:, 1] - 42.0) - 2.4 * (1 - q[:, 0] / 7.0)])
        d, mat = _put(d, mat, sdf.capsule(q, (0, 38.0, 0), (0, 45.0, 0), 0.45), STEEL)
        d, mat = _put(d, mat, flag, BAND)
        d, mat = _put(d, mat, sdf.torus_y(q - [0, 4.6, 0], 8.8, 1.0), STEEL)
        for k in range(3):
            link = sdf.torus_y((q - [-7.5 - 2.3 * k, 1.2, 4.0]) @ sdf.rot_x(np.pi / 2 * (k % 2)), 1.2, 0.45)
            d, mat = _put(d, mat, link, STEEL)
        return self.arms(q, d, mat)

    def face_anchor(self):
        return self._anchor((0, 15.0, 0), (11.5, 12.5, 11.5), xs=(-3.6, 3.6), dy=6.0), 0.9


CHARS = {"karat": Karat, "cyl": Cyl, "bob": Bob}
VCENTRE = {"karat": 25.0, "cyl": 29.0, "bob": 21.0}
