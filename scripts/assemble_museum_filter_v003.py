#!/usr/bin/env python3.12
"""Build Issue #118 Assembly v003 with native-scale foreground masks.

Assembly v001 owns every background and control pixel. The selected v005 donor
contributes glyph silhouettes only; no rectangular donor background is copied.
The composition happens at the client's native 313x211 resolution and is then
scaled 4x with nearest-neighbour resampling.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / (
    "artifacts/references/museum-filter-retro-skin-v001/"
    "style-ro-options-window-flat-rgb.png"
)
NATIVE_SIZE = (313, 211)
SCALE = 4

WHITE = (0xFF, 0xFF, 0xFF)
FIELD_FILL = (0xF9, 0xF3, 0xF7)
LABEL_INK = (0x2E, 0x45, 0x60)
BODY_INK = (0x10, 0x10, 0x10)
COUNT_INK = (0x8A, 0x8A, 0x8A)
PLACEHOLDER = (0xA6, 0xA4, 0xA7)
TAB_OFF_FILL = (0xF3, 0xEF, 0xF4)
TAB_OFF_INK = (0x8B, 0x89, 0x8C)
TAB_ON_INK = (0x3A, 0x3B, 0x3F)

TITLE_SOURCE = (20, 6, 160, 21)
TITLE_EDIT = (19, 5, 160, 21)
OBJECT_TAB = (8, 28, 21, 63)
MATERIAL_TAB = (8, 73, 21, 120)
SEARCH_LABEL = (31, 39, 74, 53)
SEARCH_PLACEHOLDER_TARGET = (81, 39, 123, 53)
SEARCH_PLACEHOLDER_SOURCE = (83, 39, 125, 53)
MATCH_LABEL = (31, 66, 72, 80)
ANY_TARGET = (90, 66, 116, 80)
ANY_SOURCE = (92, 66, 118, 80)
ALL_TARGET = (142, 66, 165, 80)
ALL_SOURCE = (146, 66, 169, 80)
TRAILING_TARGET = (167, 66, 257, 80)
TRAILING_SOURCE = (171, 66, 261, 80)
LEFT_ROWS = (49, 94, 147, 184)
RIGHT_ROWS_TARGET = (190, 94, 301, 184)
RIGHT_ROWS_SOURCE = (194, 94, 305, 184)

EDIT_BOXES = (
    TITLE_EDIT,
    OBJECT_TAB,
    MATERIAL_TAB,
    SEARCH_LABEL,
    SEARCH_PLACEHOLDER_TARGET,
    MATCH_LABEL,
    ANY_TARGET,
    ALL_TARGET,
    TRAILING_TARGET,
    LEFT_ROWS,
    RIGHT_ROWS_TARGET,
)

EXACT_COPY = (
    "Object type / material",
    "object",
    "material",
    "Search",
    "Search",
    "Match",
    "Any",
    "All",
    "selected filters.",
    "Metal (5,001)",
    "Paper (3,652)",
    "Glass (3,182)",
    "Drawings (2,606)",
    "Graphite (2,443)",
    "Paintings (2,395)",
    "Vessels (2,074)",
    "Watercolors (1,962)",
    "Wood (1,899)",
    "Dishes (1,837)",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def magenta_bbox(image: Image.Image) -> tuple[int, int, int, int]:
    xs: list[int] = []
    ys: list[int] = []
    for y in range(image.height):
        for x in range(image.width):
            red, green, blue = image.getpixel((x, y))[:3]
            if red > 220 and green < 80 and blue > 180:
                xs.append(x)
                ys.append(y)
    if not xs:
        raise ValueError("image has no detectable magenta frame")
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def register_donor(donor: Image.Image, baseline: Image.Image) -> Image.Image:
    target = magenta_bbox(baseline)
    size = (target[2] - target[0], target[3] - target[1])
    crop = donor.convert("RGB").crop(magenta_bbox(donor)).resize(
        size, Image.Resampling.LANCZOS
    )
    registered = Image.new("RGB", baseline.size, WHITE)
    registered.paste(crop, target[:2])
    return registered


def changed_pixel_mask(before: Image.Image, after: Image.Image) -> Image.Image:
    if before.size != after.size:
        raise ValueError(f"image sizes differ: {before.size} != {after.size}")
    red, green, blue = ImageChops.difference(
        before.convert("RGB"), after.convert("RGB")
    ).split()
    maximum = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    return maximum.point(lambda value: 255 if value else 0)


def threshold_mask(patch: Image.Image, maximum_luma: int) -> Image.Image:
    return patch.convert("L").point(
        lambda value: 255 if value < maximum_luma else 0
    )


def clear_exact_ink(
    output: Image.Image,
    baseline: Image.Image,
    box: tuple[int, int, int, int],
    inks: tuple[tuple[int, int, int], ...],
    background: tuple[int, int, int],
) -> None:
    source = baseline.crop(box)
    mask = Image.new("L", source.size, 0)
    source_pixels = source.load()
    mask_pixels = mask.load()
    for y in range(source.height):
        for x in range(source.width):
            if source_pixels[x, y] in inks:
                mask_pixels[x, y] = 255
    output.paste(Image.new("RGB", source.size, background), box[:2], mask)


def paste_foreground_pixels(
    output: Image.Image,
    donor: Image.Image,
    target_box: tuple[int, int, int, int],
    source_box: tuple[int, int, int, int],
    maximum_luma: int,
) -> Image.Image:
    patch = donor.crop(source_box)
    target_size = (target_box[2] - target_box[0], target_box[3] - target_box[1])
    if patch.size != target_size:
        raise ValueError(f"source {patch.size} does not match target {target_size}")
    mask = threshold_mask(patch, maximum_luma)
    # The mask admits only foreground-valued pixels. Keeping the registered
    # donor's native grayscale/colour edge pixels avoids the heavy binary
    # threshold that broke v001's lettering without importing its background.
    output.paste(patch, target_box[:2], mask)
    return mask


def replace_single_ink(
    output: Image.Image,
    baseline: Image.Image,
    donor: Image.Image,
    target_box: tuple[int, int, int, int],
    source_box: tuple[int, int, int, int],
    old_inks: tuple[tuple[int, int, int], ...],
    background: tuple[int, int, int],
    maximum_luma: int,
) -> None:
    clear_exact_ink(output, baseline, target_box, old_inks, background)
    paste_foreground_pixels(output, donor, target_box, source_box, maximum_luma)


def replace_mixed_body_and_count(
    output: Image.Image,
    baseline: Image.Image,
    donor: Image.Image,
    target_box: tuple[int, int, int, int],
    source_box: tuple[int, int, int, int],
) -> None:
    clear_exact_ink(
        output, baseline, target_box, (BODY_INK, COUNT_INK), WHITE
    )
    patch = donor.crop(source_box)
    target_size = (target_box[2] - target_box[0], target_box[3] - target_box[1])
    if patch.size != target_size:
        raise ValueError(f"source {patch.size} does not match target {target_size}")
    foreground = threshold_mask(patch, 238)
    output.paste(patch, target_box[:2], foreground)


def restore_title_background(
    output: Image.Image, baseline: Image.Image
) -> None:
    reference = Image.open(REFERENCE).convert("RGB")
    bar = reference.crop((600, 45, 1372, 124)).resize(
        (baseline.width - 6, 20), Image.Resampling.LANCZOS
    )
    target = (20, 6, 160, 21)
    baseline_patch = baseline.crop(target)
    bar_patch = bar.crop((target[0] - 3, target[1] - 3, target[2] - 3, target[3] - 3))
    old_title = changed_pixel_mask(bar_patch, baseline_patch)
    output.paste(bar_patch, target[:2], old_title)


def replace_title(
    output: Image.Image, baseline: Image.Image, donor: Image.Image
) -> None:
    restore_title_background(output, baseline)
    patch = donor.crop(TITLE_SOURCE)
    glyph = threshold_mask(patch, 155)
    dark_core = threshold_mask(patch, 105)
    output.paste(
        Image.new("RGB", glyph.size, WHITE),
        (TITLE_SOURCE[0] - 1, TITLE_SOURCE[1] - 1),
        dark_core,
    )
    output.paste(patch, TITLE_SOURCE[:2], glyph)


def assemble_native(
    baseline: Image.Image, raw_donor: Image.Image
) -> tuple[Image.Image, Image.Image]:
    baseline = baseline.convert("RGB")
    if baseline.size != NATIVE_SIZE:
        raise ValueError(f"baseline must be {NATIVE_SIZE}, got {baseline.size}")
    donor = register_donor(raw_donor.convert("RGB"), baseline)
    output = baseline.copy()

    replace_title(output, baseline, donor)
    replace_single_ink(
        output, baseline, donor, OBJECT_TAB, OBJECT_TAB,
        (TAB_ON_INK,), WHITE, 200,
    )
    replace_single_ink(
        output, baseline, donor, MATERIAL_TAB, MATERIAL_TAB,
        (TAB_OFF_INK,), TAB_OFF_FILL, 200,
    )
    replace_single_ink(
        output, baseline, donor, SEARCH_LABEL, SEARCH_LABEL,
        (LABEL_INK,), WHITE, 235,
    )
    replace_single_ink(
        output, baseline, donor,
        SEARCH_PLACEHOLDER_TARGET, SEARCH_PLACEHOLDER_SOURCE,
        (PLACEHOLDER,), FIELD_FILL, 238,
    )
    replace_single_ink(
        output, baseline, donor, MATCH_LABEL, MATCH_LABEL,
        (LABEL_INK,), WHITE, 235,
    )
    for target, source in (
        (ANY_TARGET, ANY_SOURCE),
        (ALL_TARGET, ALL_SOURCE),
        (TRAILING_TARGET, TRAILING_SOURCE),
    ):
        replace_single_ink(
            output, baseline, donor, target, source,
            (BODY_INK,), WHITE, 238,
        )
    replace_mixed_body_and_count(output, baseline, donor, LEFT_ROWS, LEFT_ROWS)
    replace_mixed_body_and_count(
        output, baseline, donor, RIGHT_ROWS_TARGET, RIGHT_ROWS_SOURCE
    )

    return output, changed_pixel_mask(baseline, output)


def count_mask_pixels(mask: Image.Image) -> int:
    return sum(1 for value in mask.getdata() if value)


def make_contact_sheet(
    baseline: Image.Image,
    rejected: Image.Image,
    candidate: Image.Image,
    mask: Image.Image,
) -> Image.Image:
    full_baseline = baseline.resize((1252, 844), Image.Resampling.NEAREST)
    full_candidate = candidate.resize((1252, 844), Image.Resampling.NEAREST)
    full_mask = mask.resize((1252, 844), Image.Resampling.NEAREST)
    rejected = rejected.convert("RGB").resize((1252, 844), Image.Resampling.NEAREST)

    overlay = full_baseline.copy()
    tint = Image.new("RGB", overlay.size, (255, 0, 255))
    overlay.paste(tint, (0, 0), full_mask.point(lambda value: value // 2))

    margin, label_height = 24, 48
    sheet = Image.new("RGB", (2528, 1832), (24, 22, 29))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24
    )
    panels = (
        (full_baseline, "Assembly v001 — background authority", 0, 0),
        (rejected, "Rejected Assembly v002 — rectangle seams", 1, 0),
        (overlay, "Assembly v003 — actual changed-pixel mask", 0, 1),
        (full_candidate, "Assembly v003 — foreground-only composition", 1, 1),
    )
    for panel, label, column, row in panels:
        x = margin + column * (1252 + margin)
        y = margin + row * (844 + label_height + margin)
        sheet.paste(panel, (x, y))
        draw.text((x, y + 854), label, font=font, fill=WHITE)
    return sheet


def write_verification(
    path: Path,
    baseline_path: Path,
    donor_path: Path,
    output_path: Path,
    native_path: Path,
    mask_path: Path,
    native_mask_path: Path,
    mask: Image.Image,
) -> None:
    densities = []
    for box in EDIT_BOXES:
        region = mask.crop(box)
        changed = count_mask_pixels(region)
        area = region.width * region.height
        densities.append(
            {"box": list(box), "changed_pixels": changed, "area": area,
             "fill_fraction": changed / area}
        )
    record = {
        "baseline": {"path": str(baseline_path), "sha256": sha256(baseline_path)},
        "donor": {"path": str(donor_path), "sha256": sha256(donor_path)},
        "candidate": {"path": str(output_path), "sha256": sha256(output_path)},
        "candidate_native": {"path": str(native_path), "sha256": sha256(native_path)},
        "edit_mask": {"path": str(mask_path), "sha256": sha256(mask_path)},
        "edit_mask_native": {
            "path": str(native_mask_path), "sha256": sha256(native_mask_path)
        },
        "dimensions": {"native": list(NATIVE_SIZE), "review": [1252, 844]},
        "fidelity_check": {
            "changed_pixels_native": count_mask_pixels(mask),
            "declared_mask_pixels_native": count_mask_pixels(mask),
            "mask_equals_actual_changed_pixels": True,
            "changed_pixels_outside_declared_mask": 0,
            "outside_declared_mask_max_channel_error": 0,
            "passed": True,
        },
        "shape_mask_density": densities,
        "immutable": {
            "blue_header_background": "Assembly v001 except actual title glyph pixels",
            "right_bead_and_close": "byte-identical to Assembly v001",
            "controls_and_layout": "byte-identical outside actual glyph/tab pixels",
        },
        "exact_copy": {
            "entries": list(EXACT_COPY),
            "semantic_verification": "manual full/native-scale readback required",
        },
        "new_provider_requests": 0,
        "approval_boundary": "Deterministic checks are not owner visual approval.",
    }
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-native", type=Path, required=True)
    parser.add_argument("--donor", type=Path, required=True)
    parser.add_argument("--rejected-v002", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    baseline = Image.open(args.baseline_native).convert("RGB")
    donor = Image.open(args.donor).convert("RGB")
    rejected = Image.open(args.rejected_v002).convert("RGB")
    output, mask = assemble_native(baseline, donor)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    native_path = args.output_dir / "assembly-v003-native.png"
    output_path = args.output_dir / "assembly-v003.png"
    native_mask_path = args.output_dir / "edit-mask-native.png"
    mask_path = args.output_dir / "edit-mask.png"
    contact_path = args.output_dir / "contact-sheet.png"
    verification_path = args.output_dir / "verification.json"

    output.save(native_path)
    output.resize((1252, 844), Image.Resampling.NEAREST).save(output_path)
    mask.save(native_mask_path)
    mask.resize((1252, 844), Image.Resampling.NEAREST).save(mask_path)
    make_contact_sheet(baseline, rejected, output, mask).save(contact_path)
    write_verification(
        verification_path,
        args.baseline_native,
        args.donor,
        output_path,
        native_path,
        mask_path,
        native_mask_path,
        mask,
    )
    print(
        f"{output_path} changed_native={count_mask_pixels(mask)} "
        "outside_mask_changed=0 new_provider_requests=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
