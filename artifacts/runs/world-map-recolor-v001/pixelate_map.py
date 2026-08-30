"""Deterministic pixelate/assembly: generated candidate -> flat 1x pixel map.

Usage: python3 pixelate_map.py CANDIDATE.png SOURCE_16x9_FULL.png OUT_PREFIX [--no-labels]

Output grid = the source screenshot at exactly half size (its native GIF pixel
grid). The candidate is first un-warped onto the source geometry with a
block-wise displacement field (image models redraw maps with small local
distortions). Land colours come from the un-warped candidate (snapped to its
dominant flat colours, fringes and specks removed); outlines from the
candidate (hard black); background, lavender grid, lightened zone lines,
frame, blue bar, credit box and every city label come pixel-exact from the
source. Badge digits are never copied (they sit inside a black-bordered box).
"""

import sys
import numpy as np
from PIL import Image
from scipy import ndimage

cand_path, src_path, out = sys.argv[1], sys.argv[2], sys.argv[3]
with_labels = "--no-labels" not in sys.argv

src_full = Image.open(src_path).convert("RGB")
W, H = src_full.width // 2, src_full.height // 2               # native 1x grid
src = np.asarray(src_full.resize((W, H), Image.NEAREST)).astype(np.int16)
cand0 = np.asarray(Image.open(cand_path).convert("RGB").resize((W, H), Image.LANCZOS)).astype(np.int16)

# ------------------------------------------------ block-wise un-warp (land boundaries, affine fit)
def landmask(a):
    mx_, mn_ = a.max(axis=2), a.min(axis=2)
    sat_ = np.where(mx_ > 0, (mx_ - mn_) / np.maximum(mx_, 1), 0)
    return ndimage.binary_opening((sat_ > 0.3) & (mx_ > 90), iterations=1)
def boundary(m):
    return ndimage.binary_dilation(m & ~ndimage.binary_erosion(m), iterations=1)
sbd, cbd = boundary(landmask(src)), boundary(landmask(cand0))
M = 40
sbd[:M, :] = sbd[-M:, :] = False; sbd[:, :M] = sbd[:, -M:] = False
B, R = 160, 24
ny, nx = int(np.ceil(H / B)), int(np.ceil(W / B))
pts = []                                                       # (x, y, dx, dy, weight)
for by in range(ny):
    for bx in range(nx):
        ys, xs = slice(by * B, min(H, (by + 1) * B)), slice(bx * B, min(W, (bx + 1) * B))
        a = sbd[ys, xs]
        if a.sum() < 150:
            continue
        y0, x0 = ys.start, xs.start
        best = (0, 0, -1)
        for dy in range(-R, R + 1):
            for dx in range(-R, R + 1):
                yy, xx = slice(y0 - dy, y0 - dy + a.shape[0]), slice(x0 - dx, x0 - dx + a.shape[1])
                if yy.start < 0 or xx.start < 0 or yy.stop > H or xx.stop > W:
                    continue
                sc = int((a & cbd[yy, xx]).sum())
                if sc > best[2]:
                    best = (dx, dy, sc)
        ratio = best[2] / a.sum()
        if ratio >= 0.35:
            pts.append((x0 + a.shape[1] / 2, y0 + a.shape[0] / 2, best[0], best[1], ratio))
pts = np.array(pts)
A = np.stack([np.ones(len(pts)), pts[:, 0], pts[:, 1]], axis=1) * pts[:, 4:5]
cx_, cy_ = np.linalg.lstsq(A, pts[:, 2] * pts[:, 4], rcond=None)[0], np.linalg.lstsq(A, pts[:, 3] * pts[:, 4], rcond=None)[0]
yy, xx = np.mgrid[0:H, 0:W]
dxf = cx_[0] + cx_[1] * xx + cx_[2] * yy
dyf = cy_[0] + cy_[1] * xx + cy_[2] * yy
print(f"un-warp: {len(pts)} blocks used; dx = {cx_[0]:.2f} + {cx_[1]:.5f}x + {cx_[2]:.5f}y ; dy = {cy_[0]:.2f} + {cy_[1]:.5f}x + {cy_[2]:.5f}y")
cand = np.stack([ndimage.map_coordinates(cand0[..., c].astype(np.float32), [yy - dyf, xx - dxf], order=1, mode="nearest") for c in range(3)], axis=-1)
cand = np.clip(cand, 0, 255).astype(np.int16)
print("land-boundary overlap before/after un-warp:", int((sbd & cbd).sum()), int((sbd & boundary(landmask(cand))).sum()))

