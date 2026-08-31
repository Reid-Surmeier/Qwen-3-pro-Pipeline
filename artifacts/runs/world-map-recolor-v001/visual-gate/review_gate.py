"""Visual-review gate prototype (wayfinder #144, map #140).

Every assertion samples in the SOURCE-RASTER frame (checklist item 16).
Usage: python3 review_gate.py CANDIDATE.png SOURCE.gif OUT_DIR
Emits: verdict.json, REVIEW.md, side-by-side full map + gridded 4x region crops.
Exit 0 = mechanical PASS (blind visual review still required); exit 1 = NO-SHIP.
"""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

cand_p, src_p, out_p = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
out_p.mkdir(parents=True, exist_ok=True)
S = np.asarray(Image.open(src_p).convert("RGB")).astype(np.int16)
C = np.asarray(Image.open(cand_p).convert("RGB")).astype(np.int16)
assert S.shape == C.shape, f"size mismatch {S.shape} vs {C.shape}"
H, W = S.shape[:2]

def eq(img, *c):
    return (img == np.array(c, np.int16)).all(axis=2)

FILLS = [(0x04,0x9A,0xFC),(0xFC,0x32,0x34),(0x04,0xCE,0x34),(0xFC,0xCE,0x34),(0x04,0xFE,0x54),
         (0x04,0xBE,0x3C),(0x6C,0xB6,0xFC),(0xFC,0x82,0x84),(0xF7,0x7C,0x7C),(0x94,0xF7,0xC6),
         (0xCC,0xFE,0x9C),(0x34,0xCE,0xFC),(0xCC,0xC6,0xFC),(0x9C,0xFE,0xCC)]
BG = [(0xFC,0xFE,0xFC),(0xCC,0xCE,0xFC),(0xB8,0xB8,0xB8)]
INK = [(0x04,0x02,0x04),(0x04,0x02,0x34),(0x34,0x32,0x34),(0x64,0x66,0x64),(0x6C,0x6D,0x6C),
       (0x5C,0x5E,0x5C),(0x5C,0x5A,0x5C),(0x64,0x66,0x9C),(0xFC,0x66,0x04),(0xFC,0xFE,0x04),(0xFC,0xFE,0x34)]

def mask_of(img, cols):
    m = np.zeros((H, W), bool)
    for c in cols:
        m |= eq(img, *c)
    return m

def land_of(img):
    return ~mask_of(img, BG) & ~mask_of(img, INK)

src_fill = land_of(S)          # symmetric definition: identity compares equal masks
src_bgm = mask_of(S, BG[:2])
src_inkm = mask_of(S, INK)
cand_land = land_of(C)
src_dark = eq(S, 4, 2, 4) | eq(S, 4, 2, 0x34)
cand_dark = eq(C, 4, 2, 4) | eq(C, 4, 2, 0x34)
# annotation zone in the source (plates/tags carry shadows & yellows; date line orange; greenwich slate)
annot = ndimage.binary_dilation(
    mask_of(S, [(0x34,0x32,0x34),(0xFC,0xFE,0x04),(0xFC,0xFE,0x34),(0xFC,0x66,0x04),(0x64,0x66,0x9C)]), iterations=6)
annot[H - 70:, :360] = True
annot[:80, :200] = True
annot[:80, W - 200:] = True

REGIONS = {
    "north-america": (60, 60, 340, 300), "south-america": (230, 300, 430, 480),
    "europe": (430, 60, 590, 210), "great-britain": (440, 105, 530, 180),
    "africa": (430, 210, 640, 430), "middle-east": (570, 215, 670, 310),
    "asia": (590, 60, 880, 300), "se-asia": (700, 240, 900, 340), "australia": (750, 330, 950, 440),
}
checks = []

def add(cid_, name, passed, detail):
    checks.append({"id": cid_, "name": name, "pass": bool(passed), "detail": detail})

