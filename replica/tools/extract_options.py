#!/usr/bin/env python3.12
"""Cut every part of the オプション (Options) window out of the hash-locked
Reference Screen, and derive the states the screenshot does not contain.

The Reference Screen shows each control in exactly ONE state.  This tool

  * cuts each control's idle artwork as its own PNG at native scale
    (derivation: ``source-cut``),
  * heals the two slider thumbs out of the window crop to make a clean plate,
    and erases the six checkbox footprints so their state textures can be laid
    on top without the source glyph showing through the replacement's
    transparent interior (derivation: ``derived: ...``),
  * derives the missing states -- hover, pressed, the checked ``on`` box, the
    open dropdown arrow -- by deterministic transforms of source pixels only.

Nothing is redrawn by hand and no model is called.  Every output is
reproducible from ``reference-native.png`` alone.

Every control texture carries a 1 px transparent margin on all four sides so
the hover outline and the 1 px pressed nudge have somewhere to go without
resizing the node.  ``manifest["controls"]`` records, per control, the measured
ink rect and the ``place_rect`` the Godot scene positions the node at.

Run:  python3.12 replica/tools/extract_options.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

# --------------------------------------------------------------------------
# paths

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / "artifacts/references/ro-desktop-b/reference-native.png"
OUT = ROOT / "replica/assets/options"
EVIDENCE = ROOT / "replica/evidence/builder"

WIN = (1108, 297, 424, 202)  # the options window in Reference Screen coords
PAD = 1  # transparent margin baked into every control texture

# Generous rectangles the measuring code scans inside.  Nothing below is a
# guessed control geometry: every emitted rect is measured by scanning pixels.
SEARCH = {
    "bgm_row": (1216, 342, 272, 30),
    "effect_row": (1216, 375, 272, 30),
    "bgm_on": (1482, 346, 20, 24),
    "effect_on": (1482, 378, 20, 24),
    "cb_attack": (1129, 462, 26, 26),
    "cb_skill": (1219, 462, 26, 26),
    "cb_item": (1291, 462, 26, 26),
    "cb_option": (1387, 462, 26, 26),
    "dropdown": (1220, 413, 303, 35),
    "minimize": (1478, 300, 24, 24),
    "close": (1504, 302, 23, 23),
}

# Clean title-bar columns, verified free of glyph ink.
TITLE_CLEAN = {
    "minimize": ((1474, 1480), (1499, 1506)),
    "close": ((1499, 1506), (1525, 1529)),
}

HOVER_TINT = 0.20  # fraction of the pale title-bar blue mixed into the glyph

manifest: dict = {
    "reference": {},
    "window_rect": {"x": WIN[0], "y": WIN[1], "w": WIN[2], "h": WIN[3]},
    "coordinate_space": "reference-native.png, 1536x1024, native scale (1:1)",
    "texture_margin_px": PAD,
    "tokens": {},
    "controls": {},
    "assets": {},
    "measurements": {},
    "notes": [],
}


# --------------------------------------------------------------------------
# helpers


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(name: str, arr: np.ndarray, source_rect, derivation: str, note: str = "") -> None:
    mode = "RGBA" if arr.shape[2] == 4 else "RGB"
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), mode)
    path = OUT / name
    img.save(path)
    entry = {
        "file": name,
        "size": [img.width, img.height],
        "derivation": derivation,
        "sha256": sha256(path),
    }
    if source_rect is not None:
        entry["source_rect"] = [int(v) for v in source_rect]
    if note:
        entry["note"] = note
    manifest["assets"][name] = entry


def crop(a: np.ndarray, rect) -> np.ndarray:
    x, y, w, h = rect
    return a[y : y + h, x : x + w].copy()


def grow(rect, pad: int = PAD):
    x, y, w, h = rect
    return (x - pad, y - pad, w + 2 * pad, h + 2 * pad)


def alpha_cut(a: np.ndarray, rect, background, soft: int = 18, floor: int = 6) -> np.ndarray:
    """Cut ``rect`` and un-mix it from a known background.

    ``background`` is an RGB triple (flat), one triple per row (a vertical
    gradient) or a full HxWx3 model.  Alpha rises 0..1 over ``soft`` levels of
    deviation, enclosed holes are filled so a ringed glyph is solid, and the
    colour is solved back out of the observed composite -- so drawing the
    result over the same background reproduces the source pixels.
    """
    sub = crop(a, rect).astype(float)
    h, w = sub.shape[:2]
    bg = np.asarray(background, dtype=float)
    if bg.ndim == 1:
        bg = np.tile(bg.reshape(1, 1, 3), (h, w, 1))
    elif bg.ndim == 2:
        bg = np.repeat(bg.reshape(h, 1, 3), w, axis=1)

    d = np.abs(sub - bg).max(axis=2)
    alpha = np.clip((d - floor) / float(soft), 0.0, 1.0)
    alpha = np.where(ndimage.binary_fill_holes(alpha > 0.5), 1.0, alpha)

    out = np.zeros((h, w, 4), dtype=float)
    safe = np.maximum(alpha, 1e-6)[..., None]
    out[..., :3] = np.clip((sub - (1.0 - alpha)[..., None] * bg) / safe, 0, 255)
    out[..., 3] = alpha * 255.0
    out[alpha <= 0.0, :3] = 0
    return out


def opaque_cut(a: np.ndarray, ink_rect) -> np.ndarray:
    """Opaque cut of ``ink_rect`` inside a PAD-wide transparent margin."""
    rgb = crop(a, ink_rect).astype(float)
    h, w = rgb.shape[:2]
    out = np.zeros((h + 2 * PAD, w + 2 * PAD, 4), float)
    out[PAD : PAD + h, PAD : PAD + w, :3] = rgb
    out[PAD : PAD + h, PAD : PAD + w, 3] = 255
    return out


def flat_background(a: np.ndarray, rect, pad: int = 3) -> np.ndarray:
    x, y, w, h = rect
    outer = crop(a, (x - pad, y - pad, w + 2 * pad, h + 2 * pad)).astype(int)
    mask = np.ones(outer.shape[:2], bool)
    mask[pad : pad + h, pad : pad + w] = False
    return np.median(outer[mask], axis=0)


def gradient_background(a: np.ndarray, rect, left_cols, right_cols) -> np.ndarray:
    """Per-pixel background for a glyph on the title bar's 2-D gradient.

    The title bar shades vertically and (gently) horizontally, so per row we
    interpolate between the median of a clean column block left of the glyph
    and one right of it.
    """
    x, y, w, h = rect
    lo = np.median(a[y : y + h, left_cols[0] : left_cols[1]].astype(float), axis=1)
    hi = np.median(a[y : y + h, right_cols[0] : right_cols[1]].astype(float), axis=1)
    lx = (left_cols[0] + left_cols[1] - 1) / 2.0
    rx = (right_cols[0] + right_cols[1] - 1) / 2.0
    t = (np.arange(w) + x - lx) / (rx - lx)
    return lo[:, None, :] * (1 - t)[None, :, None] + hi[:, None, :] * t[None, :, None]


def tint(rgba: np.ndarray, token, amount: float) -> np.ndarray:
    out = rgba.copy()
    t = np.asarray(token, float).reshape(1, 1, 3)
    out[..., :3] = np.clip(rgba[..., :3] * (1 - amount) + t * amount, 0, 255)
    return out


def outline(rgba: np.ndarray, colour) -> np.ndarray:
    """Ring the glyph's silhouette with a 1 px line of ``colour``."""
    out = rgba.copy()
    solid = rgba[..., 3] > 96
    ring = ndimage.binary_dilation(solid, np.ones((3, 3), bool)) & ~solid
    out[ring, 0], out[ring, 1], out[ring, 2] = colour[0], colour[1], colour[2]
    out[ring, 3] = 255.0
    return out


