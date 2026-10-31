import json
import os
import sys

import numpy as np
import pytest
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

from src.anims import REGISTRY  # noqa: E402
from src.render import DIRECTIONS  # noqa: E402
from src import palette as P  # noqa: E402

OUT = os.path.join(HERE, "out")
CELL = 64
ALLOWED = {P.hex_rgb(c) for c in P.all_colours()}


def sheet(name):
    return np.array(Image.open(os.path.join(OUT, "sheets", f"{name}.png")).convert("RGBA"))


def cells(name):
    s = sheet(name)
    for r, d in enumerate(DIRECTIONS):
        for i in range(REGISTRY[name]["frames"]):
            yield d, i, s[r * CELL:(r + 1) * CELL, i * CELL:(i + 1) * CELL]


@pytest.mark.parametrize("name", list(REGISTRY))
def test_sheet_shape(name):
    s = sheet(name)
    assert s.shape[:2] == (CELL * len(DIRECTIONS), CELL * REGISTRY[name]["frames"])


@pytest.mark.parametrize("name", list(REGISTRY))
def test_frames_present_and_unclipped(name):
    for d, i, c in cells(name):
        a = c[:, :, 3] > 0
        assert a.sum() > 40, f"{name} {d} {i} is empty"
        border = np.concatenate([a[0], a[-1], a[:, 0], a[:, -1]])
        assert not border.any(), f"{name} {d} {i} touches the cell edge"


@pytest.mark.parametrize("name", list(REGISTRY))
def test_palette_only(name):
    s = sheet(name)
    px = s[s[:, :, 3] > 0][:, :3]
    used = {tuple(int(v) for v in p) for p in np.unique(px, axis=0)}
    assert used <= ALLOWED, f"{name} uses off-palette colours {sorted(used - ALLOWED)[:5]}"


def _feet_row(c):
    rows = np.nonzero((c[:, :, 3] > 0).any(1))[0]
    return rows.max()


def test_walk_feet_stay_on_ground():
    # Side views only. On front/back views the forward foot is nearer the
    # camera and correctly sits lower on screen. Even side-on, the near leg is
    # ~3.5 units closer than the far one, which the 20 deg camera pitch turns
    # into ~1.2 px, so allow 2 px.
    for d in ("E", "W"):
        rows = [_feet_row(c) for dd, i, c in cells("walk") if dd == d]
        assert max(rows) - min(rows) <= 2, (d, rows)


def test_idle_does_not_jitter():
    for d in DIRECTIONS:
        cs = [c for dd, i, c in cells("idle") if dd == d]
        cx = [np.nonzero((c[:, :, 3] > 0).any(0))[0].mean() for c in cs]
        assert max(cx) - min(cx) <= 1.0, (d, cx)


def test_atlas_matches_anims():
    atlas = json.load(open(os.path.join(OUT, "smudge_atlas.json")))
    names = {f["filename"] for t in atlas["textures"] for f in t["frames"]}
    anims = json.load(open(os.path.join(OUT, "smudge_anims.json")))["anims"]
    want = {fr["frame"] for a in anims for fr in a["frames"]}
    assert want == names
    assert len(anims) == len(REGISTRY) * len(DIRECTIONS)
    for t in atlas["textures"]:
        w, h = Image.open(os.path.join(OUT, t["image"])).size
        assert (w, h) == (t["size"]["w"], t["size"]["h"]) and w <= 2048 and h <= 2048


def test_portraits():
    from src.portraits import EXPR, FRAMES
    s = np.array(Image.open(os.path.join(OUT, "portraits.png")))
    assert s.shape[:2] == (96 * len(EXPR), 96 * len(FRAMES))
