"""Smudge, detective edition, as a posable SDF character.

Local space: units are final pixels, y up, feet on y=0, character faces +z.
Character's right side is -x (the viewer's left when it faces the camera).
"""
from dataclasses import dataclass, field

import numpy as np

from . import sdf
from .palette import (INK, COAT, COAT_DARK, BELT, METAL, HAT, BAND, PEN,
                      GLASS, PAPER, WOOD, STEEL, SCREEN, SLEEVE)

HIP_Y = 10.4
THIGH = 4.6
SHIN = 4.6
SHOULDER = np.array([7.2, 19.4, -0.2])
UPPER_ARM = 4.6
FOREARM = 4.2
HEAD_PIVOT = np.array([0.0, 23.0, 0.0])
HEAD_C = np.array([0.0, 31.8, 0.4])
HEAD_R = np.array([9.6, 8.7, 9.0])
COAT_Z = 0.80


@dataclass
class Pose:
    # whole body
    root: tuple = (0.0, 0.0, 0.0)      # translation
    lean: float = 0.0                  # forward pitch of the upper body (rad)
    twist: float = 0.0                 # upper-body yaw (rad)
    squash: float = 1.0                # vertical scale of the whole figure
    bob: float = 0.0                   # hip height offset
    # legs: thigh swing (+ forward), knee bend (+ bends back), foot pitch
    leg_r: tuple = (0.0, 0.0)
    leg_l: tuple = (0.0, 0.0)
    # arms: swing (+ forward), raise (+ outward), elbow bend (+ forward)
    arm_r: tuple = (0.12, 0.30, 0.45)
    arm_l: tuple = (0.12, 0.30, 0.45)
    # head
    head_yaw: float = 0.0
    head_pitch: float = 0.0            # + nods down
    head_roll: float = 0.0
    # hat relative to head
    hat_off: tuple = (0.0, 0.0, 0.0)
    hat_tilt: float = 0.0              # + tips forward
    hat_roll: float = 0.0
    hat_on: bool = True
    hat_free: tuple = None             # world-space hat position when tossed
    # coat secondary motion
    coat_sway: tuple = (0.0, 0.0)      # hem offset x, z
    coat_flare: float = 1.0
    # ink
    drip: float = 0.0                  # 0..1 phase of the head drip
    melt: float = 0.0                  # 0 = Smudge, 1 = flat puddle
    # face (2D decals)
    eyes: str = "neutral"
    look: tuple = (0.0, 0.0)           # pupil offset in pixels
    blink: float = 0.0
    # props held in hands
    prop_r: str = None                 # "magnifier" | "bigpen" | "pen"
    prop_l: str = None                 # "notebook"
    prop_angle: float = 0.0
    # instrument form (shapeshift)
    form: str = None
    form_t: float = 1.0                # 0..1 how fully formed
    extra: dict = field(default_factory=dict)


def _leg(side, swing, bend, bob):
    hip = np.array([side * 3.5, HIP_Y + bob, 0.0])
    d1 = np.array([0.0, -np.cos(swing), np.sin(swing)])
    knee = hip + THIGH * d1
    a2 = swing - bend
    d2 = np.array([0.0, -np.cos(a2), np.sin(a2)])
    ankle = knee + SHIN * d2
    return hip, knee, ankle


def _arm(side, swing, raise_, elbow, shoulder):
    base = np.array([0.0, -1.0, 0.0])
    r_up = sdf.rot_x(-swing) @ sdf.rot_z(side * raise_)
    d1 = r_up @ base
    elbow_p = shoulder + UPPER_ARM * d1
    r_fore = sdf.rot_x(-(swing + elbow)) @ sdf.rot_z(side * raise_)
    d2 = r_fore @ base
    wrist = elbow_p + FOREARM * d2
    return elbow_p, wrist, d2


def reach(side, target, rest=(0.12, 0.3, 0.45)):
    """Tiny IK: grid-search arm angles so the hand lands nearest `target`
    (rest-pose upper-body space). Ties break toward the rest pose."""
    target = np.asarray(target, float)
    sh = SHOULDER * np.array([side, 1, 1])
    best, best_e = rest, 1e9
    for sw in np.linspace(-0.6, 3.0, 37):
        for ra in np.linspace(-0.9, 2.6, 36):
            for el in np.linspace(0.0, 2.4, 25):
                _, wrist, d2 = _arm(side, sw, ra, el, sh)
                e = np.linalg.norm(wrist + d2 * 1.4 - target) + 0.02 * abs(ra - rest[1])
                if e < best_e:
                    best, best_e = (sw, ra, el), e
    return tuple(float(x) for x in best)


