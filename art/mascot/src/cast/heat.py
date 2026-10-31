"""Case 7, Kelvin Springs: Al (aluminium saucepan chef), Ferris (cast-iron radiator boilerman), Brewster (copper kettle)."""
import numpy as np

from .. import sdf
from .. import palette as P
from ..palette import METAL, WHITE, INK, BAND, WOOD, PAPER
from ..suspects import _Base, _legs, _put  # noqa: F401

ALU = P.register(["#3E4652", "#66707E", "#949EAC", "#C4CCD6", "#EEF2F8"], specular="#FFFFFF")
RUST = P.register(["#2A1210", "#46201A", "#663024", "#864432", "#A65C44"], specular="#E8B8A0")
VALVE = P.register(["#4A0A08", "#8E1A14", "#C9302A", "#EE5A4C", "#FF9C8C"], specular="#FFFFFF")
KETTLE = P.register(["#4A1C0A", "#7A3214", "#AC5022", "#D87434", "#F6A060"], specular="#FFEAD0")
STEAM = P.register(["#9AA4B4", "#B8C2D0", "#D6DEE8", "#EEF2F8", "#FFFFFF"])
CHINA = P.register(["#8A96B4", "#AEB8D2", "#D0D8EC", "#ECF0FA", "#FFFFFF"], specular="#FFFFFF")


class Al(_Base):
    """An aluminium saucepan: the pan is the body, the long handle a ponytail, steam curling off the top."""
    skin = ALU
    brow_hex = "#2A303A"
    shoulder = (10.4, 15.0, 0.0)
    front = 10.4

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.2, 5.0), np.full(len(q), INK)
        pan = sdf.cylinder_y(q - [0, 15.0, 0], 10.4, 9.4, 1.6)
        d, mat = _put(d, mat, pan, ALU)
        rim = sdf.torus_y(q - [0, 24.4, 0], 10.4, 1.0)
        d, mat = _put(d, mat, rim, ALU)
        inside = sdf.cylinder_y(q - [0, 24.6, 0], 9.2, 0.3)
        d, mat = _put(d, mat, inside, INK)
        handle = sdf.capsule(q, (-9.0, 21.0, -3.0), (-21.0, 24.0, -7.0), 1.4)
        d, mat = _put(d, mat, handle, INK)
        d, mat = _put(d, mat, sdf.sphere(q, (-21.6, 24.2, -7.2), 1.8), BAND)
        for x, y, r in ((-2.0, 28.0, 2.6), (1.6, 31.6, 2.2), (-0.8, 35.0, 1.8)):
            d, mat = _put(d, mat, sdf.sphere(q, (x, y, 0.0), r), STEAM)
        # a red neckerchief knotted below the face
        kq = q - [0, 9.0, 10.2]
        knot = sdf.ellipsoid(q, (0, 8.6, 10.6), (2.2, 1.6, 1.0))
        tails = np.minimum(sdf.round_cone(q, (0, 8.0, 10.6), (-2.2, 4.0, 10.6), 1.0, 0.5), sdf.round_cone(q, (0, 8.0, 10.6), (2.0, 4.4, 10.6), 1.0, 0.5))
        d, mat = _put(d, mat, np.minimum(knot, tails), BAND)
        del kq
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != 1:
            return []
        return [(sdf.capsule(q, h + [0, -2.0, 0.6], h + [0.8, 6.0, 1.8], 0.55), WOOD),
                (sdf.ellipsoid(q, h + [0.9, 7.6, 2.0], (1.4, 2.0, 0.7)), WOOD)]

    def face_anchor(self):
        return self._anchor((0, 16.0, 0), (10.4, 9.4, 10.4), xs=(-3.4, 3.4)), 0.88


