#!/usr/bin/env python3
"""Local registration of the NE cid layer to the source raster (research ticket #146, map #140).

Block-matching land-overlap: 64x64 tiles, 50% overlap, +-60 px search, agreement
score = (land&land + water&water)/valid over annotation-excluded pixels.
Outputs (to OUT):
  displacement-field.npz        dense smoothed (dy,dx) float32 fields + per-tile raw table
  countries-registered.npy      countries-raw warped by the smoothed field (nearest, ids integral)
  residuals.json                per-tile before/after tables + per-region summaries
  make_registration.py          this script (copied by the caller)
Usage: python3 make_registration.py ASSEMBLY_DIR OUT_DIR
"""
import json, sys
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage
from scipy.signal import fftconvolve
from scipy.interpolate import griddata

ASM, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

TS, STRIDE, R = 64, 32, 60          # tile size, stride (50% overlap), search radius
MIN_LAND = 250                      # min cid land px in a tile to attempt a match
EXCL = 5                            # px radius excluded around peak for 2nd-peak margin

g = np.asarray(Image.open(ASM / 'wtz-map-12map-1001x485.gif').convert('RGB')).astype(np.int16)
H, W = g.shape[:2]
craw = np.load(ASM / 'countries-raw.npy')
plates = np.asarray(Image.open(ASM / 'plates-mask.png')) > 0

def eq(*c):
    return (g == np.array(c, np.int16)).all(axis=2)

FILLS = [(0x04,0x9A,0xFC),(0xFC,0x32,0x34),(0x04,0xCE,0x34),(0xFC,0xCE,0x34),(0x04,0xFE,0x54),
         (0x04,0xBE,0x3C),(0x6C,0xB6,0xFC),(0xFC,0x82,0x84),(0xF7,0x7C,0x7C),(0x94,0xF7,0xC6),
         (0xCC,0xFE,0x9C),(0x34,0xCE,0xFC),(0xCC,0xC6,0xFC),(0x9C,0xFE,0xCC)]
fills = np.zeros((H, W), bool)
for c in FILLS:
    fills |= eq(*c)
BLACK = eq(0x04, 0x02, 0x04)

# credit box = largest mint component (as compose_v3 does)
mintm = eq(0x9C, 0xFE, 0xCC)
labm, nm = ndimage.label(mintm)
credit = np.zeros((H, W), bool)
if nm:
    sizes = ndimage.sum(mintm, labm, range(1, nm + 1))
    sl = ndimage.find_objects(labm)[int(np.argmax(sizes))]
    credit[max(0, sl[0].start - 4):sl[0].stop + 4, max(0, sl[1].start - 4):sl[1].stop + 4] = True

fills_np = fills & ~plates & ~credit

# black components that touch a fill are coastlines/borders; label boxes on open ocean are not
labb, nb = ndimage.label(BLACK & ~plates, structure=np.ones((3, 3)))
touch = np.unique(labb[ndimage.binary_dilation(fills_np, iterations=1) & (labb > 0)])
black_ok = np.isin(labb, touch[touch > 0])

base = fills_np | black_ok
closed = ndimage.binary_closing(base, structure=np.ones((5, 5)))   # bridge 1-2 px border/grid holes
src_land = ndimage.binary_fill_holes(closed)                       # enclosed white-fill countries -> land

valid = ~ndimage.binary_dilation(plates, iterations=2) & ~credit
valid[:4, :] = valid[-4:, :] = False
valid[:, :4] = valid[:, -4:] = False

