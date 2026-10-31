import numpy as np

from ..rig import Pose
from . import anim, keys, ground

TAU = 2 * np.pi


@anim("talk", 8, 8, group="emote")
def talk(i, n):
    ph = TAU * i / n
    a = np.sin(ph)
    return ground(Pose(
        arm_r=(0.75 + 0.35 * max(a, 0), 0.65 + 0.2 * a, 1.0),
        arm_l=(0.45 + 0.35 * max(-a, 0), 0.5 - 0.2 * a, 0.9),
        head_pitch=-0.05 + 0.05 * np.sin(2 * ph),
        head_roll=0.05 * a,
        twist=0.06 * a,
        eyes="happy" if i in (2, 3) else "neutral",
        coat_sway=(0.2 * a, 0.0),
        drip=i / n,
    ))


@anim("surprised", 6, 12, loop=False, group="emote")
def surprised(i, n):
    t = i / (n - 1)
    jolt = keys(t, [(0, 0.0), (0.25, 1.0), (0.6, 0.7), (1.0, 0.5)])
    p = Pose(
        root=(0, 0, -1.6 * jolt),
        lean=-0.22 * jolt,
        squash=keys(t, [(0, 1.0), (0.25, 1.07), (0.5, 0.97), (1, 1.0)]),
        arm_r=(0.6 * jolt, 0.2 + 1.2 * jolt, 0.4 + 0.6 * jolt),
        arm_l=(0.6 * jolt, 0.2 + 1.2 * jolt, 0.4 + 0.6 * jolt),
        hat_off=(0, 3.2 * keys(t, [(0, 0), (0.25, 1), (0.55, 0.2), (1, 0)]), 0),
        hat_tilt=-0.15 * jolt,
        coat_sway=(0.0, 1.0 * jolt),
        eyes="surprised" if t > 0.1 else "neutral",
    )
    return ground(p, lift=1.5 * keys(t, [(0, 0), (0.25, 1), (0.5, 0)]))


@anim("celebrate", 12, 12, loop=False, group="emote")
def celebrate(i, n):
    t = i / (n - 1)
    up = keys(t, [(0, 0.0), (0.15, 1.0), (0.85, 1.0), (1.0, 0.0)])
    hop = max(0.0, np.sin(np.pi * np.clip((t - 0.1) / 0.4, 0, 1))) * 4.0
    # the hat flies up, spins and lands back on the head
    ht = np.clip((t - 0.12) / 0.66, 0, 1)
    hat_h = 41.0 + 7.0 * 4 * ht * (1 - ht)
    hat_free = (0.0, hat_h, 0.4) if 0.0 < ht < 1.0 else None
    p = Pose(
        arm_r=(0.3 * up + 0.12, 2.3 * up + 0.3, 0.2),
        arm_l=(0.3 * up + 0.12, 2.3 * up + 0.3, 0.2),
        leg_r=(0.5 * (hop > 0.5), 1.1 * (hop > 0.5)),
        leg_l=(-0.1 * (hop > 0.5), 0.7 * (hop > 0.5)),
        hat_free=hat_free,
        hat_tilt=ht * 2 * np.pi if hat_free else 0.0,
        head_pitch=-0.15 * up,
        eyes="happy",
        coat_sway=(0.0, 0.8 if hop > 0.5 else 0.0),
        coat_flare=1.0 + 0.1 * (hop > 0.5),
    )
    return ground(p, lift=hop)


@anim("defeated", 8, 8, loop=False, group="emote")
def defeated(i, n):
    t = i / (n - 1)
    d = keys(t, [(0, 0.0), (0.6, 1.0), (1.0, 1.0)])
    return ground(Pose(
        lean=0.14 * d,
        head_pitch=0.26 * d,
        squash=1.0 - 0.1 * d,
        arm_r=(0.0, 0.08, 0.1),
        arm_l=(0.0, 0.08, 0.1),
        hat_tilt=0.3 * d,
        coat_flare=1.0 + 0.08 * d,
        eyes="sad" if d > 0.3 else "worried",
        look=(0, 1.0 * d),
        drip=t,
    ))
