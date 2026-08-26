"""Measure Issue #2 deterministic mask qualification and build visual proof."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageDraw, ImageFilter


BACKGROUNDS = (
    ("checker", None),
    ("black", (0, 0, 0)),
    ("white", (255, 255, 255)),
    ("gray", (127, 127, 127)),
    ("bright green", (0, 255, 0)),
)


def _pixels(image: Image.Image):
    """Use Pillow's current flat-pixel API with compatibility for 10.x."""

    flattened = getattr(image, "get_flattened_data", None)
    return flattened() if flattened is not None else image.getdata()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _checker(size: tuple[int, int], cell: int = 16) -> Image.Image:
    image = Image.new("RGB", size, (224, 224, 224))
    draw = ImageDraw.Draw(image)
    width, height = size
    for top in range(0, height, cell):
        for left in range(0, width, cell):
            if ((left // cell) + (top // cell)) % 2:
                draw.rectangle(
                    (left, top, min(left + cell - 1, width), min(top + cell - 1, height)),
                    fill=(176, 176, 176),
                )
    return image


def _binary_mask(image: Image.Image) -> Image.Image:
    return image.convert("L").point(lambda value: 255 if value >= 128 else 0)


def _outside_nonblack_pixels(output: Image.Image, truth: Image.Image) -> int:
    return sum(
        any(channel for channel in pixel) and not foreground
        for pixel, foreground in zip(
            _pixels(output.convert("RGB")),
            (bool(value) for value in _pixels(truth)),
            strict=True,
        )
    )


def _boundary(mask: Image.Image) -> Image.Image:
    expanded = mask.filter(ImageFilter.MaxFilter(3))
    contracted = mask.filter(ImageFilter.MinFilter(3))
    return ImageChops.difference(expanded, contracted).point(
        lambda value: 255 if value else 0
    )


def _geometry(mask: Image.Image) -> dict[str, Any]:
    width, height = mask.size
    count = 0
    sum_x = 0
    sum_y = 0
    left = width
    top = height
    right = -1
    bottom = -1
    for index, value in enumerate(_pixels(mask)):
        if not value:
            continue
        x = index % width
        y = index // width
        count += 1
        sum_x += x
        sum_y += y
        left = min(left, x)
        top = min(top, y)
        right = max(right, x)
        bottom = max(bottom, y)
    return {
        "foreground_pixels": count,
        "bbox": [left, top, right + 1, bottom + 1] if count else None,
        "centroid": [sum_x / count, sum_y / count] if count else None,
    }


def _compare_masks(truth: Image.Image, candidate: Image.Image) -> dict[str, Any]:
    truth_values = tuple(bool(value) for value in _pixels(truth))
    candidate_values = tuple(bool(value) for value in _pixels(candidate))
    false_opaque = sum(
        candidate_value and not truth_value
        for truth_value, candidate_value in zip(
            truth_values, candidate_values, strict=True
        )
    )
    false_transparent = sum(
        truth_value and not candidate_value
        for truth_value, candidate_value in zip(
            truth_values, candidate_values, strict=True
        )
    )
    intersection = sum(
        truth_value and candidate_value
        for truth_value, candidate_value in zip(
            truth_values, candidate_values, strict=True
        )
    )
    union = sum(
        truth_value or candidate_value
        for truth_value, candidate_value in zip(
            truth_values, candidate_values, strict=True
        )
    )
    truth_geometry = _geometry(truth)
    candidate_geometry = _geometry(candidate)
    if truth_geometry["centroid"] and candidate_geometry["centroid"]:
        centroid_drift = sum(
            (left - right) ** 2
            for left, right in zip(
                truth_geometry["centroid"],
                candidate_geometry["centroid"],
                strict=True,
            )
        ) ** 0.5
    else:
        centroid_drift = None
    truth_count = truth_geometry["foreground_pixels"]
    candidate_count = candidate_geometry["foreground_pixels"]
    scale_drift = (
        abs(candidate_count - truth_count) / truth_count
        if truth_count
        else (0.0 if not candidate_count else None)
    )
    truth_boundary = _boundary(truth)
    candidate_boundary = _boundary(candidate)
    boundary_truth = tuple(bool(value) for value in _pixels(truth_boundary))
    boundary_candidate = tuple(bool(value) for value in _pixels(candidate_boundary))
    boundary_difference = sum(
        left != right
        for left, right in zip(boundary_truth, boundary_candidate, strict=True)
    )
    boundary_union = sum(
        left or right
        for left, right in zip(boundary_truth, boundary_candidate, strict=True)
    )
    return {
        "false_opaque_pixels": false_opaque,
        "false_transparent_pixels": false_transparent,
        "outside_mask_changed_pixels": false_opaque,
        "silhouette_iou": intersection / union if union else 1.0,
        "centroid_drift_px": centroid_drift,
        "scale_drift": scale_drift,
        "boundary_symmetric_difference_pixels": boundary_difference,
        "boundary_error_fraction": (
            boundary_difference / boundary_union if boundary_union else 0.0
        ),
        "truth_geometry": truth_geometry,
        "candidate_geometry": candidate_geometry,
    }


def _write_background_sheet(
    cutouts: tuple[tuple[str, Image.Image], ...],
    output_path: Path,
) -> None:
    thumbnail_size = (320, 306)
    header = 44
    row_label_width = 96
    sheet = Image.new(
        "RGB",
        (
            row_label_width + thumbnail_size[0] * len(BACKGROUNDS),
            thumbnail_size[1] * len(cutouts) + header,
        ),
        (32, 34, 37),
    )
    draw = ImageDraw.Draw(sheet)
    for index, (label, _) in enumerate(BACKGROUNDS):
        draw.text(
            (row_label_width + index * thumbnail_size[0] + 12, 14),
            label,
            fill=(255, 255, 255),
        )
    for row, (candidate_label, cutout) in enumerate(cutouts):
        draw.text(
            (10, header + row * thumbnail_size[1] + 12),
            candidate_label,
            fill=(255, 255, 255),
        )
        for index, (_, color) in enumerate(BACKGROUNDS):
            background = (
                _checker(cutout.size)
                if color is None
                else Image.new("RGB", cutout.size, color)
            )
            background.paste(cutout.convert("RGB"), mask=cutout.getchannel("A"))
            background.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)
            left = row_label_width + index * thumbnail_size[0]
            top = (
                header
                + row * thumbnail_size[1]
                + (thumbnail_size[1] - background.height) // 2
            )
            sheet.paste(background, (left, top))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)


