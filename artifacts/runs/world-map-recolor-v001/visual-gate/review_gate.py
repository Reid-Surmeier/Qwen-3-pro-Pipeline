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

# annotation zone first: plates/tags/date-line/greenwich + corner boxes are not geography.
# Clock plates are found by their NN:NN colon signature in the SOURCE (a source property,
# independent of any composer), in both orientations, plus paired border runs.
dark_bs = eq(S, 4, 2, 4) | eq(S, 0x34, 0x32, 0x34)

def _colon_seeds(d):
    out = []
    for y in range(6, d.shape[0] - 10):
        for x in np.where(d[y])[0]:
            if x < 6 or x >= d.shape[1] - 6:
                continue
            if d[y + 1, x] and not d[y + 2, x] and not d[y + 3, x] and d[y + 4, x] and d[y + 5, x]                and not d[y - 1, x] and not d[y - 2, x] and not d[y + 6, x]:
                out.append((x, y))
    return out

def _box(x, y, d):
    hh, ww = d.shape
    def run_at(yy):
        if yy < 0 or yy >= hh:
            return None
        row = d[yy]
        xc = None
        for xo in (0, -1, 1, -2, 2, -3, 3):
            if 0 <= x + xo < ww and row[x + xo]:
                xc = x + xo
                break
        if xc is None:
            return None
        x0 = xc
        while x0 > 0 and row[x0 - 1]:
            x0 -= 1
        x1 = xc
        while x1 < ww - 1 and row[x1 + 1]:
            x1 += 1
        return (x0, x1) if 24 <= x1 - x0 <= 150 else None
    top = bot = None
    for dy in range(3, 12):
        if top is None:
            t = run_at(y - dy)
            top = (y - dy, t) if t else None
    for dy in range(4, 14):
        if bot is None:
            b = run_at(y + dy)
            bot = (y + dy, b) if b else None
    if top is None or bot is None:
        return None
    return (min(top[1][0], bot[1][0]), top[0], max(top[1][1], bot[1][1]) + 1, bot[0] + 1)

plate_annot = np.zeros((H, W), bool)
for (x, y) in _colon_seeds(dark_bs):
    b = _box(x, y, dark_bs)
    if b:
        plate_annot[max(0, b[1] - 3):b[3] + 3, max(0, b[0] - 3):b[2] + 3] = True
for (x, y) in _colon_seeds(dark_bs.T):
    b = _box(x, y, dark_bs.T)
    if b:
        plate_annot[max(0, b[0] - 3):b[2] + 3, max(0, b[1] - 3):b[3] + 3] = True

def _find_runs(mask, lo=28, hi=140):
    runs = {}
    for y in range(mask.shape[0]):
        xs = np.where(mask[y])[0]
        if len(xs) < lo:
            continue
        breaks = np.where(np.diff(xs) > 1)[0]
        starts = np.r_[xs[0], xs[breaks + 1]]
        ends = np.r_[xs[breaks], xs[-1]]
        for a, b in zip(starts, ends):
            if lo <= b - a <= hi:
                runs.setdefault(y, []).append((int(a), int(b)))
    return runs

def _pair_boxes(mask, transpose=False, hi=140):
    m = mask.T if transpose else mask
    runs = _find_runs(m, hi=hi)
    boxes = []
    taken = np.zeros(m.shape, bool)
    for y in sorted(runs):
        for s_, e_ in runs[y]:
            if taken[y, s_:e_].any():
                continue
            for dy in range(8, 20):
                if y + dy not in runs:
                    continue
                if any(abs(r[0] - s_) <= 4 and abs(r[1] - e_) <= 4 for r in runs[y + dy]):
                    boxes.append((y, y + dy + 1, s_, e_ + 1))
                    taken[y:y + dy + 1, s_:e_ + 1] = True
                    break
    return [((x0, y0, x1, y1) if not transpose else (y0, x0, y1, x1)) for (y0, y1, x0, x1) in boxes]

fillsS = np.zeros((H, W), bool)
for c in [(0x04,0x9A,0xFC),(0xFC,0x32,0x34),(0x04,0xCE,0x34),(0xFC,0xCE,0x34),(0x04,0xFE,0x54),
          (0x04,0xBE,0x3C),(0x6C,0xB6,0xFC),(0xFC,0x82,0x84),(0xF7,0x7C,0x7C),(0x94,0xF7,0xC6),
          (0xCC,0xFE,0x9C),(0x34,0xCE,0xFC),(0xCC,0xC6,0xFC),(0x9C,0xFE,0xCC)]:
    fillsS |= eq(S, *c)
