#!/usr/bin/env python3
"""Gridded side-by-side verification crops for ticket #146.
Left: source raster. Right: source + cid land outlines — CYAN = uncorrected
countries-raw, MAGENTA = countries-registered. 4x magnified, 10-px grid with
native 1001x485 coordinates on both halves.
Usage: python3 make_reg_crops.py ASSEMBLY_DIR REG_DIR OUT_DIR
"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

ASM, REG, OUT = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
OUT.mkdir(parents=True, exist_ok=True)
g = np.asarray(Image.open(ASM / 'wtz-map-12map-1001x485.gif').convert('RGB'))
craw = np.load(ASM / 'countries-raw.npy')
creg = np.load(REG / 'countries-registered.npy')

def outline(m):
    return m & ~ndimage.binary_erosion(m, np.ones((3, 3)))

o_raw = outline(craw >= 0)
o_reg = outline(creg >= 0)

CROPS = {  # name: (x0, x1, y0, y1) in the native frame
    'reg-australia-sw': (750, 900, 340, 445),
    'reg-great-britain': (430, 520, 105, 180),
    'reg-arabia': (565, 690, 195, 310),
}
Z = 4
for name, (x0, x1, y0, y1) in CROPS.items():
    src = g[y0:y1, x0:x1]
    ov = src.copy()
    ov[o_raw[y0:y1, x0:x1]] = (0, 220, 255)     # cyan: uncorrected cid outline
    ov[o_reg[y0:y1, x0:x1]] = (255, 0, 200)     # magenta: registered outline
    h, w = src.shape[:2]
    gap = 24
    panelw = w * Z
    canvas = Image.new('RGB', (panelw * 2 + gap, h * Z + 40), (24, 24, 24))
    for i, arr in enumerate((src, ov)):
        im = Image.fromarray(arr).resize((panelw, h * Z), Image.NEAREST)
        d = ImageDraw.Draw(im)
        for gx in range((x0 // 10 + 1) * 10, x1, 10):
            px = (gx - x0) * Z
            d.line([(px, 0), (px, h * Z)], fill=(255, 0, 255), width=1)
        for gy in range((y0 // 10 + 1) * 10, y1, 10):
            py = (gy - y0) * Z
            d.line([(0, py), (panelw, py)], fill=(255, 0, 255), width=1)
        for gx in range((x0 // 50 + 1) * 50, x1, 50):
            d.text(((gx - x0) * Z + 2, 2), str(gx), fill=(255, 0, 255))
        for gy in range((y0 // 50 + 1) * 50, y1, 50):
            d.text((2, (gy - y0) * Z + 2), str(gy), fill=(255, 0, 255))
        canvas.paste(im, (i * (panelw + gap), 0))
    d = ImageDraw.Draw(canvas)
    d.text((4, h * Z + 8), '%s  x%d-%d y%d-%d  | left: source | right: source + cid outlines '
           '(CYAN=raw grid, MAGENTA=registered)' % (name, x0, x1, y0, y1), fill=(255, 255, 255))
    canvas.save(OUT / ('%s.png' % name))
    print('wrote', OUT / ('%s.png' % name))
