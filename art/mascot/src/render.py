"""Raymarch a Character into a pixel-art frame.

Pipeline: supersampled raymarch -> lighting terms per subpixel ->
downsample to one material + one light value per pixel -> cel ramps ->
selective outline + depth-edge lines -> orphan cleanup -> face decals.
Lights are fixed to the camera, so every facing gets the same look.
"""
import numpy as np

from . import palette as P
from .rig import Character, Pose

SIZE = 64
SS = 3
PITCH = np.radians(20.0)
V_CENTER = 27.0          # world height of the frame's centre line (feet land on row ~60)
BOUND_C = np.array([0.0, 22.0, 0.0])
BOUND_R = 40.0

DIRECTIONS = ["S", "SE", "E", "NE", "N", "NW", "W", "SW"]
YAW = {d: np.radians(45 * i) for i, d in enumerate(DIRECTIONS)}

RAY = np.array([0.0, -np.sin(PITCH), -np.cos(PITCH)])
RIGHT = np.array([1.0, 0.0, 0.0])
UP = np.array([0.0, np.cos(PITCH), -np.sin(PITCH)])
VIEW = -RAY


def _n(v):
    v = np.asarray(v, dtype=float)
    return v / np.linalg.norm(v)


L_KEY = _n([-0.55, 0.78, 0.62])
L_RIM = _n([0.85, 0.35, -0.55])
L_FILL = _n([0.65, -0.15, 0.7])
H_KEY = _n(L_KEY + VIEW)

THRESH = np.array([0.24, 0.43, 0.62, 0.82])


def _rgb_table():
    tab = {}
    for mat, ramp in P.RAMPS.items():
        tab[mat] = np.array([P.hex_rgb(c) for c in ramp], dtype=np.uint8)
    return tab


RGB = _rgb_table()


def rgb():
    """The colour table, refreshed if a cast file has registered more ramps since import."""
    if len(RGB) != len(P.RAMPS):
        RGB.clear()
        RGB.update(_rgb_table())
    return RGB


class Scene:
    """World-space SDF for a character turned to a facing."""

    def __init__(self, pose: Pose, facing: str, char_cls=None):
        self.char = (char_cls or Character)(pose)
        self.yaw = YAW[facing] if isinstance(facing, str) else np.radians(facing)
        if pose.form or getattr(self.char, "billboard", False):
            # instruments stay readable: never turn more than 40 deg off front or back
            a = (self.yaw + np.pi) % (2 * np.pi) - np.pi
            base = 0.0 if abs(a) <= np.pi / 2 else np.pi * np.sign(a)
            off = np.clip(a - base, -np.radians(40), np.radians(40))
            self.yaw = base + off
        c, s = np.cos(self.yaw), np.sin(self.yaw)
        # local = R_y(-yaw) world ; world = R_y(yaw) local
        self.R = np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])

    def eval(self, pts):
        local = pts @ self.R      # == (R^T pts^T)^T
        return self.char.eval(local)

    def to_world(self, v):
        return self.R @ v


def _march(scene, origins, dirs_t0):
    t = dirs_t0.copy()
    n = len(origins)
    hit = np.zeros(n, bool)
    alive = np.ones(n, bool)
    t_max = dirs_t0 + 2 * BOUND_R
    for _ in range(96):
        idx = np.nonzero(alive)[0]
        if len(idx) == 0:
            break
        p = origins[idx] + np.outer(t[idx], RAY)
        d, _ = scene.eval(p)
        done = d < 0.04
        hit[idx[done]] = True
        t[idx] += np.maximum(d * 0.85, 0.02)
        gone = t[idx] > t_max[idx]
        alive[idx[done | gone]] = False
    return hit, t


def _normals(scene, p):
    e = 0.06
    nx = scene.eval(p + [e, 0, 0])[0] - scene.eval(p - [e, 0, 0])[0]
    ny = scene.eval(p + [0, e, 0])[0] - scene.eval(p - [0, e, 0])[0]
    nz = scene.eval(p + [0, 0, e])[0] - scene.eval(p - [0, 0, e])[0]
    n = np.stack([nx, ny, nz], 1)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)