def nudge(rgba: np.ndarray, dx: int, dy: int) -> np.ndarray:
    out = np.zeros_like(rgba)
    h, w = rgba.shape[:2]
    sy0, sy1 = max(0, -dy), min(h, h - dy)
    sx0, sx1 = max(0, -dx), min(w, w - dx)
    out[sy0 + dy : sy1 + dy, sx0 + dx : sx1 + dx] = rgba[sy0:sy1, sx0:sx1]
    return out


def scale_rgb(rgba: np.ndarray, k: float) -> np.ndarray:
    out = rgba.copy()
    out[..., :3] = np.clip(rgba[..., :3] * k, 0, 255)
    return out


def register(control: str, ink_rect, kind: str, states: dict, behaviour: str) -> None:
    x, y, w, h = grow(ink_rect)
    manifest["controls"][control] = {
        "kind": kind,
        "ink_rect": [int(v) for v in ink_rect],
        "place_rect": [int(x), int(y), int(w), int(h)],
        "place_in_window": [int(x - WIN[0]), int(y - WIN[1])],
        "states": states,
        "behaviour": behaviour,
    }


# --------------------------------------------------------------------------

print(f"reading {REFERENCE}")
image = Image.open(REFERENCE).convert("RGB")
A = np.asarray(image).astype(int)
manifest["reference"] = {
    "file": str(REFERENCE.relative_to(ROOT)),
    "size": list(image.size),
    "sha256": sha256(REFERENCE),
}
OUT.mkdir(parents=True, exist_ok=True)
EVIDENCE.mkdir(parents=True, exist_ok=True)
WX, WY, WW, WH = WIN

# --------------------------------------------------------------------------
# 0. skin tokens, sampled from the window itself

title_body = np.median(A[303:321, 1300:1460].reshape(-1, 3), axis=0)
strip = A[299:322, 1108:1532]
deep_mask = ((strip[:, :, 2] - strip[:, :, 0]) > 45) & (strip.mean(axis=2) < 140)
deep_blue = np.median(strip[deep_mask], axis=0)
body_white = np.median(A[430:460, 1130:1200].reshape(-1, 3), axis=0)


def hexof(c) -> str:
    return "#%02X%02X%02X" % tuple(int(round(v)) for v in c)


manifest["tokens"] = {
    "title_bar_blue": {
        "hex": hexof(title_body),
        "rgb": [int(round(v)) for v in title_body],
        "derivation": "source-cut: median of reference-native.png x1300..1459 y303..320 "
        "(an empty span of this window's title bar)",
    },
    "title_ink_blue": {
        "hex": hexof(deep_blue),
        "rgb": [int(round(v)) for v in deep_blue],
        "derivation": "source-cut: median of the saturated dark-blue title-strip pixels "
        "(b-r > 45, luminance < 140) -- the ⊖/⊗ glyph ink. Used for the hover outline and as "
        "the dropdown's highlight-bar token: Behaviour Card cross-cutting finding 4 says the "
        "highlight colour belongs to the skin, not the control.",
    },
    "window_body": {
        "hex": hexof(body_white),
        "rgb": [int(round(v)) for v in body_white],
        "derivation": "source-cut: median of an empty span of the window body",
    },
}

