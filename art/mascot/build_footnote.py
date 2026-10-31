"""Render Footnote's sheets and portraits (same layout and atlas rules as Smudge)."""
import json
import os
from multiprocessing import Pool

import numpy as np
from PIL import Image

from src.render import render, render_portrait, DIRECTIONS
from src.rig import Pose
from src.footnote import Footnote

OUT = os.path.join(os.path.dirname(__file__), "out", "footnote")
CELL = 64
TAU = 2 * np.pi


def idle(i, n):
    ph = TAU * i / n
    return Pose(extra={"bob": 1.6 * np.sin(ph), "spin": 0.12 * np.sin(ph)}, eyes="neutral", blink=1.0 if i == 5 else 0.0)


def talk(i, n):
    ph = TAU * i / n
    return Pose(extra={"bob": 1.0 * np.sin(ph), "spin": 0.22 * np.sin(2 * ph), "stretch": 1.0 + 0.07 * np.sin(2 * ph)},
                eyes="happy" if i in (2, 3) else "neutral")


def pop(i, n):
    t = i / (n - 1)
    return Pose(extra={"pop": min(1.0, t * 1.3), "spin": TAU * t, "stretch": 1.0 + 0.15 * np.sin(np.pi * t)},
                eyes="surprised" if t > 0.6 else "closed")


def worried(i, n):
    ph = TAU * i / n
    return Pose(extra={"bob": 0.8 * np.sin(2 * ph), "spin": 0.06 * np.sin(4 * ph)}, eyes="worried")


def spin(i, n):
    return Pose(extra={"spin": TAU * i / n, "bob": 2.0 * np.sin(np.pi * i / n)}, eyes="happy")


ANIMS = {"foot_idle": (idle, 8, 6, True), "foot_talk": (talk, 8, 10, True), "foot_pop": (pop, 8, 12, False),
         "foot_worried": (worried, 8, 10, True), "foot_spin": (spin, 8, 14, False)}

PCFG = dict(size=96, zoom=3.0, v_center=20.0)
PEXPR = {"neutral": "neutral", "happy": "happy", "worried": "worried", "surprised": "surprised"}


def _task(a):
    name, d, i = a
    fn, n, _, _ = ANIMS[name]
    return name, d, i, render(fn(i, n), d, char_cls=Footnote)


def _ptask(e):
    return e, render_portrait(Pose(eyes=PEXPR[e], extra={"spin": 0.08}), yaw_deg=-12.0, char_cls=Footnote, cfg=PCFG)


if __name__ == "__main__":
    os.makedirs(os.path.join(OUT, "sheets"), exist_ok=True)
    tasks = [(nm, d, i) for nm, (fn, n, _, _) in ANIMS.items() for d in DIRECTIONS for i in range(n)]
    with Pool(11) as pool:
        frames = {(nm, d, i): img for nm, d, i, img in pool.imap_unordered(_task, tasks)}
        ports = dict(pool.map(_ptask, list(PEXPR)))
    anims = []
    for nm, (fn, n, fps, loop) in ANIMS.items():
        sheet = np.zeros((CELL * 8, CELL * n, 4), np.uint8)
        for r, d in enumerate(DIRECTIONS):
            for i in range(n):
                sheet[r * CELL:(r + 1) * CELL, i * CELL:(i + 1) * CELL] = frames[(nm, d, i)]
        Image.fromarray(sheet).save(os.path.join(OUT, "sheets", f"{nm}.png"))
        anims.append(dict(name=nm, frames=n, fps=fps, loop=loop))
    strip = np.concatenate([ports[e] for e in PEXPR], 1)
    Image.fromarray(strip).save(os.path.join(OUT, "portraits.png"))
    json.dump({"anims": anims, "dirs": DIRECTIONS, "portraits": list(PEXPR)}, open(os.path.join(OUT, "meta.json"), "w"), indent=1)
    print("footnote frames", len(frames))
