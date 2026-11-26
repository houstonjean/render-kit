"""Cut a fixed-aspect crop from the winning image and record where it came from,
so the edited crop can be pasted back in exactly the same place.

usage: cut_crop.py <source> <out.png> <out.json> <center_x_frac> <top_y_frac> <width_px> <aspect_w> <aspect_h>
"""
import json
import sys

from PIL import Image

Image.MAX_IMAGE_PIXELS = None
src, out_png, out_json = sys.argv[1:4]
cx, top = float(sys.argv[4]), float(sys.argv[5])
w, aw, ah = int(sys.argv[6]), int(sys.argv[7]), int(sys.argv[8])
im = Image.open(src).convert("RGB")
W, H = im.size
w -= w % aw  # keep the aspect exact
h = w * ah // aw
x0 = int(round(cx * W - w / 2))
y0 = int(round(top * H))
box = (x0, y0, x0 + w, y0 + h)
assert box[0] >= 0 and box[1] >= 0 and box[2] <= W and box[3] <= H, box
im.crop(box).save(out_png)
json.dump({"source": src, "source_size": [W, H], "box": box, "aspect": [aw, ah]}, open(out_json, "w"), indent=2)
print("source", (W, H), "box", box, "crop", (w, h))
