from __future__ import annotations

import json
import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageStat


def _require_binary(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise RuntimeError(f"{name} is required for video verification")
    return found


def probe(video: Path) -> dict[str, Any]:
    result = subprocess.run(
        [
            _require_binary("ffprobe"),
            "-v",
            "error",
            "-show_streams",
            "-show_format",
            "-of",
            "json",
            str(video),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def extract_frame(video: Path, destination: Path, position: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    args = [_require_binary("ffmpeg"), "-y", "-v", "error"]
    if position == "last":
        args += ["-sseof", "-0.08", "-i", str(video)]
    else:
        args += ["-i", str(video), "-ss", position]
    args += ["-frames:v", "1", str(destination)]
    subprocess.run(args, check=True)


def image_rmse(left: Path, right: Path) -> float:
    with Image.open(left).convert("RGB") as first, Image.open(right).convert("RGB") as second:
        if first.size != second.size:
            second = second.resize(first.size, Image.Resampling.LANCZOS)
        stat = ImageStat.Stat(ImageChops.difference(first, second))
        return math.sqrt(sum(value * value for value in stat.rms) / len(stat.rms))


def verify_video(
    video: Path,
    expected_duration: float,
    expected_size: tuple[int, int],
    expect_audio: bool,
    first_anchor: Path | None = None,
    last_anchor: Path | None = None,
    loop: bool = False,
) -> dict[str, Any]:
    metadata = probe(video)
    streams = metadata.get("streams", [])
    video_stream = next((stream for stream in streams if stream.get("codec_type") == "video"), None)
    if not video_stream:
        raise ValueError("Output has no video stream")
    actual_duration = float(
        metadata.get("format", {}).get("duration") or video_stream.get("duration")
    )
    checks: dict[str, Any] = {
        "duration": {
            "expected_seconds": expected_duration,
            "actual_seconds": actual_duration,
            "pass": abs(actual_duration - expected_duration) <= 0.35,
        },
        "dimensions": {
            "expected": list(expected_size),
            "actual": [video_stream.get("width"), video_stream.get("height")],
            "pass": [video_stream.get("width"), video_stream.get("height")] == list(expected_size),
        },
        "audio": {
            "expected": expect_audio,
            "actual": any(stream.get("codec_type") == "audio" for stream in streams),
        },
    }
    checks["audio"]["pass"] = checks["audio"]["expected"] == checks["audio"]["actual"]
    evidence = video.parent.parent / "verification"
    first = evidence / "first-output.png"
    last = evidence / "last-output.png"
    extract_frame(video, first, "0")
    extract_frame(video, last, "last")
    if first_anchor:
        checks["first_anchor_rmse"] = image_rmse(first_anchor, first)
    if last_anchor:
        checks["last_anchor_rmse"] = image_rmse(last_anchor, last)
    if loop:
        checks["loop_seam_rmse"] = image_rmse(first, last)
    checks["machine_checks_pass"] = all(
        value.get("pass", True) for value in checks.values() if isinstance(value, dict)
    )
    checks["requires_human_style_review"] = True
    return {"probe": metadata, "checks": checks}