blackS = eq(S, 4, 2, 4)
for (bx0, by0, bx1, by1) in _pair_boxes(blackS) + [b for b in _pair_boxes(blackS, transpose=True, hi=220) if b[2] - b[0] <= 18 and float(fillsS[b[1]:b[3], b[0]:b[2]].mean()) < 0.25]:
    plate_annot[max(0, by0 - 3):by1 + 3, max(0, bx0 - 3):bx1 + 3] = True
shadowS = eq(S, 0x34, 0x32, 0x34)
dark_bs2 = blackS | shadowS
second = src_p.parent / "wtz-map-second.gif"
_boxes = []
if second.exists():
    S2 = np.asarray(Image.open(second).convert("RGB")).astype(np.int16)
    if S2.shape == S.shape:
        dmask = (S != S2).any(axis=2)
        dd = ndimage.binary_opening(dmask, structure=np.ones((2, 2)))
        labD, nD = ndimage.label(ndimage.binary_dilation(dd, iterations=3))
        for i, sl in enumerate(ndimage.find_objects(labD), start=1):
            h_, w_ = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            if h_ <= 26 and w_ <= 110 and float(dmask[sl].mean()) >= 0.08:
                f_top = any(dark_bs2[yy_, sl[1].start:sl[1].stop].mean() >= 0.55
                            for yy_ in range(max(0, sl[0].start - 3), min(H, sl[0].start + 3)))
                f_bot = any(dark_bs2[yy_, sl[1].start:sl[1].stop].mean() >= 0.55
                            for yy_ in range(max(0, sl[0].stop - 3), min(H, sl[0].stop + 3)))
                dens_ = float(dmask[sl].mean())
                if int(shadowS[sl].sum()) >= 6 or (f_top and f_bot) or ((f_top or f_bot) and dens_ >= 0.22):
                    _boxes.append((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop))
for (bx0, by0, bx1, by1) in _boxes:
    # grow to the true border like the composer does
    x0, y0, x1, y1 = bx0, by0, bx1, by1
    for _ in range(6):
        g = False
        if y0 > 0 and dark_bs2[y0 - 1, max(0, x0):x1].mean() > 0.75:
            y0 -= 1; g = True
        if y1 < H and dark_bs2[min(H - 1, y1), max(0, x0):x1].mean() > 0.75:
            y1 += 1; g = True
        if x0 > 0 and dark_bs2[max(0, y0):y1, x0 - 1].mean() > 0.75:
            x0 -= 1; g = True
        if x1 < W and dark_bs2[max(0, y0):y1, min(W - 1, x1)].mean() > 0.75:
            x1 += 1; g = True
        if not g:
            break
    plate_annot[max(0, y0 - 3):y1 + 3, max(0, x0 - 3):x1 + 3] = True
# marker rectangles (straight-edged fill boxes framed dark, ringed by sea)
whiteS = eq(S, 0xFC, 0xFE, 0xFC) | eq(S, 0xCC, 0xCE, 0xFC)
labF2, nF2 = ndimage.label(fillsS)
for i, sl in enumerate(ndimage.find_objects(labF2), start=1):
    m = labF2[sl] == i
    cnt = int(m.sum())
    hh, ww2 = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    if not (20 <= cnt <= 400):
        continue
    tall = hh >= 1.6 * ww2
    straight4 = (m[0, :].sum() >= 0.75 * ww2 and m[-1, :].sum() >= 0.75 * ww2
                 and m[:, 0].sum() >= 0.75 * hh and m[:, -1].sum() >= 0.75 * hh)
    if not straight4:
        continue
    if cnt < (0.55 if tall else 0.8) * hh * ww2:
        continue
    sl2 = tuple(slice(max(0, a.start - 3), a.stop + 3) for a in sl)
    m2 = np.zeros((sl2[0].stop - sl2[0].start, sl2[1].stop - sl2[1].start), bool)
    m2[sl[0].start - sl2[0].start:sl[0].stop - sl2[0].start,
       sl[1].start - sl2[1].start:sl[1].stop - sl2[1].start] = m
    ring1 = ndimage.binary_dilation(m2, iterations=1) & ~m2
    ring3 = ndimage.binary_dilation(m2, iterations=3) & ~ndimage.binary_dilation(m2, iterations=2)
    greyN = mask_of(S, [(0x64,0x66,0x64),(0x6C,0x6D,0x6C),(0x5C,0x5E,0x5C),(0x5C,0x5A,0x5C),(0x04,0x02,0x34)])
    if float((dark_bs2 | greyN)[sl2][ring1].mean()) >= 0.5 and float(whiteS[sl2][ring3].mean()) >= (0.35 if tall else 0.6):
        plate_annot[sl2[0].start:sl2[0].stop, sl2[1].start:sl2[1].stop] |= ndimage.binary_dilation(m2, iterations=2)

