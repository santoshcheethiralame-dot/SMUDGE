"""Case 3, Echo Valley: Reverb (gramophone radio host), Thump (marching-drum bandleader), Coil (spring postman)."""
import numpy as np

from .. import sdf
from .. import palette as P
from ..palette import METAL, STEEL, WHITE, INK, NAVY, WOOD, BAND, PAPER, COAT, BELT
from ..suspects import _Base, _legs, _put  # noqa: F401

TEAL = P.register(["#0B3B3A", "#14615E", "#1F8C86", "#3DB8AE", "#86E0D6"], specular="#E6FFFB")
MAGENTA = P.register(["#4A0F3A", "#7A1A60", "#B02C8A", "#DB58B4", "#F59AD8"], specular="#FFE6F6")
SUN = P.register(["#5C4410", "#9C7A1C", "#D9B23A", "#F4D86A", "#FFF2B0"])


class Reverb(_Base):
    """A wooden radio cabinet with a brass gramophone horn flaring up behind it."""
    skin = WOOD
    brow_hex = "#2A1608"
    shoulder = (11.0, 17.0, 0.0)
    front = 8.0

    def eval(self, q):
        q = self._local(q)
        cab = sdf.box(q - [0, 13.0, 0], (10.5, 9.5, 8.0), 1.6)
        d, mat = cab, np.full(len(q), WOOD)
        grille = sdf.box(q - [0, 7.6, 7.6], (7.6, 3.6, 0.7), 0.5)
        d, mat = _put(d, mat, grille, COAT)
        slats = (np.abs(((q[:, 0] + 50) % 2.4) - 1.2) < 0.35) & (np.abs(q[:, 1] - 7.6) < 3.4) & (q[:, 2] > 7.6)
        mat = np.where(slats & (mat == COAT), BELT, mat)
        for x in (-5.0, 5.0):
            d, mat = _put(d, mat, sdf.sphere(q, (x, 3.6, 8.2), 1.1), METAL)
        # the horn: a flared bell from the back of the lid, opening up and forward
        a, b = np.array([1.0, 22.0, -3.0]), np.array([4.0, 39.0, 3.0])
        outer = sdf.round_cone(q, a, b, 1.3, 9.5)
        axis = (b - a) / np.linalg.norm(b - a)
        inner = sdf.round_cone(q, a + axis * 2.5, b + axis * 1.6, 0.4, 8.6)
        horn = np.maximum(outer, -inner)
        d, mat = _put(d, mat, horn, METAL)
        crank = np.minimum(sdf.capsule(q, (0.0, 13.0, -8.6), (1.5, 14.5, -11.5), 0.6), sdf.sphere(q, (1.6, 14.6, -11.8), 1.1))
        d, mat = _put(d, mat, crank, METAL)
        d, mat = _put(d, mat, _legs(q, 4.0, 4.0), INK)
        # a glowing tuning window with its needle, two knobs and an ON AIR lamp on the lid
        win = sdf.box(q - [0, 20.2, 8.3], (5.6, 1.2, 0.5), 0.4)
        d, mat = _put(d, mat, win, SUN)
        d, mat = _put(d, mat, sdf.box(q - [1.2, 20.2, 8.8], (0.3, 1.0, 0.3)), BAND)
        for x in (-8.2, 8.2):
            d, mat = _put(d, mat, sdf.cylinder_y((q - [x, 20.2, 8.4]) @ sdf.rot_x(np.pi / 2), 1.3, 0.8, 0.3), METAL)
        lamp = sdf.ellipsoid(q, (-6.5, 23.6, 3.0), (2.6, 1.4, 1.6))
        d, mat = _put(d, mat, lamp, BAND)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != 1:
            return []
        # a ribbon microphone on a short handle
        return [(sdf.capsule(q, h + [0, 0.5, 0.8], h + [0.6, 3.5, 1.8], 0.55), STEEL),
                (sdf.ellipsoid(q, h + [0.8, 5.4, 2.2], (1.5, 2.0, 1.3)), METAL)]

    def face_anchor(self):
        return self._anchor((0, 16.0, 0), (13.5, 10.0, 8.6), xs=(-3.4, 3.4)), 0.9


