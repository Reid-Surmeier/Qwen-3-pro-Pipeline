#!/usr/bin/env python3
"""Deterministic derived plates for the replica (no generation involved).

Outputs, all composited from reference-owned pixels:
  textures/desktop-plate.png   reference frame, window rects magenta-filled,
                               orphaned border/shadow bands scrubbed so a
                               moved or minimized window leaves no chrome
                               behind on the desktop
  plates/<id>-minimized.png    collapsed window state: title-bar rows plus
                               the window's own bottom-border rows (ADR 0009
                               item 12: a clipped frame is not a minimized
                               state; this is a closed, source-owned asset)
"""
from PIL import Image
import numpy as np
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
REF_DIR = ROOT.parent / "artifacts/references/ro-hud-fullscreen"
MAG = (239, 7, 239)
TITLE_ROWS = 40      # title bar height kept in the minimized composite
BORDER_ROWS = 7      # bottom-border rows appended to close the frame
SCRUB_BAND = 6       # px band below/right of each rect scanned for orphans

ref = Image.open(REF_DIR / "reference-native.png").convert("RGB")
rects = json.loads((REF_DIR / "window-rects.json").read_text())
a = np.array(ref)
H, W = a.shape[:2]

# --- desktop plate -----------------------------------------------------------
plate = a.copy()
for x, y, w, h in rects.values():
    plate[y:y + h, x:x + w] = MAG

def orphan_mask(seg):
    """Chrome the reference drew just outside a window rect, over the magenta
    desktop: the 1px leaked border row (blue-grey) or the fading shadow
    (magenta-tinted, green-suppressed). World pixels stay untouched."""
    r, g, b = seg[..., 0].astype(int), seg[..., 1].astype(int), seg[..., 2].astype(int)
    shadow = (g < 50) & (b > 100) & (r > 40)
    border = (r < 90) & (g > 80) & (g < 140) & (b > 130)
    return shadow | border

for x, y, w, h in rects.values():
    x0, y0 = max(x - SCRUB_BAND, 0), max(y - SCRUB_BAND, 0)
    x1, y1 = min(x + w + SCRUB_BAND, W), min(y + h + SCRUB_BAND, H)
    for bx0, by0, bx1, by1 in (
            (x0, y + h, x1, y1),   # below
            (x0, y0, x1, y),       # above
            (x0, y0, x, y1),       # left
            (x + w, y0, x1, y1)):  # right
        band = plate[by0:by1, bx0:bx1]
        if band.size:
            band[orphan_mask(band)] = MAG

out = ROOT / "textures/desktop-plate.png"
Image.fromarray(plate).save(out)
print("wrote", out)

# --- minimized plates --------------------------------------------------------
# Donor bottom border: every window shares the same chrome, and windows that
# abut a neighbor have contaminated bottom rows — so close every collapsed bar
# with basic-info's clean bottom border (corners kept, middle tiled to width).
bx, by, bw, bh = rects["create-room"]
bsrc = a[by:by + bh, bx:bx + bw]
bbot = bh - 1
while bbot > 0:
    row = bsrc[bbot]
    if (~((row[:, 0] > 230) & (row[:, 1] < 25) & (row[:, 2] > 230))).mean() > 0.8:
        break
    bbot -= 1
donor = bsrc[bbot - BORDER_ROWS + 1:bbot + 1]
CORNER = 14

def closing_border(width):
    mid = donor[:, CORNER:CORNER + 1]
    middle = np.repeat(mid, max(width - 2 * CORNER, 0), axis=1)
    # right corner = mirrored left corner: the donor's own right corner
    # carries a cyan shadow wedge from its neighbourhood in the reference
    right = donor[:, :CORNER][:, ::-1]
    return np.concatenate([donor[:, :CORNER], middle, right], axis=1)

for wid, (x, y, w, h) in rects.items():
    if wid == "bottom-bar":
        continue  # source has no minimize control on the bar
    src = a[y:y + h, x:x + w]
    mini = np.concatenate([src[:TITLE_ROWS], closing_border(w)], axis=0)
    p = ROOT / f"plates/{wid}-minimized.png"
    Image.fromarray(mini).save(p)
    print("wrote", p, mini.shape[1], "x", mini.shape[0])