# ------------------------------------------------ candidate classes
mx, mn = cand.max(axis=2), cand.min(axis=2)
sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
black = mx < 70
land = (sat > 0.22) & (mx > 90) & ~black
near_black = ndimage.binary_dilation(black, iterations=2)
core = land & ~near_black
land_pixels = cand[core].astype(np.uint8)
pal_img = Image.fromarray(land_pixels.reshape(-1, 1, 3)).quantize(colors=32, method=Image.Quantize.MEDIANCUT)
pal = np.array(pal_img.getpalette()[: 32 * 3]).reshape(-1, 3)
counts = np.bincount(np.asarray(pal_img).ravel(), minlength=32)
dominant = []
for i in np.argsort(-counts):
    if counts[i] < core.sum() * 0.002:
        continue
    c = pal[i]
    if all(np.abs(c - d).sum() > 60 for d in dominant):
        dominant.append(c)
dominant = np.array(dominant, dtype=np.int32)
print("dominant land colours:", len(dominant), ["#%02x%02x%02x" % tuple(c) for c in dominant])
lp = cand[land].astype(np.int32)
d = ((lp[:, None, :] - dominant[None, :, :]) ** 2).sum(axis=2)
labels = np.full((H, W), -1, dtype=np.int16)
labels[land] = np.argmin(d, axis=1)

# fringe / speck cleanup: small same-colour components surrounded by another land colour take that colour
K = len(dominant)
for _ in range(2):
    for k in range(K):
        comp, n = ndimage.label(labels == k)
        if n == 0:
            continue
        sizes = ndimage.sum(np.ones_like(comp), comp, range(1, n + 1))
        small_ids = np.where(sizes < 40)[0] + 1
        if len(small_ids) == 0:
            continue
        for i in small_ids:
            sl = ndimage.find_objects(comp == i)[0]
            sl2 = tuple(slice(max(0, s.start - 3), s.stop + 3) for s in sl)
            m = comp[sl2] == i
            r = ndimage.binary_dilation(m, iterations=2) & ~m & (labels[sl2] >= 0)
            if r.sum() == 0:
                continue
            vals = labels[sl2][r]
            maj = np.bincount(vals, minlength=K).argmax()
            if maj != k and (vals == maj).mean() > 0.6:
                labels[sl2][m] = maj

# ------------------------------------------------ source classes
sr, sg, sb = src[..., 0], src[..., 1], src[..., 2]
grid = (sb > 225) & (sr > 185) & (sr < 240) & (np.abs(sr - sg) < 12) & (sb - sr > 12)
full = np.asarray(src_full).astype(np.int16)
grey = (np.abs(full - np.array([0x8B, 0x8C, 0x8A])) <= 10).all(axis=2)
lab, n = ndimage.label(grey, structure=np.ones((3, 3)))
keep = np.zeros(n + 1, dtype=bool)
for i, sl in enumerate(ndimage.find_objects(lab), start=1):
    hgt, wid = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
    cnt = int((lab[sl] == i).sum())
    keep[i] = max(hgt, wid) >= 60 and cnt <= 0.06 * hgt * wid + 3 * max(hgt, wid)
grey = keep[lab]
zone = np.asarray(Image.fromarray((grey * 255).astype(np.uint8)).resize((W, H), Image.BOX)) > 90
edge = np.zeros((H, W), dtype=bool); edge[:60, :] = edge[-60:, :] = True; edge[:, :60] = edge[:, -60:] = True
frame_black = edge & (src.sum(axis=2) < 150)
frame_blue = edge & (sb > 200) & (sr < 120)

