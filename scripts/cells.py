"""Row of crops at a common height, each from its own image and box (true aspect kept).
usage: cells.py <out.png> <height_px> <label=path@x0,y0,x1,y1> [...]
"""
import sys

from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
out, H = sys.argv[1], int(sys.argv[2])
font = ImageFont.truetype("arial.ttf", 28)
cells = []
for spec in sys.argv[3:]:
    label, rest = spec.split("=", 1)
    path, box = rest.rsplit("@", 1)
    x0, y0, x1, y1 = (float(v) for v in box.split(","))
    im = Image.open(path).convert("RGB")
    W_, H_ = im.size
    c = im.crop((int(x0 * W_), int(y0 * H_), int(x1 * W_), int(y1 * H_)))
    cells.append((label, c.resize((max(1, int(c.width * H / c.height)), H), Image.LANCZOS)))
sheet = Image.new("RGB", (sum(c.width for _, c in cells) + 8 * (len(cells) - 1), H + 40), "white")
d = ImageDraw.Draw(sheet)
x = 0
for label, c in cells:
    d.text((x + 6, 4), label, fill="black", font=font)
    sheet.paste(c, (x, 40))
    x += c.width + 8
sheet.save(out)
print(sheet.size, out)
