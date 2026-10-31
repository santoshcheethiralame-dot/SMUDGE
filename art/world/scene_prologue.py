"""Prologue backdrop at Smudge's scale: we stand on page 137. The page is the
floor; the next page curls up behind like a wall. Printed text is a texture
in page space, pre-stretched so it reads upright through the 20 deg camera.

build(erased=True) renders the same page after the Rubber Baron has rubbed
the density formula out.
"""
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from envrender import Obj, World, Light, gradient_sky
from src import sdf
from src.render import PITCH

(PAGE, LINE, MARGIN, PRINT, PRINT_RED, SMEAR, DESK, COVER) = range(1, 9)

W, H = 480, 270
CENTRE = (0.0, 92.0)
FLOOR_FRONT, FLOOR_BACK = 150.0, -100.0       # z range of the flat page
R = 120.0                                      # radius of the curl
S_FLAT = FLOOR_FRONT - FLOOR_BACK              # 250
S_MAX = S_FLAT + R * np.pi / 2
X0, X1 = -320, 320
FONT = "C:/Windows/Fonts/"
FLOOR_STRETCH = 1.0 / np.sin(PITCH)            # ~2.92: floor text pre-stretch
ASTERISK = None                                # filled in by _texture: (x, z) of the '*'


def _font(name, size):
    return ImageFont.truetype(FONT + name, size)


def _stamp(canvas, text, font, x, s_bottom, stretch, fill):
    """Draw text so that, on screen, it reads upright with its baseline at page-distance s_bottom."""
    bbox = font.getbbox(text)
    w, h = bbox[2] - bbox[0] + 4, bbox[3] - bbox[1] + 6
    tmp = Image.new("L", (w, h), 0)
    ImageDraw.Draw(tmp).text((2 - bbox[0], 3 - bbox[1]), text, font=font, fill=255)
    tmp = tmp.resize((w, max(1, int(h * stretch))), Image.BILINEAR)
    rows = canvas.shape[0]
    top_row = int(rows - (s_bottom + tmp.height))
    left = int(x - X0)
    a = np.array(tmp) > 110
    sub = canvas[top_row:top_row + a.shape[0], left:left + a.shape[1]]
    sub[a[:sub.shape[0], :sub.shape[1]]] = fill
    return left + X0, s_bottom, w, tmp.height


def _texture(erased):
    global ASTERISK
    rows = int(S_MAX) + 2
    tex = np.zeros((rows, X1 - X0), np.int16)

    def srow(s):
        return int(rows - s)

    # ruled lines, thicker on the flat floor where the camera squashes them
    for s in np.arange(14, S_MAX, 26):
        th = 3 if s < S_FLAT else 2
        tex[srow(s + th):srow(s), :] = LINE
    # double margin rule
    for x in (-236, -230):
        tex[:, x - X0:x - X0 + 2] = MARGIN

    # page number, front-left
    _stamp(tex, "137", _font("georgia.ttf", 18), -290, 8, FLOOR_STRETCH, PRINT)

    if not erased:
        # the law itself, printed on the floor at Smudge's feet
        x, s, w, h = _stamp(tex, "\u03c1 = m / V", _font("georgiai.ttf", 34), -70, 108, FLOOR_STRETCH, PRINT)
        ax, _, aw, ah = _stamp(tex, "*", _font("georgiab.ttf", 44), x + w + 6, 108 + 40, FLOOR_STRETCH, PRINT_RED)
        ASTERISK = (ax + aw / 2, FLOOR_FRONT - (108 + 40 + ah * 0.5))
    else:
        # rubbed-out patch with crumbs of graphite
        rng = np.random.default_rng(7)
        yy, xx = np.mgrid[0:rows, 0:X1 - X0]
        cx, cs = 30 - X0, srow(118 + 60)
        blob = ((xx - cx) / 120.0) ** 2 + ((yy - cs) / 62.0) ** 2 < 1.0
        noise = rng.random(blob.shape) < 0.55
        tex[blob & noise & (tex == 0)] = SMEAR
        ASTERISK = (110.0, FLOOR_FRONT - 170.0)

    # the curled page reads like a wall: chapter heading and a beaker diagram
    _stamp(tex, "CHAPTER 9", _font("georgiab.ttf", 15), -60, S_FLAT + 128, 1.12, PRINT_RED)
    _stamp(tex, "Density", _font("georgiab.ttf", 46), -78, S_FLAT + 64, 1.12, PRINT)
    _stamp(tex, "Why do some things float?", _font("georgiai.ttf", 15), -78, S_FLAT + 40, 1.12, PRINT)
    _stamp(tex, "density = mass ÷ volume", _font("georgia.ttf", 19), -78, S_FLAT + 12, 1.12, PRINT)
    # beaker diagram (left of the heading)
    img = Image.new("L", (110, 130), 0)
    d = ImageDraw.Draw(img)
    d.line([(20, 10), (20, 118), (90, 118), (90, 10)], fill=255, width=4)
    d.line([(14, 10), (26, 10)], fill=255, width=3)
    d.line([(84, 10), (96, 10)], fill=255, width=3)
    for yy in (40, 62, 84, 106):
        d.line([(20, yy), (34, yy)], fill=255, width=2)
    d.arc([(20, 52), (55, 66)], 180, 360, fill=255, width=3)
    d.arc([(55, 52), (90, 66)], 0, 180, fill=255, width=3)
    d.ellipse([(44, 80), (66, 102)], outline=255, width=3)
    a = np.array(img.resize((110, int(130 * 1.12)))) > 100
    top = srow(S_FLAT + 22 + a.shape[0])
    left = -250 - X0
    tex[top:top + a.shape[0], left:left + a.shape[1]][a] = PRINT
    return tex, rows


