#!/usr/bin/env python3.12
"""Correct v004's clipped beads and reversed, undersized material tab.

Assembly v001 still owns every unmarked pixel. The beads are recut with native
padding from the full-resolution source instead of the tight 13px sprite crop.
The inactive material tab is widened and its stairs run from wide tips to a
narrower middle, matching the source orientation. No generation is used.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw

try:
    from scripts import assemble_museum_filter_v004 as v004
except ModuleNotFoundError:
    import assemble_museum_filter_v004 as v004


ROOT = v004.ROOT
REFERENCE_DIR = v004.REFERENCE_DIR
BASELINE = v004.BASELINE
PARENT = ROOT / "artifacts/runs/museum-filter-assembly-v004/assembly-v004-native.png"
DEFAULT_OUTPUT = ROOT / "artifacts/runs/museum-filter-assembly-v005"

NATIVE_SIZE = v004.NATIVE_SIZE
SCALE = v004.SCALE
TITLE_ORIGIN = v004.TITLE_ORIGIN

LEFT_BEAD_BOX = (5, 5, 20, 20)
RIGHT_BEAD_BOX = (269, 5, 284, 20)
CLOSE_BOX = v004.CLOSE_BOX
RIGHT_HEADER_BOX = (269, 3, 307, 22)
MATERIAL_BOX = (3, 69, 23, 124)
MATERIAL_INK_BOX = v004.MATERIAL_BOX
MATERIAL_TEXT_SHIFT = (-2, 0)
EDIT_BOXES = (LEFT_BEAD_BOX, RIGHT_HEADER_BOX, MATERIAL_BOX)

TAB_OFF_FILL = v004.TAB_OFF_FILL
TAB_EDGE = v004.TAB_EDGE
TAB_OFF_INK = v004.TAB_OFF_INK

changed_pixel_mask = v004.changed_pixel_mask
add_mask = v004.add_mask
header_bar = v004.header_bar
sha256 = v004.sha256
repo_path = v004.repo_path
count_pixels = v004.count_pixels


def bead_asset() -> tuple[Image.Image, Image.Image]:
    """Return a 15px bead with a guaranteed one-pixel transparent margin."""
    reference = Image.open(REFERENCE_DIR / "style-ro-options-window-flat-rgb.png").convert("RGB")
    # The full-resolution source bead occupies roughly x/y 60..109. The 64px
    # crop keeps real header pixels around it so the downsampled orb is not cut
    # off like the earlier tight 13px sprite.
    source = reference.crop((52, 52, 116, 116))
    source_mask = Image.new("L", source.size, 0)
    ImageDraw.Draw(source_mask).ellipse((7, 7, 58, 58), fill=255)
    image = source.resize((15, 15), Image.Resampling.LANCZOS)
    alpha = source_mask.resize((15, 15), Image.Resampling.LANCZOS)

    # LANCZOS can ring by a one-digit alpha value beyond the source ellipse.
    # Zero the outer row/column explicitly: the visible orb remains inside and
    # therefore cannot be clipped by the ownership box.
    draw = ImageDraw.Draw(alpha)
    draw.line((0, 0, 14, 0), fill=0)
    draw.line((0, 14, 14, 14), fill=0)
    draw.line((0, 0, 0, 14), fill=0)
    draw.line((14, 0, 14, 14), fill=0)
    return image, alpha


def material_tab_points() -> tuple[tuple[int, int], ...]:
    """Wide tips step inward to the narrower body—the source orientation."""
    return (
        (0, 0),
        (19, 0),
        (19, 1),
        (18, 1),
        (18, 3),
        (17, 3),
        (17, 5),
        (16, 5),
        (16, 49),
        (17, 49),
        (17, 51),
        (18, 51),
        (18, 53),
        (19, 53),
        (19, 54),
        (0, 54),
    )


def material_tab_mask() -> Image.Image:
    mask = Image.new("L", (20, 55), 0)
    ImageDraw.Draw(mask).polygon(material_tab_points(), fill=255)
    return mask


def paste_bead(
    output: Image.Image,
    baseline: Image.Image,
    declared: Image.Image,
    bar: Image.Image,
    box: tuple[int, int, int, int],
) -> None:
    local_box = (
        box[0] - TITLE_ORIGIN[0],
        box[1] - TITLE_ORIGIN[1],
        box[2] - TITLE_ORIGIN[0],
        box[3] - TITLE_ORIGIN[1],
    )
    patch = bar.crop(local_box)
    bead, alpha = bead_asset()
    patch.paste(bead, (0, 0), alpha)
    local_change = changed_pixel_mask(baseline.crop(box), patch)
    output.paste(patch, box[:2], local_change)
    add_mask(declared, local_change, box[:2])


def paste_close(
    output: Image.Image,
    baseline: Image.Image,
    declared: Image.Image,
    bar: Image.Image,
) -> None:
    v004.paste_header_icon(
        output,
        baseline,
        declared,
        bar,
        "close",
        CLOSE_BOX,
        v004.close_mask(),
    )


def rebuild_material_tab(output: Image.Image, baseline: Image.Image, declared: Image.Image) -> None:
    final = baseline.crop(MATERIAL_BOX)

    # Clear only the old v001 tab rectangle back to its correctly phased body
    # stripes. Expanded pixels to its right remain baseline-owned unless the
    # new stair silhouette explicitly covers them.
    old_width = MATERIAL_INK_BOX[2] - MATERIAL_INK_BOX[0]
    old_underlying = v004.striped_margin(MATERIAL_INK_BOX)
    final.paste(old_underlying, (0, 0, old_width, old_underlying.height))

    shape = material_tab_mask()
    tab = Image.new("RGB", shape.size, TAB_OFF_FILL)
    edge = Image.new("L", shape.size, 0)
    points = material_tab_points()
    ImageDraw.Draw(edge).line(points + (points[0],), fill=255, width=1)
    tab.paste(Image.new("RGB", tab.size, TAB_EDGE), (0, 0), edge)
    final.paste(tab, (0, 0), shape)

    old_ink = baseline.crop(MATERIAL_INK_BOX)
    ink = v004.exact_color_mask(old_ink, TAB_OFF_INK)
    final.paste(old_ink, MATERIAL_TEXT_SHIFT, ink)

    local_change = changed_pixel_mask(baseline.crop(MATERIAL_BOX), final)
    output.paste(final, MATERIAL_BOX[:2], local_change)
    add_mask(declared, local_change, MATERIAL_BOX[:2])


def assemble_native(baseline: Image.Image) -> tuple[Image.Image, Image.Image]:
    baseline = baseline.convert("RGB")
    if baseline.size != NATIVE_SIZE:
        raise ValueError(f"baseline must be {NATIVE_SIZE}, got {baseline.size}")
    output = baseline.copy()
    declared = Image.new("L", baseline.size, 0)
    bar = header_bar()
    paste_bead(output, baseline, declared, bar, LEFT_BEAD_BOX)
    paste_bead(output, baseline, declared, bar, RIGHT_BEAD_BOX)
    paste_close(output, baseline, declared, bar)
    rebuild_material_tab(output, baseline, declared)
    return output, declared


def zoom(image: Image.Image, box: tuple[int, int, int, int], scale: int = 8) -> Image.Image:
    crop = image.crop(box)
    return crop.resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST)


def contact_sheet(
    baseline: Image.Image, parent: Image.Image, candidate: Image.Image
) -> Image.Image:
    fulls = [
        image.resize((image.width * 2, image.height * 2), Image.Resampling.NEAREST)
        for image in (baseline, parent, candidate)
    ]
    crop_boxes = (
        ("left bead", (2, 2, 82, 23)),
        ("right bead and close", (262, 2, 310, 23)),
        ("material tab", (1, 65, 25, 128)),
    )
    crop_rows = [(name, zoom(parent, box), zoom(candidate, box)) for name, box in crop_boxes]
    width = max(
        sum(image.width for image in fulls) + 48,
        max(before.width + after.width + 36 for _, before, after in crop_rows),
    )
    height = (
        26
        + fulls[0].height
        + sum(26 + max(before.height, after.height) for _, before, after in crop_rows)
        + 20
    )
    sheet = Image.new("RGB", (width, height), (32, 35, 43))
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 7), "v001 / rejected v004 / corrected v005", fill=(255, 255, 255))
    x, y = 12, 26
    for image in fulls:
        sheet.paste(image, (x, y))
        x += image.width + 12
    y += fulls[0].height
    for name, before, after in crop_rows:
        draw.text((12, y + 7), f"{name}: v004 left / v005 right", fill=(255, 255, 255))
        y += 26
        sheet.paste(before, (12, y))
        sheet.paste(after, (24 + before.width, y))
        y += max(before.height, after.height)
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    parser.add_argument("--parent", type=Path, default=PARENT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    baseline_path = args.baseline.resolve()
    parent_path = args.parent.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline = Image.open(baseline_path).convert("RGB")
    parent = Image.open(parent_path).convert("RGB")
    candidate, declared = assemble_native(baseline)
    actual = changed_pixel_mask(baseline, candidate)
    if actual.tobytes() != declared.tobytes():
        raise RuntimeError("declared mask does not exactly equal the actual difference")

    native_path = output_dir / "assembly-v005-native.png"
    review_path = output_dir / "assembly-v005.png"
    mask_native_path = output_dir / "edit-mask-native.png"
    mask_path = output_dir / "edit-mask.png"
    contact_path = output_dir / "contact-sheet.png"
    candidate.save(native_path)
    candidate.resize(
        (candidate.width * SCALE, candidate.height * SCALE), Image.Resampling.NEAREST
    ).save(review_path)
    declared.save(mask_native_path)
    declared.resize(
        (declared.width * SCALE, declared.height * SCALE), Image.Resampling.NEAREST
    ).save(mask_path)
    contact_sheet(baseline, parent, candidate).save(contact_path)

    verification = {
        "issue": 118,
        "assembly": "v005",
        "baseline": repo_path(baseline_path),
        "baseline_sha256": sha256(baseline_path),
        "rejected_parent": repo_path(parent_path),
        "rejected_parent_sha256": sha256(parent_path),
        "candidate": repo_path(native_path),
        "candidate_sha256": sha256(native_path),
        "edit_boxes": [list(box) for box in EDIT_BOXES],
        "changed_pixels": count_pixels(actual),
        "declared_mask_pixels": count_pixels(declared),
        "changed_pixels_outside_declared_mask": 0,
        "declared_mask_equals_actual_difference": True,
        "unmarked_pixels_identical_to_v001": True,
        "generation_requests": 0,
    }
    (output_dir / "verification.json").write_text(
        json.dumps(verification, indent=2) + "\n", encoding="utf-8"
    )
    run = {
        "issue": 118,
        "method": "deterministic native-pixel Assembly from v001",
        "corrections": [
            "padded full-resolution source beads",
            "reversed inactive-tab stair direction",
            "wider inactive tab with material label moved inward for clearance",
        ],
        "frozen": "all pixels outside the declared three-region mask",
        "provider": None,
        "model": None,
        "requested_images": 0,
        "completed_images": 0,
        "cost_usd": 0,
        "outputs": {
            "native": repo_path(native_path),
            "review": repo_path(review_path),
            "mask_native": repo_path(mask_native_path),
            "mask": repo_path(mask_path),
            "contact_sheet": repo_path(contact_path),
            "verification": repo_path(output_dir / "verification.json"),
        },
    }
    (output_dir / "run.json").write_text(json.dumps(run, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(verification, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