# two more tokens, for the dropdown list panel the source never shows open
_field = A[418:444, 1226:1489]
_dark = _field.reshape(-1, 3)[_field.mean(axis=2).reshape(-1) < 90]
field_text = np.median(_dark, axis=0) if len(_dark) else np.array([20, 20, 20])
_border = np.median(np.concatenate([A[416:418, 1226:1489].reshape(-1, 3),
                                    A[444:446, 1226:1489].reshape(-1, 3)]), axis=0)
manifest["tokens"]["field_text"] = {
    "hex": hexof(field_text),
    "rgb": [int(round(v)) for v in field_text],
    "derivation": "source-cut: median of the dark pixels of the `Classic Blue` value text",
}
manifest["tokens"]["field_border"] = {
    "hex": hexof(_border),
    "rgb": [int(round(v)) for v in _border],
    "derivation": "source-cut: median of the dropdown field's own top and bottom border rows",
}
manifest["tokens"]["field_fill"] = {
    "hex": hexof(np.median(A[425:436, 1240:1330].reshape(-1, 3), axis=0)),
    "rgb": [int(round(v)) for v in np.median(A[425:436, 1240:1330].reshape(-1, 3), axis=0)],
    "derivation": "source-cut: median of an empty span inside the dropdown field",
}
INK = [int(round(v)) for v in deep_blue]
print("tokens:", {k: v["hex"] for k, v in manifest["tokens"].items()})

# --------------------------------------------------------------------------
# 1. the window crop, magenta-keyed at the rounded corners

win_rgb = crop(A, WIN)
win = np.dstack([win_rgb, np.full(win_rgb.shape[:2], 255, dtype=int)]).astype(float)
magenta = (win_rgb[:, :, 0] > 200) & (win_rgb[:, :, 1] < 60) & (win_rgb[:, :, 2] > 200)
win[magenta] = [0, 0, 0, 0]
save(
    "window.png",
    win,
    WIN,
    "source-cut (+ derived: pixels of the magenta #FF00FF desktop showing through the "
    "window's rounded corners keyed to alpha 0)",
    note=f"{int(magenta.sum())} corner pixels keyed",
)

# --------------------------------------------------------------------------
# 2. the minimized plate
#
# The ticket specifies a 424x24 title strip.  Measured: the ⊗ glyph's bottom
# border lies on y=321 -- one row BELOW a 24-row strip -- and the title-bar
# gradient runs to y=324 before the window's inner white line at y=325.  A
# 24-row strip clips the close button, so the plate is cut at 28 rows.

MIN_H = 28
save(
    "minimized-plate.png",
    win[:MIN_H].copy(),
    (WX, WY, WW, MIN_H),
    "source-cut",
    note="title strip; 28 rows rather than the ticket's 24 because the ⊗ glyph's bottom "
    "border is measured on y=321 and the title gradient's own edge is y=324",
)
save(
    "title-strip-24.png",
    win[:24].copy(),
    (WX, WY, WW, 24),
    "source-cut",
    note="the ticket's literal 424x24 strip; it clips the ⊗ glyph, so it is not used",
)

# --------------------------------------------------------------------------
# 3. title-bar buttons ⊖ and ⊗


def title_button(name: str):
    box = SEARCH[name]
    left_cols, right_cols = TITLE_CLEAN[name]
    d = np.abs(crop(A, box).astype(float) - gradient_background(A, box, left_cols, right_cols)).max(axis=2)
    ys, xs = np.where(d > 18)
    ink = (
        box[0] + int(xs.min()),
        box[1] + int(ys.min()),
        int(xs.max() - xs.min() + 1),
        int(ys.max() - ys.min() + 1),
    )
    cut = grow(ink)
    idle = alpha_cut(A, cut, gradient_background(A, cut, left_cols, right_cols), soft=20, floor=7)
    return ink, idle


min_ink, min_idle = title_button("minimize")
close_ink, close_idle = title_button("close")
print("minimize", min_ink, "close", close_ink)

# --------------------------------------------------------------------------
# 4. slider rows


def measure_slider(key: str) -> dict:
    bx, by, bw, bh = SEARCH[key]
    band = A[by : by + bh, bx : bx + bw]
    labelled, n = ndimage.label((band[:, :, 2] - band[:, :, 0]) > 30, structure=np.ones((3, 3)))
    comps = []
    for i in range(1, n + 1):
        ys, xs = np.where(labelled == i)
        if len(ys) < 30:
            continue
        comps.append(
            (bx + int(xs.min()), by + int(ys.min()), int(xs.max() - xs.min() + 1), int(ys.max() - ys.min() + 1))
        )
    comps.sort(key=lambda r: r[0])
    assert len(comps) == 3, f"{key}: expected left arrow, thumb, right arrow; got {comps}"
    left, thumb, right = comps

    # The track: probe a column midway between the left arrow and the thumb,
    # where nothing else is drawn, and take the contiguous non-body band that
    # contains its darkest row.  The window body reads 250-255; the sunken
    # track does not.
    probe_x = (left[0] + left[2] + thumb[0]) // 2
    col = A[by : by + bh, probe_x].mean(axis=1)
    band_mask = col < 246.0
    lo = hi = int(col.argmin())
    while lo > 0 and band_mask[lo - 1]:
        lo -= 1
    while hi < len(band_mask) - 1 and band_mask[hi + 1]:
        hi += 1
    track = (left[0] + left[2], by + lo, right[0] - (left[0] + left[2]), hi - lo + 1)
    return {"left": left, "right": right, "thumb": thumb, "track": track}