# ------------------------------------------------ compose
outimg = np.full((H, W, 3), 255, dtype=np.uint8)
outimg[grid] = (0xD9, 0xDA, 0xFF)
outimg[zone] = (0xB8, 0xB8, 0xB8)
for k, c in enumerate(dominant):
    outimg[labels == k] = c
outimg[black & ~edge] = (0, 0, 0)
outimg[frame_black] = (0, 0, 0)
outimg[frame_blue] = src[frame_blue].astype(np.uint8)

mint = (np.abs(src - np.array([0x70, 0xF8, 0xC0])) <= 40).all(axis=2)
mint[: H // 2, :] = False; mint[:, W // 2:] = False
lab2, n2 = ndimage.label(mint)
if n2:
    sizes = ndimage.sum(mint, lab2, range(1, n2 + 1)); big = int(np.argmax(sizes)) + 1
    sl = ndimage.find_objects(lab2)[big - 1]
    y0, y1, x0, x1 = sl[0].start - 2, sl[0].stop + 2, sl[1].start - 2, sl[1].stop + 2
    outimg[y0:y1, x0:x1] = src[y0:y1, x0:x1].astype(np.uint8)

# ------------------------------------------------ labels (source, pixel-exact)
if with_labels:
    # 1. badge / tag / date boxes in the source: solid rectangles of fill colour -> never copy text inside them
    smx, smn = src.max(axis=2), src.min(axis=2)
    ssat = np.where(smx > 0, (smx - smn) / np.maximum(smx, 1), 0)
    sblack = src.sum(axis=2) < 150
    coloured = (ssat > 0.25) & (smx > 150) & ~sblack
    greyfill = (ssat < 0.08) & (smx > 150) & (smx < 235)
    boxmask = np.zeros((H, W), dtype=bool)
    def add_rects(mask, wmin, wmax, hmin, hmax, fill):
        labm, nm = ndimage.label(mask); found = 0
        for i, sl in enumerate(ndimage.find_objects(labm), start=1):
            h, w = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
            if not (wmin <= w <= wmax and hmin <= h <= hmax):
                continue
            if int((labm[sl] == i).sum()) / (h * w) < fill:
                continue
            boxmask[max(0, sl[0].start - 2):sl[0].stop + 2, max(0, sl[1].start - 2):sl[1].stop + 2] = True
            found += 1
        return found
    nb = add_rects(coloured, 55, 110, 13, 28, 0.55) + add_rects(coloured, 14, 30, 7, 14, 0.7) + add_rects(greyfill, 60, 120, 12, 28, 0.55)
    # 2. slate text pixels from the full-res source, outside those boxes
    fr, fg, fb = full[..., 0], full[..., 1], full[..., 2]
    slate_full = (np.abs(fr - 64) <= 20) & (np.abs(fg - 64) <= 20) & (np.abs(fb - 104) <= 22) & (fb > fr + 24)
    slate_full = ndimage.binary_dilation(slate_full, structure=np.ones((3, 3)))
    slate = np.asarray(Image.fromarray((slate_full * 255).astype(np.uint8)).resize((W, H), Image.BOX)) > 76
    slate &= ~boxmask
    # 3. keep glyph-sized components (>= 6 px and >= 4 px tall) plus tiny parts (i-dots, periods) within 3 px of one
    labg, ng = ndimage.label(slate, structure=np.ones((3, 3)))
    objs = ndimage.find_objects(labg)
    sizes = ndimage.sum(slate, labg, range(1, ng + 1))
    heights = np.array([o[0].stop - o[0].start for o in objs])
    glyph_ids = np.where((sizes >= 3) & (heights >= 3) & (heights <= 18))[0] + 1
    glyphs = np.isin(labg, glyph_ids)
    near = ndimage.binary_dilation(glyphs, iterations=3)
    small_ids = np.where((sizes >= 2) & (sizes < 6))[0] + 1
    smalls = np.isin(labg, small_ids) & near
    text = glyphs | smalls
    outimg[text] = (0x40, 0x40, 0x68)
    print(f"labels: {nb} badge/tag/date boxes masked; {len(glyph_ids)} glyph components, {int(text.sum())} text pixels copied")
    # 5. labels drawn over coloured land: dark-on-bright glyphs inside candidate land, away from outlines
    src_lum = (src[..., 0] * 0.299 + src[..., 1] * 0.587 + src[..., 2] * 0.114)
    bg = ndimage.maximum_filter(src_lum, size=13)
    dark = (src_lum < 0.6 * bg) & (src_lum < 120) & ~boxmask & ~edge
    on_land = (labels >= 0) & ~ndimage.binary_dilation(black, iterations=3)
    cand_txt = dark & on_land
    labd, nd = ndimage.label(cand_txt, structure=np.ones((3, 3)))
    if nd:
        objs_d = ndimage.find_objects(labd)
        sz = ndimage.sum(cand_txt, labd, range(1, nd + 1))
        hgt = np.array([o[0].stop - o[0].start for o in objs_d]); wid = np.array([o[1].stop - o[1].start for o in objs_d])
        ok = (sz >= 3) & (sz <= 120) & (hgt >= 3) & (hgt <= 18) & (wid <= 30)
        # word-ness: a glyph needs at least one other glyph within 14 px horizontally / 6 px vertically
        cy_ = np.array([(o[0].start + o[0].stop) / 2 for o in objs_d]); cx0 = np.array([(o[1].start + o[1].stop) / 2 for o in objs_d])
        ids = np.where(ok)[0]
        keep_d = []
        for i in ids:
            near_ = (np.abs(cx0[ids] - cx0[i]) <= 18) & (np.abs(cy_[ids] - cy_[i]) <= 6)
            if near_.sum() >= 2:
                keep_d.append(i + 1)
        land_text = np.isin(labd, keep_d)
        outimg[land_text] = (0x40, 0x40, 0x68)
        print(f"land labels: {len(keep_d)} glyph components, {int(land_text.sum())} pixels")
    # 4. badge remnants the model kept at the frame edges: components confined to the edge strip are wiped
    strip = np.zeros((H, W), dtype=bool); strip[:, W - 45:] = True; strip[:, 14:45] = True
    struct = (labels >= 0) | (black & ~edge)
    labst, nst = ndimage.label(struct, structure=np.ones((3, 3)))
    inside = ndimage.sum(strip, labst, range(1, nst + 1)); total = ndimage.sum(struct, labst, range(1, nst + 1))
    rem_ids = np.where((inside == total) & (total < 600))[0] + 1
    rem = np.isin(labst, rem_ids)
    outimg[rem] = 255; outimg[rem & grid] = (0xD9, 0xDA, 0xFF); outimg[rem & zone] = (0xB8, 0xB8, 0xB8)
    print("edge-strip remnant components wiped:", len(rem_ids))

# ------------------------------------------------ stray marks: small black blobs far from any land are model noise
cb, ncb = ndimage.label(black & ~edge)
if ncb:
    near_land = ndimage.binary_dilation(labels >= 0, iterations=3)
    csz = ndimage.sum(np.ones_like(cb), cb, range(1, ncb + 1))
    touches = ndimage.sum(near_land, cb, range(1, ncb + 1))
    stray_ids = np.where((csz < 120) & (touches == 0))[0] + 1
    stray = np.isin(cb, stray_ids)
    outimg[stray] = 255
    outimg[stray & grid] = (0xD9, 0xDA, 0xFF)
    print("stray black blobs removed:", len(stray_ids))

# ------------------------------------------------ crop to frame
rows = np.where(((outimg.astype(int).sum(axis=2) < 120).sum(axis=1) > W * 0.5))[0]
top, bottom = int(rows.min()), int(rows.max())
final = Image.fromarray(outimg).crop((0, max(0, top - 1), W, min(H, bottom + 2)))
final.save(f"{out}-final.png")
print("final", final.size, "unique colours", len(np.unique(np.asarray(final).reshape(-1, 3), axis=0)))
