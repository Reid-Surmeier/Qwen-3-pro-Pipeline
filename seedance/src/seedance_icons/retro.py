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
    min_frames: int = 2
    max_frames: int = 8
    max_effective_fps: float = 10.0
    min_silhouette_iou: float = 0.90


def certify(report: dict, thresholds: RetroThresholds | None = None) -> dict:
    t = thresholds or RetroThresholds()
    checks = {
        "unique_frames_in_range": t.min_frames <= report["unique_frames"] <= t.max_frames,
        "effective_fps_ok": report["effective_fps"] <= t.max_effective_fps,
        "palette_locked": report["out_of_palette_pixels"] == 0,
        "silhouette_stable": report["min_silhouette_iou"] >= t.min_silhouette_iou,
    }
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