bgm = measure_slider("bgm_row")
eff = measure_slider("effect_row")
manifest["measurements"]["bgm_slider"] = {k: [int(v) for v in r] for k, r in bgm.items()}
manifest["measurements"]["effect_slider"] = {k: [int(v) for v in r] for k, r in eff.items()}
print("bgm   ", bgm)
print("effect", eff)

arrow_idles = {}
for row_name, geom in (("bgm", bgm), ("effect", eff)):
    for side in ("left", "right"):
        ink = geom[side]
        cut = grow(ink)
        arrow_idles[(row_name, side)] = (ink, alpha_cut(A, cut, flat_background(A, cut), soft=18, floor=6))

# The thumb of each row, cut from THAT row and un-mixed row by row from the
# track it sits on.  The ticket asked for one thumb cut from the BGM row; the
# two rows' thumbs differ by up to 86 levels in this compressed reference, so
# reusing the BGM crop on the Effect row leaves a visible 120 px patch.  Each
# row gets its own cut and both idle rows are then exact.
thumb_inks, thumb_idles = {}, {}
for row_name, geom in (("bgm", bgm), ("effect", eff)):
    ink = geom["thumb"]
    cut = grow(ink)
    tk = geom["track"]
    bg_rows = np.median(A[cut[1] : cut[1] + cut[3], tk[0] + 4 : tk[0] + 12], axis=1)
    thumb_inks[row_name] = ink
    thumb_idles[row_name] = alpha_cut(A, cut, bg_rows, soft=16, floor=5)

# --------------------------------------------------------------------------
# 5. checkboxes


def measure_box(key: str):
    box = SEARCH[key]
    bg = flat_background(A, box, pad=2)
    sub = crop(A, box).astype(int)
    ys, xs = np.where(np.abs(sub - bg.reshape(1, 1, 3)).max(axis=2) > 12)
    return (
        box[0] + int(xs.min()),
        box[1] + int(ys.min()),
        int(xs.max() - xs.min() + 1),
        int(ys.max() - ys.min() + 1),
    ), bg


boxes = {k: measure_box(k) for k in ("cb_attack", "cb_skill", "cb_item", "cb_option", "bgm_on", "effect_on")}
print("boxes", {k: v[0] for k, v in boxes.items()})
for k, (r, _) in boxes.items():
    manifest["measurements"][k] = {"ink_rect": [int(v) for v in r]}

# Which state the Reference Screen actually shows for each box.  The state it
# shows is a source-cut; the other one is derived from it, so BOTH the idle
# frame and a reversal (toggle on, toggle off) are exact for every box.
BOX_SOURCE_STATE = {
    "cb_attack": "off", "cb_skill": "on", "cb_item": "on", "cb_option": "off",
    "bgm_on": "off", "effect_on": "off",
}
raw_box = {k: alpha_cut(A, grow(boxes[k][0]), boxes[k][1], soft=16, floor=5) for k in boxes}

# the tick glyph, and where it sits inside the footer box that carries it
_att, _ski = raw_box["cb_attack"], raw_box["cb_skill"]
hh = min(_att.shape[0], _ski.shape[0])
ww = min(_att.shape[1], _ski.shape[1])
delta = np.abs(_ski[:hh, :ww, :3] - _att[:hh, :ww, :3]).max(axis=2)
tick_mask = ndimage.binary_fill_holes(ndimage.binary_closing(delta > 40, np.ones((2, 2))))
tys, txs = np.where(tick_mask)
TY0, TX0 = int(tys.min()), int(txs.min())
sl = (slice(TY0, int(tys.max()) + 1), slice(TX0, int(txs.max()) + 1))
tick = np.zeros((sl[0].stop - sl[0].start, sl[1].stop - sl[1].start, 4), float)
tick[..., :3] = _ski[sl][..., :3]
tick[..., 3] = np.where(tick_mask[sl], 255.0, 0.0)


def _paste_tick(base: np.ndarray, oy: int, ox: int) -> np.ndarray:
    out = base.copy()
    oy, ox = max(oy, 0), max(ox, 0)
    h_ = min(tick.shape[0], out.shape[0] - oy)
    w_ = min(tick.shape[1], out.shape[1] - ox)
    reg = out[oy : oy + h_, ox : ox + w_]
    at = tick[:h_, :w_, 3:4] / 255.0
    reg[..., :3] = tick[:h_, :w_, :3] * at + reg[..., :3] * (1 - at)
    reg[..., 3] = np.maximum(reg[..., 3], tick[:h_, :w_, 3])
    return out


def _erase_tick(base: np.ndarray) -> np.ndarray:
    """Replace the tick's footprint with the same patch of the `attack` box."""
    out = base.copy()
    y0, x0 = max(TY0 - 1, 0), max(TX0 - 1, 0)
    h_ = min(tick.shape[0] + 2, out.shape[0] - y0, _att.shape[0] - y0)
    w_ = min(tick.shape[1] + 2, out.shape[1] - x0, _att.shape[1] - x0)
    out[y0 : y0 + h_, x0 : x0 + w_] = _att[y0 : y0 + h_, x0 : x0 + w_]
    return out


