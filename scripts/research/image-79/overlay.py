#!/usr/bin/env python3
"""Draw the control inventory over the reference so it can be eyeballed."""
import json
import os
import sys
from PIL import Image, ImageDraw

REF = "/home/reidsurmeier/Qwen-3-pro-Pipeline/.claude/worktrees/agent-aa0361cb0549b2773/artifacts/references/ro-desktop-b"
SCRATCH = "/tmp/claude-1000/-home-reidsurmeier-Qwen-3-pro-Pipeline/ad61c962-aeb7-4583-bb02-12f0c19476ff/scratchpad"
inv = json.load(open(os.path.join(REF, "control-inventory.json")))
wr = json.load(open(os.path.join(REF, "window-rects.json")))
im = Image.open(os.path.join(REF, "reference-native.png")).convert("RGB")

COL = {
    "button": (255, 0, 0), "checkbox": (0, 200, 0), "radio": (0, 255, 128),
    "tab": (255, 140, 0), "stepper": (0, 128, 255), "slider": (255, 0, 255),
    "scrollbar": (0, 255, 255), "dropdown": (255, 255, 0),
    "grid cell": (140, 140, 255), "list row": (255, 200, 0), "title drag": (120, 120, 120),
    "minimize": (0, 0, 255), "close": (200, 0, 0), "text field": (0, 180, 180),
    "meter": (180, 0, 255),
}

full = im.copy()
d = ImageDraw.Draw(full)
for c in inv["controls"]:
    x, y, w, h = c["rect"]
    d.rectangle([x, y, x + w - 1, y + h - 1], outline=COL.get(c["type"], (0, 0, 0)))
full.save(os.path.join(SCRATCH, "work/controls-all.png"))

# per-window zooms at 2x for the ones worth a close look
want = sys.argv[1:] or ["options", "skill-tree", "party", "storage"]
for w in wr["windows"]:
    if w["key"] not in want:
        continue
    x, y, ww, hh = w["rect"]
    crop = im.crop((x, y, x + ww, y + hh)).resize((ww * 2, hh * 2), Image.NEAREST)
    dd = ImageDraw.Draw(crop)
    for c in inv["controls"]:
        if c["window"] != w["key"]:
            continue
        cx, cy, cw, ch = c["rect"]
        cx, cy = (cx - x) * 2, (cy - y) * 2
        dd.rectangle([cx, cy, cx + cw * 2 - 1, cy + ch * 2 - 1],
                     outline=COL.get(c["type"], (0, 0, 0)), width=2)
    p = os.path.join(SCRATCH, f"work/ctl-{w['key']}.png")
    crop.save(p)
    print(p, crop.size)
