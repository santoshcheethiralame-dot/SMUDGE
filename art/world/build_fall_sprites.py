"""The Midnight Fall's two small sprites, drawn pixel by pixel (they replace the flat placeholder shapes):

    sheet_ghost.png  64x32, two frames: 0 the Tower Ghost (a sheet with hollow eyes), 1 the same bedsheet on its line
    sack.png         16x16, the burlap sack dropped in the lab

Run: python art/world/build_fall_sprites.py   (writes into game/public/assets/case10)
"""
import math
from pathlib import Path

from PIL import Image

OUT = Path(__file__).resolve().parents[2] / "game/public/assets/case10"
BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def hexc(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5)) + (255,)


def shade(ramp, t, x, y):
    """t in 0..1 picked from the ramp with ordered dither between neighbouring steps."""
    v = max(0.0, min(0.999, t)) * (len(ramp) - 1)
    i = int(v)
    return ramp[min(len(ramp) - 1, i + (1 if (v - i) * 16 > BAYER[y % 4][x % 4] else 0))]


def paint(im, ox, mask, light, ramp, outline):
    """Fill a mask (set of (x, y)) with a lit ramp; the edge pixels take the outline colour."""
    for (x, y) in mask:
        edge = any((x + dx, y + dy) not in mask for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        im.putpixel((ox + x, y), outline if edge else shade(ramp, light(x, y), x, y))


SHEET = [hexc(c) for c in ("#6E7CA4", "#8E9CC0", "#B4C0DE", "#D6DEF0", "#EEF2FB", "#FFFFFF")]
SHEET_EDGE = hexc("#4A587E")


def ghost_frame(im):
    mask = set()
    for y in range(32):
        for x in range(32):
            head = (x - 16) ** 2 + (y - 10) ** 2 <= 8.6 ** 2
            half = min(13.5, 8.6 + max(0, y - 10) * 0.42) + (1.6 if 15 <= y <= 19 else 0)       # shoulders flare into arms
            hem = 25.5 + 3.2 * abs(math.sin((x - 2.5) * math.pi / 6.8))
            if head or (y >= 10 and abs(x - 16) <= half and y <= hem):
                mask.add((x, y))
    # lit from the top left; soft folds run down from the shoulders
    light = lambda x, y: 0.95 - 0.018 * (x - 6) - 0.012 * y + 0.13 * math.cos((x - 16) * 0.9) * (y > 14)
    paint(im, 0, mask, light, SHEET, SHEET_EDGE)
    hole, rim = hexc("#0B1026"), hexc("#2A3560")
    for ex in (12, 19):                                       # hollow eyes, taller than wide
        for y in range(8, 13):
            for x in (ex, ex + 1):
                im.putpixel((x, y), rim if y in (8, 12) else hole)
    for x, y in ((15, 15), (16, 15), (15, 16), (16, 16), (15, 17), (16, 17)):   # a small round "oo" mouth
        im.putpixel((x, y), hole if y == 16 else rim)


def sheet_frame(im):
    ox = 32
    line, wood, wood_hi = hexc("#2A1A10"), hexc("#6B4320"), hexc("#A06A34")
    mask = set()
    for y in range(3, 32):
        for x in range(32):
            hem = 25.0 + 2.6 * abs(math.sin((x - 4) * math.pi / 7.5))
            if 4 <= x <= 27 and y <= hem:
                mask.add((x, y))
    light = lambda x, y: 0.9 - 0.012 * (x - 4) - 0.01 * y + 0.16 * math.cos((x - 4) * 0.75)
    paint(im, ox, mask, light, SHEET, SHEET_EDGE)
    for x in range(32):
        im.putpixel((ox + x, 2), line)
    for px in (7, 15, 23):                                    # three wooden pegs over the line
        for y in range(1, 6):
            for x in (px, px + 1):
                im.putpixel((ox + x, y), wood_hi if x == px and y < 4 else wood)


SACK = [hexc(c) for c in ("#5A3A1E", "#7A5430", "#9C7044", "#BC8E5C", "#D8AE78", "#ECCC98")]
SACK_EDGE, ROPE, ROPE_HI = hexc("#2E1C0E"), hexc("#7A2A1A"), hexc("#B04A2E")


def sack(im):
    mask = set()
    for y in range(16):
        for x in range(16):
            body = ((x - 7.5) / 6.4) ** 2 + ((y - 10.2) / 5.4) ** 2 <= 1
            neck = 4 <= y <= 6 and abs(x - 7.5) <= 2.2
            tuft = 1 <= y <= 4 and abs(x - 7.5) <= 1.8 + (4 - y) * 0.8
            if body or neck or tuft:
                mask.add((x, y))
    light = lambda x, y: 0.92 - 0.05 * (x - 2) * 0.9 - 0.035 * (y - 5) + (0.06 if (x + y) % 3 == 0 else 0)   # weave
    paint(im, 0, mask, light, SACK, SACK_EDGE)
    for x in range(6, 10):                                    # the rope tie round the neck
        im.putpixel((x, 5), ROPE_HI if x < 8 else ROPE)
    for x, y in ((5, 11), (7, 12), (9, 10), (10, 13)):        # a few stitches
        im.putpixel((x, y), SACK[1])


if __name__ == "__main__":
    g = Image.new("RGBA", (64, 32), (0, 0, 0, 0))
    ghost_frame(g)
    sheet_frame(g)
    g.save(OUT / "sheet_ghost.png")
    s = Image.new("RGBA", (16, 16), (0, 0, 0, 0))
    sack(s)
    s.save(OUT / "sack.png")
    print("wrote", OUT / "sheet_ghost.png", OUT / "sack.png")
