"""Footnote: a floating pink asterisk, the coach agent's face in the world."""
import numpy as np

from . import sdf
from .palette import FOOT
from .rig import Pose

ARM = 9.5          # arm length from centre
THICK = 2.6        # arm radius (in the asterisk's plane)
DEPTH = 0.62       # front-to-back flattening


class Footnote:
    skin = FOOT
    billboard = True
    brow_hex = "#5A1530"
    def __init__(self, pose: Pose):
        self.p = pose
        e = pose.extra
        self.hover = 20.0 + e.get("bob", 0.0)
        self.spin = e.get("spin", 0.0)
        self.pop = e.get("pop", 1.0)          # 0 = flat print on the page, 1 = fully lifted
        self.stretch = e.get("stretch", 1.0)  # vertical squash/stretch

    def _centre(self):
        return np.array([0.0, 2.0 + (self.hover - 2.0) * self.pop, 2.0])

    def eval(self, q):
        c = self._centre()
        lq = q - c
        lq = lq @ sdf.rot_x(-np.pi / 2 * (1 - self.pop))      # lies flat when unpopped
        lq = lq @ sdf.rot_z(self.spin)
        lq[:, 1] /= self.stretch
        lq[:, 2] /= DEPTH * max(self.pop, 0.25)
        d = None
        for k in range(3):
            a = np.pi / 2 + k * np.pi / 3
            v = np.array([np.cos(a), np.sin(a), 0.0]) * ARM
            arm = sdf.capsule(lq, -v, v, THICK)
            d = arm if d is None else sdf.smin(d, arm, 1.6)
        d = d * min(self.stretch, 1.0) * DEPTH * max(self.pop, 0.25)
        return d, np.full(len(q), FOOT)

    def face_anchor(self):
        if self.pop < 0.6:
            return None, 1.0
        c = self._centre()
        z = THICK * DEPTH * 0.98
        pts = [(c + np.array([x, 0.6, z + 0.2]), np.array([x * 0.05, 0.05, 1.0])) for x in (-2.4, 2.4)]
        return [(pt, n / np.linalg.norm(n)) for pt, n in pts], 0.7

    def head_dir(self, v):
        return np.asarray(v)