class Thump(_Base):
    """A red marching drum with gold lacing, white rims and a tall plumed bandleader's hat."""
    skin = BAND
    brow_hex = "#4A0A08"
    shoulder = (10.4, 19.0, 0.0)
    front = 10.5

    def eval(self, q):
        q = self._local(q)
        shell = sdf.cylinder_y(q - [0, 15.5, 0], 10.5, 8.6, 0.8)
        d, mat = shell, np.full(len(q), BAND)
        ang = np.arctan2(q[:, 2], q[:, 0])
        h = (q[:, 1] - 7.0) / 17.0
        lace = ((np.abs(((ang * 10 / (2 * np.pi) + h) % 1.0) - 0.5) < 0.07) | (np.abs(((ang * 10 / (2 * np.pi) - h) % 1.0) - 0.5) < 0.07))
        lace &= np.abs(ang - np.pi / 2) > 0.75                        # keep the face clear
        mat = np.where(lace & (np.abs(q[:, 1] - 15.5) < 7.6), METAL, mat)
        for y in (7.2, 23.8):
            d, mat = _put(d, mat, sdf.torus_y(q - [0, y, 0], 10.6, 1.4), WHITE)
        head = sdf.cylinder_y(q - [0, 24.4, 0], 9.8, 0.4, 0.2)
        d, mat = _put(d, mat, head, PAPER)
        d, mat = _put(d, mat, _legs(q, 3.6, 7.0), INK)
        shako = sdf.cylinder_y(q - [0, 30.0, 0], 5.6, 5.4, 0.8)
        band = sdf.cylinder_y(q - [0, 26.2, 0], 5.8, 1.0, 0.4)
        peak = np.maximum(sdf.ellip_cylinder_y(q - [0, 25.4, 3.6], 5.8, 4.2, 0.45, 0.3), -q[:, 2] + 2.5)
        plume = sdf.ellipsoid(q, (0, 40.0, -0.5), (2.2, 5.0, 2.2))
        d, mat = _put(d, mat, shako, NAVY)
        d, mat = _put(d, mat, band, METAL)
        d, mat = _put(d, mat, peak, NAVY)
        d, mat = _put(d, mat, plume, WHITE)
        # a gold chinstrap on the shako
        d, mat = _put(d, mat, sdf.box(q - [0, 25.6, 5.7], (3.6, 0.35, 0.3)), METAL)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        # drumsticks, tips up and out
        tip = h + [side * 2.0, 7.5, 3.0]
        return [(sdf.capsule(q, h + [0, -0.8, 0.2], tip, 0.55), PAPER), (sdf.sphere(q, tip, 1.0), PAPER)]

    def face_anchor(self):
        return self._anchor((0, 17.5, 0), (10.5, 9.0, 10.5), xs=(-3.4, 3.4)), 0.9


class Coil(_Base):
    """A rainbow spring for a body, a round teal head, a postman's cap and a mailbag."""
    skin = TEAL
    brow_hex = "#0B3B3A"
    shoulder = (6.4, 25.0, 0.0)
    front = 7.6

    def eval(self, q):
        q = self._local(q)
        d, mat = np.full(len(q), 1e9), np.full(len(q), TEAL)
        cols = (TEAL, MAGENTA, SUN)
        for k in range(8):
            y = 2.2 + 3.1 * k
            lean = 0.7 * np.sin(k * 0.9)
            ring = sdf.torus_y(q - [lean, y, 0], 7.6 - 0.25 * k, 1.55)
            d, mat = _put(d, mat, ring, cols[k % 3])
        headc = sdf.sphere(q, (0, 32.0, 0), 7.4)
        d, mat = _put(d, mat, headc, TEAL)
        cq = q - [0, 38.4, 0]
        cap = sdf.ellip_cylinder_y(cq, 6.6, 6.6, 2.0, 1.4)
        peak = np.maximum(sdf.ellip_cylinder_y(cq - [0, -1.6, 3.6], 6.2, 4.6, 0.45, 0.3), -cq[:, 2] + 1.8)
        badge = sdf.sphere(q, (0, 39.0, 6.4), 1.2)
        d, mat = _put(d, mat, cap, NAVY)
        d, mat = _put(d, mat, peak, NAVY)
        d, mat = _put(d, mat, badge, METAL)
        bag = sdf.box(q - [9.4, 14.0, 2.0], (2.6, 3.6, 3.0), 0.8)
        flap = sdf.box(q - [9.6, 16.4, 2.6], (2.7, 1.3, 2.6), 0.5)
        strap = sdf.capsule(q, (8.6, 17.0, 2.5), (-4.0, 29.0, 4.5), 0.5)
        d, mat = _put(d, mat, bag, COAT)
        d, mat = _put(d, mat, flap, BELT)
        d, mat = _put(d, mat, strap, BELT)
        # stamps on the mailbag
        for y in (12.6, 15.0):
            d, mat = _put(d, mat, sdf.box(q - [9.4, y, 5.1], (1.0, 0.8, 0.3)), BAND if y < 14 else SUN)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        env = sdf.box(q - (h + [0.4, 2.6, 2.0]), (3.4, 2.2, 0.35), 0.2)
        seal = sdf.sphere(q, h + [0.4, 2.6, 2.5], 0.7)
        return [(env, PAPER), (seal, BAND)]

    def face_anchor(self):
        return self._anchor((0, 32.5, 0), (7.4, 7.4, 7.4), xs=(-2.8, 2.8)), 0.85


CHARS = {"reverb": Reverb, "thump": Thump, "coil": Coil}
VCENTRE = {"reverb": 22.0, "thump": 22.0, "coil": 30.0}
