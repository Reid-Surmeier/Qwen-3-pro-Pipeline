#!/usr/bin/env python3.12
"""Build Issue #138 v002 from source-owned RO chrome.

The source window is widened only to make the required English copy fit at one
source-matched size. Existing controls are never redrawn: the OK/cancel pair,
dropdown arrows, and radio sprites are copied from the full-resolution source
without resizing. The prior v001 remains rejected evidence.
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
RENDER_RUN = ROOT / "artifacts/runs/custom-filters-ro-render-v001"
QWEN_POPUP_SOURCE = RENDER_RUN / "image-01.png"
QWEN_POPUP_SOURCE_SHA256 = "b61a9c82e151ab3e1db5e4557644f27ba4c9da3030c98038c1a0f41ab92e355c"
# Candidate 1's missing-element contribution: popup frame and row surface only.
# Generated glyphs are deliberately excluded and replaced deterministically.
QWEN_POPUP_BOX = (1150, 374, 1768, 864)
QWEN_SELECTED_ROW_BOTTOM = 64
REJECTED_V001 = (
    ROOT
    / "artifacts/runs/custom-filters-ro-assembly-v001/custom-filters-closed.png"
)
DEFAULT_OUTPUT = ROOT / "artifacts/runs/custom-filters-ro-assembly-v002"
FONT = ROOT / "godot/fonts/PixelMplus10-Regular.ttf"
FONT_SHA256 = "01b5e4aea5a3bbe80463c178e7868d5a34cd75e8ed7bc4d97097ebb1a71af7c7"

SOURCE_SIZE = (1088, 504)
REVIEW_SIZE = (1344, 504)
OPEN_REVIEW_SIZE = (1344, 784)
NATIVE_SIZE = (336, 126)
OPEN_NATIVE_SIZE = (336, 196)
SCALE = 4

BODY_FONT_SIZE = 40
TITLE_FONT_SIZE = 48
ROW_BASELINES = (120, 204, 288)

SOURCE_TITLE_BLANK_BOX = (430, 28, 970, 88)
SOURCE_BLANK_FIELD_BOX = (196, 112, 1024, 180)
SOURCE_DROPDOWN_BOX = (196, 196, 532, 260)
SOURCE_ARROW_BOX = (468, 200, 532, 260)
SOURCE_ON_RADIO_BOX = (196, 280, 244, 336)
SOURCE_OFF_RADIO_BOX = (340, 280, 388, 336)
SOURCE_BUTTON_PAIR_BOX = (712, 376, 1036, 460)

TITLE_FIELD_BOX = (376, 112, 1280, 180)
PAGE_FIELD_BOX = (392, 196, 616, 260)
# The sort control is widened by extending only its source-owned field middle.
# Its arrow/divider remains a byte-exact source crop, and the popup shares the
# control's left and right edges.
SORT_FIELD_BOX = (808, 196, 1292, 260)
PAGE_ARROW_BOX = (552, 200, 616, 260)
SORT_ARROW_BOX = (1228, 200, 1292, 260)
TARGET_ON_RADIO_BOX = SOURCE_ON_RADIO_BOX
TARGET_OFF_RADIO_BOX = SOURCE_OFF_RADIO_BOX
TARGET_BUTTON_PAIR_BOX = (968, 376, 1292, 460)
POPUP_BOX = (808, 256, 1292, 768)
POPUP_ROW_SPACING = 56

TITLE_EDIT_BOX = (40, 24, 760, 96)
ROW_ONE_EDIT_BOX = (48, 104, 1296, 184)
ROW_TWO_EDIT_BOX = (48, 188, 1296, 268)
ROW_THREE_EDIT_BOX = (48, 272, 520, 344)
BUTTON_EDIT_BOX = TARGET_BUTTON_PAIR_BOX
EDIT_BOXES = (
    TITLE_EDIT_BOX,
    ROW_ONE_EDIT_BOX,
    ROW_TWO_EDIT_BOX,
    ROW_THREE_EDIT_BOX,
    BUTTON_EDIT_BOX,
)

LABEL_INK = (26, 68, 102, 255)
BODY_INK = (16, 16, 16, 255)
WHITE = (255, 255, 255, 255)

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

BODY_TEXT_RULES = (
    {"text": "Custom filters:", "xy": (56, ROW_BASELINES[0]), "size": BODY_FONT_SIZE, "fill": LABEL_INK},
    {"text": "Images per page:", "xy": (52, ROW_BASELINES[1]), "size": BODY_FONT_SIZE, "fill": LABEL_INK},
    {"text": "20", "xy": (408, ROW_BASELINES[1]), "size": BODY_FONT_SIZE, "fill": BODY_INK},
    {"text": "Sort by:", "xy": (640, ROW_BASELINES[1]), "size": BODY_FONT_SIZE, "fill": LABEL_INK},
    {"text": "Relevance", "xy": (824, ROW_BASELINES[1]), "size": BODY_FONT_SIZE, "fill": BODY_INK},
    {"text": "On", "xy": (252, ROW_BASELINES[2]), "size": BODY_FONT_SIZE, "fill": BODY_INK},
    {"text": "Off", "xy": (400, ROW_BASELINES[2]), "size": BODY_FONT_SIZE, "fill": BODY_INK},
)

EXACT_COPY = {
    "title": "Custom filters",
    "custom_filters": "Custom filters:",
    "images_per_page": "Images per page:",
    "page_value": "20",
    "sort_by": "Sort by:",
    "selected_sort": "Relevance",
    "choices": ("On", "Off"),
    "source_buttons": ("OK", "cancel"),
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


def changed_pixel_mask(before: Image.Image, after: Image.Image) -> Image.Image:
    if before.size != after.size:
        raise ValueError(f"image sizes differ: {before.size} != {after.size}")
    channels = ImageChops.difference(
        before.convert("RGBA"), after.convert("RGBA")
    ).split()
    maximum = channels[0]
    for channel in channels[1:]:
        maximum = ImageChops.lighter(maximum, channel)
    return maximum.point(lambda value: 255 if value else 0)


def count_pixels(mask: Image.Image) -> int:
    return sum(mask.convert("L").histogram()[1:])


def permitted_edit_mask() -> Image.Image:
    permitted = Image.new("L", REVIEW_SIZE, 0)
    for box in EDIT_BOXES:
        permitted.paste(255, box)
    return permitted


def draw_text(
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
    font = ImageFont.truetype(str(FONT), size)
    if highlight is not None:
        draw.text((xy[0] - 4, xy[1] - 4), text, font=font, fill=highlight)
    draw.text(xy, text, font=font, fill=fill)


def horizontal_nine_slice(
    source: Image.Image, width: int, cap: int = 12
) -> Image.Image:
    if width < 2 * cap:
        raise ValueError("nine-slice target is narrower than its caps")
    output = Image.new(source.mode, (width, source.height))
    output.paste(source.crop((0, 0, cap, source.height)), (0, 0))
    middle = source.crop((cap, 0, source.width - cap, source.height)).resize(
        (width - 2 * cap, source.height), Image.Resampling.LANCZOS
    )
    output.paste(middle, (cap, 0))
    output.paste(
        source.crop((source.width - cap, 0, source.width, source.height)),
        (width - cap, 0),
    )
    return output


def clean_dropdown_sprite(source: Image.Image) -> Image.Image:
    control = source.crop(SOURCE_DROPDOWN_BOX)
    # Restore the text interior from the source's blank top field. The bevel,
    # divider and arrow remain untouched source pixels.
    blank = source.crop((208, 124, 456, 172))
    control.paste(blank, (12, 8))
    return control


def source_dropdown(source: Image.Image, width: int) -> Image.Image:
    """Extend only the source field middle and retain its exact arrow sprite."""
    clean = clean_dropdown_sprite(source)
    arrow_width = SOURCE_ARROW_BOX[2] - SOURCE_ARROW_BOX[0]
    body = clean.crop((0, 0, clean.width - arrow_width, clean.height))
    output = Image.new("RGBA", (width, clean.height))
    output.paste(horizontal_nine_slice(body, width - arrow_width), (0, 0))
    output.paste(clean.crop((clean.width - arrow_width, 0, clean.width, clean.height)), (width - arrow_width, 0))
    return output


def widened_shell(source: Image.Image) -> Image.Image:
    source = source.convert("RGBA")
    if source.size != SOURCE_SIZE:
        raise ValueError(f"style source must be {SOURCE_SIZE}, got {source.size}")

    output = source.resize(REVIEW_SIZE, Image.Resampling.LANCZOS)
    # Restore exact side caps after the horizontal extension.
    output.paste(source.crop((0, 0, 48, 504)), (0, 0))
    output.paste(source.crop((1040, 0, 1088, 504)), (1296, 0))

    # One continuous source-derived glass field; no title-sized blue patch.
    clean_title = source.crop(SOURCE_TITLE_BLANK_BOX).resize(
        (1184, 60), Image.Resampling.LANCZOS
    )
    output.paste(clean_title, (48, 28))
    output.paste(source.crop((976, 20, 1040, 92)), (1232, 20))

    body_fill = source.getpixel((540, 348))
    ImageDraw.Draw(output).rectangle((48, 96, 1295, 351), fill=body_fill)

    # Rebuild the footer from a clean source stripe, then reapply the exact
    # source button crop during Assembly.
    footer = source.crop((48, 368, 700, 460)).resize(
        (1248, 92), Image.Resampling.LANCZOS
    )
    output.paste(footer, (48, 368))
    return output


def assemble_closed(
    source: Image.Image,
) -> tuple[Image.Image, Image.Image, Image.Image]:
    baseline = widened_shell(source)
    permitted = permitted_edit_mask()
    output = baseline.copy()

    draw_text(
        output,
        (60, 36),
        EXACT_COPY["title"],
        size=TITLE_FONT_SIZE,
        fill=BODY_INK,
        highlight=WHITE,
    )

    blank_field = source.crop(SOURCE_BLANK_FIELD_BOX)
    output.paste(
        horizontal_nine_slice(
            blank_field, TITLE_FIELD_BOX[2] - TITLE_FIELD_BOX[0]
        ),
        TITLE_FIELD_BOX[:2],
    )

    output.paste(
        source_dropdown(source, PAGE_FIELD_BOX[2] - PAGE_FIELD_BOX[0]),
        PAGE_FIELD_BOX[:2],
    )
    output.paste(
        source_dropdown(source, SORT_FIELD_BOX[2] - SORT_FIELD_BOX[0]),
        SORT_FIELD_BOX[:2],
    )

    output.paste(source.crop(SOURCE_ON_RADIO_BOX), TARGET_ON_RADIO_BOX[:2])
    output.paste(source.crop(SOURCE_OFF_RADIO_BOX), TARGET_OFF_RADIO_BOX[:2])
    output.paste(source.crop(SOURCE_BUTTON_PAIR_BOX), TARGET_BUTTON_PAIR_BOX[:2])

    for rule in BODY_TEXT_RULES:
        draw_text(
            output,
            rule["xy"],
            rule["text"],
            size=rule["size"],
            fill=rule["fill"],
        )

    actual = changed_pixel_mask(baseline, output)
    outside = ImageChops.multiply(actual, ImageChops.invert(permitted))
    if outside.getbbox() is not None:
        raise RuntimeError(
            f"Assembly changed pixels outside declared regions: {outside.getbbox()}"
        )
    return output, permitted, baseline


def qwen_popup_surface(width: int, height: int) -> Image.Image:
    if sha256(QWEN_POPUP_SOURCE) != QWEN_POPUP_SOURCE_SHA256:
        raise RuntimeError("Qwen popup donor hash does not match")
    with Image.open(QWEN_POPUP_SOURCE) as generated:
        donor = generated.convert("RGBA").crop(QWEN_POPUP_BOX)
    donor = donor.resize((width, height), Image.Resampling.LANCZOS)

    # The far-right interior strip is free of generated lettering. Extend it
    # across each masked region so the Qwen surface/gradient remains while all
    # visible copy is owned by deterministic Assembly.
    strip = donor.crop((width - 52, 4, width - 20, height - 4))
    selected_bottom = round(QWEN_SELECTED_ROW_BOTTOM * height / (QWEN_POPUP_BOX[3] - QWEN_POPUP_BOX[1]))
    selected = strip.crop((0, 0, strip.width, selected_bottom - 4)).resize(
        (width - 8, 52), Image.Resampling.BILINEAR
    )
    remaining = strip.crop((0, selected_bottom - 4, strip.width, strip.height)).resize(
        (width - 8, height - 60), Image.Resampling.BILINEAR
    )
    panel = Image.new("RGBA", (width, height))
    panel.paste(selected, (4, 4))
    panel.paste(remaining, (4, 56))

    # Retain the generated frame itself, but no generated glyph pixels.
    panel.paste(donor.crop((0, 0, width, 4)), (0, 0))
    panel.paste(donor.crop((0, height - 4, width, height)), (0, height - 4))
    panel.paste(donor.crop((0, 0, 4, height)), (0, 0))
    panel.paste(donor.crop((width - 4, 0, width, height)), (width - 4, 0))
    return panel


def popup_panel(closed: Image.Image) -> Image.Image:
    width = POPUP_BOX[2] - POPUP_BOX[0]
    height = POPUP_BOX[3] - POPUP_BOX[1]
    panel = qwen_popup_surface(width, height)
    for index, option in enumerate(SORT_OPTIONS):
        draw_text(
            panel,
            (20, 8 + index * POPUP_ROW_SPACING),
            option,
            size=BODY_FONT_SIZE,
            fill=BODY_INK,
        )
    return panel


def assemble_open(closed: Image.Image) -> Image.Image:
    if closed.size != REVIEW_SIZE:
        raise ValueError(f"closed state must be {REVIEW_SIZE}, got {closed.size}")
    output = Image.new("RGBA", OPEN_REVIEW_SIZE, (0, 0, 0, 0))
    output.paste(closed, (0, 0))
    output.paste(popup_panel(closed), POPUP_BOX[:2])
    return output


def make_contact_sheet(
    source: Image.Image,
    rejected: Image.Image,
    closed: Image.Image,
    open_state: Image.Image,
) -> Image.Image:
    source = source.convert("RGB")
    rejected = rejected.convert("RGB")
    closed = closed.convert("RGB")
    open_rgba = open_state.convert("RGBA")
    open_back = Image.new("RGB", open_rgba.size, WHITE[:3])
    open_back.paste(open_rgba, (0, 0), open_rgba.getchannel("A"))

    margin = 20
    width = max(source.width + rejected.width + 3 * margin, closed.width + 2 * margin, open_back.width + 2 * margin)
    height = 28 + max(source.height, rejected.height) + 36 + closed.height + 36 + open_back.height + margin
    sheet = Image.new("RGB", (width, height), (32, 35, 43))
    draw = ImageDraw.Draw(sheet)
    draw.text((margin, 7), "source / rejected v001", fill=(255, 255, 255))
    y = 28
    sheet.paste(source, (margin, y))
    sheet.paste(rejected, (source.width + 2 * margin, y))
    y += max(source.height, rejected.height)
    draw.text((margin, y + 9), "v002 closed — source controls, uniform type size", fill=(255, 255, 255))
    y += 36
    sheet.paste(closed, (margin, y))
    y += closed.height
    draw.text((margin, y + 9), "v002 open — masked Qwen surface, deterministic text", fill=(255, 255, 255))
    y += 36
    sheet.paste(open_back, (margin, y))
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
    closed, permitted, baseline = assemble_closed(source)
    open_state = assemble_open(closed)
    actual = changed_pixel_mask(baseline, closed)
    outside = ImageChops.multiply(actual, ImageChops.invert(permitted))

    paths = {
        "closed": output_dir / "custom-filters-closed.png",
        "closed_native": output_dir / "custom-filters-closed-native.png",
        "open": output_dir / "custom-filters-open.png",
        "open_native": output_dir / "custom-filters-open-native.png",
        "permitted": output_dir / "permitted-edit-mask.png",
        "permitted_native": output_dir / "permitted-edit-mask-native.png",
        "actual": output_dir / "actual-difference-mask.png",
        "actual_native": output_dir / "actual-difference-mask-native.png",
        "contact": output_dir / "contact-sheet.png",
    }
    closed.save(paths["closed"])
    closed.resize(NATIVE_SIZE, Image.Resampling.NEAREST).save(paths["closed_native"])
    open_state.save(paths["open"])
    open_state.resize(OPEN_NATIVE_SIZE, Image.Resampling.NEAREST).save(paths["open_native"])
    permitted.save(paths["permitted"])
    permitted.resize(NATIVE_SIZE, Image.Resampling.NEAREST).save(paths["permitted_native"])
    actual.save(paths["actual"])
    actual.resize(NATIVE_SIZE, Image.Resampling.NEAREST).save(paths["actual_native"])
    make_contact_sheet(
        source,
        Image.open(REJECTED_V001),
        closed,
        open_state,
    ).save(paths["contact"])

    button_exact = (
        source.crop(SOURCE_BUTTON_PAIR_BOX).tobytes()
        == closed.crop(TARGET_BUTTON_PAIR_BOX).tobytes()
    )
    arrow = source.crop(SOURCE_ARROW_BOX)
    arrows_exact = all(
        arrow.tobytes() == closed.crop(box).tobytes()
        for box in (PAGE_ARROW_BOX, SORT_ARROW_BOX)
    )
    radios_exact = (
        source.crop(SOURCE_ON_RADIO_BOX).tobytes()
        == closed.crop(TARGET_ON_RADIO_BOX).tobytes()
        and source.crop(SOURCE_OFF_RADIO_BOX).tobytes()
        == closed.crop(TARGET_OFF_RADIO_BOX).tobytes()
    )
    verification = {
        "issue": 138,
        "assembly": "custom-filters-ro-v002",
        "status": "candidate_pending_owner_visual_approval",
        "style_source": repo_path(style_path),
        "style_source_sha256": sha256(style_path),
        "data_source": repo_path(DATA_SOURCE),
        "data_source_sha256": sha256(DATA_SOURCE),
        "data_source_usage": "strings and order only",
        "rejected_parent": repo_path(REJECTED_V001),
        "rejected_parent_sha256": sha256(REJECTED_V001),
        "font": repo_path(FONT),
        "font_sha256": FONT_SHA256,
        "body_font_size": BODY_FONT_SIZE,
        "body_font_sizes_used": sorted({rule["size"] for rule in BODY_TEXT_RULES}),
        "row_baselines": list(ROW_BASELINES),
        "row_gaps": [ROW_BASELINES[1] - ROW_BASELINES[0], ROW_BASELINES[2] - ROW_BASELINES[1]],
        "source_button_pair_exact": button_exact,
        "source_dropdown_arrows_exact": arrows_exact,
        "source_radios_exact": radios_exact,
        "source_control_sprites_rescaled": False,
        "source_field_middles_nine_sliced": True,
        "qwen_popup_surface_source": repo_path(QWEN_POPUP_SOURCE),
        "qwen_popup_surface_source_sha256": QWEN_POPUP_SOURCE_SHA256,
        "qwen_popup_surface_box": list(QWEN_POPUP_BOX),
        "generated_glyph_pixels_in_final": False,
        "review_size": list(closed.size),
        "native_size": list(NATIVE_SIZE),
        "open_review_size": list(open_state.size),
        "open_native_size": list(OPEN_NATIVE_SIZE),
        "changed_pixels": count_pixels(actual),
        "permitted_mask_pixels": count_pixels(permitted),
        "changed_pixels_outside_permitted_mask": count_pixels(outside),
        "actual_is_subset_of_permitted_mask": outside.getbbox() is None,
        "closed_sha256": sha256(paths["closed"]),
        "open_sha256": sha256(paths["open"]),
        "exact_copy": {
            key: list(value) if isinstance(value, tuple) else value
            for key, value in EXACT_COPY.items()
        },
        "render_pass": {
            "provider": "openrouter",
            "model": "qwen/qwen-image-3-pro",
            "requested_outputs": 2,
            "completed_outputs": 2,
            "ambiguous_outputs": 0,
            "prompt_id": "e12f195d-dfaa-4810-bac9-96963b4b3c35",
            "usage": "candidate 1 supplies only the masked popup frame and row surface; no generated glyph or closed-state control pixels",
            "new_requests_for_v002": 0,
            "estimated_cost_usd": 0.10,
            "actual_cost_usd": None,
        },
    }
    verification_path = output_dir / "verification.json"
    verification_path.write_text(
        json.dumps(verification, indent=2) + "\n", encoding="utf-8"
    )
    run = {
        "issue": 138,
        "method": "widened source-derived shell with byte-exact source control sprites",
        "rejected": "custom-filters-ro-assembly-v001",
        "corrections": [
            "byte-exact full-resolution OK/cancel source crop",
            "byte-exact source dropdown arrows and radio controls",
            "one 40-pixel body font size on three 84-pixel row baselines",
            "source-derived fields plus masked Qwen popup surface",
        ],
        "outputs": {
            name: repo_path(path) for name, path in paths.items()
        },
        "verification": repo_path(verification_path),
        "render_pass": verification["render_pass"],
    }
    (output_dir / "run.json").write_text(
        json.dumps(run, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(verification, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
