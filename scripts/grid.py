"""Crop a pixel box and overlay a labelled grid in SOURCE pixel coordinates, for reading landmarks.
usage: grid.py <image> <out.png> <x0> <y0> <x1> <y1> <step_px> [scale]
"""
import sys

from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
src, out = sys.argv[1], sys.argv[2]
x0, y0, x1, y1, step = (int(v) for v in sys.argv[3:8])
scale = float(sys.argv[8]) if len(sys.argv) > 8 else 1.0
im = Image.open(src).convert("RGB").crop((x0, y0, x1, y1))
if scale != 1.0:
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
d = ImageDraw.Draw(im)
font = ImageFont.truetype("arial.ttf", 16)
for x in range((x0 // step + 1) * step, x1, step):
    px = (x - x0) * scale
    d.line([(px, 0), (px, im.height)], fill=(255, 0, 0), width=1)
    d.text((px + 2, 2), str(x), fill=(255, 0, 0), font=font)
for y in range((y0 // step + 1) * step, y1, step):
    py = (y - y0) * scale
    d.line([(0, py), (im.width, py)], fill=(0, 90, 255), width=1)
    d.text((2, py + 2), str(y), fill=(0, 90, 255), font=font)
im.save(out)
print(im.size, out)
