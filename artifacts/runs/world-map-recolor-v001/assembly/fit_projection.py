"""Fit the GIF's projection (lon linear, lat Mercator) against Natural Earth land."""
import json
import numpy as np
from PIL import Image
from scipy import ndimage

g = np.asarray(Image.open('wtz-map-12map-1001x485.gif').convert('RGB')).astype(np.int16)
H, W = g.shape[:2]
FILLS = [(0x04,0x9A,0xFC),(0xFC,0x32,0x34),(0x04,0xCE,0x34),(0xFC,0xCE,0x34),(0x04,0xFE,0x54),(0x04,0xBE,0x3C),
         (0x6C,0xB6,0xFC),(0xFC,0x82,0x84),(0xF7,0x7C,0x7C),(0x94,0xF7,0xC6),(0xCC,0xFE,0x9C),(0x34,0xCE,0xFC),
         (0xCC,0xC6,0xFC)]
land = np.zeros((H, W), bool)
for c in FILLS:
    land |= (g == np.array(c, np.int16)).all(axis=2)
land = ndimage.binary_opening(land, iterations=1)

# NE land on a 0.25 deg grid
d = json.load(open('ne_110m_admin0.geojson'))
LON = np.arange(-180, 180, 0.25) + 0.125
LAT = np.arange(-90, 90, 0.25) + 0.125
lon_g, lat_g = np.meshgrid(LON, LAT)
pts = np.stack([lon_g.ravel(), lat_g.ravel()], axis=1)
def fill_ring(mask, ring, LON, LAT, invert=False):
    """Scanline fill of one polygon ring into mask (rows = LAT bins, cols = LON bins)."""
    v = np.array(ring, float)
    if len(v) < 3:
        return
    la0, la1 = v[:,1].min(), v[:,1].max()
    r0 = max(0, int((la0 + 90) / 0.25) - 1); r1 = min(len(LAT) - 1, int((la1 + 90) / 0.25) + 1)
    x1s, y1s = v[:-1,0], v[:-1,1]; x2s, y2s = v[1:,0], v[1:,1]
    for r in range(r0, r1 + 1):
        y = LAT[r]
        c = (y1s <= y) != (y2s <= y)
        if not c.any():
            continue
        xs = x1s[c] + (y - y1s[c]) * (x2s[c] - x1s[c]) / (y2s[c] - y1s[c])
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            c0 = int(np.ceil((xs[i] + 180) / 0.25 - 0.5)); c1 = int(np.floor((xs[i+1] + 180) / 0.25 - 0.5))
            if c1 >= c0:
                c0 = max(0, c0); c1 = min(len(LON) - 1, c1)
                if invert:
                    mask[r, c0:c1+1] = False
                else:
                    mask[r, c0:c1+1] = True

ne_land = np.zeros(lon_g.shape, bool)
for f in d['features']:
    geom = f['geometry']
    polys = geom['coordinates'] if geom['type'] == 'MultiPolygon' else [geom['coordinates']]
    for poly in polys:
        fill_ring(ne_land, poly[0], LON, LAT)
        for hole in poly[1:]:
            fill_ring(ne_land, hole, LON, LAT, invert=True)
print('NE land cells:', int(ne_land.sum()))
np.save('ne_land_grid.npy', ne_land)

yy, xx = np.mgrid[0:H, 0:W]
def score(x0, kx, y0, k):
    lon = (xx - x0) * kx
    lat = np.degrees(2*np.arctan(np.exp((y0 - yy)/k)) - np.pi/2)
    li = np.clip(((lon + 180)/0.25).astype(int), 0, 1439)
    la = np.clip(((lat + 90)/0.25).astype(int), 0, 719)
    ne = ne_land[la, li]
    return int((ne & land).sum()) - int((ne ^ land).sum()) // 4

best = None
for x0 in (498, 500, 502):
    for kx in (0.355, 0.36, 0.365, 0.37, 0.375, 0.38):
        for y0 in range(200, 300, 10):
            for k in range(120, 260, 10):
                s = score(x0, kx, y0, k)
                if best is None or s > best[0]:
                    best = (s, x0, kx, y0, k)
print('coarse best:', best)
s0, x0b, kxb, y0b, kb = best
for x0 in np.arange(x0b-3, x0b+3.5, 1):
    for kx in np.arange(kxb-0.008, kxb+0.009, 0.002):
        for y0 in np.arange(y0b-8, y0b+9, 2):
            for k in np.arange(kb-8, kb+9, 2):
                s = score(x0, kx, y0, k)
                if s > best[0]:
                    best = (s, float(x0), float(kx), float(y0), float(k))
print('fine best:', best)
json.dump({'x0': best[1], 'kx': best[2], 'y0': best[3], 'k': best[4], 'score': best[0]}, open('projection.json','w'))
# overlay check: NE land boundary in magenta on the GIF
_, x0, kx, y0, k = best
lon = (xx - x0) * kx
lat = np.degrees(2*np.arctan(np.exp((y0 - yy)/k)) - np.pi/2)
li = np.clip(((lon + 180)/0.25).astype(int), 0, 1439)
la = np.clip(((lat + 90)/0.25).astype(int), 0, 719)
ne = ne_land[la, li]
edge = ne & ~ndimage.binary_erosion(ne)
ov = g.copy(); ov[edge] = (255, 0, 255)
Image.fromarray(ov.astype(np.uint8)).save('projection-check.png')
print('overlay saved')