# --- control state patches ---------------------------------------------------
# Visible toggle states for stateful bitmap controls (ADR 0009 item 9).
# Radios: both states exist in the source; pure pixel swaps. Checkboxes: the
# unchecked state is synthesized by erasing the blue check inside the box.
import os

manifest = json.loads((ROOT / "data/runtime-manifest.json").read_text())
WINS = {w["id"]: w for w in manifest["windows"]}
patches_dir = ROOT / "plates/patches"
patches_dir.mkdir(exist_ok=True)
meta = {}

def hit_rect(wid, hid):
    for hit in WINS[wid]["hits"]:
        if hit["id"] == hid:
            return hit["r"]
    raise KeyError((wid, hid))

def plate_px(wid):
    return np.array(Image.open(ROOT / f"plates/{wid}.png").convert("RGB"))

def glyph_bbox(px, r, margin=2):
    x, y, w, h = r
    seg = px[y:y + h, x:x + w].astype(int)
    rr, gg, bb = seg[..., 0], seg[..., 1], seg[..., 2]
    ink = ((rr < 140) & (gg < 140) & (bb < 140)) | ((bb > 110) & (bb > rr + 25) & (bb > gg + 25))
    ys, xs = np.where(ink)
    # leftmost glyph only: cut at the first 4px-wide ink gap after the glyph
    order = np.argsort(xs)
    xs, ys = xs[order], ys[order]
    keep_to = xs[0]
    for xv in np.unique(xs):
        if xv - keep_to > 4:
            break
        keep_to = xv
    sel = xs <= keep_to
    xs, ys = xs[sel], ys[sel]
    return [x + int(xs.min()) - margin, y + int(ys.min()) - margin,
            int(xs.max() - xs.min()) + 1 + 2 * margin, int(ys.max() - ys.min()) + 1 + 2 * margin]

def save_patch(name, arr):
    p = patches_dir / f"{name}.png"
    Image.fromarray(arr.astype(np.uint8)).save(p)
    return f"res://plates/patches/{name}.png"

# checkboxes (party): synthesize unchecked. The box frame is the dark square
# in the first 44px of the hit row; the check overflows it in light blue, so
# the patch covers an expanded region and flat-fills the interior.
ppx = plate_px("party")
# detect the box frame once on check-item (its chrome reads darkest), then
# derive the identical check-exp box by the fixed 40px row offset
ix, iy, iw, ih = hit_rect("party", "check-item")
seg = ppx[iy:iy + ih, ix:ix + 44].astype(int)
dark = (seg[..., 0] < 140) & (seg[..., 1] < 140) & (seg[..., 2] < 140)
ys, xs = np.where(dark)
item_box = [ix + int(xs.min()), iy + int(ys.min()),
            int(xs.max() - xs.min()) + 1, int(ys.max() - ys.min()) + 1]
ex, ey, ew, eh = hit_rect("party", "check-exp")
item_box[2] = item_box[3]  # the source box is square; width detection can
                           # bleed into the label, height cannot
boxes = {"check-item": item_box,
         "check-exp": [item_box[0], item_box[1] - (iy - ey), item_box[2], item_box[3]]}
for hid in ["check-exp", "check-item"]:
    box = boxes[hid]
    gx, gy = box[0] - 4, box[1] - 8
    gw, gh = box[2] + 8, box[3] + 10
    crop = ppx[gy:gy + gh, gx:gx + gw].astype(int).copy()
    rr, gg, bb = crop[..., 0], crop[..., 1], crop[..., 2]
    blue = (bb > 90) & (bb > rr + 12) & (bb > gg + 12)
    ink = blue | ((rr < 140) & (gg < 140) & (bb < 140))
    panel = np.median(crop[~ink].reshape(-1, 3), axis=0)
    # redraw the box procedurally: flat panel, then the frame from per-edge
    # sampled colors and a clean interior — no anti-aliased check ghosts.
    bx0, by0, bw2, bh2 = box[0] - gx, box[1] - gy, box[2], box[3]
    src_box = ppx[box[1]:box[1] + bh2, box[0]:box[0] + bw2].astype(int)
    edge_t = np.median(src_box[0][(src_box[0] < 140).all(axis=-1)].reshape(-1, 3), axis=0)
    edge_b = np.median(src_box[-1][(src_box[-1] < 140).all(axis=-1)].reshape(-1, 3), axis=0)
    inner_px = src_box[3:-3, 3:-3]
    keep = ~(((inner_px < 140).all(axis=-1)) |
             ((inner_px[..., 2] > 90) & (inner_px[..., 2] > inner_px[..., 0] + 12)))
    interior_color = np.median(inner_px[keep].reshape(-1, 3), axis=0) if keep.any() else [250, 250, 250]
    crop[...] = panel
    crop[by0:by0 + bh2, bx0:bx0 + bw2] = interior_color
    crop[by0:by0 + 2, bx0:bx0 + bw2] = edge_t
    crop[by0 + bh2 - 2:by0 + bh2, bx0:bx0 + bw2] = edge_b
    crop[by0:by0 + bh2, bx0:bx0 + 2] = edge_t
    crop[by0:by0 + bh2, bx0 + bw2 - 2:bx0 + bw2] = edge_b
    off = save_patch(f"party-{hid}-off", crop)
    meta.setdefault("party", {})[hid] = {
        "pos": [gx, gy], "size": [gw, gh], "source_state": True,
        "on_asset": None, "off_asset": off}

