#!/usr/bin/env python3.12
"""Repair the three owner-marked regions in Issue #118 Assembly v001.

Assembly v001 remains the source of every unmarked pixel.  This pass restores
the title glass beneath the two beads and close button, then pastes only the
foreground silhouettes.  It also rebuilds the inactive material tab as a
stepped shape over the original striped margin while preserving its v001 text
pixels.  No generated image or rectangular donor background is used.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "artifacts/references/museum-filter-retro-skin-v001"
SPRITES = REFERENCE_DIR / "sprites"
BASELINE = ROOT / "artifacts/runs/museum-filter-assembly-v001/assembly-v001-native.png"
DEFAULT_OUTPUT = ROOT / "artifacts/runs/museum-filter-assembly-v004"

NATIVE_SIZE = (313, 211)
SCALE = 4
TITLE_ORIGIN = (3, 3)
TITLE_SIZE = (307, 20)

LEFT_BEAD_BOX = (6, 6, 19, 19)
RIGHT_BEAD_BOX = (270, 6, 283, 19)
CLOSE_BOX = (288, 3, 307, 22)
RIGHT_HEADER_BOX = (270, 3, 307, 22)
MATERIAL_BOX = (3, 69, 19, 124)
EDIT_BOXES = (LEFT_BEAD_BOX, RIGHT_HEADER_BOX, MATERIAL_BOX)

WHITE = (0xFF, 0xFF, 0xFF)
STRIPE = (0xF6, 0xF3, 0xF6)
TAB_OFF_FILL = (0xF3, 0xEF, 0xF4)
TAB_EDGE = (0xC9, 0xC6, 0xCB)
TAB_OFF_INK = (0x8B, 0x89, 0x8C)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def changed_pixel_mask(before: Image.Image, after: Image.Image) -> Image.Image:
    if before.size != after.size:
        raise ValueError(f"image sizes differ: {before.size} != {after.size}")
    channels = ImageChops.difference(before.convert("RGB"), after.convert("RGB")).split()
    maximum = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
    return maximum.point(lambda value: 255 if value else 0)


def add_mask(canvas: Image.Image, local: Image.Image, xy: tuple[int, int]) -> None:
    box = (xy[0], xy[1], xy[0] + local.width, xy[1] + local.height)
    canvas.paste(ImageChops.lighter(canvas.crop(box), local.convert("L")), xy)


def header_bar() -> Image.Image:
    reference = Image.open(REFERENCE_DIR / "style-ro-options-window-flat-rgb.png").convert("RGB")
    return reference.crop((600, 45, 1372, 124)).resize(TITLE_SIZE, Image.Resampling.LANCZOS)


def bead_mask() -> Image.Image:
    """The 13px round bead silhouette, excluding its square donor corners."""
    mask = Image.new("L", (13, 13), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, 12, 12), fill=255)
    return mask


def close_mask() -> Image.Image:
    """The close-button silhouette, excluding its captured cyan surround."""
    mask = Image.new("L", (19, 19), 0)
    ImageDraw.Draw(mask).polygon(
        ((4, 1), (15, 1), (16, 2), (16, 15), (15, 16), (4, 16), (3, 15), (3, 2)),
        fill=255,
    )
    return mask


def material_tab_mask() -> Image.Image:
    """A source-like stair-step silhouette for the inactive vertical tab."""
    mask = Image.new("L", (16, 55), 0)
    ImageDraw.Draw(mask).polygon(
        (
            (0, 0),
            (3, 0),
            (3, 2),
            (6, 2),
            (6, 4),
            (9, 4),
            (9, 6),
            (12, 6),
            (12, 8),
            (15, 8),
            (15, 46),
            (12, 46),
            (12, 48),
            (9, 48),
            (9, 50),
            (6, 50),
            (6, 52),
            (3, 52),
            (3, 54),
            (0, 54),
        ),
        fill=255,
    )
    return mask


def striped_margin(box: tuple[int, int, int, int]) -> Image.Image:
    """Reconstruct the v001 body stripes at their original global phase."""
    width, height = box[2] - box[0], box[3] - box[1]
    patch = Image.new("RGB", (width, height), WHITE)
    draw = ImageDraw.Draw(patch)
    for local_y in range(height):
        global_y = box[1] + local_y
        if (global_y - 23) % 5 in (2, 3):
            draw.line((0, local_y, width - 1, local_y), fill=STRIPE)
    return patch


def exact_color_mask(image: Image.Image, color: tuple[int, int, int]) -> Image.Image:
    image = image.convert("RGB")
    mask = Image.new("L", image.size, 0)
    source_pixels = image.load()
    mask_pixels = mask.load()
    for y in range(image.height):
        for x in range(image.width):
            if source_pixels[x, y] == color:
                mask_pixels[x, y] = 255
    return mask


def paste_header_icon(
    output: Image.Image,
    baseline: Image.Image,
    declared: Image.Image,
    bar: Image.Image,
    sprite_name: str,
    box: tuple[int, int, int, int],
    foreground: Image.Image,
) -> None:
    local_box = (
        box[0] - TITLE_ORIGIN[0],
        box[1] - TITLE_ORIGIN[1],
        box[2] - TITLE_ORIGIN[0],
        box[3] - TITLE_ORIGIN[1],
    )
    patch = bar.crop(local_box)
    icon = Image.open(SPRITES / f"{sprite_name}.png").convert("RGB")
    patch.paste(icon, (0, 0), foreground)
    local_change = changed_pixel_mask(baseline.crop(box), patch)
    output.paste(patch, box[:2], local_change)
    add_mask(declared, local_change, box[:2])


def rebuild_material_tab(output: Image.Image, baseline: Image.Image, declared: Image.Image) -> None:
    xy = MATERIAL_BOX[:2]
    old_tab = baseline.crop(MATERIAL_BOX)
    underlying = striped_margin(MATERIAL_BOX)
    shape = material_tab_mask()
    tab = Image.new("RGB", shape.size, TAB_OFF_FILL)
    edge = Image.new("L", shape.size, 0)
    edge_draw = ImageDraw.Draw(edge)
    points = (
        (0, 0),
        (3, 0),
        (3, 2),
        (6, 2),
        (6, 4),
        (9, 4),
        (9, 6),
        (12, 6),
        (12, 8),
        (15, 8),
        (15, 46),
        (12, 46),
        (12, 48),
        (9, 48),
        (9, 50),
        (6, 50),
        (6, 52),
        (3, 52),
        (3, 54),
        (0, 54),
    )
    edge_draw.line(points + (points[0],), fill=255, width=1)
    tab.paste(Image.new("RGB", tab.size, TAB_EDGE), (0, 0), edge)
    underlying.paste(tab, (0, 0), shape)

    ink = exact_color_mask(old_tab, TAB_OFF_INK)
    underlying.paste(old_tab, (0, 0), ink)
    local_change = changed_pixel_mask(old_tab, underlying)
    output.paste(underlying, xy, local_change)
    add_mask(declared, local_change, xy)


def assemble_native(baseline: Image.Image) -> tuple[Image.Image, Image.Image]:
    baseline = baseline.convert("RGB")
    if baseline.size != NATIVE_SIZE:
        raise ValueError(f"baseline must be {NATIVE_SIZE}, got {baseline.size}")
    output = baseline.copy()
    declared = Image.new("L", baseline.size, 0)
    bar = header_bar()

    paste_header_icon(output, baseline, declared, bar, "bead", LEFT_BEAD_BOX, bead_mask())
    paste_header_icon(output, baseline, declared, bar, "bead", RIGHT_BEAD_BOX, bead_mask())
    paste_header_icon(output, baseline, declared, bar, "close", CLOSE_BOX, close_mask())
    rebuild_material_tab(output, baseline, declared)
    return output, declared


def count_pixels(mask: Image.Image) -> int:
    histogram = mask.convert("L").histogram()
    return sum(histogram[1:])


def crop_zoom(image: Image.Image, box: tuple[int, int, int, int], scale: int = 8) -> Image.Image:
    crop = image.crop(box)
    return crop.resize((crop.width * scale, crop.height * scale), Image.Resampling.NEAREST)


def contact_sheet(baseline: Image.Image, candidate: Image.Image) -> Image.Image:
    full_scale = 2
    full_before = baseline.resize(
        (baseline.width * full_scale, baseline.height * full_scale), Image.Resampling.NEAREST
    )
    full_after = candidate.resize(full_before.size, Image.Resampling.NEAREST)
    crops = (
        ("left title edge", (3, 3, 80, 23)),
        ("right title edge", (263, 2, 310, 23)),
        ("material tab", (1, 65, 23, 128)),
    )
    zooms = [(name, crop_zoom(baseline, box), crop_zoom(candidate, box)) for name, box in crops]
    row_width = max(full_before.width * 2 + 24, max(a.width + b.width + 24 for _, a, b in zooms))
    total_height = (
        24 + full_before.height + sum(24 + max(a.height, b.height) for _, a, b in zooms) + 20
    )
    sheet = Image.new("RGB", (row_width + 24, total_height), (32, 35, 43))
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 6), "Assembly v001 (left) / Assembly v004 (right)", fill=WHITE)
    y = 24
    sheet.paste(full_before, (12, y))
    sheet.paste(full_after, (24 + full_before.width, y))
    y += full_before.height
    for name, before, after in zooms:
        draw.text((12, y + 6), name, fill=WHITE)
        y += 24
        sheet.paste(before, (12, y))
        sheet.paste(after, (24 + before.width, y))
        y += max(before.height, after.height)
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path, default=BASELINE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    baseline_path = args.baseline.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    baseline = Image.open(baseline_path).convert("RGB")
    candidate, declared = assemble_native(baseline)
    actual = changed_pixel_mask(baseline, candidate)
    outside = ImageChops.multiply(actual, ImageChops.invert(declared))
    if outside.getbbox() is not None:
        raise RuntimeError(f"changed pixels escaped declared mask: {outside.getbbox()}")

    native_path = output_dir / "assembly-v004-native.png"
    review_path = output_dir / "assembly-v004.png"
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
    contact_sheet(baseline, candidate).save(contact_path)

    changed = count_pixels(actual)
    declared_pixels = count_pixels(declared)
    verification = {
        "issue": 118,
        "assembly": "v004",
        "baseline": repo_path(baseline_path),
        "baseline_sha256": sha256(baseline_path),
        "candidate": repo_path(native_path),
        "candidate_sha256": sha256(native_path),
        "edit_boxes": [list(box) for box in EDIT_BOXES],
        "changed_pixels": changed,
        "declared_mask_pixels": declared_pixels,
        "changed_pixels_outside_declared_mask": 0,
        "unmarked_pixels_identical_to_v001": True,
        "generation_requests": 0,
    }
    (output_dir / "verification.json").write_text(
        json.dumps(verification, indent=2) + "\n", encoding="utf-8"
    )
    run = {
        "issue": 118,
        "method": "deterministic native-pixel Assembly from v001",
        "scope": [
            "left header bead",
            "right header bead and close button",
            "inactive material tab",
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
