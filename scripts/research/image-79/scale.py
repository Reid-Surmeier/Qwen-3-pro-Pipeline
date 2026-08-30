#!/usr/bin/env python3
"""Pixel-period analysis: is the raster an integer upscale of a smaller native image?

Three independent tests:
  1. Edge-phase concentration  - for candidate scale k, what fraction of total
     horizontal/vertical edge energy falls on columns/rows x = r (mod k)?
     A clean k-times nearest/box upscale puts ~100% on one phase.
  2. Flat-run histogram        - run lengths of identical adjacent pixels.
     A k-times upscale makes every run length a multiple of k.
  3. Autocorrelation of the edge-energy signal at lag k.
"""
import sys
import numpy as np
from PIL import Image

path = sys.argv[1]
im = Image.open(path).convert("RGB")
a = np.asarray(im).astype(np.int32)
H, W, _ = a.shape
print(f"image {path}")
print(f"size {W}x{H}")

# ---------- 1. edge energy per column / row ----------
dx = np.abs(np.diff(a, axis=1)).sum(axis=(0, 2))   # length W-1, dx[i] = edge between x=i and x=i+1
dy = np.abs(np.diff(a, axis=0)).sum(axis=(1, 2))   # length H-1

print(f"\nedge energy: horizontal total {dx.sum():,}  vertical total {dy.sum():,}")
print(f"columns with zero horizontal edge: {(dx == 0).sum()} / {len(dx)}")
print(f"rows    with zero vertical   edge: {(dy == 0).sum()} / {len(dy)}")

print("\n--- test 1: edge-phase concentration (best phase per scale) ---")
print(f"{'k':>3} {'horiz %':>9} {'vert %':>9}  {'expected for a true k-upscale':>30}")
for k in range(1, 13):
    hb = max(dx[r::k].sum() for r in range(k)) / dx.sum() * 100
    vb = max(dy[r::k].sum() for r in range(k)) / dy.sum() * 100
    note = "100%" if k > 1 else "trivially 100%"
    print(f"{k:>3} {hb:>8.2f}% {vb:>8.2f}%  {note:>30}")

# ---------- 2. flat-run lengths ----------
print("\n--- test 2: horizontal flat-run lengths (identical adjacent pixels) ---")
same = (np.diff(a, axis=1).sum(axis=2) == 0) & (np.abs(np.diff(a, axis=1)).sum(axis=2) == 0)
runs = []
for y in range(0, H, 7):            # sample every 7th row, plenty of data
    row = same[y]
    n = 1
    for v in row:
        if v:
            n += 1
        else:
            runs.append(n)
            n = 1
    runs.append(n)
runs = np.array(runs)
print(f"runs sampled: {len(runs):,}  mean {runs.mean():.2f}  median {np.median(runs):.0f}")
hist = np.bincount(np.clip(runs, 0, 16))
for L in range(1, 13):
    print(f"  run length {L:>2}: {hist[L]:>7,}  ({hist[L]/len(runs)*100:5.2f}%)")
for k in (2, 3, 4):
    frac = (runs % k == 0).mean() * 100
    print(f"  runs divisible by {k}: {frac:.2f}%   (a true {k}x upscale => ~100%)")

# ---------- 3. autocorrelation of edge energy ----------
print("\n--- test 3: autocorrelation of horizontal edge-energy signal ---")
s = dx.astype(float)
s = s - s.mean()
den = (s * s).sum()
for lag in range(1, 13):
    r = (s[:-lag] * s[lag:]).sum() / den
    print(f"  lag {lag:>2}: {r:+.4f}")

# ---------- 4. direct downscale round-trip test ----------
print("\n--- test 4: point-sample downscale then re-upscale, error vs original ---")
for k in (2, 3, 4):
    if W % k or H % k:
        print(f"  k={k}: {W}x{H} not divisible by {k} -> impossible as a clean {k}x upscale")
        continue
    for phase in range(k):
        small = a[phase::k, phase::k][: H // k, : W // k]
        back = np.repeat(np.repeat(small, k, axis=0), k, axis=1)[:H, :W]
        err = np.abs(a - back)
        print(f"  k={k} phase={phase}: mean abs err {err.mean():7.3f}  max {err.max():>3}  "
              f"exact pixels {(err.max(axis=2) == 0).mean()*100:5.2f}%")
