"""compose_v4 — recolour-only, source-frame-native (spec #147, architecture #143).

Rules:
  * Output starts as the source. A pixel may only be (a) recoloured in place, or
    (b) annotation-wiped and filled from the nearest non-wiped FLAT source-frame
    neighbour. No pixel is ever drawn from the projected country grid.
  * The registered NE grid (countries-registered.npy, #146) VOTES a country per
    source patch; it never paints. Per-pixel colour splits (no strokes) only for
    strongly mixed patches outside the #146 exclusion zones.
  * Colours come exclusively from assembly/pinned-country-colours.json (#145).

Usage: python3 compose_v4.py SOURCE.gif OUT_DIR
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

src_p, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)
S = np.asarray(Image.open(src_p).convert("RGB")).astype(np.int16)
H, W = S.shape[:2]
O = S.copy()

def eq(*c):
    return (S == np.array(c, np.int16)).all(axis=2)

BLACK = eq(0x04, 0x02, 0x04)
NAVY = eq(0x04, 0x02, 0x34)
SHADOW = eq(0x34, 0x32, 0x34)
GREY = eq(0x64, 0x66, 0x64) | eq(0x6C, 0x6D, 0x6C) | eq(0x5C, 0x5E, 0x5C) | eq(0x5C, 0x5A, 0x5C)
GRID = eq(0xCC, 0xCE, 0xFC)
WHITE = eq(0xFC, 0xFE, 0xFC)
ORANGE = eq(0xFC, 0x66, 0x04)
YELLOW = eq(0xFC, 0xFE, 0x04) | eq(0xFC, 0xFE, 0x34) | eq(0xFC, 0xCE, 0x04) | eq(0xF4, 0xC3, 0x04)
GWLINE = eq(0x64, 0x66, 0x9C)
DARK = BLACK | SHADOW | GREY | NAVY
FILLS = [(0x04, 0x9A, 0xFC), (0xFC, 0x32, 0x34), (0x04, 0xCE, 0x34), (0xFC, 0xCE, 0x34), (0x04, 0xFE, 0x54),
         (0x04, 0xBE, 0x3C), (0x6C, 0xB6, 0xFC), (0xFC, 0x82, 0x84), (0xF7, 0x7C, 0x7C), (0x94, 0xF7, 0xC6),
         (0xCC, 0xFE, 0x9C), (0x34, 0xCE, 0xFC), (0xCC, 0xC6, 0xFC), (0x9C, 0xFE, 0xCC)]
fills = np.zeros((H, W), bool)
for c in FILLS:
    fills |= eq(*c)

# credit box (kept verbatim)
mintm = eq(0x9C, 0xFE, 0xCC)
labm, nm = ndimage.label(mintm)
credit = np.zeros((H, W), bool)
if nm:
    szm = ndimage.sum(mintm, labm, range(1, nm + 1))
    sl = ndimage.find_objects(labm)[int(np.argmax(szm))]
    credit[max(0, sl[0].start - 4):sl[0].stop + 4, max(0, sl[1].start - 4):sl[1].stop + 4] = True

gridmask = np.zeros((H, W), bool)
gridmask[:, np.where(GRID.sum(axis=0) > H * 0.25)[0]] = True
gridmask[np.where(GRID.sum(axis=1) > W * 0.25)[0], :] = True

# ---------------------------------------------------------------- inputs
regcid = np.load("countries-registered.npy").astype(np.int32)
names = json.load(open("country-names.json"))
pinned = json.load(open("pinned-country-colours.json"))["assignments"]
def hex2rgb(h):
    return np.array([int(h[1:3], 16), int(h[3:5], 16), int(h[5:7], 16)], np.int16)
colour_of = np.zeros((len(names), 3), np.int16)
for i, n in enumerate(names):
    colour_of[i] = hex2rgb(pinned[n])
dist_idx = ndimage.distance_transform_edt(regcid < 0, return_distances=True, return_indices=True)
cid_near, cid_dist = regcid[dist_idx[1][0], dist_idx[1][1]], dist_idx[0]

# #146 patch-vote-only zones (no per-pixel splitting there)
noSplit = np.zeros((H, W), bool)
noSplit[:40, :] = True                     # Arctic fringe
noSplit[40:80, 330:470] = True             # north Greenland
noSplit[370:, 900:] = True                 # New Zealand / far Pacific
noSplit[:, :30] = True
noSplit[:, W - 30:] = True

# ------------------------------------------------- annotation detection (from v3)
dark_bs = BLACK | SHADOW

def colon_seeds(d):
    seeds = []
    for y in range(6, d.shape[0] - 10):
        for x in np.where(d[y])[0]:
            if x < 6 or x >= d.shape[1] - 6:
                continue
            if d[y + 1, x] and not d[y + 2, x] and not d[y + 3, x] and d[y + 4, x] and d[y + 5, x] \
               and not d[y - 1, x] and not d[y - 2, x] and not d[y + 6, x]:
                seeds.append((x, y))
    return seeds

def box_from_colon(x, y, transpose=False):
    d = dark_bs.T if transpose else dark_bs
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
    x0 = min(top[1][0], bot[1][0]); x1 = max(top[1][1], bot[1][1])
    if transpose:
        return (top[0], x0, bot[0] + 1, x1 + 1)
    return (x0, top[0], x1 + 1, bot[0] + 1)

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

def pair_boxes(mask, transpose=False, hi=140):
    m = mask.T if transpose else mask
    runs = find_runs(m, hi=hi)
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

badge_boxes = []
for (x, y) in colon_seeds(dark_bs):
    b = box_from_colon(x, y)
    if b:
        badge_boxes.append(b)
for (yv, xv) in colon_seeds(dark_bs.T):
    b = box_from_colon(yv, xv, transpose=True)
    if b:
        badge_boxes.append(b)
copies = [q for q in (Path("wtz-map-second.gif"), Path("wtz-map-third.gif")) if q.exists()]
diff = np.zeros((H, W), bool)
if copies:
    for q in copies:
        b2 = np.asarray(Image.open(q).convert("RGB")).astype(np.int16)
        diff |= (S != b2).any(axis=2)
    dd = ndimage.binary_opening(diff, structure=np.ones((2, 2)))
    labD, nD = ndimage.label(ndimage.binary_dilation(dd, iterations=3))
    for i, sl in enumerate(ndimage.find_objects(labD), start=1):
        h_, w_ = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        if h_ <= 26 and w_ <= 110 and float(diff[sl].mean()) >= 0.08:
            f_top = any(dark_bs[yy_, sl[1].start:sl[1].stop].mean() >= 0.55
                        for yy_ in range(max(0, sl[0].start - 3), min(H, sl[0].start + 3)))
            f_bot = any(dark_bs[yy_, sl[1].start:sl[1].stop].mean() >= 0.55
                        for yy_ in range(max(0, sl[0].stop - 3), min(H, sl[0].stop + 3)))
            dens_ = float(diff[sl].mean())
            if int(SHADOW[sl].sum()) >= 6 or (f_top and f_bot) or ((f_top or f_bot) and dens_ >= 0.22):
                badge_boxes.append((sl[1].start, sl[0].start, sl[1].stop, sl[0].stop))
badge_boxes += pair_boxes(BLACK) + pair_boxes(BLACK, transpose=True, hi=220)
dedup = []
for b in badge_boxes:
    if not any(abs(b[0] - o[0]) <= 3 and abs(b[1] - o[1]) <= 3 for o in dedup):
        dedup.append(b)
grown = []
for (x0, y0, x1, y1) in dedup:
    for _ in range(6):
        g = False
        if y0 > 0 and dark_bs[y0 - 1, max(0, x0):x1].mean() > 0.75:
            y0 -= 1; g = True
        if y1 < H and dark_bs[min(H - 1, y1), max(0, x0):x1].mean() > 0.75:
            y1 += 1; g = True
        if x0 > 0 and dark_bs[max(0, y0):y1, x0 - 1].mean() > 0.75:
            x0 -= 1; g = True
        if x1 < W and dark_bs[max(0, y0):y1, min(W - 1, x1)].mean() > 0.75:
            x1 += 1; g = True
        if not g:
            break
    grown.append((int(x0), int(y0), int(x1), int(y1)))
R1 = np.zeros((H, W), bool)
for (x0, y0, x1, y1) in grown:
    if not credit[max(0, y0):y1, max(0, x0):x1].any():
        R1[max(0, y0 - 1):y1 + 1, max(0, x0 - 1):x1 + 1] = True

R2 = np.zeros((H, W), bool)
laby, ny = ndimage.label(ndimage.binary_dilation(YELLOW, iterations=1))
for i, sl in enumerate(ndimage.find_objects(laby), start=1):
    h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    dk = DARK[sl][laby[sl] == i].mean() if (laby[sl] == i).any() else 0
    if 4 <= h <= 30 and 6 <= w <= 56 and 0.03 <= dk <= 0.92:
        R2[max(0, sl[0].start - 1):sl[0].stop + 1, max(0, sl[1].start - 1):sl[1].stop + 1] = True

strip = np.zeros((H, W), bool)
strip[H - 70:, :360] = True
strip[:80, :200] = True
strip[:80, W - 200:] = True
R3 = strip & ~WHITE & ~GRID & ~credit & ~fills

R4 = ndimage.binary_dilation(ORANGE, iterations=1) & ~credit

colsum_gw = GWLINE.sum(axis=0)
gwcols = np.where(colsum_gw >= 80)[0]
gwcols = gwcols[np.abs(gwcols - W // 2) <= 20]
R5 = GWLINE & ~credit
if len(gwcols):
    xlo, xhi = int(gwcols.min()) - 4, int(gwcols.max()) + 5
    for x in range(max(0, xlo), min(W, xhi)):
        colm = BLACK[:, x] | GWLINE[:, x]
        dcol = np.diff(np.r_[0, colm.view(np.int8), 0])
        for a, b in zip(np.where(dcol == 1)[0], np.where(dcol == -1)[0]):
            if b - a >= 4:
                R5[a:b, x] = True
    gwband = ndimage.binary_dilation(GWLINE & (np.abs(np.arange(W) - W // 2) <= 20)[None, :],
                                     structure=np.ones((1, 9))) & (WHITE | GRID)
    R5 |= gwband & ~credit
    corr = np.zeros((H, W), bool)
    corr[:, max(0, int(gwcols.min()) - 14):min(W, int(gwcols.max()) + 15)] = True
    labt, nt = ndimage.label((BLACK | GREY | SHADOW) & corr & ~R1, structure=np.ones((3, 3)))  # NAVY = city labels, never caption
    for i, sl in enumerate(ndimage.find_objects(labt), start=1):
        m = labt[sl] == i
        deep = sl[0].start >= 340
        if int(m.sum()) <= 320 and (deep or not fills[sl][m].any()):
            R5[sl] |= m

# marker rectangles: small rectangular fill patches framed in black, ringed by sea
labf, nf = ndimage.label(fills)
for i, sl in enumerate(ndimage.find_objects(labf), start=1):
    m = labf[sl] == i
    cnt = int(m.sum())
    hh, ww2 = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    if not (20 <= cnt <= 400):
        continue
    tall = hh >= 1.6 * ww2 and m[:, 0].sum() >= 0.9 * hh and m[:, -1].sum() >= 0.9 * hh
    if cnt < (0.55 if tall else 0.8) * hh * ww2:
        continue
    flatb = m[0, :].sum() >= 0.9 * ww2 and m[-1, :].sum() >= 0.9 * ww2
    if not (tall or flatb):
        continue          # true marker boxes have dead-straight edges
    sl2 = tuple(slice(max(0, a.start - 3), a.stop + 3) for a in sl)
    m2 = np.zeros((sl2[0].stop - sl2[0].start, sl2[1].stop - sl2[1].start), bool)
    m2[sl[0].start - sl2[0].start:sl[0].stop - sl2[0].start,
       sl[1].start - sl2[1].start:sl[1].stop - sl2[1].start] = m
    ring1 = ndimage.binary_dilation(m2, iterations=1) & ~m2
    ring3 = ndimage.binary_dilation(m2, iterations=3) & ~ndimage.binary_dilation(m2, iterations=2)
    frame_frac = float((BLACK | SHADOW | GREY | NAVY)[sl2][ring1].mean())
    sea_frac = float((WHITE | GRID)[sl2][ring3].mean())
    if frame_frac >= 0.5 and sea_frac >= (0.35 if tall else 0.6):
        R1[sl2[0].start:sl2[0].stop, sl2[1].start:sl2[1].stop] |= ndimage.binary_dilation(m2, iterations=2)

wiped = (R1 | R2 | R3 | R4 | R5) & ~credit
wiped |= SHADOW & ~credit
# a glyph that lives mostly OUTSIDE the boxes is a map label clipped by padding: spare it
labG, nG = ndimage.label((BLACK | NAVY) & ~R3, structure=np.ones((3, 3)))
szG = ndimage.sum((BLACK | NAVY) & ~R3, labG, range(1, nG + 1))
inG = ndimage.mean(wiped.astype(np.float32), labG, range(1, nG + 1))
spare = np.zeros(nG + 1, bool)
spare[1:] = (szG <= 80) & (inG > 0) & (inG < 0.8)
wiped &= ~spare[labG]
labN, nN = ndimage.label(NAVY, structure=np.ones((3, 3)))
szN = ndimage.sum(NAVY, labN, range(1, nN + 1))
spareN = np.zeros(nN + 1, bool)
spareN[1:] = szN <= 120
wiped &= ~(spareN[labN] & NAVY)      # city labels are navy; annotations never are
diff_d3 = ndimage.binary_dilation(diff, iterations=3) if copies else np.zeros((H, W), bool)
annotish = R2 | R3 | R5 | ndimage.binary_dilation(SHADOW, iterations=2)
labB3, nB3 = ndimage.label(BLACK, structure=np.ones((3, 3)))
szB3 = ndimage.sum(BLACK, labB3, range(1, nB3 + 1))
difB3 = ndimage.mean(diff_d3.astype(np.float32), labB3, range(1, nB3 + 1))
annB3 = ndimage.mean(annotish.astype(np.float32), labB3, range(1, nB3 + 1))
spareB = np.zeros(nB3 + 1, bool)
inW3 = ndimage.mean(wiped.astype(np.float32), labB3, range(1, nB3 + 1))
spareB[1:] = (szB3 <= 80) & (difB3 == 0.0) & (annB3 < 0.3) & (inW3 < 0.85)
wiped &= ~(spareB[labB3] & BLACK)    # black glyphs with no changing digits nearby are labels

# ---------------------------------------------------------------- recolour
labp, npatch = ndimage.label(fills)
objs = ndimage.find_objects(labp)
recol = 0
splits = 0
for i in range(1, npatch + 1):
    sl = objs[i - 1]
    m = labp[sl] == i
    ids = regcid[sl][m]
    good = ids[ids >= 0]
    if len(good) < max(3, 0.25 * m.sum()):
        near = cid_near[sl][m]
        dst = cid_dist[sl][m]
        good = near[(near >= 0) & (dst <= 12)]
        if not len(good):
            continue                       # unassigned: keep source colours
    vals, cts = np.unique(good, return_counts=True)
    order = np.argsort(-cts)
    major = int(vals[order[0]])
    in_nosplit = bool(noSplit[sl][m].any())
    second_big = len(vals) >= 2 and cts[order[1]] >= max(25, 0.15 * m.sum())
    if second_big and not in_nosplit:
        cand = vals[cts >= max(20, 0.08 * cts.sum())]
        dmin = np.full(m.shape, 1e18)
        use = np.full(m.shape, -1, np.int32)
        for cv in cand:
            seed = (regcid[sl] == cv) & m
            if not seed.any():
                continue
            ddm = ndimage.distance_transform_edt(~seed)
            upd = ddm < dmin
            dmin[upd] = ddm[upd]
            use[upd] = int(cv)
        use[~m | (use < 0)] = major
        sub = O[sl]
        yy, xx = np.where(m)
        sub[yy, xx] = colour_of[use[yy, xx]]
        splits += 1
    else:
        O[sl][m] = colour_of[major]
    recol += 1

# white-filled countries: enclosed white cells that the registered grid calls land
cells = (WHITE | GRID) & ~ndimage.binary_dilation(BLACK | NAVY | SHADOW, iterations=1)
labC, nC = ndimage.label(cells)
edge_ids = set(np.unique(np.r_[labC[0, :], labC[-1, :], labC[:, 0], labC[:, -1]]).tolist())
landfrac = ndimage.mean((regcid >= 0).astype(np.float32), labC, range(1, nC + 1))
sizes = ndimage.sum(cells, labC, range(1, nC + 1))
white_cells = 0
inR1frac = ndimage.mean(wiped.astype(np.float32), labC, range(1, nC + 1))
for i in range(1, 0):  # DISABLED for v1: recolouring white countries changes source land topology (A6); owner option on #147
    if i in edge_ids or sizes[i - 1] < 30 or landfrac[i - 1] < 0.85 or inR1frac[i - 1] > 0.3:
        continue
    m = labC == i
    grow = m.copy()
    for _ in range(2):
        grow |= ndimage.binary_dilation(grow) & (WHITE | GRID) & (regcid >= 0)
    ids = regcid[grow]
    good = ids[ids >= 0]
    vals, cts = np.unique(good, return_counts=True)
    yy, xx = np.where(grow & ~credit & ~strip)
    O[yy, xx] = colour_of[int(vals[cts.argmax()])]
    white_cells += 1

# lighten grey zone-joint lines in place (owner's original ask)
O[GREY & ~credit & ~strip] = (0xB8, 0xB8, 0xB8)

# ---------------------------------------------------------------- context fill
donor_land = fills & ~wiped                     # post-recolour palette pixels, source frame
donor_bg = (WHITE | GRID) & ~wiped
dl = ndimage.distance_transform_edt(~donor_land, return_distances=True, return_indices=True)
db = ndimage.distance_transform_edt(~donor_bg)
wy, wx = np.where(wiped)
dz = dl[0][wy, wx] - db[wy, wx]
is_land = np.where(np.abs(dz) > 8, dz < 0, regcid[wy, wx] >= 0)   # grid votes only in ambiguity (#143)
ly, lx = wy[is_land], wx[is_land]
O[ly, lx] = O[dl[1][0][ly, lx], dl[1][1][ly, lx]]
sy, sx = wy[~is_land], wx[~is_land]
O[sy, sx] = (0xFC, 0xFE, 0xFC)
# stranded texture/blend pixels on recoloured land take the neighbour patch colour
known = fills | WHITE | GRID | BLACK | NAVY | GREY | SHADOW | GWLINE | ORANGE
luma_S = 0.299 * S[..., 0] + 0.587 * S[..., 1] + 0.114 * S[..., 2]
odd = ((~known & (luma_S >= 90)) | YELLOW) & ~wiped & ~credit & ~ndimage.binary_dilation(GREY, iterations=1)
# grey-line anti-aliasing lightens with its line instead
grey_aa = (~known & (luma_S >= 90)) & ~wiped & ~credit & ndimage.binary_dilation(GREY, iterations=1)
O[grey_aa] = (0xB8, 0xB8, 0xB8)
dy2, dx2 = np.where(odd & (dl[0] <= 3))
O[dy2, dx2] = O[dl[1][0][dy2, dx2], dl[1][1][dy2, dx2]]

# restore lat/long grid through wiped areas where the fill came out white
wnow = (O == np.array((0xFC, 0xFE, 0xFC), np.int16)).all(axis=2)
gg = wiped & gridmask & wnow
O[gg] = (0xCC, 0xCE, 0xFC)

Image.fromarray(O.astype(np.uint8)).save(out_dir / "assembled-v4.png")
Image.fromarray(O.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(out_dir / "assembled-v4-2x.png")
manifest = {"composer": "compose_v4 recolour-only (spec #147)", "patches_recoloured": recol,
            "per_pixel_splits": splits, "white_cells_recoloured": white_cells,
            "plates_detected": len(grown), "wiped_px": int(wiped.sum()),
            "inputs": ["countries-registered.npy (#146)", "pinned-country-colours.json (#145)"]}
(out_dir / "manifest-v4.json").write_text(json.dumps(manifest, indent=2) + "\n")
print(json.dumps(manifest))
