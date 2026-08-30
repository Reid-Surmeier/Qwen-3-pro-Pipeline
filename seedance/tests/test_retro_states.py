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
