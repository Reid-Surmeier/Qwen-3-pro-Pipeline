#!/usr/bin/env python3
"""Failure-catalogue crop generator (issue #141).
Side-by-side pairs: source (left) vs final-v011-assembly.png (right), 4x nearest-neighbour.
Run from the run directory: python3 failure-catalogue/make_crops.py
"""
from PIL import Image, ImageDraw

SRC = 'assembly/wtz-map-12map-1001x485.gif'
V11 = 'final-v011-assembly.png'
SCALE = 4
REGIONS = {
    'australia-nz':      (750, 290, 1001, 480),
    'us-east-newyork':   (190, 120, 400, 260),
    'caribbean':         (190, 230, 390, 330),
    'western-europe':    (420, 110, 570, 240),
    'africa-west-dakar': (370, 230, 510, 340),
    'middle-east':       (560, 180, 710, 300),
    'se-asia-singapore': (690, 240, 860, 370),
    'south-america-south': (230, 320, 410, 485),
}

def pair(name, box, src, v11):
    a = src.crop(box); b = v11.crop(box)
    a = a.resize((a.width*SCALE, a.height*SCALE), Image.NEAREST)
    b = b.resize((b.width*SCALE, b.height*SCALE), Image.NEAREST)
    gap, head = 16, 28
    out = Image.new('RGB', (a.width + b.width + gap, a.height + head), (30, 30, 30))
    d = ImageDraw.Draw(out)
    d.text((4, 7), f'SOURCE  {name}  box={box}  {SCALE}x', fill=(255, 255, 0))
    d.text((a.width + gap + 4, 7), 'v011', fill=(255, 255, 0))
    out.paste(a, (0, head)); out.paste(b, (a.width + gap, head))
    out.save(f'failure-catalogue/{name}.png')

def full(src, v11):
    gap, head = 8, 28
    out = Image.new('RGB', (src.width, src.height*2 + gap + head), (30, 30, 30))
    d = ImageDraw.Draw(out)
    d.text((4, 7), 'FULL: source (top) vs v011 (bottom), 1x', fill=(255, 255, 0))
    out.paste(src, (0, head)); out.paste(v11, (0, head + src.height + gap))
    out.save('failure-catalogue/full-map-pair.png')

if __name__ == '__main__':
    src = Image.open(SRC).convert('RGB')
    v11 = Image.open(V11).convert('RGB')
    assert src.size == v11.size == (1001, 485), (src.size, v11.size)
    full(src, v11)
    for name, box in REGIONS.items():
        pair(name, box, src, v11)
    print('wrote', len(REGIONS) + 1, 'images')
