"""Build a labeled contact sheet for the Issue #53 seed-variance outputs."""

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "artifacts" / "benchmarks" / "issue-53-seed-variance"
REFERENCE = ROOT / "artifacts" / "references" / "plantstudio-main-window.png"

CELL_W, CELL_H, LABEL_H = 512, 410, 28


def main():
    tiles = [("reference 474x403", Image.open(REFERENCE).convert("RGB"))]
    for path in sorted(OUT.glob("outputs/seed-*.png"),
                       key=lambda p: int(p.stem.split("-")[1])):
        tiles.append((path.stem, Image.open(path).convert("RGB")))
    columns, rows = 3, (len(tiles) + 2) // 3
    sheet = Image.new("RGB", (columns * CELL_W, rows * (CELL_H + LABEL_H)), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    for index, (label, image) in enumerate(tiles):
        col, row = index % columns, index // columns
        image.thumbnail((CELL_W - 8, CELL_H - 8))
        x = col * CELL_W + (CELL_W - image.width) // 2
        y = row * (CELL_H + LABEL_H) + (CELL_H - image.height) // 2
        sheet.paste(image, (x, y))
        draw.text(
            (col * CELL_W + 10, row * (CELL_H + LABEL_H) + CELL_H + 6),
            label, fill=(255, 255, 255),
        )
    target = OUT / "contact-sheet.png"
    sheet.save(target)
    print("wrote", target, sheet.size)


if __name__ == "__main__":
    main()
