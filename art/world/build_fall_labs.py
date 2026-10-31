"""Case 10's lab art, drawn flat (front-on, no camera pitch) so the game can do real physics on it.

    python build_fall_labs.py

Writes to out/fall/: lab_tower.png and lab_gramophone.png (480x270), sack.png (16x16), sheet_ghost.png (two
32x32 frames: the ghost, then the plain sheet), and fall_layout.json, the pixel geometry LabFall needs:
ground line, pixels per metre, each balcony's floor, the chalk outline, the waveform strip.
"""
import json
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "out", "fall")
W, H = 480, 270
PX_PER_M = 10.0
GROUND = 250
WALL_X = 230                         # the tower's front face; the courtyard runs off to the right
TOWER_L = 150
BALCONIES = {"rivet": 4.9, "varnish": 11.0, "pendle": 19.6}
BANNER = {"rivet": "#B8251C", "varnish": "#2A5E46", "pendle": "#D8A63E"}
OUTLINE_M = 4.5                      # demo seed: 3 m/s x 1.5 s

INK, NIGHT, NIGHT2 = "#07090F", "#05060E", "#1A1A2E"
STONE, STONE_L, STONE_D = "#383846", "#484858", "#1C1C26"
COBBLE, COBBLE_D = "#282834", "#14141C"
PAPER, PAPER_D, RULE = "#E3D8B8", "#B3A584", "#8F8268"
WOOD, WOOD_L, WOOD_D = "#4A2A18", "#623A22", "#22120A"
BRASS, BRASS_L, BRASS_D = "#AC7A22", "#F6D070", "#4A2E08"
CANDLE, SHEET, SHEET_D, GHOST = "#F8C870", "#D8DCE6", "#8890A0", "#A8C8FF"


def _font(n, s):
    return ImageFont.truetype("C:/Windows/Fonts/" + n, s)


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def sky(w, h, top, bottom):
    """A vertical gradient in six dithered bands, like the rendered districts."""
    a, b = np.array(_rgb(top), float), np.array(_rgb(bottom), float)
    bayer = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    t = np.linspace(0, 1, h)[:, None] * 5 + bayer[np.arange(h) % 4][:, np.arange(w) % 4] - 0.5
    t = np.clip(np.round(t), 0, 5) / 5
    img = (a + (b - a) * t[..., None]).astype(np.uint8)
    return Image.fromarray(np.dstack([img, np.full((h, w), 255, np.uint8)]), "RGBA")


def y_of(m):
    return round(GROUND - m * PX_PER_M)


