"""Make magnified before/after crops for vision review.

Usage: python3 review_crops.py SOURCE.png CANDIDATE.png OUT_PREFIX

Both images are resampled to the candidate's size for aligned comparison.
Crops are taken at the same relative positions and magnified 3x (nearest
neighbour) so pixel-scale defects rise above the reviewer's threshold.
"""

import sys
from PIL import Image

src = Image.open(sys.argv[1]).convert("RGB")
cand = Image.open(sys.argv[2]).convert("RGB")
out = sys.argv[3]
W, H = cand.size
src = src.resize((W, H), Image.NEAREST)

# relative boxes (x0, y0, x1, y1) over the 2:1 canvas
BOXES = {
    "nw-alaska-canada": (0.00, 0.00, 0.30, 0.35),
    "europe": (0.44, 0.15, 0.72, 0.42),
    "south-america": (0.28, 0.45, 0.50, 0.98),
    "africa-middle-east": (0.46, 0.38, 0.72, 0.85),
    "east-asia-australia": (0.72, 0.15, 0.98, 0.95),
    "pacific-bottom-left": (0.00, 0.55, 0.30, 1.00),
}
for name, (x0, y0, x1, y1) in BOXES.items():
    box = (int(x0 * W), int(y0 * H), int(x1 * W), int(y1 * H))
    a = src.crop(box)
    b = cand.crop(box)
    scale = 3 if max(a.size) * 3 <= 2400 else 2
    a = a.resize((a.width * scale, a.height * scale), Image.NEAREST)
    b = b.resize((b.width * scale, b.height * scale), Image.NEAREST)
    sheet = Image.new("RGB", (a.width + b.width + 12, max(a.height, b.height)), (40, 40, 40))
    sheet.paste(a, (0, 0))
    sheet.paste(b, (a.width + 12, 0))
    sheet.save(f"{out}-{name}.png")
    print(name, box, "x%d" % scale, sheet.size)