def match_field(cid_land, R=R):
    """Tile block-match cid_land against src_land. Returns list of per-tile dicts."""
    S = (src_land & valid).astype(np.float32)
    Wt = (~src_land & valid).astype(np.float32)
    V = valid.astype(np.float32)
    pad = lambda a: np.pad(a, R)
    Sp, Wp, Vp = pad(S), pad(Wt), pad(V)
    C = pad(cid_land.astype(np.float32))
    rows = []
    for y0 in range(0, H - TS + 1, STRIDE):
        for x0 in range(0, W - TS + 1, STRIDE):
            T = C[y0 + R:y0 + R + TS, x0 + R:x0 + R + TS]
            tsum = T.sum()
            if tsum < MIN_LAND:
                rows.append(dict(x=x0, y=y0, ok=False, why='sparse', land=int(tsum)))
                continue
            U = 1.0 - T
            win = np.s_[y0:y0 + TS + 2 * R, x0:x0 + TS + 2 * R]
            kT, kU = T[::-1, ::-1], U[::-1, ::-1]
            A1 = fftconvolve(Sp[win], kT, mode='valid')   # land agree
            A2 = fftconvolve(Wp[win], kU, mode='valid')   # water agree
            B1 = fftconvolve(Vp[win], kT, mode='valid')   # valid px under T-land
            B2 = fftconvolve(Vp[win], kU, mode='valid')
            N = B1 + B2
            score = np.where(N > TS * TS * 0.25, (A1 + A2) / np.maximum(N, 1), 0.0)
            iy, ix = np.unravel_index(np.argmax(score), score.shape)
            peak = float(score[iy, ix])
            ratio = float(A1[iy, ix] / max(B1[iy, ix], 1))    # land-overlap ratio at peak
            # second peak outside EXCL radius
            m = score.copy()
            m[max(0, iy - EXCL):iy + EXCL + 1, max(0, ix - EXCL):ix + EXCL + 1] = -1
            second = float(m.max())
            # sub-pixel parabolic refinement
            dy, dx = iy - R, ix - R
            sy = sx = 0.0
            if 0 < iy < 2 * R and 0 < ix < 2 * R:
                c0, l, r = score[iy, ix], score[iy, ix - 1], score[iy, ix + 1]
                d = l - 2 * c0 + r
                if d < 0: sx = 0.5 * (l - r) / d
                u, dwn = score[iy - 1, ix], score[iy + 1, ix]
                d = u - 2 * c0 + dwn
                if d < 0: sy = 0.5 * (u - dwn) / d
            on_edge = iy in (0, 2 * R) or ix in (0, 2 * R)
            rows.append(dict(x=x0, y=y0, ok=True, land=int(tsum), dx=int(dx), dy=int(dy),
                             dxs=round(dx + sx, 2), dys=round(dy + sy, 2),
                             peak=round(peak, 4), overlap=round(ratio, 4),
                             margin=round(peak - second, 4), edge=bool(on_edge)))
    return rows

MIN_LAND_STATS = 600   # below this a tile is sparse (islands): matcher unreliable, flagged not scored

def reliable(r, mmin):
    return (r['ok'] and not r['edge'] and r['margin'] >= mmin and r['peak'] >= 0.80
            and r['overlap'] >= 0.5 and r['land'] >= MIN_LAND_STATS)

print('src_land px:', int(src_land.sum()), ' cid land px:', int((craw >= 0).sum()))

# ---- pass 1: measure the raw displacement field ------------------------------
pre = match_field(craw >= 0)
margins = sorted(r['margin'] for r in pre if r['ok'] and not r['edge'])
print('tiles matched:', sum(r['ok'] for r in pre), '/', len(pre),
      ' margin quartiles:', [round(margins[int(q * (len(margins) - 1))], 4) for q in (0.1, 0.25, 0.5, 0.75)])
MARGIN_MIN = 0.010

# ---- dense smoothed field ----------------------------------------------------
SIGMA = 16
yy, xx = np.mgrid[0:H, 0:W]

def dense_field(pts_k, vec_k):
    dyf = griddata(pts_k, vec_k[:, 0], (yy, xx), method='linear')
    dxf = griddata(pts_k, vec_k[:, 1], (yy, xx), method='linear')
    dyn = griddata(pts_k, vec_k[:, 0], (yy, xx), method='nearest')
    dxn = griddata(pts_k, vec_k[:, 1], (yy, xx), method='nearest')
    dyf = np.where(np.isnan(dyf), dyn, dyf)
    dxf = np.where(np.isnan(dxf), dxn, dxf)
    return (ndimage.gaussian_filter(dyf, SIGMA).astype(np.float32),
            ndimage.gaussian_filter(dxf, SIGMA).astype(np.float32))

def filter_tiles(rows, mmin):
    rel = [r for r in rows if reliable(r, mmin)]
    pts = np.array([[r['y'] + TS / 2, r['x'] + TS / 2] for r in rel])
    vec = np.array([[r['dys'], r['dxs']] for r in rel])
    keep = []
    for i in range(len(rel)):
        d = np.hypot(*(pts - pts[i]).T)
        nb_ = (d > 0) & (d < 120)
        if nb_.sum() >= 3:
            med = np.median(vec[nb_], axis=0)
            keep.append(np.hypot(*(vec[i] - med)) <= 12)
        else:
            keep.append(False)
    keep = np.array(keep, bool)
    return pts[keep], vec[keep], int(keep.sum()), len(rel)

pts_k, vec_k, nk, nr = filter_tiles(pre, MARGIN_MIN)
print('reliable tiles:', nr, ' after outlier/isolation filter:', nk)
dyf, dxf = dense_field(pts_k, vec_k)
print('field-1 range dy [%.1f, %.1f]  dx [%.1f, %.1f]' % (dyf.min(), dyf.max(), dxf.min(), dxf.max()))

# ---- warp (reverse map, nearest neighbour: ids stay integral) ---------------
def warp(dyf, dxf):
    sy = np.rint(yy - dyf).astype(np.int32)
    sx = np.rint(xx - dxf).astype(np.int32)
    inb = (sy >= 0) & (sy < H) & (sx >= 0) & (sx < W)
    reg = np.full((H, W), -1, craw.dtype)
    reg[inb] = craw[sy[inb], sx[inb]]
    return reg

reg1 = warp(dyf, dxf)

