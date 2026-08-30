"""Deterministic retro-conformance pipeline and gate metrics.

Implements docs/research/retro-sprite-animation-authenticity.md §4: a video-model
output only becomes reviewable pixel-art animation after temporal quantization,
palette locking, and grid snapping — and the gate's real decisions (did the model
redraw the icon, did motion escape the tile) are measured, not eyeballed.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from PIL import Image

MATTE_TOLERANCE = 60  # per-channel distance from the matte color to count as background


class RetroError(RuntimeError):
    pass


def extract_palette(source: Image.Image, colors: int = 16) -> Image.Image:
    """Fixed indexed palette from the source crop; every output pixel must map into it."""
    return source.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT)


def snap_and_lock(frame: Image.Image, palette: Image.Image, grid: int) -> Image.Image:
    """Grid-snap (NEAREST downscale) then palette-lock with no dithering."""
    small = frame.convert("RGB").resize((grid, grid), Image.NEAREST)
    return small.quantize(palette=palette, dither=Image.Dither.NONE).convert("RGB")


def dedupe_frames(frames: list[Image.Image], max_frames: int) -> list[Image.Image]:
    """Drop consecutive identical frames, then cap at max_frames by even sampling."""
    unique: list[Image.Image] = []
    for frame in frames:
        if not unique or frame.tobytes() != unique[-1].tobytes():
            unique.append(frame)
    if len(unique) > max_frames:
        step = len(unique) / max_frames
        unique = [unique[int(i * step)] for i in range(max_frames)]
    return unique


def _mask(frame: Image.Image, matte: tuple[int, int, int]) -> list[bool]:
    data = frame.convert("RGB").getdata()
    return [
        max(abs(p[0] - matte[0]), abs(p[1] - matte[1]), abs(p[2] - matte[2])) > MATTE_TOLERANCE
        for p in data
    ]



def mask_fill_ratio(image: Image.Image, matte: tuple[int, int, int]) -> float:
    """How completely the non-matte pixels fill their own bounding box.

    Why this is checked, and why the obvious check does not work: `silhouette_iou`
    compares the *non-matte mask*. If an Anchor carries the icon on an opaque panel,
    the mask is that panel — a rectangle that never moves — so the IoU reads 1.0 no
    matter what the icon does inside it. A run then certifies with states visibly
    redrawn. Observed on the first four-state take, 2026-08-30.

    Measuring the overall matte fraction misses it, because a small panel inside a
    large matte field still leaves most of the frame as background. What distinguishes
    a panel from an icon is *shape*: a panel fills its bounding box completely, an icon
    does not. A silhouette that fills its own box is not a silhouette.
    """
    on = _mask(image, matte)
    w = image.width
    xs = [i % w for i, v in enumerate(on) if v]
    ys = [i // w for i, v in enumerate(on) if v]
    if not xs:
        return 0.0
    box = (max(xs) - min(xs) + 1) * (max(ys) - min(ys) + 1)
    return sum(on) / max(1, box)


MAX_ANCHOR_MASK_FILL = 0.92

# Two framings, two fidelity metrics, because the metric has to measure something the
# framing leaves free to vary.
#
#   "matte"  — the icon floats in the key colour. Its silhouette is the icon, so
#              silhouette IoU against the Anchor is meaningful, and an Anchor whose
#              silhouette is a rectangle is a bug (see mask_fill_ratio).
#   "filled" — the icon fills its tile edge to edge, the key colour is only a thin
#              border marking the edge. Every frame's silhouette is then the same
#              square whatever is drawn inside it, so silhouette IoU is worthless and
#              per-pixel identity against the Anchor is the only thing that can see
#              drift. Reid's rule, 2026-08-30: the key colour locks the square, it is
#              not the ground the icon sits in.
FRAME_MODES = ("matte", "filled")
MIN_ANCHOR_PIXEL_IDENTITY = 0.80


def ground_color(image: Image.Image) -> tuple[int, int, int]:
    """The most common colour in an image: in a filled tile, the icon's own ground."""
    data = list(image.convert("RGB").getdata())
    return max(set(data), key=data.count)


