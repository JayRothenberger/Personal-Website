"""Draw the site favicon from personal/static/me.jpg: the head cropped from the photo, reduced to a
few flat colours (an MS Paint look), two light blue lenses with an anime-style glint slash, and
flat green mountains against a blue sky behind. Each size is made natively from the photo.
Writes personal/static/favicon.ico (16, 32, 48) and apple-touch-icon.png (180).
Run: python3 tools/favicon.py [n_colours]   (needs Pillow and numpy)
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter

STATIC = Path(__file__).resolve().parent.parent / "personal" / "static"
NCOL = int(sys.argv[1]) if len(sys.argv) > 1 else 7
BRIGHT, SAT = 1.35, 1.6

# geometry in the 730 px square cropped from the photo at CROP (measured by eye on a grid)
CROP = (520, 520, 1250, 1250)
U = 730.0
HEAD = (130, 40, 598, 680)
SHOULDERS = [(0, 730), (0, 705), (140, 655), (250, 625), (480, 625), (590, 655), (730, 690), (730, 730)]
LENS_CENTRES = [(293, 390), (475, 390)]   # over the eyes
LENS_D = 115                              # round lenses, both the same diameter
RIDGE = [(0, 300), (70, 215), (130, 260), (215, 150), (300, 235), (365, 175), (450, 250), (540, 140),
         (620, 230), (680, 185), (730, 240), (730, 730), (0, 730)]

# Windows 7 Paint palette
SKY = (0, 162, 232)
GREEN = (34, 177, 76)
LENS = (110, 185, 255)   # blue tint, strong enough to stay blue over warm skin
LENS_ALPHA = 0.7         # how much of the tint covers the face behind the lens
GLINT = (255, 255, 255)


def draw(n: int) -> Image.Image:
    k = n / U
    sc = lambda pts: [(round(x * k), round(y * k)) for x, y in pts]  # noqa: E731
    box = lambda b: [round(v * k) for v in b]  # noqa: E731
    photo = Image.open(STATIC / "me.jpg").convert("RGB").crop(CROP)

    mask = Image.new("L", photo.size, 0)
    md = ImageDraw.Draw(mask)
    md.ellipse(HEAD, fill=255)
    md.polygon(SHOULDERS, fill=255)
    person = np.asarray(mask.resize((n, n), Image.Resampling.LANCZOS)) > 127

    # flatten detail before shrinking: a median turns skin and hair into smooth fields
    work = photo.resize((256, 256), Image.Resampling.LANCZOS).filter(ImageFilter.MedianFilter(7))
    # cartoon colours: lift the shadowed face and saturate before the fills are picked
    work = ImageEnhance.Contrast(ImageEnhance.Color(ImageEnhance.Brightness(work).enhance(BRIGHT)).enhance(SAT)).enhance(1.15)
    px = np.asarray(work.resize((n, n), Image.Resampling.LANCZOS)).copy()

    # a few flat colours, picked from the person only (background pixels would skew the palette)
    px[~person] = px[person].mean(0).astype(np.uint8)
    q = Image.fromarray(px).quantize(colors=NCOL, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    flat = np.asarray(q.convert("RGB")).copy()

    # flat Paint background: blue sky, green mountains
    bg = Image.new("RGB", (n, n), SKY)
    ImageDraw.Draw(bg).polygon(sc(RIDGE), fill=GREEN)
    flat[~person] = np.asarray(bg)[~person]

    # two tinted lenses, alpha-blended over the face, each with a solid white diagonal glint
    # like anime glasses. One pixel size for both, so rounding can't make them differ.
    w = h = max(2, round(LENS_D * k))
    lens = Image.new("L", (n, n), 0)
    glints = []
    for cx, cy in LENS_CENTRES:
        x0, y0 = round(cx * k - w / 2), round(cy * k - h / 2)
        ImageDraw.Draw(lens).ellipse((x0, y0, x0 + w - 1, y0 + h - 1), fill=255)
        # lower left to upper right, kept inside the lens
        gx, gy = w * 0.22, h * 0.22
        mx, my = x0 + (w - 1) / 2, y0 + (h - 1) / 2
        glints.append((round(mx - gx), round(my + gy), round(mx + gx), round(my - gy)))
    inside = np.asarray(lens) > 0
    flat[inside] = (flat[inside] * (1 - LENS_ALPHA) + np.array(LENS) * LENS_ALPHA).round().astype(np.uint8)
    im = Image.fromarray(flat)
    d = ImageDraw.Draw(im)
    for g in glints:
        d.line(g, fill=GLINT, width=max(1, round(12 * k)))
    return im


if __name__ == "__main__":
    sizes = {s: draw(s) for s in (16, 32, 48)}
    sizes[48].save(STATIC / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)], append_images=[sizes[16], sizes[32]])
    # home-screen icon: the 60 px version scaled 3x with hard pixels, to keep the Paint look
    draw(60).resize((180, 180), Image.Resampling.NEAREST).save(STATIC / "apple-touch-icon.png", optimize=True)