def lab_tower():
    im = sky(W, H, NIGHT, NIGHT2)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(5)
    for _ in range(40):
        x, y = rng.integers(0, W), rng.integers(0, 150)
        d.point((x, y), fill="#C9D8FF" if rng.random() < 0.5 else "#5A6A9A")
    d.ellipse((400, 20, 418, 38), fill="#D8DCEC")
    d.ellipse((404, 25, 409, 30), fill="#9AA0B8")
    # the tower, in coursed stone, with the clock at the top
    d.rectangle((TOWER_L, 20, WALL_X, GROUND), fill=STONE)
    for row, y in enumerate(range(20, GROUND, 6)):
        d.line((TOWER_L, y, WALL_X, y), fill=STONE_D)
        for x in range(TOWER_L + (5 if row % 2 else 0), WALL_X, 10):
            d.line((x, y, x, y + 5), fill=STONE_D)
    d.line((WALL_X, 20, WALL_X, GROUND), fill=STONE_L, width=2)
    d.polygon([(TOWER_L - 4, 20), (WALL_X + 4, 20), ((TOWER_L + WALL_X) / 2, -30)], fill="#1C2232")
    cx, cy = (TOWER_L + WALL_X) // 2, 34
    d.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), fill=BRASS)
    d.ellipse((cx - 9, cy - 9, cx + 9, cy + 9), fill=PAPER)
    d.line((cx, cy, cx, cy - 7), fill=INK, width=2)
    # the balconies, sticking out of the front face, each under a lit door, each flying its owner's banner
    floors = {}
    for sid, m in BALCONIES.items():
        y = y_of(m)
        floors[sid] = {"metres": m, "x": WALL_X + 18, "y": y}
        d.rectangle((WALL_X - 14, y - 22, WALL_X - 2, y - 1), fill=CANDLE)
        d.polygon([(WALL_X - 14, y - 22), (WALL_X - 2, y - 22), (WALL_X - 8, y - 28)], fill=CANDLE)
        d.rectangle((WALL_X, y, WALL_X + 30, y + 3), fill=STONE_L, outline=STONE_D)
        d.line((WALL_X + 30, y - 10, WALL_X + 30, y), fill="#6A7080", width=2)
        d.line((WALL_X, y - 10, WALL_X + 30, y - 10), fill="#6A7080", width=2)
        for x in range(WALL_X + 4, WALL_X + 30, 5):
            d.line((x, y - 10, x, y), fill="#6A7080")
        d.rectangle((WALL_X + 8, y + 4, WALL_X + 20, y + 18), fill=BANNER[sid])
        d.polygon([(WALL_X + 8, y + 18), (WALL_X + 20, y + 18), (WALL_X + 14, y + 13)], fill=STONE)
    # the courtyard: cobbles, the chalk outline 4.5 m out, a ground ruler in metres
    d.rectangle((0, GROUND, W, H), fill=COBBLE)
    for x in range(0, W, 7):
        d.line((x, GROUND + 1, x + 3, H), fill=COBBLE_D)
    ox = round(WALL_X + OUTLINE_M * PX_PER_M)
    d.ellipse((ox - 16, GROUND - 1, ox + 16, GROUND + 5), outline="#F2F4FA")
    d.ellipse((ox - 24, GROUND, ox - 16, GROUND + 4), outline="#F2F4FA")
    small = _font("arialbd.ttf", 8)
    for k in range(0, 23):
        x = WALL_X + k * PX_PER_M
        d.line((x, GROUND + 6, x, GROUND + (11 if k % 5 == 0 else 8)), fill=PAPER_D)
        if k % 5 == 0:
            d.text((x - 3, GROUND + 11), f"{k}", font=small, fill=PAPER)
    d.line((WALL_X, GROUND + 6, WALL_X + 220, GROUND + 6), fill=PAPER_D)
    # the metre strip up the wall: a tick every metre, numbered every five
    sx = TOWER_L - 22
    d.rectangle((sx, y_of(21), sx + 10, GROUND), fill=PAPER, outline=RULE)
    for k in range(0, 22):
        y = y_of(k)
        d.line((sx, y, sx + (10 if k % 5 == 0 else 5), y), fill=INK)
        if k % 5 == 0:
            d.text((sx - 14, y - 5), f"{k}", font=small, fill=PAPER)
    d.text((sx - 6, y_of(21) - 12), "m", font=small, fill=PAPER)
    im.save(os.path.join(OUT, "lab_tower.png"))
    return {"ground_y": GROUND, "px_per_m": PX_PER_M, "wall_x": WALL_X, "balconies": floors,
            "outline": {"x": ox, "y": GROUND + 2, "metres": OUTLINE_M}, "drop_from_x": WALL_X + 18}


