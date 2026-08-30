"""State-set segmentation: the cut rule, its failure modes, and per-state certification."""

from __future__ import annotations

import pytest

from seedance_icons.retro import (
    DEFAULT_STATE_MAP,
    RetroError,
    _segment,
    parse_state_map,
)


def test_default_state_map_is_four_equal_quarters() -> None:
    assert list(DEFAULT_STATE_MAP) == ["idle", "hover", "pressed", "settled"]
    for lo, hi in DEFAULT_STATE_MAP.values():
        assert round(hi - lo, 6) == 0.25


def test_parses_a_brief_style_span_string() -> None:
    parsed = parse_state_map(
        {"idle": "0.00-0.25", "hover": "0.25-0.50", "pressed": "0.50-0.75", "settled": "0.75-1.00"}
    )
    assert parsed["pressed"] == (0.50, 0.75)


def test_parses_a_pair() -> None:
    assert parse_state_map({"a": (0.0, 0.5), "b": [0.5, 1.0]})["b"] == (0.5, 1.0)


def test_missing_state_map_falls_back_to_quarters() -> None:
    assert parse_state_map(None) == DEFAULT_STATE_MAP


@pytest.mark.parametrize(
    "bad",
    [
        {"a": "0.0-0.4", "b": "0.5-1.0"},   # gap: which state owns 0.4-0.5?
        {"a": "0.0-0.6", "b": "0.5-1.0"},   # overlap: two states own 0.5-0.6
        {"a": "0.1-1.0"},                    # does not start at zero
        {"a": "0.0-0.9"},                    # does not reach the end
        {"a": "0.5-0.2"},                    # inverted
        {"a": "0.0-1.5"},                    # outside the take
        {"a": "nonsense"},                   # unparseable
    ],
)
def test_ambiguous_cuts_are_rejected(bad: dict) -> None:
    with pytest.raises(RetroError):
        parse_state_map(bad)


def test_segment_slices_by_fraction() -> None:
    frames = list(range(20))
    assert _segment(frames, (0.0, 0.25)) == [0, 1, 2, 3, 4]
    assert _segment(frames, (0.75, 1.0)) == [15, 16, 17, 18, 19]


def test_segment_never_returns_empty() -> None:
    """A span narrower than one frame still owns a frame; a state with no pixels is
    a worse failure than a state with one."""
    assert len(_segment(list(range(3)), (0.4, 0.45))) >= 1


def test_mask_fill_ratio_separates_a_panel_from_a_silhouette() -> None:
    """A guard born of a real failure: an Anchor on an opaque panel makes every
    silhouette metric meaningless, because the mask becomes the panel. The overall
    matte fraction cannot see this — a small panel in a large matte field still
    leaves most of the frame as background — so the test is shape, not area."""
    from PIL import Image

    from seedance_icons.retro import MAX_ANCHOR_MASK_FILL, mask_fill_ratio

    matte = (0, 255, 0)

    panel = Image.new("RGB", (40, 40), matte)
    panel.paste(Image.new("RGB", (16, 16), (254, 254, 253)), (12, 12))
    assert mask_fill_ratio(panel, matte) == 1.0
    assert mask_fill_ratio(panel, matte) > MAX_ANCHOR_MASK_FILL

    # a diagonal, the crudest possible real silhouette
    icon = Image.new("RGB", (40, 40), matte)
    for i in range(16):
        icon.putpixel((12 + i, 12 + i), (0, 0, 0))
    assert mask_fill_ratio(icon, matte) < 0.2

    empty = Image.new("RGB", (10, 10), matte)
    assert mask_fill_ratio(empty, matte) == 0.0


def test_anchor_iou_gates_only_state_set_runs() -> None:
    """The Anchor check must not touch the single-loop path: its thresholds are
    calibrated against Issue #87 and that calibration has to stay valid."""
    from seedance_icons.retro import certify

    single_loop = {
        "unique_frames": 4,
        "effective_fps": 6.0,
        "out_of_palette_pixels": 0,
        "min_silhouette_iou": 0.998,
        "frame0_identity": 0.72,
    }
    result = certify(single_loop)
    assert "matches_anchor" not in result["checks"]
    assert result["certified"]

    faithful_state = dict(single_loop, anchor_silhouette_iou=0.979)
    assert certify(faithful_state)["certified"]

    redrawn_state = dict(single_loop, anchor_silhouette_iou=0.466)
    verdict = certify(redrawn_state)
    assert verdict["checks"]["matches_anchor"] is False
    assert not verdict["certified"]


def test_filled_mode_asserts_no_automatic_fidelity_check() -> None:
    """Filled framing has no calibrated fidelity metric, and the gate must not pretend
    otherwise. Four were tried on the 2026-08-30 run and none separated a good state
    from a bad one, so a person judges these runs and the report says so."""
    from seedance_icons.retro import certify

    base = {
        "unique_frames": 4,
        "effective_fps": 6.0,
        "out_of_palette_pixels": 0,
        "min_silhouette_iou": 0.998,
        "frame0_identity": 0.72,
    }

    filled = certify(dict(base, frame_mode="filled", anchor_pixel_identity=0.41))
    assert "matches_anchor" not in filled["checks"]
    assert filled["checks"]["human_gate_required"] is False

    # matte keeps the calibrated silhouette decision
    drifted = certify(dict(base, frame_mode="matte", anchor_silhouette_iou=0.466))
    assert drifted["checks"]["matches_anchor"] is False
    assert not drifted["certified"]

    faithful = certify(dict(base, frame_mode="matte", anchor_silhouette_iou=0.979))
    assert faithful["certified"]
