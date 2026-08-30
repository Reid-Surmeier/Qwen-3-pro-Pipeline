#!/usr/bin/env python3
"""Per-window 2x crops with a native-pixel grid, for reading control rects."""
import json
import os
from PIL import Image, ImageDraw

SCRATCH = "/tmp/claude-1000/-home-reidsurmeier-Qwen-3-pro-Pipeline/ad61c962-aeb7-4583-bb02-12f0c19476ff/scratchpad"
OUT = os.path.join(SCRATCH, "work/win")
os.makedirs(OUT, exist_ok=True)
REF = "/home/reidsurmeier/Qwen-3-pro-Pipeline/.claude/worktrees/agent-aa0361cb0549b2773/artifacts/references/ro-desktop-b"
wr = json.load(open(os.path.join(REF, "window-rects.json")))
im = Image.open(os.path.join(REF, "reference-native.png")).convert("RGB")

S = 2
GRID = 20
for i, w in enumerate(wr["windows"], start=1):
    x, y, ww, hh = w["rect"]
    c = im.crop((x, y, x + ww, y + hh)).resize((ww * S, hh * S), Image.NEAREST)
    d = ImageDraw.Draw(c, "RGBA")
    for gx in range(0, ww + 1, GRID):
        col = (255, 0, 0, 200) if gx % 100 == 0 else (0, 200, 255, 90)
        d.line([(gx * S, 0), (gx * S, hh * S)], fill=col, width=1)
        if gx % 100 == 0:
            d.rectangle([gx * S, 0, gx * S + 26, 11], fill=(0, 0, 0, 220))
            d.text((gx * S + 2, 1), str(gx), fill=(255, 255, 0, 255))
    for gy in range(0, hh + 1, GRID):
        col = (255, 0, 0, 200) if gy % 100 == 0 else (0, 200, 255, 90)
        d.line([(0, gy * S), (ww * S, gy * S)], fill=col, width=1)
        if gy % 100 == 0:
            d.rectangle([0, gy * S, 26, gy * S + 11], fill=(0, 0, 0, 220))
            d.text((2, gy * S + 1), str(gy), fill=(255, 255, 0, 255))
    p = os.path.join(OUT, f"{i:02d}-{w['key']}.png")
    c.save(p)
    print(p, c.size, "window rect", w["rect"])
