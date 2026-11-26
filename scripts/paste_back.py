"""Paste an edited crop back into the full render, changing ONLY the centre-wall zone.

usage: paste_back.py <full_image> <generated_crop> <out.png> <x0> <y0> <x1> <y1> <wall_x0> <wall_x1> <top_y> <bottom_y>
  box (x0..y1)      where the crop was cut from the full image, in full-image pixels
  wall_x0, wall_x1  vertical seams (the two bay edges), full-image pixels
  top_y, bottom_y   horizontal seams (sky above the gable, driveway below the steps), full-image pixels

Steps: resize the generated crop to the box size, register it to the original crop using only the
zones that should be unchanged (bays, roof edges, driveway), match its tone to the original there,
then blend through a feathered mask. Everything outside the mask is byte-for-byte the original.
"""
import sys

import cv2
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
full_p, gen_p, out_p = sys.argv[1:4]
x0, y0, x1, y1, wx0, wx1, ty, by = (int(v) for v in sys.argv[4:12])
EXTRA = [tuple(int(v) for v in a.split(",")) for a in sys.argv[12:]]  # extra replace zones "x0,y0,x1,y1", full-image pixels
FEATHER = 10

full = Image.open(full_p).convert("RGB")
orig = np.asarray(full.crop((x0, y0, x1, y1)), dtype=np.float32)
h, w = orig.shape[:2]
gen_im = Image.open(gen_p).convert("RGB")
print("generated", gen_im.size, "aspect", round(gen_im.width / gen_im.height, 4), "| box", (w, h), "aspect", round(w / h, 4))
gen = np.asarray(gen_im.resize((w, h), Image.LANCZOS), dtype=np.float32)

# zones that must be unchanged: used for registration and tone matching
keep = np.zeros((h, w), np.uint8)
keep[:, : max(0, wx0 - x0 - 8)] = 255
keep[:, min(w, wx1 - x0 + 8):] = 255
keep[: max(0, ty - y0 - 8), :] = 255
keep[min(h, by - y0 + 8):, :] = 255
for ex0, ey0, ex1, ey1 in EXTRA:
    keep[max(0, ey0 - y0 - 8): ey1 - y0 + 8, max(0, ex0 - x0 - 8): ex1 - x0 + 8] = 0

g0 = cv2.cvtColor(orig.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
g1 = cv2.cvtColor(gen.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255
warp = np.eye(2, 3, dtype=np.float32)
try:
    cc, warp = cv2.findTransformECC(cv2.GaussianBlur(g0, (0, 0), 2), cv2.GaussianBlur(g1, (0, 0), 2), warp, cv2.MOTION_AFFINE,
                                    (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 300, 1e-7), keep, 5)
    print(f"registration: correlation {cc:.3f}, shift ({warp[0,2]:+.1f}, {warp[1,2]:+.1f}) px, scale x {warp[0,0]:.4f} y {warp[1,1]:.4f}")
except cv2.error as e:
    print("registration failed, using the crop unshifted:", e)
gen = cv2.warpAffine(gen, warp, (w, h), flags=cv2.INTER_LANCZOS4 | cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REFLECT)

# tone match in the keep zones (per-channel gain and offset in Lab)
lab_o = cv2.cvtColor(orig / 255, cv2.COLOR_RGB2LAB)
lab_g = cv2.cvtColor(np.clip(gen, 0, 255) / 255, cv2.COLOR_RGB2LAB)
m = keep > 0
for c in range(3):
    so, sg = lab_o[..., c][m].std(), lab_g[..., c][m].std()
    gain = np.clip(so / (sg + 1e-6), 0.9, 1.1)
    lab_g[..., c] = (lab_g[..., c] - lab_g[..., c][m].mean()) * gain + lab_o[..., c][m].mean()
gen = np.clip(cv2.cvtColor(lab_g, cv2.COLOR_LAB2RGB) * 255, 0, 255)
res = np.abs(cv2.cvtColor(gen.astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) - g0 * 255)[m]
print(f"after registration, mean difference in the unchanged zones: {res.mean():.1f} grey levels (0 = identical, <8 good)")

mask = np.zeros((h, w), np.float32)
mask[ty - y0: by - y0, wx0 - x0: wx1 - x0] = 1
for ex0, ey0, ex1, ey1 in EXTRA:
    mask[ey0 - y0: ey1 - y0, ex0 - x0: ex1 - x0] = 1
mask = cv2.GaussianBlur(mask, (0, 0), FEATHER)[..., None]
blend = gen * mask + orig * (1 - mask)

result = np.asarray(full).copy()
result[y0:y1, x0:x1] = np.clip(blend + 0.5, 0, 255).astype(np.uint8)
Image.fromarray(result).save(out_p)
changed = np.any(result != np.asarray(full), axis=2)
ys, xs = np.where(changed)
print("changed pixels lie inside x", xs.min(), "-", xs.max(), " y", ys.min(), "-", ys.max(), "| saved", out_p)
