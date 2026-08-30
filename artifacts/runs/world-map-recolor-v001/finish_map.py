"""Deterministic finishing for the recolored map.

Usage: python3 finish_map.py CANDIDATE.png SOURCE_16x9_FULL.png OUT_PREFIX

1. Restore the source's dark-grey ocean zone-boundary lines onto the candidate
   as pale grey (#d0d0d0), only where the candidate shows background (white
   ocean or lavender grid) — nothing is painted over land, outlines or frame.
2. Crop the white padding bands by locating the black frame's top and bottom.
3. Save OUT_PREFIX-final.png and a 3x review sheet of the restored lines.
"""

import sys
import numpy as np
from PIL import Image

cand = Image.open(sys.argv[1]).convert("RGB")
src = Image.open(sys.argv[2]).convert("RGB")
out = sys.argv[3]
W, H = cand.size
sw, sh = src.size

# --- 1. grey-line mask from the source --------------------------------------
s = np.asarray(src).astype(np.int16)
# the zone lines are one exact colour (#8b8c8a); anti-aliased text and badge
# edges are greyish but not this neutral, so a tight window rejects them
target = np.array([0x8B, 0x8C, 0x8A], dtype=np.int16)
grey = (np.abs(s - target) <= 10).all(axis=2)
# keep only line-like components: long and thin. Glyph and box ghosts are
# small or boxy; zone lines are hundreds of px long and ~1 px wide.
from scipy import ndimage  # noqa: E402
labels, n = ndimage.label(grey, structure=np.ones((3, 3)))
keep = np.zeros(n + 1, dtype=bool)
for i, sl in enumerate(ndimage.find_objects(labels), start=1):
    hgt = sl[0].stop - sl[0].start
    wid = sl[1].stop - sl[1].start
    count = int((labels[sl] == i).sum())
    thin = count <= 0.06 * hgt * wid + 3 * max(hgt, wid)
    keep[i] = max(hgt, wid) >= 60 and thin
grey = keep[labels]
print("grey components kept:", int(keep.sum()), "of", n)
mask = Image.fromarray((grey * 255).astype(np.uint8))
mask = mask.resize((W, H), Image.BOX)                            # box average
m = np.asarray(mask) > 90                                        # thin, single-px lines

c = np.asarray(cand).copy()
r, g, b = c[..., 0].astype(int), c[..., 1].astype(int), c[..., 2].astype(int)
background = ((r > 225) & (g > 225) & (b > 225)) | ((r > 195) & (g > 195) & (b > r) & (b > g))
paint = m & background
LINE = (0xB8, 0xB8, 0xB8)   # lighter than the source's #8b8c8a, still readable on white
c[paint] = LINE
restored = Image.fromarray(c)
print("grey-line pixels restored:", int(paint.sum()), "of mask", int(m.sum()))

# --- 2. crop to the black frame ---------------------------------------------
dark_rows = ((c.astype(int).sum(axis=2) < 120).sum(axis=1) > W * 0.5)
rows = np.where(dark_rows)[0]
top, bottom = int(rows.min()), int(rows.max())
final = restored.crop((0, max(0, top - 1), W, min(H, bottom + 2)))
final.save(f"{out}-final.png")
print("frame rows", top, bottom, "-> final size", final.size)

# --- 3. review sheet ---------------------------------------------------------
box = (int(W * 0.30), int(H * 0.45), int(W * 0.62), int(H * 0.95))
a = cand.crop(box); bimg = restored.crop(box)
a = a.resize((a.width * 3, a.height * 3), Image.NEAREST); bimg = bimg.resize((bimg.width * 3, bimg.height * 3), Image.NEAREST)
sheet = Image.new("RGB", (a.width * 2 + 12, a.height), (40, 40, 40)); sheet.paste(a, (0, 0)); sheet.paste(bimg, (a.width + 12, 0))
sheet.save(f"{out}-lines-review.png"); print("review sheet", sheet.size)