# 2. registration: per-region land centroid shift <= 2 px
worst = {}
for rn, (x0, y0, x1, y1) in REGIONS.items():
    sm = src_fill[y0:y1, x0:x1]
    cm = cand_land[y0:y1, x0:x1]
    if sm.sum() < 200 or cm.sum() < 200:
        continue
    sy, sx = np.argwhere(sm).mean(axis=0)
    cy, cx = np.argwhere(cm).mean(axis=0)
    worst[rn] = round(float(np.hypot(cy - sy, cx - sx)), 2)
add("A2", "registration: region land-centroid shift <=2px",
    all(v <= 2.0 for v in worst.values()), worst)

# 3. coverage: source fill pixels carrying land paint in candidate
cov = float(cand_land[src_fill].mean()) if src_fill.any() else 1.0
add("A3", "coverage: >=98% of source land fills painted (source frame)", cov >= 0.98, {"coverage": round(cov, 4)})

# 4. sea stays sea: deep-ocean source pixels must not be land-painted
deep_sea = src_bgm & ~ndimage.binary_dilation(src_fill | src_inkm, iterations=3)
sea_bad = float(cand_land[deep_sea].mean()) if deep_sea.any() else 0.0
add("A4", "sea stays sea: <=0.5% of deep ocean land-painted", sea_bad <= 0.005,
    {"violation_frac": round(sea_bad, 5), "violation_px": int((cand_land & deep_sea).sum())})

# 6. component fusion/fragmentation per region (land comps >=30px, majority inside box)
comp_bad = {}
for rn, (x0, y0, x1, y1) in REGIONS.items():
    def comps(m):
        lab, n = ndimage.label(m[y0:y1, x0:x1])
        sz = ndimage.sum(m[y0:y1, x0:x1], lab, range(1, n + 1))
        return int((sz >= 30).sum())
    cs, cc = comps(src_fill), comps(cand_land)
    if abs(cs - cc) > 1:
        comp_bad[rn] = {"source": cs, "candidate": cc}
add("A6", "component count per region within +-1 (no fusion/fragmentation)", not comp_bad, comp_bad)

# 7. palette census: distinct flat colours above 200 px
def census(img, m):
    fl = img[m]
    if not fl.size:
        return 0
    _, cts_ = np.unique(fl.reshape(-1, 3), axis=0, return_counts=True)
    return int((cts_ >= 200).sum())
big_c, big_s = census(C, cand_land), census(S, src_fill)
add("A7", "palette census: candidate flat colours <= source's + 2 (final rule awaits pinned palette, #145)",
    big_c <= big_s + 2, {"candidate": big_c, "source": big_s})

# 9. anchoring: source dark marks adjacent to source land must have candidate land within 2 px
anchors = src_dark & ndimage.binary_dilation(src_fill, iterations=1) & ~annot
cand_land_d = ndimage.binary_dilation(cand_land, iterations=2)
anch_ok = float(cand_land_d[anchors].mean()) if anchors.any() else 1.0
add("A9", "anchoring: >=97% of coastal ink marks still touch land", anch_ok >= 0.97,
    {"anchored_frac": round(anch_ok, 4), "orphaned_px": int((anchors & ~cand_land_d).sum())})

# 10. label integrity: per word cluster outside annotation zones, >=90% glyph survival
lab_b, n_b = ndimage.label(src_dark & ~annot, structure=np.ones((3, 3)))
sz_b = ndimage.sum(src_dark & ~annot, lab_b, range(1, n_b + 1))
objs_b = ndimage.find_objects(lab_b)
letters = np.zeros((H, W), bool)
for j in range(1, n_b + 1):
    sl = objs_b[j - 1]
    if sz_b[j - 1] <= 60 and (sl[0].stop - sl[0].start) <= 14 and (sl[1].stop - sl[1].start) <= 14:
        letters[sl] |= lab_b[sl] == j
wlab, wn = ndimage.label(ndimage.binary_dilation(letters, structure=np.ones((3, 9))))
bad_words = []
same = (C == S).all(axis=2)
for wi, wsl in enumerate(ndimage.find_objects(wlab), start=1):
    wm = (wlab[wsl] == wi) & letters[wsl]
    tot = int(wm.sum())
    if tot < 12:
        continue
    surv = float(same[wsl][wm].mean())
    if surv < 0.9:
        bad_words.append({"x": int(wsl[1].start), "y": int(wsl[0].start), "survival": round(surv, 2), "px": tot})
