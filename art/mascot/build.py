"""Render every Smudge animation into sheets, an atlas, anim defs and previews.

    python build.py                 # everything
    python build.py --only walk,run # quick iteration
"""
import argparse
import json
import os
import time
from multiprocessing import Pool

import numpy as np
from PIL import Image

from src.render import render, render_portrait, DIRECTIONS
from src.portraits import EXPR, FRAMES, portrait_pose
from src.anims import REGISTRY

OUT = os.path.join(os.path.dirname(__file__), "out")
CELL = 64


def _task(args):
    name, d, i = args
    a = REGISTRY[name]
    return name, d, i, render(a["fn"](i, a["frames"]), d)


def _ptask(args):
    expr, fr = args
    pose, mouth = portrait_pose(expr, fr)
    return expr, fr, render_portrait(pose, mouth=mouth)


def write_portraits(procs):
    P = 96
    with Pool(procs) as pool:
        res = pool.map(_ptask, [(e, f) for e in EXPR for f in FRAMES])
    sheet = np.zeros((P * len(EXPR), P * len(FRAMES), 4), np.uint8)
    os.makedirs(os.path.join(OUT, "portraits"), exist_ok=True)
    for e, f, img in res:
        r, c = list(EXPR).index(e), FRAMES.index(f)
        sheet[r * P:(r + 1) * P, c * P:(c + 1) * P] = img
        Image.fromarray(img, "RGBA").save(os.path.join(OUT, "portraits", f"{e}_{f}.png"))
    Image.fromarray(sheet, "RGBA").save(os.path.join(OUT, "portraits.png"), optimize=True)


def render_all(names, procs):
    tasks = [(nm, d, i) for nm in names for d in DIRECTIONS for i in range(REGISTRY[nm]["frames"])]
    frames = {}
    with Pool(procs) as pool:
        for nm, d, i, img in pool.imap_unordered(_task, tasks, chunksize=2):
            frames[(nm, d, i)] = img
    return frames


def write_sheet(name, frames):
    n = REGISTRY[name]["frames"]
    sheet = np.zeros((CELL * len(DIRECTIONS), CELL * n, 4), np.uint8)
    for r, d in enumerate(DIRECTIONS):
        for i in range(n):
            sheet[r * CELL:(r + 1) * CELL, i * CELL:(i + 1) * CELL] = frames[(name, d, i)]
    os.makedirs(os.path.join(OUT, "sheets"), exist_ok=True)
    Image.fromarray(sheet, "RGBA").save(os.path.join(OUT, "sheets", f"{name}.png"), optimize=True)


def write_preview(name, frames, scale=4, bg=(236, 228, 206)):
    a = REGISTRY[name]
    n = a["frames"]
    W = CELL * scale
    imgs = []
    for i in range(n):
        im = Image.new("RGBA", (W * len(DIRECTIONS), W), bg + (255,))
        for c, d in enumerate(DIRECTIONS):
            fi = Image.fromarray(frames[(name, d, i)], "RGBA").resize((W, W), Image.NEAREST)
            im.alpha_composite(fi, (c * W, 0))
        imgs.append(im.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=255))
    os.makedirs(os.path.join(OUT, "previews"), exist_ok=True)
    imgs[0].save(os.path.join(OUT, "previews", f"{name}.gif"), save_all=True,
                 append_images=imgs[1:], duration=int(1000 / a["fps"]), loop=0, disposal=2)


def frames_from_sheets():
    frames = {}
    for nm, a in REGISTRY.items():
        s = np.array(Image.open(os.path.join(OUT, "sheets", f"{nm}.png")).convert("RGBA"))
        for r, d in enumerate(DIRECTIONS):
            for i in range(a["frames"]):
                frames[(nm, d, i)] = s[r * CELL:(r + 1) * CELL, i * CELL:(i + 1) * CELL]
    return frames


def write_atlas(frames, page=2048):
    per_row = page // CELL
    per_page = per_row * per_row
    keys = sorted(frames, key=lambda k: (list(REGISTRY).index(k[0]), DIRECTIONS.index(k[1]), k[2]))
    textures = []
    for p0 in range(0, len(keys), per_page):
        chunk = keys[p0:p0 + per_page]
        rows = (len(chunk) + per_row - 1) // per_row
        h = 1 << int(np.ceil(np.log2(rows * CELL)))
        img = np.zeros((h, page, 4), np.uint8)
        fr = []
        for j, (nm, d, i) in enumerate(chunk):
            x, y = (j % per_row) * CELL, (j // per_row) * CELL
            img[y:y + CELL, x:x + CELL] = frames[(nm, d, i)]
            fr.append({"filename": f"{nm}/{d}/{i}", "frame": {"x": x, "y": y, "w": CELL, "h": CELL},
                       "rotated": False, "trimmed": False,
                       "spriteSourceSize": {"x": 0, "y": 0, "w": CELL, "h": CELL},
                       "sourceSize": {"w": CELL, "h": CELL}})
        fname = f"smudge_atlas_{len(textures)}.png"
        Image.fromarray(img, "RGBA").save(os.path.join(OUT, fname), optimize=True)
        textures.append({"image": fname, "format": "RGBA8888", "size": {"w": page, "h": h},
                         "scale": 1, "frames": fr})
    with open(os.path.join(OUT, "smudge_atlas.json"), "w") as f:
        json.dump({"textures": textures, "meta": {"app": "smudge build.py", "version": "1"}}, f)
    anims = []
    for nm, a in REGISTRY.items():
        for d in DIRECTIONS:
            anims.append({"key": f"{nm}_{d}", "frameRate": a["fps"], "repeat": -1 if a["loop"] else 0,
                          "frames": [{"key": "smudge", "frame": f"{nm}/{d}/{i}"} for i in range(a["frames"])]})
    with open(os.path.join(OUT, "smudge_anims.json"), "w") as f:
        json.dump({"anims": anims}, f, indent=1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--portraits", action="store_true")
    ap.add_argument("--procs", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    args = ap.parse_args()
    if args.portraits:
        write_portraits(args.procs)
        raise SystemExit
    names = [n for n in args.only.split(",") if n] or list(REGISTRY)
    t0 = time.time()
    frames = render_all(names, args.procs)
    for nm in names:
        write_sheet(nm, frames)
        write_preview(nm, frames)
    write_atlas(frames_from_sheets())
    if not args.only:
        write_portraits(args.procs)
    print(f"rendered {len(frames)} frames in {time.time() - t0:.0f}s")
