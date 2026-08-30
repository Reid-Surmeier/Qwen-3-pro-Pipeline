#!/usr/bin/env python3.12
"""Build Issue #138's source-owned Custom filters dialog.

The attached chat-room window is reduced to its 272x126 native pixel grid and
owns all chrome. Qwen candidates are retained as Render Pass evidence only and
are never opened by this assembler. The museum screenshot is likewise never
opened: its approved strings are represented below as data, not donor pixels.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
REFERENCE_DIR = ROOT / "artifacts/references/custom-filters-ro-v001"
STYLE_SOURCE = REFERENCE_DIR / "style-chat-room.png"
DATA_SOURCE = REFERENCE_DIR / "data-sort-dropdown.png"
RAW_RUN = ROOT / "artifacts/runs/custom-filters-ro-render-v001"
DEFAULT_OUTPUT = ROOT / "artifacts/runs/custom-filters-ro-assembly-v001"
FONT = ROOT / "godot/fonts/PixelMplus10-Regular.ttf"
FONT_SHA256 = "01b5e4aea5a3bbe80463c178e7868d5a34cd75e8ed7bc4d97097ebb1a71af7c7"

NATIVE_SIZE = (272, 126)
OPEN_SIZE = (272, 196)
SCALE = 4

TITLE_EDIT_BOX = (10, 6, 248, 24)
ROW_ONE_EDIT_BOX = (13, 27, 257, 46)
ROW_TWO_EDIT_BOX = (13, 48, 257, 66)
ROW_THREE_EDIT_BOX = (13, 68, 257, 87)
BUTTON_EDIT_BOX = (178, 94, 259, 115)
EDIT_BOXES = (
    TITLE_EDIT_BOX,
    ROW_ONE_EDIT_BOX,
    ROW_TWO_EDIT_BOX,
    ROW_THREE_EDIT_BOX,
    BUTTON_EDIT_BOX,
)

SOURCE_ARROW_BOX = (117, 50, 133, 65)
PAGE_ARROW_BOX = (117, 50, 133, 65)
SORT_ARROW_BOX = (240, 50, 256, 65)
SOURCE_ON_RADIO_BOX = (49, 70, 61, 84)
SOURCE_OFF_RADIO_BOX = (85, 70, 97, 84)
ON_RADIO_BOX = SOURCE_ON_RADIO_BOX
OFF_RADIO_BOX = SOURCE_OFF_RADIO_BOX
SOURCE_PASSWORD_BOX = (140, 69, 256, 86)
POPUP_BOX = (138, 64, 261, 192)

WHITE = (255, 255, 255, 255)
FIELD_FILL = (255, 251, 248, 255)
FIELD_EDGE = (197, 196, 194, 255)
FIELD_SHADOW = (169, 168, 168, 255)
FIELD_LIGHT = (255, 255, 255, 255)
LABEL_INK = (26, 68, 102, 255)
BODY_INK = (16, 16, 16, 255)
TITLE_HIGHLIGHT = (255, 255, 255, 255)
BUTTON_FILL = (242, 241, 242, 255)
BUTTON_BOTTOM = (182, 181, 182, 255)
POPUP_SELECTED = (181, 208, 235, 255)
POPUP_STRIPE = (250, 247, 250, 255)

SORT_OPTIONS = (
    "Relevance",
    "Title (a-z)",
    "Title (z-a)",
    "Date (newest-oldest)",
    "Date (oldest-newest)",
    "Artist/Maker (a-z)",
    "Artist/Maker (z-a)",
    "Accession Number (0-9)",
    "Accession Number (9-0)",
)
EXACT_COPY = {
    "title": "Custom filters",
    "custom_filters": "Custom filters:",
    "images_per_page": "Images per page:",
    "page_value": "20",
    "sort_by": "Sort by:",
    "selected_sort": "Relevance",
    "choices": ("On", "Off"),
    "buttons": ("OK", "Cancel"),
    "sort_options": SORT_OPTIONS,
}


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


def native_source(source: Image.Image) -> Image.Image:
    source = source.convert("RGBA")
    if source.size != (1088, 504):
        raise ValueError(f"style source must be 1088x504, got {source.size}")
    return source.resize(NATIVE_SIZE, Image.Resampling.NEAREST)


def changed_pixel_mask(before: Image.Image, after: Image.Image) -> Image.Image:
    if before.size != after.size:
        raise ValueError(f"image sizes differ: {before.size} != {after.size}")
    difference = ImageChops.difference(before.convert("RGBA"), after.convert("RGBA"))
    channels = difference.split()
    maximum = channels[0]
    for channel in channels[1:]:
        maximum = ImageChops.lighter(maximum, channel)
    return maximum.point(lambda value: 255 if value else 0)


def permitted_edit_mask() -> Image.Image:
    """Declare every source pixel Assembly may change before composition."""
    permitted = Image.new("L", NATIVE_SIZE, 0)
    for box in EDIT_BOXES:
        permitted.paste(255, box)
    return permitted


def crisp_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT), size)


def draw_crisp_text(
    image: Image.Image,
    xy: tuple[int, int],
    text: str,
    *,
    size: int,
    fill: tuple[int, int, int, int],
    highlight: tuple[int, int, int, int] | None = None,
) -> None:
    draw = ImageDraw.Draw(image)
    draw.fontmode = "1"
    font = crisp_font(size)
    if highlight is not None:
        draw.text((xy[0] - 1, xy[1] - 1), text, font=font, fill=highlight)
    draw.text(xy, text, font=font, fill=fill)


def draw_field(
    image: Image.Image,
    box: tuple[int, int, int, int],
    *,
    arrow: Image.Image | None = None,
    arrow_box: tuple[int, int, int, int] | None = None,
) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(image)
    draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=FIELD_FILL, outline=FIELD_EDGE)
    draw.line((x0 + 1, y0 + 1, x1 - 2, y0 + 1), fill=FIELD_SHADOW)
    draw.line((x0 + 1, y0 + 1, x0 + 1, y1 - 2), fill=FIELD_SHADOW)
    draw.line((x0 + 2, y1 - 2, x1 - 2, y1 - 2), fill=FIELD_LIGHT)
    if arrow is not None and arrow_box is not None:
        image.paste(arrow, arrow_box[:2])


def draw_button(
    image: Image.Image, box: tuple[int, int, int, int], text: str
) -> None:
    x0, y0, x1, y1 = box
    draw = ImageDraw.Draw(image)
    draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=BUTTON_FILL, outline=(106, 106, 106, 255))
    draw.line((x0 + 1, y0 + 1, x1 - 2, y0 + 1), fill=WHITE)
    draw.line((x0 + 1, y0 + 1, x0 + 1, y1 - 2), fill=WHITE)
    draw.line((x0 + 2, y1 - 2, x1 - 2, y1 - 2), fill=BUTTON_BOTTOM)
    font = crisp_font(10)
    left, top, right, bottom = font.getbbox(text)
    width, height = right - left, bottom - top
    xy = (x0 + (x1 - x0 - width) // 2 - left, y0 + (y1 - y0 - height) // 2 - top)
    draw_crisp_text(image, xy, text, size=10, fill=BODY_INK)


def title_background(baseline: Image.Image) -> Image.Image:
    clean = baseline.crop((108, 7, 244, 23))
    return clean.resize(
        (TITLE_EDIT_BOX[2] - TITLE_EDIT_BOX[0], TITLE_EDIT_BOX[3] - TITLE_EDIT_BOX[1]),
        Image.Resampling.LANCZOS,
    )


def assemble_closed(source: Image.Image) -> tuple[Image.Image, Image.Image]:
    baseline = native_source(source)
    permitted = permitted_edit_mask()
    output = baseline.copy()

    output.paste(title_background(baseline), TITLE_EDIT_BOX[:2])
    draw_crisp_text(
        output,
        (15, 9),
        EXACT_COPY["title"],
        size=12,
        fill=BODY_INK,
        highlight=TITLE_HIGHLIGHT,
    )

    # Each authorized row is reconstructed over the source's plain white body.
    # Narrow row boxes avoid importing any generated background or changing the
    # magenta edge bloom around the panel.
    for box in (ROW_ONE_EDIT_BOX, ROW_TWO_EDIT_BOX, ROW_THREE_EDIT_BOX):
        ImageDraw.Draw(output).rectangle(
            (box[0], box[1], box[2] - 1, box[3] - 1), fill=WHITE
        )

    arrow = baseline.crop(SOURCE_ARROW_BOX)

    draw_crisp_text(output, (14, 30), EXACT_COPY["custom_filters"], size=10, fill=LABEL_INK)
    draw_field(output, (92, 28, 256, 45))

    draw_crisp_text(output, (13, 51), EXACT_COPY["images_per_page"], size=10, fill=LABEL_INK)
    draw_field(output, (95, 49, 133, 65), arrow=arrow, arrow_box=PAGE_ARROW_BOX)
    draw_crisp_text(output, (99, 51), EXACT_COPY["page_value"], size=10, fill=BODY_INK)

    draw_crisp_text(output, (136, 51), EXACT_COPY["sort_by"], size=10, fill=LABEL_INK)
    draw_field(output, (178, 49, 256, 65), arrow=arrow, arrow_box=SORT_ARROW_BOX)
    draw_crisp_text(output, (182, 51), EXACT_COPY["selected_sort"], size=10, fill=BODY_INK)

    on_radio = baseline.crop(SOURCE_ON_RADIO_BOX)
    off_radio = baseline.crop(SOURCE_OFF_RADIO_BOX)
    output.paste(on_radio, ON_RADIO_BOX[:2])
    output.paste(off_radio, OFF_RADIO_BOX[:2])
    draw_crisp_text(output, (63, 72), EXACT_COPY["choices"][0], size=10, fill=BODY_INK)
    draw_crisp_text(output, (100, 72), EXACT_COPY["choices"][1], size=10, fill=BODY_INK)

    # The source password label and field disappear with the row reconstruction.
    draw_button(output, (179, 94, 217, 114), EXACT_COPY["buttons"][0])
    draw_button(output, (219, 94, 258, 114), EXACT_COPY["buttons"][1])

    actual = changed_pixel_mask(baseline, output)
    outside = ImageChops.multiply(actual, ImageChops.invert(permitted))
    if outside.getbbox() is not None:
        raise RuntimeError(f"Assembly changed source pixels outside edit boxes: {outside.getbbox()}")
    return output, permitted


def assemble_open(closed: Image.Image) -> Image.Image:
    if closed.size != NATIVE_SIZE:
        raise ValueError(f"closed state must be {NATIVE_SIZE}, got {closed.size}")
    output = Image.new("RGBA", OPEN_SIZE, (0, 0, 0, 0))
    output.paste(closed.convert("RGBA"), (0, 0))
    x0, y0, x1, y1 = POPUP_BOX
    draw = ImageDraw.Draw(output)
    draw.rectangle((x0, y0, x1 - 1, y1 - 1), fill=WHITE, outline=FIELD_EDGE)
    row_height = 14
    for index, option in enumerate(SORT_OPTIONS):
        top = y0 + 2 + index * row_height
        bottom = top + row_height
        fill = POPUP_SELECTED if index == 0 else (WHITE if index % 2 else POPUP_STRIPE)
        draw.rectangle((x0 + 1, top - 1, x1 - 2, bottom - 1), fill=fill)
        draw_crisp_text(output, (x0 + 5, top), option, size=10, fill=BODY_INK)
    return output


def count_pixels(mask: Image.Image) -> int:
    histogram = mask.convert("L").histogram()
    return sum(histogram[1:])


def make_contact_sheet(
    source: Image.Image,
    raw_one: Image.Image,
    raw_two: Image.Image,
    closed: Image.Image,
    open_state: Image.Image,
) -> Image.Image:
    source_review = source.convert("RGB")
    raw_size = (640, 360)
    raw_one = raw_one.convert("RGB").resize(raw_size, Image.Resampling.LANCZOS)
    raw_two = raw_two.convert("RGB").resize(raw_size, Image.Resampling.LANCZOS)
    closed_review = closed.convert("RGB").resize((1088, 504), Image.Resampling.NEAREST)
    open_review = open_state.convert("RGBA").resize((1088, 760), Image.Resampling.NEAREST)
    open_back = Image.new("RGB", open_review.size, WHITE[:3])
    open_back.paste(open_review, (0, 0), open_review.getchannel("A"))

    width = max(24 + source_review.width + 12 + closed_review.width, 24 + raw_size[0] * 2 + 12, 24 + open_back.width)
    height = 24 + max(source_review.height, closed_review.height) + 30 + raw_size[1] + 30 + open_back.height + 24
    sheet = Image.new("RGB", (width, height), (32, 35, 43))
    draw = ImageDraw.Draw(sheet)
    draw.text((12, 6), "style source / deterministic closed state", fill=(255, 255, 255))
    y = 24
    sheet.paste(source_review, (12, y))
    sheet.paste(closed_review, (24 + source_review.width, y))
    y += max(source_review.height, closed_review.height)
    draw.text((12, y + 8), "Qwen Render Pass candidates (diagnostic only)", fill=(255, 255, 255))
    y += 30
    sheet.paste(raw_one, (12, y)); sheet.paste(raw_two, (24 + raw_size[0], y))
    y += raw_size[1]
    draw.text((12, y + 8), "deterministic open dropdown state — all nine options", fill=(255, 255, 255))
    y += 30
    sheet.paste(open_back, (12, y))
    return sheet


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--style-source", type=Path, default=STYLE_SOURCE)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    style_path = args.style_source.resolve()
    output_dir = args.output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    if sha256(FONT) != FONT_SHA256:
        raise RuntimeError("pinned PixelMplus font hash does not match")
    source = Image.open(style_path).convert("RGBA")
    closed, permitted = assemble_closed(source)
    open_state = assemble_open(closed)

    closed_native = output_dir / "custom-filters-closed-native.png"
    closed_review = output_dir / "custom-filters-closed.png"
    open_native = output_dir / "custom-filters-open-native.png"
    open_review = output_dir / "custom-filters-open.png"
    mask_native = output_dir / "edit-mask-native.png"
    mask_review = output_dir / "edit-mask.png"
    actual_native = output_dir / "actual-difference-mask-native.png"
    actual_review = output_dir / "actual-difference-mask.png"
    contact = output_dir / "contact-sheet.png"

    closed.save(closed_native)
    closed.resize((closed.width * SCALE, closed.height * SCALE), Image.Resampling.NEAREST).save(closed_review)
    open_state.save(open_native)
    open_state.resize((open_state.width * SCALE, open_state.height * SCALE), Image.Resampling.NEAREST).save(open_review)
    permitted.save(mask_native)
    permitted.resize((permitted.width * SCALE, permitted.height * SCALE), Image.Resampling.NEAREST).save(mask_review)
    make_contact_sheet(
        source,
        Image.open(RAW_RUN / "image-01.png"),
        Image.open(RAW_RUN / "image-02.png"),
        closed,
        open_state,
    ).save(contact)

    baseline = native_source(source)
    actual = changed_pixel_mask(baseline, closed)
    actual.save(actual_native)
    actual.resize((actual.width * SCALE, actual.height * SCALE), Image.Resampling.NEAREST).save(actual_review)
    outside = ImageChops.multiply(actual, ImageChops.invert(permitted))
    verification = {
        "issue": 138,
        "assembly": "custom-filters-ro-v001",
        "style_source": repo_path(style_path),
        "style_source_sha256": sha256(style_path),
        "data_source": repo_path(DATA_SOURCE),
        "data_source_sha256": sha256(DATA_SOURCE),
        "data_source_usage": "strings and order only; assembler never opens this image",
        "font": repo_path(FONT),
        "font_sha256": FONT_SHA256,
        "qwen_candidates_usage": "diagnostic evidence only; assembler never opens them until contact-sheet rendering",
        "closed_native_sha256": sha256(closed_native),
        "open_native_sha256": sha256(open_native),
        "edit_boxes": [list(box) for box in EDIT_BOXES],
        "changed_native_pixels": count_pixels(actual),
        "permitted_mask_pixels": count_pixels(permitted),
        "actual_difference_is_subset_of_permitted_mask": outside.getbbox() is None,
        "changed_pixels_outside_edit_boxes": count_pixels(outside),
        "closed_native_size": list(closed.size),
        "open_native_size": list(open_state.size),
        "exact_copy": {
            **{key: list(value) if isinstance(value, tuple) else value for key, value in EXACT_COPY.items()},
        },
        "sort_option_count": len(SORT_OPTIONS),
        "password_row_present": False,
        "provider": "openrouter",
        "model": "qwen/qwen-image-3-pro",
        "requested_outputs": 2,
        "completed_outputs": 2,
        "ambiguous_outputs": 0,
        "prompt_id": "e12f195d-dfaa-4810-bac9-96963b4b3c35",
        "estimated_cost_usd": 0.10,
        "actual_cost_usd": None,
    }
    (output_dir / "verification.json").write_text(
        json.dumps(verification, indent=2) + "\n", encoding="utf-8"
    )
    run = {
        "issue": 138,
        "method": "source-owned deterministic native Assembly after bounded Qwen Render Pass",
        "sources": {
            "style": repo_path(style_path),
            "data_only": repo_path(DATA_SOURCE),
        },
        "font": {
            "path": repo_path(FONT),
            "sha256": FONT_SHA256,
        },
        "outputs": {
            "closed_native": repo_path(closed_native),
            "closed_review": repo_path(closed_review),
            "open_native": repo_path(open_native),
            "open_review": repo_path(open_review),
            "mask_native": repo_path(mask_native),
            "mask_review": repo_path(mask_review),
            "actual_difference_mask_native": repo_path(actual_native),
            "actual_difference_mask_review": repo_path(actual_review),
            "contact_sheet": repo_path(contact),
            "verification": repo_path(output_dir / "verification.json"),
        },
        "render_pass": {
            "provider": "openrouter",
            "model": "qwen/qwen-image-3-pro",
            "prompt_id": "e12f195d-dfaa-4810-bac9-96963b4b3c35",
            "requested_outputs": 2,
            "completed_outputs": 2,
            "ambiguous_outputs": 0,
            "estimated_cost_usd": 0.10,
            "actual_cost_usd": None,
        },
    }
    (output_dir / "run.json").write_text(
        json.dumps(run, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(verification, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