def lab_gramophone():
    im = sky(W, H, "#0E0A08", "#2A1C12")
    d = ImageDraw.Draw(im)
    # a desk under a lamp, the gramophone on the left, a long paper strip for the trace
    d.rectangle((0, 196, W, H), fill=WOOD)
    d.line((0, 196, W, 196), fill=WOOD_L, width=2)
    for y in range(204, H, 9):
        d.line((0, y, W, y), fill=WOOD_D)
    d.ellipse((150, -60, 330, 40), fill="#3A2614")
    d.polygon([(220, 0), (260, 0), (300, 40), (180, 40)], fill="#5A3A1C")
    # the gramophone
    d.rectangle((20, 150, 96, 196), fill=WOOD_L, outline=WOOD_D)
    d.ellipse((24, 140, 92, 156), fill="#0C0C10", outline="#16161C")
    d.line((84, 146, 96, 104), fill=BRASS, width=3)
    d.polygon([(92, 108), (100, 98), (150, 40), (170, 70), (104, 112)], fill=BRASS, outline=BRASS_D)
    d.ellipse((140, 34, 178, 82), fill=BRASS_L, outline=BRASS_D)
    d.ellipse((150, 46, 168, 70), fill=BRASS_D)
    # the paper strip: six seconds across, a tick every tenth, a number every second
    x0, x1, y0, y1 = 112, 468, 112, 188
    d.rectangle((x0 - 2, y0 - 2, x1 + 2, y1 + 2), fill=PAPER_D)
    d.rectangle((x0, y0, x1, y1), fill=PAPER)
    mid = (y0 + y1) // 2
    d.line((x0, mid, x1, mid), fill=RULE)
    small = _font("arialbd.ttf", 8)
    per_s = (x1 - x0) / 6.0
    for k in range(0, 61):
        x = round(x0 + k * per_s / 10)
        d.line((x, y1 - (6 if k % 10 == 0 else 3 if k % 5 == 0 else 1), x, y1), fill=RULE)
        if k % 10 == 0:
            d.text((x - 2, y1 + 3), f"{k // 10}", font=small, fill=PAPER)
    d.text((x1 + 6, y1 + 3), "s", font=small, fill=PAPER)
    im.save(os.path.join(OUT, "lab_gramophone.png"))
    return {"strip": {"x0": x0, "x1": x1, "y0": y0, "y1": y1, "mid": mid, "seconds": 6.0, "px_per_s": per_s}}


def sprites():
    # a flour sack, tied at the neck
    s = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    d = ImageDraw.Draw(s)
    d.ellipse((2, 5, 13, 15), fill="#C8B48A", outline="#5A4020")
    d.polygon([(5, 6), (10, 6), (9, 2), (6, 2)], fill="#C8B48A", outline="#5A4020")
    d.line((5, 5, 10, 5), fill="#5A4020")
    d.point([(6, 10), (9, 11), (7, 12)], fill="#86622E")
    s.save(os.path.join(OUT, "sack.png"))
    # the bedsheet: as the ghost (glowing, two holes for eyes), then just a sheet with pegs
    g = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    for f, (fill, edge) in enumerate(((GHOST, "#6A9AFF"), (SHEET, SHEET_D))):
        ox = f * 32
        d.line((ox, 2, ox + 31, 2), fill=WOOD_D)
        pts = [(ox + 4, 3), (ox + 28, 3), (ox + 29, 26), (ox + 25, 29), (ox + 21, 26), (ox + 16, 30), (ox + 11, 26),
               (ox + 7, 29), (ox + 3, 26)]
        d.polygon(pts, fill=fill, outline=edge)
        if f == 0:
            d.ellipse((ox + 10, 10, ox + 13, 14), fill=INK)
            d.ellipse((ox + 19, 10, ox + 22, 14), fill=INK)
        else:
            for px in (7, 16, 25):
                d.rectangle((ox + px, 1, ox + px + 1, 5), fill=WOOD_L)
    g.save(os.path.join(OUT, "sheet_ghost.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    import scene_manor as M
    district = {"width": M.W, "cu": M.CENTRE[0], "cv": M.CENTRE[1], "hotspots": M.HOTSPOTS,
                "clues": {"sheet": [M.BODY_X, 4, M.BODY_Z], "gramophone": [M.GRAM_X, 30, M.GRAM_Z],
                          "tower": [M.TOWER_X, 100, M.FRONT], "ghost": [272, 30, -70]},
                "balconies": {sid: [M.TOWER_X, hb, M.FRONT + 6] for sid, (hb, _) in zip(BALCONIES, M.BALCONIES)}}
    layout = {"district": district, "tower": lab_tower(), "gramophone": lab_gramophone(), "g": 9.8}
    sprites()
    with open(os.path.join(OUT, "fall_layout.json"), "w") as f:
        json.dump(layout, f, indent=1)
    print("ok", OUT)
