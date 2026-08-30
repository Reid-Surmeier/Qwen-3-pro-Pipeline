#!/usr/bin/env python3.12
"""Build Issue #118 Assembly v003 with deterministic shape-aware text masks.

Assembly v001 owns every background and control pixel. English lettering is
rendered from the repository-pinned PixelMplus fonts; no generated raster or
rectangular donor background is copied. The permitted mask is computed from
the old and new glyph silhouettes before composition, then checked against the
actual baseline-to-candidate difference.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / (
    "artifacts/references/museum-filter-retro-skin-v001/"
    "style-ro-options-window-flat-rgb.png"
)
BODY_FONT = ROOT / "godot/fonts/PixelMplus10-Regular.ttf"
TITLE_FONT = ROOT / "godot/fonts/PixelMplus12-Regular.ttf"
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
ROW_STRIDE = 19

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


@dataclass(frozen=True)
class TextRule:
    """One deterministic text edit and the pixels it is allowed to own."""

    box: tuple[int, int, int, int]
    text: str
    xy: tuple[int, int]
    fill: tuple[int, int, int]
    background: tuple[int, int, int]
    old_inks: tuple[tuple[int, int, int], ...]
    font_path: Path = BODY_FONT
    font_size: int = 10
    vertical: bool = False


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def repo_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(ROOT))
    except ValueError:
        return str(path)


def changed_pixel_mask(before: Image.Image, after: Image.Image) -> Image.Image:
    if before.size != after.size:
        raise ValueError(f"image sizes differ: {before.size} != {after.size}")
    red, green, blue = ImageChops.difference(
        before.convert("RGB"), after.convert("RGB")
    ).split()
    maximum = ImageChops.lighter(ImageChops.lighter(red, green), blue)
    return maximum.point(lambda value: 255 if value else 0)


def add_mask(
    declared: Image.Image, local: Image.Image, xy: tuple[int, int]
) -> None:
    box = (xy[0], xy[1], xy[0] + local.width, xy[1] + local.height)
    combined = ImageChops.lighter(declared.crop(box), local.convert("L"))
    declared.paste(combined, xy)


def exact_ink_mask(
    baseline: Image.Image,
    box: tuple[int, int, int, int],
    inks: tuple[tuple[int, int, int], ...],
) -> Image.Image:
    source = baseline.crop(box)
    mask = Image.new("L", source.size, 0)
    source_pixels = source.load()
    mask_pixels = mask.load()
    for y in range(source.height):
        for x in range(source.width):
            if source_pixels[x, y] in inks:
                mask_pixels[x, y] = 255
    return mask


def binary_text_mask(
    text: str,
    font_path: Path,
    font_size: int,
    vertical: bool = False,
) -> Image.Image:
    font = ImageFont.truetype(str(font_path), font_size)
    left, top, right, bottom = font.getbbox(text)
    mask = Image.new("L", (right - left, bottom - top), 0)
    draw = ImageDraw.Draw(mask)
    draw.fontmode = "1"
    draw.text((-left, -top), text, font=font, fill=255, stroke_width=0)
    if vertical:
        mask = mask.rotate(90, expand=True)
    return mask


def clear_and_draw_rule(
    output: Image.Image,
    baseline: Image.Image,
    declared: Image.Image,
    rule: TextRule,
) -> None:
    old_mask = exact_ink_mask(baseline, rule.box, rule.old_inks)
    output.paste(
        Image.new("RGB", old_mask.size, rule.background), rule.box[:2], old_mask
    )
    add_mask(declared, old_mask, rule.box[:2])

    glyph = binary_text_mask(
        rule.text, rule.font_path, rule.font_size, vertical=rule.vertical
    )
    output.paste(Image.new("RGB", glyph.size, rule.fill), rule.xy, glyph)
    add_mask(declared, glyph, rule.xy)


def restore_title_background(
    output: Image.Image, baseline: Image.Image, declared: Image.Image
) -> None:
    reference = Image.open(REFERENCE).convert("RGB")
    bar = reference.crop((600, 45, 1372, 124)).resize(
        (baseline.width - 6, 20), Image.Resampling.LANCZOS
    )
    target = (20, 6, 160, 21)
    baseline_patch = baseline.crop(target)
    bar_patch = bar.crop((target[0] - 3, target[1] - 3, target[2] - 3, target[3] - 3))
    # v001's title was drawn with exact black and white palette entries. Use
    # those source-owned glyph pixels as the predeclared erase mask; comparing
    # two whole gradient crops would incorrectly license incidental glass
    # resampling differences.
    old_title = exact_ink_mask(
        baseline, target, (BODY_INK, WHITE)
    )
    output.paste(bar_patch, target[:2], old_title)
    add_mask(declared, old_title, target[:2])


def replace_title(
    output: Image.Image, baseline: Image.Image, declared: Image.Image
) -> None:
    restore_title_background(output, baseline, declared)
    glyph = binary_text_mask(
        "Object type / material", TITLE_FONT, 12
    )
    xy = (20, 6)
    highlight_xy = (xy[0] - 1, xy[1] - 1)
    # The source uses a one-pixel upper-left highlight, not a dilation halo.
    # Keeping that palette-shaped treatment avoids a thick synthetic outline.
    output.paste(Image.new("RGB", glyph.size, WHITE), highlight_xy, glyph)
    output.paste(Image.new("RGB", glyph.size, BODY_INK), xy, glyph)
    add_mask(declared, glyph, highlight_xy)
    add_mask(declared, glyph, xy)


def assemble_native(baseline: Image.Image) -> tuple[Image.Image, Image.Image]:
    baseline = baseline.convert("RGB")
    if baseline.size != NATIVE_SIZE:
        raise ValueError(f"baseline must be {NATIVE_SIZE}, got {baseline.size}")
    output = baseline.copy()
    declared = Image.new("L", baseline.size, 0)

    replace_title(output, baseline, declared)
    rules = (
        TextRule(OBJECT_TAB, "object", (10, 30), TAB_ON_INK, WHITE,
                 (TAB_ON_INK,), vertical=True),
        TextRule(MATERIAL_TAB, "material", (10, 76), TAB_OFF_INK,
                 TAB_OFF_FILL, (TAB_OFF_INK,), vertical=True),
        TextRule(SEARCH_LABEL, "Search", (31, 41), LABEL_INK, WHITE,
                 (LABEL_INK,)),
        TextRule(SEARCH_PLACEHOLDER_TARGET, "Search", (81, 41), PLACEHOLDER,
                 FIELD_FILL, (PLACEHOLDER,)),
        TextRule(MATCH_LABEL, "Match", (31, 68), LABEL_INK, WHITE,
                 (LABEL_INK,)),
        TextRule(ANY_TARGET, "Any", (90, 68), BODY_INK, WHITE, (BODY_INK,)),
        TextRule(ALL_TARGET, "All", (142, 68), BODY_INK, WHITE, (BODY_INK,)),
        TextRule(TRAILING_TARGET, "selected filters.", (167, 68), BODY_INK,
                 WHITE, (BODY_INK,)),
    )
    for rule in rules:
        clear_and_draw_rule(output, baseline, declared, rule)

    columns = (
        (LEFT_ROWS, ("Metal (5,001)", "Paper (3,652)", "Glass (3,182)",
                     "Drawings (2,606)", "Graphite (2,443)")),
        (RIGHT_ROWS_TARGET,
         ("Paintings (2,395)", "Vessels (2,074)",
          "Watercolors (1,962)", "Wood (1,899)", "Dishes (1,837)")),
    )
    for box, entries in columns:
        old_mask = exact_ink_mask(baseline, box, (BODY_INK, COUNT_INK))
        output.paste(Image.new("RGB", old_mask.size, WHITE), box[:2], old_mask)
        add_mask(declared, old_mask, box[:2])
        for row, entry in enumerate(entries):
            name, count = entry.rsplit(" ", 1)
            y = box[1] + 4 + row * ROW_STRIDE
            name_mask = binary_text_mask(name, BODY_FONT, 10)
            output.paste(Image.new("RGB", name_mask.size, BODY_INK),
                         (box[0], y), name_mask)
            add_mask(declared, name_mask, (box[0], y))
            count_x = box[0] + name_mask.width + 4
            count_mask = binary_text_mask(count, BODY_FONT, 10)
            output.paste(Image.new("RGB", count_mask.size, COUNT_INK),
                         (count_x, y), count_mask)
            add_mask(declared, count_mask, (count_x, y))

    actual = changed_pixel_mask(baseline, output)
    outside = ImageChops.multiply(actual, ImageChops.invert(declared))
    if outside.getbbox() is not None:
        raise AssertionError("composition changed pixels outside the declared mask")
    return output, declared


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
        (overlay, "Assembly v003 — predeclared shape-aware mask", 0, 1),
        (full_candidate, "Assembly v003 — deterministic text composition", 1, 1),
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
    output_path: Path,
    native_path: Path,
    mask_path: Path,
    native_mask_path: Path,
    declared_mask: Image.Image,
    actual_mask: Image.Image,
) -> None:
    densities = []
    for box in EDIT_BOXES:
        region = declared_mask.crop(box)
        changed = count_mask_pixels(region)
        area = region.width * region.height
        densities.append(
            {"box": list(box), "changed_pixels": changed, "area": area,
             "fill_fraction": changed / area}
        )
    record = {
        "baseline": {"path": repo_path(baseline_path), "sha256": sha256(baseline_path)},
        "style_source": {"path": repo_path(REFERENCE), "sha256": sha256(REFERENCE)},
        "fonts": [
            {"path": repo_path(BODY_FONT), "sha256": sha256(BODY_FONT)},
            {"path": repo_path(TITLE_FONT), "sha256": sha256(TITLE_FONT)},
        ],
        "candidate": {"path": repo_path(output_path), "sha256": sha256(output_path)},
        "candidate_native": {"path": repo_path(native_path), "sha256": sha256(native_path)},
        "edit_mask": {"path": repo_path(mask_path), "sha256": sha256(mask_path)},
        "edit_mask_native": {
            "path": repo_path(native_mask_path), "sha256": sha256(native_mask_path)
        },
        "dimensions": {"native": list(NATIVE_SIZE), "review": [1252, 844]},
        "fidelity_check": {
            "changed_pixels_native": count_mask_pixels(actual_mask),
            "declared_mask_pixels_native": count_mask_pixels(declared_mask),
            "mask_equals_actual_changed_pixels": (
                declared_mask.tobytes() == actual_mask.tobytes()
            ),
            "changed_pixels_outside_declared_mask": count_mask_pixels(
                ImageChops.multiply(actual_mask, ImageChops.invert(declared_mask))
            ),
            "outside_declared_mask_max_channel_error": 0,
            "passed": ImageChops.multiply(
                actual_mask, ImageChops.invert(declared_mask)
            ).getbbox() is None,
        },
        "shape_mask_density": densities,
        "immutable": {
            "blue_header_background": "Assembly v001 except actual title glyph pixels",
            "right_bead_and_close": "byte-identical to Assembly v001",
            "controls_and_layout": "byte-identical outside actual glyph/tab pixels",
        },
        "exact_copy": {
            "entries": list(EXACT_COPY),
            "source": "deterministic strings rendered with pinned repository fonts",
            "semantic_verification": "manual full/native-scale readback required",
        },
        "new_provider_requests": 0,
        "approval_boundary": "Deterministic checks are not owner visual approval.",
    }
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-native", type=Path, required=True)
    parser.add_argument("--rejected-v002", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    baseline = Image.open(args.baseline_native).convert("RGB")
    rejected = Image.open(args.rejected_v002).convert("RGB")
    output, declared_mask = assemble_native(baseline)
    actual_mask = changed_pixel_mask(baseline, output)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    native_path = args.output_dir / "assembly-v003-native.png"
    output_path = args.output_dir / "assembly-v003.png"
    native_mask_path = args.output_dir / "edit-mask-native.png"
    mask_path = args.output_dir / "edit-mask.png"
    contact_path = args.output_dir / "contact-sheet.png"
    verification_path = args.output_dir / "verification.json"

    output.save(native_path)
    output.resize((1252, 844), Image.Resampling.NEAREST).save(output_path)
    declared_mask.save(native_mask_path)
    declared_mask.resize((1252, 844), Image.Resampling.NEAREST).save(mask_path)
    make_contact_sheet(baseline, rejected, output, declared_mask).save(contact_path)
    write_verification(
        verification_path,
        args.baseline_native,
        output_path,
        native_path,
        mask_path,
        native_mask_path,
        declared_mask,
        actual_mask,
    )
    print(
        f"{output_path} changed_native={count_mask_pixels(actual_mask)} "
        f"declared_native={count_mask_pixels(declared_mask)} "
        "outside_mask_changed=0 new_provider_requests=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
