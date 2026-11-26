"""Undo the colour cast that builds up over repeated AI edits.

Every pass through the image model tinted the WHOLE picture slightly magenta (sky, roof, street and lawn
all moved together), so the approved cut-stone beige drifted with it. This fits one colour transform from
regions that were never meant to change, comparing the drifted image to the original render, and applies
it to a target image.

usage: color_fix.py <reference_original> <drifted> <target_to_correct> <out.png> [boxes_preview.png]
"""
import sys

import numpy as np
from PIL import Image, ImageDraw

Image.MAX_IMAGE_PIXELS = None
ref_p, drift_p, target_p, out_p = sys.argv[1:5]
preview = sys.argv[5] if len(sys.argv) > 5 else None

# regions that no pass was asked to change, valid in both images (fractions of width/height)
PATCHES = {
    "sky": (0.28, 0.03, 0.42, 0.09),
    "roof left": (0.31, 0.245, 0.43, 0.285),
    "roof right": (0.53, 0.245, 0.63, 0.285),
    "street": (0.20, 0.80, 0.80, 0.86),
    "lawn": (0.20, 0.93, 0.80, 0.99),
    "driveway": (0.40, 0.72, 0.52, 0.76),
    "cut stone bay L": (0.34, 0.32, 0.40, 0.35),
    "cut stone bay R": (0.55, 0.32, 0.61, 0.35),
    "trees left": (0.02, 0.30, 0.12, 0.50),
    "trees right": (0.88, 0.30, 0.98, 0.48),
    "bay glass": (0.345, 0.40, 0.395, 0.47),
}
CHECK = {"FIELD stone wing L": (0.1925, 0.355, 0.215, 0.46)}  # reported only, never used for the fit

M_RGB2XYZ = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
WHITE = np.array([0.95047, 1.0, 1.08883])


def rgb2lab(rgb):
    c = rgb / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = c @ M_RGB2XYZ.T / WHITE
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


def lab2rgb(lab):
    fy = (lab[..., 0] + 16) / 116
    f = np.stack([fy + lab[..., 1] / 500, fy, fy - lab[..., 2] / 200], -1)
    xyz = np.where(f > 0.206893, f ** 3, (f - 16 / 116) / 7.787) * WHITE
    c = xyz @ np.linalg.inv(M_RGB2XYZ).T
    c = np.clip(c, 0, 1)
    c = np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)
    return np.clip(c * 255, 0, 255)


def means(path, boxes):
    im = np.asarray(Image.open(path).convert("RGB"), dtype=np.float64)
    H, W = im.shape[:2]
    return {k: rgb2lab(im[int(b[1] * H):int(b[3] * H), int(b[0] * W):int(b[2] * W)].reshape(-1, 3)).mean(0) for k, b in boxes.items()}


if preview:
    cells = []
    for p in (ref_p, drift_p):
        im = Image.open(p).convert("RGB").resize((1280, 714), Image.LANCZOS)
        d = ImageDraw.Draw(im)
        for b in list(PATCHES.values()) + list(CHECK.values()):
            d.rectangle([b[0] * 1280, b[1] * 714, b[2] * 1280, b[3] * 714], outline=(255, 0, 0), width=2)
        cells.append(im)
    sheet = Image.new("RGB", (2560, 714))
    sheet.paste(cells[0], (0, 0))
    sheet.paste(cells[1], (1280, 0))
    sheet.save(preview)

ref, dr = means(ref_p, PATCHES), means(drift_p, PATCHES)
X = np.array([dr[k] for k in PATCHES])
Y = np.array([ref[k] for k in PATCHES])
# affine Lab -> Lab, ridge-regularized toward "identity + offset" so 11 patches cannot overfit
Xa = np.hstack([X, np.ones((len(X), 1))])
lam = 25.0
I0 = np.vstack([np.eye(3), np.zeros((1, 3))])
reg = np.diag([lam, lam, lam, 0.0])
A = np.linalg.solve(Xa.T @ Xa + reg, Xa.T @ Y + reg @ I0)
fit = Xa @ A
print("transform (rows L,a,b,offset):")
print(np.round(A, 3))
print(f"{'region':20s} {'cast before':>12s} {'after fix':>10s}   (dE vs original render)")
for i, k in enumerate(PATCHES):
    print(f"{k:20s} {np.linalg.norm(X[i] - Y[i]):12.1f} {np.linalg.norm(fit[i] - Y[i]):10.1f}")

tgt = np.asarray(Image.open(target_p).convert("RGB"), dtype=np.float64)
out = np.empty_like(tgt)
for r0 in range(0, tgt.shape[0], 256):  # in strips to keep memory low
    lab = rgb2lab(tgt[r0:r0 + 256])
    out[r0:r0 + 256] = lab2rgb(lab @ A[:3] + A[3])
Image.fromarray((out + 0.5).astype(np.uint8)).save(out_p)

o = means(ref_p, {"cut": PATCHES["cut stone bay L"], "cut2": PATCHES["cut stone bay R"]})
b4 = means(target_p, {**{"cut": PATCHES["cut stone bay L"], "cut2": PATCHES["cut stone bay R"]}, **CHECK})
af = means(out_p, {**{"cut": PATCHES["cut stone bay L"], "cut2": PATCHES["cut stone bay R"]}, **CHECK})
c_o, c_b, c_a = (o["cut"] + o["cut2"]) / 2, (b4["cut"] + b4["cut2"]) / 2, (af["cut"] + af["cut2"]) / 2
f_b, f_a = b4["FIELD stone wing L"], af["FIELD stone wing L"]
fmt = lambda v: f"L*={v[0]:.1f} a*={v[1]:.1f} b*={v[2]:.1f}"
print("cut stone, original render :", fmt(c_o))
print("cut stone, before fix      :", fmt(c_b), f"(dE {np.linalg.norm(c_b - c_o):.1f} from original)")
print("cut stone, after fix       :", fmt(c_a), f"(dE {np.linalg.norm(c_a - c_o):.1f} from original)")
print("field stone, before fix    :", fmt(f_b))
print("field stone, after fix     :", fmt(f_a), f"| field-vs-cut L* gap {c_a[0] - f_a[0]:.1f}, colour gap dE {np.linalg.norm(c_a - f_a):.1f}")
print("saved", out_p)
