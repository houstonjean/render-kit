"""Cut the entry crop from the render AND rasterize the elevation PDF with exactly the same framing,
so the photo crop and the drawing register line for line.

usage: align_entry.py <render> <elevation.pdf> <out_dir> <x0> <y0> <x1> <y1>
Registration (measured from gridded views of pass3_1 and the elevation):
  render pixel (2648, 1997)  <->  PDF point (1366.07, 1337.77)   [entry centreline at ground]
  scale 2.0385 render px per PDF pt
"""
import json
import sys
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFilter

Image.MAX_IMAGE_PIXELS = None
render, pdf, out = sys.argv[1], sys.argv[2], Path(sys.argv[3])
x0, y0, x1, y1 = (int(v) for v in sys.argv[4:8])

RX, RY, PX, PY, S = 2648.0, 1997.0, 1366.07, 1337.77, 2.0385
WALL = (2326, 2970)  # render x of the wall between the two bowed bays; drawing is blanked outside it
LABEL_PT = (1403.1, 896.8, 1493.9, 927.9)  # "LEADED GLASS" label text
UP = 3  # drawing is rasterized at 3x the crop's pixel size


def to_pt(x, y):
    return PX + (x - RX) / S, PY + (y - RY) / S


photo = Image.open(render).convert("RGB").crop((x0, y0, x1, y1))
photo.save(out / "crop_entry_v2.png")

page = pymupdf.open(pdf)[0]
(ax, ay), (bx, by) = to_pt(x0, y0), to_pt(x1, y1)
clip = pymupdf.Rect(ax, ay, bx, by)
z = (x1 - x0) * UP / clip.width
pix = page.get_pixmap(matrix=pymupdf.Matrix(z, z), clip=clip, alpha=False)
draw = Image.frombytes("RGB", (pix.width, pix.height), pix.samples).resize(((x1 - x0) * UP, (y1 - y0) * UP), Image.LANCZOS)

# erase the black label text only (keeps the light stone hatch under it)
lx0, ly0, lx1, ly1 = [int(round(v)) for v in ((LABEL_PT[0] - ax) * z, (LABEL_PT[1] - ay) * z, (LABEL_PT[2] - ax) * z, (LABEL_PT[3] - ay) * z)]
region = draw.crop((lx0, ly0, lx1, ly1))
mask = region.convert("L").point(lambda v: 255 if v < 150 else 0).filter(ImageFilter.MaxFilter(9))
region.paste((255, 255, 255), mask=mask)
draw.paste(region, (lx0, ly0))

# blank the bay zones: the drawing shows the bays in flat projection, the render has them bowed
d = ImageDraw.Draw(draw)
d.rectangle([0, 0, (WALL[0] - x0) * UP, draw.height], fill="white")
d.rectangle([(WALL[1] - x0) * UP, 0, draw.width, draw.height], fill="white")
# blank everything below the ground line (the sheet title sits there)
GROUND_Y = 2012  # render y just under the landing slab
d.rectangle([0, (GROUND_Y - y0) * UP, draw.width, draw.height], fill="white")

# blank the roof and sky above the eave, except inside a margin around the curved gable:
# the drawing's ridge sits higher than the render's, and the roof must stay as rendered.
EAVE_Y = 540 + y0  # render y just under the eave line
gable = [(200, 540), (200, 455), (240, 445), (285, 420), (310, 370), (325, 325), (360, 318), (365, 290),
         (410, 232), (445, 218), (455, 170), (535, 170), (545, 218), (580, 232), (625, 290), (630, 318),
         (665, 325), (680, 370), (705, 420), (750, 445), (790, 455), (790, 540)]  # crop pixels
keep = Image.new("L", draw.size, 0)
k = ImageDraw.Draw(keep)
k.rectangle([0, (EAVE_Y - y0) * UP, draw.width, draw.height], fill=255)
k.polygon([(x * UP, y * UP) for x, y in gable], fill=255)
white = Image.new("RGB", draw.size, "white")
draw = Image.composite(draw, white, keep)
draw.save(out / "I_elevation_entry_aligned.png")

# check image: drawing ink in red over the photo
small = draw.resize(photo.size, Image.LANCZOS).convert("L")
ink = small.point(lambda v: 255 if v < 120 else 0)
chk = photo.copy()
chk.paste((255, 0, 0), mask=ink)
chk.save(out / "_check_alignment.png")

json.dump({"source": render, "box": [x0, y0, x1, y1], "wall_x": WALL, "registration": [RX, RY, PX, PY, S]},
          open(out / "crop_entry_v2.json", "w"), indent=2)
print("photo crop", photo.size, "aspect", photo.width / photo.height, "| drawing", draw.size, "| clip pt", [round(v, 1) for v in clip])
