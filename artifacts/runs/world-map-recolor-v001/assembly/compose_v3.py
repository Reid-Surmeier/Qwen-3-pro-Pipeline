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
ink3 = ~eq(0xFC, 0xFE, 0xFC) & ~GRID
R3 = strip & ink3 & ~credit & ~fills
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

# Greenwich meridian double line is drawn in slate-blue #64669C — but plates use
# that colour too, so the corridor logic is limited to the meridian columns.
GWLINE = eq(0x64, 0x66, 0x9C)
colsum_gw = GWLINE.sum(axis=0)
gwcols = np.where(colsum_gw >= 80)[0]
gwcols = gwcols[np.abs(gwcols - W // 2) <= 20]
print("greenwich columns:", gwcols.tolist())
corr_mask = np.zeros((H, W), bool)
if len(gwcols):
    corr_mask[:, max(0, int(gwcols.min()) - 6):min(W, int(gwcols.max()) + 7)] = True
GWL_COR = GWLINE & corr_mask
gwband = ndimage.binary_dilation(GWL_COR, structure=np.ones((1, 9))) & (eq(0xFC, 0xFE, 0xFC) | GRID)
seg = np.zeros((H, W), bool)
if len(gwcols):
    for x in range(max(0, int(gwcols.min()) - 4), min(W, int(gwcols.max()) + 5)):
        colm = BLACK[:, x] | GWL_COR[:, x]
        dcol = np.diff(np.r_[0, colm.view(np.int8), 0])
        for a, b in zip(np.where(dcol == 1)[0], np.where(dcol == -1)[0]):
            if b - a >= 4:
                seg[a:b, x] = True
bandall = (GWL_COR | gwband | seg) & ~credit
R5 |= bandall | (GWLINE & ~credit)

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

WHITE_BG = (g > 235).all(axis=2)
cells = (WHITE_BG | GRID) & ~ndimage.binary_dilation(BLACK | NAVY | SHADOW, iterations=1)
labC, nC = ndimage.label(cells)
border_ids = np.unique(np.r_[labC[0, :], labC[-1, :], labC[:, 0], labC[:, -1]])
landfrac = ndimage.mean((cid >= 0).astype(np.float32), labC, range(1, nC + 1))
keepW = np.zeros(nC + 1, bool)
keepW[1:] = landfrac >= 0.55
keepW[border_ids] = False
keepW[0] = False
white_land = keepW[labC]
for _ in range(2):   # grow back over the 1-px ring the dark dilation excluded
    white_land |= ndimage.binary_dilation(white_land) & (WHITE_BG | GRID) & (cid >= 0)
white_land &= (WHITE_BG | GRID) & ~credit & ~strip
land = (fills | white_land) & ~R1 & ~R2 & ~credit
labp, npatch = ndimage.label(land)
R6 = np.zeros((H, W), bool)
patch_country = {}
objs_p = ndimage.find_objects(labp)
small_ids = []
for i in range(1, npatch + 1):
    sl = objs_p[i - 1]
    m = labp[sl] == i
    if m.sum() < 12:
        small_ids.append(i)
        continue
    core = ndimage.binary_erosion(m, iterations=2)
    sample = cid[sl][core if core.sum() >= 6 else m]
    good = sample[sample >= 0]
    if len(good) >= max(3, 0.3 * (core.sum() if core.sum() >= 6 else m.sum())):
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
# tiny fragments inherit the dominant assigned country around them, else nearest NE
cty_tmp = np.full((H, W), -1, np.int32)
for i, ci in patch_country.items():
    sl = objs_p[i - 1]
    m = labp[sl] == i
    t = cty_tmp[sl]; t[m] = ci; cty_tmp[sl] = t
for i in small_ids:
    sl = objs_p[i - 1]
    sl2 = tuple(slice(max(0, a.start - 4), a.stop + 4) for a in sl)
    m = labp[sl] == i
    ring = cty_tmp[sl2]
    vals, cts = np.unique(ring[ring >= 0], return_counts=True)
    if len(vals):
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

# second chance: any sizable patch still unassigned takes the nearest NE country within 40 px
un_report = []
for i in range(1, npatch + 1):
    if i in patch_country:
        continue
    sl = objs_p[i - 1]
    m = labp[sl] == i
    if m.sum() < 12:
        continue
    near = cid_near[sl][m]
    dists = cid_dist[sl][m]
    near = near[(near >= 0) & (dists <= 40)]
    if len(near):
        vals, cts = np.unique(near, return_counts=True)
        patch_country[i] = int(vals[cts.argmax()])
        R6[sl] |= m
    else:
        un_report.append({"bbox": [int(sl[1].start), int(sl[0].start), int(sl[1].stop), int(sl[0].stop)], "px": int(m.sum())})
print("unassigned patches:", json.dumps(un_report))

# ------------------------------------------------------- R7: grey zone lines
labz, nz = ndimage.label(GREY & ~R5, structure=np.ones((3, 3)))
keepz = np.zeros(nz + 1, bool)
for i, sl in enumerate(ndimage.find_objects(labz), start=1):
    h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    cnt = int((labz[sl] == i).sum())
    m2 = labz[sl] == i
    near_land = float(ndimage.binary_dilation(fills, iterations=2)[sl][m2].mean())
    keepz[i] = (max(h, w) >= 40 and cnt <= 0.08 * h * w + 3 * max(h, w)) or (cnt <= 60 and near_land >= 0.6)
R7 = (keepz[labz] | (GREY & (cid >= 0))) & ~R1 & ~R3 & ~credit

# ---------------------------------------------------------------- compose
out = g.copy()
wiped = (R1 | R2 | R3 | R4 | R5) & ~credit
out[wiped] = (0xFC, 0xFE, 0xFC)
out[wiped & gridmask] = (0xCC, 0xCE, 0xFC)

# paint countries; patches spanning 2+ countries are painted per-pixel with drawn borders
multi = 0
for i, ci in patch_country.items():
    sl = objs_p[i - 1]
    m = labp[sl] == i
    ids = cid[sl][m]
    good = ids[ids >= 0]
    split = False
    if len(good) > 40:
        vals, cts = np.unique(good, return_counts=True)
        share = cts / cts.sum()
        top2 = share[np.argsort(-share)[:2]]
        if len(vals) >= 2 and (top2[1] >= 0.12 or int(np.sort(cts)[-2]) >= 30):
            split = True
    if not split:
        out[sl][m] = PALETTE[colour_idx[ci]]
        continue
    multi += 1
    cand_vals = vals[(share >= 0.08) | (cts >= 20)]
    dmin = np.full(m.shape, 1e18)
    use = np.full(m.shape, -1, np.int32)
    for cval in cand_vals:
        seedm = (cid[sl] == cval) & m
        if not seedm.any():
            continue
        dd = ndimage.distance_transform_edt(~seedm)
        upd = dd < dmin
        dmin[upd] = dd[upd]
        use[upd] = int(cval)
    ok_px = m & (use >= 0)
    subout = out[sl]
    subout[ok_px] = PALETTE[colour_idx[use[ok_px]]]
    subout[m & ~ok_px] = PALETTE[colour_idx[ci]]
    # internal border where the country id changes inside the patch
    bord = np.zeros_like(m)
    bord[:, 1:] |= (use[:, 1:] != use[:, :-1]) & m[:, 1:] & m[:, :-1] & (use[:, 1:] >= 0) & (use[:, :-1] >= 0)
    bord[1:, :] |= (use[1:, :] != use[:-1, :]) & m[1:, :] & m[:-1, :] & (use[1:, :] >= 0) & (use[:-1, :] >= 0)
    subout[bord] = (0x04, 0x02, 0x04)
print("multi-country patches split:", multi)

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
oc_sea = ocean_line & (cid < 0)
out[oc_sea] = (0xB8, 0xB8, 0xB8)
oc_land = np.where(ocean_line & (cid >= 0))
out[oc_land[0], oc_land[1]] = PALETTE[colour_idx[cid[oc_land]]]

# plates whose surrounding ring is land get reconstructed across their full box
plate_full = np.zeros((H, W), bool)
landgif0 = (fills | white_land) & ~wiped
for (x0, y0, x1, y1) in badge_boxes:
    ys0, ys1 = max(0, y0 - 4), min(H, y1 + 6)
    xs0, xs1 = max(0, x0 - 4), min(W, x1 + 6)
    ring = landgif0[ys0:ys1, xs0:xs1].copy()
    if ring.shape[0] > 4 and ring.shape[1] > 4:
        ring[2:-2, 2:-2] = False
    denom = max(1, int(ring.size - max(0, ring.shape[0] - 4) * max(0, ring.shape[1] - 4)))
    inner = (cid[max(0, y0 - 2):y1 + 4, max(0, x0 - 2):x1 + 4] >= 0) | landgif0[max(0, y0 - 2):y1 + 4, max(0, x0 - 2):x1 + 4]
    if ring.sum() / denom >= 0.55 and inner.size and inner.mean() >= 0.55:
        plate_full[max(0, y0 - 2):y1 + 4, max(0, x0 - 2):x1 + 4] = True
# sea truth: pre-smear NE says water and no GIF land within 4 px -> stays sea
cid_raw = np.load("countries-raw.npy")
gifdist = ndimage.distance_transform_edt(~landgif0)
sea_truth = (cid_raw < 0) & (gifdist > 2)
# under-plate reconstruction: country colour where NE says land, else white+grid
under = wiped & (cid >= 0) & ~bandall & ~sea_truth
uc = np.where(under)
out[uc[0], uc[1]] = PALETTE[colour_idx[cid[uc]]]
# clip the reconstruction to plausible land: drop reconstructed pixels not near GIF land
sandL = np.zeros((H, W), bool); sandR = np.zeros((H, W), bool)
for k in range(1, 41):
    sandL |= np.roll(landgif0, k, axis=1)
    sandR |= np.roll(landgif0, -k, axis=1)
sandP = sandL & sandR
near_gif_land = ndimage.binary_dilation(landgif0, iterations=5) | plate_full | (sandP & ~bandall)
# misregistered land under plates: NE says water but GIF land is near -> nearest country
under2 = wiped & (cid < 0) & near_gif_land & (cid_dist <= 6) & ~bandall & ~sea_truth
u2 = np.where(under2)
out[u2[0], u2[1]] = PALETTE[colour_idx[cid_near[u2]]]
# outline reconstructed land inside plates
filled = under | under2
edge_base = filled & ~bandall
edge_px = edge_base & ~ndimage.binary_erosion(filled | fills | BLACK, iterations=1)
rawland_e = cid_raw >= 0
ne_coast = rawland_e & ~ndimage.binary_erosion(rawland_e, iterations=1)
edge_px &= ndimage.binary_dilation(ne_coast, iterations=1)
out[edge_px] = (0x04, 0x02, 0x04)
# Greenwich corridor: repaint only pixels sandwiched by real GIF land on both sides
landgif = fills | white_land
land_l = np.zeros((H, W), bool)
land_r = np.zeros((H, W), bool)
for k in range(1, 8):
    land_l |= np.roll(landgif, k, axis=1)
    land_r |= np.roll(landgif, -k, axis=1)
sandw = bandall & land_l & land_r
sc = sandw & (cid >= 0) & ~sea_truth
si = np.where(sc)
out[si[0], si[1]] = PALETTE[colour_idx[cid[si]]]
sn = sandw & (cid < 0) & (cid_dist <= 8) & ~sea_truth
sj = np.where(sn)
out[sj[0], sj[1]] = PALETTE[colour_idx[cid_near[sj]]]
rest_b = bandall & ~(sc | sn)
out[rest_b] = (0xFC, 0xFE, 0xFC)
out[rest_b & gridmask] = (0xCC, 0xCE, 0xFC)

# frame hammer + sliver cleanup around plates
hug = ndimage.binary_dilation(R1, iterations=3) & (BLACK | SHADOW | GREY) & ~NAVY & ~credit & ~wiped
far_land = fills & ~ndimage.binary_dilation(R1, iterations=4)
kill = hug & ~ndimage.binary_dilation(far_land, iterations=1)
cpk = ndimage.grey_dilation(country_px, size=7)
kl = kill & (cid >= 0) & (cpk >= 0)
ki = np.where(kl)
out[ki[0], ki[1]] = PALETTE[colour_idx[cpk[ki]]]
kw = kill & ~kl
out[kw] = (0xFC, 0xFE, 0xFC)
out[kw & gridmask] = (0xCC, 0xCE, 0xFC)
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
        ml = m & (cid[sl] >= 0) & (cpk[sl] >= 0)
        yi2, xi2 = np.where(ml)
        sub[yi2, xi2] = PALETTE[colour_idx[cpk[sl][yi2, xi2]]]
        mw = m & ~ml
        sub[mw] = (0xFC, 0xFE, 0xFC)
        sub[mw & gridmask[sl]] = (0xCC, 0xCE, 0xFC)
        wiped[sl][m] = True

# artifact sweep: tiny palette-colour islands surrounded by one other colour take it
artifact_edits = np.zeros((H, W), bool)
pal_set = {tuple(int(v) for v in c) for c in PALETTE}
is_pal = np.zeros((H, W), bool)
for c in PALETTE:
    is_pal |= (out == c).all(axis=2)
lab_a, n_a = ndimage.label(is_pal)
sz_a = ndimage.sum(is_pal, lab_a, range(1, n_a + 1))
for i in np.where(sz_a < 10)[0] + 1:
    sl = ndimage.find_objects(lab_a == i)[0]
    sl2 = tuple(slice(max(0, a.start - 2), a.stop + 2) for a in sl)
    m = lab_a[sl2] == i
    ring = ndimage.binary_dilation(m, iterations=2) & ~m
    rc = out[sl2][ring]
    palr = np.array([tuple(int(v) for v in c) in pal_set for c in rc])
    if palr.mean() >= 0.7 and palr.any():
        vals, cts = np.unique(rc[palr], axis=0, return_counts=True)
        if cts.max() / palr.sum() >= 0.7:
            out[sl2][m] = vals[cts.argmax()]
            artifact_edits[sl2] |= m

# floating plate-border remnants: thin straight black bits near wiped plates, not near land
darkrem = (out == np.array((0x04, 0x02, 0x04), np.int16)).all(axis=2) & ~credit & ~edge_px
nearR1b = ndimage.binary_dilation(R1 | R2, iterations=3)
land_nearb = ndimage.binary_dilation(landgif0, iterations=2)
labB2, nB2 = ndimage.label(darkrem, structure=np.ones((3, 3)))
objsB2 = ndimage.find_objects(labB2)
n_br = 0
for i in range(1, nB2 + 1):
    slb = objsB2[i - 1]
    hb, wb = slb[0].stop - slb[0].start, slb[1].stop - slb[1].start
    if max(hb, wb) < 10 or hb * wb > 900:
        continue
    m = labB2[slb] == i
    cnt = int(m.sum())
    if cnt > 40 or cnt / max(hb, wb) > 2.6:
        continue
    sl2b = tuple(slice(max(0, a.start - 2), a.stop + 2) for a in slb)
    m2b = labB2[sl2b] == i
    ringb = ndimage.binary_dilation(m2b, iterations=2) & ~m2b
    rcb = out[sl2b][ringb]
    sea_like = ((rcb == (0xFC, 0xFE, 0xFC)).all(axis=1) | (rcb == (0xCC, 0xCE, 0xFC)).all(axis=1)
                | (rcb == (0xB8, 0xB8, 0xB8)).all(axis=1))
    if not len(rcb) or sea_like.mean() < 0.7:
        continue
    sub = out[slb]
    sub[m] = (0xFC, 0xFE, 0xFC)
    sub[m & gridmask[slb]] = (0xCC, 0xCE, 0xFC)
    artifact_edits[slb] |= m
    n_br += 1
print("plate border remnants wiped:", n_br)

# restore labels the plate boxes overlapped: navy always; black letter-words all-or-nothing
pmask = (R1 | R2) & ~credit
label_edits = np.zeros((H, W), bool)
nav = NAVY & pmask
out[nav] = (0x04, 0x02, 0x34)
cp_g = ndimage.grey_dilation(country_px, size=9)
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
        onl = gone & (cp_g[wsl] >= 0) & (cid[wsl] >= 0)
        yi, xi = np.where(onl)
        sub[yi, xi] = PALETTE[colour_idx[cp_g[wsl][yi, xi]]]
        offl = gone & ~onl
        sub[offl] = (0xFC, 0xFE, 0xFC)
        sub[offl & gridmask[wsl]] = (0xCC, 0xCE, 0xFC)
        label_edits[wsl] |= gone
        continue
    rest = wm & letters_mask[wsl] & pmask[wsl]
    sub = out[wsl]
    sub[rest & BLACK[wsl]] = (0x04, 0x02, 0x04)
    sub[rest & NAVY[wsl]] = (0x04, 0x02, 0x34)

# anti-alias & marker cleanup: blend pixels keep the OLD fill tint after repainting.
OUTSET = [tuple(int(v) for v in c) for c in PALETTE] + [
    (0x04, 0x02, 0x04), (0x04, 0x02, 0x34), (0xFC, 0xFE, 0xFC), (0xCC, 0xCE, 0xFC), (0xB8, 0xB8, 0xB8),
    (0x34, 0x32, 0x34), (0x64, 0x66, 0x64), (0x6C, 0x6D, 0x6C), (0x5C, 0x5E, 0x5C), (0x5C, 0x5A, 0x5C)]
known = np.zeros((H, W), bool)
for c in OUTSET:
    known |= (out == np.array(c, np.int16)).all(axis=2)
odd = ~known & ~credit
landish = ndimage.binary_dilation(R6, iterations=2)
cp_near = ndimage.grey_dilation(country_px, size=7)
darkpx = out.sum(axis=2) < 300
bgnow = ((out == np.array((0xFC, 0xFE, 0xFC), np.int16)).all(axis=2)
         | (out == np.array((0xCC, 0xCE, 0xFC), np.int16)).all(axis=2))
white_next = ndimage.binary_dilation(bgnow, iterations=1)
a_dark = odd & landish & darkpx
a_light = odd & landish & ~darkpx & (cp_near >= 0) & (cid >= 0)
out[a_dark] = (0x04, 0x02, 0x04)
al = np.where(a_light)
out[al[0], al[1]] = PALETTE[colour_idx[cp_near[al]]]
b_zone = odd & ~landish & ndimage.binary_dilation(ORANGE | GWLINE, iterations=2)
out[b_zone] = (0xFC, 0xFE, 0xFC)
out[b_zone & gridmask] = (0xCC, 0xCE, 0xFC)
artifact_edits |= a_dark | a_light | b_zone
print("aa cleanup:", int(a_dark.sum()), "dark", int(a_light.sum()), "light", int(b_zone.sum()), "zone")

# dashed zone/state borders inside one country: collinear chains of tiny dashes
import collections as _c
GREY_OUT = np.zeros((H, W), bool)
for c in [(0x64, 0x66, 0x64), (0x6C, 0x6D, 0x6C), (0x5C, 0x5E, 0x5C), (0x5C, 0x5A, 0x5C), (0x34, 0x32, 0x34)]:
    GREY_OUT |= (out == np.array(c, np.int16)).all(axis=2)
dashish = ((out == np.array((0x04, 0x02, 0x04), np.int16)).all(axis=2) | GREY_OUT) & ~credit
labK, nK = ndimage.label(dashish, structure=np.ones((3, 3)))
objsK = ndimage.find_objects(labK)
cands = []
for i in range(1, nK + 1):
    slk = objsK[i - 1]
    hk, wk = slk[0].stop - slk[0].start, slk[1].stop - slk[1].start
    if hk <= 4 and wk <= 4 and int((labK[slk] == i).sum()) <= 9:
        cands.append((i, (slk[0].start + slk[0].stop) // 2, (slk[1].start + slk[1].stop) // 2))
byx = _c.defaultdict(set)
byy = _c.defaultdict(set)
for i, cy, cx in cands:
    for o in (-1, 0, 1):
        byx[cx + o].add((cy, i))
        byy[cy + o].add((cx, i))
chain_ids = set()
for d in (byx, byy):
    for lst0 in d.values():
        lst = sorted(lst0)
        run = [lst[0]]
        for q in lst[1:]:
            if q[0] - run[-1][0] <= 8:
                run.append(q)
            else:
                if len({t[1] for t in run}) >= 4:
                    chain_ids |= {t[1] for t in run}
                run = [q]
        if len({t[1] for t in run}) >= 4:
            chain_ids |= {t[1] for t in run}
pal_lookup = {tuple(int(v) for v in c): k for k, c in enumerate(PALETTE)}
n_dash = 0
for i, cy, cx in cands:
    if i not in chain_ids:
        continue
    slk = objsK[i - 1]
    sl2 = tuple(slice(max(0, a.start - 2), a.stop + 2) for a in slk)
    m2 = labK[sl2] == i
    ring = ndimage.binary_dilation(m2, iterations=2) & ~m2
    rc = out[sl2][ring]
    palr = np.array([tuple(int(v) for v in c) in pal_lookup for c in rc])
    if palr.any() and palr.mean() >= 0.7:
        vals3, cts3 = np.unique(rc[palr], axis=0, return_counts=True)
        if cts3.max() / palr.sum() >= 0.7:
            out[sl2][m2] = vals3[cts3.argmax()]
            artifact_edits[sl2] |= m2
            n_dash += 1
print("dash chain segments recoloured:", n_dash)

# white dash remnants: tiny white islands ringed by a single country colour (never near text)
WHITE_OUT = (out == np.array((0xFC, 0xFE, 0xFC), np.int16)).all(axis=2) & ~credit
labW2, nW2 = ndimage.label(WHITE_OUT)
objsW2 = ndimage.find_objects(labW2)
darkout = ((out == np.array((0x04, 0x02, 0x04), np.int16)).all(axis=2)
           | (out == np.array((0x04, 0x02, 0x34), np.int16)).all(axis=2))
n_wd = 0
for i in range(1, nW2 + 1):
    slw = objsW2[i - 1]
    if slw[0].stop - slw[0].start > 4 or slw[1].stop - slw[1].start > 4:
        continue
    sl2 = tuple(slice(max(0, a.start - 2), a.stop + 2) for a in slw)
    m2 = labW2[sl2] == i
    if int(m2.sum()) > 9:
        continue
    ring = ndimage.binary_dilation(m2, iterations=2) & ~m2
    if darkout[sl2][ring].any():
        continue
    rc = out[sl2][ring]
    palr = np.array([tuple(int(v) for v in c) in pal_lookup for c in rc])
    if palr.any() and palr.mean() >= 0.85:
        vals4, cts4 = np.unique(rc[palr], axis=0, return_counts=True)
        if cts4.max() / palr.sum() >= 0.85:
            out[sl2][m2] = vals4[cts4.argmax()]
            artifact_edits[sl2] |= m2
            n_wd += 1
print("white dash remnants filled:", n_wd)

# orange residue: any off-set colour within 2 px of the (wiped) orange date line
odd2 = np.zeros((H, W), bool)
for c in OUTSET:
    odd2 |= (out == np.array(c, np.int16)).all(axis=2)
odd2 = ~odd2 & ~credit
oz = odd2 & ndimage.binary_dilation(ORANGE, iterations=2)
ozl = oz & (cp_near >= 0) & (cid >= 0)
oi = np.where(ozl)
out[oi[0], oi[1]] = PALETTE[colour_idx[cp_near[oi]]]
ozw = oz & ~ozl
out[ozw] = (0xFC, 0xFE, 0xFC)
out[ozw & gridmask] = (0xCC, 0xCE, 0xFC)
artifact_edits |= oz
print("orange residue cleared:", int(oz.sum()))

# final consistency sweep: tiny palette islands created by earlier passes
n_fix2 = 0
for kcol, ccol in enumerate(PALETTE):
    mask_c = (out == ccol).all(axis=2) & ~credit
    lab_f2, n_f2 = ndimage.label(mask_c)
    if not n_f2:
        continue
    objs_f2 = ndimage.find_objects(lab_f2)
    sz_f2 = ndimage.sum(mask_c, lab_f2, range(1, n_f2 + 1))
    for i in np.where(sz_f2 <= 200)[0] + 1:
        sl = objs_f2[i - 1]
        sl2 = tuple(slice(max(0, a.start - 2), a.stop + 2) for a in sl)
        m = lab_f2[sl2] == i
        cc2 = cid[sl2][m]
        cc2 = cc2[cc2 >= 0]
        if len(cc2) < 6 or len(cc2) < 0.4 * int(m.sum()):
            continue
        vals6, cts6 = np.unique(cc2, return_counts=True)
        if cts6.max() / len(cc2) < 0.7:
            continue
        want = PALETTE[colour_idx[int(vals6[cts6.argmax()])]]
        if (np.array(ccol) == want).all():
            continue
        out[sl2][m] = want
        artifact_edits[sl2] |= m
        n_fix2 += 1
print("final sweep recoloured:", n_fix2)

declared = R1 | R2 | R3 | R4 | R5 | R6 | R7 | wiped | label_edits | artifact_edits

# mechanical colour-accuracy spot check on major countries
names_l = json.load(open("country-names.json"))
checks = ["Russia", "Canada", "United States of America", "Brazil", "China", "Australia", "India",
          "Mexico", "Argentina", "Kazakhstan", "Mongolia", "France", "Germany", "Egypt", "South Africa", "Indonesia",
          "Saudi Arabia", "Turkey", "Iran", "Nigeria", "Algeria", "Ethiopia", "Kenya", "Dem. Rep. Congo", "Sudan",
          "Libya", "Iraq", "Ukraine", "Poland", "Spain", "Sweden", "Norway", "Finland", "Vietnam", "Thailand",
          "Portugal", "Switzerland", "Austria", "Czechia", "Netherlands", "Belgium", "Chile", "Peru", "Bolivia",
          "Colombia", "Venezuela", "Paraguay", "Uruguay", "Ecuador", "Japan", "South Korea", "Morocco", "Ghana",
          "Cameroon", "Angola", "Tanzania", "Mozambique", "Zambia", "Zimbabwe", "Botswana", "Namibia", "Madagascar",
          "Somalia", "Mali", "Niger", "Chad", "Pakistan", "Afghanistan", "Myanmar", "Malaysia", "Philippines",
          "New Zealand", "Papua New Guinea", "Cuba", "Guatemala"]
spot = {}
for nm in checks:
    if nm not in names_l:
        continue
    ci = names_l.index(nm)
    mm = (cid == ci)
    if not mm.any():
        spot[nm] = "no NE pixels"
        continue
    cols = out[mm]
    keepc = np.array([tuple(int(v) for v in c) in pal_lookup for c in cols])
    if not keepc.any():
        spot[nm] = "unpainted"
        continue
    vals_c, cts_c = np.unique(cols[keepc], axis=0, return_counts=True)
    got = tuple(int(v) for v in vals_c[cts_c.argmax()])
    want = tuple(int(v) for v in PALETTE[colour_idx[ci]])
    spot[nm] = "ok" if got == want else f"got {got} want {want}"
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
