"""Signed-distance primitives, vectorised over (N, 3) point arrays.

Units are final-sprite pixels. Most formulas follow Inigo Quilez's
distance-function reference (iquilezles.org/articles/distfunctions).
"""
import numpy as np


def _len(v):
    return np.sqrt(np.einsum("ij,ij->i", v, v))


def rot_x(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = np.cos(a), np.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def to_local(p, origin, rot=None):
    """World points -> a local frame whose axes are the columns of `rot`."""
    q = p - np.asarray(origin, dtype=float)
    return q if rot is None else q @ rot


def sphere(p, c, r):
    return _len(p - np.asarray(c, dtype=float)) - r


def ellipsoid(p, c, radii):
    r = np.asarray(radii, dtype=float)
    q = p - np.asarray(c, dtype=float)
    k0 = _len(q / r)
    k1 = _len(q / (r * r))
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def capsule(p, a, b, r):
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    pa, ba = p - a, b - a
    h = np.clip((pa @ ba) / max(ba @ ba, 1e-9), 0.0, 1.0)
    return _len(pa - np.outer(h, ba)) - r


def round_cone(p, a, b, r1, r2):
    """Cone between sphere(a, r1) and sphere(b, r2) with tangent sides."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    ba = b - a
    l2 = ba @ ba
    rr = r1 - r2
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = p - a
    y = pa @ ba
    z = y - l2
    xv = pa * l2 - np.outer(y, ba)
    x2 = np.einsum("ij,ij->i", xv, xv)
    y2 = y * y * l2
    z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d = np.where(
        np.sign(z) * a2 * z2 > k,
        np.sqrt(np.maximum(x2 + z2, 0)) * il2 - r2,
        np.where(
            np.sign(y) * a2 * y2 < k,
            np.sqrt(np.maximum(x2 + y2, 0)) * il2 - r1,
            (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - r1,
        ),
    )
    return d


def cylinder_y(q, r, h, round_r=0.0):
    """Capped cylinder along local y, half-height h, edge rounding round_r."""
    dx = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2) - (r - round_r)
    dy = np.abs(q[:, 1]) - (h - round_r)
    outside = np.sqrt(np.maximum(dx, 0) ** 2 + np.maximum(dy, 0) ** 2)
    return np.minimum(np.maximum(dx, dy), 0.0) + outside - round_r


def ellip_cylinder_y(q, rx, rz, h, round_r=0.0):
    """Cylinder with elliptical cross-section (approximate distance)."""
    s = min(rx, rz)
    qq = q.copy()
    qq[:, 0] *= s / rx
    qq[:, 2] *= s / rz
    return cylinder_y(qq, s, h, round_r)


def box(q, half, round_r=0.0):
    half = np.asarray(half, dtype=float) - round_r
    d = np.abs(q) - half
    outside = _len(np.maximum(d, 0.0))
    return outside + np.minimum(d.max(axis=1), 0.0) - round_r


def torus_y(q, R, r):
    xz = np.sqrt(q[:, 0] ** 2 + q[:, 2] ** 2) - R
    return np.sqrt(xz ** 2 + q[:, 1] ** 2) - r


def smin(a, b, k):
    """Polynomial smooth minimum: blends two distances over width k."""
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    return -smin(-a, -b, k)
