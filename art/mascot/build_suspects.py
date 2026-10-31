"""Render the suspects: sheets (8 directions) and portraits with talk frames.

    python build_suspects.py            # all of them
    python build_suspects.py karat      # just one
"""
import os
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

from src.render import render, render_portrait, DIRECTIONS
from src.rig import Pose
from src.suspects import CHARS, VCENTRE

OUT = os.path.join(os.path.dirname(__file__), "out", "suspects")
CELL = 64
TAU = 2 * np.pi


def idle(i, n):
    return Pose(extra={"bob": 0.8 * np.sin(TAU * i / n), "squash": 1 - 0.015 * (1 - np.cos(TAU * i / n)), "ph": i / n},
                blink=1.0 if i == 5 else 0.0)


def talk(i, n):
    return Pose(extra={"bob": 0.6 * np.sin(2 * TAU * i / n), "tilt": 0.05 * np.sin(TAU * i / n), "arm": "talk", "ph": i / n},
                eyes="happy" if i in (2, 3) else "neutral")


def nervous(i, n):
    return Pose(extra={"tilt": 0.06 * np.sin(4 * TAU * i / n), "bob": 0.3 * np.sin(4 * TAU * i / n), "arm": "wring", "ph": i / n},
                eyes="worried", look=(float(np.sin(TAU * i / n)), 0))


def shocked(i, n):
    t = i / (n - 1)
    return Pose(extra={"bob": 4.0 * np.sin(np.pi * min(t * 1.6, 1.0)), "squash": 1 + 0.12 * np.sin(np.pi * t),
                       "arm": "up", "amt": min(1.0, t * 2.5)},
                eyes="surprised")


ANIMS = {"idle": (idle, 8, 6, True), "talk": (talk, 8, 10, True), "nervous": (nervous, 8, 12, True),
         "shocked": (shocked, 6, 12, False)}
PEXPR = [("neutral", "neutral", "line"), ("smug", "smug", "smirk"), ("nervous", "worried", "frown"),
         ("shocked", "surprised", "o"), ("angry", "angry", "frown")]
GESTURE = {"neutral": "rest", "smug": "hips", "nervous": "wring", "shocked": "up", "angry": "point"}


def _task(a):
    who, name, d, i = a
    fn, n, _, _ = ANIMS[name]
    return who, name, d, i, render(fn(i, n), d, char_cls=CHARS[who])


def _ptask(a):
    who, k, eyes, mouth, talkf = a
    m = mouth if talkf == 0 else ("open" if talkf == 1 else "wide")
    cfg = dict(size=96, zoom=2.4, v_center=VCENTRE[who])
    return who, k, talkf, render_portrait(Pose(eyes=eyes, extra={"arm": GESTURE[k]}), yaw_deg=14.0, mouth=m, char_cls=CHARS[who], cfg=cfg)


if __name__ == "__main__":
    who_list = sys.argv[1].split(",") if len(sys.argv) > 1 else list(CHARS)
    os.makedirs(OUT, exist_ok=True)
    tasks = [(w, nm, d, i) for w in who_list for nm, (fn, n, _, _) in ANIMS.items() for d in DIRECTIONS for i in range(n)]
    ptasks = [(w, k, e, m, t) for w in who_list for k, e, m in PEXPR for t in range(3)]
    with Pool(11) as pool:
        frames = {(w, nm, d, i): img for w, nm, d, i, img in pool.imap_unordered(_task, tasks)}
        ports = {(w, k, t): img for w, k, t, img in pool.imap_unordered(_ptask, ptasks)}
    for w in who_list:
        for nm, (fn, n, fps, loop) in ANIMS.items():
            sheet = np.zeros((CELL * 8, CELL * n, 4), np.uint8)
            for r, d in enumerate(DIRECTIONS):
                for i in range(n):
                    sheet[r * CELL:(r + 1) * CELL, i * CELL:(i + 1) * CELL] = frames[(w, nm, d, i)]
            Image.fromarray(sheet).save(os.path.join(OUT, f"{w}_{nm}.png"))
        P = np.zeros((96 * len(PEXPR), 96 * 3, 4), np.uint8)
        for r, (k, _, _) in enumerate(PEXPR):
            for t in range(3):
                P[r * 96:(r + 1) * 96, t * 96:(t + 1) * 96] = ports[(w, k, t)]
        Image.fromarray(P).save(os.path.join(OUT, f"{w}_portraits.png"))
    print("done", len(frames), "frames")
