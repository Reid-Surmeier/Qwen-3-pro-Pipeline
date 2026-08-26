"""Measure the frozen Issue #2 mask-reference comparison outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image


TARGET_GREEN = (0, 255, 0)
CONDITIONS = (
    "b0-reference-only",
    "b1-plain-mask",
    "b2-ownership-guide",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_near_green(pixel: tuple[int, int, int]) -> bool:
    red, green, blue = pixel
    return green >= 180 and green - red >= 150 and green - blue >= 150


def measure_image(path: Path, *, border_width: int = 32) -> dict[str, Any]:
    """Return deterministic green-background and subject-geometry measurements."""

    with Image.open(path) as source:
        image = source.convert("RGB")
        width, height = image.size
        pixels = image.load()

        exact_green = 0
        near_green = 0
        border_near_green = 0
        border_pixels = 0
        border_error = 0
        subject_pixels = 0
        subject_sum_x = 0
        subject_sum_y = 0
        subject_left = width
        subject_top = height
        subject_right = -1
        subject_bottom = -1

        effective_border = max(1, min(border_width, width // 2, height // 2))
        for y in range(height):
            for x in range(width):
                pixel = pixels[x, y]
                is_near = _is_near_green(pixel)
                if pixel == TARGET_GREEN:
                    exact_green += 1
                if is_near:
                    near_green += 1
                else:
                    subject_pixels += 1
                    subject_sum_x += x
                    subject_sum_y += y
                    subject_left = min(subject_left, x)
                    subject_top = min(subject_top, y)
                    subject_right = max(subject_right, x)
                    subject_bottom = max(subject_bottom, y)

                if (
                    x < effective_border
                    or x >= width - effective_border
                    or y < effective_border
                    or y >= height - effective_border
                ):
                    border_pixels += 1
                    border_near_green += int(is_near)
                    border_error += sum(
                        abs(channel - target)
                        for channel, target in zip(pixel, TARGET_GREEN, strict=True)
                    )

    total = width * height
    if subject_pixels:
        subject_bbox = [
            subject_left,
            subject_top,
            subject_right + 1,
            subject_bottom + 1,
        ]
        subject_bbox_fraction = [
            subject_left / width,
            subject_top / height,
            (subject_right + 1) / width,
            (subject_bottom + 1) / height,
        ]
        subject_centroid = [
            subject_sum_x / subject_pixels / width,
            subject_sum_y / subject_pixels / height,
        ]
    else:
        subject_bbox = None
        subject_bbox_fraction = None
        subject_centroid = None

    return {
        "path": path.as_posix(),
        "sha256": _sha256(path),
        "width": width,
        "height": height,
        "exact_green_fraction": exact_green / total,
        "near_green_fraction": near_green / total,
        "border_near_green_fraction": border_near_green / border_pixels,
        "border_mean_absolute_error_to_00ff00": border_error / (border_pixels * 3),
        "subject_fraction": subject_pixels / total,
        "subject_bbox": subject_bbox,
        "subject_bbox_fraction": subject_bbox_fraction,
        "subject_centroid_fraction": subject_centroid,
    }


def evaluate(root: Path) -> dict[str, Any]:
    conditions: dict[str, Any] = {}
    for condition in CONDITIONS:
        paths = sorted((root / condition).glob("*.png"))
        if len(paths) != 2:
            raise ValueError(f"Expected exactly two PNG outputs for {condition}")
        images = [measure_image(path) for path in paths]
        conditions[condition] = {
            "images": images,
            "mean_near_green_fraction": sum(
                image["near_green_fraction"] for image in images
            )
            / len(images),
            "mean_border_near_green_fraction": sum(
                image["border_near_green_fraction"] for image in images
            )
            / len(images),
            "mean_subject_fraction": sum(
                image["subject_fraction"] for image in images
            )
            / len(images),
        }
    return {
        "schema_version": 1,
        "method": {
            "target_background_rgb": list(TARGET_GREEN),
            "near_green_rule": (
                "green >= 180 and green-red >= 150 and green-blue >= 150"
            ),
            "border_width_pixels": 32,
            "limitations": [
                "These measurements test background uniformity and geometry only.",
                "They do not establish text correctness or subjective visual fidelity.",
            ],
        },
        "conditions": conditions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
