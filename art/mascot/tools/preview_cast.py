"""Quick look at a cast: S/SE/E/N idle frames at 3x and the five portraits at 2x on paper."""
import sys
from multiprocessing import Pool

import numpy as np
from PIL import Image

sys.path.insert(0, __import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)), ".."))
from src.render import render, render_portrait  # noqa: E402
from src.rig import Pose  # noqa: E402
from src.suspects import CHARS, VCENTRE  # noqa: E402

FACES = ["S", "SE", "E", "N"]
PORTS = [("neutral", "line"), ("smug", "smirk"), ("worried", "frown"), ("surprised", "o"), ("angry", "frown")]


def _s(a):
    who, f = a
    return who, f, render(Pose(), f, char_cls=CHARS[who])


def _p(a):
    who, k = a
    e, m = PORTS[k]
    return who, k, render_portrait(Pose(eyes=e), yaw_deg=14.0, mouth=m, char_cls=CHARS[who], cfg=dict(size=96, zoom=2.4, v_center=VCENTRE[who]))


if __name__ == "__main__":
    who_list, out = sys.argv[1].split(","), sys.argv[2]
    with Pool(11) as pool:
        sp = {(w, f): i for w, f, i in pool.map(_s, [(w, f) for w in who_list for f in FACES])}
        pp = {(w, k): i for w, k, i in pool.map(_p, [(w, k) for w in who_list for k in range(5)])}
    rows = []
    for w in who_list:
        row = Image.new("RGBA", (64 * 4 * 3 + 96 * 5 * 2, 192), (242, 233, 207, 255))
        for j, f in enumerate(FACES):
            row.alpha_composite(Image.fromarray(sp[(w, f)]).resize((192, 192), Image.NEAREST), (j * 192, 0))
        for k in range(5):
            row.alpha_composite(Image.fromarray(pp[(w, k)]).resize((192, 192), Image.NEAREST), (768 + k * 192, 0))
        rows.append(row)
    sheet = Image.new("RGBA", (rows[0].width, 192 * len(rows)))
    for i, r in enumerate(rows):
        sheet.paste(r, (0, 192 * i))
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 2       # downscale factor; 1 keeps full size
    sheet.resize((sheet.width // k, sheet.height // k), Image.NEAREST).save(out)
    print("ok", out)