def evaluate_qualification(
    *,
    reference_path: Path,
    mask_path: Path,
    custom_mask_path: Path,
    custom_output_path: Path,
    core_output_path: Path,
    custom_cutout_path: Path,
    core_cutout_path: Path,
    contact_sheet_path: Path,
) -> dict[str, Any]:
    with Image.open(reference_path) as source:
        reference = source.convert("RGBA")
    with Image.open(mask_path) as source:
        truth = source.getchannel("L").point(lambda value: 255 if value >= 128 else 0)
    with Image.open(custom_mask_path) as source:
        custom_mask = _binary_mask(source)
    with Image.open(custom_output_path) as source:
        custom = source.convert("RGB")
    with Image.open(core_output_path) as source:
        core = source.convert("RGB")
    if not (
        reference.size == truth.size == custom_mask.size == custom.size == core.size
    ):
        raise ValueError("Reference, mask, and live output dimensions must match")

    core_mask = _binary_mask(reference.getchannel("A"))
    custom_cutout = custom.convert("RGBA")
    custom_cutout.putalpha(custom_mask)
    core_cutout = core.convert("RGBA")
    core_cutout.putalpha(core_mask)
    custom_cutout_path.parent.mkdir(parents=True, exist_ok=True)
    custom_cutout.save(custom_cutout_path)
    core_cutout.save(core_cutout_path)
    _write_background_sheet(
        (("custom", custom_cutout), ("core", core_cutout)),
        contact_sheet_path,
    )

    custom_metrics = _compare_masks(truth, custom_mask)
    core_metrics = _compare_masks(truth, core_mask)
    custom_metrics["outside_mask_changed_pixels"] = _outside_nonblack_pixels(
        custom, truth
    )
    core_metrics["outside_mask_changed_pixels"] = _outside_nonblack_pixels(
        core, truth
    )
    changed_rgb_pixels = sum(
        left != right
        for left, right in zip(_pixels(custom), _pixels(core), strict=True)
    )
    return {
        "schema_version": 1,
        "alpha_and_mask_convention": {
            "truth_foreground": "L >= 128 means editable/opaque foreground",
            "truth_background": "L < 128 means protected/transparent background",
            "comfyui_load_image_mask": "inverse alpha; the live graph uses InvertMask",
            "candidate_alpha": "each background row uses the actual candidate mask; StickerMaskBands thresholds soft input at the declared threshold",
            "assembly_output": "RGB composited onto black; transparency is carried by the candidate mask, not claimed for SaveImage output",
        },
        "dimensions": {
            "width": reference.width,
            "height": reference.height,
            "reference_mode": "RGBA",
            "live_output_mode": "RGB",
        },
        "custom_path": custom_metrics,
        "core_path": core_metrics,
        "custom_vs_core_changed_rgb_pixels": changed_rgb_pixels,
        "artifacts": {
            "reference": {"path": reference_path.as_posix(), "sha256": _sha256(reference_path)},
            "mask": {"path": mask_path.as_posix(), "sha256": _sha256(mask_path)},
            "custom_mask_output": {"path": custom_mask_path.as_posix(), "sha256": _sha256(custom_mask_path)},
            "custom_output": {"path": custom_output_path.as_posix(), "sha256": _sha256(custom_output_path)},
            "core_output": {"path": core_output_path.as_posix(), "sha256": _sha256(core_output_path)},
            "custom_transparent_cutout": {"path": custom_cutout_path.as_posix(), "sha256": _sha256(custom_cutout_path)},
            "core_transparent_cutout": {"path": core_cutout_path.as_posix(), "sha256": _sha256(core_cutout_path)},
            "background_contact_sheet": {"path": contact_sheet_path.as_posix(), "sha256": _sha256(contact_sheet_path)},
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--mask", type=Path, required=True)
    parser.add_argument("--custom-mask", type=Path, required=True)
    parser.add_argument("--custom-output", type=Path, required=True)
    parser.add_argument("--core-output", type=Path, required=True)
    parser.add_argument("--custom-cutout", type=Path, required=True)
    parser.add_argument("--core-cutout", type=Path, required=True)
    parser.add_argument("--contact-sheet", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate_qualification(
        reference_path=args.reference,
        mask_path=args.mask,
        custom_mask_path=args.custom_mask,
        custom_output_path=args.custom_output,
        core_output_path=args.core_output,
        custom_cutout_path=args.custom_cutout,
        core_cutout_path=args.core_cutout,
        contact_sheet_path=args.contact_sheet,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
