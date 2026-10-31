import sys, time
import numpy as np
from PIL import Image
from src.render import render, DIRECTIONS
from src.rig import Pose

def sheet(frames, scale=6, bg=(236, 228, 206)):
    n = len(frames)
    W = 64 * scale
    im = Image.new("RGBA", (W * n, W), bg + (255,))
    for i, f in enumerate(frames):
        fi = Image.fromarray(f, "RGBA").resize((W, W), Image.NEAREST)
        im.alpha_composite(fi, (i * W, 0))
    return im

t0 = time.time()
dirs = sys.argv[1].split(",") if len(sys.argv) > 1 else DIRECTIONS
frames = []
for d in dirs:
    t = time.time()
    frames.append(render(Pose(), d))
    print(d, round(time.time() - t, 2), "s")
sheet(frames).save("out/dev/turnaround.png")
sheet(frames, 1).save("out/dev/turnaround_1x.png")
sheet(frames, 6, (24, 30, 48)).save("out/dev/turnaround_dark.png")
print("total", round(time.time() - t0, 1))