def _shadow(scene, p, ldir):
    res = np.ones(len(p))
    t = np.full(len(p), 0.35)
    for _ in range(28):
        d, _ = scene.eval(p + np.outer(t, ldir))
        res = np.minimum(res, 6.0 * d / t)
        t += np.clip(d, 0.15, 2.5)
    return np.clip(res, 0.0, 1.0)


def _ao(scene, p, n):
    occ = np.zeros(len(p))
    w = 1.0
    for h in (0.7, 1.5, 2.6, 3.8, 5.2):
        d, _ = scene.eval(p + n * h)
        occ += w * np.maximum(h - d, 0)
        w *= 0.62
    return np.clip(1.0 - 0.22 * occ, 0.0, 1.0)


def raymarch(pose: Pose, facing, size=SIZE, ss=SS, v_center=V_CENTER, zoom=1.0, char_cls=None):
    scene = Scene(pose, facing, char_cls)
    n = size * ss
    coords = (np.arange(n) + 0.5) / ss
    u = (coords - size / 2) / zoom
    v = v_center + (size / 2 - coords) / zoom
    uu, vv = np.meshgrid(u, v)
    origins = (uu.reshape(-1, 1) * RIGHT + vv.reshape(-1, 1) * UP) - RAY * 70.0
    # bounding-sphere entry
    oc = origins - (BOUND_C + np.asarray(pose.root))
    b = oc @ RAY
    c = np.einsum("ij,ij->i", oc, oc) - BOUND_R ** 2
    disc = b * b - c
    inside = disc > 0
    t0 = np.where(inside, -b - np.sqrt(np.maximum(disc, 0)), 0.0)
    t0 = np.maximum(t0, 0.0)

    hit = np.zeros(len(origins), bool)
    t = np.zeros(len(origins))
    sub = np.nonzero(inside)[0]
    h, tt = _march(scene, origins[sub], t0[sub])
    hit[sub] = h
    t[sub] = tt

    out = {"hit": hit, "t": t, "mat": np.zeros(len(origins), int),
           "light": np.zeros(len(origins)), "rim": np.zeros(len(origins)),
           "spec": np.zeros(len(origins)), "n": n, "scene": scene}
    hi = np.nonzero(hit)[0]
    if len(hi) == 0:
        return out
    p = origins[hi] + np.outer(t[hi], RAY)
    _, mat = scene.eval(p)
    nrm = _normals(scene, p)
    ndl = nrm @ L_KEY
    wrap = np.clip(ndl * 0.6 + 0.4, 0, 1)
    sh = _shadow(scene, p + nrm * 0.25, L_KEY)
    sh = np.where(ndl > 0, sh, np.minimum(sh, 0.6))
    ao = _ao(scene, p, nrm)
    fill = np.clip(nrm @ L_FILL, 0, 1)
    light = 0.08 + 0.92 * (wrap ** 1.3) * (0.22 + 0.78 * sh)
    light = light * (0.55 + 0.45 * ao) + 0.08 * fill
    fres = (1 - np.clip(nrm @ VIEW, 0, 1)) ** 2.2
    rim = fres * np.clip(nrm @ L_RIM + 0.35, 0, 1)
    spec = np.clip(nrm @ H_KEY, 0, 1) ** 36 * sh
    out["mat"][hi] = mat
    out["light"][hi] = light
    out["rim"][hi] = rim
    out["spec"][hi] = spec
    return out


def _tone(light):
    return np.searchsorted(THRESH, light)


