#!/usr/bin/env python3.12
"""Deterministically assemble an RO-style options window from sprites cut from
the Reference Screen.

Every control is a sprite lifted from the reference at its native scale; nothing
is generated. The window is composed at the client's native resolution and then
enlarged with nearest-neighbour, which is how the Reference Screen itself was
produced.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

SPRITES = Path("artifacts/references/museum-filter-retro-skin-v001/sprites")
FONT = "/usr/share/fonts/opentype/ipafont-gothic/ipagp.ttf"

# Sampled from the Reference Screen; see docs/runs/museum-filter-retro-skin.md
MAGENTA = (0xFF, 0x00, 0xFF)
BLOOM = (0xFF, 0x96, 0xFF)
WHITE = (0xFF, 0xFF, 0xFF)
STRIPE = (0xF6, 0xF3, 0xF6)
PANEL_RULE = (0xC8, 0xC6, 0xCB)
FIELD_FILL = (0xF9, 0xF3, 0xF7)
FIELD_EDGE = (0xC5, 0xC3, 0xC6)
FIELD_SHADOW = (0xA9, 0xA7, 0xAA)
LABEL_INK = (0x2E, 0x45, 0x60)
BODY_INK = (0x10, 0x10, 0x10)
COUNT_INK = (0x8A, 0x8A, 0x8A)
PLACEHOLDER = (0xA6, 0xA4, 0xA7)
TAB_OFF_FILL = (0xF3, 0xEF, 0xF4)
TAB_EDGE = (0xC9, 0xC6, 0xCB)
TAB_OFF_INK = (0x8B, 0x89, 0x8C)
TAB_ON_INK = (0x3A, 0x3B, 0x3F)

TITLE_H, TAB_W, PAD, ROW_H = 20, 18, 11, 19


def sprite(name: str) -> Image.Image:
    return Image.open(SPRITES / f"{name}.png").convert("RGB")


def crisp(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size)


def text_width(font, s: str) -> int:
    if " " in s:
        words = s.split(" ")
        return sum(int(font.getbbox(w)[2]) for w in words) + WORD_GAP * (len(words) - 1)
    return int(font.getbbox(s)[2])


WORD_GAP = 4


def _word(img, xy, word, font, fill, highlight):
    w, h = text_width(font, word) + 4, font.size + 6
    mask = Image.new("L", (w, h), 255)
    ImageDraw.Draw(mask).text((1, 1), word, font=font, fill=0)
    mask = mask.point(lambda v: 255 if v < 128 else 0)  # hard edges only
    x, y = xy
    if highlight is not None:
        img.paste(Image.new("RGB", (w, h), highlight), (x - 1, y - 1), mask)
    img.paste(Image.new("RGB", (w, h), fill), (x, y), mask)
    return text_width(font, word)


def draw_text(img, xy, s, font, fill, highlight=None):
    """Render text with antialiasing removed, the way a bitmap face reads.

    Words are placed individually: a thresholded space collapses to nothing, so
    the gap has to be measured out rather than drawn.
    """
    x, y = xy
    for i, word in enumerate(s.split(" ")):
        if i:
            x += WORD_GAP
        x += _word(img, (x, y), word, font, fill, highlight) if word else 0
    return x - xy[0]


def stripes(img, box):
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    d.rectangle(box, fill=WHITE)
    for y in range(y0, y1):
        if (y - y0) % 5 in (2, 3):
            d.line([(x0, y), (x1, y)], fill=STRIPE)


def vertical_text(s, font, fill, bg):
    w, h = text_width(font, s) + 4, font.size + 4
    strip = Image.new("RGB", (w, h), bg)
    draw_text(strip, (1, 1), s, font, fill)
    return strip.rotate(90, expand=True)


def build(spec: dict) -> Image.Image:
    body, label, title_f = crisp(11), crisp(11), crisp(12)
    box_off, box_on = sprite("box-empty"), sprite("box-tick")
    bead, close, drop = sprite("bead"), sprite("close"), sprite("dropdown")
    BW = box_off.width

    left = [f"{n} ({c})" for n, c in spec["materials"][:5]]
    right = [f"{n} ({c})" for n, c in spec["materials"][5:]]
    col_w = BW + 5 + max(text_width(body, s) for s in left + right)
    grid_w = col_w * 2 + 20

    match_w = (
        text_width(label, spec["match_label"])
        + 8
        + BW
        + 4
        + text_width(body, spec["any"])
        + 16
        + BW
        + 4
        + text_width(body, spec["all"])
        + 12
        + text_width(body, spec["trailing"])
    )
    inner_w = max(grid_w, match_w, 250)
    panel_w = PAD * 2 + inner_w
    interior_w = TAB_W + panel_w + 3

    panel_h = PAD + 22 + 8 + 17 + 12 + ROW_H * 5 + 4
    interior_h = TITLE_H + panel_h + 16

    W = interior_w + 6
    H = interior_h + 6
    img = Image.new("RGB", (W, H), BLOOM)
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, W - 2, H - 2], fill=MAGENTA)
    d.rectangle([2, 2, W - 3, H - 3], outline=WHITE)
    ox, oy = 3, 3  # interior origin

    # ---- title bar: the reference's own glass, resampled to this width -------
    ref = Image.open(
        "artifacts/references/museum-filter-retro-skin-v001/style-ro-options-window-flat-rgb.png"
    ).convert("RGB")
    bar = ref.crop((600, 45, 1372, 124)).resize((interior_w, TITLE_H), Image.LANCZOS)
    img.paste(bar, (ox, oy))
    img.paste(bead, (ox + 3, oy + (TITLE_H - bead.height) // 2))
    draw_text(
        img,
        (ox + 3 + bead.width + 5, oy + (TITLE_H - 12) // 2 - 1),
        spec["title"],
        title_f,
        BODY_INK,
        highlight=WHITE,
    )
    img.paste(close, (ox + interior_w - close.width - 3, oy + (TITLE_H - close.height) // 2))
    img.paste(
        bead,
        (ox + interior_w - close.width - 3 - bead.width - 5, oy + (TITLE_H - bead.height) // 2),
    )

    cy = oy + TITLE_H
    stripes(img, (ox, cy, ox + interior_w - 1, oy + interior_h - 1))

    # ---- tabs ---------------------------------------------------------------
    on = vertical_text(spec["tab_on"], body, TAB_ON_INK, WHITE)
    off = vertical_text(spec["tab_off"], body, TAB_OFF_INK, TAB_OFF_FILL)
    tx, ty = ox, cy
    d.rectangle([tx, ty, tx + TAB_W - 1, ty + on.height + 7], fill=WHITE)
    d.line([(tx, ty), (tx, ty + on.height + 7)], fill=TAB_EDGE)
    img.paste(on, (tx + 3, ty + 4))
    fy = ty + on.height + 9
    fw_, fh_ = TAB_W - 3, off.height + 8
    d.rectangle([tx, fy, tx + fw_, fy + fh_], fill=TAB_OFF_FILL)
    for i in range(3):  # stair-stepped corners
        d.rectangle([tx + fw_ - i, fy + i * 2, tx + fw_, fy + i * 2 + 1], fill=WHITE)
        d.rectangle([tx + fw_ - i, fy + fh_ - i * 2 - 1, tx + fw_, fy + fh_], fill=WHITE)
    d.line([(tx, fy), (tx, fy + fh_)], fill=TAB_EDGE)
    d.line([(tx, fy + fh_), (tx + fw_ - 3, fy + fh_)], fill=TAB_EDGE)
    for i in range(3):
        d.point([(tx + fw_ - i, fy + i * 2 + 2)], fill=TAB_EDGE)
        d.point([(tx + fw_ - i, fy + fh_ - i * 2 - 2)], fill=TAB_EDGE)
    d.line([(tx + fw_ - 2, fy + 7), (tx + fw_ - 2, fy + fh_ - 7)], fill=TAB_EDGE)
    img.paste(off, (tx + 3, fy + 4))

    # ---- panel --------------------------------------------------------------
    px, py = ox + TAB_W, cy
    d.rectangle([px, py, px + panel_w - 1, py + panel_h - 1], fill=WHITE, outline=PANEL_RULE)
    d.line([(px, py), (px, py + panel_h - 1)], fill=WHITE)  # flush with the active tab

    x0, y = px + PAD, py + PAD

    # search row
    lw = draw_text(img, (x0, y + 6), spec["search_label"], label, LABEL_INK)
    fx = x0 + lw + 8
    fw = inner_w - (lw + 8)
    d.rectangle([fx, y, fx + fw - 1, y + 21], fill=FIELD_FILL, outline=FIELD_EDGE)
    d.line([(fx + 1, y + 1), (fx + fw - 2, y + 1)], fill=FIELD_SHADOW)
    d.line([(fx + 1, y + 1), (fx + 1, y + 20)], fill=FIELD_SHADOW)
    draw_text(img, (fx + 5, y + 6), spec["placeholder"], body, PLACEHOLDER)
    img.paste(drop, (fx + fw - drop.width - 1, y + 1))
    y += 22 + 8

    # match row
    lw = draw_text(img, (x0, y + 3), spec["match_label"], label, LABEL_INK)
    mx = x0 + lw + 8
    img.paste(box_on, (mx, y + 1))
    mx += BW + 4
    mx += draw_text(img, (mx, y + 3), spec["any"], body, BODY_INK) + 16
    img.paste(box_off, (mx, y + 1))
    mx += BW + 4
    mx += draw_text(img, (mx, y + 3), spec["all"], body, BODY_INK) + 12
    draw_text(img, (mx, y + 3), spec["trailing"], body, BODY_INK)
    y += 17 + 12

    # material grid
    for col, names in ((0, left), (1, right)):
        for r, s in enumerate(names):
            bx = x0 + col * (col_w + 20)
            by = y + r * ROW_H
            img.paste(box_off, (bx, by))
            name, count = s.rsplit(" (", 1)
            w = draw_text(img, (bx + BW + 5, by + 2), name, body, BODY_INK)
            draw_text(img, (bx + BW + 5 + w + 4, by + 2), "(" + count, body, COUNT_INK)
    return img


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("spec", type=Path)
    ap.add_argument("--scale", type=int, default=4)
    ap.add_argument("--output", type=Path, required=True)
    a = ap.parse_args()
    img = build(json.loads(a.spec.read_text()))
    a.output.parent.mkdir(parents=True, exist_ok=True)
    img.save(a.output.with_name(a.output.stem + "-native.png"))
    img.resize((img.width * a.scale, img.height * a.scale), Image.NEAREST).save(a.output)
    print(
        f"{a.output} ({img.width * a.scale}x{img.height * a.scale}, native {img.width}x{img.height})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