add("A10", "label integrity: every word keeps >=90% of its glyph pixels", not bad_words,
    {"damaged_words": len(bad_words), "worst": sorted(bad_words, key=lambda d: d["survival"])[:8]})

# 13. interior strokes: candidate dark ink with no source ink within 3 px, surrounded by land
src_ink_d = ndimage.binary_dilation(src_dark | src_inkm, iterations=3)
ghost = cand_dark & ~src_ink_d & ndimage.binary_erosion(cand_land | cand_dark, iterations=1)
add("A13", "no interior strokes absent from the source (<=30px tolerance)", int(ghost.sum()) <= 30,
    {"ghost_stroke_px": int(ghost.sum())})

# 15. deliverable identity (published-render hash must be supplied at deploy time)
add("A15", "deliverable identity: candidate hash recorded; publish step must match it", True,
    {"sha256": hashlib.sha256(cand_p.read_bytes()).hexdigest()})
add("A16", "frame declaration: all assertions above sample the SOURCE-raster frame", True,
    {"frame": "source raster 1001x485"})

# ---- review packet -----------------------------------------------------------
def gridded(img, box, z):
    x0, y0, x1, y1 = box
    t = Image.fromarray(img[y0:y1, x0:x1].astype(np.uint8)).resize(((x1 - x0) * z, (y1 - y0) * z), Image.NEAREST)
    a = np.asarray(t).copy()
    for gx in range(x0 - x0 % 10 + 10, x1, 10):
        a[:, (gx - x0) * z] = (255, 0, 255)
    for gy in range(y0 - y0 % 10 + 10, y1, 10):
        a[(gy - y0) * z, :] = (255, 0, 255)
    return Image.fromarray(a)

for rn, box in REGIONS.items():
    z = 4 if (box[2] - box[0]) > 120 else 6
    a, b = gridded(S, box, z), gridded(C, box, z)
    sheet = Image.new("RGB", (a.width * 2 + 20, a.height), (40, 40, 40))
    sheet.paste(a, (0, 0)); sheet.paste(b, (a.width + 20, 0))
    sheet.save(out_p / f"pair-{rn}.png")
full = Image.new("RGB", (W, H * 2 + 10), (40, 40, 40))
full.paste(Image.fromarray(S.astype(np.uint8)), (0, 0))
full.paste(Image.fromarray(C.astype(np.uint8)), (0, H + 10))
full.save(out_p / "pair-full.png")

verdict = {"candidate": cand_p.name, "source": src_p.name,
           "mechanical_pass": all(c["pass"] for c in checks), "checks": checks,
           "note": "mechanical PASS is necessary, never sufficient: an independent visual reviewer "
                   "must read the pair-*.png packet and return ship/no-ship before any deploy."}
(out_p / "verdict.json").write_text(json.dumps(verdict, indent=2) + "\n")
lines = [f"# Visual gate review — {cand_p.name}", "",
         f"Mechanical verdict: {'PASS' if verdict['mechanical_pass'] else 'NO-SHIP'}", "",
         "| # | assertion | verdict | detail |", "|---|---|---|---|"]
for c in checks:
    lines.append(f"| {c['id']} | {c['name']} | {'PASS' if c['pass'] else 'FAIL'} | `{json.dumps(c['detail'])[:220]}` |")
lines += ["", "Reviewer: read every `pair-*.png` (source left, candidate right, magenta 10px grid),",
          "then record ship/no-ship. A deploy without that recorded verdict is invalid."]
(out_p / "REVIEW.md").write_text("\n".join(lines) + "\n")
print(("PASS" if verdict["mechanical_pass"] else "NO-SHIP"),
      "-", sum(c["pass"] for c in checks), "of", len(checks), "assertions;",
      "packet:", str(out_p))
sys.exit(0 if verdict["mechanical_pass"] else 1)