# ---- iteration 2: measure the remaining error of reg1, fold it into the field
mid = match_field(reg1 >= 0, R=25)
pts2, vec2, nk2, nr2 = filter_tiles(mid, MARGIN_MIN)
print('iter-2 tiles kept:', nk2, '/', nr2)
dyf2, dxf2 = dense_field(pts2, vec2)
dyf, dxf = dyf + dyf2, dxf + dxf2      # fields are smooth and small: additive compose
print('field-total range dy [%.1f, %.1f]  dx [%.1f, %.1f]' % (dyf.min(), dyf.max(), dxf.min(), dxf.max()))
reg = warp(dyf, dxf)
np.save(OUT / 'countries-registered.npy', reg)
np.savez_compressed(OUT / 'displacement-field.npz', dy=dyf, dx=dxf,
                    tile_y=pts_k[:, 0], tile_x=pts_k[:, 1], tile_dy=vec_k[:, 0], tile_dx=vec_k[:, 1])

# ---- final pass: residual AFTER, measured identically but with a tight search
# (+-15 px kills along-coast ridge slides that fake huge residuals; anything the
# correction left >15 px shows up as edge/unreliable, not as a clean number)
post = match_field(reg >= 0, R=15)

REGIONS = {  # x0,x1,y0,y1 in the 1001x485 source frame
    'N America': (40, 330, 55, 260), 'Greenland': (330, 455, 10, 110),
    'C America/Caribbean': (180, 335, 255, 325), 'S America': (255, 425, 300, 484),
    'Europe': (430, 585, 75, 210), 'Great Britain/Ireland': (435, 505, 110, 180),
    'Africa': (420, 645, 205, 430), 'Arabia/Middle East': (575, 685, 195, 305),
    'Russia/N Asia': (560, 960, 45, 200), 'S/E Asia': (640, 870, 195, 320),
    'SE Asia/Indonesia': (740, 895, 280, 365), 'Australia': (775, 955, 335, 445),
    'Australia SW': (760, 870, 355, 440), 'New Zealand': (915, 1000, 395, 484),
    'Pacific islands': (0, 260, 290, 470),
}

def summarize(rows):
    out = {}
    for name, (x0, x1, y0, y1) in REGIONS.items():
        rs = [r for r in rows if r['ok'] and x0 <= r['x'] + TS / 2 <= x1 and y0 <= r['y'] + TS / 2 <= y1]
        rr = [r for r in rs if reliable(r, MARGIN_MIN)]
        mags = sorted(np.hypot(r['dys'], r['dxs']) for r in rr)
        if mags:
            q = lambda p: round(float(mags[min(len(mags) - 1, int(np.ceil(p * len(mags))) - 1)]), 2)
            out[name] = dict(n_tiles=len(rs), n_reliable=len(rr), median=q(0.5), p90=q(0.9),
                             max=round(float(mags[-1]), 2),
                             mean_overlap=round(float(np.mean([r['overlap'] for r in rr])), 3))
        else:
            out[name] = dict(n_tiles=len(rs), n_reliable=0)
    return out

res = dict(params=dict(tile=TS, stride=STRIDE, search=R, search_after=15, iter2_search=25, min_land=MIN_LAND, margin_min=MARGIN_MIN,
                       smoothing_sigma=SIGMA, min_land_stats=MIN_LAND_STATS, outlier_radius=120, outlier_max_dev=12),
           src_land_px=int(src_land.sum()), cid_land_px=int((craw >= 0).sum()),
           before=dict(tiles=pre, regions=summarize(pre)),
           after=dict(tiles=post, regions=summarize(post)))
json.dump(res, open(OUT / 'residuals.json', 'w'), indent=1)

fmt = '%-22s %4s %4s %7s %6s %6s %7s || %7s %6s %6s %7s'
print(fmt % ('region', 'tls', 'rel', 'medB', 'p90B', 'maxB', 'ovlB', 'medA', 'p90A', 'maxA', 'ovlA'))
for name in REGIONS:
    b, a = res['before']['regions'][name], res['after']['regions'][name]
    print(fmt % (name, b['n_tiles'], b['n_reliable'],
                 b.get('median', '-'), b.get('p90', '-'), b.get('max', '-'), b.get('mean_overlap', '-'),
                 a.get('median', '-'), a.get('p90', '-'), a.get('max', '-'), a.get('mean_overlap', '-')))

worst = sorted((r for r in pre if reliable(r, MARGIN_MIN)),
               key=lambda r: -np.hypot(r['dys'], r['dxs']))[:15]
print('\nworst pre-correction tiles (x,y,dx,dy,|d|,overlap,margin):')
for r in worst:
    print(' (%4d,%3d) dx=%+6.1f dy=%+6.1f |d|=%5.1f ovl=%.3f mg=%.3f' %
          (r['x'], r['y'], r['dxs'], r['dys'], np.hypot(r['dys'], r['dxs']), r['overlap'], r['margin']))
