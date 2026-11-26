"""Side-by-side zoom cells. usage: zoom.py <out.png> <cell_w> <h|v> <label=path> [...] -- <x0,y0,x1,y1> [...]
Layout h: one row; for each box, one cell per image. Layout v: boxes side by side, images stacked.
"""
import sys

from PIL import Image, ImageDraw, ImageFont

Image.MAX_IMAGE_PIXELS = None
out, cell_w, layout = sys.argv[1], int(sys.argv[2]), sys.argv[3]
rest = sys.argv[4:]
split = rest.index("--")
imgs = [(s.split("=", 1)[0], Image.open(s.split("=", 1)[1]).convert("RGB")) for s in rest[:split]]
boxes = [tuple(float(v) for v in s.split(",")) for s in rest[split + 1:]]
font = ImageFont.truetype("arial.ttf", 26)
CAP = 36
cells = []
for b in boxes:
    for label, im in imgs:
        W, H = im.size
        c = im.crop((int(b[0] * W), int(b[1] * H), int(b[2] * W), int(b[3] * H)))
        # use the nominal 16:9 frame so every image yields the same cell shape
        ch = int(cell_w * ((b[3] - b[1]) * 9) / ((b[2] - b[0]) * 16))
        cells.append((label, c.resize((cell_w, ch), Image.LANCZOS)))
if layout == "h":
    sheet = Image.new("RGB", (sum(c.width for _, c in cells), max(c.height for _, c in cells) + CAP), "white")
    d = ImageDraw.Draw(sheet)
    x = 0
    for label, c in cells:
        d.text((x + 6, 4), label, fill="black", font=font)
        sheet.paste(c, (x, CAP))
        x += c.width
else:
    n = len(imgs)
    col_w = cell_w
    heights = [cells[i][1].height + CAP for i in range(n)]
    sheet = Image.new("RGB", (col_w * len(boxes), sum(heights)), "white")
    d = ImageDraw.Draw(sheet)
    for bi in range(len(boxes)):
        y = 0
        for ii in range(n):
            label, c = cells[bi * n + ii]
            d.text((bi * col_w + 6, y + 4), label, fill="black", font=font)
            sheet.paste(c, (bi * col_w, y + CAP))
            y += c.height + CAP
sheet.save(out)
print(sheet.size, out)