# radios (create-room): swap source crops
cpx = plate_px("create-room")
gpub = glyph_bbox(cpx, hit_rect("create-room", "radio-public"), margin=2)
gpriv = glyph_bbox(cpx, hit_rect("create-room", "radio-private"), margin=2)
side = max(gpub[2], gpub[3], gpriv[2], gpriv[3])
def square(g):
    cx, cy = g[0] + g[2] // 2, g[1] + g[3] // 2
    return [cx - side // 2, cy - side // 2, side, side]
gpub, gpriv = square(gpub), square(gpriv)
on_crop = cpx[gpub[1]:gpub[1] + side, gpub[0]:gpub[0] + side]
off_crop = cpx[gpriv[1]:gpriv[1] + side, gpriv[0]:gpriv[0] + side]
on_a = save_patch("create-room-radio-on", on_crop)
off_a = save_patch("create-room-radio-off", off_crop)
meta.setdefault("create-room", {})["radio-public"] = {
    "pos": gpub[:2], "size": [side, side], "source_state": True,
    "on_asset": on_a, "off_asset": off_a}
meta["create-room"]["radio-private"] = {
    "pos": gpriv[:2], "size": [side, side], "source_state": False,
    "on_asset": on_a, "off_asset": off_a}

(ROOT / "data/state-patches.json").write_text(json.dumps(meta, indent=1))
print("wrote", ROOT / "data/state-patches.json")

# --- tab active-state patches (party) ---------------------------------------
# The source shows no distinct active-tab chrome, so we borrow the source's
# own active-state language: the blue-tinted status button in basic-info.
# Multiply-tint each tab's background with that sampled tint (ink survives).
# All tabs get source_state=false so the untouched frame stays exact; the
# highlight appears only once the user interacts with the tab group.
bpx = plate_px("basic-info")
sx, sy, sw, sh = hit_rect("basic-info", "btn-status")
sseg = bpx[sy + 8:sy + sh - 8, sx + 8:sx + sw - 8].astype(int)
light = sseg[(sseg > 170).all(axis=-1)]
tint = np.median(light.reshape(-1, 3), axis=0)  # the active blue background

# the visual tab band sits between two horizontal border lines; clamp the
# patch to it (hit rects are looser than the drawn cell)
tx, ty, tw, th = hit_rect("party", "tab-party")
lines = [yy for yy in range(ty - 30, ty + th + 30)
         if ((ppx[yy, 12:518].astype(int) < 190).all(axis=-1)).mean() > 0.5]
band_top = min(l for l in lines) + 2
band_bot = max(l for l in lines if l > band_top + 10)
for hid in ["tab-friends", "tab-party", "tab-guild"]:
    x, y, w, h = hit_rect("party", hid)
    gx, gy, gw, gh = x + 2, band_top, w - 4, band_bot - band_top - 1
    crop = ppx[gy:gy + gh, gx:gx + gw].astype(float)
    on = (crop * (tint / 255.0) ** 1.6).clip(0, 255)
    on_asset = save_patch(f"party-{hid}-on", on)
    meta.setdefault("party", {})[hid] = {
        "pos": [gx, gy], "size": [gw, gh], "source_state": False,
        "on_asset": on_asset, "off_asset": None}

(ROOT / "data/state-patches.json").write_text(json.dumps(meta, indent=1))
print("tab patches written")
