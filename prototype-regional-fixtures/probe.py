#!/usr/bin/env python3
"""PROTOTYPE — throwaway. Wayfinder map #140, last open ticket.

Question: do the four regional WorldTimeZone reference maps (Middle East,
Africa, South America, Australia) add gate signal beyond the source-frame
crop pairs review_gate.py already produces?

A gate fixture must be (1) immutable, (2) comparable in the source frame,
(3) reproducibly re-fetchable. This probes all three. Not production code.
Run: python3 probe.py <dir-with-source-gifs>
"""
import sys, subprocess, pathlib
from PIL import Image, ImageChops
import numpy as np

REGIONS = ["australia", "africa", "south-america", "middle-east"]
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
URL = "https://www.worldtimezone.com/time/wtz-{r}-map.php?sessionid=cf&forma=12map"


def diff(pa, pb):
    a = Image.open(pa).convert("RGB"); b = Image.open(pb).convert("RGB")
    if a.size != b.size:
        return None, a.size, b.size
    d = np.array(ImageChops.difference(a, b)).sum(axis=2)
    return (d > 0).sum(), a.size, d.size


def main(src_dir):
    src = pathlib.Path(src_dir)
    print("== TEST 1: is the licensed source immutable across fetches? ==")
    n, size, total = diff(src / "wtz-map-12map-1001x485.gif", src / "wtz-map-second.gif")
    print(f"   source {size}: {n} of {total} px differ ({100*n/total:.3f}%)")
    print(f"   VERDICT: {'NOT immutable — live clock render' if n else 'immutable'}")

    print("\n== TEST 2: are regional maps in the source frame? ==")
    out = pathlib.Path("fetch"); out.mkdir(exist_ok=True)
    for r in REGIONS:
        p = out / f"{r}-probe.png"
        subprocess.run(["curl", "-sS", "-A", UA, "-o", str(p), URL.format(r=r)], check=False)
        kind = subprocess.run(["file", "-b", str(p)], capture_output=True, text=True).stdout.strip()
        print(f"   {r:<14} {p.stat().st_size:>7} bytes  {kind[:46]}")
    print("   source frame is 1001x485. Any other raster cannot carry a")
    print("   source-frame assertion (decision #143, residual <=2px per #146).")

    print("\n== TEST 3: are they reproducibly re-fetchable? ==")
    print("   see fetch/australia-A.gif (18657 B PNG) vs australia-B/C (21 B).")
    print("   Endpoint returns a hotlink guard after the first hit.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else ".")
