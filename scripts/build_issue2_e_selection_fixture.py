"""Build the frozen final-e selection fixture for Issue #2."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import deque
from pathlib import Path
from typing import Any

from PIL import Image, ImageChops, ImageFilter


EXPECTED_SOURCE_EXPORT_SHA256 = (
    "c72cd0ec91e6e8490a5549dea015c0e866b126b674a3d255ffff071c06a5ff23"
)
EXPECTED_REFERENCE_SHA256 = (
    "7c8e8767f72b72ce4fa4c888507f5ad060003a6cab7802f3e0deef44c8de35d7"
)
SOURCE_SEARCH_BOX = (575, 230, 665, 335)
SOURCE_SEED = (610, 285)
TARGET_ORIGIN = (360, 640)
REGION_EXPANSION = 8
EXACT_GREEN = (0, 255, 0)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _is_blue_letter(pixel: tuple[int, int, int]) -> bool:
    red, green, blue = pixel
    return red < 90 and green < 135 and blue < 185 and (blue - red) > 35


def _connected_letter_mask(reference: Image.Image) -> Image.Image:
    rgb = reference.convert("RGB")
    left, top, right, bottom = SOURCE_SEARCH_BOX
    if not _is_blue_letter(rgb.getpixel(SOURCE_SEED)):
        raise ValueError("The frozen source seed no longer lands on the final e")
    selected = Image.new("L", rgb.size, 0)
    selected_pixels = selected.load()
    queue = deque([SOURCE_SEED])
    visited = {SOURCE_SEED}
    while queue:
        x, y = queue.popleft()
        if not _is_blue_letter(rgb.getpixel((x, y))):
            continue
        selected_pixels[x, y] = 255
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            candidate = (x + dx, y + dy)
            if (
                left <= candidate[0] < right
                and top <= candidate[1] < bottom
                and candidate not in visited
            ):
                visited.add(candidate)
                queue.append(candidate)
    return selected


def _expanded_region_mask(letter_mask: Image.Image) -> Image.Image:
    kernel = (REGION_EXPANSION * 2) + 1
    return letter_mask.filter(ImageFilter.MaxFilter(kernel))


def _translated_mask(
    source_mask: Image.Image,
    source_box: tuple[int, int, int, int],
) -> tuple[Image.Image, tuple[int, int, int, int]]:
    left, top, right, bottom = source_box
    glyph = source_mask.crop(source_box)
    target = Image.new("L", source_mask.size, 0)
    target.paste(glyph, TARGET_ORIGIN)
    target_box = (
        TARGET_ORIGIN[0],
        TARGET_ORIGIN[1],
        TARGET_ORIGIN[0] + (right - left),
        TARGET_ORIGIN[1] + (bottom - top),
    )
    return target, target_box


def _nonzero_pixels(mask: Image.Image) -> int:
    return sum(mask.histogram()[1:])


def build_fixture(
    reference_path: Path,
    source_export_path: Path,
    output_directory: Path,
) -> dict[str, Any]:
    reference_sha256 = _sha256(reference_path)
    source_export_sha256 = _sha256(source_export_path)
    if reference_sha256 != EXPECTED_REFERENCE_SHA256:
        raise ValueError("Reference 1 is not the authoritative Intel Inside crop")
    if source_export_sha256 != EXPECTED_SOURCE_EXPORT_SHA256:
        raise ValueError("Source export does not match FigJam node 67:710")
    with Image.open(reference_path) as source:
        reference = source.convert("RGBA")
    source_letter = _connected_letter_mask(reference)
    source_box = source_letter.getbbox()
    if source_box is None:
        raise ValueError("The final e selection is empty")
    target_letter, target_box = _translated_mask(source_letter, source_box)
    source_region = _expanded_region_mask(source_letter)
    target_region = _expanded_region_mask(target_letter)
    source_region_box = source_region.getbbox()
    target_region_box = target_region.getbbox()
    if source_region_box is None or target_region_box is None:
        raise ValueError("Expanded source or target region is empty")
    combined_region = ImageChops.lighter(source_region, target_region)

    green_key = Image.new("RGB", reference.size, (0, 0, 0))
    green_fill = Image.new("RGB", reference.size, EXACT_GREEN)
    green_key.paste(green_fill, mask=combined_region)

    guide = reference.convert("RGB")
    source_outline = source_letter.filter(ImageFilter.MaxFilter(13))
    target_outline = target_letter.filter(ImageFilter.MaxFilter(13))
    guide.paste(green_fill, mask=source_outline)
    guide.paste(green_fill, mask=target_outline)
    guide.paste(reference.convert("RGB"), mask=source_letter)
    target_green = Image.new("RGB", reference.size, EXACT_GREEN)
    guide.paste(target_green, mask=target_letter)

    output_directory.mkdir(parents=True, exist_ok=True)
    paths = {
        "source_letter_mask": output_directory / "source-e-mask-v001.png",
        "target_letter_mask": output_directory / "target-e-mask-v001.png",
        "source_region_mask": output_directory / "source-region-mask-v001.png",
        "target_region_mask": output_directory / "target-region-mask-v001.png",
        "combined_region_mask": output_directory / "combined-region-mask-v001.png",
        "green_key": output_directory / "green-selection-key-v001.png",
        "guide": output_directory / "green-selection-guide-v001.png",
    }
    source_letter.save(paths["source_letter_mask"])
    target_letter.save(paths["target_letter_mask"])
    source_region.save(paths["source_region_mask"])
    target_region.save(paths["target_region_mask"])
    combined_region.save(paths["combined_region_mask"])
    green_key.save(paths["green_key"])
    guide.save(paths["guide"])

    artifacts = {
        name: {"path": path.as_posix(), "sha256": _sha256(path)}
        for name, path in paths.items()
    }
    return {
        "schema_version": 1,
        "source_export": {
            "path": source_export_path.as_posix(),
            "sha256": source_export_sha256,
            "figjam_node_id": "67:710",
            "role": "source identity and crop provenance; not a Qwen input",
        },
        "reference": {
            "path": reference_path.as_posix(),
            "sha256": reference_sha256,
            "width": reference.width,
            "height": reference.height,
            "role": "authoritative Reference 1 for both matched Qwen conditions",
        },
        "selection": {
            "source_search_box": list(SOURCE_SEARCH_BOX),
            "source_seed": list(SOURCE_SEED),
            "source_letter_box": list(source_box),
            "source_region_box": list(source_region_box),
            "target_letter_box": list(target_box),
            "target_region_box": list(target_region_box),
            "region_expansion": REGION_EXPANSION,
            "green_rgb": list(EXACT_GREEN),
            "green_integer": 65280,
            "source_letter_pixels": _nonzero_pixels(source_letter),
            "target_letter_pixels": _nonzero_pixels(target_letter),
            "combined_region_pixels": _nonzero_pixels(combined_region),
        },
        "artifacts": artifacts,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--source-export", type=Path, required=True)
    parser.add_argument("--output-directory", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    args = parser.parse_args()
    manifest = build_fixture(args.reference, args.source_export, args.output_directory)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