class Ferris(_Base):
    """A cast-iron radiator: a row of rounded fins, a smooth front panel for a face, a red valve wheel on top."""
    skin = RUST
    brow_hex = "#1A0A08"
    shoulder = (12.4, 16.0, 0.0)
    front = 6.0

    def eval(self, q):
        q = self._local(q)
        d, mat = np.full(len(q), 1e9), np.full(len(q), RUST)
        for k in range(7):
            x = -10.8 + 3.6 * k
            fin = sdf.capsule(q, (x, 5.0, 0), (x, 25.0, 0), 2.3)
            d = sdf.smin(d, fin, 0.8)
        top = sdf.box(q - [0, 26.6, 0], (12.6, 1.4, 2.6), 0.8)
        bot = sdf.box(q - [0, 4.0, 0], (12.6, 1.4, 2.6), 0.8)
        d = np.minimum(d, np.minimum(top, bot))
        mat = np.full(len(q), RUST)
        panel = sdf.box(q - [0, 16.0, 2.6], (7.6, 7.0, 0.8), 1.6)
        d, mat = _put(d, mat, panel, RUST)
        for sx in (-1, 1):
            leg = sdf.box(q - [sx * 9.0, 1.4, 0], (1.8, 1.6, 2.2), 0.6)
            d, mat = _put(d, mat, leg, INK)
        # pipe out the side and the valve wheel on top
        d, mat = _put(d, mat, sdf.capsule(q, (12.6, 6.0, 0), (16.0, 6.0, 0), 1.4), METAL)
        d, mat = _put(d, mat, sdf.capsule(q, (8.0, 28.0, 0), (8.0, 31.0, 0), 0.8), METAL)
        wheel = sdf.torus_y(q - [8.0, 31.6, 0], 2.8, 0.7)
        spokes = np.minimum(sdf.box(q - [8.0, 31.6, 0], (2.6, 0.4, 0.4)), sdf.box(q - [8.0, 31.6, 0], (0.4, 0.4, 2.6)))
        d, mat = _put(d, mat, np.minimum(wheel, spokes), VALVE)
        for x, y, r in ((-6.0, 31.0, 1.8), (-4.0, 34.6, 1.4)):
            d, mat = _put(d, mat, sdf.sphere(q, (x, y, 0.0), r), STEAM)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        # a big spanner
        return [(sdf.capsule(q, h + [0, -1.0, 0.6], h + [0.4, 7.0, 1.4], 0.7), METAL),
                (np.maximum(sdf.torus_y((q - (h + [0.5, 8.4, 1.5])) @ sdf.rot_x(np.pi / 2), 1.6, 0.6), -(q[:, 1] - h[1] - 8.0)), METAL)]

    def face_anchor(self):
        return self._anchor((0, 16.0, 2.0), (7.6, 7.0, 2.8), xs=(-2.8, 2.8)), 0.86


class Brewster(_Base):
    """A copper kettle with a whistling spout, a handle arched over the top, a bow tie and a cup of tea."""
    skin = KETTLE
    brow_hex = "#3A1404"
    shoulder = (10.8, 14.0, 0.0)
    front = 11.0

    def eval(self, q):
        q = self._local(q)
        d, mat = _legs(q, 3.2, 4.0), np.full(len(q), INK)
        body = sdf.ellipsoid(q, (0, 14.0, 0), (11.6, 10.4, 11.0))
        base = sdf.cylinder_y(q - [0, 4.6, 0], 8.6, 1.0, 0.6)
        d, mat = _put(d, mat, sdf.smin(body, base, 1.5), KETTLE)
        lid = sdf.ellipsoid(q, (0, 23.6, 0), (6.6, 2.0, 6.6))
        knob = sdf.sphere(q, (0, 26.4, 0), 1.6)
        d, mat = _put(d, mat, lid, KETTLE)
        d, mat = _put(d, mat, knob, INK)
        spout = sdf.round_cone(q, (8.0, 12.0, 4.0), (15.0, 21.0, 6.0), 2.6, 1.2)
        d, mat = _put(d, mat, spout, KETTLE)
        whistle = sdf.cylinder_y((q - [15.6, 22.2, 6.2]) @ sdf.rot_z(-0.6), 1.5, 1.2, 0.4)
        d, mat = _put(d, mat, whistle, METAL)
        hq = (q - [0, 24.0, 0]) @ sdf.rot_x(np.pi / 2)
        handle = np.maximum(sdf.torus_y(hq, 7.4, 1.0), -(q[:, 1] - 24.0))
        d, mat = _put(d, mat, handle, INK)
        bow = np.minimum(sdf.ellipsoid(q, (-2.0, 6.4, 10.2), (2.0, 1.4, 0.8)), sdf.ellipsoid(q, (2.0, 6.4, 10.2), (2.0, 1.4, 0.8)))
        d, mat = _put(d, mat, np.minimum(bow, sdf.sphere(q, (0, 6.4, 10.6), 0.9)), BAND)
        return self.arms(q, d, mat)

    def held(self, q, h, side):
        if side != -1:
            return []
        cup = np.maximum(sdf.cylinder_y(q - (h + [0.6, 2.6, 2.0]), 2.0, 1.4, 0.4), -sdf.cylinder_y(q - (h + [0.6, 3.6, 2.0]), 1.5, 1.2))
        saucer = sdf.cylinder_y(q - (h + [0.6, 1.0, 2.0]), 3.0, 0.3, 0.2)
        return [(np.minimum(cup, saucer), CHINA)]

    def face_anchor(self):
        return self._anchor((0, 15.0, 0), (11.6, 10.4, 11.0), xs=(-3.4, 3.4)), 0.9


CHARS = {"al": Al, "ferris": Ferris, "brewster": Brewster}
VCENTRE = {"al": 18.0, "ferris": 18.0, "brewster": 17.0}