class Character:
    """Builds the SDF for one pose. Call .eval(points) -> (dist, material)."""

    def __init__(self, pose: Pose):
        self.p = pose
        self.upper_rot = sdf.rot_y(pose.twist) @ sdf.rot_x(pose.lean)
        self.head_rot = (self.upper_rot @ sdf.rot_y(pose.head_yaw)
                         @ sdf.rot_x(pose.head_pitch) @ sdf.rot_z(pose.head_roll))
        bob = pose.bob
        self.legs = [_leg(-1, *pose.leg_r, bob), _leg(1, *pose.leg_l, bob)]
        self.hip_y = HIP_Y + bob
        # upper body pivots around the hips
        self.pivot = np.array([0.0, self.hip_y, 0.0])
        sh_r = self._upper(SHOULDER * np.array([-1, 1, 1]))
        sh_l = self._upper(SHOULDER)
        self.arms = [(-1, sh_r) + _arm(-1, *pose.arm_r, sh_r),
                     (1, sh_l) + _arm(1, *pose.arm_l, sh_l)]
        self.head_origin = self._upper(HEAD_PIVOT)

    # ---- frames -------------------------------------------------------
    def _upper(self, v):
        """Point in rest-pose upper-body space -> local space."""
        rest = np.asarray(v, dtype=float) + np.array([0, self.p.bob, 0])
        return self.pivot + self.upper_rot @ (rest - self.pivot)

    def to_upper(self, q):
        q = q - self.pivot
        q = q @ self.upper_rot
        return q + self.pivot - np.array([0, self.p.bob, 0])

    def to_head(self, q):
        q = q - self.head_origin
        return q @ self.head_rot + HEAD_PIVOT

    def head_point(self, v):
        """Head-space point -> local space (used for eye decals)."""
        return self.head_origin + self.head_rot @ (np.asarray(v) - HEAD_PIVOT)

    def head_dir(self, v):
        return self.head_rot @ np.asarray(v)

    # ---- pieces -------------------------------------------------------
    def _coat_space(self, qu):
        """Apply hem sway/flare shear inside upper-body space."""
        p = self.p
        w = np.clip((20.0 - qu[:, 1]) / 12.0, 0.0, 1.0) ** 1.4
        qc = qu.copy()
        qc[:, 0] -= p.coat_sway[0] * w
        qc[:, 2] -= p.coat_sway[1] * w
        flare = 1.0 + (p.coat_flare - 1.0) * w
        qc[:, 0] /= flare
        qc[:, 2] /= flare * COAT_Z
        return qc, np.minimum(flare, flare * COAT_Z)

    def coat(self, qu):
        qc, s = self._coat_space(qu)
        body = sdf.round_cone(qc, (0, 10.0, 0), (0, 19.6, 0), 8.6, 6.9) * s
        hem = 8.4 - qu[:, 1]
        body = sdf.smax(body, hem, 0.6)
        # front split below the belt shows the darker lining
        cut = sdf.box(qc - np.array([0, 10.2, 9.0]), (0.9, 3.0, 4.0))
        # V-neck between the lapels, revealing the dark lining
        yy = qu[:, 1]
        vee = np.maximum.reduce([np.abs(qu[:, 0]) - (yy - 15.8) * 0.42 - 0.3,
                                 15.8 - yy, -(qu[:, 2] - 3.0)])
        cut = np.minimum(cut, vee)
        d = np.maximum(body, -cut)
        mat = np.where(-cut > body, COAT_DARK, COAT)
        # popped collar: a flaring shell, open at the front
        col = sdf.round_cone(qu, (0, 18.6, -0.4), (0, 25.6, -1.2), 6.6, 8.0)
        col = np.abs(col + 0.7) - 0.85
        col = np.maximum(col, qu[:, 1] - 26.4 + 1.6 * np.clip(qu[:, 2] / 6.0, 0, 1))
        col = np.maximum(col, 18.0 - qu[:, 1])
        notch = sdf.box(qu - np.array([0, 22.8, 6.8]), (3.2, 3.6, 3.0))
        col = np.maximum(col, -notch)
        mat = np.where(col < d, COAT, mat)
        d = np.minimum(d, col)
        # shoulders: soften the top of the cone into the arms
        for side in (-1, 1):
            sh = sdf.sphere(qu, (side * 6.2, 18.8, -0.2), 3.0)
            d = sdf.smin(d, sh, 1.6)
        return d, mat

    def belt(self, qu):
        qc, s = self._coat_space(qu)
        band = sdf.ellip_cylinder_y(qc - np.array([0, 13.4, 0]), 8.45, 8.45, 1.05, 0.35) * s
        buckle = sdf.box(qc - np.array([0, 13.4, 8.45]), (1.15, 1.05, 0.6), 0.2) * s
        d = np.minimum(band, buckle)
        mat = np.where(buckle < band, METAL, BELT)
        # buttons and breast-pocket pen
        btns = None
        for x in (-2.3, 2.3):
            for y in (16.0, 18.0):
                zb = (8.6 - (8.6 - 6.9) * (y - 9.4) / 10.2) + 0.15
                b = sdf.sphere(qc, (x, y, zb), 0.75) * s
                btns = b if btns is None else np.minimum(btns, b)
        mat = np.where(btns < d, BELT, mat)
        d = np.minimum(d, btns)
        pen = sdf.capsule(qc, (3.4, 16.8, 7.25), (3.4, 19.6, 7.0), 0.7) * s
        mat = np.where(pen < d, PEN, mat)
        d = np.minimum(d, pen)
        return d, mat

    def ink_body(self, q, qu):
        p = self.p
        parts = []
        for hip, knee, ankle in self.legs:
            parts.append(sdf.round_cone(q, hip, knee, 2.5, 2.2))
            parts.append(sdf.round_cone(q, knee, ankle, 2.2, 1.9))
            parts.append(sdf.ellipsoid(q, ankle + np.array([0, -0.25, 1.0]), (2.4, 1.6, 3.1)))
        for side, sh, elbow, wrist, d2 in self.arms:
            parts.append(sdf.sphere(q, wrist + d2 * 1.4, 2.2))
        qh = self.to_head(q)
        parts.append(sdf.ellipsoid(qh, HEAD_C, HEAD_R))
        parts.append(sdf.capsule(qu, (0, 19, 0), (0, 25, 0), 3.4))
        # the signature drip running down the cheek
        t = p.drip
        drip_len = 1.2 + 2.6 * t
        parts.append(sdf.capsule(qh, (6.6, 27.8, 6.1), (6.9, 27.8 - drip_len, 6.3), 0.95))
        if t > 0.75:
            fall = (t - 0.75) / 0.25
            parts.append(sdf.sphere(qh, (7.0, 24.0 - 6 * fall, 6.4), 0.85))
        d = parts[0]
        for x in parts[1:]:
            d = sdf.smin(d, x, 1.8)
        # loose ink droplets (footfalls, splashes) stay crisp, no blending
        for c in p.extra.get("drops", []):
            d = np.minimum(d, sdf.sphere(q, c, 0.95))
        return d

    def sleeves(self, q):
        d = None
        for side, sh, elbow, wrist, d2 in self.arms:
            a = sdf.round_cone(q, sh, elbow, 2.6, 2.3)
            b = sdf.round_cone(q, elbow, wrist, 2.3, 2.15)
            cuff = sdf.capsule(q, wrist - d2 * 0.9, wrist, 2.45)
            x = sdf.smin(np.minimum(a, b), cuff, 0.5)
            d = x if d is None else np.minimum(d, x)
        return d

    def hat(self, q):
        p = self.p
        if not p.hat_on:
            return None, None
        if p.hat_free is not None:
            qh = q - np.asarray(p.hat_free) + np.array([0, 41.0, 0])
            qh = (qh - np.array([0, 41.0, 0])) @ (sdf.rot_x(p.hat_tilt) @ sdf.rot_z(p.hat_roll)) \
                + np.array([0, 41.0, 0])
        else:
            qh = self.to_head(q) - np.asarray(p.hat_off)
            pivot = np.array([0, 40.0, 1.0])
            qh = (qh - pivot) @ (sdf.rot_x(p.hat_tilt) @ sdf.rot_z(p.hat_roll)) + pivot
        # snap brim: tipped down at the front
        qb = (qh - np.array([0, 39.4, 0.6])) @ sdf.rot_x(-0.12)
        brim = sdf.ellip_cylinder_y(qb, 12.4, 11.2, 0.55, 0.5)
        # crown tapers toward the top, with a soft centre crease and front pinch
        qcr = qh - np.array([0, 43.0, -0.2])
        taper = 1.0 - 0.07 * np.clip((qcr[:, 1] + 3.7) / 7.4, 0, 1)
        qcr = qcr / np.stack([taper, np.ones_like(taper), taper], 1)
        crown = sdf.ellip_cylinder_y(qcr, 7.3, 6.5, 3.7, 2.2) * 0.93
        crease = sdf.ellipsoid(qh, (0, 47.6, -0.4), (1.6, 1.2, 5.0))
        pinch = np.minimum(sdf.ellipsoid(qh, (-4.4, 45.6, 5.0), (1.6, 2.2, 1.8)),
                           sdf.ellipsoid(qh, (4.4, 45.6, 5.0), (1.6, 2.2, 1.8)))
        crown = sdf.smax(crown, -np.minimum(crease, pinch), 1.4)
        band = sdf.ellip_cylinder_y(qh - np.array([0, 40.95, -0.2]), 7.55, 6.75, 1.0, 0.3)
        d = sdf.smin(brim, crown, 0.9)
        mat = np.where(band < d, BAND, HAT)
        return np.minimum(d, band), mat

    def props(self, q):
        p = self.p
        out = []
        for (side, sh, elbow, wrist, d2), name in zip(self.arms, (p.prop_r, p.prop_l)):
            if not name:
                continue
            hand = wrist + d2 * 1.4
            if name == "magnifier":
                fwd = sdf.rot_x(-p.prop_angle) @ np.array([0, 0.35, 1.0])
                fwd /= np.linalg.norm(fwd)
                ring_c = hand + fwd * 7.0
                handle = sdf.capsule(q, hand - fwd * 0.5, hand + fwd * 3.6, 0.9)
                out.append((handle, WOOD))
                ql = q - ring_c
                # ring plane faces the direction of the handle
                ax = np.cross(fwd, [1, 0, 0])
                ax /= np.linalg.norm(ax)
                basis = np.stack([[1, 0, 0], fwd, ax], axis=1)
                qr = ql @ basis
                ring = np.sqrt((np.sqrt(qr[:, 0] ** 2 + qr[:, 2] ** 2) - 3.2) ** 2 + qr[:, 1] ** 2) - 0.75
                lens = sdf.cylinder_y(qr, 3.0, 0.3, 0.2)
                out.append((ring, METAL))
                out.append((lens, GLASS))
            elif name == "notebook":
                c = hand + np.array([0, 1.2, 1.6])
                book = sdf.box((q - c) @ sdf.rot_x(0.6), (3.4, 0.7, 4.2), 0.3)
                pages = sdf.box((q - c - np.array([0, 0.75, 0])) @ sdf.rot_x(0.6), (3.0, 0.2, 3.8), 0.1)
                out.append((book, BELT))
                out.append((pages, PAPER))
            elif name in ("bigpen", "pen"):
                L = 12.5 if name == "bigpen" else 5.0
                r = 1.5 if name == "bigpen" else 0.7
                ang = p.prop_angle
                fwd = sdf.rot_x(-ang) @ np.array([0, 1.0, 0.0])
                body = sdf.capsule(q, hand - fwd * 2.0, hand + fwd * L, r)
                nib = sdf.round_cone(q, hand - fwd * 2.0, hand - fwd * 5.0, r * 0.9, 0.3)
                cap = sdf.capsule(q, hand + fwd * (L - 3.0), hand + fwd * L, r + 0.25)
                out.append((body, PEN))
                out.append((nib, METAL))
                out.append((cap, STEEL))
        return out

    # ---- instrument forms (shapeshift) --------------------------------
    def form_parts(self, q):
        """Instrument body made of ink + material, keeps head+hat on top."""
        name = self.p.form
        t = self.p.extra.get("phase", 0.0)
        parts = []
        if name == "beaker":
            qq = q - np.array([0, 9.5, 0])
            outer = sdf.cylinder_y(qq, 9.0, 9.5, 1.2)
            inner = sdf.cylinder_y(qq - np.array([0, 1.4, 0]), 7.8, 9.6, 1.0)
            glass = np.maximum(outer, -inner)
            water = sdf.cylinder_y(qq - np.array([0, -3.0, 0]), 7.9, 5.6, 0.8)
            parts += [(glass, GLASS), (water, INK)]
            for y in (-4.0, 0.0, 4.0):
                mark = sdf.box(qq - np.array([-6.0, y, 6.5]), (2.0, 0.35, 0.6))
                parts.append((mark, STEEL))
        elif name == "ruler":
            qq = q - np.array([0, 13.0, 0])
            body = sdf.box(qq, (3.2, 13.0, 1.4), 0.4)
            parts.append((body, WOOD))
            for i in range(-11, 12, 2):
                ln = 1.8 if i % 4 == 1 else 1.1
                tick = sdf.box(qq - np.array([-3.2 + ln / 2, i, 1.45]), (ln / 2, 0.3, 0.3))
                parts.append((tick, INK))
        elif name == "stopwatch":
            qq = q - np.array([0, 11.0, 0])
            case = sdf.cylinder_y(qq @ sdf.rot_x(np.pi / 2), 10.0, 2.4, 1.6)
            face = sdf.cylinder_y((qq - np.array([0, 0, 2.2])) @ sdf.rot_x(np.pi / 2), 8.2, 0.4, 0.3)
            crown = sdf.capsule(qq, (0, 10.0, 0), (0, 13.0, 0), 1.4)
            hand_ = sdf.capsule(qq, (0, 0, 2.8), (3.5 * np.sin(t * 6.28), 3.5 * np.cos(t * 6.28), 2.8), 0.5)
            parts += [(case, STEEL), (face, PAPER), (crown, STEEL), (hand_, BAND)]
        elif name == "protractor":
            qq = q - np.array([0, 0.5, 0])
            r = np.sqrt(qq[:, 0] ** 2 + qq[:, 1] ** 2)
            half = np.maximum(r - 12.5, -qq[:, 1])
            half = np.maximum(half, np.abs(qq[:, 2]) - 1.0)
            hole = np.maximum(r - 5.0, np.abs(qq[:, 2]) - 2.0)
            arc = np.maximum(np.maximum(half, -hole), -qq[:, 1] - 0.1)
            parts.append((arc, GLASS))
            for k in range(1, 9):
                a = np.pi * k / 9
                tick = sdf.capsule(qq, (11.0 * np.cos(a), 11.0 * np.sin(a), 1.1),
                                   (12.4 * np.cos(a), 12.4 * np.sin(a), 1.1), 0.35)
                parts.append((tick, INK))
        elif name == "lens":
            qq = (q - np.array([0, 12.0, 0])) @ sdf.rot_x(np.pi / 2)
            ring = np.sqrt((np.sqrt(qq[:, 0] ** 2 + qq[:, 2] ** 2) - 8.5) ** 2 + qq[:, 1] ** 2) - 1.6
            lens = sdf.cylinder_y(qq, 8.0, 0.9, 0.8)
            handle = sdf.capsule(q, (5.5, 5.5, 0), (10.0, 0.5, 0), 1.6)
            parts += [(ring, METAL), (lens, GLASS), (handle, WOOD)]
        elif name == "voltmeter":
            qq = q - np.array([0, 10.5, 0])
            case = sdf.box(qq, (9.0, 10.0, 3.0), 1.6)
            screen = sdf.box(qq - np.array([0, 4.0, 3.0]), (6.2, 3.2, 0.4), 0.3)
            dial = sdf.cylinder_y((qq - np.array([0, -3.5, 3.0])) @ sdf.rot_x(np.pi / 2), 3.0, 0.5, 0.3)
            probe_r = sdf.capsule(q, (-6, 1.0, 0), (-9.5, -0.0, 4.0), 0.7)
            probe_b = sdf.capsule(q, (6, 1.0, 0), (9.5, -0.0, 4.0), 0.7)
            parts += [(case, BAND), (screen, SCREEN), (dial, STEEL), (probe_r, BAND), (probe_b, INK)]
        return parts

    # ---- full scene -----------------------------------------------------
    def eval(self, q):
        p = self.p
        q = q - np.asarray(p.root, dtype=float)
        if p.squash != 1.0:
            q = q.copy()
            q[:, 1] /= p.squash
        scale = min(p.squash, 1.0)

        if p.form:
            return self._eval_form(q, scale)

        q_hat = q
        mscale = 1.0
        if p.melt > 0:
            # the whole figure sags and spreads like a drop of ink
            m = p.melt
            sy = 1.0 - 0.82 * m ** 1.15
            wide = 1.0 + 0.55 * m
            q = q.copy()
            q[:, 1] /= sy
            q[:, 0] /= wide
            q[:, 2] /= 1.0 + 0.25 * m
            mscale = min(sy, 1.0)
        qu = self.to_upper(q)
        layers = []
        ink = self.ink_body(q, qu) * mscale
        if p.melt > 0.45:
            ink = self._melt(q_hat, ink, (p.melt - 0.45) / 0.55)
        layers.append((ink, np.full(len(q), INK)))
        if p.melt < 0.9:
            fade = max(0.0, p.melt - 0.45) * 30.0
            cd, cm = self.coat(qu)
            layers.append((cd * mscale + fade, cm))
            bd, bm = self.belt(qu)
            layers.append((bd * mscale + fade, bm))
            layers.append((self.sleeves(q) * mscale + fade, np.full(len(q), SLEEVE)))
        q = q_hat
        hd, hm = self.hat(q)
        if hd is not None:
            layers.append((hd, hm))
        for d, m in self.props(q):
            layers.append((d, np.full(len(q), m) if np.isscalar(m) else m))
        d, mat = layers[0]
        mat = mat.copy()
        for dd, mm in layers[1:]:
            closer = dd < d
            mat = np.where(closer, mm, mat)
            d = np.minimum(d, dd)
        return d * scale, mat

    def _melt(self, q, ink, m):
        puddle = sdf.ellipsoid(q, (0, 0.8, 0.0), (12.0 + 2 * m, 1.8, 7.5 + 1 * m))
        blob = sdf.ellipsoid(q, (0, 4.0 * (1 - m), 0.6), (9.0, 6.0 * (1 - m) + 1.5, 8.0))
        target = sdf.smin(puddle, blob, 2.0)
        return ink * (1 - m) + target * m

    def _eval_form(self, q, scale):
        p = self.p
        parts = self.form_parts(q)
        # Smudge's eyes ride on a small ink blob head atop the instrument
        top = {"beaker": 22.5, "ruler": 29.0, "stopwatch": 25.0,
               "protractor": 16.0, "lens": 24.0, "voltmeter": 24.5}[p.form]
        head = sdf.ellipsoid(q, (0, top + 3.6, 0.6), (6.4, 5.0, 5.6))
        layers = [(head, np.full(len(q), INK))]
        for d, m in parts:
            layers.append((d, np.full(len(q), m)))
        if p.hat_on:
            s = 0.66
            off = np.array([0.0, top + 7.4 - 39.4 * s, 0.4])
            sub = Character(Pose(hat_tilt=p.hat_tilt))
            hd, hm = sub.hat((q - off) / s)
            layers.append((hd * s, hm))
        d, mat = layers[0]
        mat = mat.copy()
        for dd, mm in layers[1:]:
            mat = np.where(dd < d, mm, mat)
            d = np.minimum(d, dd)
        if p.form_t < 1.0:
            puddle = sdf.ellipsoid(q, (0, 0.8, 1.0), (14.0, 1.8, 11.0))
            d = d * p.form_t + puddle * (1 - p.form_t)
        return d * scale, mat

    # ---- face anchors -------------------------------------------------
    def face_anchor(self):
        """Eye anchor points + outward normals in local space, or None."""
        p = self.p
        if p.form:
            top = {"beaker": 22.5, "ruler": 29.0, "stopwatch": 25.0,
                   "protractor": 16.0, "lens": 24.0, "voltmeter": 24.5}[p.form]
            c = np.array([0, top + 3.4, 0.6])
            r = np.array([6.4, 5.0, 5.6])
            pts = []
            for x in (-2.3, 2.3):
                z = r[2] * np.sqrt(max(1 - (x / r[0]) ** 2 - 0.02, 0.05))
                pt = c + np.array([x, -0.2, z])
                n = np.array([x / r[0] ** 2, -0.2 / r[1] ** 2, z / r[2] ** 2])
                pts.append((pt, n / np.linalg.norm(n)))
            return pts, 0.7
        if p.melt > 0.55:
            return None, 1.0
        pts = []
        for x in (-3.3, 3.3):
            y = 30.2
            dy = y - HEAD_C[1]
            z = HEAD_R[2] * np.sqrt(max(1 - (x / HEAD_R[0]) ** 2 - (dy / HEAD_R[1]) ** 2, 0.05))
            pt = HEAD_C + np.array([x, dy, z])
            n = np.array([x / HEAD_R[0] ** 2, dy / HEAD_R[1] ** 2, z / HEAD_R[2] ** 2])
            n /= np.linalg.norm(n)
            pts.append((self.head_point(pt) * np.array([1, p.squash, 1]) + np.asarray(p.root) +
                        np.array([0, -p.melt * 18, 0]), self.head_dir(n)))
        return pts, 1.0
