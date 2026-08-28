from PIL import Image

from seedance_icons.retro import (
    RetroThresholds,
    certify,
    dedupe_frames,
    extract_palette,
    identity_fraction,
    silhouette_iou,
    snap_and_lock,
)

MATTE = (0, 255, 0)


def tile(color, size=32, matte=MATTE):
    img = Image.new("RGB", (size, size), matte)
    for x in range(8, 24):
        for y in range(8, 24):
            img.putpixel((x, y), color)
    return img


def test_snap_and_lock_maps_every_pixel_into_the_palette():
    source = tile((200, 40, 40))
    palette = extract_palette(source, colors=4)
    locked = snap_and_lock(tile((205, 45, 38)), palette, grid=16)
    allowed = {tuple(palette.getpalette()[i * 3 : i * 3 + 3]) for i in range(4)}
    assert set(locked.getdata()) <= allowed


def test_dedupe_frames_collapses_identical_and_caps_count():
    a, b = tile((200, 40, 40)), tile((40, 40, 200))
    frames = [a, a, b, b, a, a, b, b, a, a]
    unique = dedupe_frames(frames, max_frames=4)
    assert 2 <= len(unique) <= 4


def test_silhouette_iou_penalizes_escaping_pixels():
    base = tile((200, 40, 40))
    escaped = tile((200, 40, 40))
    for x in range(32):
        escaped.putpixel((x, 0), (200, 40, 40))
    assert silhouette_iou(base, base, MATTE) == 1.0
    assert silhouette_iou(escaped, base, MATTE) < 1.0


def test_identity_fraction_detects_redraw():
    source = tile((200, 40, 40))
    palette = extract_palette(source, colors=4)
    same = snap_and_lock(source, palette, grid=16)
    redrawn = snap_and_lock(tile((40, 200, 40)), palette, grid=16)
    assert identity_fraction(same, same) == 1.0
    assert identity_fraction(redrawn, same) < 0.97


def test_certify_applies_thresholds():
    good = {
        "unique_frames": 4,
        "effective_fps": 6.0,
        "out_of_palette_pixels": 0,
        "min_silhouette_iou": 0.95,
        "frame0_identity": 0.99,
    }
    bad = dict(good, min_silhouette_iou=0.5, frame0_identity=0.7)
    assert certify(good, RetroThresholds())["certified"] is True
    result = certify(bad, RetroThresholds())
    assert result["certified"] is False
    assert result["checks"]["silhouette_stable"] is False
    assert result["diagnostics"]["frame0_identity"] == 0.7