def ink_silhouette_iou(
    frame: Image.Image, anchor: Image.Image, ground: tuple[int, int, int]
) -> float:
    """Silhouette agreement measured against the icon's own ground, not the key colour.

    Two dead ends got us here, both of them metrics that measured everything except the
    drawing:

    - Keying on the key colour in a filled tile gives every frame the same square
      outline, so the IoU is 1.0 whatever is drawn inside it.
    - Per-pixel identity fails in the other direction. The video model re-renders rather
      than copying: a run whose magnifier never left the bust scored 0.457 overall and
      0.186 over the Anchor's ink, because the whole tile is redrawn a shade warmer and
      a fraction larger. No identity metric survives that, and demanding one would
      reject every run this model can produce.

    Keying on the ground instead makes the mask the drawing again, which is what the
    Issue #87 calibration was measuring all along.
    """
    return silhouette_iou(frame, anchor, ground)



def border_leak(frame: Image.Image, anchor: Image.Image, matte: tuple[int, int, int]) -> float:
    """Fraction of the Anchor's border ring the frame has drawn into.

    In filled framing the key colour is the tile's edge, so it is also the containment
    test: anything of the icon that appears out there has left the tile. The brief says
    so in words and the model does it anyway — observed on the 2026-08-30 sweep, where
    the magnifying glass crossed the border on several poses.

    Zero means the icon stayed inside. This is deterministic and cheap, unlike every
    fidelity metric tried for filled tiles, because it asks a question the framing
    actually answers.
    """
    a = _mask(anchor, matte)   # True where the Anchor draws
    f = _mask(frame, matte)
    ring = [i for i, on in enumerate(a) if not on]  # the Anchor's border
    if not ring:
        return 0.0
    return sum(1 for i in ring if f[i]) / len(ring)


MAX_BORDER_LEAK = 0.02
MIN_INNER_MARGIN = 0.03


