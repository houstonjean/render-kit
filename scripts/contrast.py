"""Mean CIE L*a*b* of named patches. usage: contrast.py <image> name:x0,y0,x1,y1 ... (fractions)"""
import sys

import numpy as np
from PIL import Image


def lab(rgb):
    c = rgb / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750], [0.0193339, 0.1191920, 0.9503041]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    return np.stack([116 * f[..., 1] - 16, 500 * (f[..., 0] - f[..., 1]), 200 * (f[..., 1] - f[..., 2])], -1)


im = np.asarray(Image.open(sys.argv[1]).convert("RGB"), dtype=float)
H, W = im.shape[:2]
print(sys.argv[1].replace("\\", "/").split("/")[-1], (W, H))
for spec in sys.argv[2:]:
    name, box = spec.split(":")
    x0, y0, x1, y1 = (float(v) for v in box.split(","))
    p = im[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)].reshape(-1, 3)
    L = lab(p)
    r, g, b = p.mean(0)
    print(f"  {name:12s} L*={L[:,0].mean():5.1f} a*={L[:,1].mean():5.1f} b*={L[:,2].mean():5.1f}  rgb=({r:.0f},{g:.0f},{b:.0f}) #{int(r):02x}{int(g):02x}{int(b):02x}  n={len(p)}")