def resolve(buf, size=SIZE, ss=SS):
    """Downsample subpixels to pixel material/tone/depth."""
    hit = buf["hit"].reshape(size, ss, size, ss).transpose(0, 2, 1, 3).reshape(size, size, ss * ss)
    mat = buf["mat"].reshape(size, ss, size, ss).transpose(0, 2, 1, 3).reshape(size, size, ss * ss)
    light = buf["light"].reshape(size, ss, size, ss).transpose(0, 2, 1, 3).reshape(size, size, ss * ss)
    rim = buf["rim"].reshape(size, ss, size, ss).transpose(0, 2, 1, 3).reshape(size, size, ss * ss)
    spec = buf["spec"].reshape(size, ss, size, ss).transpose(0, 2, 1, 3).reshape(size, size, ss * ss)
    tt = np.where(buf["hit"], buf["t"], np.inf)
    tt = tt.reshape(size, ss, size, ss).transpose(0, 2, 1, 3).reshape(size, size, ss * ss)

    cov = hit.sum(-1)
    filled = cov * 2 >= ss * ss
    pm = np.zeros((size, size), int)
    pl = np.zeros((size, size))
    pr = np.zeros((size, size))
    ps = np.zeros((size, size))
    pd = np.full((size, size), np.inf)
    ys, xs = np.nonzero(filled)
    for y, x in zip(ys, xs):
        h = hit[y, x]
        m = mat[y, x][h]
        vals, cnt = np.unique(m, return_counts=True)
        # prefer the nearest material when counts tie, so thin parts survive
        best = vals[np.argmax(cnt)]
        sel = h & (mat[y, x] == best)
        pm[y, x] = best
        pl[y, x] = light[y, x][sel].mean()
        pr[y, x] = rim[y, x][sel].max()
        ps[y, x] = spec[y, x][sel].max()
        pd[y, x] = tt[y, x][sel].min()
    return pm, pl, pr, ps, pd


FAMILY = {P.COAT: 1, P.COAT_DARK: 1, P.BELT: 1, P.METAL: 1, P.PEN: 1, P.HAT: 2, P.BAND: 2}


def _same_family(a, b):
    fa = np.vectorize(lambda m: FAMILY.get(m, 100 + m))(a)
    fb = np.vectorize(lambda m: FAMILY.get(m, 100 + m))(b)
    return fa == fb


def _smooth_light(pm, pl):
    out = pl.copy()
    size = pm.shape[0]
    for y in range(size):
        for x in range(size):
            m = pm[y, x]
            if not m:
                continue
            y0, y1, x0, x1 = max(y - 1, 0), min(y + 2, size), max(x - 1, 0), min(x + 2, size)
            win = pl[y0:y1, x0:x1][pm[y0:y1, x0:x1] == m]
            out[y, x] = 0.5 * pl[y, x] + 0.5 * np.median(win)
    return out


def shade(pm, pl, pr, ps, pd):
    size = pm.shape[0]
    pl = _smooth_light(pm, pl)
    tone = np.where(pm > 0, _tone(pl), -1)
    tone = np.where((pr > 0.32) & (pm > 0), np.minimum(tone + 1, 4), tone)
    filled = pm > 0

    # orphan cleanup: a lone tone inside its own material takes the majority neighbour tone
    t2 = tone.copy()
    for y in range(1, size - 1):
        for x in range(1, size - 1):
            if not filled[y, x]:
                continue
            nb = [(y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)]
            same = [tone[a, b] for a, b in nb if filled[a, b] and pm[a, b] == pm[y, x]]
            if len(same) >= 3 and tone[y, x] not in same:
                vals, cnt = np.unique(same, return_counts=True)
                t2[y, x] = vals[np.argmax(cnt)]
    tone = t2

    img = np.zeros((size, size, 4), np.uint8)
    for mat, tab in rgb().items():
        m = pm == mat
        if m.any():
            img[m, :3] = tab[np.clip(tone[m], 0, 4)]
            img[m, 3] = 255

    # specular glints on glossy materials
    for mat in P.GLOSSY:
        m = (pm == mat) & (ps > 0.5)
        img[m, :3] = P.hex_rgb(P.SPECULAR[mat])

    # depth-edge lines: a pixel just behind a much nearer neighbour gets its darkest tone
    edge = np.zeros_like(filled)
    pdf = np.where(filled, pd, 1e9)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nd = np.roll(np.roll(pdf, dy, 0), dx, 1)
        nm = np.roll(np.roll(pm, dy, 0), dx, 1)
        gap = pdf - nd
        edge |= filled & (nm > 0) & (gap > 2.2)
        # a different part sitting in front of this one (sleeve over coat, hat over head)
        edge |= filled & (nm > 0) & (nm != pm) & (gap > 0.7) & ~_same_family(pm, nm)
    # silhouette: pixels touching empty space
    sil = np.zeros_like(filled)
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        sil |= filled & ~np.roll(np.roll(filled, dy, 0), dx, 1)
    for mat, tab in rgb().items():
        m = (pm == mat) & (edge | sil)
        img[m, :3] = tab[0]
    # very light ramps get a true outline on the silhouette so they don't bleed into paper
    light_mats = (pm == P.PAPER) | (pm == P.GLASS)
    img[sil & light_mats, :3] = P.hex_rgb(P.OUTLINE)
    return img, pm, pd


