import numpy as np

from ..rig import Pose
from . import anim, keys, ground

TAU = 2 * np.pi
FORMS = ["ruler", "beaker", "stopwatch", "protractor", "lens", "voltmeter"]


@anim("strikethrough", 12, 14, loop=False, group="signature")
def strikethrough(i, n):
    """Draw the giant red pen, wind up, slash, hold the pose."""
    t = i / (n - 1)
    swing = keys(t, [(0, 0.12), (0.2, 0.9), (0.45, 2.7), (0.6, 0.2), (0.7, -0.2), (1.0, 0.0)])
    raise_ = keys(t, [(0, 0.3), (0.45, 0.5), (0.6, 0.7), (1.0, 0.6)])
    elbow = keys(t, [(0, 0.45), (0.2, 1.4), (0.45, 0.4), (0.6, 0.1), (1.0, 0.2)])
    pen = keys(t, [(0, 0.0), (0.2, 0.4), (0.45, -0.4), (0.6, 1.9), (0.7, 2.1), (1.0, 1.85)])
    lean = keys(t, [(0, 0.0), (0.45, -0.12), (0.6, 0.28), (1.0, 0.18)])
    p = Pose(
        arm_r=(swing, raise_, elbow),
        arm_l=(keys(t, [(0, 0.12), (0.45, 0.8), (0.6, -0.3), (1, -0.2)]), 0.5, 0.6),
        prop_r="bigpen" if i >= 2 else ("pen" if i == 1 else None),
        prop_angle=pen,
        lean=lean,
        twist=keys(t, [(0, 0.0), (0.45, -0.3), (0.6, 0.35), (1.0, 0.25)]),
        leg_r=(keys(t, [(0, 0), (0.45, -0.2), (0.6, 0.45), (1, 0.4)]), keys(t, [(0, 0), (0.6, 0.5), (1, 0.4)])),
        leg_l=(keys(t, [(0, 0), (0.45, 0.2), (0.6, -0.35), (1, -0.3)]), 0.2),
        hat_tilt=keys(t, [(0, 0.0), (0.6, 0.12), (1, 0.1)]),
        coat_sway=(keys(t, [(0, 0), (0.45, -0.8), (0.6, 1.4), (1, 0.6)]), keys(t, [(0, 0), (0.6, -1.2), (1, -0.4)])),
        coat_flare=keys(t, [(0, 1.0), (0.6, 1.12), (1, 1.05)]),
        eyes="determined" if t > 0.15 else "neutral",
        extra={"drops": [(-9.0, 26.0, 9.0), (-11.0, 22.0, 8.0), (-7.0, 30.0, 10.0)] if 7 <= i <= 8 else []},
    )
    return ground(p)


@anim("shapeshift_melt", 8, 12, loop=False, group="signature")
def shapeshift_melt(i, n):
    t = i / (n - 1)
    m = keys(t, [(0, 0.0), (1, 1.0)])
    sy = 1.0 - 0.82 * m ** 1.15
    hat_y = 41.0 * sy + 1.2 * m
    return Pose(
        melt=m,
        squash=1.0 + 0.05 * np.sin(np.pi * m),
        hat_on=True,
        hat_free=(0.0, hat_y, 0.4) if m > 0.05 else None,
        hat_tilt=0.15 * m,
        eyes="surprised" if m < 0.4 else "closed",
        arm_r=(0.12, 0.3 + 0.8 * m, 0.45),
        arm_l=(0.12, 0.3 + 0.8 * m, 0.45),
    )


@anim("shapeshift_reform", 8, 12, loop=False, group="signature")
def shapeshift_reform(i, n):
    return shapeshift_melt(n - 1 - i, n)


def _form_anim(name):
    @anim(f"form_{name}", 6, 8, group="forms")
    def idle(i, n):
        ph = TAU * i / n
        return Pose(
            form=name,
            form_t=1.0,
            squash=1.0 - 0.02 * (0.5 - 0.5 * np.cos(ph)),
            hat_tilt=0.04 * np.sin(ph),
            eyes="neutral" if i != 4 else "closed",
            extra={"phase": i / n},
        )

    @anim(f"form_{name}_in", 4, 12, loop=False, group="forms")
    def into(i, n):
        t = (i + 1) / n
        return Pose(form=name, form_t=t, squash=1.0 + 0.08 * np.sin(np.pi * t),
                    eyes="closed" if t < 0.5 else "happy", hat_on=t > 0.5)


for _f in FORMS:
    _form_anim(_f)
