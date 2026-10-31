import numpy as np

from ..rig import Pose
from . import anim, keys, ground

TAU = 2 * np.pi


@anim("idle", 8, 6, group="locomotion")
def idle(i, n):
    ph = TAU * i / n
    breath = 0.5 - 0.5 * np.cos(ph)
    return Pose(
        squash=1.0 - 0.018 * breath,
        arm_r=(0.12, 0.30 + 0.03 * breath, 0.45),
        arm_l=(0.12, 0.30 + 0.03 * breath, 0.45),
        head_pitch=-0.02 * breath,
        coat_sway=(0.15 * np.sin(ph), 0.0),
        drip=i / n,
        blink=1.0 if i == 6 else 0.0,
    )


@anim("idle_fidget", 14, 8, loop=False, group="locomotion")
def idle_fidget(i, n):
    t = i / (n - 1)
    # reach up and tip the hat, then glance left and right
    swing = keys(t, [(0, 0.12), (0.18, 2.7), (0.42, 2.7), (0.55, 0.12)])
    elbow = keys(t, [(0, 0.45), (0.18, 0.0), (0.42, 0.0), (0.55, 0.45)])
    rz = keys(t, [(0, 0.3), (0.18, -0.1), (0.42, -0.1), (0.55, 0.3)])
    tip = keys(t, [(0, 0.0), (0.2, 0.0), (0.3, 0.32), (0.42, 0.0)])
    yaw = keys(t, [(0.5, 0.0), (0.62, 0.55), (0.76, 0.55), (0.86, -0.5), (0.95, -0.5), (1.0, 0.0)])
    look = keys(t, [(0.5, 0.0), (0.62, 1.0), (0.76, 1.0), (0.86, -1.0), (0.95, -1.0), (1.0, 0.0)])
    return Pose(
        arm_r=(swing, rz, elbow),
        hat_tilt=tip,
        head_pitch=-0.6 * tip,
        head_yaw=yaw,
        look=(look, 0.0),
        eyes="smug" if 0.22 < t < 0.45 else "neutral",
        drip=t,
    )


@anim("walk", 8, 10, group="locomotion")
def walk(i, n):
    ph = TAU * i / n
    s = np.sin(ph)
    c = np.cos(ph)
    swing = 0.52 * s
    bend_r = 0.18 + 0.75 * max(0.0, c)
    bend_l = 0.18 + 0.75 * max(0.0, -c)
    p = Pose(
        leg_r=(swing, bend_r),
        leg_l=(-swing, bend_l),
        arm_r=(-0.5 * s + 0.1, 0.22, 0.55 + 0.25 * max(0, -s)),
        arm_l=(0.5 * s + 0.1, 0.22, 0.55 + 0.25 * max(0, s)),
        lean=0.07,
        twist=0.07 * s,
        head_pitch=-0.04 + 0.03 * np.cos(2 * ph),
        coat_sway=(0.45 * s, -0.7 + 0.35 * np.cos(2 * ph)),
        drip=i / n,
    )
    return ground(p)


@anim("run", 8, 14, group="locomotion")
def run(i, n):
    ph = TAU * i / n
    s = np.sin(ph)
    c = np.cos(ph)
    swing = 0.85 * s
    bend_r = 0.35 + 1.25 * max(0.0, c)
    bend_l = 0.35 + 1.25 * max(0.0, -c)
    flight = max(0.0, np.cos(2 * ph)) * 1.6
    drops = []
    if i in (2, 6):
        drops = [(-3.5 if i == 2 else 3.5, 0.6, -5.5)]
    p = Pose(
        leg_r=(swing, bend_r),
        leg_l=(-swing, bend_l),
        arm_r=(-0.85 * s + 0.2, 0.25, 1.25),
        arm_l=(0.85 * s + 0.2, 0.25, 1.25),
        lean=0.24,
        twist=0.12 * s,
        head_pitch=-0.12,
        hat_tilt=-0.08,
        coat_sway=(0.6 * s, -2.0 + 0.5 * np.cos(2 * ph)),
        coat_flare=1.1,
        eyes="determined",
        drip=(i / n) * 0.6,
        extra={"drops": drops},
    )
    return ground(p, lift=flight)