def project(world_pt, size=SIZE, v_center=V_CENTER, zoom=1.0):
    u = world_pt @ RIGHT
    v = world_pt @ UP
    x = u * zoom + size / 2
    y = size / 2 - (v - v_center) * zoom
    depth = -(world_pt @ VIEW)
    return x, y, depth


# Eye masks for the eye on the viewer's left, inner side = right.
# W white, S soft shade, . empty. Pupils are placed separately.
EYE_MASKS = {
    "open":   [".SS.", "WWWW", "WWWW", "WWWW", ".WW."],
    "wide":   [".SS.", "WWWW", "WWWW", "WWWW", "WWWW", ".WW."],
    "half":   ["....", "SSSS", "WWWW", ".WW."],
    "happy":  ["....", ".WW.", "W..W"],
    "closed": ["....", "....", "WWWW"],
    "angry":  ["S...", "WWS.", "WWWW", "WWWW", ".WW."],
    "worried": ["...S", ".SWW", "WWWW", "WWWW", ".WW."],
}
# Narrow eyes for side and far-3/4 views, drawn facing screen-right; P = pupil.
SIDE_MASKS = {
    "open":    ["SW", "WP", "WP", "WW"],
    "wide":    ["SW", "WW", "WP", "WP", "WW"],
    "half":    ["SS", "WP", "WW"],
    "happy":   ["WW", "W."],
    "closed":  ["..", "..", "WW"],
    "angry":   ["S.", "WP", "WP", "WW"],
    "worried": [".S", "WP", "WP", "WW"],
}

EXPRESSIONS = {
    # mask, pupil (w, h, row), brow style
    "neutral":    ("open", (2, 3, 1), None),
    "happy":      ("happy", None, None),
    "surprised":  ("wide", (2, 2, 2), "up"),
    "thinking":   ("open", (2, 2, 1), "flat"),
    "smug":       ("half", (2, 2, 1), "flat"),
    "determined": ("angry", (2, 2, 2), None),
    "angry":      ("angry", (2, 2, 2), "angry"),
    "worried":    ("worried", (2, 2, 2), None),
    "sad":        ("worried", (2, 2, 3), None),
    "closed":     ("closed", None, None),
}


