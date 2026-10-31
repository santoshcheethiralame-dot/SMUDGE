import sys
from PIL import Image, ImageDraw
from src.anims import REGISTRY
names = sys.argv[1].split(",")
rows = sys.argv[2].split(",") if len(sys.argv) > 2 else ["S", "E"]
from src.render import DIRECTIONS
scale = int(sys.argv[3]) if len(sys.argv) > 3 else 2
maxf = max(REGISTRY[n]["frames"] for n in names)
H = 64 * scale
lab = 90
out = Image.new("RGBA", (lab + maxf * H, H * len(rows) * len(names)), (236, 228, 206, 255))
dr = ImageDraw.Draw(out)
y = 0
for nm in names:
    sh = Image.open(f"out/sheets/{nm}.png")
    for d in rows:
        r = DIRECTIONS.index(d)
        for i in range(REGISTRY[nm]["frames"]):
            c = sh.crop((i * 64, r * 64, (i + 1) * 64, (r + 1) * 64)).resize((H, H), Image.NEAREST)
            out.alpha_composite(c, (lab + i * H, y))
        dr.text((4, y + 4), f"{nm}\n{d}", fill=(40, 30, 20, 255))
        y += H
out.save("out/dev/contact.png")
