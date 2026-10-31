"""Pre-rendered 3D environments as pixel art, matched to the Smudge sprites.

Same camera (orthographic, 20 deg pitch) and the same camera-fixed key light
as the mascot, plus coloured point lights, emissive materials, procedural
surface patterns and ordered dithering between ramp tones.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mascot"))
from src import sdf  # noqa: E402,F401
from src.render import RAY, RIGHT, UP, VIEW, L_KEY, L_RIM, L_FILL, PITCH  # noqa: E402

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.5


def hexrgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float64)


class Obj:
    """A bounded piece of the scene. fn(points) -> (dist, mat_ids)."""

    def __init__(self, fn, lo, hi, name=""):
        self.fn = fn
        self.lo = np.asarray(lo, float)
        self.hi = np.asarray(hi, float)
        self.name = name

    def bound(self, p):
        c = (self.lo + self.hi) / 2
        h = (self.hi - self.lo) / 2
        q = np.abs(p - c) - h
        return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0)


class World:
    def __init__(self, objs):
        self.objs = objs

    def without(self, names):
        return World([o for o in self.objs if o.name not in names])

    def eval(self, p):
        d = np.full(len(p), 1e9)
        m = np.zeros(len(p), int)
        for o in self.objs:
            b = o.bound(p)
            near = b < np.minimum(d, 4.0) + 0.5
            if not near.any():
                d = np.minimum(d, np.where(near, d, b + 0.5))
                continue
            idx = np.nonzero(near)[0]
            od, om = o.fn(p[idx])
            od = np.asarray(od, float)
            om = np.broadcast_to(np.asarray(om), od.shape)
            closer = od < d[idx]
            d[idx] = np.where(closer, od, d[idx])
            m[idx] = np.where(closer, om, m[idx])
            far = ~near
            d[far] = np.minimum(d[far], b[far] + 0.5)
        return d, m


class Light:
    def __init__(self, pos, colour, power, radius, shadow=True, ignore=()):
        self.ignore = tuple(ignore)
        self.pos = np.asarray(pos, float)
        self.colour = hexrgb(colour) / 255.0
        self.power = power
        self.radius = radius
        self.shadow = shadow


def _normals(world, p):
    e = 0.05
    n = np.stack([world.eval(p + d)[0] - world.eval(p - d)[0]
                  for d in (np.array([e, 0, 0]), np.array([0, e, 0]), np.array([0, 0, e]))], 1)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)


def _soft_shadow(world, p, ldir, maxt=60.0, k=7.0, steps=40):
    res = np.ones(len(p))
    t = np.full(len(p), 0.4)
    alive = np.ones(len(p), bool)
    for _ in range(steps):
        idx = np.nonzero(alive)[0]
        if not len(idx):
            break
        dl = ldir[idx] if ldir.ndim == 2 else ldir
        d, _ = world.eval(p[idx] + t[idx, None] * dl)
        res[idx] = np.minimum(res[idx], k * d / t[idx])
        t[idx] += np.clip(d, 0.2, 4.0)
        lim = maxt if np.isscalar(maxt) else maxt[idx]
        alive[idx] = (res[idx] > 0.02) & (t[idx] < lim)
    return np.clip(res, 0, 1)


def _ao(world, p, n):
    occ = np.zeros(len(p))
    w = 1.0
    for h in (0.8, 1.8, 3.2, 5.0, 7.5):
        d, _ = world.eval(p + n * h)
        occ += w * np.maximum(h - d, 0)
        w *= 0.6
    return np.clip(1 - 0.16 * occ, 0, 1)


# pixels per world unit. 1 = the game's sprites; 2 = high-res renders (the trailer). Set SMUDGE_SCALE=2.
SCALE = int(os.environ.get("SMUDGE_SCALE", "1"))


def render(world, materials, width, height, centre, lights=(), ss=2, top=120.0,
           key=1.0, ambient=0.12, sky=None, steps=140, y_off=0):
    """Returns RGBA uint8 (h, w, 4), plus depth and material maps at pixel res.

    centre: (u, v) world coordinates at the middle of the frame.
    materials: id -> dict(ramp=[hex...], pattern=fn(p, n) -> tone shift array,
               emissive=bool, gloss=float, colour_fn=fn(p, n)->ramp index override or None)
    """
    wu, hu = width, height                       # world units across the frame
    width, height = int(round(wu * SCALE)), int(round(hu * SCALE))   # pixels from here on
    W, H = width * ss, height * ss
    xs = (np.arange(W) + 0.5) / (ss * SCALE) - wu / 2 + centre[0]
    ys = centre[1] + (hu / 2 - (np.arange(H) + 0.5) / (ss * SCALE))
    uu, vv = np.meshgrid(xs, ys)
    o = uu.reshape(-1, 1) * RIGHT + vv.reshape(-1, 1) * UP
    # start each ray where it crosses the top of the world (y = top); may be behind the screen plane
    t = (top - o[:, 1]) / RAY[1]
    hit = np.zeros(len(o), bool)
    alive = np.ones(len(o), bool)
    tmax = t + 1400.0
    for _ in range(steps):
        idx = np.nonzero(alive)[0]
        if not len(idx):
            break
        p = o[idx] + t[idx, None] * RAY
        d, _ = world.eval(p)
        done = d < 0.03
        hit[idx[done]] = True
        t[idx] += np.maximum(d * 0.9, 0.03)
        gone = (t[idx] > tmax[idx]) | (p[:, 1] < -80)
        alive[idx[done | gone]] = False

    N = len(o)
    out_rgb = np.zeros((N, 3))
    tone_f = np.zeros(N)
    mat = np.zeros(N, int)
    hi = np.nonzero(hit)[0]
    if len(hi):
        p = o[hi] + t[hi, None] * RAY
        _, m = world.eval(p)
        for mid, spec in materials.items():
            if "sub" in spec:
                fn, other = spec["sub"]
                sel = m == mid
                if sel.any():
                    m[np.nonzero(sel)[0][fn(p[sel])]] = other
        for mid, spec in materials.items():
            if "submap" in spec:
                sel = np.nonzero(m == mid)[0]
                if len(sel):
                    new = spec["submap"](p[sel])
                    m[sel[new > 0]] = new[new > 0]
        n = _normals(world, p)
        mat[hi] = m
        ndl = n @ L_KEY
        sh = _soft_shadow(world, p + n * 0.3, L_KEY) if key > 0 else np.zeros(len(p))
        ao = _ao(world, p, n)
        diff = np.clip(ndl * 0.65 + 0.35, 0, 1) ** 1.3 * (0.2 + 0.8 * sh) * key
        fill = 0.1 * np.clip(n @ L_FILL, 0, 1)
        light = ambient + diff + fill
        warm = np.zeros((len(p), 3))
        for L in lights:
            to = L.pos - p
            dist = np.linalg.norm(to, axis=1)
            ld = to / dist[:, None]
            att = np.clip(1 - dist / L.radius, 0, 1) ** 2 * L.power
            nd = np.clip((n * ld).sum(1) * 0.7 + 0.3, 0, 1)
            sw = world.without(L.ignore) if L.ignore else world
            s = _soft_shadow(sw, p + n * 0.3, ld, maxt=dist - 10.0, k=16) if L.shadow else 1.0
            contrib = att * nd * s
            light = light + contrib
            warm += contrib[:, None] * L.colour[None, :]
        light = light * (0.55 + 0.45 * ao)
        rim = (1 - np.clip(n @ VIEW, 0, 1)) ** 2.2 * np.clip(n @ L_RIM + 0.3, 0, 1)
        tone_f[hi] = light
        # keep per-hit extras for shading
        extra = dict(p=p, n=n, rim=rim, warm=warm, ao=ao)
    else:
        extra = None

    # resolve supersamples: majority material, mean light
    hitg = hit.reshape(height, ss, width, ss).transpose(0, 2, 1, 3).reshape(height, width, ss * ss)
    matg = mat.reshape(height, ss, width, ss).transpose(0, 2, 1, 3).reshape(height, width, ss * ss)
    full_light = np.zeros(N)
    full_light[hit] = tone_f[hit]
    lg = full_light.reshape(height, ss, width, ss).transpose(0, 2, 1, 3).reshape(height, width, ss * ss)
    warm_full = np.zeros((N, 3))
    rim_full = np.zeros(N)
    pat_full = np.zeros(N)
    emis_full = np.zeros(N, bool)
    gloss_full = np.zeros(N)
    pos_full = np.zeros((N, 3))
    if extra is not None:
        warm_full[hi] = extra["warm"]
        rim_full[hi] = extra["rim"]
        pos_full[hi] = extra["p"]
        for mid, spec in materials.items():
            sel = mat[hi] == mid
            if not sel.any():
                continue
            if "pattern" in spec:
                pat_full[hi[sel]] = spec["pattern"](extra["p"][sel], extra["n"][sel])
            if spec.get("emissive"):
                emis_full[hi[sel]] = True
            if spec.get("gloss"):
                hvec = L_KEY + VIEW
                hvec = hvec / np.linalg.norm(hvec)
                gloss_full[hi[sel]] = np.clip(extra["n"][sel] @ hvec, 0, 1) ** spec["gloss"]

    def grid(a, ch=None):
        if ch:
            return a.reshape(height, ss, width, ss, ch).transpose(0, 2, 1, 3, 4).reshape(height, width, ss * ss, ch)
        return a.reshape(height, ss, width, ss).transpose(0, 2, 1, 3).reshape(height, width, ss * ss)

    warmg, rimg, patg, emisg, glossg = grid(warm_full, 3), grid(rim_full), grid(pat_full), grid(emis_full), grid(gloss_full)
    tg = grid(np.where(hit, t, np.inf))

    img = np.zeros((height, width, 4), np.uint8)
    pmat = np.zeros((height, width), int)
    pdep = np.full((height, width), np.inf)
    cov = hitg.sum(-1)
    filled = cov * 2 >= ss * ss
    for y, x in zip(*np.nonzero(filled)):
        h = hitg[y, x]
        mm = matg[y, x][h]
        vals, cnt = np.unique(mm, return_counts=True)
        best = vals[np.argmax(cnt)]
        sel = h & (matg[y, x] == best)
        spec = materials.get(best)
        if spec is None:
            continue
        ramp = spec["_rgb"]
        nT = len(ramp)
        if spec.get("emissive"):
            k = nT - 1 - int(patg[y, x][sel].mean() > 0.5)
            col = ramp[k]
        else:
            L = lg[y, x][sel].mean()
            L += 0.18 * (rimg[y, x][sel].max() > 0.35)
            L += patg[y, x][sel].mean() * spec.get("pattern_gain", 0.18)
            # ordered dither between ramp steps
            f = np.clip(L * spec.get("expo", 1.0), 0, 1.15) * (nT - 1) + BAYER4[(y + y_off) % 4, x % 4] * spec.get("dither", 0.22)
            k = int(np.clip(np.floor(f + 0.5), 0, nT - 1))
            col = ramp[k].astype(float)
            w = warmg[y, x][sel].mean(0)
            if w.max() > 0.02:
                tint = spec.get("warm_tint", 0.55) * np.clip(w.max(), 0, 1)
                hue = w / max(w.max(), 1e-6)
                col = col * (1 - tint) + tint * col * (0.35 + 0.9 * hue)
            if glossg[y, x][sel].max() > 0.6:
                col = spec.get("_spec", ramp[-1]).astype(float)
        img[y, x, :3] = np.clip(col, 0, 255).astype(np.uint8)
        img[y, x, 3] = 255
        pmat[y, x] = best
        pdep[y, x] = tg[y, x][sel].min()
    if sky is not None:
        bg = ~filled
        img[bg] = sky[bg]
    return img, pdep, pmat


def outline(img, pdep, pmat, materials, gap=4.0):
    """Darken pixels that sit just behind a much nearer neighbour (object edges)."""
    h, w = pmat.shape
    filled = img[:, :, 3] > 0
    out = img.copy()
    for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        nd = np.roll(np.roll(np.where(filled, pdep, 1e9), dy, 0), dx, 1)
        nm = np.roll(np.roll(pmat, dy, 0), dx, 1)
        edge = filled & (pdep - nd > gap) & (nm > 0) & (nm != pmat)
        for mid, spec in materials.items():
            m = edge & (pmat == mid)
            if m.any() and not spec.get("emissive"):
                out[m, :3] = spec["_rgb"][0]
    sil = filled & ~(np.roll(filled, 1, 0) & np.roll(filled, -1, 0) & np.roll(filled, 1, 1) & np.roll(filled, -1, 1))
    for mid, spec in materials.items():
        m = sil & (pmat == mid)
        if m.any() and not spec.get("emissive"):
            out[m, :3] = spec["_rgb"][0]
    return out


def prep(materials):
    for spec in materials.values():
        spec["_rgb"] = np.array([hexrgb(c) for c in spec["ramp"]])
        if "spec" in spec:
            spec["_spec"] = hexrgb(spec["spec"])
    return materials


def gradient_sky(width, height, top_hex, bottom_hex, glow=None):
    """Vertical gradient background, dithered into 6 bands; optional (x, y, r, hex) glow."""
    a, b = hexrgb(top_hex), hexrgb(bottom_hex)
    out = np.zeros((height, width, 4), np.uint8)
    for y in range(height):
        for x in range(width):
            f = y / max(height - 1, 1)
            if glow:
                gx, gy, gr, gh = glow
                g = max(0.0, 1 - np.hypot(x - gx, (y - gy) * 1.3) / gr)
            else:
                g = 0.0
            f6 = np.floor(f * 6 + BAYER4[y % 4, x % 4] * 0.9) / 6
            col = a * (1 - f6) + b * f6
            if glow and g > 0:
                g6 = np.floor(g * 5 + BAYER4[y % 4, x % 4]) / 5
                col = col * (1 - 0.6 * g6) + hexrgb(gh) * 0.6 * g6
            out[y, x, :3] = np.clip(col, 0, 255)
            out[y, x, 3] = 255
    return out


def stars(sky, n, seed=7, ymax=None, hexes=("#FFF6D8", "#C9D8FF", "#FFFFFF")):
    """Scatter n one-pixel stars (a few with a cross twinkle) over the top of a sky image, in place."""
    rng = np.random.default_rng(seed)
    h, w = sky.shape[:2]
    ymax = ymax or h // 2
    for i in range(n):
        x, y = int(rng.integers(1, w - 1)), int(rng.integers(1, ymax))
        c = hexrgb(hexes[i % len(hexes)])
        a = 0.35 + 0.65 * (1 - y / ymax) * rng.random()
        sky[y, x, :3] = np.clip(sky[y, x, :3] * (1 - a) + c * a, 0, 255)
        if i % 17 == 0:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                sky[y + dy, x + dx, :3] = np.clip(sky[y + dy, x + dx, :3] * 0.6 + c * 0.4, 0, 255)
    return sky


def moon(sky, cx, cy, r, hex_lit="#FFF2C8", hex_dark="#C9B98A", halo="#5A6A9A"):
    """A pixel moon with a crater or two and a dithered halo, painted into a sky image in place."""
    h, w = sky.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.hypot(xx - cx, yy - cy)
    g = np.clip(1 - (d - r) / (r * 2.2), 0, 1) * (d > r)
    g6 = np.floor(g * 4 + BAYER4[yy % 4, xx % 4] * 0.9) / 4
    sky[:, :, :3] = np.clip(sky[:, :, :3] * (1 - 0.35 * g6[..., None]) + hexrgb(halo) * 0.35 * g6[..., None], 0, 255)
    disc = d <= r
    shade = (xx - cx) * 0.6 + (yy - cy) * 0.4 > r * 0.35
    sky[disc] = np.append(hexrgb(hex_lit), 255)
    sky[disc & shade] = np.append(hexrgb(hex_dark), 255)
    for ox, oy, cr in ((-0.3, -0.2, 0.22), (0.25, 0.3, 0.16), (0.35, -0.35, 0.1)):
        crater = np.hypot(xx - (cx + ox * r), yy - (cy + oy * r)) <= cr * r
        sky[disc & crater, :3] = hexrgb(hex_dark)
    return sky


def _strip(args):
    import importlib
    mod, y0, y1, kw = args                       # y0, y1 in output pixels
    scene = importlib.import_module(mod).build(**kw)
    prep(scene["materials"])
    W, H = scene["width"], scene["height"]
    cu, cv = scene["centre"]
    cv_strip = cv + H / 2 - (y0 + y1) / 2 / SCALE
    img, dep, mat = render(scene["world"], scene["materials"], W, (y1 - y0) / SCALE, (cu, cv_strip),
                           lights=scene.get("lights", ()), ss=scene.get("ss", 2), top=scene.get("top", 120.0),
                           key=scene.get("key", 1.0), ambient=scene.get("ambient", 0.12),
                           steps=scene.get("steps", 140), y_off=y0)
    return y0, img, dep, mat


def render_parallel(mod, procs=11, strip=12, **kw):
    """Render scene module `mod` (which exposes build(**kw) -> dict) in horizontal strips."""
    import importlib
    from multiprocessing import Pool
    scene = importlib.import_module(mod).build(**kw)
    W, H = scene["width"] * SCALE, scene["height"] * SCALE
    jobs = [(mod, y, min(y + strip, H), kw) for y in range(0, H, strip)]
    img = np.zeros((H, W, 4), np.uint8)
    dep = np.full((H, W), np.inf)
    mat = np.zeros((H, W), int)
    with Pool(procs) as pool:
        for y0, im, dp, mt in pool.imap_unordered(_strip, jobs):
            img[y0:y0 + im.shape[0]] = im
            dep[y0:y0 + im.shape[0]] = dp
            mat[y0:y0 + im.shape[0]] = mt
    img = outline(img, dep, mat, prep(scene["materials"]))
    if scene.get("sky") is not None:
        sky = scene["sky"]
        if SCALE > 1:                            # skies are painted in world pixels; keep their dither crisp
            sky = np.repeat(np.repeat(sky, SCALE, 0), SCALE, 1)
        bg = img[:, :, 3] == 0
        img[bg] = sky[bg]
    for mid, colour, radius, strength in scene.get("bloom", []):
        img = bloom(img, mat == mid, colour, radius * SCALE, strength)
    if scene.get("post"):                        # screen-space finish (mist, grading), in output pixels
        img = scene["post"](img, dep, mat)
    return img, dep, mat, scene


def bloom(img, mask, colour, radius, strength):
    """Soft additive glow around emissive pixels, banded and dithered so it stays pixel art."""
    if not mask.any():
        return img
    h, w = mask.shape
    ys, xs = np.mgrid[0:h, 0:w]
    glow = np.zeros((h, w))
    pts = np.argwhere(mask)
    if len(pts) > 4000:
        pts = pts[np.random.default_rng(0).choice(len(pts), 4000, replace=False)]
    # distance to nearest emissive pixel, via chunks
    best = np.full((h, w), 1e9)
    for chunk in np.array_split(pts, max(1, len(pts) // 200)):
        dy = ys[None] - chunk[:, 0, None, None]
        dx = xs[None] - chunk[:, 1, None, None]
        best = np.minimum(best, np.sqrt(dx * dx + dy * dy).min(0))
    glow = np.clip(1 - best / radius, 0, 1) ** 1.6 * strength
    bands = np.floor(glow * 4 + BAYER4[ys % 4, xs % 4] * 0.9) / 4
    c = hexrgb(colour)
    out = img.copy().astype(float)
    a = bands[..., None]
    out[..., :3] = out[..., :3] + (c - out[..., :3] * 0.4) * a * 0.55
    out[..., 3] = np.maximum(out[..., 3], np.where(bands > 0, 255, 0))
    return np.clip(out, 0, 255).astype(np.uint8)
