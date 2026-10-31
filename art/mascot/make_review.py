"""Bundle every sheet + portraits into one self-contained review page."""
import base64
import json
import os

from src.anims import REGISTRY
from src.render import DIRECTIONS
from src.portraits import EXPR, FRAMES

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")


def b64(path):
    with open(path, "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


anims = [{"name": n, "frames": a["frames"], "fps": a["fps"], "loop": a["loop"], "group": a["group"],
          "src": b64(os.path.join(OUT, "sheets", f"{n}.png"))} for n, a in REGISTRY.items()]
data = {"anims": anims, "dirs": DIRECTIONS, "portraits": b64(os.path.join(OUT, "portraits.png")),
        "expr": list(EXPR), "pframes": FRAMES}

html = open(os.path.join(HERE, "review_template.html"), encoding="utf-8").read()
html = html.replace("/*DATA*/null", json.dumps(data))
with open(os.path.join(OUT, "review.html"), "w", encoding="utf-8") as f:
    f.write(html)
print("wrote", os.path.join(OUT, "review.html"), round(len(html) / 1e6, 2), "MB")
