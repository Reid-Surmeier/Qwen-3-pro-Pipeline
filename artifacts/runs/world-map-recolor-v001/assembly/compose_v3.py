"""Assembly v3 — fully deterministic, no generative model anywhere.

Reference : native WorldTimeZone GIF (source-locked; typography untouched).
Country   : Natural Earth admin-0 rasterized through the fitted projection
            (countries.npy / country-colour-idx.npy from country_layer.py).
Plates    : found by their NN:NN colon pattern + border-run pairing + strips.

Usage: python3 compose_v3.py REFERENCE.gif OUT_DIR
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ref_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)

g = np.asarray(Image.open(ref_path).convert("RGB")).astype(np.int16)
H, W = g.shape[:2]

def eq(*c):
    return (g == np.array(c, np.int16)).all(axis=2)

BLACK = eq(0x04, 0x02, 0x04)
NAVY = eq(0x04, 0x02, 0x34)
SHADOW = eq(0x34, 0x32, 0x34)
GREY = eq(0x64, 0x66, 0x64) | eq(0x6C, 0x6D, 0x6C) | eq(0x5C, 0x5E, 0x5C) | eq(0x5C, 0x5A, 0x5C)
GRID = eq(0xCC, 0xCE, 0xFC)
ORANGE = eq(0xFC, 0x66, 0x04)
DARK = BLACK | SHADOW | GREY | NAVY
YELLOW = eq(0xFC, 0xFE, 0x04) | eq(0xFC, 0xFE, 0x34)
FILLS = [(0x04, 0x9A, 0xFC), (0xFC, 0x32, 0x34), (0x04, 0xCE, 0x34), (0xFC, 0xCE, 0x34), (0x04, 0xFE, 0x54),
         (0x04, 0xBE, 0x3C), (0x6C, 0xB6, 0xFC), (0xFC, 0x82, 0x84), (0xF7, 0x7C, 0x7C), (0x94, 0xF7, 0xC6),
         (0xCC, 0xFE, 0x9C), (0x34, 0xCE, 0xFC), (0xCC, 0xC6, 0xFC), (0x9C, 0xFE, 0xCC)]
fills = np.zeros((H, W), bool)
for c in FILLS:
    fills |= eq(*c)

mintm = eq(0x9C, 0xFE, 0xCC)
labm, nm = ndimage.label(mintm)
credit = np.zeros((H, W), bool)
if nm:
    sizes_m = ndimage.sum(mintm, labm, range(1, nm + 1))
    sl = ndimage.find_objects(labm)[int(np.argmax(sizes_m))]
    credit[max(0, sl[0].start - 4):sl[0].stop + 4, max(0, sl[1].start - 4):sl[1].stop + 4] = True

grid_x = np.where(GRID.sum(axis=0) > H * 0.25)[0]
grid_y = np.where(GRID.sum(axis=1) > W * 0.25)[0]
gridmask = np.zeros((H, W), bool)
gridmask[:, grid_x] = True
gridmask[grid_y, :] = True

# ---------------------------------------------------------------- R1: plates
dark_bs = BLACK | SHADOW

def colon_seeds(d):
    seeds = []
    for y in range(6, d.shape[0] - 10):
        xs = np.where(d[y])[0]
        for x in xs:
            if x < 6 or x >= d.shape[1] - 6:
                continue
            if d[y + 1, x] and not d[y + 2, x] and not d[y + 3, x] and d[y + 4, x] and d[y + 5, x] \
               and not d[y - 1, x] and not d[y - 2, x] and not d[y + 6, x]:
                seeds.append((x, y))
    return seeds

def box_from_colon(x, y, transpose=False):
    d = dark_bs.T if transpose else dark_bs
    hh, ww = d.shape
    # top border: black run through columns near x, in rows y-10..y-2
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
            top = (y - dy, run_at(y - dy))
            if top[1] is None:
                top = None
    for dy in range(4, 14):
        if bot is None:
            bot = (y + dy, run_at(y + dy))
            if bot[1] is None:
                bot = None
    if top is None or bot is None:
        return None
    x0 = min(top[1][0], bot[1][0]); x1 = max(top[1][1], bot[1][1])
    y0, y1 = top[0], bot[0] + 1
    if transpose:
        return (y0, x0, y1, x1 + 1)
    return (x0, y0, x1 + 1, y1)

badge_boxes = []
R1 = np.zeros((H, W), bool)
for (x, y) in colon_seeds(dark_bs):
    b = box_from_colon(x, y)
    if b:
        badge_boxes.append(b)
for (yv, xv) in colon_seeds(dark_bs.T):
    b = box_from_colon(yv, xv, transpose=True)
    if b:
        badge_boxes.append(b)

def find_runs(mask, lo=28, hi=140):
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

def pair_boxes(mask, transpose=False):
    m = mask.T if transpose else mask
    runs = find_runs(m)
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

# diff-driven plates: a second fetch of the live map differs exactly at the changing digits
diff_mask = np.zeros((H, W), bool)
copies = [q for q in (Path("wtz-map-second.gif"), Path("wtz-map-third.gif")) if q.exists()]
if copies:
    diff = np.zeros((H, W), bool)
    for q in copies:
        b2 = np.asarray(Image.open(q).convert("RGB")).astype(np.int16)
        diff |= (g != b2).any(axis=2)
    diff_dense = ndimage.binary_opening(diff, structure=np.ones((2, 2)))
    labD, nD = ndimage.label(ndimage.binary_dilation(diff_dense, iterations=3))
    for i, sl in enumerate(ndimage.find_objects(labD), start=1):
        h_, w_ = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        dens = float(diff[sl].mean())
        if h_ <= 26 and w_ <= 110 and dens >= 0.08:
            # grow the bbox to the enclosing plate border (dark ring within 5 px)
            y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
            for _ in range(5):
                grew = False
                if y0 > 0 and dark_bs[y0 - 1, max(0, x0):x1].mean() > 0.25:
                    y0 -= 1; grew = True
                if y1 < H and dark_bs[min(H - 1, y1), max(0, x0):x1].mean() > 0.25:
                    y1 += 1; grew = True
                if x0 > 0 and dark_bs[max(0, y0):y1, x0 - 1].mean() > 0.25:
                    x0 -= 1; grew = True
                if x1 < W and dark_bs[max(0, y0):y1, min(W - 1, x1)].mean() > 0.25:
                    x1 += 1; grew = True
                if not grew:
                    break
            badge_boxes.append((int(x0), int(y0), int(x1), int(y1)))


badge_boxes += pair_boxes(BLACK) + pair_boxes(BLACK, transpose=True)
dedup = []
for b in badge_boxes:
    if not any(abs(b[0] - o[0]) <= 3 and abs(b[1] - o[1]) <= 3 for o in dedup):
        dedup.append(b)
badge_boxes = dedup
for (x0, y0, x1, y1) in badge_boxes:
    if credit[max(0, y0):y1, max(0, x0):x1].any():
        continue
    R1[max(0, y0 - 2):y1 + 4, max(0, x0 - 2):x1 + 4] = True
R1 |= diff_mask & ~credit

# ---------------------------------------------------------------- R2: DST tags
R2 = np.zeros((H, W), bool)
tag_count = 0
laby, ny = ndimage.label(ndimage.binary_dilation(YELLOW, iterations=1))
for i, sl in enumerate(ndimage.find_objects(laby), start=1):
    h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    dk = DARK[sl][laby[sl] == i].mean() if (laby[sl] == i).any() else 0
    if 4 <= h <= 26 and 8 <= w <= 56 and 0.03 <= dk <= 0.8:
        R2[max(0, sl[0].start - 1):sl[0].stop + 1, max(0, sl[1].start - 1):sl[1].stop + 1] = True
        tag_count += 1

# --------------------------------------- R3: corner strips (dates, +1/-1, UTC)
strip = np.zeros((H, W), bool)
strip[H - 70:, :360] = True
strip[:80, :200] = True
strip[:80, W - 200:] = True
R3 = strip & (DARK | ORANGE | YELLOW) & ~credit & ~fills
R3 = ndimage.binary_dilation(R3, iterations=1) & strip & ~credit & ~fills

# ------------------------------------------------------------------ R4: orange
R4 = ndimage.binary_dilation(ORANGE, iterations=1) & ~credit

# ------------------------------------------- R5: Greenwich lines + caption
R5 = np.zeros((H, W), bool)
corridor = [x for x in range(W // 2 - 15, W // 2 + 16) if BLACK[:, x].sum() > 0.25 * H]
for x in corridor:
    col = BLACK[:, x]
    dcol = np.diff(np.r_[0, col.view(np.int8), 0])
    for a, b in zip(np.where(dcol == 1)[0], np.where(dcol == -1)[0]):
        if b - a >= 5:
            R5[a:b, x] = True
if corridor:
    lo, hi = min(corridor), max(corridor) + 1
    labt, nt = ndimage.label((BLACK | NAVY | GREY | SHADOW) & ~R1, structure=np.ones((3, 3)))
    for i, sl in enumerate(ndimage.find_objects(labt), start=1):
        if sl[1].start >= lo - 12 and sl[1].stop <= hi + 12:
            if int((labt[sl] == i).sum()) <= 320 and not fills[sl][labt[sl] == i].any():
                R5[sl] |= (labt[sl] == i)

# ------------------------------------------------------- country colour layer
cid = np.load("countries.npy")
colour_idx = np.load("country-colour-idx.npy")
PALETTE = np.array([[0xFC, 0x32, 0x34], [0x04, 0x9A, 0xFC], [0x04, 0xCE, 0x34], [0xFC, 0xCE, 0x34],
                    [0xFC, 0x82, 0x84], [0x6C, 0xB6, 0xFC], [0x94, 0xF7, 0xC6], [0xCC, 0xC6, 0xFC],
                    [0xCC, 0xFE, 0x9C], [0x34, 0xCE, 0xFC]], np.int16)
# nearest-country field for islands NE misses
dist_idx = ndimage.distance_transform_edt(cid < 0, return_distances=True, return_indices=True)
cid_near = cid[dist_idx[1][0], dist_idx[1][1]]
cid_dist = dist_idx[0]

land = fills & ~R1 & ~R2 & ~credit
labp, npatch = ndimage.label(land)
R6 = np.zeros((H, W), bool)
patch_country = {}
objs_p = ndimage.find_objects(labp)
for i in range(1, npatch + 1):
    sl = objs_p[i - 1]
    m = labp[sl] == i
    ids = cid[sl][m]
    good = ids[ids >= 0]
    if len(good) >= max(3, 0.3 * m.sum()):
        vals, cts = np.unique(good, return_counts=True)
        patch_country[i] = int(vals[cts.argmax()])
    else:
        near = cid_near[sl][m]
        dists = cid_dist[sl][m]
        near = near[(near >= 0) & (dists <= 15)]
        if len(near):
            vals, cts = np.unique(near, return_counts=True)
            patch_country[i] = int(vals[cts.argmax()])
    if i in patch_country:
        R6[sl] |= m

# ------------------------------------------------------- R7: grey zone lines
labz, nz = ndimage.label(GREY & ~R5, structure=np.ones((3, 3)))
keepz = np.zeros(nz + 1, bool)
for i, sl in enumerate(ndimage.find_objects(labz), start=1):
    h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    cnt = int((labz[sl] == i).sum())
    m2 = labz[sl] == i
    near_land = float(ndimage.binary_dilation(fills, iterations=2)[sl][m2].mean())
    keepz[i] = (max(h, w) >= 40 and cnt <= 0.08 * h * w + 3 * max(h, w)) or (cnt <= 60 and near_land >= 0.6)
R7 = keepz[labz] & ~R1 & ~R3 & ~credit

# ---------------------------------------------------------------- compose
out = g.copy()
wiped = (R1 | R2 | R3 | R4 | R5) & ~credit
out[wiped] = (0xFC, 0xFE, 0xFC)
out[wiped & gridmask] = (0xCC, 0xCE, 0xFC)

# paint countries
for i, ci in patch_country.items():
    sl = objs_p[i - 1]
    m = labp[sl] == i
    out[sl][m] = PALETTE[colour_idx[ci]]

# grey lines: between two countries -> black border; inside one country -> its colour; ocean -> light grey
country_px = np.full((H, W), -1, np.int32)
for i, ci in patch_country.items():
    sl = objs_p[i - 1]
    m = labp[sl] == i
    tgt = country_px[sl]
    tgt[m] = ci
    country_px[sl] = tgt
cp_d = ndimage.grey_dilation(country_px, size=5)
cp_d2 = -ndimage.grey_dilation(-country_px, size=5)     # min-dilation (another neighbour)
on_line = R7
between_countries = on_line & (cp_d >= 0) & (cp_d2 >= 0) & (cp_d != cp_d2)
inside_country = on_line & (cp_d >= 0) & (cp_d == cp_d2)
ocean_line = on_line & ~between_countries & ~inside_country
out[between_countries] = (0x04, 0x02, 0x04)
ic = np.where(inside_country)
out[ic[0], ic[1]] = PALETTE[colour_idx[cp_d[ic]]]
out[ocean_line] = (0xB8, 0xB8, 0xB8)

# under-plate reconstruction: country colour where NE says land, else white+grid
under = wiped & (cid >= 0)
uc = np.where(under)
out[uc[0], uc[1]] = PALETTE[colour_idx[cid[uc]]]
# clip the reconstruction to plausible land: drop reconstructed pixels not near GIF land
near_gif_land = ndimage.binary_dilation(fills, iterations=8)
bad = under & ~near_gif_land
out[bad] = (0xFC, 0xFE, 0xFC)
out[bad & gridmask] = (0xCC, 0xCE, 0xFC)
# outline reconstructed land inside plates
filled = under & near_gif_land
edge_px = filled & ~ndimage.binary_erosion(filled | fills | BLACK, iterations=1)
out[edge_px] = (0x04, 0x02, 0x04)

# frame hammer + sliver cleanup around plates
hug = ndimage.binary_dilation(R1, iterations=3) & (BLACK | SHADOW | GREY) & ~NAVY & ~credit & ~wiped
far_land = fills & ~ndimage.binary_dilation(R1, iterations=4)
kill = hug & ~ndimage.binary_dilation(far_land, iterations=1)
out[kill] = (0xFC, 0xFE, 0xFC)
out[kill & gridmask] = (0xCC, 0xCE, 0xFC)
wiped |= kill
dark_left = (BLACK | SHADOW | GREY) & ~wiped & ~credit
lab_f, n_f = ndimage.label(dark_left, structure=np.ones((3, 3)))
near_wipe = ndimage.binary_dilation(wiped, iterations=2)
for i, sl in enumerate(ndimage.find_objects(lab_f), start=1):
    m = lab_f[sl] == i
    h_, w_ = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    cnt_ = int(m.sum())
    long_ = max(h_, w_)
    if cnt_ > 400 or long_ < 18 or cnt_ / max(1, long_) > 2.6:
        continue
    if (near_wipe[sl][m]).mean() >= 0.35 and not fills[sl][m].any():
        sub = out[sl]
        sub[m] = (0xFC, 0xFE, 0xFC)
        sub[m & gridmask[sl]] = (0xCC, 0xCE, 0xFC)
        wiped[sl][m] = True

# restore labels the plate boxes overlapped: navy always; black letter-words all-or-nothing
pmask = (R1 | R2) & ~credit
label_edits = np.zeros((H, W), bool)
nav = NAVY & pmask
out[nav] = (0x04, 0x02, 0x34)
lab_b, n_b = ndimage.label(BLACK, structure=np.ones((3, 3)))
total_b = ndimage.sum(BLACK, lab_b, range(1, n_b + 1))
inside_b = ndimage.sum(pmask, lab_b, range(1, n_b + 1))
frac_b = inside_b / np.maximum(total_b, 1)
objs_b = ndimage.find_objects(lab_b)
letter = np.zeros(n_b + 1, bool)
for j in range(n_b):
    bs = objs_b[j]
    bh, bw = bs[0].stop - bs[0].start, bs[1].stop - bs[1].start
    letter[j + 1] = total_b[j] <= 60 and bh <= 14 and bw <= 14
letters_mask = letter[lab_b] | NAVY
wlab, wn = ndimage.label(ndimage.binary_dilation(letters_mask, structure=np.ones((3, 9))))
for wi, wsl in enumerate(ndimage.find_objects(wlab), start=1):
    wm = wlab[wsl] == wi
    ids = np.unique(lab_b[wsl][wm & BLACK[wsl]])
    ids = ids[ids > 0]
    if len(ids) and (frac_b[ids - 1] >= 0.45).any():
        gone = wm & letters_mask[wsl] & np.isin(lab_b[wsl], ids) & ~R1[wsl] & ~R2[wsl]
        sub = out[wsl]
        sub[gone] = (0xFC, 0xFE, 0xFC)
        sub[gone & gridmask[wsl]] = (0xCC, 0xCE, 0xFC)
        label_edits[wsl] |= gone
        continue
    rest = wm & letters_mask[wsl] & pmask[wsl]
    sub = out[wsl]
    sub[rest & BLACK[wsl]] = (0x04, 0x02, 0x04)
    sub[rest & NAVY[wsl]] = (0x04, 0x02, 0x34)

declared = R1 | R2 | R3 | R4 | R5 | R6 | R7 | wiped | label_edits

# mechanical colour-accuracy spot check on major countries
names_l = json.load(open("country-names.json"))
checks = ["Russia", "Canada", "United States of America", "Brazil", "China", "Australia", "India",
          "Mexico", "Argentina", "Kazakhstan", "Mongolia", "France", "Germany", "Egypt", "South Africa", "Indonesia"]
spot = {}
for nm in checks:
    if nm not in names_l:
        continue
    ci = names_l.index(nm)
    m = (country_px == ci)
    if not m.any():
        spot[nm] = "no patch"
        continue
    lab_c, n_c = ndimage.label(m)
    big = int(np.argmax(ndimage.sum(m, lab_c, range(1, n_c + 1)))) + 1
    ys, xs2 = np.where(lab_c == big)
    cyx = (int(np.median(ys)), int(np.median(xs2)))
    got = tuple(int(v) for v in out[cyx])
    want = tuple(int(v) for v in PALETTE[colour_idx[ci]])
    spot[nm] = "ok" if got == want else f"got {got} want {want} at {cyx}"
print("SPOT:", json.dumps(spot))

# ---------------------------------------------------------------- fidelity
changed = (out != g).any(axis=2)
outside = changed & ~declared
report = {
    "reference": {"file": ref_path.name, "sha256": hashlib.sha256(ref_path.read_bytes()).hexdigest(), "size": [W, H]},
    "country_layer": "Natural Earth 110m admin-0 via fitted Mercator (projection.json); no generative model used",
    "declared_pixels": int(declared.sum()),
    "changed_pixels": int(changed.sum()),
    "outside_changed": int(outside.sum()),
    "passed": bool(outside.sum() == 0),
    "regions": {"R1_plates": len(badge_boxes), "R2_tags": tag_count, "R6_patches": len(patch_country),
                "countries_used": len({v for v in patch_country.values()})},
}
Image.fromarray(out.astype(np.uint8)).save(out_dir / "assembled-v3.png")
Image.fromarray(out.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(out_dir / "assembled-v3-2x.png")
(out_dir / "fidelity-report-v3.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: report[k] for k in ("declared_pixels", "outside_changed", "passed", "regions")}))
if not report["passed"]:
    raise SystemExit("FIDELITY FAILED")
