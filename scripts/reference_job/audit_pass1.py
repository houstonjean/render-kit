"""Audit pass-1 outputs against the base render.

usage: audit_pass1.py <base> <sheet_out.png> <cand1> <cand2> ...
Reports: pixel size, global shift vs base, stone colour (field vs cut), and how well
the parts that must not change (roof, sky, glass, street, structure) were preserved.
"""
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

Image.MAX_IMAGE_PIXELS = None


def lab(rgb):
    c = rgb / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def box(a, b):
    H, W = a.shape[:2]
    x0, y0, x1, y1 = b
    return a[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]


def shift(g0, g1):
    """Phase correlation: (dx, dy) that g1 is displaced relative to g0, in pixels of the given arrays."""
    F = np.fft.fft2(g0 - g0.mean()) * np.conj(np.fft.fft2(g1 - g1.mean()))
    r = np.fft.ifft2(F / (np.abs(F) + 1e-9)).real
    y, x = np.unravel_index(np.argmax(r), r.shape)
    H, W = r.shape
    return (x if x <= W // 2 else x - W), (y if y <= H // 2 else y - H), r.max()


def ncc(a, b):
    a = a - a.mean()
    b = b - b.mean()
    return float((a * b).sum() / (np.sqrt((a * a).sum() * (b * b).sum()) + 1e-9))


FIELD = {"wing L": (0.1925, 0.355, 0.215, 0.46), "center": (0.435, 0.355, 0.45, 0.46), "wing R": (0.645, 0.50, 0.665, 0.56)}
CUT = {"bay L": (0.34, 0.32, 0.40, 0.35), "bay R": (0.55, 0.32, 0.61, 0.35)}
KEEP_COLOR = {  # must be visually unchanged: mean colour difference (delta E) vs base
    "sky": (0.30, 0.02, 0.60, 0.10),
    "roof": (0.31, 0.245, 0.43, 0.285),
    "street": (0.20, 0.80, 0.80, 0.86),
    "lawn": (0.20, 0.93, 0.80, 0.99),
    "cut bay L": (0.34, 0.32, 0.40, 0.35),
}
KEEP_SHAPE = {  # must keep the same structure in the same place: correlation vs base (1.00 = identical)
    "bay L glass": (0.33, 0.35, 0.41, 0.62),
    "bay R glass": (0.54, 0.35, 0.62, 0.62),
    "entry": (0.44, 0.40, 0.51, 0.62),
    "arch win L": (0.20, 0.49, 0.285, 0.62),
    "arch win R": (0.66, 0.49, 0.745, 0.62),
    "wing L upper": (0.21, 0.34, 0.28, 0.45),
    "center gable": (0.44, 0.19, 0.51, 0.33),
    "chimney L": (0.17, 0.07, 0.24, 0.27),
    "gate R": (0.84, 0.55, 0.98, 0.66),
    "whole image": (0.0, 0.0, 1.0, 1.0),
}

base_path, sheet_out, cands = sys.argv[1], sys.argv[2], sys.argv[3:]
base = Image.open(base_path).convert("RGB")
BW, BH = base.size
b_rgb = np.asarray(base, dtype=float)
b_lab = lab(b_rgb)
b_gray = np.asarray(base.convert("L").filter(ImageFilter.GaussianBlur(2)), dtype=float)
small = (1024, 576)
b_small = np.asarray(base.convert("L").resize(small, Image.LANCZOS), dtype=float)


def stone(L, tag):
    f = np.concatenate([box(L, b).reshape(-1, 3) for b in FIELD.values()])
    c = np.concatenate([box(L, b).reshape(-1, 3) for b in CUT.values()])
    fm, cm = f.mean(0), c.mean(0)
    dE = float(np.linalg.norm(fm - cm))
    print(f"  {tag:10s} field L*={fm[0]:5.1f} a*={fm[1]:4.1f} b*={fm[2]:5.1f} | cut L*={cm[0]:5.1f} a*={cm[1]:4.1f} b*={cm[2]:5.1f}"
          f" | L* gap={cm[0]-fm[0]:5.1f}  colour gap dE={dE:5.1f}  stone-to-stone L* spread={f[:,0].std():4.1f}")


print("BASE", base_path.replace("\\", "/").split("/")[-1], base.size)
stone(b_lab, "base")
thumbs = [("BASE (gray render)", base)]
for p in cands:
    im = Image.open(p).convert("RGB")
    name = p.replace("\\", "/").split("/")[-1]
    print(f"\n{name}  pixels={im.size}  aspect={im.width/im.height:.4f} (base {BW/BH:.4f})")
    r = im.resize((BW, BH), Image.LANCZOS)
    o_rgb = np.asarray(r, dtype=float)
    o_lab = lab(o_rgb)
    o_gray = np.asarray(r.convert("L").filter(ImageFilter.GaussianBlur(2)), dtype=float)
    dx, dy, peak = shift(b_small, np.asarray(r.convert("L").resize(small, Image.LANCZOS), dtype=float))
    print(f"  global shift vs base: dx={dx*BW/small[0]:+.1f}px dy={dy*BH/small[1]:+.1f}px (at base size; peak {peak:.2f})")
    stone(o_lab, "result")
    print("  must-not-change colour (dE vs base, <5 good): " + ", ".join(
        f"{k}={float(np.linalg.norm(box(o_lab, b).reshape(-1,3).mean(0) - box(b_lab, b).reshape(-1,3).mean(0))):.1f}" for k, b in KEEP_COLOR.items()))
    print("  structure match (1.00 = identical): " + ", ".join(f"{k}={ncc(box(b_gray, b), box(o_gray, b)):.2f}" for k, b in KEEP_SHAPE.items()))
    thumbs.append((name, im))

# contact sheet 2x2
tw = 1280
th = int(tw * BH / BW)
cap = 44
font = ImageFont.truetype("arial.ttf", 28)
cols = 2
rows = (len(thumbs) + 1) // 2
sheet = Image.new("RGB", (cols * tw, rows * (th + cap)), "white")
d = ImageDraw.Draw(sheet)
for i, (name, im) in enumerate(thumbs):
    x, y = (i % cols) * tw, (i // cols) * (th + cap)
    d.text((x + 8, y + 6), name, fill="black", font=font)
    sheet.paste(im.resize((tw, th), Image.LANCZOS), (x, y + cap))
sheet.save(sheet_out)
print("\nsheet", sheet.size, sheet_out)
