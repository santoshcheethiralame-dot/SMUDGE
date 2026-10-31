"""python render_scene.py scene_title [out_name]  -> out/<name>.png (+ _x3 preview)"""
import os
import sys
import time

from PIL import Image

from envrender import render_parallel, SCALE

if __name__ == "__main__":
    mod = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else mod.replace("scene_", "")
    kw = dict(a.split("=") for a in sys.argv[3:])
    kw = {k: (v == "1") if v in ("0", "1") else v for k, v in kw.items()}
    t = time.time()
    img, dep, mat, scene = render_parallel(mod, **kw)
    os.makedirs("out", exist_ok=True)
    im = Image.fromarray(img, "RGBA")
    if SCALE > 1:                                # high-res render: no preview, its own name
        im.save(f"out/{name}_hd{SCALE}.png")
    else:
        im.save(f"out/{name}.png")
        im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(f"out/{name}_x3.png")
    print(f"{name}: {im.size} in {time.time() - t:.0f}s")
