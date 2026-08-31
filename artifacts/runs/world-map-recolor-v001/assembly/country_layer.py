"""Country-id raster on the GIF pixel grid + deterministic palette colouring."""
import json
import numpy as np
from PIL import Image
from scipy import ndimage

H, W = 485, 1001
prm = json.load(open('projection.json'))
d = json.load(open('ne_50m_admin0_lakes.geojson'))
LON = np.arange(-180, 180, 0.1) + 0.05
LAT = np.arange(-90, 90, 0.1) + 0.05

def fill_ring(mask, ring, invert=False):
    v = np.array(ring, float)
    if len(v) < 3:
        return
    r0 = max(0, int((v[:,1].min() + 90) / 0.1) - 1); r1 = min(len(LAT) - 1, int((v[:,1].max() + 90) / 0.1) + 1)
    x1s, y1s = v[:-1,0], v[:-1,1]; x2s, y2s = v[1:,0], v[1:,1]
    for r in range(r0, r1 + 1):
        y = LAT[r]
        c = (y1s <= y) != (y2s <= y)
        if not c.any():
            continue
        xs = x1s[c] + (y - y1s[c]) * (x2s[c] - x1s[c]) / (y2s[c] - y1s[c])
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            c0 = int(np.ceil((xs[i] + 180) / 0.1 - 0.5)); c1 = int(np.floor((xs[i+1] + 180) / 0.1 - 0.5))
            if c1 >= c0:
                mask[r, max(0,c0):min(len(LON)-1,c1)+1] = not invert

names = []
cid_grid = np.full((len(LAT), len(LON)), -1, np.int16)
for ci, f in enumerate(d['features']):
    names.append(f['properties'].get('NAME', str(ci)))
    m = np.zeros((len(LAT), len(LON)), bool)
    geom = f['geometry']
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    for poly in polys:
        fill_ring(m, poly[0])
        for hole in poly[1:]:
            fill_ring(m, hole, invert=True)
    cid_grid[m] = ci

yy, xx = np.mgrid[0:H, 0:W]
corr = json.load(open('residual-correction.json'))
cy, cx = corr['cy'], corr['cx']
dyf = cy[0] + cy[1]*yy + cy[2]*yy*yy + (cy[3]*yy*yy*yy if len(cy) > 3 else 0)
dxf = cx[0] + cx[1]*xx
xs_ = xx - dxf
ys_ = yy - dyf
lon = (xs_ - prm['x0']) * prm['kx']
lat = np.degrees(2*np.arctan(np.exp((prm['y0'] - ys_)/prm['k'])) - np.pi/2)
li = np.clip(((lon + 180)/0.1).astype(int), 0, len(LON)-1)
la = np.clip(((lat + 90)/0.1).astype(int), 0, len(LAT)-1)
cid = cid_grid[la, li]
np.save('countries-raw.npy', cid)
# fill small ocean gaps near coasts so slight misalignment still lands on a country
for _ in range(3):
    empty = cid < 0
    grow = ndimage.grey_dilation(cid, size=3)
    cid = np.where(empty, grow, cid)
np.save('countries.npy', cid)
json.dump(names, open('country-names.json','w'))
print('countries on pixel grid:', len(np.unique(cid[cid>=0])))

# adjacency + greedy palette colouring (deterministic)
PALETTE = ['#fc3234', '#049afc', '#04ce34', '#fcce34', '#fc8284', '#6cb6fc', '#94f7c6', '#ccc6fc', '#ccfe9c', '#34cefc']
pal = np.array([[int(h[1:3],16), int(h[3:5],16), int(h[5:7],16)] for h in PALETTE])
n = len(names)
adj = np.zeros((n, n), bool)
for axis in (0, 1):
    a = cid if axis == 0 else cid.T
    p1, p2 = a[:, :-1], a[:, 1:]
    m = (p1 >= 0) & (p2 >= 0) & (p1 != p2)
    for u, v in zip(p1[m].ravel(), p2[m].ravel()):
        adj[u, v] = adj[v, u] = True
# also treat near-neighbours (within 3px across straits) as adjacent for contrast
cid_d = ndimage.grey_dilation(cid, size=7)
m = (cid >= 0) & (cid_d >= 0) & (cid != cid_d)
for u, v in zip(cid[m].ravel(), cid_d[m].ravel()):
    adj[u, v] = adj[v, u] = True
sizes = np.bincount(cid[cid >= 0].ravel(), minlength=n)
order = np.argsort(-sizes)
colour = np.full(n, -1, int)
for c in order:
    if sizes[c] == 0:
        continue
    used = {colour[o] for o in np.where(adj[c])[0] if colour[o] >= 0}
    counts_used = np.bincount(colour[colour >= 0], minlength=len(PALETTE))
    free = [k for k in range(len(PALETTE)) if k not in used]
    if free:
        colour[c] = min(free, key=lambda k: (counts_used[k], k))
    else:
        colour[c] = int(np.argmin(counts_used))
clashes = sum(1 for a_ in range(n) for b_ in range(a_+1, n) if adj[a_, b_] and colour[a_] == colour[b_] >= 0)
print('adjacent same-colour clashes:', clashes)
json.dump({names[i]: PALETTE[colour[i]] for i in range(n) if sizes[i] > 0}, open('country-colours.json','w'), indent=1)
np.save('country-colour-idx.npy', colour)
# preview
prev = np.full((H, W, 3), 255, np.uint8)
ok = cid >= 0
prev[ok] = pal[colour[cid[ok]]]
Image.fromarray(prev).save('country-layer-preview.png')
print('preview saved')