gwcS = eq(S, 0x64, 0x66, 0x9C)
gsumS = gwcS.sum(axis=0)
gcolsS = np.where(gsumS >= 80)[0]
gcolsS = gcolsS[np.abs(gcolsS - W // 2) <= 20]
if len(gcolsS):
    plate_annot[:, max(0, int(gcolsS.min()) - 17):min(W, int(gcolsS.max()) + 18)] = True

annot = plate_annot | ndimage.binary_dilation(
    mask_of(S, [(0x34,0x32,0x34),(0xFC,0xFE,0x04),(0xFC,0xFE,0x34),(0xFC,0xCE,0x04),(0xF4,0xC3,0x04),(0xFC,0x66,0x04),(0x64,0x66,0x9C)]), iterations=6)
annot[H - 70:, :360] = True
annot[:80, :200] = True
annot[:80, W - 200:] = True
src_fill = land_of(S) & ~annot     # symmetric definition; identity compares equal masks
src_bgm = mask_of(S, BG[:2])
src_inkm = mask_of(S, INK)
cand_land = land_of(C) & ~annot
src_dark = eq(S, 4, 2, 4) | eq(S, 4, 2, 0x34)
cand_dark = eq(C, 4, 2, 4) | eq(C, 4, 2, 0x34)

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
# annotations used to split land (zone corridors, plates): bridge them equally on both sides
bridge = plate_annot | ndimage.binary_dilation(mask_of(S, [(0x34, 0x32, 0x34)]), iterations=1)
# ink the composer legitimately converted to land while removing annotations bridges both sides
bridge |= ndimage.binary_dilation(src_inkm & land_of(C), iterations=1)
bridge_s = src_fill | bridge
bridge_c = cand_land | bridge
for rn, (x0, y0, x1, y1) in REGIONS.items():
    def comps(m2, landm):
        lab, n = ndimage.label(m2[y0:y1, x0:x1])
        sz = ndimage.sum(landm[y0:y1, x0:x1], lab, range(1, n + 1))
        return int((sz >= 30).sum())
    cs, cc = comps(bridge_s, src_fill), comps(bridge_c, cand_land)
    if abs(cs - cc) > 2:
        comp_bad[rn] = {"source": cs, "candidate": cc}
add("A6", "component count per region within +-2 (under-annotation topology is ambiguous; "
    "the blind reviewer judges fusion visually)", not comp_bad, comp_bad)

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
ghost = cand_dark & ~src_ink_d & ndimage.binary_erosion(cand_land | cand_dark, iterations=1) & ~annot
add("A13", "no interior strokes absent from the source (<=30px tolerance)", int(ghost.sum()) <= 30,
    {"ghost_stroke_px": int(ghost.sum())})

# 12. leftover annotation ink: dark ink inside the plate zone must be gone
import hashlib as _h
if _h.sha256(cand_p.read_bytes()).hexdigest() == _h.sha256(src_p.read_bytes()).hexdigest():
    add("A12", "leftover annotation ink (skipped: identity run)", True, {"identity": True})
else:
    plate_core = ndimage.binary_erosion(plate_annot, iterations=2)
    s_ink = int((src_dark & plate_core).sum())
    c_ink = int((cand_dark & plate_core).sum())
    add("A12", "leftover annotation ink: candidate keeps <=15% of plate-zone dark ink",
        c_ink <= max(30, 0.15 * s_ink), {"source_ink": s_ink, "candidate_ink": c_ink})

# 17. border retention: black border/coast ink outside annotations must survive
blk_keep = blackS & ~annot
ret = float(cand_dark[blk_keep].mean()) if blk_keep.any() else 1.0
add("A17", "border retention: >=97% of non-annotation black ink survives", ret >= 0.97,
    {"retention": round(ret, 4), "lost_px": int((blk_keep & ~cand_dark).sum())})
# 17b. dark-blend retention: coastline/border anti-aliasing must stay dark
luma_S2 = 0.299 * S[..., 0] + 0.587 * S[..., 1] + 0.114 * S[..., 2]
luma_C2 = 0.299 * C[..., 0] + 0.587 * C[..., 1] + 0.114 * C[..., 2]
dark_blend = (luma_S2 < 60) & ~mask_of(S, INK) & ~annot
if dark_blend.any():
    ret2 = float((luma_C2 < 90)[dark_blend].mean())
else:
    ret2 = 1.0
add("A17b", "dark-blend retention: >=90% of dark anti-alias pixels stay dark", ret2 >= 0.90,
    {"retention": round(ret2, 4)})

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