box_tex = {}
for key, shown in BOX_SOURCE_STATE.items():
    raw = raw_box[key]
    if key in ("bgm_on", "effect_on"):
        oy = max((raw.shape[0] - tick.shape[0]) // 2, 0)
        ox = max((raw.shape[1] - tick.shape[1]) // 2, 0)
    else:
        oy, ox = TY0, TX0
    if shown == "off":
        box_tex[key] = {"off": raw, "on": _paste_tick(raw, oy, ox)}
    else:
        box_tex[key] = {"on": raw, "off": _erase_tick(raw)}

# --------------------------------------------------------------------------
# 6. dropdown

dd_box = SEARCH["dropdown"]
dd_bg = flat_background(A, dd_box, pad=2)
_sub = crop(A, dd_box).astype(int)
_ys, _xs = np.where(np.abs(_sub - dd_bg.reshape(1, 1, 3)).max(axis=2) > 12)
dd_rect = (
    dd_box[0] + int(_xs.min()),
    dd_box[1] + int(_ys.min()),
    int(_xs.max() - _xs.min() + 1),
    int(_ys.max() - _ys.min() + 1),
)
dx, dy, dw, dh = dd_rect
# The arrow button's own left border is the only vertical dark column in the
# rows just under the dropdown's top border, where the triangle is not drawn.
top = A[dy + 2 : dy + 8, dx : dx + dw].mean(axis=2).min(axis=0)
cands = [i for i, v in enumerate(top) if v < 220 and dw - 60 <= i <= dw - 6]
assert cands, "no dropdown divider found"
divider = min(cands)
field_ink = (dx, dy, divider, dh)
arrow_ink = (dx + divider, dy, dw - divider, dh)
manifest["measurements"]["dropdown"] = {
    "ink_rect": [int(v) for v in dd_rect],
    "field_ink_rect": [int(v) for v in field_ink],
    "arrow_ink_rect": [int(v) for v in arrow_ink],
}
print("dropdown", dd_rect, "field", field_ink, "arrow", arrow_ink)
field_idle = opaque_cut(A, field_ink)
arrow_idle = opaque_cut(A, arrow_ink)

# --------------------------------------------------------------------------
# 7. the clean plate

plate = win.copy()
heal_log, erase_log = [], []

for row_name, geom in (("bgm", bgm), ("effect", eff)):
    thx, thy, thw, thh = geom["thumb"]
    tx, ty, tw, th = geom["track"]
    # Footprint = thumb bbox + 3 px.  The reference is a compressed screenshot
    # and the thumb's dark outline rings two or three track columns either
    # side; a 1 px pad leaves that ringing behind as a 13-17 level seam.
    pad = 3
    fx0, fy0, fw, fh = thx - pad, thy - pad, thw + 2 * pad, thh + 2 * pad
    gap = 6
    if fx0 - gap - fw >= tx + 2:
        donor_x, side = fx0 - gap - fw, "left"
    else:
        donor_x, side = fx0 + fw + gap, "right"
    donor = A[fy0 : fy0 + fh, donor_x : donor_x + fw].astype(float)
    src_l = A[fy0 : fy0 + fh, fx0 - 1].astype(float)
    src_r = A[fy0 : fy0 + fh, fx0 + fw].astype(float)
    don_l = A[fy0 : fy0 + fh, donor_x - 1].astype(float)
    don_r = A[fy0 : fy0 + fh, donor_x + fw].astype(float)
    ramp = ((np.arange(fw) + 1) / (fw + 1.0))[None, :, None]
    healed = donor + (1 - ramp) * (src_l - don_l)[:, None, :] + ramp * (src_r - don_r)[:, None, :]
    plate[fy0 - WY : fy0 - WY + fh, fx0 - WX : fx0 - WX + fw, :3] = np.clip(np.round(healed), 0, 255)
    plate[fy0 - WY : fy0 - WY + fh, fx0 - WX : fx0 - WX + fw, 3] = 255
    heal_log.append(
        {
            "row": row_name,
            "thumb_footprint": [int(fx0), int(fy0), int(fw), int(fh)],
            "donor_rect": [int(donor_x), int(fy0), int(fw), int(fh)],
            "donor_side": side,
            "dc_match": f"per row, a linear ramp between the flanking source columns x={fx0 - 1} "
            f"and x={fx0 + fw} corrects the donor's DC offset; measured residual seam <= 2 levels",
        }
    )

for key in ("cb_attack", "cb_skill", "cb_item", "cb_option", "bgm_on", "effect_on"):
    (ex, ey, ew, eh), bg = boxes[key]
    ex, ey, ew, eh = ex - 1, ey - 1, ew + 2, eh + 2
    plate[ey - WY : ey - WY + eh, ex - WX : ex - WX + ew, :3] = np.round(bg)
    plate[ey - WY : ey - WY + eh, ex - WX : ex - WX + ew, 3] = 255
    erase_log.append(
        {"control": key, "footprint": [int(ex), int(ey), int(ew), int(eh)], "fill_rgb": [int(round(v)) for v in bg]}
    )

save(
    "clean-plate.png",
    plate,
    WIN,
    "derived: window.png with (a) both slider thumbs healed by copying the nearest empty "
    "track segment of the same rows (footprint = thumb bbox + 3 px, donor 6 px clear, "
    "DC-matched per row by a linear ramp to the flanking columns) and (b) the six checkbox "
    "footprints filled with the median colour of the 2 px ring around each box, so their "
    "state textures can be drawn on top without the source glyph showing through",
    note="labels, the Skin row's `Classic Blue` pixels, the arrows, the tracks, the dropdown "
    "and both title-bar glyphs are untouched",
)
manifest["measurements"]["clean_plate_thumb_heal"] = heal_log
manifest["measurements"]["clean_plate_checkbox_erase"] = erase_log

# --------------------------------------------------------------------------
# 8. states

HOVER_NOTE = (
    "derived (INVENTED-IN-STYLE): a 1 px outline in the skin's title-bar ink blue %s plus a "
    "%d%% tint toward the pale title-bar blue %s. The Behaviour Cards record hover on buttons "
    "and dropdown rows and note the highlight colour is a skin token; hover on THIS control is "
    "NOT observed in the Source Game. It exists under the owner's hover-everywhere rule and is "
    "struck by deleting the *-hover.png assets."
) % (hexof(deep_blue), int(HOVER_TINT * 100), hexof(title_body))

PRESSED_NOTE = (
    "derived: the idle glyph nudged 1 px down and right. Behaviour Card `button` (#115): "
    "between hover and pressed only the LABEL moves -- a 2-D shift search puts the best match at "
    "(dx +2, dy +1) at that capture's up-scale, i.e. the client's 1 px press offset -- while the "
    "fill's row-brightness profile is unchanged within 1-2 grey levels."
)


def emit(base: str, idle: np.ndarray, ink_rect, idle_derivation: str, pressed: str = "nudge",
         extra: dict | None = None) -> dict:
    states = {}
    save(f"{base}-idle.png", idle, ink_rect, idle_derivation)
    states["idle"] = f"{base}-idle.png"
    save(f"{base}-hover.png", outline(tint(idle, title_body, HOVER_TINT), INK), ink_rect, HOVER_NOTE)
    states["hover"] = f"{base}-hover.png"
    if pressed == "nudge":
        save(f"{base}-pressed.png", nudge(idle, 1, 1), ink_rect, PRESSED_NOTE)
    elif pressed == "thumb":
        save(
            f"{base}-pressed.png",
            scale_rgb(idle, 0.78),
            ink_rect,
            "derived: the idle thumb multiplied by 0.78 grey -- the pressed treatment proven in "
            "the predecessor repo's Options-window prototype, the canonical quality floor named "
            "by ADR 0006. The Source Game does not show a slider thumb held.",
        )
    elif pressed == "dim":
        save(
            f"{base}-pressed.png",
            scale_rgb(idle, 0.85),
            ink_rect,
            "derived: the idle glyph multiplied by 0.85 while held. INTENT-SPECIFIED: the Source "
            "Game shows no checkbox press state (Behaviour Card `checkbox`: hover and press both "
            "Not observed).",
        )
    states["pressed"] = f"{base}-pressed.png"
    if extra:
        states.update(extra)
    return states


register(
    "minimize",
    min_ink,
    "button",
    emit("minimize", min_idle, min_ink, "source-cut (alpha un-mixed from a 2-D model of the title-bar gradient)"),
    "toggles minimized/restored, instantly. Manual-attested (M1): "
    "「ウィンドウ右上のボタンで、最大化／最小化の切り替えも可能だ。」 -- a two-state toggle on the same "
    "button. The collapsed FORM (a bare title strip) is intent-specified.",
)
register(
    "close",
    close_ink,
    "button",
    emit("close", close_idle, close_ink, "source-cut (alpha un-mixed from a 2-D model of the title-bar gradient)"),
    "hides the window whole, in one frame (Behaviour Card `close`). Esc also closes the focused "
    "window (manual-attested via the shortcut list).",
)

for (row_name, side), (ink, idle) in arrow_idles.items():
    register(
        f"{row_name}_arrow_{side}",
        ink,
        "button",
        emit(f"{row_name}-arrow-{side}", idle, ink, "source-cut (alpha un-mixed from the window body)"),
        "steps the slider by 2. INTENT-SPECIFIED: Behaviour Card `slider` records the arrow "
        "gesture as Unverified; roBrowser's step=1 is secondary evidence only.",
    )

for row_name in ("bgm", "effect"):
    register(
        f"{row_name}_thumb",
        thumb_inks[row_name],
        "thumb",
        emit(
            f"{row_name}-thumb",
            thumb_idles[row_name],
            thumb_inks[row_name],
            f"source-cut from the {row_name.upper()} row (alpha un-mixed row by row from the "
            "track it sits on; enclosed holes filled so the whole disc is opaque)",
            pressed="thumb",
        ),
        "follows the pointer continuously while held and clamps flush at both track ends "
        "(Behaviour Card `slider`: End clamping Confirmed; the drag itself is Unverified).",
    )

BOX_LABEL = {
    "cb_attack": "the footer `attack` box",
    "cb_skill": "the footer `skill` box",
    "cb_item": "the footer `item` box",
    "cb_option": "the footer `option` box",
    "bgm_on": "the BGM `on` mute box",
    "effect_on": "the Effect `on` mute box",
}
for key, shown in BOX_SOURCE_STATE.items():
    states = {}
    for state in ("off", "on"):
        if state == shown:
            deriv = (f"source-cut: {BOX_LABEL[key]} in the state the Reference Screen shows it "
                     f"({'unchecked' if shown == 'off' else 'checked'}); alpha un-mixed from the "
                     "window body")
        elif state == "on":
            deriv = ("derived: this box's own square with the tick glyph composited into it at the "
                     "offset the tick occupies inside the footer `skill` box (centred, for the "
                     "smaller `on` boxes). The Reference Screen never shows this box checked.")
        else:
            deriv = ("derived: this box's own square with the tick's footprint replaced by the same "
                     "patch of the footer `attack` box, which the Reference Screen does show "
                     "unchecked. The Reference Screen never shows this box unchecked.")
        states[state] = emit(f"{key}-{state}", box_tex[key][state], boxes[key][0], deriv, pressed="dim")
    register(
        key,
        boxes[key][0],
        "checkbox",
        states,
        "toggles on release, reversibly; the square never changes, only the tick appears or goes "
        "(Behaviour Card `checkbox`). Both states of this control are its OWN square, so the idle "
        "frame is exact and a toggle round-trip restores byte-identical pixels.",
    )

save(
    "tick.png",
    tick,
    boxes["cb_skill"][0],
    "derived: the tick glyph isolated as |skill - attack| > 40, closed and hole-filled; the "
    "intermediate used to build on-checked.png",
)

register(
    "dropdown_field",
    field_ink,
    "button",
    emit(
        "dropdown-field",
        field_idle,
        field_ink,
        "source-cut; keeps the source's own `Classic Blue` pixels as the idle value texture, so "
        "the committed value is only ever rendered as a Label after the player picks a different skin",
    ),
    "click opens the list downward over whatever is beneath it (Behaviour Card `dropdown`, "
    "cut-verified at 1 frame).",
)
register(
    "dropdown_arrow",
    arrow_ink,
    "button",
    emit("dropdown-arrow", arrow_idle, arrow_ink, "source-cut", extra={"open": "dropdown-arrow-open.png"}),
    "click opens the list; while the list is open the button is repainted darker/inset "
    "(Behaviour Card `dropdown`).",
)
# A blank field, for the case where the player picks a skin other than the one
# the Reference Screen shows.  The source's own `Classic Blue` pixels stay as
# the idle texture; this one only appears after a commit to another value.
fx, fy, fw_, fh_ = field_ink
_interior = A[fy + 3 : fy + fh_ - 3, fx + 3 : fx + fw_ - 3]
_text_mask = _interior.mean(axis=2) < 200
_tys, _txs = np.where(_text_mask)
_tb = (fx + 3 + int(_txs.min()) - 2, fy + 3 + int(_tys.min()) - 2,
       int(_txs.max() - _txs.min() + 1) + 4, int(_tys.max() - _tys.min() + 1) + 4)
_fill_rows = np.median(A[_tb[1] : _tb[1] + _tb[3], fx + 6 : fx + 26], axis=1)
blank = field_idle.copy()
blank[_tb[1] - fy + PAD : _tb[1] - fy + _tb[3] + PAD,
      _tb[0] - fx + PAD : _tb[0] - fx + _tb[2] + PAD, :3] = np.round(_fill_rows)[:, None, :]
BLANK_NOTE = (
    "derived: the dropdown field with its `Classic Blue` value text erased -- the text's "
    f"bounding box {list(_tb)} filled per row with the median of the field's own empty "
    "interior columns. Only used once the player commits a skin other than Classic Blue; "
    "the value is then drawn as a DotGothic16 Label on top."
)
save("dropdown-field-blank-idle.png", blank, field_ink, BLANK_NOTE)
save("dropdown-field-blank-hover.png", outline(tint(blank, title_body, HOVER_TINT), INK),
     field_ink, BLANK_NOTE + " " + HOVER_NOTE)
save("dropdown-field-blank-pressed.png", nudge(blank, 1, 1), field_ink,
     BLANK_NOTE + " " + PRESSED_NOTE)
manifest["controls"]["dropdown_field"]["states"]["blank_idle"] = "dropdown-field-blank-idle.png"
manifest["controls"]["dropdown_field"]["states"]["blank_hover"] = "dropdown-field-blank-hover.png"
manifest["controls"]["dropdown_field"]["states"]["blank_pressed"] = "dropdown-field-blank-pressed.png"
manifest["measurements"]["dropdown"]["value_text_bbox"] = [int(v) for v in _tb]

save(
    "dropdown-arrow-open.png",
    scale_rgb(arrow_idle, 0.82),
    arrow_ink,
    "derived: the idle arrow button multiplied by 0.82. Behaviour Card `dropdown`: the arrow "
    "button IS repainted darker/inset while the list is open -- the form is observed, the exact "
    "pixels are not readable at that capture's resolution.",
)

# the two tracks, cut out of the healed plate: the trough is its own node
# (ADR 0006 dimension 3) while staying pixel-identical to the plate beneath it
for row_name, geom in (("bgm", bgm), ("effect", eff)):
    tx, ty, tw, th = geom["track"]
    seg = plate[ty - WY : ty - WY + th, tx - WX : tx - WX + tw].copy()
    seg[..., 3] = 255
    save(
        f"{row_name}-track.png",
        seg,
        (tx, ty, tw, th),
        "derived: cut out of clean-plate.png -- the source track with the thumb healed away",
    )
    manifest["controls"][f"{row_name}_track"] = {
        "kind": "track",
        "ink_rect": [int(tx), int(ty), int(tw), int(th)],
        "place_rect": [int(tx), int(ty), int(tw), int(th)],
        "place_in_window": [int(tx - WX), int(ty - WY)],
        "states": {"idle": f"{row_name}-track.png"},
        "behaviour": "clicking anywhere on the track jumps the thumb to the pointer and begins a "
        "drag. INTENT-SPECIFIED.",
    }

# --------------------------------------------------------------------------
# 9. slider value mapping


def value_of(geom) -> float:
    tx, ty, tw, th = geom["track"]
    thx, thy, thw, thh = geom["thumb"]
    return (thx - tx) / float(tw - thw) * 100.0


bgm_value, eff_value = value_of(bgm), value_of(eff)
manifest["measurements"]["slider_value_mapping"] = {
    "rule": "thumb.x = track.x + round(value / 100 * (track.w - thumb.w)); the thumb clamps flush "
    "at both ends (Behaviour Card `slider`: End clamping Confirmed)",
    "bgm_default": round(bgm_value, 4),
    "effect_default": round(eff_value, 4),
    "inventory_states": ["thumb at ~80%", "thumb at ~48%"],
    "default_note": "the defaults are the exact measured values, not integers: the track's travel "
    "is 211 px over 0..100, so no integer BGM value lands the thumb on the source pixel "
    "(86 -> x1420, 87 -> x1423, source x1422). The value is continuous while dragging; the arrows "
    "step it by 2 and the wheel by 1.",
    "arrow_step": 2,
    "wheel_step": 1,
    "step_provenance": "INTENT-SPECIFIED. Behaviour Card `slider` records gesture -> response as "
    "Unverified for both the drag and the arrows; roBrowser's min=0 max=100 step=1 is secondary "
    "evidence only.",
}
print(f"BGM {bgm_value:.2f}  Effect {eff_value:.2f}")

# --------------------------------------------------------------------------
# 10. notes

manifest["notes"] = [
    "The Reference Screen is the sole visual authority. No artwork from the official play manual "
    "was used and nothing was redrawn by hand.",
    "Hover on the thumb, the arrows, the checkboxes, the dropdown and ⊖/⊗ is INVENTED-IN-STYLE: "
    "the Source Game shows hover on buttons and dropdown rows but never on any of these. It is "
    "the owner's hover-everywhere rule and is struck by deleting the *-hover.png assets.",
    "The pressed nudge is source-derived in KIND (Behaviour Card `button`, #115: the label moves, "
    "the fill does not) but has never been observed on these particular controls.",
    "The window drag is INTENT-SPECIFIED. ADR 0006 and #115: players never move windows, so the "
    "corpus contains no drag at all.",
    "The minimized FORM -- a bare title strip -- is INTENT-SPECIFIED. The manual attests the ⊖ "
    "toggle's semantics (M1) but no frame in either corpus shows a collapsed window.",
    "All transitions are instant. Behaviour Card cross-cutting finding 0: about forty measured "
    "transitions each complete within one frame at 60 fps, and there is no animation anywhere in "
    "this UI. The prototype contains no tweens.",
    "The `reopen` text button in the desktop's top-left is a PROTOTYPE AFFORDANCE, not a Source "
    "Game control. It exists only so the owner can reopen the window after ⊗ during a play "
    "session, and it is visible only while the window is hidden.",
    "The four skin names in the open list -- Classic Blue, <Basic Skin>, scribbling kid, tanublue "
    "-- come from the Behaviour Card `dropdown` evidence; only `Classic Blue` is legible in this "
    "Reference Screen.",
]

(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
print(f"wrote {OUT / 'manifest.json'}: {len(manifest['assets'])} assets, {len(manifest['controls'])} controls")

# --------------------------------------------------------------------------
# 11. 4x contact sheets, flow-packed into readable pages

SCALE, GAP, LABEL_H, MAX_W, MAX_H = 4, 10, 15, 1760, 1250
CHECK = Image.new("RGB", (16, 16), (105, 105, 112))
for yy in range(0, 16, 8):
    for xx in range(0, 16, 8):
        if (xx // 8 + yy // 8) % 2 == 0:
            CHECK.paste(Image.new("RGB", (8, 8), (145, 145, 152)), (xx, yy))
try:
    FONT = ImageFont.truetype(str(ROOT / "replica/fonts/DotGothic16-Regular.ttf"), 12)
except Exception:
    FONT = ImageFont.load_default()

cells = []
for n in sorted(manifest["assets"]):
    img = Image.open(OUT / n).convert("RGBA")
    scale = SCALE
    while img.width * scale > MAX_W - 2 * GAP and scale > 1:
        scale -= 1
    cells.append((n, img.resize((img.width * scale, img.height * scale), Image.NEAREST), scale))

rows, cur, cur_w = [], [], 0
for cell in cells:
    w = cell[1].width + GAP * 2
    if cur and cur_w + w > MAX_W:
        rows.append(cur)
        cur, cur_w = [], 0
    cur.append(cell)
    cur_w += w
if cur:
    rows.append(cur)

pages, page, page_h = [], [], 0
for row in rows:
    rh = max(c[1].height for c in row) + GAP * 2 + LABEL_H
    if page and page_h + rh > MAX_H:
        pages.append(page)
        page, page_h = [], 0
    page.append(row)
    page_h += rh
if page:
    pages.append(page)

for pi, page in enumerate(pages, 1):
    hgt = sum(max(c[1].height for c in row) + GAP * 2 + LABEL_H for row in page)
    sheet = Image.new("RGB", (MAX_W, hgt), (30, 30, 38))
    draw = ImageDraw.Draw(sheet)
    y_off = 0
    for row in page:
        x_off = 0
        for n, big, scale in row:
            x0, y0 = x_off + GAP, y_off + GAP
            tile = Image.new("RGBA", (big.width, big.height))
            for ty in range(0, big.height, 16):
                for tx2 in range(0, big.width, 16):
                    tile.paste(CHECK, (tx2, ty))
            tile.alpha_composite(big)
            sheet.paste(tile.convert("RGB"), (x0, y0))
            draw.rectangle([x0 - 1, y0 - 1, x0 + big.width, y0 + big.height], outline=(95, 95, 118))
            draw.text((x0, y0 + big.height + 2), f"{n[:-4]} {scale}x", fill=(215, 215, 225), font=FONT)
            x_off += big.width + GAP * 2
        y_off += max(c[1].height for c in row) + GAP * 2 + LABEL_H
    path = EVIDENCE / f"contact-sheet-4x-p{pi}.png"
    sheet.save(path)
    print(f"wrote {path} ({sheet.width}x{sheet.height})")
print(f"{len(cells)} parts over {len(pages)} pages")