def draw_face(img, pd, pose: Pose, scene: Scene, size=SIZE, pm=None, zoom=1, v_center=V_CENTER, mouth=None):
    anchors, scale = scene.char.face_anchor()
    if not anchors:
        return img
    expr = "closed" if pose.blink > 0.5 else pose.eyes
    mask_name, pupil_spec, brow = EXPRESSIONS.get(expr, EXPRESSIONS["neutral"])
    base = EYE_MASKS[mask_name]
    col = {"W": np.array(P.hex_rgb(P.EYE_WHITE)), "S": np.array(P.hex_rgb(P.EYE_SHADE))}
    pupil = np.array(P.hex_rgb(P.PUPIL))
    brow_c = np.array(P.hex_rgb(getattr(scene.char, "brow_hex", P.RAMPS[P.INK][4])))
    fwd = scene.to_world(scene.char.head_dir([0, 0, 1.0]))
    fwd_x = fwd @ RIGHT

    eyes = []
    for pt, nrm in anchors:
        wp = scene.to_world(pt)
        facing = scene.to_world(nrm) @ VIEW
        if facing < 0.2:
            continue
        x, y, depth = project(wp, size, v_center, zoom)
        xi, yi = int(np.floor(x)), int(np.floor(y))
        if not (0 <= xi < size and 0 <= yi < size):
            continue
        surf = pd[yi, xi]
        if np.isfinite(surf) and (depth + 70.0) - surf > 1.6 + 4.0 * (1 - facing):
            continue
        eyes.append((x, xi, yi, facing))
    if not eyes:
        return img
    eyes.sort()
    cx_mid = np.mean([e[0] for e in eyes])
    for x, xi, yi, facing in eyes:
        left = x <= cx_mid if len(eyes) == 2 else fwd_x < 0
        side_view = facing < 0.6
        if side_view:
            rows = list(SIDE_MASKS[mask_name])
            if fwd_x < 0:
                rows = [r[::-1] for r in rows]
        else:
            rows = [r for r in base]
            if scale < 1:
                rows = [r[:3] for r in rows[:4]]
            if not left:
                rows = [r[::-1] for r in rows]
        if zoom > 1:
            z = int(zoom)
            rows = ["".join(ch * z for ch in r) for r in rows for _ in range(z)]
        h, w = len(rows), len(rows[0])
        x0 = xi - w // 2
        y0 = yi - h // 2
        if pm is not None:
            ink = pm == getattr(scene.char, "skin", P.INK)
            cols = np.nonzero(ink[max(y0, 0):y0 + h].any(0))[0]
            centre = cols.mean() if len(cols) else xi
            step = 1 if centre > xi else -1
            placed = False
            for k, dyk in [(k, dy) for dy in (0, 1, -1, 2) for k in range(0, 6)]:
                xx0 = x0 + step * k
                yy0 = y0 + dyk
                ok = True
                for yy, r in enumerate(rows):
                    for xx, ch in enumerate(r):
                        X, Y = xx0 + xx, yy0 + yy
                        if ch != "." and not (0 <= X < size and 0 <= Y < size and ink[Y, X]):
                            ok = False
                    # keep one ink pixel between the eye and the outer silhouette
                    edge_x = xx0 - 1 if step > 0 else xx0 + w
                    Y = yy0 + yy
                    if 0 <= Y < size and r.strip(".") and not (0 <= edge_x < size and ink[Y, edge_x]):
                        ok = False
                if ok:
                    x0, y0 = xx0, yy0
                    placed = True
                    break
            if not placed:
                continue
        for yy, r in enumerate(rows):
            for xx, ch in enumerate(r):
                X, Y = x0 + xx, y0 + yy
                if 0 <= X < size and 0 <= Y < size and img[Y, X, 3]:
                    if ch in col:
                        img[Y, X, :3] = col[ch]
                    elif ch == "P":
                        img[Y, X, :3] = pupil
        if pupil_spec and not side_view:
            pw, ph, prow = pupil_spec
            if zoom > 1:
                z = int(zoom)
                pw, ph, prow = pw * z, ph * z, prow * z
            if len(eyes) == 1 or abs(fwd_x) > 0.35:
                toward_right = fwd_x > 0
            else:
                toward_right = left            # look inward on front views
            if w <= 3:
                pw = 1 if w <= 2 else min(pw, 2)
                px = (w - pw - (1 if w == 3 else 0)) if toward_right else (1 if w == 3 else 0)
            else:
                px = (w - pw) if toward_right else 0
            lx, ly = pose.look
            lx, ly = lx * max(1, int(zoom)), ly * max(1, int(zoom))
            px = int(np.clip(px + round(lx), 0, w - pw))
            py = int(np.clip(prow + round(ly), 0, h - ph))
            for yy in range(ph):
                for xx in range(pw):
                    X, Y = x0 + px + xx, y0 + py + yy
                    if 0 <= X < size and 0 <= Y < size and rows[py + yy][px + xx] in col:
                        img[Y, X, :3] = pupil
            cxp = x0 + px + (0 if toward_right else pw - 1)
            if ph >= 2 and pw >= 2 and rows[py][px] in col:
                img[y0 + py, cxp, :3] = col["W"]
        if brow:
            by = y0 - (2 if brow == "up" else 1)
            for xx in range(w + 1):
                X = x0 + xx - (1 if left else 0)
                k = xx if left else w - xx      # distance from the outer edge
                dy = {"flat": 0, "up": 0, "angry": k // 2 - 1}.get(brow, 0)
                for th in range(max(1, int(zoom))):
                    Y = by + dy - th
                    if 0 <= X < size and 0 <= Y < size and img[Y, X, 3]:
                        img[Y, X, :3] = brow_c
    if mouth and len(eyes) == 2:
        _draw_mouth(img, eyes, mouth, size, zoom)
    return img


MOUTHS = {
    "line":  ["LLLLLL"],
    "open":  [".LLLL.", "LDDDDL", ".LLLL."],
    "wide":  [".LLLL.", "LDDDDL", "LDRRDL", ".LLLL."],
    "smirk": ["....LL", "LLLL.."],
    "smile": ["L....L", ".LLLL."],
    "frown": [".LLLL.", "L....L"],
    "o":     [".LL.", "LDDL", ".LL."],
}


def _draw_mouth(img, eyes, mouth, size, zoom):
    cols = {"L": np.array(P.hex_rgb(P.MOUTH)), "D": np.array(P.hex_rgb(P.RAMPS[P.INK][0])),
            "R": np.array(P.hex_rgb(P.RAMPS[P.BAND][2]))}
    z = max(1, int(zoom))
    rows = ["".join(ch * z for ch in r) for r in MOUTHS[mouth] for _ in range(z)]
    cx = int(round(np.mean([e[1] for e in eyes])))
    cy = int(round(np.mean([e[2] for e in eyes]))) + int(3.2 * zoom)
    x0 = cx - len(rows[0]) // 2
    for yy, r in enumerate(rows):
        for xx, ch in enumerate(r):
            X, Y = x0 + xx, cy + yy
            if ch in cols and 0 <= X < size and 0 <= Y < size and img[Y, X, 3]:
                img[Y, X, :3] = cols[ch]


PORTRAIT = dict(size=96, zoom=2.4, v_center=33.5)


def render_portrait(pose: Pose, yaw_deg=18.0, mouth=None, char_cls=None, cfg=None):
    c = cfg or PORTRAIT
    buf = raymarch(pose, yaw_deg, size=c["size"], v_center=c["v_center"], zoom=c["zoom"], char_cls=char_cls)
    pm, pl, pr, ps, pd = resolve(buf, size=c["size"])
    img, pm, pd = shade(pm, pl, pr, ps, pd)
    return draw_face(img, pd, pose, buf["scene"], size=c["size"], pm=pm, zoom=c["zoom"],
                     v_center=c["v_center"], mouth=mouth)


def render(pose: Pose, facing: str, char_cls=None):
    buf = raymarch(pose, facing, char_cls=char_cls)
    pm, pl, pr, ps, pd = resolve(buf)
    img, pm, pd = shade(pm, pl, pr, ps, pd)
    img = draw_face(img, pd, pose, buf["scene"], pm=pm)
    return img
