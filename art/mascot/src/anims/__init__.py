"""Animation registry and keyframe helpers.

Each animation is a function frame(i, n) -> Pose. Register it with @anim.
"""
from dataclasses import replace

import numpy as np

from ..rig import Pose, _leg, HIP_Y, THIGH, SHIN

REGISTRY = {}


def anim(name, frames, fps, loop=True, group="misc"):
    def deco(fn):
        REGISTRY[name] = dict(name=name, frames=frames, fps=fps, loop=loop, group=group, fn=fn)
        return fn
    return deco


def smooth(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def keys(t, pts, ease=smooth):
    """Interpolate a value through [(time, value), ...]; values may be tuples."""
    if t <= pts[0][0]:
        return pts[0][1]
    for (t0, a), (t1, b) in zip(pts, pts[1:]):
        if t <= t1:
            u = ease((t - t0) / max(t1 - t0, 1e-9))
            if isinstance(a, tuple):
                return tuple(x + (y - x) * u for x, y in zip(a, b))
            return a + (b - a) * u
    return pts[-1][1]


REST_ANKLE_Y = HIP_Y - THIGH - SHIN


def ground(pose: Pose, lift=0.0) -> Pose:
    """Set bob so the lowest foot rests on the ground (plus optional lift)."""
    lows = []
    for side, (sw, bend) in ((-1, pose.leg_r), (1, pose.leg_l)):
        _, _, ankle = _leg(side, sw, bend, 0.0)
        lows.append(ankle[1])
    return replace(pose, bob=REST_ANKLE_Y - min(lows) + lift)


# import the animation modules so they register themselves
from . import locomotion, investigate, emote, signature  # noqa: E402,F401
