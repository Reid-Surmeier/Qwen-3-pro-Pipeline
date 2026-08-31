"""Jerk is a property of the content, not the timing.

Reid, 2026-08-30: "the movement is still quite jerky." Tracking the moving element
frame by frame showed why - its per-step travel across a twelve-second take ran

    0 0 0 0 0 1 26 66 10 13 9 11 6 14 24 98 13 73 32 17 26 40 9 41 0 0 0 ...

long stretches of nothing, then leaps of a hundred pixels. Holding every frame for an
equal time cannot fix that. Selecting frames spaced evenly along the path can, and it
only ever picks frames the model already drew."""

from __future__ import annotations

from PIL import Image

from seedance_icons.retro import ink_centroid, resample_by_travel, step_evenness

MATTE = (0, 255, 0)


def _frame(x: int) -> Image.Image:
    """A tile with a small dark square at horizontal position x."""
    im = Image.new("RGB", (64, 64), MATTE)
    im.paste(Image.new("RGB", (48, 48), (255, 255, 255)), (8, 8))
    im.paste(Image.new("RGB", (6, 6), (0, 0, 40)), (x, 28))
    return im


def test_centroid_follows_the_element() -> None:
    a = ink_centroid(_frame(12), MATTE)
    b = ink_centroid(_frame(40), MATTE)
    assert a and b and b[0] > a[0]


def test_evenness_separates_a_lurch_from_a_steady_walk() -> None:
    steady = [_frame(x) for x in (12, 18, 24, 30, 36, 42)]
    lurching = [_frame(x) for x in (12, 12, 12, 12, 42, 42)]
    assert step_evenness(steady, MATTE) < 0.2
    assert step_evenness(lurching, MATTE) > step_evenness(steady, MATTE)


def test_resampling_by_travel_evens_out_a_lurch() -> None:
    lurching = [_frame(x) for x in (12, 12, 12, 12, 12, 20, 44, 46, 46, 46, 46)]
    before = step_evenness(lurching, MATTE)
    after = step_evenness(resample_by_travel(lurching, 5, MATTE), MATTE)
    assert after < before


def test_resampling_only_selects_frames_that_exist() -> None:
    frames = [_frame(x) for x in range(10, 50, 4)]
    picked = resample_by_travel(frames, 4, MATTE)
    assert all(any(p.tobytes() == f.tobytes() for f in frames) for p in picked)