@anim("stop_skid", 5, 12, loop=False, group="locomotion")
def stop_skid(i, n):
    t = i / (n - 1)
    lean = keys(t, [(0, 0.24), (0.3, -0.22), (0.7, -0.12), (1.0, 0.0)])
    p = Pose(
        leg_r=(keys(t, [(0, 0.5), (0.3, 0.75), (1, 0.0)]), keys(t, [(0, 0.3), (1, 0.0)])),
        leg_l=(keys(t, [(0, -0.4), (0.3, -0.35), (1, 0.0)]), keys(t, [(0, 0.8), (0.3, 0.9), (1, 0.0)])),
        arm_r=(keys(t, [(0, 0.3), (0.3, 1.1), (1, 0.12)]), keys(t, [(0, 0.3), (0.3, 0.7), (1, 0.3)]), 0.6),
        arm_l=(keys(t, [(0, 0.3), (0.3, 1.0), (1, 0.12)]), keys(t, [(0, 0.3), (0.3, 0.8), (1, 0.3)]), 0.6),
        lean=lean,
        coat_sway=(0.0, keys(t, [(0, -2.0), (0.3, 1.8), (0.7, -0.6), (1, 0.0)])),
        coat_flare=keys(t, [(0, 1.1), (0.3, 1.15), (1, 1.0)]),
        hat_tilt=keys(t, [(0, -0.08), (0.3, 0.2), (1, 0.0)]),
        eyes="surprised" if t < 0.7 else "neutral",
        extra={"drops": [(0.0, 0.5, 4.5)] if i in (1, 2) else []},
    )
    return ground(p)


@anim("jump_start", 3, 12, loop=False, group="locomotion")
def jump_start(i, n):
    t = i / (n - 1)
    crouch = keys(t, [(0, 0.0), (1, 1.0)])
    p = Pose(
        leg_r=(0.35 * crouch, 0.95 * crouch),
        leg_l=(0.35 * crouch, 0.95 * crouch),
        squash=1.0 - 0.1 * crouch,
        arm_r=(-0.6 * crouch + 0.12, 0.3, 0.45),
        arm_l=(-0.6 * crouch + 0.12, 0.3, 0.45),
        lean=0.15 * crouch,
        coat_flare=1.0 + 0.08 * crouch,
        eyes="determined",
    )
    return ground(p)


@anim("jump_air", 2, 8, loop=True, group="locomotion")
def jump_air(i, n):
    p = Pose(
        leg_r=(0.45, 1.2 + 0.1 * i),
        leg_l=(-0.15, 0.7 + 0.1 * i),
        squash=1.04,
        arm_r=(1.0, 1.1 - 0.1 * i, 0.5),
        arm_l=(1.0, 1.1 - 0.1 * i, 0.5),
        coat_sway=(0.0, 0.6 - 0.3 * i),
        coat_flare=1.15,
        hat_off=(0, 1.2 + 0.4 * i, 0),
        eyes="wide" if False else "surprised",
    )
    return p


@anim("jump_land", 4, 12, loop=False, group="locomotion")
def jump_land(i, n):
    t = i / (n - 1)
    sq = keys(t, [(0, 0.84), (0.4, 1.05), (0.7, 0.98), (1.0, 1.0)])
    bend = keys(t, [(0, 1.0), (0.4, 0.2), (1, 0.0)])
    p = Pose(
        leg_r=(0.35 * bend, 0.95 * bend),
        leg_l=(0.35 * bend, 0.95 * bend),
        squash=sq,
        arm_r=(0.4 * bend + 0.12, 0.3 + 0.6 * bend, 0.45),
        arm_l=(0.4 * bend + 0.12, 0.3 + 0.6 * bend, 0.45),
        coat_flare=1.0 + 0.12 * bend,
        coat_sway=(0.0, 0.8 * bend),
        hat_off=(0, -0.8 * bend, 0),
        eyes="closed" if t < 0.3 else "neutral",
    )
    return ground(p)
