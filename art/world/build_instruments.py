"""Render every lab prop into game/public/assets/lab, plus a 3x contact sheet in out/instruments_x3.png.

    python build_instruments.py              all props
    python build_instruments.py dial,thermo  just these
"""
import os
import sys

from PIL import Image

from envrender import render_parallel
from scene_instruments import PROPS

DEST = os.path.join(os.path.dirname(__file__), "..", "..", "game", "public", "assets", "lab")

if __name__ == "__main__":
    names = sys.argv[1].split(",") if len(sys.argv) > 1 else list(PROPS)
    os.makedirs(DEST, exist_ok=True)
    os.makedirs("out", exist_ok=True)
    ims = []
    for n in names:
        img, *_ = render_parallel("scene_instruments", which=n, strip=8)
        im = Image.fromarray(img, "RGBA")
        im.save(os.path.join(DEST, f"lab_{n}.png"))
        ims.append(im)
        print(n, im.size)
    W = sum(i.width for i in ims) + 6 * len(ims)
    sheet = Image.new("RGBA", (W, max(i.height for i in ims)), (60, 52, 70, 255))
    x = 0
    for i in ims:
        sheet.alpha_composite(i, (x, 0))
        x += i.width + 6
    sheet.resize((sheet.width * 3, sheet.height * 3), Image.NEAREST).save("out/instruments_x3.png")
