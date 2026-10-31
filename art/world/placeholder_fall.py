"""Placeholder art for The Midnight Fall (case 10), so the game runs before the real art lands.
Writes game/public/assets/case10/*.png. Drop the real renders over the same names and nothing else changes.
Run: python3 art/world/placeholder_fall.py"""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).resolve().parents[2] / "game/public/assets/case10"
OUT.mkdir(parents=True, exist_ok=True)

NIGHT_TOP, NIGHT_BOT = (14, 18, 44), (36, 40, 78)
SUSPECTS = {"rivet": (150, 165, 185), "varnish": (224, 160, 48), "pendle": (64, 176, 160)}
# metres to pixels on the 720x270 backdrop; the courtyard floor is at y=206
FLOOR, PX_PER_M = 206, 5


def sky(d, w, h, top, bot):
    for y in range(h):
        t = y / h
        d.line([(0, y), (w, y)], fill=tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3)))


def courtyard(restored):
    im = Image.new("RGB", (720, 270))
    d = ImageDraw.Draw(im)
    sky(d, 720, 270, (230, 190, 150) if restored else NIGHT_TOP, (250, 226, 190) if restored else NIGHT_BOT)
    d.rectangle([0, FLOOR - 12, 720, 270], fill=(60, 56, 72) if not restored else (150, 140, 120))
    tx = 630                                                    # the tower, right third
    d.rectangle([tx - 34, 30, tx + 34, FLOOR - 10], fill=(70, 66, 92))
    d.polygon([(tx - 40, 30), (tx, 4), (tx + 40, 30)], fill=(50, 46, 70))
    d.ellipse([tx - 12, 38, tx + 12, 62], fill=(240, 230, 190))         # the clock
    for h, col in ((4.9, SUSPECTS["rivet"]), (11.0, SUSPECTS["varnish"]), (19.6, SUSPECTS["pendle"])):
        y = FLOOR - 10 - int(h * PX_PER_M)
        d.rectangle([tx - 44, y, tx + 44, y + 5], fill=col)              # balcony floor
        d.rectangle([tx - 44, y - 9, tx + 44, y - 7], fill=col)          # rail
        d.rectangle([tx - 10, y - 26, tx + 10, y - 6], fill=(20, 22, 40))
    d.line([(60, 120), (260, 130)], fill=(200, 200, 210), width=1)       # the washing line
    d.polygon([(110, 124), (170, 126), (166, 168), (116, 164)], fill=(235, 235, 245))   # a bedsheet
    d.ellipse([505 - 34, FLOOR - 4, 505 + 34, FLOOR + 12], outline=(235, 235, 245), width=1)   # chalk outline
    d.rectangle([470, FLOOR - 4, 540, FLOOR + 10], fill=(235, 235, 245))   # the white sheet
    d.polygon([(440, FLOOR), (462, FLOOR), (452, FLOOR - 20), (428, FLOOR - 26)], fill=(180, 140, 70))  # gramophone
    return im


def lab_tower():
    im = Image.new("RGB", (480, 270))
    d = ImageDraw.Draw(im)
    sky(d, 480, 270, NIGHT_TOP, NIGHT_BOT)
    d.rectangle([0, 238, 480, 270], fill=(60, 56, 72))
    d.rectangle([300, 30, 380, 238], fill=(70, 66, 92))
    return im


def lab_gramophone():
    im = Image.new("RGB", (480, 270))
    d = ImageDraw.Draw(im)
    sky(d, 480, 270, (40, 30, 24), (80, 56, 40))
    d.rectangle([0, 200, 480, 270], fill=(90, 62, 40))
    d.polygon([(150, 200), (330, 200), (300, 110), (180, 110)], fill=(180, 140, 70))
    return im


def sheet(frames, colour, fn):
    """8 direction rows by `frames` columns of 64 px cells: a rounded body with a face dot, feet on row 60."""
    im = Image.new("RGBA", (64 * frames, 64 * 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for r in range(8):
        for f in range(frames):
            x, y = f * 64, r * 64
            bob = (f % 2) * 1
            d.rounded_rectangle([x + 22, y + 20 - bob, x + 42, y + 58], 6, fill=colour + (255,), outline=(14, 25, 56, 255))
            d.ellipse([x + 24, y + 6 - bob, x + 40, y + 22 - bob], fill=colour + (255,), outline=(14, 25, 56, 255))
            d.ellipse([x + 29, y + 12 - bob, x + 31, y + 14 - bob], fill=(14, 25, 56, 255))
    im.save(OUT / fn)


def portraits(colour, name):
    """5 expression rows by 3 frames, 96 px cells."""
    im = Image.new("RGBA", (96 * 3, 96 * 5), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for r in range(5):
        for f in range(3):
            x, y = f * 96, r * 96
            d.rounded_rectangle([x + 20, y + 14, x + 76, y + 96], 10, fill=colour + (255,), outline=(14, 25, 56, 255))
            d.ellipse([x + 36, y + 34, x + 40, y + 38], fill=(14, 25, 56, 255))
            d.ellipse([x + 56, y + 34, x + 60, y + 38], fill=(14, 25, 56, 255))
            d.line([(x + 40, y + 56 + (f % 2) * 2), (x + 56, y + 56)], fill=(14, 25, 56, 255), width=2)
    im.save(OUT / f"{name}_portraits.png")


if __name__ == "__main__":
    courtyard(False).save(OUT / "manor_glitch.png")
    courtyard(True).save(OUT / "manor_restored.png")
    lab_tower().save(OUT / "lab_tower.png")
    lab_gramophone().save(OUT / "lab_gramophone.png")
    for who, col in SUSPECTS.items():
        for anim, n in (("idle", 8), ("talk", 8), ("nervous", 8), ("shocked", 6)):
            sheet(n, col, f"{who}_{anim}.png")
        portraits(col, who)
    print("wrote", len(list(OUT.glob("*.png"))), "files to", OUT)
