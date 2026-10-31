"""Suspects as SDF characters, same pipeline and lighting as Smudge.

Shared parts live here; each case's cast lives in src/cast/<kit>.py with its own CHARS and VCENTRE,
and is found automatically. A new case adds a file there and touches nothing else."""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import sdf
from .palette import INK, WHITE
from .rig import Pose


def _legs(q, x=2.6, top=7.0):
    d = None
    for side in (-1, 1):
        leg = sdf.capsule(q, (side * x, top, 0), (side * x, 1.6, 0.4), 1.5)
        foot = sdf.ellipsoid(q, (side * x, 1.2, 1.2), (2.2, 1.2, 2.8))
        x_ = np.minimum(leg, foot)
        d = x_ if d is None else np.minimum(d, x_)
    return d


TAU = 2 * np.pi


class _Base:
    billboard = False
    shoulder = None          # (x, y, z) of the right shoulder in body space; None means no arms
    front = 8.0              # how far the body reaches toward the viewer, so wrung hands sit in front of it
    glove = WHITE

    def __init__(self, pose: Pose):
        self.p = pose
        e = pose.extra
        self.bob = e.get("bob", 0.0)
        self.tilt = e.get("tilt", 0.0)
        self.squash = e.get("squash", 1.0)
        self.gesture = e.get("arm", "rest")
        self.phase = e.get("ph", 0.0)
        self.amount = e.get("amt", 1.0)

    def hand(self, side):
        """Where a hand goes for the current gesture. side +1 is the character's right."""
        sx, sy, _ = self.shoulder
        g, t, s = self.gesture, self.phase, side
        rest = np.array([s * (sx + 2.6), sy - 8.5 + 0.4 * np.sin(TAU * t), 1.5])
        if g == "talk" and s == 1:
            return np.array([sx + 5.0, sy + 2.5 + 2.2 * np.sin(2 * TAU * t), 5.5])
        if g == "wring":
            return np.array([s * 2.4 + 0.9 * np.sin(2 * TAU * t + s), sy - 6.5, self.front + 2.5])
        if g == "up":
            return rest + self.amount * (np.array([s * (sx + 5.5), sy + 10.0, 2.0]) - rest)
        if g == "hips":
            return np.array([s * (sx + 0.8), sy - 5.0, 0.8])
        if g == "point" and s == 1:
            return np.array([sx + 8.5, sy + 3.5, 6.0])
        return rest

    def held(self, q, h, side):
        """Something the character carries in a hand: a list of (distance, material)."""
        return []

    def arms(self, q, d, mat):
        """Rubber-hose ink arms ending in cartoon gloves, posed by pose.extra['arm']."""
        if self.shoulder is None:
            return d, mat
        sx, sy, sz = self.shoulder
        for s in (-1, 1):
            S, H = np.array([s * sx, sy, sz]), self.hand(s)
            bend = np.array([s * 5.0, 1.0, -1.0]) if self.gesture == "hips" else np.array([s * 2.6, -1.6, 0.0])
            E = (S + H) / 2 + bend
            arm = np.minimum(sdf.capsule(q, S, E, 0.95), sdf.capsule(q, E, H, 0.95))
            d, mat = _put(d, mat, arm, INK)
            glove = sdf.smin(sdf.ellipsoid(q, H, (2.2, 2.0, 1.9)), sdf.sphere(q, H + [-s * 1.5, 1.2, 0.8], 0.9), 0.6)
            cuff = sdf.torus_y((q - (H + [0, -1.7, 0])), 1.6, 0.55)
            d, mat = _put(d, mat, np.minimum(glove, cuff), self.glove)
            for dd, mm in self.held(q, H, s):
                d, mat = _put(d, mat, dd, mm)
        return d, mat

    def _local(self, q):
        q = q - np.array([0, self.bob, 0])
        q = q @ sdf.rot_z(self.tilt)
        q = q.copy()
        q[:, 1] /= self.squash
        return q

    def head_dir(self, v):
        return np.asarray(v)

    def _anchor(self, c, r, xs=(-3.0, 3.0), dy=0.0):
        pts = []
        for x in xs:
            y = dy
            z = r[2] * np.sqrt(max(1 - (x / r[0]) ** 2 - (y / r[1]) ** 2, 0.05))
            pt = np.array(c, float) + np.array([x, y, z])
            n = np.array([x / r[0] ** 2, y / r[1] ** 2, z / r[2] ** 2])
            pt = pt * np.array([1, self.squash, 1]) + np.array([0, self.bob, 0])
            pts.append((pt, n / np.linalg.norm(n)))
        return pts


def _mask(text, size, w, h):
    """A text decal as a boolean mask, for letters carved or printed on a character."""
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype("C:/Windows/Fonts/georgiab.ttf", size)
    b = d.textbbox((0, 0), text, font=f)
    d.text(((w - (b[2] - b[0])) / 2 - b[0], (h - (b[3] - b[1])) / 2 - b[1]), text, font=f, fill=255)
    return np.array(im) > 110


def _put(d, mat, dd, mm):
    mat = np.where(dd < d, mm, mat)
    return np.minimum(d, dd), mat




CHARS: dict = {}
VCENTRE: dict = {}       # portrait framing: the height of each character's face


def _discover():
    import importlib
    import pkgutil
    from . import cast
    for m in sorted(pkgutil.iter_modules(cast.__path__), key=lambda m: m.name):
        mod = importlib.import_module(f".cast.{m.name}", __package__)
        CHARS.update(mod.CHARS)
        VCENTRE.update(getattr(mod, "VCENTRE", {}))


_discover()
