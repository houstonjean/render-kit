"""Overlay the aligned drawing's ink (red) on generated crops, to judge line-for-line match.
usage: overlay.py <aligned_drawing.png> <out.png> <y0_frac> <y1_frac> <x0_frac> <x1_frac> <label=gen.jpg> [...]
Also prints, per candidate, how much of the drawing's ink lands on an edge in the render (edge-hit rate).
"""
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
draw_p, out = sys.argv[1], sys.argv[2]
fy0, fy1, fx0, fx1 = (float(v) for v in sys.argv[3:7])
W, H = 1485, 2640  # 1.5x the crop size
d_im = Image.open(draw_p).convert("L").resize((W, H), Image.LANCZOS)
ink = np.asarray(d_im) < 110
font = ImageFont.truetype("arial.ttf", 30)
cells = []
for spec in sys.argv[7:]:
    label, path = spec.split("=", 1)
    g = Image.open(path).convert("RGB").resize((W, H), Image.LANCZOS)
    a = np.asarray(g).copy()
    gray = cv2.cvtColor(a, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (0, 0), 1.5), 20, 60)
    near = cv2.dilate(edges, np.ones((13, 13), np.uint8)) > 0  # within 6 px (4 px at crop scale)
    zone = np.zeros_like(ink)
    zone[int(0.50 * H):int(0.90 * H), int(0.18 * W):int(0.82 * W)] = True  # tablet, surround, door
    hit = (ink & near & zone).sum() / max(1, (ink & zone).sum())
    print(f"{label}: {hit * 100:.0f}% of the drawing's door-zone lines fall on an edge in the render")
    a[ink] = (255, 0, 0)
    c = Image.fromarray(a).crop((int(fx0 * W), int(fy0 * H), int(fx1 * W), int(fy1 * H)))
    cells.append((label, c))
sheet = Image.new("RGB", (sum(c.width for _, c in cells) + 8 * (len(cells) - 1), cells[0][1].height + 40), "white")
dd = ImageDraw.Draw(sheet)
x = 0
for label, c in cells:
    dd.text((x + 6, 4), label, fill="black", font=font)
    sheet.paste(c, (x, 40))
    x += c.width + 8
sheet.save(out)
print(sheet.size, out)