def inner_margin(anchor: Image.Image, matte: tuple[int, int, int]) -> float:
    """Smallest gap between the drawing and the edge of its tile, as a fraction of width.

    A gesture needs somewhere to happen. An Anchor whose drawing already touches the
    tile edge leaves the only free space outside the tile, and that is where the model
    puts the movement — which then reads, correctly, as the icon leaving its box.

    This was a mistake in building the Anchor, not in the brief: cropping the icon to
    its own content and scaling it to fill the square threw away the margin the icon
    was drawn with. Observed 2026-08-30 on the sweep, where the drawing bbox and the
    tile bbox were identical on all four sides.
    """
    on = _mask(anchor, matte)
    w, h = anchor.size
    tile_x = [i % w for i, v in enumerate(on) if v]
    tile_y = [i // w for i, v in enumerate(on) if v]
    if not tile_x:
        return 0.0
    tile = (min(tile_x), min(tile_y), max(tile_x), max(tile_y))

    # the tile's ground, not the frame's: outside a filled tile the commonest colour is
    # the key colour, which would make every tile pixel count as ink
    px = list(anchor.convert("RGB").getdata())
    inside = [p for i, p in enumerate(px) if on[i]]
    ground = max(set(inside), key=inside.count) if inside else (0, 0, 0)
    ink = [
        (i % w, i // w)
        for i, p in enumerate(px)
        if on[i] and p != ground
    ]
    if not ink:
        return 0.0
    xs = [p[0] for p in ink]
    ys = [p[1] for p in ink]
    gaps = [
        min(xs) - tile[0],
        min(ys) - tile[1],
        tile[2] - max(xs),
        tile[3] - max(ys),
    ]
    return min(gaps) / max(1, tile[2] - tile[0] + 1)


def silhouette_iou(frame: Image.Image, reference: Image.Image, matte: tuple[int, int, int]) -> float:
    a, b = _mask(frame, matte), _mask(reference, matte)
    inter = sum(1 for x, y in zip(a, b) if x and y)
    union = sum(1 for x, y in zip(a, b) if x or y)
    return inter / union if union else 1.0


def identity_fraction(frame: Image.Image, source_snapped: Image.Image) -> float:
    """Fraction of identical pixels between conformed frame 0 and the snapped source."""
    a, b = frame.convert("RGB").getdata(), source_snapped.convert("RGB").getdata()
    same = sum(1 for x, y in zip(a, b) if x == y)
    return same / len(a)


@dataclass
class RetroThresholds:
    # Calibrated on the two 2026-08-27 board-icons batches (9 runs, 2 true failures):
    # silhouette IoU separates perfectly with no overlap (faithful 0.998-1.0 vs
    # redraw/escape 0.57-0.76) and is the certification decision. frame0_identity
    # does NOT separate reliably — it tracks tile paleness (faithful 0.71-0.84
    # overlapping the redraw's 0.72), so it is recorded as a diagnostic only.
    #
    # min_anchor_silhouette_iou applies only to State Set runs, where each state is
    # compared back to the Anchor rather than to its own first frame. Calibrated on the
    # two 2026-08-30 four-state takes of UI-01 Search: the states a human accepted
    # scored 0.955-0.979, the two a human rejected scored 0.466 and 0.529 — the same
    # clean separation the single-loop metric showed in Issue #87, with nothing in
    # between. Single-loop reports do not carry the key and are certified exactly as
    # before.
    min_frames: int = 2
    max_frames: int = 8
    max_effective_fps: float = 10.0
    min_silhouette_iou: float = 0.90
    min_anchor_silhouette_iou: float = 0.90
    # filled-square runs cannot use a silhouette metric at all: every frame's outline is
    # the same tile. Per-pixel identity against the Anchor is what remains. The 0.80
    # starting point is NOT calibrated against human verdicts yet — it is a placeholder
    # chosen so a one-pixel shift of one element passes and a redraw does not.
    min_anchor_pixel_identity: float = 0.80  # kept for reporting; no longer a check


def certify(report: dict, thresholds: RetroThresholds | None = None) -> dict:
    t = thresholds or RetroThresholds()
    checks = {
        "unique_frames_in_range": t.min_frames <= report["unique_frames"] <= t.max_frames,
        "effective_fps_ok": report["effective_fps"] <= t.max_effective_fps,
        "palette_locked": report["out_of_palette_pixels"] == 0,
        "silhouette_stable": report["min_silhouette_iou"] >= t.min_silhouette_iou,
    }
    mode = report.get("frame_mode")
    if mode == "filled":  # noqa: SIM102 - the comment below is the decision
        # Deliberately no automatic fidelity check. Four metrics were tried against the
        # 2026-08-30 filled-tile run and not one of them separates a good state from a
        # bad one:
        #
        #   silhouette vs the key colour   every frame is the same square -> all 1.0
        #   per-pixel identity             the model re-renders, it never copies -> 0.457
        #   identity over the Anchor's ink  same reason, worse -> 0.186
        #   silhouette vs the icon's ground the generated ground shifts hue -> all 1.0
        #
        # Shipping a fifth guess would be shipping a number that certifies whatever it
        # is handed, which is exactly the failure this gate exists to prevent. Until a
        # metric is calibrated against human verdicts on filled tiles, filled runs are
        # certified by a person looking at the state-set GIF.
        checks["human_gate_required"] = False
        checks["stayed_in_the_tile"] = report["max_border_leak"] <= MAX_BORDER_LEAK
    elif "anchor_silhouette_iou" in report:
        checks["matches_anchor"] = (
            report["anchor_silhouette_iou"] >= t.min_anchor_silhouette_iou
        )
    return {
        "checks": checks,
        "diagnostics": {"frame0_identity": report["frame0_identity"]},
        "certified": all(checks.values()),
    }


def conform(
    video: Path,
    reference: Path,
    out_dir: Path,
    *,
    fps: int = 6,
    max_frames: int = 8,
    grid: int = 160,
    delivery: int = 640,
    colors: int = 16,
    matte: tuple[int, int, int] = (0, 255, 0),
) -> dict:
    """Run the full conformance pipeline; write frames + GIF + report, return the report.

    reference is the exact first-frame anchor (icon on matte at delivery size): the
    palette, silhouette baseline, and identity check all derive from it.
    """
    if shutil.which("ffmpeg") is None:
        raise RetroError("ffmpeg is required for retro conformance")
    out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", str(video),
             "-vf", f"fps={fps}", f"{tmp}/f%04d.png"],
            check=True,
        )
        raw = [Image.open(p).convert("RGB") for p in sorted(Path(tmp).glob("f*.png"))]
    if not raw:
        raise RetroError(f"No frames extracted from {video}")
    duration = len(raw) / fps
    ref = Image.open(reference).convert("RGB")
    if ref.size != (delivery, delivery):
        ref = ref.resize((delivery, delivery), Image.NEAREST)
    palette = extract_palette(ref, colors)
    snapped = dedupe_frames([snap_and_lock(f, palette, grid) for f in raw], max_frames)
    source_snapped = snap_and_lock(ref, palette, grid)

    palette_rgb = {tuple(palette.getpalette()[i * 3 : i * 3 + 3]) for i in range(colors)}
    out_of_palette = sum(
        1 for frame in snapped for p in frame.getdata() if tuple(p) not in palette_rgb
    )
    ious = [silhouette_iou(f, snapped[0], matte) for f in snapped[1:]] or [1.0]
    report = {
        "unique_frames": len(snapped),
        "effective_fps": round(len(snapped) / duration, 2),
        "out_of_palette_pixels": out_of_palette,
        "min_silhouette_iou": round(min(ious), 4),
        "frame0_identity": round(identity_fraction(snapped[0], source_snapped), 4),
        "grid": grid,
        "palette_colors": colors,
        "reference": str(reference),
    }
    report.update(certify(report))

    for i, frame in enumerate(snapped):
        frame.resize((delivery, delivery), Image.NEAREST).save(out_dir / f"frame{i:02d}.png")
    hold = max(1, round(24 / fps))
    subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(fps),
         "-i", f"{out_dir}/frame%02d.png",
         "-vf", "split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=none",
         str(out_dir / "conformed.gif")],
        check=True,
    )
    report["hold_frames_at_24fps"] = hold
    (out_dir / "retro-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


DEFAULT_STATE_MAP = {
    "idle": (0.00, 0.25),
    "hover": (0.25, 0.50),
    "pressed": (0.50, 0.75),
    "settled": (0.75, 1.00),
}


def parse_state_map(raw: Mapping[str, Any] | None) -> dict[str, tuple[float, float]]:
    """Read a brief's state_map ({"idle": "0.00-0.25", ...}) into fractional spans.

    Spans must be within [0, 1], ordered, non-overlapping, and cover the whole take;
    a gap or an overlap means the cut is ambiguous, which is a brief bug, not a
    rounding detail.
    """
    if not raw:
        return dict(DEFAULT_STATE_MAP)
    spans: dict[str, tuple[float, float]] = {}
    for name, value in raw.items():
        if isinstance(value, (list, tuple)) and len(value) == 2:
            lo, hi = float(value[0]), float(value[1])
        else:
            text = str(value).replace("\u2013", "-")
            parts = [p for p in text.split("-") if p.strip()]
            if len(parts) != 2:
                raise RetroError(f"state_map[{name!r}] is not a 'lo-hi' span: {value!r}")
            lo, hi = float(parts[0]), float(parts[1])
        if not (0.0 <= lo < hi <= 1.0):
            raise RetroError(f"state_map[{name!r}] span {lo}-{hi} is not inside 0..1")
        spans[name] = (lo, hi)
    ordered = sorted(spans.items(), key=lambda kv: kv[1][0])
    for (a_name, (_, a_hi)), (b_name, (b_lo, _)) in zip(ordered, ordered[1:]):
        if abs(a_hi - b_lo) > 1e-6:
            raise RetroError(
                f"state_map has a gap or overlap between {a_name!r} and {b_name!r} "
                f"({a_hi} then {b_lo}); the cut would be ambiguous"
            )
    if abs(ordered[0][1][0]) > 1e-6 or abs(ordered[-1][1][1] - 1.0) > 1e-6:
        raise RetroError("state_map must cover the whole take, from 0.0 to 1.0")
    return dict(ordered)


def _segment(frames: list[Image.Image], span: tuple[float, float]) -> list[Image.Image]:
    """Frames inside a fractional span, always at least one frame."""
    lo, hi = span
    a = int(round(lo * len(frames)))
    b = int(round(hi * len(frames)))
    return frames[a:b] or frames[a : a + 1] or frames[-1:]



def ink_centroid(frame: Image.Image, matte: tuple[int, int, int]) -> tuple[float, float] | None:
    """Centre of mass of everything that is not matte and not the tile's ground."""
    on = _mask(frame, matte)
    px = list(frame.convert("RGB").getdata())
    inside = [p for i, p in enumerate(px) if on[i]]
    if not inside:
        return None
    ground = max(set(inside), key=inside.count)
    w = frame.width
    pts = [(i % w, i // w) for i, p in enumerate(px) if on[i] and p != ground]
    if not pts:
        return None
    return (sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts))


def step_evenness(frames: list[Image.Image], matte: tuple[int, int, int]) -> float:
    """Spread of per-step travel, relative to its own mean. Lower is steadier.

    A stepped animation is supposed to look stepped; it is not supposed to look
    lurching. The difference is measurable. Measured on the 2026-08-30 sweeps, the
    per-frame travel of the moving element was

        0 0 0 0 0 1 26 66 10 13 9 11 6 14 24 98 13 73 32 17 26 40 9 41 0 0 0 ...

    - long stretches where nothing happens, then leaps of a hundred pixels. That is
    exactly what "jerky" describes, and holding each frame for an equal time cannot fix
    it, because the unevenness is in the content rather than the timing.
    """
    cents = [ink_centroid(f, matte) for f in frames]
    steps = [
        ((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5
        for a, b in zip(cents, cents[1:])
        if a and b
    ]
    if len(steps) < 2:
        return 0.0
    mean = sum(steps) / len(steps)
    if mean <= 1e-9:
        return 0.0
    var = sum((s - mean) ** 2 for s in steps) / len(steps)
    return (var ** 0.5) / mean


def resample_by_travel(
    frames: list[Image.Image], count: int, matte: tuple[int, int, int]
) -> list[Image.Image]:
    """Pick `count` frames spaced evenly along the path the element travels.

    Deduping by time keeps whatever pacing the model produced, and the model paces
    badly: it dwells, then lunges. Sampling by distance instead puts the same amount of
    movement between every pair of output frames, which is what a hand-authored sprite
    cycle does - the frame table exists precisely to make the steps regular.

    This only ever *selects* frames the model drew. Nothing is interpolated, blended or
    invented.
    """
    if count >= len(frames) or count < 2:
        return frames
    cents = [ink_centroid(f, matte) for f in frames]
    cum = [0.0]
    for a, b in zip(cents, cents[1:]):
        d = (((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5) if (a and b) else 0.0
        cum.append(cum[-1] + d)
    total = cum[-1]
    if total <= 1e-9:
        return dedupe_frames(frames, count)
    targets = [total * i / (count - 1) for i in range(count)]
    picked: list[int] = []
    j = 0
    for t in targets:
        while j < len(cum) - 1 and cum[j] < t:
            j += 1
        if not picked or j != picked[-1]:
            picked.append(j)
    return [frames[i] for i in picked]


def conform_states(
    video: Path,
    reference: Path,
    out_dir: Path,
    *,
    state_map: Mapping[str, Any] | None = None,
    fps: int = 6,
    max_frames: int = 8,
    grid: int = 160,
    delivery: int = 640,
    colors: int = 16,
    matte: tuple[int, int, int] = (0, 255, 0),
    settle_trim: float = 0.25,
    frame_mode: str = "matte",
    state_hold_ms: int = 134,
    cycle_poses: int = 12,
    pose_hold_ms: int = 100,
) -> dict:
    """Conform one multi-state take into a State Set: one certified directory per state.

    The single-loop `conform` path is untouched — its calibration against Issue #87
    depends on it. This is the four-state sibling: same reduction, same thresholds,
    cut first.

    `settle_trim` drops the leading fraction of each segment before conformance, so a
    state's frames come from the part where the pose is *held* rather than from the
    step into it. A brief that asks for instant steps still emits a transition frame
    or two at each boundary, and those frames are neither state.
    """
    if shutil.which("ffmpeg") is None:
        raise RetroError("ffmpeg is required for retro conformance")
    if frame_mode not in FRAME_MODES:
        raise RetroError(f"frame_mode must be one of {FRAME_MODES}, not {frame_mode!r}")
    spans = parse_state_map(state_map)
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-i", str(video),
             "-vf", f"fps={fps}", f"{tmp}/f%04d.png"],
            check=True,
        )
        raw = [Image.open(p).convert("RGB") for p in sorted(Path(tmp).glob("f*.png"))]
    if not raw:
        raise RetroError(f"No frames extracted from {video}")

    ref = Image.open(reference).convert("RGB")
    if ref.size != (delivery, delivery):
        ref = ref.resize((delivery, delivery), Image.NEAREST)
    palette = extract_palette(ref, colors)
    source_snapped = snap_and_lock(ref, palette, grid)
    anchor_fill = mask_fill_ratio(source_snapped, matte)
    if frame_mode == "filled":
        margin = inner_margin(source_snapped, matte)
        if margin < MIN_INNER_MARGIN:
            raise RetroError(
                f"Anchor {reference.name} leaves the drawing only {margin:.1%} of the "
                f"tile's width as margin (min {MIN_INNER_MARGIN:.0%}). A gesture needs "
                f"somewhere to happen inside the tile; with none, the only free space is "
                f"outside it, and that is where the movement goes. Rebuild the Anchor "
                f"keeping the margin the icon was drawn with."
            )
    if frame_mode == "matte" and anchor_fill > MAX_ANCHOR_MASK_FILL:
        raise RetroError(
            f"Anchor {reference.name} fills {anchor_fill:.1%} of its own bounding box, so its "
            f"silhouette is effectively a rectangle — the icon is sitting on an opaque panel "
            f"rather than on the matte. Every silhouette metric would measure that panel and "
            f"every state would certify regardless of what it drew. Key the icon's own "
            f"background to the matte first."
        )
    palette_rgb = {tuple(palette.getpalette()[i * 3 : i * 3 + 3]) for i in range(colors)}

    states: dict[str, dict] = {}
    for name, span in spans.items():
        segment = _segment(raw, span)
        if settle_trim > 0 and len(segment) > 2:
            segment = segment[int(len(segment) * settle_trim) :] or segment[-1:]
        duration = len(segment) / fps
        snapped = dedupe_frames([snap_and_lock(f, palette, grid) for f in segment], max_frames)
        out_of_palette = sum(
            1 for frame in snapped for p in frame.getdata() if tuple(p) not in palette_rgb
        )
        ious = [silhouette_iou(f, snapped[0], matte) for f in snapped[1:]] or [1.0]
        report = {
            "state": name,
            "span": list(span),
            "source_frames": len(segment),
            "unique_frames": len(snapped),
            "effective_fps": round(len(snapped) / duration, 2) if duration else 0.0,
            "out_of_palette_pixels": out_of_palette,
            "min_silhouette_iou": round(min(ious), 4),
            "frame0_identity": round(identity_fraction(snapped[0], source_snapped), 4),
            "anchor_silhouette_iou": round(silhouette_iou(snapped[0], source_snapped, matte), 4),
            "anchor_pixel_identity": round(identity_fraction(snapped[0], source_snapped), 4),
            "max_border_leak": round(
                max(border_leak(f, source_snapped, matte) for f in snapped), 4
            ),
            "anchor_ink_silhouette_iou": round(
                ink_silhouette_iou(snapped[0], source_snapped, ground_color(source_snapped)), 4
            ),
            "frame_mode": frame_mode,
            "grid": grid,
            "palette_colors": colors,
            "reference": str(reference),
        }
        report.update(certify(report))

        state_dir = out_dir / name
        state_dir.mkdir(parents=True, exist_ok=True)
        for i, frame in enumerate(snapped):
            frame.resize((delivery, delivery), Image.NEAREST).save(state_dir / f"frame{i:02d}.png")
        subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(fps),
             "-i", f"{state_dir}/frame%02d.png",
             "-vf", "split[a][b];[a]palettegen=max_colors=64[p];[b][p]paletteuse=dither=none",
             str(state_dir / "conformed.gif")],
            check=True,
        )
        report["hold_frames_at_24fps"] = max(1, round(24 / fps))
        (state_dir / "retro-report.json").write_text(json.dumps(report, indent=2) + "\n")
        states[name] = report

    # The artifact a person actually judges: the four states cycling at the era cadence,
    # each held, substituted instantly. Per-state GIFs show what a state contains; this
    # shows what the icon does.
    cycle = [
        Image.open(out_dir / name / "frame00.png").convert("RGB") for name in spans
    ]
    cycle[0].save(
        out_dir / "state-set.gif",
        save_all=True,
        append_images=cycle[1:],
        duration=state_hold_ms,
        loop=0,
        optimize=False,
    )

    # The whole gesture as one evenly-beaten cycle. Concatenating the four states'
    # frames does not work: each state is deduped inside its own quarter, so the groups
    # carry different numbers of poses and different amounts of change, and the result
    # reads as jerky even though every frame is correct. Deduping the take as a whole
    # and holding every pose for the same time is what the era's frame tables do.
    snapped_all = [snap_and_lock(f, palette, grid) for f in raw]
    whole = resample_by_travel(snapped_all, cycle_poses, matte)
    whole_out = [f.resize((delivery, delivery), Image.NEAREST) for f in whole]
    whole_out[0].save(
        out_dir / "full-cycle.gif",
        save_all=True,
        append_images=whole_out[1:],
        duration=pose_hold_ms,
        loop=0,
        optimize=False,
    )

    summary = {
        "states": states,
        "state_set_gif": str(out_dir / "state-set.gif"),
        "full_cycle_gif": str(out_dir / "full-cycle.gif"),
        "cycle_poses": len(whole),
        "pose_hold_ms": pose_hold_ms,
        "step_evenness_raw": round(step_evenness(snapped_all, matte), 3),
        "step_evenness_resampled": round(step_evenness(whole, matte), 3),
        "step_evenness_note": (
            "spread of per-step travel over its own mean; lower is steadier. The raw "
            "figure is the model's own pacing, the resampled figure is what the cycle "
            "GIF plays. Sampling by distance rather than by time is what closes the gap."
        ),
        "max_border_leak": max(r["max_border_leak"] for r in states.values())
        if states
        else 0.0,
        "state_hold_ms": state_hold_ms,
        "state_order": list(spans),
        "total_source_frames": len(raw),
        "anchor_mask_fill_ratio": round(anchor_fill, 4),
        "anchor_inner_margin": round(inner_margin(source_snapped, matte), 4),
        "settle_trim": settle_trim,
        "frame_mode": frame_mode,
        "certified": all(r["certified"] for r in states.values()),
        "uncertified_states": [n for n, r in states.items() if not r["certified"]],
        "human_gate_required": frame_mode == "filled",
        "human_gate_note": (
            "filled framing has no calibrated fidelity metric: silhouette measures the "
            "tile, identity measures a model that re-renders rather than copies. A "
            "person judges states/state-set.gif against the Anchor. `certified` here "
            "means the cadence and palette checks passed, not that the picture is right."
        )
        if frame_mode == "filled"
        else None,
        "anchor_silhouette_iou_note": (
            "anchor_silhouette_iou compares each state's first frame to the Anchor, and is a "
            "certification check for State Set runs. Calibrated on the two 2026-08-30 "
            "four-state takes of UI-01 Search: accepted states 0.955-0.979, rejected states "
            "0.466 and 0.529. Recalibrate as batches accumulate; the threshold lives in "
            "RetroThresholds.min_anchor_silhouette_iou."
        ),
    }
    (out_dir / "states-report.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
