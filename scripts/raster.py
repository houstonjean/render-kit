"""Rasterize a PDF page (or load an image) and save named crops.

usage: raster.py <src> <out_dir> <prefix> <long_side_px> [name:x0,y0,x1,y1 ...]
Crop boxes are fractions (0-1) of the full page/image.
"""
import sys
from pathlib import Path

import fitz
from PIL import Image

Image.MAX_IMAGE_PIXELS = None

src, out_dir, prefix, long_side = sys.argv[1], Path(sys.argv[2]), sys.argv[3], int(sys.argv[4])
crops = sys.argv[5:]
out_dir.mkdir(parents=True, exist_ok=True)

if src.lower().endswith(".pdf"):
    doc = fitz.open(src)
    page = doc[0]
    r = page.rect
    print("pages", len(doc), "page pt", r.width, r.height, "rotation", page.rotation)
    for i, info in enumerate(page.get_images(full=True)):
        print("embedded image", i, info[2], "x", info[3], info[8])
    print("vector drawings", len(page.get_drawings()))
    zoom = long_side / max(r.width, r.height)
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
else:
    img = Image.open(src).convert("RGB")

print("raster", img.size)
W, H = img.size
full = out_dir / f"{prefix}_full.png"
img.save(full)
for spec in crops:
    name, box = spec.split(":")
    x0, y0, x1, y1 = (float(v) for v in box.split(","))
    c = img.crop((int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H)))
    # keep previews readable: cap long side at 1800 px
    m = max(c.size)
    if m > 1800:
        s = 1800 / m
        c = c.resize((int(c.width * s), int(c.height * s)), Image.LANCZOS)
    p = out_dir / f"{prefix}_{name}.png"
    c.save(p)
    print("crop", name, c.size, p)
