import numpy as np

from ..rig import Pose
from . import anim, keys, ground

TAU = 2 * np.pi


@anim("inspect", 10, 8, loop=False, group="investigate")
def inspect(i, n):
    """Crouch, bring the magnifier up, then scan left-right (frames 4-9 loop)."""
    t_in = min(i / 3.0, 1.0)
    scan = 0.0 if i < 4 else np.sin(TAU * (i - 4) / 6)
    crouch = 0.55 * t_in
    p = Pose(
        leg_r=(0.45 * crouch, 1.1 * crouch),
        leg_l=(-0.1 * crouch, 0.9 * crouch),
        lean=0.32 * t_in,
        twist=0.18 * scan,
        arm_r=(keys(t_in, [(0, 0.12), (1, 1.15)]), 0.25, keys(t_in, [(0, 0.45), (1, 0.55)])),
        arm_l=(0.3 * t_in + 0.12, 0.45, 0.9 * t_in + 0.4),
        head_pitch=0.22 * t_in,
        head_yaw=0.12 * scan,
        prop_r="magnifier" if i >= 1 else None,
        prop_angle=keys(t_in, [(0, 0.3), (1, -0.35)]),
        eyes="thinking" if i >= 3 else "neutral",
        look=(scan, 1.0 * t_in),
        drip=i / n,
    )
    return ground(p)


@anim("pickup", 6, 10, loop=False, group="investigate")
def pickup(i, n):
    t = i / (n - 1)
    bend = keys(t, [(0, 0.0), (0.4, 1.0), (0.6, 1.0), (1.0, 0.0)])
    p = Pose(
        leg_r=(0.8 * bend, 1.7 * bend),
        leg_l=(0.35 * bend, 1.4 * bend),
        lean=0.3 * bend,
        squash=1.0 - 0.06 * bend,
        arm_r=(0.12 + 0.9 * bend, 0.2, 0.45 - 0.3 * bend),
        arm_l=(0.12 + 0.2 * bend, 0.4, 0.5),
        head_pitch=0.25 * bend,
        coat_flare=1.0 + 0.1 * bend,
        coat_sway=(0.0, -1.0 * bend),
        eyes="happy" if t > 0.75 else "neutral",
        look=(0, 1.0 * bend),
    )
    return ground(p)


@anim("write_notes", 8, 8, group="investigate")
def write_notes(i, n):
    ph = TAU * i / n
    return ground(Pose(
        arm_l=(1.0, -0.5, 0.2),
        arm_r=(1.3 + 0.08 * np.sin(2 * ph), -0.6 + 0.08 * np.cos(2 * ph), 0.1 + 0.08 * np.sin(2 * ph)),
        prop_l="notebook",
        prop_r="pen",
        prop_angle=1.1,
        head_pitch=0.28,
        eyes="thinking",
        look=(0.5 * np.sin(2 * ph), 1.0),
        drip=i / n,
        blink=1.0 if i == 5 else 0.0,
    ))


@anim("think", 8, 6, group="investigate")
def think(i, n):
    ph = TAU * i / n
    tap = 0.08 * max(0.0, np.sin(2 * ph))
    return ground(Pose(
        arm_r=(1.6 + tap, -0.4, 0.8),
        arm_l=(0.55, 0.05, 1.45),
        head_roll=0.14,
        head_pitch=-0.06,
        eyes="thinking",
        look=(0.6, -1.0),
        coat_sway=(0.15 * np.sin(ph), 0.0),
        drip=i / n,
    ))


@anim("knock", 6, 12, loop=False, group="investigate")
def knock(i, n):
    elbow = [0.6, 0.0, 0.5, 0.0, 0.5, 0.6][i]
    return ground(Pose(
        arm_r=(1.8, -0.3, elbow),
        lean=0.05,
        head_pitch=-0.04,
        eyes="neutral",
        drip=i / n,
    ))
