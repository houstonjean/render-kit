"""Build the two comparison sheets for sending.
usage: sheets.py <orig_render> <final> <aligned_drawing> <out_dir>
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
orig_p, final_p, draw_p, out = sys.argv[1], sys.argv[2], sys.argv[3], Path(sys.argv[4])
F = ImageFont.truetype("arialbd.ttf", 44)
BG, INK = (250, 248, 244), (40, 36, 30)


def label(sheet, x, y, text):
    ImageDraw.Draw(sheet).text((x, y), text, fill=INK, font=F)


orig, final = Image.open(orig_p).convert("RGB"), Image.open(final_p).convert("RGB")

# 1. before / after, full view, stacked
W = 2600
a = orig.resize((W, int(W * orig.height / orig.width)), Image.LANCZOS)
b = final.resize((W, int(W * final.height / final.width)), Image.LANCZOS)
CAP, PAD = 80, 30
s = Image.new("RGB", (W + 2 * PAD, a.height + b.height + 2 * CAP + 2 * PAD), BG)
label(s, PAD, PAD + 12, "BEFORE  -  render as received")
s.paste(a, (PAD, PAD + CAP))
label(s, PAD, PAD + CAP + a.height + 12, "AFTER  -  front elevation")
s.paste(b, (PAD, PAD + 2 * CAP + a.height))
s.save(out / "before_after.jpg", quality=90)
print("before/after", s.size)

# 2. door: drawing | before | after | after with the drawing laid over it in red
H = 1900
box_final = (2153, 420, 3143, 2180)
fx0, fy0, fx1, fy1 = 0.387, 0.137, 0.563, 0.710  # same part of the house in the original render
cw = int(H * 990 / 1760)
d = Image.open(draw_p).convert("RGB").resize((cw, H), Image.LANCZOS)
before = orig.crop((int(fx0 * orig.width), int(fy0 * orig.height), int(fx1 * orig.width), int(fy1 * orig.height))).resize((cw, H), Image.LANCZOS)
after = final.crop(box_final).resize((cw, H), Image.LANCZOS)
ov = np.asarray(after).copy()
ov[np.asarray(d.convert("L")) < 110] = (230, 0, 0)
cells = [("ELEVATION", d), ("BEFORE", before), ("AFTER", after), ("AFTER + elevation in red", Image.fromarray(ov))]
s = Image.new("RGB", (len(cells) * cw + (len(cells) + 1) * PAD, H + CAP + 2 * PAD), BG)
x = PAD
for text, im in cells:
    label(s, x, PAD + 12, text)
    s.paste(im, (x, PAD + CAP))
    x += cw + PAD
s.save(out / "front_door_check.jpg", quality=90)
print("door check", s.size)
