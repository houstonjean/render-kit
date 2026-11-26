"""Build the input kit for the first render job (reference only).

usage: kit.py <elevation.pdf> <out_dir>
All boxes are fractions of the (rotated) PDF page: x0,y0,x1,y1.
"""
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFilter

pdf, out = sys.argv[1], Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
page = pymupdf.open(pdf)[0]
R = page.rect


def clip(box, px_wide):
    x0, y0, x1, y1 = box
    c = pymupdf.Rect(R.x0 + x0 * R.width, R.y0 + y0 * R.height, R.x0 + x1 * R.width, R.y0 + y1 * R.height)
    z = px_wide / c.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z), clip=c, alpha=False)
    return Image.frombytes("RGB", (pix.width, pix.height), pix.samples)


def white_out(img, box, masks):
    """Paint page-fraction rectangles white (annotation text only, never building lines)."""
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    for mx0, my0, mx1, my1 in masks:
        px = [
            (mx0 - x0) / (x1 - x0) * img.width,
            (my0 - y0) / (y1 - y0) * img.height,
            (mx1 - x0) / (x1 - x0) * img.width,
            (my1 - y0) / (y1 - y0) * img.height,
        ]
        d.rectangle(px, fill="white")
    return img


def erase_ink(img, box, ink_box, thresh=150):
    """Inside a page-fraction box, turn only dark pixels white: removes black label text
    while leaving the light-gray stone hatch underneath untouched."""
    x0, y0, x1, y1 = box
    mx0, my0, mx1, my1 = ink_box
    px = [
        max(0, int((mx0 - x0) / (x1 - x0) * img.width)),
        max(0, int((my0 - y0) / (y1 - y0) * img.height)),
        min(img.width, int((mx1 - x0) / (x1 - x0) * img.width)),
        min(img.height, int((my1 - y0) / (y1 - y0) * img.height)),
    ]
    if px[2] <= px[0] or px[3] <= px[1]:
        return img
    region = img.crop(px)
    mask = region.convert("L").point(lambda v: 255 if v < thresh else 0)
    mask = mask.filter(ImageFilter.MaxFilter(9))  # also take the anti-aliased halo around each letter
    region.paste((255, 255, 255), mask=mask)
    img.paste(region, px[:2])
    return img


HOUSE = (0.047, 0.270, 0.921, 0.785)
MASKS = [
    (0.047, 0.270, 0.168, 0.683),  # dimension strings + plate-height note, left of the chimney
    (0.797, 0.270, 0.921, 0.680),  # datum line in the sky, right of the end parapet
]
LABEL = (0.4640, 0.519, 0.494, 0.537)  # "LEADED GLASS" label text (ink only)
ENTRY = (0.398, 0.370, 0.509, 0.780)
BAY = (0.300, 0.455, 0.402, 0.780)

jobs = [
    ("A_elevation_house.png", HOUSE, 6000, MASKS),
    ("B_elevation_entry_detail.png", ENTRY, 1800, MASKS),
    ("C_elevation_bay_detail.png", BAY, 1800, []),
]
for name, box, w, masks in jobs:
    im = white_out(clip(box, w), box, masks)
    if name[0] in "AB":
        im = erase_ink(im, box, LABEL)
    im.save(out / name)
    print(name, im.size)
