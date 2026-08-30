#!/usr/bin/env python3
"""Detect the window rectangles on the RO desktop reference.

The desktop backdrop is a saturated magenta; every window is a light grey
panel. Mask out the magenta, label 4-connected components, keep the large
ones, and report their bounding boxes in native pixels.
"""
import json
import sys
import numpy as np
from PIL import Image
from scipy import ndimage

src = sys.argv[1]
out_json = sys.argv[2]
a = np.asarray(Image.open(src).convert("RGB")).astype(int)
H, W, _ = a.shape
R, G, B = a[..., 0], a[..., 1], a[..., 2]

# magenta backdrop: red and blue high, green much lower
backdrop = (R > 150) & (B > 150) & (G < R - 60) & (G < B - 60)
print(f"backdrop pixels: {backdrop.mean()*100:.1f}%")

fg = ~backdrop
fg = np.pad(fg, 2); fg = ndimage.binary_closing(fg, np.ones((3, 3)))[2:-2, 2:-2]
# opening removed: it eroded the 1px window border
lab, n = ndimage.label(fg)
print(f"components: {n}")

boxes = []
for i, sl in enumerate(ndimage.find_objects(lab), start=1):
    ys, xs = sl
    h, w = ys.stop - ys.start, xs.stop - xs.start
    area = (lab[sl] == i).sum()
    if w < 100 or h < 80 or area < 15000:
        continue
    boxes.append({"x": int(xs.start), "y": int(ys.start), "w": int(w), "h": int(h),
                  "pixels": int(area), "fill": round(area / (w * h), 3)})

boxes.sort(key=lambda b: (b["y"] // 40, b["x"]))
print(f"kept {len(boxes)} boxes")
for b in boxes:
    print(f"  x={b['x']:>4} y={b['y']:>4} w={b['w']:>4} h={b['h']:>4} "
          f"fill={b['fill']} px={b['pixels']:,}")
json.dump(boxes, open(out_json, "w"), indent=1)
