"""Assembly for the world-map recolour (ADR 0001/0002 discipline). v2

Reference  : native WorldTimeZone 12-hour GIF (source-locked; exact typography).
Render Pass: approved gpt-image-2 recolour (colours only).
Assembly   : deterministic composite; every changed pixel lies inside a
             declared region; fidelity fails if anything else changes.

Usage: python3 compose.py REFERENCE.gif RENDER.png OUT_DIR
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ref_path, render_path, out_dir = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
plates_path = Path(sys.argv[4]) if len(sys.argv) > 4 else None
out_dir.mkdir(parents=True, exist_ok=True)

g = np.asarray(Image.open(ref_path).convert("RGB")).astype(np.int16)
H, W = g.shape[:2]

def eq(*c):
    return (g == np.array(c, np.int16)).all(axis=2)

BLACK = eq(0x04, 0x02, 0x04)
NAVY = eq(0x04, 0x02, 0x34)
SHADOW = eq(0x34, 0x32, 0x34)
GREY = eq(0x64, 0x66, 0x64) | eq(0x6C, 0x6D, 0x6C)
GRID = eq(0xCC, 0xCE, 0xFC)
WHITE = eq(0xFC, 0xFE, 0xFC)
ORANGE = eq(0xFC, 0x66, 0x04)
DARK = BLACK | SHADOW | GREY | NAVY

PRIMARY = [(0x04, 0x9A, 0xFC), (0xFC, 0x32, 0x34), (0x04, 0xCE, 0x34), (0xFC, 0xCE, 0x34)]
PALE = [(0x04, 0xFE, 0x54), (0x04, 0xBE, 0x3C), (0x6C, 0xB6, 0xFC), (0xFC, 0x82, 0x84),
        (0xF7, 0x7C, 0x7C), (0x94, 0xF7, 0xC6), (0x9C, 0xFE, 0xCC), (0xCC, 0xFE, 0x9C),
        (0x34, 0xCE, 0xFC), (0xCC, 0xC6, 0xFC), (0xFC, 0xFE, 0x04), (0xFC, 0xFE, 0x34)]
FILLS = PRIMARY + PALE

prim = np.zeros((H, W), bool)
for c in PRIMARY:
    prim |= eq(*c)
fills = prim.copy()
for c in PALE:
    fills |= eq(*c)

# credit box (immutable)
mintm = eq(0x9C, 0xFE, 0xCC)
labm, nm = ndimage.label(mintm)
credit = np.zeros((H, W), bool)
if nm:
    sizes = ndimage.sum(mintm, labm, range(1, nm + 1))
    sl = ndimage.find_objects(labm)[int(np.argmax(sizes))]
    credit[max(0, sl[0].start - 4):sl[0].stop + 4, max(0, sl[1].start - 4):sl[1].stop + 4] = True

grid_x = np.where(GRID.sum(axis=0) > H * 0.25)[0]
grid_y = np.where(GRID.sum(axis=1) > W * 0.25)[0]

# ------------------------------------------------------------- R1: badge boxes
# a badge interior = a rectangular single-colour component whose bbox ring is
# mostly black/shadow. Both orientations; relaxed near the frame edges.
badge_boxes = []
R1 = np.zeros((H, W), bool)

def find_runs(mask, lo=28, hi=95):
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
                if y + dy not in runs.keys():
                    continue
                if any(abs(r[0] - s_) <= 4 and abs(r[1] - e_) <= 4 for r in runs[y + dy]):
                    boxes.append((y, y + dy + 1, s_, e_ + 1))
                    taken[y:y + dy + 1, s_:e_ + 1] = True
                    break
    out = []
    for (y0, y1, x0, x1) in boxes:
        out.append((x0, y0, x1, y1) if not transpose else (y0, x0, y1, x1))
    return out

for (x0, y0, x1, y1) in pair_boxes(BLACK) + pair_boxes(BLACK, transpose=True):
    if credit[y0:y1, x0:x1].any():
        continue
    inner_sl = (slice(y0 + 2, y1 - 2), slice(x0 + 2, x1 - 2))
    if g[inner_sl].size == 0:
        continue
    if DARK[inner_sl].mean() > 0.75:
        continue
    badge_boxes.append((int(x0), int(y0), int(x1), int(y1)))
    R1[max(0, y0 - 2):y1 + 4, max(0, x0 - 2):x1 + 4] = True

# externally localised plates (magenta marker mask), if provided
if plates_path is not None:
    pm = np.asarray(Image.open(plates_path).convert("L")) > 140
    pm = pm & ~credit
    R1 |= pm
    labpm, npm = ndimage.label(pm)
    for i, sl in enumerate(ndimage.find_objects(labpm), start=1):
        badge_boxes.append((int(sl[1].start), int(sl[0].start), int(sl[1].stop), int(sl[0].stop)))

# --------------------------------------------------------------- R2: DST tags
R2 = np.zeros((H, W), bool)
tag_count = 0
yellow = eq(0xFC, 0xFE, 0x04) | eq(0xFC, 0xFE, 0x34)
laby, ny = ndimage.label(ndimage.binary_dilation(yellow, iterations=1))
for i, sl in enumerate(ndimage.find_objects(laby), start=1):
    h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    dk = DARK[sl][laby[sl] == i].mean() if (laby[sl] == i).any() else 0
    if 4 <= h <= 24 and 8 <= w <= 52 and 0.04 <= dk <= 0.7:
        R2[max(0, sl[0].start - 1):sl[0].stop + 1, max(0, sl[1].start - 1):sl[1].stop + 1] = True
        tag_count += 1

# ----------------------------------------- R3: corner strips (dates, +1/-1, UTC)
strip = np.zeros((H, W), bool)
strip[H - 70:, :360] = True
strip[:80, :200] = True
strip[:80, W - 200:] = True
R3 = strip & (DARK | ORANGE | yellow) & ~credit & ~fills
R3 = ndimage.binary_dilation(R3, iterations=1) & strip & ~credit & ~fills

# ------------------------------------------------------------------ R4: orange
R4 = ndimage.binary_dilation(ORANGE, iterations=1) & ~credit

# --------------------------------------------- R5: Greenwich lines + caption
R5 = np.zeros((H, W), bool)
corridor = [x for x in range(W // 2 - 15, W // 2 + 16)
            if (BLACK[:, x].sum() > 0.25 * H)]
for x in corridor:
    col = BLACK[:, x]
    d = np.diff(np.r_[0, col.view(np.int8), 0])
    for a, b in zip(np.where(d == 1)[0], np.where(d == -1)[0]):
        if b - a >= 5:
            R5[a:b, x] = True
if corridor:
    lo, hi = min(corridor), max(corridor) + 1
    labt, nt = ndimage.label((BLACK | NAVY | GREY | SHADOW) & ~R1, structure=np.ones((3, 3)))
    for i, sl in enumerate(ndimage.find_objects(labt), start=1):
        if sl[1].start >= lo - 12 and sl[1].stop <= hi + 12:
            cnt = int((labt[sl] == i).sum())
            if cnt <= 320 and not fills[sl][labt[sl] == i].any():
                R5[sl] |= (labt[sl] == i)

# -------------------------------------------------- alignment (primaries only)
render = np.asarray(Image.open(render_path).convert("RGB").resize((W, H), Image.LANCZOS)).astype(np.int16)
def landmask_render(a):
    mx_, mn_ = a.max(axis=2), a.min(axis=2)
    sat_ = np.where(mx_ > 0, (mx_ - mn_) / np.maximum(mx_, 1), 0)
    return ndimage.binary_opening((sat_ > 0.3) & (mx_ > 90), iterations=1)
def boundary(m):
    return ndimage.binary_dilation(m & ~ndimage.binary_erosion(m), iterations=1)
sbd = boundary(ndimage.binary_opening(prim & ~R1, iterations=1))
cbd = boundary(landmask_render(render))
best = (0, 0, -1)
for dy in range(-18, 19):
    for dx in range(-30, 31):
        yy0, xx0 = max(0, dy), max(0, dx)
        yy1, xx1 = H + min(0, dy), W + min(0, dx)
        a = sbd[yy0:yy1, xx0:xx1]
        b = cbd[yy0 - dy:yy1 - dy, xx0 - dx:xx1 - dx]
        sc = int((a & b).sum())
        if sc > best[2]:
            best = (dx, dy, sc)
dx0, dy0, _ = best
yy, xx = np.mgrid[0:H, 0:W]
dxf = np.full((H, W), float(dx0))
dyf = np.full((H, W), float(dy0))
cx = [dx0, 0, 0]; cy = [dy0, 0, 0]; pts = [0]
warp = np.stack([ndimage.map_coordinates(render[..., k].astype(np.float32), [yy - dyf, xx - dxf], order=1, mode="nearest") for k in range(3)], axis=-1).clip(0, 255).astype(np.int16)
align_note = {"blocks": int(len(pts)), "dx": [round(float(v), 5) for v in cx], "dy": [round(float(v), 5) for v in cy],
              "overlap_before": int((sbd & cbd).sum()), "overlap_after": int((sbd & boundary(landmask_render(warp))).sum())}

# render dominant palette (int32)
mx, mn = warp.max(axis=2), warp.min(axis=2)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
rland = (sat > 0.22) & (mx > 90)
core = rland & ~ndimage.binary_dilation(warp.max(axis=2) < 70, iterations=2)
pal_img = Image.fromarray(warp[core].astype(np.uint8).reshape(-1, 1, 3)).quantize(colors=32, method=Image.Quantize.MEDIANCUT)
pal = np.array(pal_img.getpalette()[:96]).reshape(-1, 3)
counts = np.bincount(np.asarray(pal_img).ravel(), minlength=32)
dominant = []
for i in np.argsort(-counts):
    if counts[i] < core.sum() * 0.003:
        continue
    c_ = pal[i].astype(int)
    if c_.max() < 120 or (c_.max() - c_.min()) / max(1, c_.max()) < 0.3:
        continue
    if all(np.abs(c_ - d).sum() > 60 for d in dominant):
        dominant.append(c_)
dominant = np.array(dominant, dtype=np.int32)

# ------------------------------------------- R6: per-patch majority recolour
land = fills & ~R1 & ~R2 & ~credit
labp, npatch = ndimage.label(land)
R6 = np.zeros((H, W), bool)
patch_col = {}
snapped = np.full((H, W), -1, np.int16)
valid = rland
d_all = None
for i, sl in enumerate(ndimage.find_objects(labp), start=1):
    m = labp[sl] == i
    sample = warp[sl][m & valid[sl]]
    if len(sample) < max(4, 0.25 * m.sum()):
        continue                                   # keep original colour (tiny island / no signal)
    dd = ((sample[:, None, :].astype(np.int32) - dominant[None, :, :]) ** 2).sum(axis=2)
    lab = np.argmin(dd, axis=1)
    maj = np.bincount(lab, minlength=len(dominant)).argmax()
    if np.bincount(lab, minlength=len(dominant))[maj] / len(lab) < 0.4:
        continue
    patch_col[i] = maj
    R6[sl] |= m
for i, k in patch_col.items():
    pass  # applied below

# ---------------------------------------------------------- R7: grey zone lines
labz, nz = ndimage.label(GREY & ~R5, structure=np.ones((3, 3)))
keepz = np.zeros(nz + 1, bool)
for i, sl in enumerate(ndimage.find_objects(labz), start=1):
    h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    cnt = int((labz[sl] == i).sum())
    m2 = labz[sl] == i
    near_land_frac = float(ndimage.binary_dilation(fills, iterations=2)[sl][m2].mean())
    keepz[i] = (max(h, w) >= 40 and cnt <= 0.08 * h * w + 3 * max(h, w)) or (cnt <= 60 and near_land_frac >= 0.6)
R7 = keepz[labz] & ~R1 & ~R3 & ~credit

# ---------------------------------------------------------------- compose
out = g.copy()
declared = R1 | R2 | R3 | R4 | R5 | R6 | R7
wiped = (R1 | R2 | R3 | R4 | R5) & ~credit
out[wiped] = (0xFC, 0xFE, 0xFC)
gridmask = np.zeros((H, W), bool)
gridmask[:, grid_x] = True
gridmask[grid_y, :] = True
out[wiped & gridmask] = (0xCC, 0xCE, 0xFC)
for i, k in patch_col.items():
    sl = ndimage.find_objects(labp)[i - 1]
    m = labp[sl] == i
    out[sl][m] = dominant[k]
# grey lines: on/next to land -> patch colour; in ocean -> light grey
line_on_land = R7 & ndimage.binary_dilation(R6, iterations=1)
out[R7] = (0xB8, 0xB8, 0xB8)
if line_on_land.any():
    idx = ndimage.distance_transform_edt(~R6, return_distances=False, return_indices=True)
    dist = ndimage.distance_transform_edt(~R6)
    near = line_on_land & (dist <= 2)
    out[near] = out[idx[0][near], idx[1][near]]
# sliver cleanup: dark fragments of plate borders hugging the wiped mask
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
        gm = gridmask[sl]
        sub[m & gm] = (0xCC, 0xCE, 0xFC)
        wiped[sl][m] = True
        declared[sl][m] = True

# frame hammer: dark remnants hugging the plate mask are plate frames
if plates_path is not None:
    hug = ndimage.binary_dilation(R1, iterations=3) & (BLACK | SHADOW | GREY) & ~NAVY & ~credit
    far_land = fills & ~ndimage.binary_dilation(R1, iterations=4)
    keep_dark = ndimage.binary_dilation(far_land, iterations=1)
    kill = hug & ~keep_dark
    # plate-fill slivers at the mask edge: small fill components living inside the hammer zone
    fl = fills & ~R1 & ~credit
    labfl, nfl = ndimage.label(fl, structure=np.ones((3, 3)))
    szfl = ndimage.sum(fl, labfl, range(1, nfl + 1))
    inhug = ndimage.sum(ndimage.binary_dilation(R1, iterations=3), labfl, range(1, nfl + 1))
    tot = np.maximum(szfl, 1)
    sliver_ids = np.where((szfl <= 24) & (inhug / tot >= 0.9))[0] + 1
    kill |= np.isin(labfl, sliver_ids)
    out[kill] = (0xFC, 0xFE, 0xFC)
    out[kill & gridmask] = (0xCC, 0xCE, 0xFC)
    wiped |= kill
    declared |= kill

# render-informed reconstruction: what sat under a plate comes from the render
under = wiped & rland
if under.any():
    lp2 = warp[under].astype(np.int32)
    d2 = ((lp2[:, None, :] - dominant[None, :, :]) ** 2).sum(axis=2)
    out[under] = dominant[np.argmin(d2, axis=1)]
    # outline the reconstructed land where it meets background inside the wipe
    filled = np.zeros((H, W), bool)
    filled[under] = True
    # drop tiny reconstructed islands that touch no real land
    # mode-filter the reconstructed colours so plate areas read as solid patches
    for _ in range(2):
        landish = filled | R6
        votes = np.zeros((len(dominant), H, W), np.float32)
        for k, c in enumerate(dominant):
            iscol = (out == c).all(axis=2) & landish
            votes[k] = ndimage.uniform_filter(iscol.astype(np.float32), 7)
        best_k = votes.argmax(axis=0)
        strength = votes.max(axis=0)
        strong = filled & (strength > 0.35)
        weak = filled & (strength <= 0.35)
        out[strong] = dominant[best_k[strong]]
        out[weak] = (0xFC, 0xFE, 0xFC)
        out[weak & gridmask] = (0xCC, 0xCE, 0xFC)
        filled &= ~weak
    labu, nu = ndimage.label(filled, structure=np.ones((3, 3)))
    szu = ndimage.sum(filled, labu, range(1, nu + 1))
    touch = ndimage.sum(ndimage.binary_dilation(fills, iterations=1), labu, range(1, nu + 1))
    drop = np.isin(labu, np.where((szu < 20) & (touch == 0))[0] + 1)
    out[drop] = (0xFC, 0xFE, 0xFC)
    out[drop & gridmask] = (0xCC, 0xCE, 0xFC)
    filled &= ~drop
    edge_px = filled & ~ndimage.binary_erosion(filled | fills | BLACK, iterations=1)
    out[edge_px & wiped] = (0x04, 0x02, 0x04)

# per-plate context fill: a plate whose surround is land gets land colour
src_ok = R6 & ~wiped
idx = ndimage.distance_transform_edt(~src_ok, return_distances=False, return_indices=True)
for (x0, y0, x1, y1) in badge_boxes:
    ry0, ry1, rx0, rx1 = max(0, y0 - 3), min(H, y1 + 3), max(0, x0 - 3), min(W, x1 + 3)
    ring = np.zeros((H, W), bool)
    ring[ry0:ry1, rx0:rx1] = True
    ring[y0:y1, x0:x1] = False
    frac_land = (ring & fills).sum() / max(1, ring.sum())
    if frac_land >= 0.45:
        box = np.zeros((H, W), bool)
        box[max(0, y0 - 2):y1 + 4, max(0, x0 - 2):x1 + 4] = True
        box &= wiped
        ringpix = out[ring & fills]
        dd = ((ringpix[:, None, :].astype(np.int32) - dominant[None, :, :]) ** 2).sum(axis=2)
        maj = np.bincount(dd.argmin(axis=1), minlength=len(dominant)).argmax()
        out[box] = dominant[maj]

# restore reference label pixels the plate mask overlapped
if plates_path is not None:
    pmask = R1
    # city labels (navy) always restored
    nav = NAVY & pmask
    out[nav] = (0x04, 0x02, 0x34)
    # black glyphs restored when their component is only partially covered
    lab_b, n_b = ndimage.label(BLACK, structure=np.ones((3, 3)))
    total = ndimage.sum(BLACK, lab_b, range(1, n_b + 1))
    inside = ndimage.sum(pmask, lab_b, range(1, n_b + 1))
    frac = inside / np.maximum(total, 1)
    objs_b = ndimage.find_objects(lab_b)
    letter = np.zeros(n_b + 1, bool)
    for j in range(n_b):
        bs = objs_b[j]
        bh, bw = bs[0].stop - bs[0].start, bs[1].stop - bs[1].start
        letter[j + 1] = total[j] <= 60 and bh <= 14 and bw <= 14
    # words: cluster letters (and navy) horizontally; restore a word only if NO member is mostly covered
    letters_mask = letter[lab_b] | NAVY
    wlab, wn = ndimage.label(ndimage.binary_dilation(letters_mask, structure=np.ones((3, 9))))
    rest = np.zeros((H, W), bool)
    for wi, wsl in enumerate(ndimage.find_objects(wlab), start=1):
        wm = (wlab[wsl] == wi)
        ids = np.unique(lab_b[wsl][wm & BLACK[wsl]])
        ids = ids[ids > 0]
        if len(ids) and (frac[ids - 1] >= 0.45).any():
            gone = wm & letters_mask[wsl] & np.isin(lab_b[wsl], ids) & ~R1[wsl]
            sub = out[wsl]
            sub[gone] = (0xFC, 0xFE, 0xFC)
            sub[gone & gridmask[wsl]] = (0xCC, 0xCE, 0xFC)
            declared[wsl] |= gone
            continue                      # word mostly eaten: drop it entirely
        rest[wsl] |= wm & letters_mask[wsl] & pmask[wsl]
    out[rest & BLACK] = (0x04, 0x02, 0x04)
    out[rest & NAVY] = (0x04, 0x02, 0x34)
    # navy outside pmask stays as drawn (unchanged); nothing else restored

# interior dashed zone boundaries: tiny black dashes fully inside one country
labd, ndc = ndimage.label(BLACK & ~R1 & ~credit, structure=np.ones((3, 3)))
szd = ndimage.sum(np.ones_like(labd), labd, range(1, ndc + 1))
for i in np.where(szd <= 10)[0] + 1:
    sl = ndimage.find_objects(labd == i)[0]
    sl2 = tuple(slice(max(0, a.start - 2), a.stop + 2) for a in sl)
    m = labd[sl2] == i
    ring = ndimage.binary_dilation(m, iterations=1) & ~m
    ringcols = out[sl2][ring]
    landish = np.array([tuple(c) in {tuple(d) for d in dominant} for c in ringcols])
    if len(ringcols) and landish.mean() >= 0.85:
        vals, cts = np.unique(ringcols[landish], axis=0, return_counts=True)
        out[sl2][m] = vals[cts.argmax()]
        declared[sl2][m] = True

# ---------------------------------------------------------------- fidelity
changed = (out != g).any(axis=2)
outside = changed & ~declared
report = {
    "reference": {"file": ref_path.name, "sha256": hashlib.sha256(ref_path.read_bytes()).hexdigest(), "size": [int(W), int(H)]},
    "render": {"file": render_path.name, "sha256": hashlib.sha256(render_path.read_bytes()).hexdigest()},
    "alignment": align_note,
    "declared_pixels": int(declared.sum()),
    "changed_pixels": int(changed.sum()),
    "outside_changed": int(outside.sum()),
    "passed": bool(outside.sum() == 0),
    "regions": {"R1_badges": len(badge_boxes), "R2_tags": tag_count, "R3": int(R3.sum()), "R4": int(R4.sum()),
                "R5": int(R5.sum()), "R6_patches": len(patch_col), "R6_pixels": int(R6.sum()), "R7": int(R7.sum())},
    "palette": ["#%02x%02x%02x" % tuple(c) for c in dominant],
}
Image.fromarray(out.astype(np.uint8)).save(out_dir / "assembled.png")
Image.fromarray(out.astype(np.uint8)).resize((W * 2, H * 2), Image.NEAREST).save(out_dir / "assembled-2x.png")
(out_dir / "fidelity-report.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({k: report[k] for k in ("alignment", "declared_pixels", "outside_changed", "passed")}))
print("badges:", len(badge_boxes), "tags:", tag_count, "patches recoloured:", len(patch_col), "palette:", report["palette"])
if not report["passed"]:
    raise SystemExit("FIDELITY FAILED")