def build(erased=False):
    tex, rows = _texture(erased)

    def page_coords(p):
        x = p[:, 0]
        z, y = p[:, 2], p[:, 1]
        s = np.where(z >= FLOOR_BACK, FLOOR_FRONT - z,
                     S_FLAT + R * np.arctan2(FLOOR_BACK - z, R - y))
        col = np.clip((x - X0).astype(int), 0, tex.shape[1] - 1)
        row = np.clip((rows - s).astype(int), 0, rows - 1)
        return tex[row, col]

    def paper(p, n):
        # soft gutter shadow where the flat page bends up into the curl
        z, y = p[:, 2], p[:, 1]
        s = np.where(z >= FLOOR_BACK, FLOOR_FRONT - z, S_FLAT + R * np.arctan2(FLOOR_BACK - z, R - y))
        return -np.exp(-((s - S_FLAT - 10) ** 2) / (2 * 22.0 ** 2)) * 1.4

    materials = {
        PAGE: dict(ramp=["#6A5F4B", "#8F8268", "#B3A584", "#CFC2A0", "#E3D8B8", "#F2E9CF", "#FCF6E6"],
                   submap=page_coords, pattern=paper, pattern_gain=0.28, warm_tint=0.4, dither=0.5),
        LINE: dict(ramp=["#3F5E88", "#5577A6", "#6E92C2", "#88AAD8", "#A1C0E8", "#B8D3F3"], warm_tint=0.25, dither=0.15),
        MARGIN: dict(ramp=["#7E3434", "#9E4646", "#BC5C5C", "#D47676", "#E59494", "#F1B1B1"], warm_tint=0.25),
        PRINT: dict(ramp=["#07090F", "#0E121D", "#161C2C", "#20283C", "#2B354E"], dither=0.1),
        PRINT_RED: dict(ramp=["#3A0907", "#5E100C", "#861912", "#A92318", "#C93224"], dither=0.1),
        SMEAR: dict(ramp=["#5C574D", "#76705F", "#918A77", "#ABA38E", "#C2BAA3", "#D3CBB4"], dither=0.3),
        DESK: dict(ramp=["#140B05", "#24140A", "#3A2112", "#523019", "#6B4022"]),
        COVER: dict(ramp=["#1E0504", "#3A0C09", "#5A140F", "#7D1E16"]),
    }

    def page(p):
        floor = np.where(p[:, 2] >= FLOOR_BACK, p[:, 1], 1e9)
        # quarter cylinder curling up behind the floor
        dy, dz = p[:, 1] - R, p[:, 2] - FLOOR_BACK
        ring = np.abs(np.sqrt(dy * dy + dz * dz) - R)
        ring = np.where((p[:, 2] < FLOOR_BACK) & (p[:, 1] < R + 1), ring, 1e9)
        top = np.where(p[:, 2] < FLOOR_BACK - R + 2, np.sqrt(np.maximum(p[:, 1] - R, 0) ** 2 + (p[:, 2] - (FLOOR_BACK - R)) ** 2), 1e9)
        d = np.minimum.reduce([floor, ring - 1.0, top])
        d = np.maximum(d, np.abs(p[:, 0]) - 330)
        return d, PAGE
    objs = [Obj(page, (-331, -2, FLOOR_BACK - R - 4), (331, R + 4, FLOOR_FRONT + 4), "page")]

    sky = gradient_sky(W, H, "#05060F", "#141A33", glow=(70, 0, 260, "#5A3E22"))
    lights = [Light((-260, 330, 190), "#FFC46B", 1.6, 900),
              Light((240, 120, 120), "#6F8FD8", 0.35, 600, shadow=False)]
    return dict(world=World(objs), materials=materials, width=W, height=H, centre=CENTRE,
                lights=lights, key=0.22, ambient=0.08, top=R + 6, ss=2, steps=160, sky=sky)
